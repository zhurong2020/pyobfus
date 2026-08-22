"""
Pure-Python tool implementations for the pyobfus MCP server.

These functions are deliberately MCP-SDK-agnostic: they accept primitive
types, return dicts, and are independently testable without installing
the `mcp` package. `server.py` wraps them as MCP tools; external callers
(tests, CI, custom agent frameworks) can call them directly.

Each public function is decorated with `@secure_tool(...)`, which adds
sliding-window rate limiting and JSON-line audit logging around the call.
Path-accepting tools additionally call `validate_path()` to enforce a
project-root sandbox on filesystem arguments. See `_security.py` for the
primitives and the env vars that tune them
(`PYOBFUS_MCP_PROJECT_ROOT`, `PYOBFUS_MCP_RATE_LIMIT_PER_MIN`,
`PYOBFUS_MCP_AUDIT_LOG`, `PYOBFUS_MCP_DISABLED_TOOLS`).

Phase 3 (Pro funnel via MCP) adds:
  - `pro_value` field on `check_obfuscation_risks` (and `protect_project`)
    when the scan finds likely sensitive string literals (Pro's AES-256
    string encryption would protect them) and/or likely-PII literals
    (P2-12: emails / IPv4 / GUIDs / home-directory paths naming a real
    user -- `sensitive_literal_count` and `pii_literal_count` are reported
    as separate counts since the remediation story differs).
  - Structured `pro_unlock` field on `explain_preset` Pro-preset path,
    replacing the pre-Phase-3 CLI-only hint with full ROI framing.
  - `recommend_tier(path)` — analyzes a project, recommends free vs Pro
    with reasons and the exact command for each path.
  - `start_pro_trial()` — returns structured guidance for starting the
    5-day Pro trial (does not invoke the side effect; that's
    `pyobfus-trial start` on the user's shell).
  - `tier_context` field injected into Pro-funnel-relevant tools so the
    AI knows which tier the user is currently on.

All return dicts follow a stable shape with a `status` field
("success" | "warnings" | "error"), a free-text `ai_hint`, and (on success) a
machine-readable `next_tool` field (`{tool, reason, args}` — `tool=None` means
no further call is needed) so agents can chain steps deterministically instead
of re-parsing the prose hint each hop.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from pyobfus_mcp._security import (
    PathScopeError,
    secure_tool,
    validate_path,
)

# ---------------------------------------------------------------------------
# Agent-chaining convention (the `next_tool` field)
# ---------------------------------------------------------------------------


def _next_tool(
    tool: Optional[str], reason: str, args: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build the structured ``next_tool`` envelope every tool response carries.

    Unlike the free-text ``ai_hint`` (which a human or model reads as prose),
    ``next_tool`` is machine-readable: "call THIS tool with THESE args next".
    It lets a calling agent chain multi-step workflows deterministically
    instead of re-parsing English each hop, and keeps each hand-off cheap on
    tokens. ``tool=None`` means "no further pyobfus tool call is needed."
    """
    return {"tool": tool, "reason": reason, "args": args or {}}


# ---------------------------------------------------------------------------
# Pro-funnel constants (Phase 3) — sourced from canonical pyobfus modules so
# we never duplicate the Stripe URL or trial duration. If those move in core
# pyobfus, this file picks up the change automatically.
# ---------------------------------------------------------------------------


def _pro_unlock() -> Dict[str, Any]:
    """Structured Pro-tier unlock info, reused across every Pro-funnel surface.

    Reads the canonical Stripe URL from `pyobfus.constants.STRIPE_PAYMENT_LINK`
    and the trial duration from `pyobfus.trial.TRIAL_DURATION` so this MCP
    surface stays in sync with whatever `pyobfus-trial` and the README quote.
    """
    try:
        from pyobfus.constants import STRIPE_PAYMENT_LINK
        from pyobfus.trial import TRIAL_DURATION

        trial_days = TRIAL_DURATION.days
        checkout_url = STRIPE_PAYMENT_LINK
    except ImportError:
        # Fallback values if pyobfus core moves these symbols. Should not
        # happen in a properly installed env, but keep the field populated
        # so the AI agent always gets a usable hint.
        trial_days = 5
        checkout_url = "https://buy.stripe.com/00w4gr8ta9F78Fj8oI9k400"

    return {
        "trial_command": "pyobfus-trial start",
        "trial_duration_days": trial_days,
        "checkout_url": checkout_url,
        "price_usd": 45,
        "pricing_model": "one_time",  # not a subscription, not per-seat
        "money_back_guarantee_days": 30,
        "instant_delivery": True,
    }


def _user_tier() -> Dict[str, Any]:
    """Detect the user's current tier (community / trial / pro) from local state.

    Best-effort: reads `pyobfus.trial.get_trial_status()`. When `None` the user
    is on community tier (no trial started, no Pro purchased). When a trial
    is active we surface days remaining so the AI can frame upsell timing.

    Pro license detection is intentionally NOT implemented here — that
    requires the cloudflare-worker license check, which has online
    dependencies and isn't appropriate for a local-only tier hint.
    """
    try:
        from pyobfus.trial import get_trial_status

        status = get_trial_status()
    except ImportError:
        return {"user_tier": "community"}

    if status is None or not isinstance(status, dict):
        return {"user_tier": "community"}

    if status.get("active") is True:
        return {
            "user_tier": "trial",
            "trial_days_remaining": status.get("days_remaining"),
            "trial_expires_at": status.get("expires"),
        }

    return {"user_tier": "community"}


def _tier_context(tool_tier: str = "community") -> Dict[str, Any]:
    """Build the standard `tier_context` envelope for Pro-funnel-relevant tools.

    Args:
        tool_tier: Which tier the calling tool is itself in. "community" for
            tools every user can run (the original 5); "pro_funnel" for the
            new Phase 3 tools (`recommend_tier`, `start_pro_trial`) that
            exist specifically to surface Pro options.

    Returns:
        A dict combining tool tier, user tier (detected from local trial
        state), and the canonical Stripe URL for upsell anchoring.
    """
    ctx = {"tool_tier": tool_tier}
    ctx.update(_user_tier())
    ctx["pro_unlock_url"] = _pro_unlock()["checkout_url"]
    return ctx


