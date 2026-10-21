"""PR 2 runtime matrix and shared-plan diagnostics; all processes isolate state."""

import ast
import dataclasses
import json
from pathlib import Path

import pytest

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core.mapping import ObfuscationMapping
from pyobfus.core.module_attributes import apply_attribute_plan
from pyobfus.core.preflight import PreflightChecker
from tests.test_crossfile_module_attributes import attrs, build, project, run, runner

FORMS = [
    ("import pkg.mod", "pkg.mod.LIMIT", ""),
    ("import pkg; import pkg.mod", "pkg.mod.scale()", ""),
    ("import pkg.sub.core", "pkg.sub.core.LIMIT", ""),
    ("import pkg", "pkg.LIMIT", "from .mod import LIMIT\n"),
    ("import pkg", "pkg.LIMIT", "from .mod import LIMIT\n__all__ = ['LIMIT']\n"),
    ("import pkg", "pkg.PUBLIC", "from .mod import LIMIT as PUBLIC\n__all__ = ['PUBLIC']\n"),
    ("import pkg", "pkg.LIMIT", "LIMIT = 7\n"),
    ("from pkg import mod", "mod.LIMIT", "from .mod import LIMIT\n"),
    ("from pkg import mod", "mod.LIMIT", "def unused():\n    return 0\n"),
]


def make_form(tmp_path, statement, expression, init, local=False):
    app = f"{statement}\nprint({expression})\n"
    if local:
        app = f"def read():\n    {statement}\n    return {expression}\nprint(read())\n"
    src = project(tmp_path, app, init)
    (src / "pkg/sub").mkdir()
    (src / "pkg/sub/__init__.py").write_text("")
    (src / "pkg/sub/core.py").write_text("LIMIT = 7\n")
    return src


def risks(src, enabled=True, **choices):
    config = ObfuscationConfig(crossfile_module_attributes=enabled, **choices)
    return PreflightChecker(obfuscation_config=config).check_path(src).risks


