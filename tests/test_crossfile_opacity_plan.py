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