# Sensitive-string-literal regex set used by `_count_sensitive_literals`.
# Each match increments the count by 1 (no double-counting per pattern). We
# err toward false positives (a 32-char alphanumeric literal that happens to
# be a hash, not a secret) because the worst case is recommending Pro string
# encryption when it isn't strictly needed — that's a soft-upsell, not a
# false security claim.
_SENSITIVE_LITERAL_PATTERNS = (
    # Quoted "api_key" / "secret_key" / "access_token" / "password" / "bearer"
    # appearing as keys in dicts or assignment LHS.
    re.compile(
        r"""['"]?(?:api[_-]?key|secret[_-]?key|access[_-]?token|password|bearer|auth[_-]?token)['"]?\s*[:=]""",
        re.IGNORECASE,
    ),
    # Stripe-style live/test keys (very specific).
    re.compile(r"""['"](?:sk_live|sk_test|pk_live|pk_test|rk_live|rk_test)_[A-Za-z0-9]{16,}['"]"""),
    # AWS-style access key IDs (20 chars, uppercase + digits, starts with AKIA / ASIA).
    re.compile(r"""['"](?:AKIA|ASIA)[0-9A-Z]{16}['"]"""),
    # Generic long opaque alphanumeric string literals — common shape for
    # JWT segments, hashed tokens, opaque bearer values.
    re.compile(r"""['"][A-Za-z0-9_\-]{40,}['"]"""),
)

# PII-shape regex set (P2-12) — a distinct signal class from
# _SENSITIVE_LITERAL_PATTERNS above: these are personally-identifiable-data
# shapes (who a person is / where they are), not credential shapes (what
# lets you authenticate as them). Kept as a separate pattern set + separate
# count so callers can tell "this project leaks secrets" from "this project
# leaks PII" — the Pro remediation story differs (encryption vs. redaction/
# data minimization).
_PII_LITERAL_PATTERNS = (
    # Email addresses.
    re.compile(r"""['"][A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}['"]"""),
    # IPv4 addresses (quoted string literal; deliberately not IPv6 -- IPv6
    # literal shapes collide too easily with hex/hash literals to be a
    # reliable heuristic without much more careful boundary matching).
    re.compile(r"""['"](?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)['"]"""),
    # GUID / UUID (any version).
    re.compile(
        r"""['"][0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}['"]"""
    ),
    # Filesystem paths that embed a real username (home-directory leak) --
    # deliberately narrow: a bare "/tmp/foo" or "src/utils.py" is not PII,
    # but "/home/jsmith/..." or "C:\Users\jsmith\..." names a real person.
    re.compile(
        r"""['"](?:/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+|"""
        r"""[A-Za-z]:\\{1,2}Users\\{1,2}[A-Za-z0-9_.-]+)"""
    ),
)


def _count_pattern_matches(
    target: Path,
    patterns: tuple,
    *,
    max_files: int = 200,
    max_bytes_per_file: int = 200_000,
) -> int:
    """Count regex-pattern occurrences across `.py` files under target.

    Shared by `_count_sensitive_literals` and `_count_pii_literals` --
    heuristic-only, caps file count and per-file byte read so the scan
    stays bounded on monorepos.
    """
    if target.is_file():
        files: List[Path] = [target] if target.suffix == ".py" else []
    elif target.is_dir():
        files = sorted(target.rglob("*.py"))[:max_files]
    else:
        return 0

    total = 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")[:max_bytes_per_file]
        except OSError:
            continue
        for pat in patterns:
            total += len(pat.findall(text))
    return total


def _count_sensitive_literals(
    target: Path, *, max_files: int = 200, max_bytes_per_file: int = 200_000
) -> int:
    """Count likely-sensitive (credential-shaped) string-literal occurrences.

    Heuristic-only — false positives expected (e.g. a long random hash literal
    in a test fixture might count).
    """
    return _count_pattern_matches(
        target,
        _SENSITIVE_LITERAL_PATTERNS,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
    )


def _count_pii_literals(
    target: Path, *, max_files: int = 200, max_bytes_per_file: int = 200_000
) -> int:
    """Count likely-PII (email / IPv4 / GUID / home-directory-path) occurrences.

    A distinct signal class from `_count_sensitive_literals` -- see
    `_PII_LITERAL_PATTERNS` for the rationale. Heuristic-only.
    """
    return _count_pattern_matches(
        target,
        _PII_LITERAL_PATTERNS,
        max_files=max_files,
        max_bytes_per_file=max_bytes_per_file,
    )


