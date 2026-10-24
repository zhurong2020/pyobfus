"""Slice A tests: crossfile_opacity preflight + stable binding plan.

Synthetic sources and config stubs only. No license file is read and no user
code runs, so these pass with the caller's normal HOME.
"""

from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from pyobfus.core.crossfile_opacity import (
    REASON_ASYNC,
    REASON_DECORATED,
    REASON_DELETED,
    REASON_DUPLICATE_BINDING,
    REASON_GENERATOR,
    REASON_GLOBAL_WRITE,
    REASON_NESTED_DEFINITION,
    REASON_REASSIGNED,
    REASON_SHADOWED_BY_IMPORT,
    REASON_TYPE_PARAMS,
    CrossfileOpacityError,
    import_identity,
    plan_module_targets,
    preflight,
)


def _valid_config(**overrides):
    """A config stub inside the supported envelope; override to break it."""
    base = dict(
        level="pro",
        opacity_config="opacity.toml",
        selective_opacity=True,
        bind_key_env="APP_L3_KEY",
        max_workers=1,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _run_preflight(
    config, *, cross_file=True, input_is_dir=True, incremental=False, module_names=None
):
    preflight(
        config,
        cross_file=cross_file,
        input_is_dir=input_is_dir,
        incremental=incremental,
        module_names=module_names,
    )


# --------------------------------------------------------------------------
# import_identity
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module,identity",
    [
        ("calculator", "calculator"),
        ("pkg.a", "pkg.a"),
        ("pkg.__init__", "pkg"),
        ("pkg.sub.__init__", "pkg.sub"),
        ("__init__", ""),
    ],
)
def test_import_identity(module, identity):
    assert import_identity(module) == identity


# --------------------------------------------------------------------------
# preflight: happy path + per-reason failures
# --------------------------------------------------------------------------


def test_preflight_accepts_supported_envelope():
    _run_preflight(_valid_config())  # must not raise


def test_preflight_requires_pro_level():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(level="community"))
    assert any("Pro" in r for r in exc.value.reasons)


def test_preflight_requires_directory_input():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(), input_is_dir=False)
    assert any("directory" in r for r in exc.value.reasons)


def test_preflight_rejects_no_cross_file():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(), cross_file=False)
    assert any("cross-file" in r for r in exc.value.reasons)


def test_preflight_requires_toml_selection():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(opacity_config=None))
    assert any("opacity-config" in r for r in exc.value.reasons)


def test_preflight_rejects_hand_markers_without_toml():
    # selective_opacity set but no opacity_config == hand-written marker path.
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(opacity_config=None, selective_opacity=True))
    assert any("opacity-config" in r for r in exc.value.reasons)


def test_preflight_requires_bind_key_env():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(bind_key_env=None))
    assert any("bind-key-env" in r for r in exc.value.reasons)


@pytest.mark.parametrize("workers", [None, 0, 2, 4])
def test_preflight_requires_serial(workers):
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(max_workers=workers))
    assert any("jobs 1" in r for r in exc.value.reasons)


def test_preflight_rejects_incremental():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(), incremental=True)
    assert any("incremental" in r for r in exc.value.reasons)


@pytest.mark.parametrize(
    "field", ["seal_code", "vault", "scrub_traceback", "fingerprint", "embed_data"]
)
def test_preflight_rejects_other_fusion_fields(field):
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(
            _valid_config(**{field: "x" if field in {"fingerprint", "embed_data"} else True})
        )
    assert any(field in r for r in exc.value.reasons)


@pytest.mark.parametrize("field", ["bind_device_id", "expire_warn_days"])
def test_preflight_rejects_dependency_fields(field):
    value = 5 if field == "expire_warn_days" else "machine-xyz"
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(**{field: value}))
    assert any(field in r for r in exc.value.reasons)


@pytest.mark.parametrize(
    "field,value",
    [("period_max_runs", 0), ("fingerprint", ""), ("requires_os", "")],
)
def test_preflight_rejects_nondefault_falsy_fields(field, value):
    # Falsy but non-default (all three default to None) must not slip through
    # the truthiness gap.
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(**{field: value}))
    assert any(field in r for r in exc.value.reasons)


