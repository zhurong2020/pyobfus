"""PR 1: original/artifact execution, conservative identities and atomic plans."""

import ast
import dataclasses
import inspect
import json
import os
import pickle
import subprocess
import sys

import pytest
from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.cache import BuildCache
from pyobfus.core.import_resolution import discover_accesses
from pyobfus.core.mapping import ObfuscationMapping
from pyobfus.core.module_attributes import apply_attribute_plan
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus.core.preflight import PreflightChecker

IMPORTS = ["from pkg import mod", "import pkg.mod as mod"]
DEFINITIONS = "LIMIT = 7\ndef scale():\n    return LIMIT * 2\nclass Settings:\n    VALUE = 3\n"


def project(tmp_path, app, init="", definitions=DEFINITIONS):
    src = tmp_path / "src"
    (src / "pkg").mkdir(parents=True, exist_ok=True)
    (src / "pkg/__init__.py").write_text(init)
    (src / "pkg/mod.py").write_text(definitions)
    (src / "app.py").write_text(app)
    return src


def build(src, out, **choices):
    config = ObfuscationConfig(crossfile_module_attributes=True, max_workers=1)
    for name, value in choices.items():
        setattr(config, name, value)
    ob = CrossFileOrchestrator(config)
    result = ob.obfuscate(src, out)
    assert result.success, result.errors
    return ob


def run(root, tmp_path):
    # Generated artifacts and CLI processes never see real product state.
    env = dict(os.environ, HOME=str(tmp_path), USERPROFILE=str(tmp_path))
    return subprocess.run(
        [sys.executable, str(root / "app.py")], env=env, capture_output=True, text=True
    )


def attrs(path):
    return [n.attr for n in ast.walk(ast.parse(path.read_text())) if isinstance(n, ast.Attribute)]


def runner():
    return (
        CliRunner(mix_stderr=False)
        if "mix_stderr" in inspect.signature(CliRunner).parameters
        else CliRunner()
    )