def _pro_value_for_scan(
    sensitive_literal_count: int,
    high_severity_findings: int,
    pii_literal_count: int = 0,
) -> Optional[Dict[str, Any]]:
    """Compute the `pro_value` envelope for a `check_obfuscation_risks` scan.

    Returns `None` when the project doesn't surface a Pro upsell signal (no
    sensitive literals, no PII literals, no high-severity findings). Returns
    a structured recommendation dict otherwise. Strength tiers:

    - Sensitive literals: 1-3 = low / 4-15 = medium / 16+ = high
    - PII literals: 1-3 = low / 4-15 = medium / 16+ = high (same bands --
      both are "how many string literals of this shape" counts)
    - High-severity findings: 1-2 = low / 3-5 = medium / 6+ = high

    The strongest of the three signals wins. We err on the soft-upsell
    side — the field is a hint to the AI, not a license-required gate.
    """
    if sensitive_literal_count == 0 and pii_literal_count == 0 and high_severity_findings == 0:
        return None

    def _strength(count: int, low: int, mid: int) -> str:
        if count >= mid:
            return "high"
        if count >= low:
            return "medium"
        if count > 0:
            return "low"
        return "none"

    lit_strength = _strength(sensitive_literal_count, low=1, mid=16)
    pii_strength = _strength(pii_literal_count, low=1, mid=16)
    sev_strength = _strength(high_severity_findings, low=1, mid=6)

    # Pick the strongest signal.
    rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    overall = max((lit_strength, pii_strength, sev_strength), key=lambda s: rank[s])

    applicable: List[str] = []
    rationale_parts: List[str] = []
    if sensitive_literal_count > 0:
        applicable.append("string_encryption")
        applicable.append("runtime_vault")
        rationale_parts.append(
            f"Found {sensitive_literal_count} likely-sensitive string "
            f"literal occurrence(s) (API keys, tokens, opaque bearer values). "
            f"Pro's AES-256 string encryption hides these from `strings`-style "
            f"inspection; the v0.5 Runtime String Vault (vault_secrets({{...}})) "
            f"goes further with lazy per-entry decryption."
        )
    if pii_literal_count > 0:
        applicable.append("string_encryption")
        rationale_parts.append(
            f"Found {pii_literal_count} likely-PII string literal "
            f"occurrence(s) (emails, IPv4 addresses, GUIDs, or home-directory "
            f"paths naming a real user). Consider whether these belong in "
            f"source at all (data minimization) before reaching for "
            f"encryption; if they must ship, Pro's AES-256 string encryption "
            f"applies here too."
        )
    if high_severity_findings > 0:
        applicable.append("anti_debugging")
        rationale_parts.append(
            f"Scan flagged {high_severity_findings} high-severity finding(s). "
            f"Pro's anti-debugging hooks make static + dynamic reverse "
            f"engineering measurably harder."
        )

    # de-dupe while preserving order (string_encryption can be added twice above)
    applicable = list(dict.fromkeys(applicable))

    return {
        "applicable_features": applicable,
        "rationale": " ".join(rationale_parts),
        "sensitive_literal_count": sensitive_literal_count,
        "pii_literal_count": pii_literal_count,
        "high_severity_findings": high_severity_findings,
        "recommendation_strength": overall,
        **_pro_unlock(),
    }


@secure_tool()
def check_obfuscation_risks(path: str, verify_dependencies_online: bool = False) -> Dict[str, Any]:
    """Scan a Python project for patterns that may break obfuscation.

    Wraps `pyobfus --check`. Returns a structured report with severity
    counts, detected frameworks, a suggested preset, and an `ai_hint`
    telling the calling agent the exact command to run next.

    Also runs the dependency-hallucination advisory (flags declared
    dependencies in requirements*.txt / pyproject.toml that don't resolve
    on public PyPI -- a signal of AI-hallucinated "slopsquatting" package
    names). Unlike `pyobfus --check` on the CLI, this tool does NOT make
    outbound network calls by default -- pyobfus-mcp otherwise has zero
    egress (see docs/MCP_SECURITY_SCAN.md), and that stays true unless a
    caller explicitly opts in here.

    Args:
        path: Path to a Python file or directory to scan.
        verify_dependencies_online: Set True to let this call reach out to
            pypi.org and verify declared dependencies actually exist there.
            Off by default (no network access). When off, dependency files
            are still located but not checked, and no risk is reported for
            them.

    Returns:
        Dict with keys: status, files_scanned, severity_counts,
        frameworks, suggested_preset, suggested_excludes, risks,
        ai_hint, exit_code.
    """
    try:
        from pyobfus.core.preflight import PreflightChecker
    except ImportError as e:
        return _error("PyobfusNotInstalled", str(e), "pip install pyobfus")

    try:
        target = validate_path(path, must_exist=True)
    except PathScopeError as e:
        return _error(
            "PathScopeError",
            str(e),
            "Use a path inside PYOBFUS_MCP_PROJECT_ROOT (default: server cwd).",
        )
    except FileNotFoundError as e:
        return _error("PathNotFound", str(e), "Double-check the path and try again.")

    report = PreflightChecker(
        check_dependencies=True, offline=not verify_dependencies_online
    ).check_path(target)
    payload = report.to_dict()
    payload["status"] = "success" if payload.get("exit_code", 0) == 0 else "warnings"

    # Phase 3: surface Pro funnel signal when the scan finds patterns Pro
    # features (AES-256 string encryption, anti-debugging) would protect.
    # P2-12: also scan for PII-shaped literals (emails/IPv4/GUIDs/home-dir
    # paths) -- a distinct signal class from credential-shaped literals.
    sensitive_count = _count_sensitive_literals(target)
    pii_count = _count_pii_literals(target)
    high_sev = int((payload.get("severity_counts") or {}).get("high", 0))
    pro_value = _pro_value_for_scan(sensitive_count, high_sev, pii_count)
    if pro_value is not None:
        payload["pro_value"] = pro_value
    payload["tier_context"] = _tier_context(tool_tier="community")
    payload["next_tool"] = _next_tool(
        "protect_project",
        "obfuscate-and-verify now that risks are known",
        {"path": path, "preset": payload.get("suggested_preset")},
    )

    return payload


@secure_tool()
def generate_pyobfus_config(
    path: str, preset_override: Optional[str] = None, write: bool = False
) -> Dict[str, Any]:
    """Generate a pyobfus.yaml configuration for a Python project.

    Wraps `pyobfus --init`. By default this returns the proposed YAML
    *text* in the response without touching the filesystem, so an AI
    agent can preview the config before asking the user whether to
    write it. Set `write=True` to persist to disk at <path>/pyobfus.yaml.

    Args:
        path: Root of the Python project to scan.
        preset_override: Optional preset name to force (safe, balanced,
            aggressive, fastapi, django, flask, pydantic, click,
            sqlalchemy, ml). Default: auto-detected.
        write: If True, writes the generated file to disk.

    Returns:
        Dict with keys: status, config_path, preset, excludes,
        frameworks_detected, files_scanned, high_risk_findings, yaml,
        written, ai_hint.
    """
    try:
        from pyobfus.core.init_config import build_init_result
    except ImportError as e:
        return _error("PyobfusNotInstalled", str(e), "pip install pyobfus")

    try:
        target = validate_path(path, must_exist=True)
    except PathScopeError as e:
        return _error(
            "PathScopeError",
            str(e),
            "Use a path inside PYOBFUS_MCP_PROJECT_ROOT (default: server cwd).",
        )
    except FileNotFoundError as e:
        return _error("PathNotFound", str(e), "Pass a valid project directory.")

    result = build_init_result(target, preset_override=preset_override)

    if write:
        # The config_path is computed by build_init_result as <target>/pyobfus.yaml,
        # so it inherits the same scope as the validated `target`.
        result.config_path.write_text(result.yaml_text, encoding="utf-8")
        result.written = True

    payload = result.to_dict()
    payload["status"] = "success"
    payload["yaml"] = result.yaml_text
    payload["ai_hint"] = (
        f"Review the YAML above. When ready, run "
        f"'pyobfus {path} -o dist/ -c {result.config_path}'."
        if not write
        else f"Wrote {result.config_path}. Next: pyobfus {path} -o dist/ -c {result.config_path}"
    )
    payload["next_tool"] = _next_tool(
        "protect_project",
        "obfuscate-and-verify with the detected preset",
        {"path": path, "preset": payload.get("preset")},
    )
    return payload


