"""Tests for pyobfus_mcp.tools.protect_project — the self-verifying pipeline.

These exercise the real obfuscation CLI in a subprocess (no `mcp` SDK needed)
plus the round-trip verification logic. The integration tests assert the
headline promise: a healthy project comes back `verified: True`, and output
that won't compile/import comes back `verified: False` with `status:
"warnings"` so an agent knows NOT to ship it.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

from pyobfus_mcp.tools import _run_verification, protect_project


def _write(root: Path, name: str, src: str) -> Path:
    p = root / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(src).lstrip(), encoding="utf-8")
    return p


def _healthy_src(tmp_path: Path) -> Path:
    src = tmp_path / "src"
    _write(
        src,
        "calc.py",
        """
        SECRET = "abcdefghijklmnopqrstuvwxyz0123456789ABCD"
        def add_numbers(a, b):
            return a + b
        class Calculator:
            def compute(self, x, y):
                return add_numbers(x, y)
        """,
    )
    _write(
        src,
        "app.py",
        """
        from calc import Calculator
        def run():
            return Calculator().compute(2, 3)
        """,
    )
    return src


# ---------------------------------------------------------------------------
# Integration: full pipeline
# ---------------------------------------------------------------------------


def test_protect_project_healthy_is_verified(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    out = tmp_path / "dist"

    result = protect_project(str(src), output_dir=str(out))

    assert result["status"] == "success"
    assert result["verified"] is True
    assert result["confidence"] in ("medium", "high")
    assert result["preset_used"] == "balanced"
    assert result["obfuscation"]["files_processed"] == 2
    # Output really exists and is renamed (original identifiers gone).
    assert (out / "calc.py").exists()
    obf_text = (out / "calc.py").read_text()
    assert "add_numbers" not in obf_text and "Calculator" not in obf_text
    # Both modules import cleanly; none broke.
    assert sorted(result["verification"]["modules_imported_ok"]) == ["app", "calc"]
    assert result["verification"]["modules_broke"] == []
    # next_tool signals the chain is complete.
    assert result["next_tool"]["tool"] is None


def test_protect_project_mapping_is_sibling_not_inside_output(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    out = tmp_path / "dist"

    result = protect_project(str(src), output_dir=str(out))

    mapping = Path(result["mapping_path"])
    assert mapping.exists()
    # The de-obfuscation key must NOT ship inside the protected artifact.
    assert mapping.parent == out.parent
    assert out not in mapping.parents
    assert result["mapping_security_note"]


def test_protect_project_save_mapping_false(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    result = protect_project(str(src), output_dir=str(tmp_path / "dist"), save_mapping=False)
    assert result["mapping_path"] is None
    assert result["mapping_security_note"] is None


def test_protect_project_verify_false_skips_checks(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    result = protect_project(str(src), output_dir=str(tmp_path / "dist"), verify=False)
    assert result["status"] == "success"
    assert result["verified"] is None
    assert result["verification"] is None
    assert result["confidence"] == "unverified"


def test_protect_project_preset_override(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    result = protect_project(str(src), output_dir=str(tmp_path / "dist"), preset="safe")
    assert result["preset_used"] == "safe"


def test_protect_project_broken_output_is_caught(tmp_path: Path) -> None:
    # A module that imports a nonexistent module: obfuscation succeeds, but the
    # import smoke test must catch that the output won't import.
    src = tmp_path / "src"
    _write(src, "fine.py", "def ok():\n    return 42\n")
    _write(
        src,
        "broken.py",
        """
        import totally_missing_module_xyz
        def go():
            return totally_missing_module_xyz.f()
        """,
    )
    result = protect_project(str(src), output_dir=str(tmp_path / "dist"))

    assert result["status"] == "warnings"
    assert result["verified"] is False
    broke = [m["module"] for m in result["verification"]["modules_broke"]]
    assert "broken" in broke
    assert "fine" in result["verification"]["modules_imported_ok"]
    # Agent is routed to diagnosis, and told not to ship.
    assert result["next_tool"]["tool"] == "check_obfuscation_risks"
    assert "do not ship" in result["ai_hint"].lower()


# ---------------------------------------------------------------------------
# Guard rails
# ---------------------------------------------------------------------------


def test_protect_project_rejects_path_outside_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Narrow the sandbox so an absolute path elsewhere is rejected.
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(tmp_path / "root"))
    (tmp_path / "root").mkdir()
    result = protect_project("/etc", output_dir="dist")
    assert result["status"] == "error"
    assert result["error_type"] == "PathScopeError"


def test_protect_project_rejects_output_overlapping_source(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    # Output dir inside the source tree is a footgun (obfuscating into source).
    result = protect_project(str(src), output_dir=str(src / "dist"))
    assert result["status"] == "error"
    assert result["error_type"] == "BadOutputDir"


def test_protect_project_verify_cmd_disabled_by_default(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    result = protect_project(str(src), output_dir=str(tmp_path / "dist"), verify_cmd="echo hi")
    block = result["verification"]["verify_cmd"]
    assert block["ran"] is False
    assert "PYOBFUS_MCP_ALLOW_VERIFY_CMD" in block["skipped_reason"]


# ---------------------------------------------------------------------------
# Unit: _run_verification classification
# ---------------------------------------------------------------------------


def test_run_verification_clean_dir(tmp_path: Path) -> None:
    out = tmp_path / "out"
    _write(out, "good.py", "def f():\n    return 1\n")
    v = _run_verification(out, verify_cmd=None, allow_cmd=False, timeout=60)
    assert v["verified"] is True
    assert v["confidence"] == "medium"
    assert v["compile_ok"] is True
    assert v["modules_broke"] == []


def test_run_verification_syntax_error_fails_compile(tmp_path: Path) -> None:
    out = tmp_path / "out"
    _write(out, "good.py", "def f():\n    return 1\n")
    _write(out, "bad.py", "def f(:\n    pass\n")  # syntax error
    v = _run_verification(out, verify_cmd=None, allow_cmd=False, timeout=60)
    assert v["compile_ok"] is False
    assert v["verified"] is False


def test_run_verification_missing_import_is_breaking(tmp_path: Path) -> None:
    out = tmp_path / "out"
    _write(out, "m.py", "import no_such_module_abc_xyz\n")
    v = _run_verification(out, verify_cmd=None, allow_cmd=False, timeout=60)
    assert v["verified"] is False
    assert any(m["module"] == "m" for m in v["modules_broke"])


def test_run_verification_runtime_error_is_inconclusive(tmp_path: Path) -> None:
    # A module that raises a non-structural error at import: not proof the
    # obfuscation broke anything, so it lowers confidence but doesn't fail.
    out = tmp_path / "out"
    _write(out, "needs_env.py", "raise RuntimeError('needs config at import')\n")
    v = _run_verification(out, verify_cmd=None, allow_cmd=False, timeout=60)
    assert v["verified"] is True
    assert v["confidence"] == "low"
    assert any(m["module"] == "needs_env" for m in v["import_inconclusive"])


def test_run_verification_verify_cmd_passes(tmp_path: Path) -> None:
    out = tmp_path / "out"
    _write(out, "good.py", "def f():\n    return 1\n")
    v = _run_verification(
        out,
        verify_cmd=f'"{sys.executable}" -c "import sys; sys.exit(0)"',
        allow_cmd=True,
        timeout=60,
    )
    assert v["verify_cmd"]["ran"] is True
    assert v["verify_cmd"]["passed"] is True
    assert v["verified"] is True
    assert v["confidence"] == "high"


def test_run_verification_verify_cmd_failure_fails(tmp_path: Path) -> None:
    out = tmp_path / "out"
    _write(out, "good.py", "def f():\n    return 1\n")
    v = _run_verification(
        out,
        verify_cmd=f'"{sys.executable}" -c "import sys; sys.exit(7)"',
        allow_cmd=True,
        timeout=60,
    )
    assert v["verify_cmd"]["passed"] is False
    assert v["verified"] is False


# ---------------------------------------------------------------------------
# Trace marker (auto-unmap convention) — on by default
# ---------------------------------------------------------------------------


def test_protect_project_stamps_trace_marker_by_default(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    out = tmp_path / "dist"
    result = protect_project(str(src), output_dir=str(out))

    assert result["obfuscation"]["trace_marker_id"]
    marked = (out / "calc.py").read_text(encoding="utf-8")
    assert marked.startswith("# pyobfus:obfuscated")
    assert f"id={result['obfuscation']['trace_marker_id']}" in marked


def test_protect_project_trace_marker_can_be_disabled(tmp_path: Path) -> None:
    src = _healthy_src(tmp_path)
    out = tmp_path / "dist"
    result = protect_project(str(src), output_dir=str(out), trace_marker=False)

    assert result["obfuscation"]["trace_marker_id"] is None
    assert "# pyobfus:obfuscated" not in (out / "calc.py").read_text(encoding="utf-8")
