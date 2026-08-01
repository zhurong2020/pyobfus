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
    recommend_tier,
    start_pro_trial,
    unmap_stack_trace,
)


def _write(tmp_path: Path, name: str, src: str) -> Path:
    p = tmp_path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(src).lstrip(), encoding="utf-8")
    return p


def _assert_next_tool_shape(result: dict) -> None:
    """Every successful tool response must carry a machine-readable next_tool."""
    assert "next_tool" in result, result.get("status")
    nt = result["next_tool"]
    assert set(nt) == {"tool", "reason", "args"}
    assert nt["tool"] is None or isinstance(nt["tool"], str)
    assert isinstance(nt["reason"], str) and nt["reason"]
    assert isinstance(nt["args"], dict)


def test_every_tool_success_carries_next_tool(tmp_path: Path) -> None:
    """The next_tool agent-chaining convention holds across all tools."""
    _write(tmp_path, "a.py", "def greet(name):\n    return f'hi {name}'\n")
    mapping = tmp_path / "m.json"
    mapping.write_text(json.dumps({"version": 1, "modules": {}, "global": {}}), encoding="utf-8")

    _assert_next_tool_shape(check_obfuscation_risks(str(tmp_path)))
    _assert_next_tool_shape(generate_pyobfus_config(str(tmp_path)))
    _assert_next_tool_shape(unmap_stack_trace("at I0", str(mapping)))
    _assert_next_tool_shape(list_presets())
    _assert_next_tool_shape(explain_preset("balanced"))
    _assert_next_tool_shape(explain_preset("commercial"))  # Pro path
    _assert_next_tool_shape(recommend_tier(str(tmp_path)))
    _assert_next_tool_shape(start_pro_trial())


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
    for p in ("fastapi", "django", "flask", "pydantic", "click", "sqlalchemy", "ml"):
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
    """Every `@app.tool` registration must carry the Phase 2/3 meta dict.

    Verifies the version + tier metadata is actually wired through the
    FastMCP API so downstream aggregators (Glama, Anthropic registry) can
    surface it. Skipped when the mcp SDK isn't installed in the test env;
    the integration is also covered by the `mcp-sdk-latest` CI job.

    Phase 3 added two `pro_funnel`-tier tools (recommend_tier,
    start_pro_trial) on top of the original five `community`-tier tools.
    """
    import asyncio

    pytest = __import__("pytest")
    try:
        from pyobfus_mcp.server import _build_server
    except ImportError:  # pragma: no cover — only when mcp SDK isn't installed
        pytest.skip("mcp SDK not installed in this test env")

    app = _build_server()
    tools = asyncio.run(app.list_tools())

    expected_community = {
        "protect_project",
        "check_obfuscation_risks",
        "generate_pyobfus_config",
        "unmap_stack_trace",
        "list_presets",
        "explain_preset",
    }
    expected_pro_funnel = {"recommend_tier", "start_pro_trial"}
    expected_names = expected_community | expected_pro_funnel

    actual_names = {t.name for t in tools}
    assert actual_names == expected_names, f"unexpected tool set: {actual_names ^ expected_names}"

    for tool in tools:
        # mcp SDK exposes the meta dict via `.meta` on the Tool object.
        meta = getattr(tool, "meta", None)
        assert meta is not None, f"{tool.name} has no meta dict"
        assert meta.get("version") == "1", (
            f"{tool.name} meta.version={meta.get('version')!r}, expected '1'"
        )
        expected_tier = "pro_funnel" if tool.name in expected_pro_funnel else "community"
        assert meta.get("tier") == expected_tier, (
            f"{tool.name} meta.tier={meta.get('tier')!r}, expected {expected_tier!r}"
        )


# ---------------------------------------------------------------------------
# Phase 3: Pro funnel via MCP
# ---------------------------------------------------------------------------