@secure_tool(redact_params={"trace"})
def unmap_stack_trace(trace: str, mapping_path: str) -> Dict[str, Any]:
    """Reverse obfuscated identifiers in a stack trace using a mapping.json.

    Wraps `pyobfus --unmap`. Accepts the trace as a literal string (most
    useful for agent workflows where the trace is already in the chat
    buffer); for large logs, callers can pre-read the file and pass
    its contents.

    The `trace` parameter is redacted in audit logs (it can contain
    user data captured by the original crash); only its length is
    recorded.

    Args:
        trace: Obfuscated stack trace or error log as plain text.
        mapping_path: Filesystem path to a mapping.json produced by
            `pyobfus ... --save-mapping PATH`.

    Returns:
        Dict with keys: status, original_trace, unmapped_trace,
        mapping_stats, ai_hint.
    """
    try:
        from pyobfus.core.mapping import ObfuscationMapping
    except ImportError as e:
        return _error("PyobfusNotInstalled", str(e), "pip install pyobfus")

    try:
        mp = validate_path(mapping_path, must_exist=True)
    except PathScopeError as e:
        return _error(
            "PathScopeError",
            str(e),
            "Use a mapping path inside PYOBFUS_MCP_PROJECT_ROOT.",
        )
    except FileNotFoundError as e:
        return _error(
            "MappingNotFound",
            str(e),
            "Generate one with: pyobfus src/ -o dist/ --save-mapping mapping.json",
        )

    try:
        mapping = ObfuscationMapping.load(mp)
    except (ValueError, OSError) as e:
        return _error("InvalidMapping", str(e), "Regenerate the mapping file.")

    unmapped = mapping.unmap_text(trace)
    return {
        "status": "success",
        "original_trace": trace,
        "unmapped_trace": unmapped,
        "mapping_stats": mapping.stats(),
        "ai_hint": (
            "Names are reversed, but line numbers still point to the obfuscated "
            "file. Cross-reference with the original source if needed."
        ),
        "next_tool": _next_tool(
            None, "trace is de-obfuscated; read the unmapped_trace and continue debugging"
        ),
    }


@secure_tool()
def list_presets() -> Dict[str, Any]:
    """List every pyobfus preset available, grouped by tier.

    Returns:
        Dict with keys: status, community, framework, pro, ai_hint.
    """
    try:
        from pyobfus.config import ObfuscationConfig
    except ImportError as e:
        return _error("PyobfusNotInstalled", str(e), "pip install pyobfus")

    framework = sorted(ObfuscationConfig.FRAMEWORK_PRESETS)
    all_presets = ObfuscationConfig.list_presets()
    pro = {"trial", "commercial", "library", "maximum"}
    community = [p for p in all_presets if p not in framework and p not in pro]

    return {
        "status": "success",
        "community": community,
        "framework": framework,
        "pro": sorted(pro),
        "ai_hint": (
            "Framework presets are free and the recommended starting point "
            "when your project imports fastapi/django/flask/pydantic/click/"
            "sqlalchemy or ML/model-serving libraries. Fall back to 'balanced' otherwise."
        ),
        "next_tool": _next_tool("explain_preset", "inspect a specific preset before applying it"),
    }


@secure_tool()
def explain_preset(name: str) -> Dict[str, Any]:
    """Describe what a named preset changes compared to balanced.

    Returns the concrete exclude_names count, preserve_param_names,
    remove_docstrings flag, and any framework-specific exclude patterns
    so an AI agent can explain the preset to the user before applying it.

    Args:
        name: Preset name (e.g. "fastapi", "pydantic", "safe").

    Returns:
        Dict with keys: status, preset, level, exclude_names_count,
        exclude_patterns, preserve_param_names, remove_docstrings,
        ai_hint.
    """
    try:
        from pyobfus.config import ObfuscationConfig
    except ImportError as e:
        return _error("PyobfusNotInstalled", str(e), "pip install pyobfus")

    try:
        cfg = ObfuscationConfig.get_preset(name)
    except ValueError as e:
        return _error("UnknownPreset", str(e), "Call list_presets to see valid names.")

    payload: Dict[str, Any] = {
        "status": "success",
        "preset": name.lower(),
        "level": cfg.level,
        "exclude_names_count": len(cfg.exclude_names),
        "exclude_patterns": list(cfg.exclude_patterns),
        "preserve_param_names": cfg.preserve_param_names,
        "remove_docstrings": cfg.remove_docstrings,
        "string_encoding": cfg.string_encoding,
    }

    if cfg.level == "community":
        payload["ai_hint"] = f"Apply with: pyobfus src/ -o dist/ --preset {name.lower()}"
    else:
        # Phase 3: replace the bare CLI-only hint with full ROI framing +
        # the structured pro_unlock dict so an MCP client (or the AI on the
        # other end) can render a checkout link / pricing / trial duration
        # without round-tripping back to a separate tool.
        unlock = _pro_unlock()
        payload["pro_unlock"] = unlock
        payload["ai_hint"] = (
            f"'{name}' is a Pro preset (level=pro). Free {unlock['trial_duration_days']}-day trial via "
            f"`{unlock['trial_command']}` (no registration). Full unlock: "
            f"${unlock['price_usd']} USD one-time at {unlock['checkout_url']} "
            f"({unlock['money_back_guarantee_days']}-day money-back guarantee, instant delivery)."
        )

    payload["tier_context"] = _tier_context(tool_tier="community")
    payload["next_tool"] = (
        _next_tool(
            "protect_project",
            "apply this community preset and verify the result",
            {"preset": name.lower()},
        )
        if cfg.level == "community"
        else _next_tool("start_pro_trial", "this is a Pro preset; offer the trial before applying")
    )
    return payload