@pytest.mark.parametrize("statement", IMPORTS)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize(
    "expression,export",
    [("mod.LIMIT", "LIMIT"), ("mod.scale()", "scale"), ("mod.Settings().VALUE", "Settings")],
)
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("params_preserved", [False, True])
def test_runtime_matrix(
    tmp_path, statement, local, expression, export, locals_enabled, params_preserved
):
    app = f"{statement}\nprint({expression})\n"
    if local:
        app = f"def run():\n    {statement}\n    return {expression}\nprint(run())\n"
    src = project(tmp_path, app)
    out = tmp_path / "out"
    ob = build(
        src, out, crossfile_local_names=locals_enabled, preserve_param_names=params_preserved
    )
    original, artifact = run(src, tmp_path), run(out, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout
    emitted = ob.global_table.get_obfuscated_import("pkg.mod", export)
    assert emitted in attrs(out / "app.py")
    assert export not in attrs(out / "app.py")
    if statement.startswith("import"):
        imports = [
            n
            for n in ast.walk(ast.parse((out / "app.py").read_text()))
            if isinstance(n, ast.Import)
        ]
        assert imports[0].names[0].asname == "mod"
    if export == "Settings":
        assert "VALUE" in attrs(out / "app.py")  # Intermediate class is never a module.


def test_config_application_partial_preservation(tmp_path):
    src = project(
        tmp_path,
        "from consumer import read\nfrom nested import local\nprint(read(), local())\n",
        definitions="ROLE_READER = 2\nROLE_WRITER = 3\nROLE_OWNER = 5\n",
    )
    (src / "consumer.py").write_text(
        "from pkg import mod\ndef read():\n    return mod.ROLE_READER + mod.ROLE_WRITER\n"
    )
    (src / "nested.py").write_text(
        "def local():\n    from pkg import mod\n    return mod.ROLE_OWNER + mod.ROLE_READER\n"
    )
    out = tmp_path / "out"
    ob = build(src, out, exclude_names=ObfuscationConfig().exclude_names | {"ROLE_READER"})
    assert run(src, tmp_path).stdout == run(out, tmp_path).stdout == "5 7\n"
    assert run(out, tmp_path).returncode == 0
    assert "ROLE_READER" in attrs(out / "consumer.py")
    assert "ROLE_WRITER" not in attrs(out / "consumer.py")
    assert "ROLE_OWNER" not in attrs(out / "nested.py")
    assert ob.global_table.get_obfuscated_import("pkg.mod", "ROLE_READER") is None


NEGATIVES = [
    "if True:\n    from pkg import mod\nprint(mod.LIMIT)\n",
    "try:\n    from pkg import mod\nexcept ImportError:\n    import os as mod\nprint(mod.LIMIT)\n",
    "for item in range(1):\n    from pkg import mod\nprint(mod.LIMIT)\n",
    "print(mod.LIMIT)\nfrom pkg import mod\n",
    "from pkg import mod\nmod = object()\nprint(mod.LIMIT)\n",
    "from pkg import mod\ndel mod\nprint(mod.LIMIT)\n",
    "from pkg import mod\ndef change():\n    global mod\n    mod = object()\nprint(mod.LIMIT)\n",
    "def outer():\n    from pkg import mod\n    def change():\n        nonlocal mod\n        mod = object()\n    return mod.LIMIT\n",
    "from pkg import mod\nmod.LIMIT = 9\nprint(mod.LIMIT)\n",
    "from pkg import mod\ndel mod.LIMIT\n",
    "from pkg import mod\nmod.LIMIT += 1\n",
    "from pkg import mod\nprint(mod.factory().LIMIT)\n",
    "from pkg import mod\nprint(mod.Settings.LIMIT)\n",
    "from pkg import mod\ndef read(mod):\n    return mod.LIMIT\n",
    "from pkg import mod\ndef read():\n    mod = object()\n    return mod.LIMIT\n",
    "from pkg import mod\nprint([mod.LIMIT for mod in []])\n",
    "from pkg import mod\ntry:\n    pass\nexcept Exception as mod:\n    print(mod.LIMIT)\n",
    "from pkg import mod\ncopy = mod\nprint(copy.LIMIT)\n",
    "from .pkg import mod\nprint(mod.LIMIT)\n",
    "from pkg import mod\nexec('pass')\nprint(mod.LIMIT)\n",
]


@pytest.mark.parametrize("app", NEGATIVES)
def test_rejected_attribute_sites(tmp_path, app):
    src = project(tmp_path, app)
    out = tmp_path / "out"
    ob = build(src, out)
    assert "LIMIT" in attrs(out / "app.py")
    assert not any(e.expected == "LIMIT" for e in ob.attribute_plans["app"].edits)
    # The class/factory module export itself can be rewritten; its member cannot.


@pytest.mark.parametrize(
    "init",
    [
        "mod = 42\n",
        "def __getattr__(name):\n    return 42\n",
        "mod = 42\n__all__ = ['mod']\n",
    ],
)
def test_package_proof_rejects_conflict_and_dynamic_init(tmp_path, init):
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n", init)
    out = tmp_path / "out"
    ob = build(src, out)
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(out / "app.py")


@pytest.mark.parametrize(
    "app",
    [
        "def read():\n    return mod.LIMIT\nread()\nfrom pkg import mod\n",
        "def read():\n    return mod.LIMIT\nfrom pkg import mod\nprint(read())\n",
        "from pkg import mod\nprint([(mod := object()).LIMIT])\n",
        "from pkg import mod\nmatch object():\n    case mod:\n        print(mod.LIMIT)\n",
    ],
)
def test_deferred_order_and_modern_bindings(tmp_path, app):
    if "match " in app and sys.version_info < (3, 10):
        pytest.skip("match requires 3.10")
    src = project(tmp_path, app)
    out = tmp_path / "out"
    ob = build(src, out)
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(out / "app.py")


def test_inventory_namespace_cycles_and_mutation(tmp_path):
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n")
    (src / "pkg/__init__.py").unlink()
    ob = build(src, tmp_path / "namespace")
    assert not ob.attribute_plans["app"].edits
    (src / "pkg/__init__.py").write_text("")
    (src / "pkg/mod.py").write_text(DEFINITIONS + "import app\n")
    ob = build(src, tmp_path / "cyclic")
    assert not ob.attribute_plans["app"].edits
    (src / "pkg/mod.py").write_text(DEFINITIONS)
    (src / "mutator.py").write_text("import pkg.mod as engine\nengine.LIMIT = 9\n")
    ob = build(src, tmp_path / "mutated")
    assert not ob.attribute_plans["app"].edits


def test_workers_repeat_reset_and_serialization(tmp_path):
    src = project(tmp_path, "from pkg import mod\nprint(mod.scale())\n")
    outputs = []
    ob = None
    for workers in [1, 2, 1, 2]:
        out = tmp_path / f"out-{len(outputs)}"
        ob = build(src, out, max_workers=workers)
        outputs.append({p.relative_to(out): p.read_bytes() for p in out.rglob("*.py")})
        assert pickle.loads(pickle.dumps(ob.attribute_plans)) == ob.attribute_plans
        json.dumps(dataclasses.asdict(ob.attribute_plans["app"]))
    assert all(o == outputs[0] for o in outputs)
    ob.config.crossfile_module_attributes = False
    ob.phase1_scan(src)
    assert ob.attribute_plans == {}


@pytest.mark.parametrize("fault", ["hash", "span", "binding", "duplicate", "missing", "source"])
@pytest.mark.parametrize("workers", [1, 2])
def test_mismatch_never_publishes_partial_output(tmp_path, fault, workers):
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n")
    ob = CrossFileOrchestrator(
        ObfuscationConfig(crossfile_module_attributes=True, max_workers=workers)
    )
    ob.phase1_scan(src)
    plan = ob.attribute_plans["app"]
    edit = plan.edits[0]
    if fault == "hash":
        plan = dataclasses.replace(plan, digest="wrong")
    elif fault == "span":
        plan = dataclasses.replace(
            plan, edits=(dataclasses.replace(edit, location=(99, 0, 99, 8)),)
        )
    elif fault == "binding":
        plan = dataclasses.replace(plan, edits=(dataclasses.replace(edit, binding="wrong"),))
    elif fault == "duplicate":
        plan = dataclasses.replace(plan, edits=(edit, edit))
    elif fault == "source":
        (src / "app.py").write_text((src / "app.py").read_text() + "# changed\n")
    ob.attribute_plans["app"] = plan
    if fault == "missing":
        del ob.attribute_plans["app"]
    out = tmp_path / "out"
    out.mkdir()
    (out / "app.py").write_text("old artifact\n")
    assert ob.phase2_transform(src, out)
    assert {p.name: p.read_text() for p in out.iterdir()} == {"app.py": "old artifact\n"}
    assert not list(tmp_path.glob(".pyobfus-attributes-*"))
    if fault not in {"missing", "source"}:
        tree = ast.parse((src / "app.py").read_text())
        before = ast.dump(tree)
        with pytest.raises(ValueError):
            apply_attribute_plan(tree, (src / "app.py").read_text(), "app.py", plan)
        assert ast.dump(tree) == before


def h_risks(src, enabled):
    config = ObfuscationConfig(crossfile_module_attributes=enabled)
    report = PreflightChecker(obfuscation_config=config).check_path(src)
    return [r for r in report.risks if "attribute access through a module" in r.message]


def test_advisories_only_suppress_scheduled_sites(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\nprint(mod.LIMIT)\nif True:\n    import pkg.mod as conditional\nprint(conditional.LIMIT)\n",
    )
    assert len(h_risks(src, False)) == 1
    risks = h_risks(src, True)
    assert len(risks) == 1 and risks[0].line == 5
    candidates = discover_accesses(ast.parse((src / "app.py").read_text()), lambda n: n.module)
    assert len(candidates) == 2  # Candidate discovery still sees conditional imports.


def test_cli_yaml_precedence_check_help_init_and_singlefile_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n")
    config = tmp_path / "pyobfus.yaml"
    config.write_text("obfuscation:\n  crossfile_module_attributes: true\n")
    cli = runner()
    assert "--crossfile-module-attributes" in cli.invoke(main, ["--help"]).output
    for flag, expected in [
        (None, False),
        ("--no-crossfile-module-attributes", True),
        ("--crossfile-module-attributes", False),
    ]:
        args = [str(src), "--check", "--json", "--offline", "-c", str(config)]
        if flag:
            args.append(flag)
        result = cli.invoke(main, args)
        assert result.exit_code == 0, result.output
        payload = json.loads(result.stdout)
        assert (
            any("attribute access through a module" in r["message"] for r in payload["risks"])
            == expected
        )
    for enabled in [False, True]:
        out = tmp_path / f"single-{enabled}"
        result = cli.invoke(
            main,
            [
                str(src),
                "-o",
                str(out),
                "--no-cross-file",
                "--no-config",
                "--crossfile-module-attributes" if enabled else "--no-crossfile-module-attributes",
            ],
        )
        assert result.exit_code == 0, result.output
    assert {
        p.relative_to(tmp_path / "single-False"): p.read_bytes()
        for p in (tmp_path / "single-False").rglob("*.py")
    } == {
        p.relative_to(tmp_path / "single-True"): p.read_bytes()
        for p in (tmp_path / "single-True").rglob("*.py")
    }
    result = cli.invoke(
        main, [str(src), "--check", "--json", "--offline", "-c", str(config), "--no-cross-file"]
    )
    assert "attribute access through a module" in result.stdout
    config.unlink()
    result = cli.invoke(main, [str(src), "--init"])
    assert result.exit_code == 0, result.output
    assert "crossfile_module_attributes: false" in (src / "pyobfus.yaml").read_text()


def test_cache_signature_tracks_switch(tmp_path):
    src = project(tmp_path, "pass\n")
    cache = BuildCache(tmp_path / "out")
    config = ObfuscationConfig()
    first = cache.build_signature(src, src.rglob("*.py"), config)
    config.crossfile_module_attributes = True
    second = cache.build_signature(src, src.rglob("*.py"), config)
    assert first != second


def test_generated_trace_cli_unmap_and_mapping_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(
        tmp_path,
        "from pkg import mod\nmod.scale()\n",
        definitions="def scale():\n    raise ValueError('trace')\n",
    )
    out = tmp_path / "out"
    ob = build(src, out)
    trace = run(out, tmp_path)
    assert trace.returncode == 1
    mapping = ObfuscationMapping.from_global_table(ob.global_table)
    mapping.files = ob.file_line_maps
    path = tmp_path / "mapping.json"
    mapping.save(path)
    assert ObfuscationMapping.load(path).marker_id() == mapping.marker_id()
    assert ObfuscationMapping.merge([mapping]).global_map == mapping.global_map
    assert json.loads(mapping.to_json())["version"] == 1
    assert "scale" in mapping.unmap_text(trace.stderr)
    trace_path = tmp_path / "trace.txt"
    trace_path.write_text(trace.stderr)
    result = runner().invoke(main, [str(trace_path), "--unmap", "--mapping", str(path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "scale" in payload["unmapped_trace"]
    assert any(f.get("original_line") == 2 for f in payload["frames"])


def test_outer_function_binding_never_borrows_module_import(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\ndef outer(mod):\n    def inner():\n        return mod.LIMIT\n    return inner\n",
    )
    out = tmp_path / "out"
    ob = build(src, out)
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(out / "app.py")


def test_cli_mismatch_fails_without_mapping_or_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n")
    original = CrossFileOrchestrator.phase1_scan

    def corrupt(self, root):
        table = original(self, root)
        self.attribute_plans["app"] = dataclasses.replace(
            self.attribute_plans["app"], digest="wrong"
        )
        return table

    monkeypatch.setattr(CrossFileOrchestrator, "phase1_scan", corrupt)
    out = tmp_path / "out"
    path = tmp_path / "mapping.json"
    result = runner().invoke(
        main,
        [
            str(src),
            "-o",
            str(out),
            "--no-config",
            "--crossfile-module-attributes",
            "--save-mapping",
            str(path),
            "--incremental",
            "--json",
            "-j",
            "1",
        ],
    )
    assert result.exit_code == 1, result.output
    assert json.loads(result.stdout)["status"] == "error"
    assert not path.exists()
    assert not list(out.rglob("*.py"))
    assert not (out / ".pyobfus-cache").exists()


def test_trace_markers_match_mapping_and_restored_locations(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(
        tmp_path,
        "import pkg.mod as engine\nengine.scale()\n",
        definitions="def scale():\n    raise ValueError('trace')\n",
    )
    out = tmp_path / "out"
    path = tmp_path / "mapping.json"
    result = runner().invoke(
        main,
        [
            str(src),
            "-o",
            str(out),
            "--crossfile-module-attributes",
            "--no-config",
            "--save-mapping",
            str(path),
            "--trace-marker",
            "--json",
            "-j",
            "2",
        ],
    )
    assert result.exit_code == 0, result.output
    mapping = ObfuscationMapping.load(path)
    assert json.loads(result.stdout)["trace_marker_id"] == mapping.marker_id()
    for file in out.rglob("*.py"):
        assert f"id={mapping.marker_id()}" in file.read_text()
    trace = run(out, tmp_path)
    assert trace.returncode == 1
    restored = mapping.unmap_trace(trace.stderr)
    assert all(frame["original_line"] == 2 for frame in restored["frames"])
    assert "engine.scale()" in restored["unmapped_trace"]


def test_package_all_does_not_fabricate_module_binding(tmp_path):
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n", "__all__ = ['mod']\n")
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits


def test_proof_api_distinguishes_candidate_from_preserved_identity(tmp_path):
    from pyobfus.core.module_attributes import ModuleInventory, prove_accesses

    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n")
    config = ObfuscationConfig(crossfile_module_attributes=True)
    config.exclude_names.add("LIMIT")
    ob = CrossFileOrchestrator(config)
    ob.phase1_scan(src)
    sources = {fi.module_name: fi.path.read_text() for fi in ob.files}
    inventory = ModuleInventory(sources, lambda module, node: node.module)
    results = prove_accesses(sources["app"], "app", inventory, ob.global_table)
    assert results[0].candidate_module == results[0].proved_module == "pkg.mod"
    assert results[0].edit is None
    assert results[0].reason == "no changed export mapping"
    uncertain = prove_accesses(
        "if True:\n    from pkg import mod\nprint(mod.LIMIT)\n", "app", inventory, ob.global_table
    )
    assert uncertain[0].candidate_module == "pkg.mod"
    assert uncertain[0].proved_module is None
    assert uncertain[0].edit is None


@pytest.mark.parametrize(
    "source",
    [
        "from pkg import mod\ndef read[T]():\n    return mod.LIMIT\n",
        "from pkg import mod\ntype Payload = mod.Settings\nprint(mod.LIMIT)\n",
    ],
)
def test_modern_type_scopes_are_uncertain(tmp_path, source):
    if sys.version_info < (3, 12):
        pytest.skip("PEP 695 requires 3.12")
    src = project(tmp_path, source)
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits


def test_existing_flat_import_conflict_is_not_claimed_fixed(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\ndef unrelated():\n    from helper import mod\n    return mod\nprint(mod.LIMIT)\n",
    )
    (src / "helper.py").write_text("mod = 9\n")
    out = tmp_path / "out"
    ob = build(src, out, crossfile_local_names=False)
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(out / "app.py")
    assert h_risks(src, True)  # Limitation I remains a separate prerequisite.