def test_preflight_rejects_import_identity_collision():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(_valid_config(), module_names=["pkg", "pkg.__init__", "pkg.a"])
    assert any("import identity" in r for r in exc.value.reasons)


def test_preflight_allows_distinct_modules():
    _run_preflight(_valid_config(), module_names=["pkg.__init__", "pkg.a", "pkg.sub.b"])


def test_preflight_collects_all_reasons_at_once():
    with pytest.raises(CrossfileOpacityError) as exc:
        _run_preflight(
            _valid_config(level="community", bind_key_env=None, max_workers=2),
            input_is_dir=False,
        )
    assert len(exc.value.reasons) >= 4


@pytest.mark.skipif(sys.implementation.name != "cpython", reason="CPython-only assertion")
def test_preflight_accepts_cpython_build_interpreter():
    # On CPython the interpreter check must not contribute a reason.
    _run_preflight(_valid_config())


# --------------------------------------------------------------------------
# plan_module_targets: selection + rejection reasons
# --------------------------------------------------------------------------


def test_plain_function_is_selected():
    plan = plan_module_targets("m", "def f(x):\n    return x + 1\n")
    assert [b.name for b in plan.selected] == ["f"]
    assert plan.rejected == ()
    assert plan.selected[0].source_digest


def test_lambda_and_comprehension_in_body_do_not_reject():
    src = "def f(xs):\n    g = lambda y: y * 2\n    return [g(x) for x in xs]\n"
    plan = plan_module_targets("m", src)
    assert [b.name for b in plan.selected] == ["f"]


def _reason_for(src, name):
    plan = plan_module_targets("m", src)
    return {r.name: r.reason for r in plan.rejected}.get(name)


def test_reject_async():
    assert _reason_for("async def f():\n    return 1\n", "f") == REASON_ASYNC


def test_reject_decorated():
    assert (
        _reason_for("import functools\n@functools.cache\ndef f():\n    return 1\n", "f")
        == REASON_DECORATED
    )


def test_reject_generator():
    assert _reason_for("def f():\n    yield 1\n", "f") == REASON_GENERATOR


def test_reject_yield_from():
    assert _reason_for("def f(xs):\n    yield from xs\n", "f") == REASON_GENERATOR


def test_genexp_in_body_is_not_a_generator_function():
    plan = plan_module_targets("m", "def f(xs):\n    return sum(x for x in xs)\n")
    assert [b.name for b in plan.selected] == ["f"]


def test_reject_nested_def():
    assert (
        _reason_for("def f():\n    def g():\n        return 1\n    return g\n", "f")
        == REASON_NESTED_DEFINITION
    )


def test_reject_nested_class():
    assert (
        _reason_for("def f():\n    class C:\n        pass\n    return C\n", "f")
        == REASON_NESTED_DEFINITION
    )


def test_reject_duplicate_binding():
    src = "def f():\n    return 1\ndef f():\n    return 2\n"
    plan = plan_module_targets("m", src)
    assert plan.selected == ()
    assert all(r.reason == REASON_DUPLICATE_BINDING for r in plan.rejected)


def test_reject_reassigned():
    assert _reason_for("def f():\n    return 1\nf = None\n", "f") == REASON_REASSIGNED


def test_reject_deleted():
    assert _reason_for("def f():\n    return 1\ndel f\n", "f") == REASON_DELETED


def test_reject_shadowed_by_import():
    assert (
        _reason_for("from os import f\ndef f():\n    return 1\n", "f") == REASON_SHADOWED_BY_IMPORT
    )


def test_reject_global_write_elsewhere():
    src = "def f():\n    return 1\ndef g():\n    global f\n    f = 2\n"
    assert _reason_for(src, "f") == REASON_GLOBAL_WRITE


@pytest.mark.skipif(sys.version_info < (3, 12), reason="PEP 695 type params need 3.12+")
def test_reject_generic_type_params():
    assert _reason_for("def f[T](x: T) -> T:\n    return x\n", "f") == REASON_TYPE_PARAMS


def test_source_digest_is_stable_and_content_sensitive():
    a = plan_module_targets("m", "def f(x):\n    return x + 1\n").selected[0]
    a2 = plan_module_targets("m", "def f(x):\n    return x + 1\n").selected[0]
    b = plan_module_targets("m", "def f(x):\n    return x + 2\n").selected[0]
    assert a.source_digest == a2.source_digest
    assert a.source_digest != b.source_digest