@secure_tool()
def recommend_tier(path: str) -> Dict[str, Any]:
    """Analyze a Python project and recommend the best pyobfus tier (community vs Pro).

    Wraps `check_obfuscation_risks` plus a sensitive-string-literal heuristic
    to produce a tier recommendation with reasoning. Use this before
    suggesting an obfuscation command — the recommendation distinguishes
    "community is enough" projects from "Pro will materially help" ones.

    The tool itself is in the `pro_funnel` tier (its purpose is upsell
    surfacing); the recommendation it returns may still be "community".

    Args:
        path: Path to a Python file or directory to analyze.

    Returns:
        Dict with keys: status, recommended_tier ("community" | "pro"),
        reasons, free_tier_capabilities, pro_tier_capabilities,
        free_action, pro_action, tier_context, ai_hint.
    """
    try:
        from pyobfus.core.preflight import PreflightChecker
    except ImportError as e:
        return _error("PyobfusNotInstalled", str(e), "pip install pyobfus")

    try:
        target = validate_path(path, must_exist=True)
    except PathScopeError as e:
        return _error(
            "PathScopeError",
            str(e),
            "Use a path inside PYOBFUS_MCP_PROJECT_ROOT (default: server cwd).",
        )
    except FileNotFoundError as e:
        return _error("PathNotFound", str(e), "Pass a valid project path.")

    report = PreflightChecker().check_path(target)
    report_dict = report.to_dict()
    high_sev = int((report_dict.get("severity_counts") or {}).get("high", 0))
    sensitive_count = _count_sensitive_literals(target)
    frameworks = [fw.get("name") for fw in (report_dict.get("frameworks") or [])]

    # Decision rule: Pro recommended if sensitive_count >= 4 OR high_sev >= 3.
    # Otherwise community (which has framework presets that cover most apps).
    pro_recommended = sensitive_count >= 4 or high_sev >= 3

    reasons: List[str] = []
    if sensitive_count > 0:
        reasons.append(
            f"Found {sensitive_count} likely-sensitive string literal(s) — "
            f"{'Pro AES-256 string encryption strongly recommended' if pro_recommended else 'community is fine; consider Pro if those are real secrets'}."
        )
    if high_sev > 0:
        reasons.append(f"Scan flagged {high_sev} high-severity finding(s).")
    if frameworks:
        reasons.append(
            f"Detected framework(s): {', '.join(frameworks)} — covered by community framework presets."
        )
    if not reasons:
        reasons.append(
            "No risk patterns or sensitive literals detected — community 'balanced' preset is sufficient."
        )

    free_action = {
        "command": (
            f"pyobfus {path} -o dist/ --preset "
            f"{report_dict.get('suggested_preset') or 'balanced'} --save-mapping mapping.json"
        ),
        "estimated_protection": "moderate (name mangling + framework-aware excludes)",
    }
    pro_action = {
        **_pro_unlock(),
        "estimated_protection": (
            "high (adds AES-256 string encryption + anti-debugging, plus the v0.5 "
            "mechanisms: Selective Opacity, forensic watermarking, Runtime String "
            "Vault, @seal_code, --scrub-traceback, and v0.5.7's --import-obfuscation)"
        ),
    }

    payload: Dict[str, Any] = {
        "status": "success",
        "recommended_tier": "pro" if pro_recommended else "community",
        "reasons": reasons,
        "free_tier_capabilities": [
            "AST-based name mangling (classes, functions, locals)",
            "Framework presets (FastAPI, Django, Flask, Pydantic, Click, SQLAlchemy)",
            "JSON CLI for AI agents (--json + ai_hint fields)",
            "Reverse stack-trace mapping (--save-mapping + --unmap)",
            "No file-count or line-count limit on the project itself (unlike PyArmor's "
            "free trial, capped around 935-940 lines/file, measured 2026-05-09) -- "
            "project size alone is never a reason this tool needs Pro",
        ],
        "pro_tier_capabilities": [
            "AES-256 string encryption, control-flow flattening, dead-code injection, anti-debugging",
            "Selective Opacity (v0.5) — per-symbol AES-256-GCM encryption of chosen functions with lazy code materialization",
            "Forensic watermarking (v0.5) — per-buyer deterministic builds for piracy traceback",
            "Runtime String Vault (v0.5) — encrypted KV namespace for runtime secrets",
            "@seal_code bytecode integrity + --scrub-traceback production traceback encryption (v0.5)",
            "--import-obfuscation (v0.5.7) — rewrites top-level imports into runtime importlib/__import__ calls with automatic AES string encryption of module/symbol names",
            "Available as `pyobfus build` flags (v0.5.1) and the `pyobfus_pro` API",
        ],
        "free_action": free_action,
        "pro_action": pro_action,
        "scan_summary": {
            "sensitive_literal_count": sensitive_count,
            "high_severity_findings": high_sev,
            "frameworks_detected": frameworks,
            "files_scanned": report_dict.get("files_scanned", 0),
        },
        "tier_context": _tier_context(tool_tier="pro_funnel"),
    }
    payload["ai_hint"] = (
        f"Run: {free_action['command']}"
        if not pro_recommended
        else (
            f"Pro recommended ({sensitive_count} sensitive literal(s) + {high_sev} high-sev finding(s)). "
            f"Try free trial first: {pro_action['trial_command']} "
            f"(no card, {pro_action['trial_duration_days']} days). "
            f"Or buy direct: {pro_action['checkout_url']} (${pro_action['price_usd']} USD)."
        )
    )
    payload["next_tool"] = (
        _next_tool(
            "start_pro_trial",
            "Pro is recommended; surface the trial before obfuscating",
        )
        if pro_recommended
        else _next_tool(
            "protect_project", "community tier is sufficient; obfuscate and verify", {"path": path}
        )
    )
    return payload


