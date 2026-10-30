"""MCP check_delivery: wraps pyobfus --check-delivery inside the project root."""

from __future__ import annotations

import json

import pytest

from pyobfus_mcp.tools import check_delivery

pytest.importorskip("pyobfus.core.delivery_check")

MAPPING = {"version": 1, "pyobfus_version": "0.7.0", "modules": {}, "global": {}}


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv("PYOBFUS_MCP_PROJECT_ROOT", str(tmp_path))
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "app.py").write_text("I1 = 2\n", encoding="utf-8")
    return tmp_path


def test_clean_delivery_is_ok(root):
    result = check_delivery(str(root / "dist"))
    assert result["status"] == "ok"
    assert result["findings"] == []
    assert result["next_tool"]["tool"] is None
    assert "ai_hint" in result


def test_mapping_in_delivery_fails(root):
    (root / "dist" / "names.json").write_text(json.dumps(MAPPING), encoding="utf-8")
    result = check_delivery(str(root / "dist"))
    assert result["status"] == "fail"
    assert [f["code"] for f in result["findings"]] == ["delivery.mapping_file"]
    assert "remove" in result["next_tool"]["reason"]


def test_paths_outside_the_project_root_are_rejected(root, tmp_path_factory):
    outside = tmp_path_factory.mktemp("elsewhere")
    result = check_delivery(str(outside))
    assert result["status"] == "error"
    assert result["error_type"] == "PathScopeError"


def test_missing_build_report_is_reported(root):
    result = check_delivery(str(root / "dist"), build_report=str(root / "nope.json"))
    assert result["status"] == "error"
    assert result["error_type"] == "NotFound"


def test_invalid_build_report_is_reported(root):
    (root / "report.json").write_text("[1, 2]", encoding="utf-8")
    result = check_delivery(str(root / "dist"), build_report=str(root / "report.json"))
    assert result["status"] == "error"
    assert result["error_type"] == "InvalidInput"


def test_warning_does_not_recommend_shipping(root):
    (root / "dist" / "app.pyc").write_bytes(b"truncated")
    result = check_delivery(str(root / "dist"))
    assert result["status"] == "warn"
    assert "review" in result["next_tool"]["reason"]
    assert "no known" not in result["next_tool"]["reason"]


def test_malformed_nested_report_returns_mcp_error(root):
    (root / "report.json").write_text('{"outputs": []}')
    result = check_delivery(str(root / "dist"), build_report=str(root / "report.json"))
    assert result["status"] == "error"
    assert result["error_type"] == "InvalidInput"
    assert result["ai_hint"] and "next_tool" in result