def test_check_obfuscation_risks_attaches_tier_context(tmp_path: Path) -> None:
    """Phase 3: every check_obfuscation_risks response carries tier_context."""
    _write(tmp_path, "a.py", "def greet(name): return f'hi {name}'\n")
    result = check_obfuscation_risks(str(tmp_path))
    assert "tier_context" in result
    assert result["tier_context"]["tool_tier"] == "community"
    assert "user_tier" in result["tier_context"]
    assert "pro_unlock_url" in result["tier_context"]


def test_check_obfuscation_risks_no_pro_value_on_clean_project(tmp_path: Path) -> None:
    """When the scan finds no sensitive literals and no high-severity findings,
    pro_value is omitted (Pro upsell would be noise)."""
    _write(tmp_path, "a.py", "def greet(name): return f'hi {name}'\n")
    result = check_obfuscation_risks(str(tmp_path))
    assert result["status"] == "success"
    assert "pro_value" not in result, (
        f"clean project should not get pro_value; got {result.get('pro_value')!r}"
    )


def test_check_obfuscation_risks_pro_value_on_sensitive_literals(
    tmp_path: Path,
) -> None:
    """Phase 3: scanning code with sensitive-looking string literals surfaces
    pro_value with applicable_features and a recommendation_strength.

    Note: fixture strings are deliberately shaped to trigger our pattern #1
    (keyword=value) and pattern #4 (40+ char alphanumeric) without matching
    pattern #2 (Stripe sk_live/test) or pattern #3 (AWS AKIA/ASIA). That
    avoids GitHub Push Protection's secret scanner flagging legitimate test
    data as real secrets — and stays as effective for our own heuristic
    (which catches both shapes via complementary patterns).
    """
    _write(
        tmp_path,
        "secrets.py",
        """
        API_KEY = "totally_fake_long_alphanumeric_test_value_xxxxxxxx_yyyy"
        SECRET_KEY = "another_long_random_alphanumeric_token_for_testing_only"
        access_token = "third_long_alphanumeric_value_purely_test_data_xx_yyy"
        password = "hunter2_long_enough_to_trigger_the_pattern_match_x"
        bearer = "very_long_bearer_token_value_for_authentication_purposes"
        """,
    )
    result = check_obfuscation_risks(str(tmp_path))
    assert "pro_value" in result, "sensitive literals should trigger pro_value"
    pv = result["pro_value"]
    assert "string_encryption" in pv["applicable_features"]
    assert pv["sensitive_literal_count"] >= 3
    assert pv["recommendation_strength"] in {"low", "medium", "high"}
    assert pv["price_usd"] == 45
    assert pv["trial_command"] == "pyobfus-trial start"
    assert pv["checkout_url"].startswith("https://buy.stripe.com/")


def test_explain_preset_pro_returns_structured_pro_unlock() -> None:
    """Phase 3: Pro preset path returns full pro_unlock dict + ROI ai_hint."""
    result = explain_preset("commercial")
    assert result["status"] == "success"
    assert result["level"] == "pro"
    assert "pro_unlock" in result, "Pro preset must surface structured unlock info"
    pu = result["pro_unlock"]
    assert pu["trial_command"] == "pyobfus-trial start"
    assert pu["trial_duration_days"] == 5
    assert pu["price_usd"] == 45
    assert pu["money_back_guarantee_days"] == 30
    assert pu["checkout_url"].startswith("https://buy.stripe.com/")
    # ai_hint should mention price + duration + checkout URL
    assert "$45" in result["ai_hint"]
    assert "5-day" in result["ai_hint"]
    assert "buy.stripe.com" in result["ai_hint"]


def test_explain_preset_community_no_pro_unlock_field() -> None:
    """Community presets don't get pro_unlock (it would be noise)."""
    result = explain_preset("balanced")
    assert result["status"] == "success"
    assert result["level"] == "community"
    assert "pro_unlock" not in result, "community preset should not carry pro_unlock"
    # but tier_context is still attached so the AI knows the user's tier
    assert "tier_context" in result


# ---------------------------------------------------------------------------
# recommend_tier
# ---------------------------------------------------------------------------