@secure_tool()
def start_pro_trial() -> Dict[str, Any]:
    """Return structured guidance for starting a 5-day pyobfus Pro trial.

    Does NOT actually start the trial — that's the side-effecting
    `pyobfus-trial start` shell command, which is what an AI agent should
    surface to the user. This tool just returns the structured info an
    agent needs to present a clear yes/no to the user (trial command,
    duration, included features, post-trial pricing) without round-
    tripping into the README.

    Returns:
        Dict with keys: status, trial_command, trial_duration_days,
        trial_features, post_trial_options, current_status, tier_context,
        ai_hint.
    """
    user = _user_tier()
    current_status: Dict[str, Any]
    if user.get("user_tier") == "trial":
        current_status = {
            "trial_already_active": True,
            "trial_days_remaining": user.get("trial_days_remaining"),
            "trial_expires_at": user.get("trial_expires_at"),
        }
        ai_hint = (
            f"User already has an active trial — {user.get('trial_days_remaining')} "
            f"day(s) remaining. No need to re-run `pyobfus-trial start`. "
            f"After expiry, full unlock at {_pro_unlock()['checkout_url']}."
        )
    else:
        current_status = {"trial_already_active": False}
        ai_hint = (
            "User should run `pyobfus-trial start` in their shell to begin "
            "the 5-day Pro trial. No registration or credit card required. "
            "After trial, full unlock is $45 USD one-time at the checkout URL."
        )

    unlock = _pro_unlock()
    return {
        "status": "success",
        "trial_command": unlock["trial_command"],
        "trial_duration_days": unlock["trial_duration_days"],
        "trial_features": [
            "AES-256 string encryption, control-flow flattening, dead-code injection, anti-debugging",
            "Selective Opacity (v0.5) — per-symbol AES-256-GCM encryption of chosen functions",
            "Forensic watermarking (v0.5) — per-buyer deterministic builds for piracy traceback",
            "Runtime String Vault (v0.5) — encrypted KV namespace for runtime secrets",
            "@seal_code bytecode integrity + --scrub-traceback production traceback encryption (v0.5)",
            "--import-obfuscation (v0.5.7) — rewrites top-level imports into runtime importlib/__import__ calls with automatic AES string encryption of module/symbol names",
            "Unlimited files and lines of code",
        ],
        "post_trial_options": {
            "checkout_url": unlock["checkout_url"],
            "price_usd": unlock["price_usd"],
            "money_back_guarantee_days": unlock["money_back_guarantee_days"],
            "instant_delivery": unlock["instant_delivery"],
        },
        "current_status": current_status,
        "tier_context": _tier_context(tool_tier="pro_funnel"),
        "ai_hint": ai_hint,
        "next_tool": _next_tool(
            None,
            "user runs `pyobfus-trial start` in their shell; no further tool call",
        ),
    }


# ---------------------------------------------------------------------------
# protect_project — the one-call, self-verifying obfuscation pipeline
# ---------------------------------------------------------------------------

# Exception class names in a failed-import traceback that mean obfuscation
# genuinely *broke* the code (a renamed reference didn't resolve, a rewritten
# import points nowhere, the output won't parse). Anything else (e.g. the
# module needs argv, network, or env at import time) is treated as
# "inconclusive" — it doesn't prove breakage, so it lowers confidence rather
# than failing the verification outright.
_VERIFY_BREAKING_ERRORS = (
    "SyntaxError",
    "IndentationError",
    "ImportError",
    "ModuleNotFoundError",
    "NameError",
    "AttributeError",
)


def _obfuscate_command() -> List[str]:
    """Return the argv prefix that invokes the pyobfus CLI in a subprocess.

    Prefers ``python -m pyobfus`` using the *same* interpreter that runs this
    server — where ``pyobfus`` is guaranteed importable because pyobfus-mcp
    depends on it. Falls back to a ``-c`` launcher that calls
    ``pyobfus.cli.main`` directly, so the tool still works against an
    installed pyobfus that predates the ``pyobfus/__main__.py`` module entry.
    """
    if importlib.util.find_spec("pyobfus.__main__") is not None:
        return [sys.executable, "-m", "pyobfus"]
    return [
        sys.executable,
        "-c",
        "import sys; from pyobfus.cli import main; " "main(args=sys.argv[1:], prog_name='pyobfus')",
    ]


def _discover_top_level_modules(out: Path, *, limit: int = 50) -> List[str]:
    """Top-level importable module names produced in an obfuscated output dir."""
    mods: List[str] = []
    for child in sorted(out.iterdir()):
        if child.is_dir() and (child / "__init__.py").exists():
            mods.append(child.name)
        elif child.is_file() and child.suffix == ".py" and child.name != "__init__.py":
            mods.append(child.stem)
        if len(mods) >= limit:
            break
    return mods


def _classify_import_failure(stderr: str) -> str:
    """Return 'broke' if stderr names a breaking error, else 'inconclusive'."""
    for err in _VERIFY_BREAKING_ERRORS:
        if err in stderr:
            return "broke"
    return "inconclusive"


