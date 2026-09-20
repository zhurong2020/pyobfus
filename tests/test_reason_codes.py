"""Tests for the stable reason-code catalog and its emission in plan/report."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core import reason_codes as rc
from pyobfus.core.build_plan import build_obfuscation_plan


def _plan(input_path: Path, output_path: Path, config: ObfuscationConfig, cross_file: bool):
    return build_obfuscation_plan(
        input_path=input_path,
        output_path=output_path,
        config=config,
        config_source="test",
        config_path=None,
        preset=None,
        cross_file=cross_file,
        mapping_path=None,
        provenance_manifest_path=None,
        build_report_path=None,
        trace_marker=False,
        cwd=input_path if input_path.is_dir() else input_path.parent,
    )


# ---- catalog contract ----------------------------------------------------


def test_reason_codes_version_is_an_int():
    assert isinstance(rc.REASON_CODES_VERSION, int)
    assert rc.REASON_CODES_VERSION >= 1


def test_code_string_values_are_stable():
    # Locking the exact strings: consumers branch on these.
    assert rc.SELECTED_INCLUDED == "selected.included"
    assert rc.EXCLUDED_PATTERN == "excluded.pattern"
    assert rc.DISABLED_CROSS_FILE_MODE == "disabled.cross_file_mode"
    assert rc.DISABLED_REQUIRES_PRO == "disabled.requires_pro"
    assert rc.DISABLED_NOT_SELECTED == "disabled.not_selected"
    assert rc.PRESERVED_DUNDER == "preserved.dunder"
    assert rc.PRESERVED_IMPORTED == "preserved.imported"


def test_catalog_helpers():
    assert rc.is_known(rc.EXCLUDED_PATTERN) is True
    assert rc.is_known("not.a.code") is False
    assert rc.describe(rc.EXCLUDED_PATTERN)  # non-empty
    assert rc.describe("not.a.code") == "Unknown reason code."
    cat = rc.catalog()
    assert set(cat) == set(rc.ALL_REASON_CODES)
    cat["x"] = "y"  # mutation must not leak back
    assert "x" not in rc.ALL_REASON_CODES


# ---- plan emission -------------------------------------------------------


def test_plan_carries_reason_codes_version(tmp_path: Path):
    src = tmp_path / "a.py"
    src.write_text("def f():\n    return 1\n", encoding="utf-8")
    plan = _plan(src, tmp_path / "out.py", ObfuscationConfig(), cross_file=False)
    assert plan["reason_codes_version"] == rc.REASON_CODES_VERSION
    assert plan["files"]["selected"][0]["reason"] == rc.SELECTED_INCLUDED


def test_plan_excluded_uses_catalog_code(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("x = 1\n", encoding="utf-8")
    (src / "test_app.py").write_text("y = 2\n", encoding="utf-8")
    cfg = ObfuscationConfig()
    plan = _plan(src, tmp_path / "dist", cfg, cross_file=True)
    assert plan["files"]["excluded"][0]["reason"] == rc.EXCLUDED_PATTERN


def test_disabled_transforms_empty_for_plain_config(tmp_path: Path):
    src = tmp_path / "a.py"
    src.write_text("z = 1\n", encoding="utf-8")
    plan = _plan(src, tmp_path / "out.py", ObfuscationConfig(), cross_file=False)
    assert plan["disabled_transforms"] == []


def test_disabled_transforms_flags_fusion_mechanism_in_cross_file(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("x = 1\n", encoding="utf-8")
    cfg = ObfuscationConfig()
    cfg.seal_code = True  # a build-fusion mechanism
    plan = _plan(src, tmp_path / "dist", cfg, cross_file=True)
    assert plan["mode"] == "cross_file"
    hits = [d for d in plan["disabled_transforms"] if d["transform"] == "seal_code"]
    assert hits and hits[0]["reason"] == rc.DISABLED_CROSS_FILE_MODE


def test_disabled_transforms_flags_pro_transform_at_community(tmp_path: Path):
    src = tmp_path / "a.py"
    src.write_text("x = 1\n", encoding="utf-8")
    cfg = ObfuscationConfig()
    cfg.level = "community"
    cfg.string_encryption = True  # Pro-only
    plan = _plan(src, tmp_path / "out.py", cfg, cross_file=False)
    hits = [d for d in plan["disabled_transforms"] if d["transform"] == "string_encryption"]
    assert hits and hits[0]["reason"] == rc.DISABLED_REQUIRES_PRO


# ---- report emission -----------------------------------------------------


def test_build_report_carries_reason_codes_version_and_disabled(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    out = tmp_path / "dist"
    report_path = tmp_path / "report.json"
    result = CliRunner().invoke(
        main, [str(src), "-o", str(out), "--build-report", str(report_path), "--json"]
    )
    assert result.exit_code == 0, result.output
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["reason_codes_version"] == rc.REASON_CODES_VERSION
    assert isinstance(report["disabled_transforms"], list)
    assert report["selection"]["selected"][0]["reason"] == rc.SELECTED_INCLUDED
