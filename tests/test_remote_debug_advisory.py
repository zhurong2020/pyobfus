"""Tests for the Python 3.14 (PEP 768) remote-debug hardening advisory.

The advisory is a narrow-trigger increment on the existing
``compatibility_advisory`` category (design decision "A"): it fires only when
the effective build *both* requests anti-debug protection *and* targets Python
3.14+ (declared ``requires_python_min`` floor, else the running interpreter).
It is severity ``info`` and must never change the scan exit code, and it must
not claim pyobfus can disable the interface.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

from pyobfus.core.preflight import (
    CAT_COMPAT_ADVISORY,
    SEVERITY_INFO,
    PreflightChecker,
    _parse_python_minor,
)


def _write(tmp_path: Path, src: str = "def f(x):\n    return x + 1\n") -> Path:
    p = tmp_path / "m.py"
    p.write_text(src)
    return p


def _remote_debug_risks(report):
    return [
        r
        for r in report.risks
        if r.category == CAT_COMPAT_ADVISORY and "remote debugging" in r.message
    ]


# ---- trigger matrix -------------------------------------------------------


def test_fires_with_protection_and_declared_floor_314(tmp_path: Path) -> None:
    f = _write(tmp_path)
    report = PreflightChecker(protection_intent=True, target_python_min="3.14").check_path(f)
    hits = _remote_debug_risks(report)
    assert len(hits) == 1
    assert hits[0].severity == SEVERITY_INFO


def test_fires_with_declared_floor_above_314(tmp_path: Path) -> None:
    f = _write(tmp_path)
    report = PreflightChecker(protection_intent=True, target_python_min="3.15").check_path(f)
    assert len(_remote_debug_risks(report)) == 1


def test_no_fire_without_protection_intent(tmp_path: Path) -> None:
    """Narrow trigger: a 3.14 target alone is not enough — needs anti-debug."""
    f = _write(tmp_path)
    report = PreflightChecker(protection_intent=False, target_python_min="3.14").check_path(f)
    assert _remote_debug_risks(report) == []


def test_no_fire_when_declared_floor_below_314(tmp_path: Path) -> None:
    """A declared floor < 3.14 is respected as the user's stated target."""
    f = _write(tmp_path)
    report = PreflightChecker(protection_intent=True, target_python_min="3.9").check_path(f)
    assert _remote_debug_risks(report) == []


def test_no_floor_falls_back_to_running_interpreter(tmp_path: Path) -> None:
    f = _write(tmp_path)

    with mock.patch("pyobfus.core.preflight.sys.version_info", (3, 12, 0)):
        report = PreflightChecker(protection_intent=True, target_python_min=None).check_path(f)
    assert _remote_debug_risks(report) == []

    with mock.patch("pyobfus.core.preflight.sys.version_info", (3, 14, 0)):
        report = PreflightChecker(protection_intent=True, target_python_min=None).check_path(f)
    assert len(_remote_debug_risks(report)) == 1


def test_unparseable_floor_falls_back_to_interpreter(tmp_path: Path) -> None:
    f = _write(tmp_path)
    with mock.patch("pyobfus.core.preflight.sys.version_info", (3, 14, 0)):
        report = PreflightChecker(
            protection_intent=True, target_python_min="not-a-version"
        ).check_path(f)
    assert len(_remote_debug_risks(report)) == 1


def test_default_construction_never_fires(tmp_path: Path) -> None:
    """Existing callers that don't pass the new kwargs see no behavior change."""
    f = _write(tmp_path)
    report = PreflightChecker().check_path(f)
    assert _remote_debug_risks(report) == []


# ---- contract -------------------------------------------------------------


def test_advisory_is_info_and_does_not_change_exit_code(tmp_path: Path) -> None:
    """An info advisory must not flip a clean scan to a non-zero exit code."""
    f = _write(tmp_path)
    baseline = PreflightChecker().check_path(f)
    report = PreflightChecker(protection_intent=True, target_python_min="3.14").check_path(f)
    assert len(_remote_debug_risks(report)) == 1
    # Same exit code with and without the info advisory (no high-severity added).
    assert report.exit_code() == baseline.exit_code()


def test_advisory_message_is_honest(tmp_path: Path) -> None:
    """Must not imply pyobfus disables the interface; must point to the startup
    control and the cookbook."""
    f = _write(tmp_path)
    report = PreflightChecker(protection_intent=True, target_python_min="3.14").check_path(f)
    risk = _remote_debug_risks(report)[0]
    # Honest about where the control lives.
    assert "interpreter startup" in risk.message
    assert "do not disable" in risk.message
    # Actionable, points at the real controls + doc.
    assert "disable_remote_debug" in risk.suggestion
    assert "PYTHON_DISABLE_REMOTE_DEBUG" in risk.suggestion
    assert "REMOTE_DEBUG_HARDENING.md" in risk.suggestion
    # Report-level advisory: no fabricated source coordinates.
    assert risk.line == 0 and risk.col == 0


def test_advisory_leaks_no_source_or_secret(tmp_path: Path) -> None:
    f = _write(tmp_path, "TOKEN = 'super-secret-value'\ndef f():\n    return TOKEN\n")
    report = PreflightChecker(protection_intent=True, target_python_min="3.14").check_path(f)
    risk = _remote_debug_risks(report)[0]
    blob = risk.message + " " + risk.suggestion
    assert "super-secret-value" not in blob
    assert "TOKEN" not in blob


# ---- version parser -------------------------------------------------------


def test_parse_python_minor() -> None:
    assert _parse_python_minor("3.14") == (3, 14)
    assert _parse_python_minor("3.14.2") == (3, 14)
    assert _parse_python_minor("3") == (3, 0)
    assert _parse_python_minor("  3.15  ") == (3, 15)
    assert _parse_python_minor(None) is None
    assert _parse_python_minor("") is None
    assert _parse_python_minor("not-a-version") is None
    assert _parse_python_minor("3.x") is None


# ---- CLI wiring (end-to-end via --check) ----------------------------------


def _run_check_json(args):
    import json

    from click.testing import CliRunner

    from pyobfus.cli import main

    result = CliRunner().invoke(main, ["--check", *args, "--json", "--offline"])
    return result, json.loads(result.output)


def _remote_debug_from_json(payload):
    return [
        r
        for r in payload.get("risks", [])
        if r.get("category") == CAT_COMPAT_ADVISORY and "remote debugging" in r.get("message", "")
    ]


def test_cli_check_wires_config_anti_debug_and_python_floor(tmp_path: Path) -> None:
    """`--check` must feed config.anti_debug + config.requires_python_min into
    the advisory (guards the cli.py wiring, not just the checker)."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def add(x, y):\n    return x + y\n")
    (tmp_path / "pyobfus.yaml").write_text(
        'obfuscation:\n  level: pro\n  anti_debug: true\n  requires_python_min: "3.14"\n'
    )

    result, payload = _run_check_json([str(src), "--config", str(tmp_path / "pyobfus.yaml")])
    assert result.exit_code == 0  # info advisory does not change exit code
    hits = _remote_debug_from_json(payload)
    assert len(hits) == 1
    assert hits[0]["severity"] == "info"


def test_cli_check_no_advisory_without_anti_debug(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a.py").write_text("def add(x, y):\n    return x + y\n")
    (tmp_path / "pyobfus.yaml").write_text(
        'obfuscation:\n  level: pro\n  requires_python_min: "3.14"\n'
    )
    _result, payload = _run_check_json([str(src), "--config", str(tmp_path / "pyobfus.yaml")])
    assert _remote_debug_from_json(payload) == []