def _run_verification(
    out: Path,
    *,
    verify_cmd: Optional[str],
    allow_cmd: bool,
    timeout: int,
) -> Dict[str, Any]:
    """Round-trip-verify obfuscated output WITHOUT importing it into this process.

    Two always-safe, API-agnostic signals (a renamed-but-consistent codebase
    still passes both):

      1. ``compileall`` — every output module byte-compiles (catches any
         structural/syntactic breakage the transform could introduce).
      2. import smoke test — each top-level module imports in a *subprocess*
         (catches broken cross-file references / mis-rewritten imports).

    Plus an optional caller-supplied ``verify_cmd`` (e.g. an end-to-end app
    check) — gated behind ``PYOBFUS_MCP_ALLOW_VERIFY_CMD`` because it runs an
    arbitrary command. NOTE for callers: ``verify_cmd`` should exercise the
    app end-to-end, NOT unit tests bound to internal symbol names — those are
    *expected* to fail once the public surface is renamed, and would be a
    false negative here.
    """
    result: Dict[str, Any] = {}

    # 1. compileall ---------------------------------------------------------
    compile_proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", str(out)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    compile_ok = compile_proc.returncode == 0
    result["compile_ok"] = compile_ok
    if not compile_ok:
        result["compile_error"] = (compile_proc.stdout + compile_proc.stderr).strip()[-800:]

    # 2. import smoke test --------------------------------------------------
    modules = _discover_top_level_modules(out)
    import_code = (
        "import importlib, sys; "
        "sys.path.insert(0, sys.argv[1]); "
        "importlib.import_module(sys.argv[2])"
    )
    modules_ok: List[str] = []
    modules_broke: List[Dict[str, str]] = []
    import_inconclusive: List[Dict[str, str]] = []
    for mod in modules:
        try:
            proc = subprocess.run(
                [sys.executable, "-c", import_code, str(out), mod],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(out),
            )
        except subprocess.TimeoutExpired:
            import_inconclusive.append({"module": mod, "reason": "import timed out"})
            continue
        if proc.returncode == 0:
            modules_ok.append(mod)
        else:
            tail = proc.stderr.strip()[-400:]
            if _classify_import_failure(proc.stderr) == "broke":
                modules_broke.append({"module": mod, "error": tail})
            else:
                import_inconclusive.append({"module": mod, "error": tail})

    result["modules_checked"] = len(modules)
    result["modules_imported_ok"] = modules_ok
    result["modules_broke"] = modules_broke
    result["import_inconclusive"] = import_inconclusive

    # 3. optional caller verify command ------------------------------------
    cmd_ok: Optional[bool] = None
    if verify_cmd:
        if not allow_cmd:
            result["verify_cmd"] = {
                "ran": False,
                "skipped_reason": (
                    "Arbitrary verify_cmd execution is disabled by default. "
                    "Set PYOBFUS_MCP_ALLOW_VERIFY_CMD=1 to enable."
                ),
            }
        else:
            try:
                cproc = subprocess.run(
                    shlex.split(verify_cmd),
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=str(out),
                    env={
                        **os.environ,
                        "PYTHONPATH": os.pathsep.join([str(out), os.environ.get("PYTHONPATH", "")]),
                    },
                )
                cmd_ok = cproc.returncode == 0
                result["verify_cmd"] = {
                    "ran": True,
                    "command": verify_cmd,
                    "exit_code": cproc.returncode,
                    "passed": cmd_ok,
                    "output_tail": (cproc.stdout + cproc.stderr).strip()[-800:],
                }
            except (OSError, subprocess.TimeoutExpired) as e:
                cmd_ok = False
                result["verify_cmd"] = {"ran": True, "command": verify_cmd, "error": str(e)}

    # Decide verified + confidence -----------------------------------------
    verified = compile_ok and not modules_broke
    if cmd_ok is not None:
        verified = verified and cmd_ok
        confidence = "high" if verified else "low"
    elif verified and not import_inconclusive:
        confidence = "medium"
    elif verified:
        confidence = "low"  # compiled + no breakage, but some imports inconclusive
    else:
        confidence = "low"

    result["verified"] = verified
    result["confidence"] = confidence
    return result