@pytest.mark.parametrize("statement,expression,init", FORMS)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("workers", [1, 2])
def test_remaining_forms_runtime(
    tmp_path, statement, expression, init, local, locals_enabled, workers
):
    src = make_form(tmp_path, statement, expression, init, local)
    out = tmp_path / "out"
    ob = build(src, out, crossfile_local_names=locals_enabled, max_workers=workers)
    original, artifact = run(src, tmp_path), run(out, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout
    if expression == "pkg.PUBLIC":
        assert "PUBLIC" in attrs(out / "app.py")
        assert not ob.attribute_plans["app"].edits
    else:
        export = "scale" if "scale" in expression else "LIMIT"
        assert export not in attrs(out / "app.py")
        assert ob.attribute_plans["app"].edits
    assert not [
        r for r in risks(src) if "module" in r.message and r.category == "compatibility_advisory"
    ]
    # The only changed dotted segment is the exported symbol.
    if "pkg.sub.core" in expression:
        assert {"sub", "core"} <= set(attrs(out / "app.py"))


@pytest.mark.parametrize(
    "statement,path",
    [
        ("from . import mod", "pkg/entry.py"),
        ("from .. import mod", "pkg/sub/entry.py"),
        ("from .sub import core", "pkg/entry.py"),
        ("from . import mod", "pkg/__init__.py"),
        ("from .sub import core", "pkg/__init__.py"),
    ],
)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("locals_enabled", [False, True])
@pytest.mark.parametrize("workers", [1, 2])
def test_relative_runtime(tmp_path, statement, path, local, locals_enabled, workers):
    src = project(tmp_path, "import pkg\n")
    (src / "pkg/sub").mkdir()
    (src / "pkg/sub/__init__.py").write_text("")
    (src / "pkg/sub/core.py").write_text("LIMIT = 7\n")
    binding = statement.split()[-1]
    # Module-level init reads are deferred in an inert function; an arbitrary
    # executable initializer remains outside the conservative package proof.
    body = f"{statement}\ndef read():\n    return {binding}.LIMIT\n"
    if local:
        body = f"def read():\n    {statement}\n    return {binding}.LIMIT\n"
    (src / path).write_text(body)
    target = path[:-3].replace("/", ".").removesuffix(".__init__")
    (src / "app.py").write_text(f"from {target} import read\nprint(read())\n")
    out = tmp_path / "out"
    ob = build(src, out, crossfile_local_names=locals_enabled, max_workers=workers)
    original, artifact = run(src, tmp_path), run(out, tmp_path)
    assert original.returncode == artifact.returncode == 0, artifact.stderr
    assert original.stdout == artifact.stdout == "7\n"
    assert "LIMIT" not in attrs(out / path)
    assert ob.attribute_plans[path[:-3].replace("/", ".")].edits
    assert not [r for r in risks(src) if "attribute access through a module" in r.message]


UNSUPPORTED = [
    ("import pkg.mod\nprint(pkg.other.LIMIT)\n", ""),
    ("import pkg\nprint(pkg.LIMIT)\n", "if True:\n    from .mod import LIMIT\n"),
    (
        "import pkg\nprint(pkg.LIMIT)\n",
        "try:\n    from .mod import LIMIT\nexcept ImportError:\n    pass\n",
    ),
    ("import pkg.mod\nprint(pkg.mod.LIMIT)\n", "mod = 42\n"),
    ("from pkg import mod\nprint(mod.LIMIT)\n", "from . import mod\nmod = 42\n"),
    ("from pkg import mod\nprint(mod.LIMIT)\n", "__all__ = names\n"),
]


@pytest.mark.parametrize("app,init", UNSUPPORTED)
def test_unproved_paths_are_unchanged_and_advised(tmp_path, app, init):
    src = project(tmp_path, app, init)
    (src / "pkg/other.py").write_text("LIMIT = 7\n")
    out = tmp_path / "out"
    ob = build(src, out)
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(out / "app.py")
    assert [r for r in risks(src) if "attribute access through a module" in r.message]


@pytest.mark.parametrize("statement", ["from . import mod", "from .. import mod"])
def test_relative_value_shadowing(tmp_path, statement):
    src = project(tmp_path, "pass\n", "mod = 42\n")
    (src / "pkg/sub").mkdir()
    (src / "pkg/sub/__init__.py").write_text("")
    path = "pkg/sub/entry.py" if ".." in statement else "pkg/entry.py"
    (src / path).write_text(f"{statement}\nprint(mod.LIMIT)\n")
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans[path[:-3].replace("/", ".")].edits
    assert "LIMIT" in attrs(tmp_path / "out" / path)
    assert any(Path(r.file).as_posix().endswith(path) and r.line == 2 for r in risks(src))


ESCAPES = [
    ("copy = mod", "module escape"),
    ("copy, other = mod, 0", "module escape"),
    ("consume(mod)", "module escape"),
    ("return mod", "module escape"),
    ("yield mod", "module escape"),
    ("yield from mod", "module escape"),
    ("box = [mod]", "module escape"),
    ("box = {'module': mod}", "module escape"),
    ("getattr(mod, 'LIMIT')", "reflection"),
    ("hasattr(mod, 'LIMIT')", "reflection"),
    ("setattr(mod, 'LIMIT', 9)", "reflection"),
    ("delattr(mod, 'LIMIT')", "reflection"),
    ("vars(mod)", "reflection"),
    ("mod.__dict__['LIMIT']", "reflection"),
    ("mod.__dict__[key]", "reflection"),
    ("mod.LIMIT = 9", "module mutation"),
    ("del mod.LIMIT", "module mutation"),
    ("mod.LIMIT += 1", "module mutation"),
    ("sys.modules['pkg.mod'].LIMIT", "dynamic module access"),
    ("importlib.import_module('pkg.mod').LIMIT", "dynamic module access"),
]


@pytest.mark.parametrize("use,kind", ESCAPES)
def test_escape_invalidates_plan_and_reports_source_line(tmp_path, use, kind):
    app = f"import sys\nimport importlib\ndef read():\n    from pkg import mod\n    {use}\n    return mod.LIMIT\n"
    src = project(tmp_path, app)
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(tmp_path / "out/app.py")
    findings = [r for r in risks(src) if f"Detected {kind}" in r.message]
    assert len(findings) == 1 and findings[0].line == 5
    assert findings[0].severity == "medium"
    assert "exclude_names" in findings[0].suggestion
    assert "LIMIT" in findings[0].suggestion
    # No prior H candidate for the assignment-alias gap.
    if use == "copy = mod":
        (src / "app.py").write_text("from pkg import mod\ncopy = mod\nprint(copy.LIMIT)\n")
        for enabled in [False, True]:
            findings = [r for r in risks(src, enabled) if "Detected module escape" in r.message]
            assert len(findings) == 1 and findings[0].line == 2


def test_helper_import_aliases_and_no_with_target_escape(tmp_path):
    src = project(
        tmp_path,
        "from importlib import import_module as load\nimport sys as system\nprint(load('pkg.mod').LIMIT, system.modules['pkg.mod'].LIMIT)\n",
    )
    assert len([r for r in risks(src) if "Detected dynamic module access" in r.message]) == 1
    # A with-as target is not assignment-alias propagation or module consumption.
    (src / "app.py").write_text("from pkg import mod\nwith context() as mod:\n    pass\n")
    assert not [r for r in risks(src) if "Detected module escape" in r.message]


def test_preserved_reflection_and_bounded_names(tmp_path):
    src = project(tmp_path, "from pkg import mod\nprint(hasattr(mod, 'LIMIT'))\n")
    out = tmp_path / "out"
    choices = {"exclude_names": ObfuscationConfig().exclude_names | {"LIMIT"}}
    build(src, out, **choices)
    assert run(src, tmp_path).stdout == run(out, tmp_path).stdout == "True\n"
    findings = [r for r in risks(src, **choices) if "Detected reflection" in r.message]
    assert len(findings) == 1 and findings[0].severity == "info"
    assert "already preserved" in findings[0].message
    (src / "pkg/mod.py").write_text("\n".join(f"NAME_{i:02} = {i}" for i in range(15)))
    (src / "app.py").write_text("from pkg import mod\ncopy = mod\n")
    findings = [r for r in risks(src) if "Detected module escape" in r.message]
    assert "and 5 more" in findings[0].suggestion
    assert "NAME_09" in findings[0].suggestion and "NAME_10" not in findings[0].suggestion


def test_off_advice_covers_distinct_escape_and_access_sites(tmp_path):
    src = project(tmp_path, "from pkg import mod\ncopy = mod\nprint(mod.LIMIT)\n")
    legacy = [r for r in risks(src, False) if "attribute access through a module" in r.message]
    escape = [r for r in risks(src, False) if "Detected module escape" in r.message]
    assert len(legacy) == len(escape) == 1
    assert "LIMIT" in escape[0].suggestion
    assert "scale" in escape[0].suggestion


@pytest.mark.parametrize("local", [False, True])
def test_reexport_exclusion_workers_and_exact_binding_validation(tmp_path, local):
    src = make_form(
        tmp_path,
        "import pkg; import pkg.mod",
        "pkg.LIMIT + pkg.mod.scale()",
        "from .mod import LIMIT\n",
        local,
    )
    outputs = []
    for workers in [1, 2]:
        out = tmp_path / f"out-{workers}"
        ob = build(
            src,
            out,
            max_workers=workers,
            exclude_names=ObfuscationConfig().exclude_names | {"LIMIT"},
        )
        assert run(src, tmp_path).stdout == run(out, tmp_path).stdout
        outputs.append({p.relative_to(out): p.read_bytes() for p in out.rglob("*.py")})
        assert "LIMIT" in attrs(out / "app.py") and "scale" not in attrs(out / "app.py")
        plan = ob.attribute_plans["app"]
        broken = dataclasses.replace(
            plan, edits=(dataclasses.replace(plan.edits[0], binding="pkg.other"),)
        )
        tree = ast.parse((src / "app.py").read_text())
        before = ast.dump(tree)
        with pytest.raises(ValueError):
            apply_attribute_plan(tree, (src / "app.py").read_text(), "app.py", broken)
        assert ast.dump(tree) == before
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("statement,expression,init", FORMS)
def test_check_plan_and_emitted_attribute_parity(tmp_path, statement, expression, init):
    src = make_form(tmp_path, statement, expression, init)
    app = src / "app.py"
    app.write_text(
        app.read_text() + "if True:\n    import pkg.mod as uncertain\nprint(uncertain.scale())\n"
    )
    ob = build(src, tmp_path / "out")
    scheduled = {(e.location[0], e.expected) for e in ob.attribute_plans["app"].edits}
    from pyobfus.core.import_resolution import discover_accesses

    candidates = discover_accesses(ast.parse(app.read_text()), lambda n: n.module)
    unresolved = {
        (n.lineno, n.attr)
        for n, module in candidates
        if ob.global_table.get_obfuscated_import(module, n.attr)
        and (n.lineno, n.attr) not in scheduled
    }
    findings = [
        r
        for r in risks(src)
        if r.file == str(app) and "attribute access through a module" in r.message
    ]
    assert {r.line for r in findings} == {line for line, _ in unresolved}
    assert all(name in attrs(tmp_path / "out/app.py") for _, name in unresolved)
    assert all(e.emitted in attrs(tmp_path / "out/app.py") for e in ob.attribute_plans["app"].edits)


@pytest.mark.parametrize("style", ["dotted", "relative", "reexport"])
@pytest.mark.parametrize("failure", ["raise ValueError('trace')", "return object().MISSING"])
@pytest.mark.parametrize("workers", [1, 2])
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_real_generated_trace_cli(tmp_path, monkeypatch, style, workers, locals_enabled, failure):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = project(
        tmp_path,
        "import pkg.mod\npkg.mod.scale()\n",
        definitions=f"def scale():\n    {failure}\n",
    )
    if style == "relative":
        (src / "app.py").write_text("import pkg.entry\n")
        (src / "pkg/entry.py").write_text("from . import mod\nmod.scale()\n")
    if style == "reexport":
        (src / "pkg/__init__.py").write_text("from .mod import scale\n__all__ = ['scale']\n")
        (src / "app.py").write_text("import pkg\npkg.scale()\n")
    ob = build(src, tmp_path / "out", max_workers=workers, crossfile_local_names=locals_enabled)
    trace = run(tmp_path / "out", tmp_path)
    assert trace.returncode == 1
    assert (
        "ValueError: trace" if failure.startswith("raise") else "AttributeError"
    ) in trace.stderr
    mapping = ObfuscationMapping.from_global_table(ob.global_table)
    mapping.files = ob.file_line_maps
    path = tmp_path / "mapping.json"
    mapping.save(path)
    trace_path = tmp_path / "trace.txt"
    trace_path.write_text(trace.stderr)
    result = runner().invoke(main, [str(trace_path), "--unmap", "--mapping", str(path), "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert "scale" in payload["unmapped_trace"]
    assert any(f.get("original_line") == 2 for f in payload["frames"])


@pytest.mark.parametrize("statement", ["import pkg.mod", "from . import mod", "import pkg"])
@pytest.mark.parametrize("mutation", ["local-import", "global-write"])
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_i_d_interactions_reject_instead_of_fixing(tmp_path, statement, mutation, locals_enabled):
    expression = (
        "pkg.mod.LIMIT"
        if statement == "import pkg.mod"
        else ("pkg.LIMIT" if statement == "import pkg" else "mod.LIMIT")
    )
    binding = "pkg" if statement.startswith("import") else "mod"
    inner = (
        f"from extra import {binding}"
        if mutation == "local-import"
        else f"global {binding}\n    {binding} = object()"
    )
    app = f"{statement}\ndef unrelated():\n    {inner}\nprint({expression})\n"
    src = project(tmp_path, app, "from .mod import LIMIT\n" if statement == "import pkg" else "")
    (src / "extra.py").write_text("pkg = 9\nmod = 9\n")
    path = "pkg/entry.py" if statement.startswith("from .") else "app.py"
    if path != "app.py":
        (src / path).write_text(app)
        (src / "app.py").write_text("import pkg.entry\n")
    results = []
    for enabled in [False, True]:
        out = tmp_path / f"out-{enabled}"
        ob = build(
            src, out, crossfile_module_attributes=enabled, crossfile_local_names=locals_enabled
        )
        assert not ob.attribute_plans.get(
            path[:-3].replace("/", "."), dataclasses.make_dataclass("Empty", [("edits", tuple)])(())
        ).edits
        assert "LIMIT" in attrs(out / path)
        result = run(out, tmp_path)
        results.append((result.returncode, result.stdout, result.stderr.splitlines()[-1:]))
    assert results[0] == results[1]
    assert any(
        Path(r.file).as_posix().endswith(path) and "attribute access through a module" in r.message
        for r in risks(src)
    )


def test_nonmodule_attribute_does_not_borrow_export(tmp_path):
    src = project(tmp_path, "class Object:\n    LIMIT = 9\nobj = Object()\nprint(obj.LIMIT)\n")
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert run(src, tmp_path).stdout == run(tmp_path / "out", tmp_path).stdout


@pytest.mark.parametrize("local", [False, True])
def test_relative_init_definition_read(tmp_path, local):
    init = "from . import mod\nVALUE = mod.LIMIT\n"
    if local:
        init = "def read():\n    from . import mod\n    return mod.LIMIT\n"
    src = project(
        tmp_path,
        "import pkg\nprint(pkg.VALUE)\n" if not local else "import pkg\nprint(pkg.read())\n",
        init,
    )
    ob = build(src, tmp_path / "out")
    assert run(src, tmp_path).stdout == run(tmp_path / "out", tmp_path).stdout == "7\n"
    assert "LIMIT" not in attrs(tmp_path / "out/pkg/__init__.py")
    assert ob.attribute_plans["pkg.__init__"].edits


def test_static_init_class_definition(tmp_path):
    src = project(
        tmp_path, "import pkg\nprint(pkg.Settings().VALUE)\n", "class Settings:\n    VALUE = 7\n"
    )
    ob = build(src, tmp_path / "out")
    assert run(src, tmp_path).stdout == run(tmp_path / "out", tmp_path).stdout == "7\n"
    assert "Settings" not in attrs(tmp_path / "out/app.py")
    assert "VALUE" in attrs(tmp_path / "out/app.py")
    assert ob.attribute_plans["app"].edits


def test_imported_reflection_helper_alias(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\nfrom builtins import getattr as read\nprint(read(mod, 'LIMIT'))\n",
    )
    findings = [r for r in risks(src) if "Detected reflection" in r.message]
    assert len(findings) == 1 and findings[0].line == 3
    assert "LIMIT" in findings[0].suggestion and "scale" not in findings[0].suggestion


@pytest.mark.parametrize(
    "init",
    [
        "from .mod import LIMIT\nLIMIT = 9\n",
        "from .mod import LIMIT\nfrom .other import LIMIT\n",
        "__all__ = mod.__dict__\n",
        "from . import mod\ndef mutate():\n    global mod\n    mod = 42\n",
    ],
)
def test_package_competing_reexports_and_global_mutation(tmp_path, init):
    src = project(tmp_path, "import pkg.mod\nprint(pkg.mod.LIMIT)\n", init)
    (src / "pkg/other.py").write_text("LIMIT = 9\n")
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(tmp_path / "out/app.py")


@pytest.mark.parametrize("statement,expression,init", FORMS)
def test_new_forms_no_cross_file_unchanged(tmp_path, monkeypatch, statement, expression, init):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    src = make_form(tmp_path, statement, expression, init)
    outputs = []
    for enabled in [False, True]:
        out = tmp_path / f"out-{enabled}"
        result = runner().invoke(
            main,
            [
                str(src),
                "-o",
                str(out),
                "--no-config",
                "--no-cross-file",
                "--crossfile-module-attributes" if enabled else "--no-crossfile-module-attributes",
            ],
        )
        assert result.exit_code == 0, result.output
        outputs.append({p.relative_to(out): p.read_bytes() for p in out.rglob("*.py")})
    assert outputs[0] == outputs[1]


@pytest.mark.parametrize("statement,expression,init", FORMS)
@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_off_new_forms_match_main_snapshot(
    tmp_path, statement, expression, init, local, locals_enabled
):
    """Frozen main bytes; only escape advisories may extend its risk list.

    Snapshot provenance and interpreter versions are stored alongside the data.
    Missing interpreter snapshots are explicitly skipped, never guessed.
    """
    src = make_form(tmp_path, statement, expression, init, local)
    key = json.dumps([FORMS.index((statement, expression, init)), local, locals_enabled])
    assert_main_snapshot(tmp_path, src, key, locals_enabled)


def assert_main_snapshot(tmp_path, src, key, locals_enabled):
    import hashlib
    import sys
    from pathlib import Path

    snapshots = json.loads(
        (Path(__file__).parent / "fixtures/module_attributes_pr1_off.json").read_text()
    )
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    if version not in snapshots["interpreters"]:
        pytest.skip(f"No independently generated main snapshot for Python {version}")
    out = tmp_path / "out"
    build(src, out, crossfile_module_attributes=False, crossfile_local_names=locals_enabled)
    # The snapshot was generated by pyobfus 0.6.1 and every output file carries
    # the tool version in its build marker; compare everything else byte for byte.
    import re

    def _frozen(data: bytes) -> bytes:
        return re.sub(rb"(# Tool: pyobfus )\S+( - )", rb"\g<1>0.6.1\g<2>", data, count=1)

    actual = {
        p.relative_to(out).as_posix(): hashlib.sha256(_frozen(p.read_bytes())).hexdigest()
        for p in sorted(out.rglob("*.py"))
    }
    reference = snapshots["interpreters"][version][key]
    assert actual == snapshots["file_sets"][reference["files"]]
    current = [dataclasses.asdict(r) for r in risks(src, False)]
    for r in current:
        r.pop("file", None)
        # H4 adds explanations and catalog fields; the historical snapshot
        # still locks every legacy diagnostic fact and all artifact bytes.
        reason = r.pop("reason", None)
        reasons = r.pop("reasons", None)
        if reason is not None:
            from pyobfus.core.reason_codes import is_known

            assert is_known(reason) and reasons and reason == reasons[0]
            assert all(is_known(code) for code in reasons)
            assert " Reason: " in r["message"]
        r["message"] = r["message"].split(" Reason: ", 1)[0]
    additions = [r for r in current if r["message"].startswith("Detected ")]
    assert all("not automatically rewritten" in r["message"] for r in additions)
    # Output bytes remain frozen; diagnostics now cover every retained site.
    old = snapshots["risk_sets"][reference["risks"]]
    for previous in old:
        if "attribute access through a module" in previous["message"]:
            assert any(
                r["line"] == previous["line"]
                and r["category"] == previous["category"]
                and r["severity"] == previous["severity"]
                and "exclude_names" in r["suggestion"]
                for r in current
            )
        else:
            assert previous in current
    assert all(
        r["severity"] in {"medium", "info"}
        for r in current
        if r["category"] == "compatibility_advisory"
    )


OFF_CASES = ["relative-dot", "relative-parent", "relative-sub", "relative-init"] + [
    f"escape-{i}" for i in range(len(ESCAPES))
]


def make_off_case(tmp_path, case):
    src = make_form(tmp_path, "import pkg.entry", "7", "")
    if case.startswith("escape-"):
        use = ESCAPES[int(case.split("-")[1])][0]
        (src / "app.py").write_text(
            f"import sys\nimport importlib\ndef read():\n    from pkg import mod\n    {use}\n    return mod.LIMIT\n"
        )
    elif case == "relative-init":
        (src / "pkg/__init__.py").write_text("from . import mod\nVALUE = mod.LIMIT\n")
        (src / "app.py").write_text("import pkg\nprint(pkg.VALUE)\n")
    else:
        path = "pkg/entry.py"
        statement = "from . import mod"
        if case == "relative-parent":
            path = "pkg/sub/entry.py"
            statement = "from .. import mod"
        elif case == "relative-sub":
            statement = "from .sub import core"
        (src / path).write_text(f"{statement}\nprint({statement.split()[-1]}.LIMIT)\n")
        (src / "app.py").write_text(f"import {path[:-3].replace('/', '.')}\n")
    return src


@pytest.mark.parametrize("case", OFF_CASES)
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_off_relative_and_escape_main_bytes_and_advice(tmp_path, case, locals_enabled):
    src = make_off_case(tmp_path, case)
    assert_main_snapshot(tmp_path, src, json.dumps([case, locals_enabled]), locals_enabled)


def test_multiple_module_escapes_at_one_call_are_combined(tmp_path):
    src = project(tmp_path, "from pkg import mod, other\nconsume(mod, other)\n")
    (src / "pkg/other.py").write_text("OTHER = 9\n")
    findings = [r for r in risks(src) if "Detected module escape" in r.message]
    assert len(findings) == 1 and findings[0].line == 2
    assert "LIMIT" in findings[0].suggestion and "OTHER" in findings[0].suggestion


def test_module_path_mutation_does_not_hide_export_warning(tmp_path):
    src = project(tmp_path, "import pkg.mod\npkg.mod = object()\n")
    findings = [r for r in risks(src) if "Detected " in r.message]
    assert len(findings) == 1 and findings[0].line == 2
    assert findings[0].severity == "medium"
    assert "LIMIT" in findings[0].suggestion


@pytest.mark.parametrize(
    "statement,path",
    [
        ("from . import mod", "pkg/entry.py"),
        ("from .. import mod", "pkg/sub/entry.py"),
        ("from .sub import core", "pkg/entry.py"),
    ],
)
def test_relative_module_level_access(tmp_path, statement, path):
    src = make_form(
        tmp_path, "import pkg.entry" if path == "pkg/entry.py" else "import pkg.sub.entry", "7", ""
    )
    (src / path).write_text(f"{statement}\nprint({statement.split()[-1]}.LIMIT)\n")
    ob = build(src, tmp_path / "out")
    assert run(src, tmp_path).stdout == run(tmp_path / "out", tmp_path).stdout == "7\n7\n"
    assert "LIMIT" not in attrs(tmp_path / "out" / path)
    assert ob.attribute_plans[path[:-3].replace("/", ".")].edits


@pytest.mark.parametrize("use,kind", ESCAPES)
def test_check_emitted_parity_for_escapes(tmp_path, use, kind):
    from pyobfus.core.import_resolution import discover_accesses

    src = project(
        tmp_path,
        f"import sys\nimport importlib\ndef read():\n    from pkg import mod\n    {use}\n    return mod.LIMIT\n",
    )
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    candidates = discover_accesses(ast.parse((src / "app.py").read_text()), lambda n: n.module)
    unmodified = set()
    for node, module in candidates:
        if ob.global_table.get_obfuscated_import(module, node.attr):
            unmodified.add(node.lineno)
            assert node.attr in attrs(tmp_path / "out/app.py")
    findings = [
        r
        for r in risks(src)
        if r.file.endswith("app.py") and r.category == "compatibility_advisory"
    ]
    assert unmodified <= {r.line for r in findings}
    assert any(f"Detected {kind}" in r.message and r.line == 5 for r in risks(src))


@pytest.mark.parametrize(
    "statement",
    [
        "storage[0] = mod.LIMIT",
        "VALUE: helper() = mod.LIMIT",
        "VALUE: helper['key'] = mod.LIMIT",
    ],
)
def test_initializer_assignment_requires_plain_definition_target(tmp_path, statement):
    src = project(
        tmp_path,
        "import pkg\nprint(pkg.LIMIT)\n",
        f"from . import mod\nfrom .mod import LIMIT\n{statement}\n",
    )
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(tmp_path / "out/app.py")
    assert any("attribute access through a module" in r.message for r in risks(src))


@pytest.mark.parametrize("hazard", ["I", "D"])
@pytest.mark.parametrize("locals_enabled", [False, True])
def test_i_d_in_reexport_source_is_not_promised_safe(tmp_path, hazard, locals_enabled):
    init = "from .mod import LIMIT\ndef change():\n    global LIMIT\n    LIMIT = 9\n"
    app = "from pkg import change as action\nimport pkg\naction()\nprint(pkg.LIMIT)\n"
    if hazard == "I":
        init = "from .mod import LIMIT\ndef read():\n    return LIMIT\ndef unrelated():\n    from .other import OTHER as LIMIT\n    return LIMIT\n"
        app = "import pkg\nprint(pkg.LIMIT, pkg.read())\n"
    src = project(tmp_path, app, init)
    (src / "pkg/other.py").write_text("OTHER = 9\n")
    original = run(src, tmp_path)
    assert original.returncode == 0
    results = []
    for enabled in [False, True]:
        out = tmp_path / f"out-{enabled}"
        ob = build(
            src, out, crossfile_module_attributes=enabled, crossfile_local_names=locals_enabled
        )
        assert not ob.attribute_plans.get("app") or not ob.attribute_plans["app"].edits
        assert "LIMIT" in attrs(out / "app.py")
        result = run(out, tmp_path)
        results.append((result.returncode, result.stdout, result.stderr.splitlines()[-1:]))
    assert results[0] == results[1]
    assert any("attribute access through a module" in r.message for r in risks(src))


def test_same_module_import_in_child_scope_is_not_flat_symbol_conflict(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\ndef read():\n    from pkg import mod\n    return mod.LIMIT\nprint(mod.LIMIT, read())\n",
    )
    ob = build(src, tmp_path / "out")
    assert len(ob.attribute_plans["app"].edits) == 2
    assert run(src, tmp_path).stdout == run(tmp_path / "out", tmp_path).stdout == "7 7\n"
    assert not [r for r in risks(src) if "attribute access through a module" in r.message]


def test_shadowed_reflection_helper_is_unknown_consumption(tmp_path):
    src = project(
        tmp_path,
        "def getattr(module, key):\n    return module.scale()\nfrom pkg import mod\nprint(getattr(mod, 'LIMIT'))\n",
    )
    findings = [r for r in risks(src) if "Detected module escape" in r.message]
    assert len(findings) == 1 and findings[0].line == 4
    assert "scale" in findings[0].suggestion
    assert not [r for r in risks(src) if "Detected reflection" in r.message]
    build(
        src,
        tmp_path / "out",
        exclude_names=ObfuscationConfig().exclude_names | {"LIMIT", "scale", "Settings"},
    )
    assert run(src, tmp_path).stdout == run(tmp_path / "out", tmp_path).stdout == "14\n"


@pytest.mark.parametrize("definition", ["LIMIT = 99\n", "OTHER = 99\n"])
def test_root_file_package_collision_is_unproved(tmp_path, definition):
    src = project(tmp_path, "import pkg\nprint(pkg.LIMIT)\n", "LIMIT = 7\n")
    (src / "pkg.py").write_text(definition)
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(tmp_path / "out/app.py")
    assert any("attribute access through a module" in r.message for r in risks(src))
    build(src, tmp_path / "preserved", exclude_names=ObfuscationConfig().exclude_names | {"LIMIT"})
    assert run(src, tmp_path).stdout == run(tmp_path / "preserved", tmp_path).stdout == "7\n"


@pytest.mark.parametrize("reexport", [False, True])
def test_all_slot_supplied_by_runtime_injection_is_not_an_emitted_binding(tmp_path, reexport):
    src = project(
        tmp_path,
        "from pkg import mod\nprint(mod.LIMIT)\n",
        definitions="__all__ = ['LIMIT']\nglobals()['LIMIT'] = 7\n",
    )
    if reexport:
        (src / "pkg/__init__.py").write_text("from .mod import LIMIT\n")
        (src / "app.py").write_text("import pkg\nprint(pkg.LIMIT)\n")
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(tmp_path / "out/app.py")
    assert any("attribute access through a module" in r.message for r in risks(src))
    build(src, tmp_path / "preserved", exclude_names=ObfuscationConfig().exclude_names | {"LIMIT"})
    assert run(src, tmp_path).stdout == run(tmp_path / "preserved", tmp_path).stdout == "7\n"


def test_known_enum_injection_does_not_become_h_support(tmp_path):
    import sys

    if sys.version_info < (3, 11):
        pytest.skip("enum.global_enum requires Python 3.11")
    src = project(
        tmp_path,
        "from pkg import mod\nprint(mod.ROLE)\n",
        definitions="from enum import global_enum, IntEnum\n__all__ = ['ROLE']\n@global_enum\nclass Flags(IntEnum):\n    ROLE = 7\n",
    )
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "ROLE" in attrs(tmp_path / "out/app.py")
    original, artifact = run(src, tmp_path), run(tmp_path / "out", tmp_path)
    assert original.returncode == artifact.returncode == 0
    assert original.stdout == artifact.stdout


def test_selected_stdlib_filename_does_not_prove_builtin_identity(tmp_path):
    src = project(tmp_path, "import sys\nprint(sys.version)\n")
    (src / "sys.py").write_text("version = 'project value'\n")
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "version" in attrs(tmp_path / "out/app.py")
    assert run(src, tmp_path).stdout == run(tmp_path / "out", tmp_path).stdout


def test_conditional_symbol_reexport_in_regular_module_is_unproved(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\nprint(mod.LIMIT)\n",
        definitions="if True:\n    from .other import LIMIT\n",
    )
    (src / "pkg/other.py").write_text("LIMIT = 7\n")
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    assert "LIMIT" in attrs(tmp_path / "out/app.py")
    assert any("attribute access through a module" in r.message for r in risks(src))


@pytest.mark.parametrize(
    "expression", ["sys.modules[KEY].LIMIT", "importlib.import_module(KEY).LIMIT"]
)
def test_computed_dynamic_target_keeps_boundary_advice(tmp_path, expression):
    src = project(
        tmp_path,
        f"import sys\nimport importlib\nfrom pkg import mod\nKEY = 'pkg.mod'\nprint({expression}, mod.LIMIT)\n",
    )
    ob = build(src, tmp_path / "out")
    assert not ob.attribute_plans["app"].edits
    findings = [
        r for r in risks(src) if "Detected dynamic module access (unknown target)" in r.message
    ]
    assert len(findings) == 1 and findings[0].line == 5
    assert "LIMIT" in findings[0].suggestion and "scale" in findings[0].suggestion
    assert "boundary" in findings[0].suggestion
    assert any(
        "Detected dynamic module access (unknown target)" in r.message for r in risks(src, False)
    )


def test_computed_registry_mutation_cannot_leave_stale_direct_read(tmp_path):
    src = project(
        tmp_path,
        "from pkg import mod\nprint(mod.LIMIT)\n",
        definitions="import sys\nLIMIT = 7\nsys.modules[__name__].LIMIT = 9\n",
    )
    outputs = []
    for enabled in [False, True]:
        out = tmp_path / f"out-{enabled}"
        ob = build(src, out, crossfile_module_attributes=enabled)
        assert not ob.attribute_plans.get("app") or not ob.attribute_plans["app"].edits
        outputs.append(run(out, tmp_path).stdout)
    assert outputs == [run(src, tmp_path).stdout] * 2 == ["9\n", "9\n"]
