"""
Pure-Python tool implementations for the pyobfus MCP server.

These functions are deliberately MCP-SDK-agnostic: they accept primitive
types, return dicts, and are independently testable without installing
the `mcp` package. `server.py` wraps them as MCP tools; external callers
(tests, CI, custom agent frameworks) can call them directly.

All return dicts follow a stable shape with a `status` field
("success" | "error") and an `ai_hint` field containing the single next
command or action the calling agent should take.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional


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

    target = Path(path)
    if not target.exists():
        return _error(
            "PathNotFound",
            f"Path does not exist: {path}",
            f"Double-check the path and try again.",
        )

    report = PreflightChecker().check_path(target)
    payload = report.to_dict()
    payload["status"] = "success" if payload.get("exit_code", 0) == 0 else "warnings"
    return payload


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

    target = Path(path)
    if not target.exists():
        return _error(
            "PathNotFound",
            f"Path does not exist: {path}",
            "Pass a valid project directory.",
        )

    result = build_init_result(target, preset_override=preset_override)

    if write:
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


def unmap_stack_trace(trace: str, mapping_path: str) -> Dict[str, Any]:
    """Reverse obfuscated identifiers in a stack trace using a mapping.json.

    Wraps `pyobfus --unmap`. Accepts the trace as a literal string (most
    useful for agent workflows where the trace is already in the chat
    buffer); for large logs, callers can pre-read the file and pass
    its contents.

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

    mp = Path(mapping_path)
    if not mp.exists():
        return _error(
            "MappingNotFound",
            f"Mapping file not found: {mapping_path}",
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

    return {
        "status": "success",
        "preset": name.lower(),
        "level": cfg.level,
        "exclude_names_count": len(cfg.exclude_names),
        "exclude_patterns": list(cfg.exclude_patterns),
        "preserve_param_names": cfg.preserve_param_names,
        "remove_docstrings": cfg.remove_docstrings,
        "string_encoding": cfg.string_encoding,
        "ai_hint": (
            f"Apply with: pyobfus src/ -o dist/ --preset {name.lower()}"
            if cfg.level == "community"
            else f"'{name}' is a Pro preset. Start a free trial: pyobfus-trial start"
        ),
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
