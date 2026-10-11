"""PR 3: default rollout and retained-attribute diagnostic coverage."""

import ast
import json
import sys
from pathlib import Path

import pytest

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.cache import BuildCache
from pyobfus.core.export_detector import ReExportSource
from pyobfus.core.import_resolution import discover_uncertain_accesses
from pyobfus.core.mapping import ObfuscationMapping
from pyobfus.core.module_attributes import ModuleInventory
from pyobfus.core.orchestrator import CrossFileOrchestrator
from pyobfus.core.preflight import PreflightChecker
from tests.test_crossfile_module_attributes import project, run, runner

UNCERTAIN = [
    "import importlib\ndef read():\n    m = importlib.import_module('pkg.mod')\n    return m.LIMIT\nprint(read())\n",
    "from importlib import import_module as load\ndef read():\n    m = load('pkg.mod')\n    return m.LIMIT\nprint(read())\n",
    "import pkg.mod\ndef read():\n    copy = pkg.mod\n    return copy.LIMIT\nprint(read())\n",
    "import pkg.mod as mod\nv = mod.LIMIT\ndel mod\n",
    "from pkg import mod\nv = mod.LIMIT\nfor mod in []:\n    pass\n",
    "import pkg.mod as mod\nimport os as mod\nprint(mod.LIMIT)\n",
    "pkg = object()\nimport pkg.mod\nprint(pkg.mod.LIMIT)\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\ndel pkg\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\nfor pkg in []:\n    pass\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\ntry:\n    pass\nexcept Exception as pkg:\n    pass\n",
    "def read():\n    pkg = object()\n    import pkg.mod\n    return pkg.mod.LIMIT\nprint(read())\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\nwith context() as pkg:\n    pass\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\npkg: object = object()\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\npkg += object()\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\n(pkg := object())\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\nmatch object():\n    case pkg:\n        pass\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\nmatch {}:\n    case {**pkg}:\n        pass\n",
    "import pkg.mod\nv = pkg.mod.LIMIT\nmatch []:\n    case [*pkg]:\n        pass\n",
    "import importlib\nm = importlib.import_module('pkg.mod')\nprint(m.LIMIT)\n",
    "from importlib import import_module as load\nm: object = load('pkg.mod')\nprint(m.LIMIT)\n",
    "import importlib as loader\nm = loader.import_module('pkg.mod')\nprint(m.LIMIT, m.LIMIT)\nprint(m.LIMIT)\n",
]

# Scan of module-member routes: relative/absolute imports, import aliases,
# implicit package roots, package exports, assignment aliases and re-exports.
MEMBER_CHAINS = [
    ("", "from . import core\n", "import pkg.a", "pkg.a.core.LIMIT"),
    ("", "from . import core\n", "from pkg import a", "a.core.LIMIT"),
    ("", "from . import core\n", "import pkg.a as a", "a.core.LIMIT"),
    ("", "from . import core as engine\n", "import pkg.a", "pkg.a.engine.LIMIT"),
    ("", "import pkg.core as engine\n", "from pkg import a", "a.engine.LIMIT"),
    ("", "import pkg.core\n", "import pkg.a", "pkg.a.pkg.core.LIMIT"),
    ("from . import a\n", "from . import core\n", "import pkg", "pkg.a.core.LIMIT"),
    ("from . import a as bridge\n", "from . import core\n", "import pkg", "pkg.bridge.core.LIMIT"),
    ("from .a import engine\n", "from . import core as engine\n", "import pkg", "pkg.engine.LIMIT"),
    ("", "from . import core\nengine = core\n", "import pkg.a", "pkg.a.engine.LIMIT"),
    ("", "from .b import engine\n", "import pkg.a", "pkg.a.engine.LIMIT"),
    (
        "",
        "from . import core as engine\nfrom .b import engine\n",
        "import pkg.a",
        "pkg.a.engine.LIMIT",
    ),
]