@secure_tool()
def protect_project(
    path: str,
    output_dir: str = "dist",
    preset: Optional[str] = None,
    verify: bool = True,
    verify_cmd: Optional[str] = None,
    save_mapping: bool = True,
    trace_marker: bool = True,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Obfuscate a Python project end-to-end and verify it still works — in one call.

    This is the high-level tool an AI agent reaches for when the user says
    "protect this code before I ship it". It runs the whole pipeline and,
    crucially, **self-verifies** the result so the agent can report a green
    check instead of hoping the transform didn't break anything:

        scan risks  →  pick a framework-aware preset  →  obfuscate
                    →  byte-compile + import-smoke-test the output
                    →  return verified: true/false (+ what changed)

    Verification never imports the obfuscated code into this server process —
    every check runs in a subprocess (see ``_run_verification``).

    Args:
        path: Python file or directory to protect (must be inside the
            server's project-root sandbox).
        output_dir: Where to write obfuscated output (default ``dist``).
        preset: Force a preset (e.g. ``fastapi``, ``balanced``). Default:
            auto-detected from a preflight framework scan.
        verify: Run the round-trip verification (default True). Set False to
            skip (faster, but you lose the green check).
        verify_cmd: Optional end-to-end check (e.g. ``python -m myapp --selftest``)
            run against the obfuscated output. Gated behind
            ``PYOBFUS_MCP_ALLOW_VERIFY_CMD=1``. Use an APP-level check, not
            unit tests bound to internal names (those are expected to fail
            once the public surface is renamed).
        save_mapping: Write the de-obfuscation mapping next to the output so
            tracebacks can later be reversed with ``unmap_stack_trace``
            (default True). The mapping is the de-obfuscation key — keep it
            private; it is intentionally NOT written inside ``output_dir``.
        trace_marker: Stamp each obfuscated file with a ``# pyobfus:obfuscated``
            header (id + mapping filename + the exact unmap command) so an agent
            that later opens one of these files from a traceback knows to
            reverse the names (default True; requires save_mapping).
        timeout: Per-subprocess timeout in seconds (default 120).

    Returns:
        Dict with: status, verified, confidence, preset_used, input, output,
        obfuscation (stats + trace_marker_id), mapping_path,
        mapping_security_note, risks, pro_value (optional), verification,
        ai_hint, next_tool, tier_context.
    """
    # --- imports up front so a missing core install fails fast -------------
    try:
        from pyobfus.core.preflight import PreflightChecker
    except ImportError as e:
        return _error("PyobfusNotInstalled", str(e), "pip install pyobfus")

    # --- validate + scope the source and the write targets -----------------
    try:
        target = validate_path(path, must_exist=True)
        out = validate_path(output_dir, must_exist=False)
    except PathScopeError as e:
        return _error(
            "PathScopeError",
            str(e),
            "Keep path and output_dir inside PYOBFUS_MCP_PROJECT_ROOT (default: server cwd).",
        )
    except FileNotFoundError as e:
        return _error("PathNotFound", str(e), "Double-check the source path and try again.")

    if out == target or out in target.parents or target in out.parents:
        return _error(
            "BadOutputDir",
            f"output_dir {out} overlaps the source {target}.",
            "Pick an output_dir outside the source tree (e.g. 'dist').",
        )

    # --- 1. preflight scan → preset selection ------------------------------
    report = PreflightChecker().check_path(target)
    report_dict = report.to_dict()
    severity = report_dict.get("severity_counts") or {}
    high_sev = int(severity.get("high", 0))
    frameworks = [fw.get("name") for fw in (report_dict.get("frameworks") or [])]
    preset_used = preset or report_dict.get("suggested_preset") or "balanced"

    # --- 2. obfuscate via the real CLI (--json) ----------------------------
    # Mapping is written as a SIBLING of the output dir, never inside it, so
    # it never ships with the protected artifact.
    mapping_path = out.parent / f"{out.name}.mapping.json"
    cmd = _obfuscate_command() + [str(target), "-o", str(out), "--preset", preset_used, "--json"]
    if save_mapping:
        cmd += ["--save-mapping", str(mapping_path)]
        # Stamp each obfuscated file with a '# pyobfus:obfuscated' header so an
        # agent that later lands in one of these files from a traceback knows
        # to reverse the names with unmap_stack_trace. On by default here (the
        # AI-native path); harmless comment lines that don't affect execution.
        if trace_marker:
            cmd += ["--trace-marker"]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return _error(
            "ObfuscationTimeout",
            f"Obfuscation exceeded {timeout}s.",
            "Raise the `timeout` argument or obfuscate a smaller subtree.",
        )

    try:
        obf = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return _error(
            "ObfuscationFailed",
            (proc.stderr or proc.stdout or "no output").strip()[-800:],
            "Run `check_obfuscation_risks` on this path to find the blocker.",
        )

    if obf.get("status") != "success":
        return {
            "status": "error",
            "error_type": "ObfuscationFailed",
            "message": obf.get("message", "obfuscation did not succeed"),
            "obfuscation": obf,
            "ai_hint": "Inspect the obfuscation report; run check_obfuscation_risks first.",
            "next_tool": _next_tool(
                "check_obfuscation_risks", "find what blocks obfuscation", {"path": path}
            ),
        }

    # --- 3. round-trip verification (subprocess-isolated) ------------------
    verification: Optional[Dict[str, Any]] = None
    verified: Optional[bool] = None
    confidence = "unverified"
    if verify:
        allow_cmd = os.environ.get("PYOBFUS_MCP_ALLOW_VERIFY_CMD", "").lower() in (
            "1",
            "true",
            "yes",
        )
        verification = _run_verification(
            out, verify_cmd=verify_cmd, allow_cmd=allow_cmd, timeout=timeout
        )
        verified = verification["verified"]
        confidence = verification["confidence"]

    # --- assemble payload --------------------------------------------------
    stats = obf.get("stats") or {}
    pro_value = _pro_value_for_scan(
        _count_sensitive_literals(target), high_sev, _count_pii_literals(target)
    )

    if verify and not verified:
        status = "warnings"
        ai_hint = (
            "Obfuscation ran but verification did NOT pass — the obfuscated "
            "output failed to compile or import. Do NOT ship it. Inspect "
            "verification.modules_broke / compile_error, then re-run "
            "check_obfuscation_risks to find the offending construct."
        )
        next_tool = _next_tool(
            "check_obfuscation_risks",
            "diagnose why the obfuscated output broke",
            {"path": path},
        )
    else:
        status = "success"
        ai_hint = f"Protected {stats.get('files_processed', '?')} file(s) into '{output_dir}' " f"with preset '{preset_used}'" + (
            f" — verified (confidence: {confidence}); safe to ship."
            if verify
            else " (verification skipped)."
        ) + (
            f" Keep {mapping_path.name} private; reverse future tracebacks with unmap_stack_trace."
            if save_mapping
            else ""
        )
        next_tool = _next_tool(None, "pipeline complete; obfuscated output is ready to ship")

    payload: Dict[str, Any] = {
        "status": status,
        "verified": verified,
        "confidence": confidence,
        "preset_used": preset_used,
        "input": str(target),
        "output": str(out),
        "obfuscation": {
            "files_processed": stats.get("files_processed"),
            "total_names_obfuscated": stats.get("total_names_obfuscated"),
            "strings_encoded": stats.get("strings_encoded"),
            "level": obf.get("level"),
            "trace_marker_id": obf.get("trace_marker_id"),
        },
        "mapping_path": str(mapping_path) if save_mapping else None,
        "mapping_security_note": (
            "This file de-obfuscates your code — keep it private, never ship it."
            if save_mapping
            else None
        ),
        "risks": {
            "severity_counts": severity,
            "high_severity_findings": high_sev,
            "frameworks_detected": frameworks,
            "files_scanned": report_dict.get("files_scanned", 0),
        },
        "verification": verification,
        "ai_hint": ai_hint,
        "next_tool": next_tool,
        "tier_context": _tier_context(tool_tier="community"),
    }
    if pro_value is not None:
        payload["pro_value"] = pro_value
    return payload


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _error(error_type: str, message: str, ai_hint: str) -> Dict[str, Any]:
    """Build a standard error payload matching the CLI `--json` error shape."""
    return {
        "status": "error",
        "error_type": error_type,
        "message": message,
        "ai_hint": ai_hint,
    }
