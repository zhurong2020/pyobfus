"""Tests for pyobfus_mcp.tools — the pure-Python tool implementations.

These do NOT require the `mcp` SDK to be installed. They exercise the
same functions that `server.py` wraps as MCP tool handlers.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import yaml

from pyobfus_mcp.tools import (
    check_obfuscation_risks,
    explain_preset,
    generate_pyobfus_config,
    list_presets,
    unmap_stack_trace,
)


def _write(tmp_path: Path, name: str, src: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(src).lstrip(), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# check_obfuscation_risks
# ---------------------------------------------------------------------------


def test_check_obfuscation_risks_clean_project(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "def greet(name): return f'hi {name}'\n")
    result = check_obfuscation_risks(str(tmp_path))
    assert result["status"] == "success"
    assert result["files_scanned"] == 1
    assert result["exit_code"] == 0


def test_check_obfuscation_risks_flags_eval(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "eval('x+1')\n")
    result = check_obfuscation_risks(str(tmp_path))
    assert result["status"] == "warnings"
    assert result["severity_counts"]["high"] >= 1
    assert result["ai_hint"]


def test_check_obfuscation_risks_detects_fastapi(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "api.py",
        """
        from fastapi import FastAPI
        app = FastAPI()
        """,
    )
    result = check_obfuscation_risks(str(tmp_path))
    assert result["suggested_preset"] == "fastapi"
    assert any(fw["name"] == "FastAPI" for fw in result["frameworks"])


def test_check_obfuscation_risks_path_not_found(tmp_path: Path) -> None:
    nonexistent = tmp_path / "definitely_does_not_exist_xyz123"
    result = check_obfuscation_risks(str(nonexistent))
    assert result["status"] == "error"
    assert result["error_type"] == "PathNotFound"


# ---------------------------------------------------------------------------
# generate_pyobfus_config
# ---------------------------------------------------------------------------


def test_generate_pyobfus_config_returns_yaml_without_writing(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "m.py",
        """
        from pydantic import BaseModel
        class U(BaseModel): x: int
        """,
    )
    result = generate_pyobfus_config(str(tmp_path))
    assert result["status"] == "success"
    assert result["preset"] == "pydantic"
    assert result["written"] is False
    assert "yaml" in result
    # YAML content is parseable
    parsed = yaml.safe_load(result["yaml"])
    assert parsed["obfuscation"]["preset"] == "pydantic"
    # No file written
    assert not (tmp_path / "pyobfus.yaml").exists()


def test_generate_pyobfus_config_writes_when_requested(tmp_path: Path) -> None:
    _write(tmp_path, "a.py", "x = 1\n")
    result = generate_pyobfus_config(str(tmp_path), write=True)
    assert result["status"] == "success"
    assert result["written"] is True
    assert Path(result["config_path"]).exists()


def test_generate_pyobfus_config_preset_override(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "api.py",
        """
        from fastapi import FastAPI
        app = FastAPI()
        """,
    )
    result = generate_pyobfus_config(str(tmp_path), preset_override="aggressive")
    assert result["preset"] == "aggressive"


def test_generate_pyobfus_config_path_not_found(tmp_path: Path) -> None:
    nonexistent = tmp_path / "definitely_does_not_exist_xyz"
    result = generate_pyobfus_config(str(nonexistent))
    assert result["status"] == "error"


# ---------------------------------------------------------------------------
# unmap_stack_trace
# ---------------------------------------------------------------------------


def test_unmap_stack_trace_roundtrip(tmp_path: Path) -> None:
    mapping_path = tmp_path / "m.json"
    mapping_path.write_text(
        json.dumps(
            {
                "version": 1,
                "modules": {"calc": {"Calculator": "I0", "add": "I1"}},
                "global": {
                    "I0": {"module": "calc", "original": "Calculator"},
                    "I1": {"module": "calc", "original": "add"},
                },
            }
        ),
        encoding="utf-8",
    )
    trace = "AttributeError: 'I0' object has no attribute 'I1'"
    result = unmap_stack_trace(trace, str(mapping_path))
    assert result["status"] == "success"
    assert result["unmapped_trace"] == (
        "AttributeError: 'Calculator' object has no attribute 'add'"
    )
    assert result["mapping_stats"]["unique_obfuscated"] == 2


def test_unmap_stack_trace_missing_mapping(tmp_path: Path) -> None:
    nonexistent = tmp_path / "does_not_exist.json"
    result = unmap_stack_trace("foo", str(nonexistent))
    assert result["status"] == "error"
    assert result["error_type"] == "MappingNotFound"


def test_unmap_stack_trace_invalid_mapping(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"version": 999}), encoding="utf-8")
    result = unmap_stack_trace("foo", str(bad))
    assert result["status"] == "error"
    assert result["error_type"] == "InvalidMapping"


# ---------------------------------------------------------------------------
# list_presets + explain_preset
# ---------------------------------------------------------------------------


def test_list_presets_groups_correctly() -> None:
    result = list_presets()
    assert result["status"] == "success"
    # Community (non-framework, non-pro)
    for p in ("safe", "balanced", "aggressive"):
        assert p in result["community"]
    # Framework
    for p in ("fastapi", "django", "flask", "pydantic", "click", "sqlalchemy"):
        assert p in result["framework"]
    # Pro
    for p in ("trial", "commercial", "library", "maximum"):
        assert p in result["pro"]


def test_explain_preset_community() -> None:
    result = explain_preset("fastapi")
    assert result["status"] == "success"
    assert result["preset"] == "fastapi"
    assert result["level"] == "community"
    assert result["preserve_param_names"] is True
    assert result["exclude_names_count"] > 0
    assert "--preset fastapi" in result["ai_hint"]


def test_explain_preset_pro_mentions_trial() -> None:
    result = explain_preset("commercial")
    assert result["status"] == "success"
    assert result["level"] == "pro"
    assert "trial" in result["ai_hint"].lower()


def test_explain_preset_unknown() -> None:
    result = explain_preset("totally_made_up")
    assert result["status"] == "error"
    assert result["error_type"] == "UnknownPreset"


# ---------------------------------------------------------------------------
# Server module is importable without the mcp SDK
# ---------------------------------------------------------------------------


def test_server_module_importable_without_mcp_sdk() -> None:
    """`pyobfus_mcp.server` must import cleanly even if `mcp` is missing.

    The SDK import happens lazily inside `_build_server()` so tests of
    tools.py don't require the SDK. This protects the test suite from
    breaking when the package is not installed in a test env.
    """
    import pyobfus_mcp.server as srv

    # tool_functions export is independent of the SDK
    assert srv.tool_functions
    assert all(callable(fn) for fn in srv.tool_functions)


def test_build_server_attaches_meta_to_each_tool() -> None:
    """Every `@app.tool` registration must carry the Phase 2 meta dict.

    Verifies the version + tier metadata is actually wired through the
    FastMCP API so downstream aggregators (Glama, Anthropic registry) can
    surface it. Skipped when the mcp SDK isn't installed in the test env;
    the integration is also covered by the `mcp-sdk-latest` CI job.
    """
    import asyncio

    pytest = __import__("pytest")
    try:
        from pyobfus_mcp.server import _build_server
    except ImportError:  # pragma: no cover — only when mcp SDK isn't installed
        pytest.skip("mcp SDK not installed in this test env")

    app = _build_server()
    tools = asyncio.run(app.list_tools())

    expected_names = {
        "check_obfuscation_risks",
        "generate_pyobfus_config",
        "unmap_stack_trace",
        "list_presets",
        "explain_preset",
    }
    actual_names = {t.name for t in tools}
    assert actual_names == expected_names, (
        f"unexpected tool set: {actual_names ^ expected_names}"
    )

    for tool in tools:
        # mcp SDK exposes the meta dict via `.meta` on the Tool object.
        meta = getattr(tool, "meta", None)
        assert meta is not None, f"{tool.name} has no meta dict"
        assert meta.get("version") == "1", (
            f"{tool.name} meta.version={meta.get('version')!r}, expected '1'"
        )
        assert meta.get("tier") == "community", (
            f"{tool.name} meta.tier={meta.get('tier')!r}, expected 'community'"
        )