def test_recommend_tier_clean_project_recommends_community(tmp_path: Path) -> None:
    """No risk patterns, no sensitive literals → community is sufficient."""
    from pyobfus_mcp.tools import recommend_tier

    _write(tmp_path, "a.py", "def greet(name): return f'hi {name}'\n")
    result = recommend_tier(str(tmp_path))
    assert result["status"] == "success"
    assert result["recommended_tier"] == "community"
    assert (
        any("balanced" in r or "no risk" in r.lower() for r in result["reasons"])
        or result["reasons"]
    )
    # Community-recommended ai_hint should suggest a runnable pyobfus command.
    assert "pyobfus" in result["ai_hint"]


def test_recommend_tier_sensitive_secrets_recommends_pro(tmp_path: Path) -> None:
    """Many sensitive-looking literals → Pro recommended."""
    from pyobfus_mcp.tools import recommend_tier

    _write(
        tmp_path,
        "secrets.py",
        """
        API_KEY_1 = "totally_fake_long_alphanumeric_test_value_aaaaaaaa_bbbb"
        API_KEY_2 = "another_fake_long_alphanumeric_test_value_cccccccc_dddd"
        access_token = "third_fake_long_test_value_eeeeeeee_ffff_gggg_hhhh"
        password = "fake_long_test_password_for_pattern_match_iiii_jjjj_x"
        secret_key = "another_long_alphanumeric_secret_value_xy_kkkk_llll"
        bearer_token = "long_opaque_bearer_value_for_auth_xyz_mmmm_nnnn_oooo"
        """,
    )
    result = recommend_tier(str(tmp_path))
    assert result["status"] == "success"
    assert result["recommended_tier"] == "pro"
    assert result["scan_summary"]["sensitive_literal_count"] >= 4
    assert result["pro_action"]["price_usd"] == 45
    assert "buy.stripe.com" in result["pro_action"]["checkout_url"]
    assert result["tier_context"]["tool_tier"] == "pro_funnel"


def test_recommend_tier_path_not_found(tmp_path: Path) -> None:
    """Nonexistent path → standard error envelope."""
    from pyobfus_mcp.tools import recommend_tier

    nonexistent = tmp_path / "definitely_not_here"
    result = recommend_tier(str(nonexistent))
    assert result["status"] == "error"
    assert result["error_type"] == "PathNotFound"


# ---------------------------------------------------------------------------
# start_pro_trial
# ---------------------------------------------------------------------------


def test_start_pro_trial_returns_structured_guidance() -> None:
    """start_pro_trial returns full trial info + post-trial purchase URL."""
    from pyobfus_mcp.tools import start_pro_trial

    result = start_pro_trial()
    assert result["status"] == "success"
    assert result["trial_command"] == "pyobfus-trial start"
    assert result["trial_duration_days"] == 5
    features_blob = " ".join(result["trial_features"])
    assert "AES-256 string encryption" in features_blob
    assert "Selective Opacity" in features_blob  # v0.5 mechanisms surfaced
    assert result["post_trial_options"]["price_usd"] == 45
    assert "buy.stripe.com" in result["post_trial_options"]["checkout_url"]
    assert result["tier_context"]["tool_tier"] == "pro_funnel"
    # ai_hint should be actionable for the AI agent.
    assert "pyobfus-trial start" in result["ai_hint"] or "trial" in result["ai_hint"]


def test_start_pro_trial_does_not_invoke_side_effect() -> None:
    """start_pro_trial must NOT actually start a trial — only return guidance.

    Verified by checking that calling it doesn't toggle the local trial
    state. (If we ever wire actual side effects, this test catches that.)
    """
    from pyobfus.trial import get_trial_status
    from pyobfus_mcp.tools import start_pro_trial

    state_before = get_trial_status()
    _ = start_pro_trial()
    state_after = get_trial_status()
    assert state_before == state_after, "start_pro_trial unexpectedly changed local trial state"