def assert_retained_accesses_have_advice(src, out, ob):
    """Compare actual emitted AST/line maps with check positions for every H fixture.

    The broader candidate observer is diagnostic only; strict edit plans are
    deliberately not used to decide whether an output access was rewritten.
    """
    config = ObfuscationConfig(**vars(ob.config))
    findings = PreflightChecker(obfuscation_config=config).check_path(src).risks
    advised = {
        (Path(r.file).relative_to(src).as_posix(), r.line)
        for r in findings
        if r.category == "compatibility_advisory"
    }
    mapping = ObfuscationMapping.from_global_table(ob.global_table)
    mapping.files = ob.file_line_maps
    retained = set()
    index = {fi.module_name: fi for fi in ob.files}
    inventory = ob.attribute_inventory or ModuleInventory(
        {fi.module_name: fi.path.read_text() for fi in ob.files},
        lambda module, node: ob._resolve_source_module(
            index[module], ReExportSource(node.module, node.level, "")
        ),
        ob.global_table,
    )
    for fi in ob.files:
        relative = fi.relative_path.as_posix()
        original = ast.parse(fi.path.read_text())
        candidates = discover_uncertain_accesses(
            original,
            lambda node: ob._resolve_source_module(fi, ReExportSource(node.module, node.level, "")),
            inventory.candidate_member,
        )
        # Direct dynamic expressions are observed by the existing hazard API.
        if ob.attribute_inventory is not None:
            for hazard in ob.attribute_inventory.hazards[fi.module_name]:
                for node in ast.walk(original):
                    if (
                        isinstance(node, ast.Attribute)
                        and (node.lineno, node.col_offset) == hazard.location
                        and node.attr in hazard.names
                    ):
                        candidates.append((node, hazard.module))
        unchanged = set()
        for node in ast.walk(ast.parse((out / fi.relative_path).read_text())):
            if isinstance(node, ast.Attribute):
                location = mapping.resolve_location(relative, node.lineno)
                if location is not None:
                    unchanged.add((location.line, node.attr))
        for node, module in candidates:
            emitted = ob.global_table.get_obfuscated_import(module, node.attr)
            if emitted and emitted != node.attr and (node.lineno, node.attr) in unchanged:
                retained.add((relative, node.lineno))
    assert (
        retained <= advised
    ), f"Retained renamed project attributes without advice: {retained - advised}"


