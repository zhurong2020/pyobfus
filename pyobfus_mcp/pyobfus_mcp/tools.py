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
  - `pro_value` field on `check_obfuscation_risks` when the scan finds
    likely sensitive string literals (Pro's AES-256 string encryption
    would protect them).
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
("success" | "warnings" | "error") and an `ai_hint` field containing the
single next command or action the calling agent should take.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pyobfus_mcp._security import (
    PathScopeError,
    secure_tool,
    validate_path,
)


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


def _count_sensitive_literals(
    target: Path, *, max_files: int = 200, max_bytes_per_file: int = 200_000
) -> int:
    """Count likely-sensitive string-literal occurrences in `.py` files under target.

    Heuristic-only — false positives expected (e.g. a long random hash literal
    in a test fixture might count). Caps file count and per-file byte read so
    the scan stays bounded on monorepos.
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
        for pat in _SENSITIVE_LITERAL_PATTERNS:
            total += len(pat.findall(text))
    return total


def _pro_value_for_scan(
    sensitive_literal_count: int, high_severity_findings: int
) -> Optional[Dict[str, Any]]:
    """Compute the `pro_value` envelope for a `check_obfuscation_risks` scan.

    Returns `None` when the project doesn't surface a Pro upsell signal
    (no sensitive literals, no high-severity findings). Returns a structured
    recommendation dict otherwise. Strength tiers:

    - Sensitive literals: 1-3 = low / 4-15 = medium / 16+ = high
    - High-severity findings: 1-2 = low / 3-5 = medium / 6+ = high

    The stronger of the two signals wins. We err on the soft-upsell side —
    the field is a hint to the AI, not a license-required gate.
    """
    if sensitive_literal_count == 0 and high_severity_findings == 0:
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
    sev_strength = _strength(high_severity_findings, low=1, mid=6)

    # Pick the stronger signal.
    rank = {"none": 0, "low": 1, "medium": 2, "high": 3}
    overall = lit_strength if rank[lit_strength] >= rank[sev_strength] else sev_strength

    applicable: List[str] = []
    rationale_parts: List[str] = []
    if sensitive_literal_count > 0:
        applicable.append("string_encryption")
        rationale_parts.append(
            f"Found {sensitive_literal_count} likely-sensitive string "
            f"literal occurrence(s) (API keys, tokens, opaque bearer values). "
            f"Pro's AES-256 string encryption would hide these from "
            f"`strings`-style inspection of the obfuscated bytes."
        )
    if high_severity_findings > 0:
        applicable.append("anti_debugging")
        rationale_parts.append(
            f"Scan flagged {high_severity_findings} high-severity finding(s). "
            f"Pro's anti-debugging hooks make static + dynamic reverse "
            f"engineering measurably harder."
        )

    return {
        "applicable_features": applicable,
        "rationale": " ".join(rationale_parts),
        "sensitive_literal_count": sensitive_literal_count,
        "high_severity_findings": high_severity_findings,
        "recommendation_strength": overall,
        **_pro_unlock(),
    }


@secure_tool()
def check_obfuscation_risks(path: str) -> Dict[str, Any]:
    """Scan a Python project for patterns that may break obfuscation.

    Wraps `pyobfus --check`. Returns a structured report with severity
    counts, detected frameworks, a suggested preset, and an `ai_hint`
    telling the calling agent the exact command to run next.

    Args:
        path: Path to a Python file or directory to scan.

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

    report = PreflightChecker().check_path(target)
    payload = report.to_dict()
    payload["status"] = "success" if payload.get("exit_code", 0) == 0 else "warnings"

    # Phase 3: surface Pro funnel signal when the scan finds patterns Pro
    # features (AES-256 string encryption, anti-debugging) would protect.
    sensitive_count = _count_sensitive_literals(target)
    high_sev = int((payload.get("severity_counts") or {}).get("high", 0))
    pro_value = _pro_value_for_scan(sensitive_count, high_sev)
    if pro_value is not None:
        payload["pro_value"] = pro_value
    payload["tier_context"] = _tier_context(tool_tier="community")

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
            sqlalchemy). Default: auto-detected.
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
            "sqlalchemy. Fall back to 'balanced' otherwise."
        ),
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
        reasons.append("No risk patterns or sensitive literals detected — community 'balanced' preset is sufficient.")

    free_action = {
        "command": (
            f"pyobfus {path} -o dist/ --preset "
            f"{report_dict.get('suggested_preset') or 'balanced'} --save-mapping mapping.json"
        ),
        "estimated_protection": "moderate (name mangling + framework-aware excludes)",
    }
    pro_action = {**_pro_unlock(), "estimated_protection": "high (adds AES-256 string encryption + anti-debugging)"}

    payload: Dict[str, Any] = {
        "status": "success",
        "recommended_tier": "pro" if pro_recommended else "community",
        "reasons": reasons,
        "free_tier_capabilities": [
            "AST-based name mangling (classes, functions, locals)",
            "Framework presets (FastAPI, Django, Flask, Pydantic, Click, SQLAlchemy)",
            "JSON CLI for AI agents (--json + ai_hint fields)",
            "Reverse stack-trace mapping (--save-mapping + --unmap)",
        ],
        "pro_tier_capabilities": [
            "AES-256 string encryption",
            "Anti-debugging hooks",
            "Unlimited files and lines of code",
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
            "AES-256 string encryption",
            "Anti-debugging hooks",
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
    }


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