def test_reject_rebinding_in_module_control_flow():
    # Rebinding inside module-level control flow still shadows the function.
    assert _reason_for("def f():\n    return 1\nif True:\n    f = 0\n", "f") == REASON_REASSIGNED


def test_reject_duplicate_definition_in_control_flow():
    src = "def f():\n    return 1\nif True:\n    def f():\n        return 2\n"
    assert _reason_for(src, "f") == REASON_DUPLICATE_BINDING


def test_reject_yield_in_comprehension_iterable():
    # yield in the comprehension's outer iterable makes f a generator.
    src = "def f():\n    return [x for x in (yield [1])]\n"
    assert _reason_for(src, "f") == REASON_GENERATOR


def test_reject_nested_def_inside_control_flow():
    src = "def f():\n    if True:\n        def g():\n            return 1\n    return 1\n"
    assert _reason_for(src, "f") == REASON_NESTED_DEFINITION


def test_reject_global_write_through_import():
    src = "def f():\n    return 1\ndef g():\n    global f\n    import math as f\n"
    assert (
        _reason_for(src, "f") == REASON_SHADOWED_BY_IMPORT
        or _reason_for(src, "f") == REASON_GLOBAL_WRITE
    )


def test_nested_local_assignment_is_not_a_global_write():
    # f=2 belongs to h's frame, not g's; g's `global f` must not implicate it.
    src = (
        "def f():\n    return 1\n"
        "def g():\n    global f\n    def h():\n        f = 2\n    return h\n"
    )
    plan = plan_module_targets("m", src)
    assert "f" in {b.name for b in plan.selected}


def test_module_level_only_nested_functions_are_not_targets():
    # Nested functions must never appear as top-level selections.
    src = "def outer():\n    def inner():\n        return 1\n    return inner\n"
    plan = plan_module_targets("m", src)
    assert all(b.name != "inner" for b in plan.selected)
    assert plan.rejected[0].name == "outer"
    assert plan.rejected[0].reason == REASON_NESTED_DEFINITION


# --------------------------------------------------------------------------
# CLI gate: preview-only, never falls back to an ordinary build
# --------------------------------------------------------------------------


def test_cli_crossfile_opacity_rejects_and_writes_nothing(tmp_path):
    from click.testing import CliRunner

    from pyobfus.cli import main

    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def f(x):\n    return x + 1\n", encoding="utf-8")
    out = tmp_path / "out"

    result = CliRunner().invoke(main, [str(src), "-o", str(out), "--crossfile-opacity"])

    # Community config without the required options: exit 2, reasons listed,
    # and no output directory created (no fallback to a normal build).
    assert result.exit_code == 2, result.output
    assert "not supported" in result.output
    assert "Pro" in result.output
    assert not out.exists()


# --------------------------------------------------------------------------
# Slice B: original-binding-id -> final-name correspondence
# --------------------------------------------------------------------------

from pyobfus.core.crossfile_opacity import resolve_correspondence  # noqa: E402


class _MappingStub:
    def __init__(self, modules):
        self.modules = modules


def _plan_from_source(module, src):
    return plan_module_targets(module, src)


def test_correspondence_resolves_renamed_and_preserved():
    src = "def pub(x):\n    return x + 1\ndef _priv(y):\n    return y * 2\n"
    plan = _plan_from_source("pkg.util", src)
    mapping = _MappingStub({"pkg.util": {"pub": "I2"}})  # _priv left unchanged
    corr = resolve_correspondence(plan, mapping)
    finals = {bf.binding.name: (bf.final_name, bf.renamed) for bf in corr.resolved}
    assert finals["pub"] == ("I2", True)
    assert finals["_priv"] == ("_priv", False)


def test_correspondence_is_file_scoped_for_same_name():
    # Two modules both define f; each resolves to its own final name.
    plan_a = _plan_from_source("a", "def f(x):\n    return x\n")
    plan_b = _plan_from_source("b", "def f(x):\n    return x\n")
    mapping = _MappingStub({"a": {"f": "I0"}, "b": {"f": "I9"}})
    assert resolve_correspondence(plan_a, mapping).resolved[0].final_name == "I0"
    assert resolve_correspondence(plan_b, mapping).resolved[0].final_name == "I9"