@pytest.mark.parametrize("init,bridge,statement,expression", MEMBER_CHAINS)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("workers", [1, 4])
def test_imported_module_member_chains(
    tmp_path,
    monkeypatch,
    init,
    bridge,
    statement,
    expression,
    local,
    enabled,
    locals_enabled,
    workers,
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    app = f"{statement}\nprint({expression}, {expression})\nprint({expression})\n"
    if local:
        app = f"def read():\n    {statement}\n    print({expression}, {expression})\n    print({expression})\nread()\n"
    src = project(tmp_path, app, init=init)
    (src / "pkg/mod.py").rename(src / "pkg/core.py")
    (src / "pkg/a.py").write_text(bridge)
    (src / "pkg/b.py").write_text("from . import core as engine\n")
    assert run(src, tmp_path).stdout == "7 7\n7\n"
    ob = CrossFileOrchestrator(
        ObfuscationConfig(
            crossfile_module_attributes=enabled,
            crossfile_local_names=locals_enabled,
            max_workers=workers,
        )
    )
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    assert ob.global_table.get_obfuscated_import("pkg.core", "LIMIT") != "LIMIT"
    assert (
        sum(
            isinstance(n, ast.Attribute) and n.attr == "LIMIT"
            for n in ast.walk(ast.parse((out / "app.py").read_text()))
        )
        == 3
    )  # Member observations never supply a rewrite.
    assert_retained_accesses_have_advice(src, out, ob)
    flag = "--crossfile-module-attributes" if enabled else "--no-crossfile-module-attributes"
    checked = runner().invoke(
        main, [str(src), "--check", "--offline", "--no-config", "--json", flag]
    )
    assert checked.exit_code in {0, 1}, checked.output
    findings = [
        r
        for r in json.loads(checked.stdout)["risks"]
        if "module identity cannot be proved" in r["message"] and "pkg.core.LIMIT" in r["message"]
    ]
    lines = {
        n.lineno
        for n in ast.walk(ast.parse(app))
        if isinstance(n, ast.Attribute) and n.attr == "LIMIT"
    }
    assert {r["line"] for r in findings} == lines
    assert len(findings) == len(lines)
    assert all(
        r["category"] == "compatibility_advisory" and r["severity"] == "medium" for r in findings
    )
    assert all(
        "from pkg.core import LIMIT" in r["suggestion"] and "exclude_names" in r["suggestion"]
        for r in findings
    )


def test_module_member_candidates_terminate_cycles_and_ignore_external_values():
    inventory = ModuleInventory(
        {
            "a": "from b import link\n",
            "b": "from a import link\n",
            "c": "import os as link\nlink = 7\n",
            "d": "import d\nlink = d.link.link\n",
        },
        lambda module, node: node.module,
    )
    assert inventory.candidate_member("a", "link") == set()
    assert inventory.candidate_member("c", "link") == set()
    assert inventory.candidate_member("d", "link") == set()


@pytest.mark.parametrize("app", UNCERTAIN)
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("workers", [1, 2])
def test_uncertain_candidates_check_and_build(
    tmp_path, monkeypatch, app, enabled, locals_enabled, workers
):
    if "match " in app and sys.version_info < (3, 10):
        pytest.skip("match requires Python 3.10")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(tmp_path, app)
    ob = CrossFileOrchestrator(
        ObfuscationConfig(
            crossfile_module_attributes=enabled,
            crossfile_local_names=locals_enabled,
            max_workers=workers,
        )
    )
    out = tmp_path / "out"
    result = ob.obfuscate(src, out)
    assert result.success, result.errors
    assert_retained_accesses_have_advice(src, out, ob)
    flag = "--crossfile-module-attributes" if enabled else "--no-crossfile-module-attributes"
    checked = runner().invoke(
        main, [str(src), "--check", "--offline", "--no-config", "--json", flag]
    )
    assert checked.exit_code in {0, 1}, checked.output
    findings = [
        r
        for r in json.loads(checked.stdout)["risks"]
        if "module identity cannot be proved" in r["message"]
    ]
    lines = {
        n.lineno
        for n in ast.walk(ast.parse(app))
        if isinstance(n, ast.Attribute) and n.attr == "LIMIT"
    }
    assert {r["line"] for r in findings} == lines
    assert len(findings) == len(lines)
    assert all(r["severity"] == "medium" and "exclude_names" in r["suggestion"] for r in findings)
    assert all("from pkg.mod import LIMIT" in r["suggestion"] for r in findings)
    single = PreflightChecker(obfuscation_config=ob.config).check_path(src / "app.py")
    assert not any("module identity cannot be proved" in r.message for r in single.risks)


@pytest.mark.parametrize(
    "statement", ["from pkg import mod", "import pkg.mod as mod", "import pkg.mod"]
)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("workers", [1, 2])
def test_default_runtime_and_check(tmp_path, statement, local, locals_enabled, workers):
    expression = "pkg.mod.scale()" if statement == "import pkg.mod" else "mod.scale()"
    app = f"{statement}\nprint({expression})\n"
    if local:
        app = f"def read():\n    {statement}\n    return {expression}\nprint(read())\n"
    src = project(tmp_path, app)
    ob = CrossFileOrchestrator(
        ObfuscationConfig(crossfile_local_names=locals_enabled, max_workers=workers)
    )
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    original, artifact = run(src, tmp_path), run(out, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout
    assert not any(
        r.category == "compatibility_advisory" for r in PreflightChecker().check_path(src).risks
    )


def test_old_default_incremental_output_is_not_reused(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(tmp_path, "from pkg import mod\nprint(mod.LIMIT)\n")
    out = tmp_path / "out"
    args = [str(src), "-o", str(out), "--no-config", "--incremental", "--json"]
    first = runner().invoke(main, args + ["--no-crossfile-module-attributes"])
    assert first.exit_code == 0, first.output
    before = (out / "app.py").read_bytes()
    cache = BuildCache(out)
    assert cache.load_manifest()["signature"]["config"]["crossfile_module_attributes"] is False
    second = runner().invoke(main, args)
    assert second.exit_code == 0, second.output
    assert (out / "app.py").read_bytes() != before
    assert run(out, tmp_path).returncode == 0
    assert cache.load_manifest()["signature"]["config"]["crossfile_module_attributes"] is True
    implicit = cache.build_signature(src, src.rglob("*.py"), ObfuscationConfig())
    explicit = cache.build_signature(
        src, src.rglob("*.py"), ObfuscationConfig(crossfile_module_attributes=True)
    )
    assert implicit == explicit


@pytest.mark.parametrize(
    "app",
    [
        "import pkg.mod\nprint(pkg.mod.LIMIT)\ndel pkg\n",
        "import pkg.mod\nprint(pkg.mod.LIMIT)\nfor pkg in []:\n    pass\n",
        "import pkg.mod\nprint(pkg.mod.LIMIT)\ntry:\n    pass\nexcept Exception as pkg:\n    pass\n",
        "def read():\n    pkg = object()\n    import pkg.mod\n    return pkg.mod.LIMIT\nprint(read())\n",
        "import importlib\nm = importlib.import_module('pkg.mod')\nprint(m.LIMIT)\n",
    ],
)
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_uncertainty_preserved_name_recovery(tmp_path, app, locals_enabled):
    src = project(tmp_path, app)
    out = tmp_path / "out"
    config = ObfuscationConfig(crossfile_local_names=locals_enabled, max_workers=2)
    config.exclude_names.add("LIMIT")
    ob = CrossFileOrchestrator(config)
    assert ob.obfuscate(src, out).success
    original, artifact = run(src, tmp_path), run(out, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout == "7\n"


def test_yaml_false_restores_cli_disabled_bytes(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(tmp_path, "from pkg import mod\nprint(mod.scale())\n")
    config = tmp_path / "config.yaml"
    config.write_text("obfuscation:\n  crossfile_module_attributes: false\n")
    outputs = []
    for mode, flags in [
        ("yaml", ["--config", str(config)]),
        ("cli", ["--no-config", "--no-crossfile-module-attributes"]),
    ]:
        out = tmp_path / mode
        result = runner().invoke(main, [str(src), "-o", str(out), *flags])
        assert result.exit_code == 0, result.output
        outputs.append({p.relative_to(out): p.read_bytes() for p in out.rglob("*.py")})
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize(
    "use,kind",
    [
        ("mod.LIMIT = mod.LIMIT", "module mutation"),
        ("copy = mod; print(mod.LIMIT)", "module escape"),
        ("getattr(mod, 'LIMIT'); print(mod.LIMIT)", "reflection"),
    ],
)
def test_hazard_and_h_advice_deduplicate_same_export_line(tmp_path, enabled, use, kind):
    src = project(tmp_path, f"from pkg import mod\n{use}\n")
    findings = (
        PreflightChecker(obfuscation_config=ObfuscationConfig(crossfile_module_attributes=enabled))
        .check_path(src)
        .risks
    )
    relevant = [r for r in findings if r.category == "compatibility_advisory"]
    assert len(relevant) == 1 and relevant[0].line == 2
    assert kind in relevant[0].message
    assert "LIMIT" in relevant[0].suggestion


@pytest.mark.parametrize("preset", ObfuscationConfig.list_presets())
def test_all_preset_factories_enable_default(preset):
    assert ObfuscationConfig.get_preset(preset).crossfile_module_attributes is True


@pytest.mark.parametrize("preset", sorted(ObfuscationConfig.FRAMEWORK_PRESETS))
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("workers", [1, 2])
def test_framework_presets_default_module_attribute_runtime(
    tmp_path, preset, locals_enabled, workers
):
    src = project(tmp_path, "import pkg.mod\nprint(pkg.mod.LIMIT)\n")
    config = ObfuscationConfig.get_preset(preset)
    config.crossfile_local_names = locals_enabled
    config.max_workers = workers
    ob = CrossFileOrchestrator(config)
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    original, artifact = run(src, tmp_path), run(out, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout == "7\n"
    assert ob.attribute_plans["app"].edits


PREFIXES = [
    'import sys\nsys.path.insert(0, "/opt")\n',
    "import logging\nlog = logging.getLogger(__name__)\n",
    "import logging\nlogging.basicConfig()\n",
    "from helper import setup\nsetup()\n",
]
PREFIX_IMPORTS = [
    ("from pkg import mod", "mod.LIMIT", "app.py"),
    ("import pkg.mod as mod", "mod.LIMIT", "app.py"),
    ("import pkg.mod", "pkg.mod.LIMIT", "app.py"),
    ("from . import mod", "mod.LIMIT", "pkg/reader.py"),
]


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("statement,expression,relative", PREFIX_IMPORTS)
@pytest.mark.parametrize("form", ["function", "nested", "async", "lambda", "default", "decorator"])
def test_opaque_prefix_before_stable_global_import(
    tmp_path, monkeypatch, prefix, statement, expression, relative, form
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    bodies = {
        "function": f"def read():\n    return {expression}\nprint(read())\n",
        "nested": f"def read():\n    def inner():\n        return {expression}\n    return inner()\nprint(read())\n",
        "async": f"import asyncio\nasync def read():\n    return {expression}\nprint(asyncio.run(read()))\n",
        "lambda": f"read = lambda: {expression}\nprint(read())\n",
        "default": f"def read(value={expression}):\n    return value\nprint(read())\n",
        "decorator": f"def decorate(value):\n    return lambda function: function\n@decorate({expression})\ndef read():\n    return {expression}\nprint(read())\n",
    }
    app = prefix + statement + "\n" + bodies[form]
    src = project(tmp_path, app if relative == "app.py" else "import pkg.reader\n")
    (src / relative).write_text(app)
    (src / "helper.py").write_text("def setup():\n    return 1\n")
    ob = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    original, artifact = run(src, tmp_path), run(out, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout == "7\n"
    assert not any(
        isinstance(n, ast.Attribute) and n.attr == "LIMIT"
        for n in ast.walk(ast.parse((out / relative).read_text()))
    )
    assert_retained_accesses_have_advice(src, out, ob)
    checked = runner().invoke(main, [str(src), "--check", "--json", "--offline", "--no-config"])
    assert checked.exit_code in {0, 1}, checked.output
    assert not any(
        "module identity cannot be proved" in r["message"]
        for r in json.loads(checked.stdout)["risks"]
    )


@pytest.mark.parametrize(
    "body",
    [
        "def read():\n    return mod.LIMIT\nfrom pkg import mod\nprint(read())\n",
        "read = lambda: mod.LIMIT\nfrom pkg import mod\nprint(read())\n",
        "def outer():\n    def read():\n        return mod.LIMIT\n    return read()\nfrom pkg import mod\nprint(outer())\n",
        "from pkg import mod\ndef read():\n    return mod.LIMIT\ndef replace():\n    global mod\n    mod = None\nprint(read())\n",
        "from pkg import mod\ndef read():\n    return mod.LIMIT\nprint(read())\nmod = None\n",
        "from pkg import mod\ndef read():\n    return mod.LIMIT\nprint(read())\ndel mod\n",
        "from pkg import mod\nclass Reader:\n    value = mod.LIMIT\nprint(Reader.value)\n",
        "from pkg import mod\nread = lambda mod: mod.LIMIT\nprint(read(mod))\n",
    ],
)
def test_opaque_prefix_does_not_relax_order_or_competing_binding_guards(
    tmp_path, monkeypatch, body
):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(tmp_path, PREFIXES[0] + body)
    ob = CrossFileOrchestrator(ObfuscationConfig(max_workers=1))
    out = tmp_path / "out"
    assert ob.obfuscate(src, out).success
    assert any(
        isinstance(n, ast.Attribute) and n.attr == "LIMIT"
        for n in ast.walk(ast.parse((out / "app.py").read_text()))
    )
    assert_retained_accesses_have_advice(src, out, ob)
    checked = runner().invoke(main, [str(src), "--check", "--json", "--offline", "--no-config"])
    assert checked.exit_code in {0, 1}, checked.output
    risks = json.loads(checked.stdout)["risks"]
    assert any(r["category"] == "compatibility_advisory" for r in risks)
    # Follow the advisory's preservation recovery for runtime equality; the
    # rejected proof itself deliberately leaves the renamed export access intact.
    ob.config.exclude_names.add("LIMIT")
    recovered = tmp_path / "recovered"
    assert ob.obfuscate(src, recovered).success
    original, artifact = run(src, tmp_path), run(recovered, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout == "7\n"