def test_correspondence_ignores_local_variable_tables():
    # Only mapping.modules is consulted; a locals table must not leak in.
    src = "def f(x):\n    return x\n"
    plan = _plan_from_source("m", src)
    mapping = _MappingStub({"m": {}})
    mapping.locals = {"m": {"Q9": "f"}}  # function-local reuse of the name
    corr = resolve_correspondence(plan, mapping)
    assert corr.resolved[0].final_name == "f"  # preserved, not Q9


def _phase1_mapping(tmp_path, files):
    from pyobfus.config import ObfuscationConfig
    from pyobfus.core.mapping import ObfuscationMapping
    from pyobfus.core.orchestrator import CrossFileOrchestrator

    src = tmp_path / "src"
    src.mkdir(parents=True)
    for rel, text in files.items():
        p = src / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    orch = CrossFileOrchestrator(ObfuscationConfig(level="community", max_workers=1))
    orch.phase1_scan(src)
    return orch, ObfuscationMapping.from_global_table(orch.global_table, root=str(src))


def test_correspondence_against_real_reexport_and_relative_import(tmp_path):
    # pkg.core defines helper; pkg.__init__ re-exports it; main imports via pkg.
    orch, mapping = _phase1_mapping(
        tmp_path,
        {
            "pkg/__init__.py": "from .core import helper\n__all__ = ['helper']\n",
            "pkg/core.py": "def helper(v):\n    return v + 1\n",
            "main.py": "from pkg import helper\n\n\ndef run():\n    return helper(1)\n",
        },
    )
    plan = plan_module_targets("pkg.core", (tmp_path / "src" / "pkg" / "core.py").read_text())
    corr = resolve_correspondence(plan, mapping)
    helper = {bf.binding.name: bf.final_name for bf in corr.resolved}["helper"]
    # The definition's final name comes from pkg.core, matching Core's table.
    assert helper == mapping.modules.get("pkg.core", {}).get("helper", "helper")
    # run() in main resolves to main's own final name, not pkg.core's helper.
    run_plan = plan_module_targets("main", (tmp_path / "src" / "main.py").read_text())
    run_final = {
        bf.binding.name: bf.final_name for bf in resolve_correspondence(run_plan, mapping).resolved
    }
    assert "helper" not in run_final  # main does not define helper
    assert run_final["run"] == mapping.modules.get("main", {}).get("run", "run")


def test_correspondence_against_circular_import(tmp_path):
    orch, mapping = _phase1_mapping(
        tmp_path,
        {
            "a.py": "import b\n\n\ndef a_fn():\n    return b.b_fn()\n",
            "b.py": "import a\n\n\ndef b_fn():\n    return 7\n",
        },
    )
    for mod, fn in (("a", "a_fn"), ("b", "b_fn")):
        plan = plan_module_targets(mod, (tmp_path / "src" / f"{mod}.py").read_text())
        corr = resolve_correspondence(plan, mapping)
        final = {bf.binding.name: bf.final_name for bf in corr.resolved}[fn]
        assert final == mapping.modules.get(mod, {}).get(fn, fn)


def test_correspondence_is_stable_regardless_of_file_creation_order(tmp_path):
    files = {
        "a.py": "def f():\n    return 1\n",
        "b.py": "def f():\n    return 2\n",
        "c.py": "def f():\n    return 3\n",
    }
    _, m1 = _phase1_mapping(tmp_path / "one", files)
    _, m2 = _phase1_mapping(tmp_path / "two", {k: files[k] for k in reversed(list(files))})
    for mod in ("a", "b", "c"):
        plan = plan_module_targets(mod, files[f"{mod}.py"])
        f1 = resolve_correspondence(plan, m1).resolved[0].final_name
        f2 = resolve_correspondence(plan, m2).resolved[0].final_name
        # Each module's own f resolves to that module's recorded final name.
        assert f1 == m1.modules.get(mod, {}).get("f", "f")
        assert f2 == m2.modules.get(mod, {}).get("f", "f")
