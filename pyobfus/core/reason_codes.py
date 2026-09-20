"""Stable, versioned reason codes for pyobfus's structured JSON surfaces.

Every "why" that ``--dry-run --json`` (the plan) and ``--build-report`` report
about a build decision uses a code from this single catalog, so consumers
(the VS Code extension, CI, MCP, auditors) can branch on a stable token instead
of parsing English prose whose wording may change between releases.

Three domains are covered:

- ``selected.*`` / ``excluded.*`` — why a file was or was not obfuscated.
- ``disabled.*`` — why a requested transform / mechanism will not run.
- ``preserved.*`` — why a symbol was kept (not renamed). **Reserved
  vocabulary: defined and documented here, but not yet emitted** on any JSON
  surface. Emitting per-symbol preserve reasons needs the analyzer to record a
  reason as it prunes each name (it currently drops preserved categories at
  collection time, so they cannot be reconstructed after the fact). Kept in the
  catalog so consumers can rely on the codes once emission lands.

Contract: consumers must ignore unknown codes. Adding a code is a minor,
backward-compatible change; removing or repurposing one requires bumping
``REASON_CODES_VERSION``.
"""

from __future__ import annotations

from typing import Dict

REASON_CODES_VERSION = 1

# --- file selection -------------------------------------------------------
SELECTED_INCLUDED = "selected.included"
EXCLUDED_PATTERN = "excluded.pattern"

# --- disabled transforms / mechanisms -------------------------------------
DISABLED_CROSS_FILE_MODE = "disabled.cross_file_mode"
DISABLED_REQUIRES_PRO = "disabled.requires_pro"
DISABLED_NOT_SELECTED = "disabled.not_selected"

# --- preserved symbols (RESERVED: defined, not yet emitted; see module docstring) ---
PRESERVED_DUNDER = "preserved.dunder"
PRESERVED_IMPORTED = "preserved.imported"
PRESERVED_CONFIG_EXCLUDE = "preserved.config_exclude"
PRESERVED_PUBLIC_API = "preserved.public_api"
PRESERVED_OTHER = "preserved.other"

_DESCRIPTIONS: Dict[str, str] = {
    SELECTED_INCLUDED: "File selected for obfuscation.",
    EXCLUDED_PATTERN: "File skipped because it matched a configured exclude pattern.",
    DISABLED_CROSS_FILE_MODE: (
        "Mechanism operates on generated source and is not applied in cross-file "
        "directory mode (use --no-cross-file or a single file)."
    ),
    DISABLED_REQUIRES_PRO: "Transform is a Pro feature and the effective level is community.",
    DISABLED_NOT_SELECTED: "Transform is not enabled in the effective configuration.",
    PRESERVED_DUNDER: "Symbol is a dunder (e.g. __init__) and is never renamed.",
    PRESERVED_IMPORTED: "Symbol is bound by an import; renaming it would break the import.",
    PRESERVED_CONFIG_EXCLUDE: "Symbol is listed in the configuration's exclude_names.",
    PRESERVED_PUBLIC_API: "Symbol was auto-detected as part of the public API.",
    PRESERVED_OTHER: "Symbol is preserved for another reason (e.g. global scope).",
}

ALL_REASON_CODES = frozenset(_DESCRIPTIONS)


def describe(code: str) -> str:
    """Return the human-readable description for a reason code, or a fallback."""
    return _DESCRIPTIONS.get(code, "Unknown reason code.")


def is_known(code: str) -> bool:
    """True if ``code`` is a defined reason code in this catalog version."""
    return code in _DESCRIPTIONS


def catalog() -> Dict[str, str]:
    """Return a copy of the full {code: description} catalog (for docs/consumers)."""
    return dict(_DESCRIPTIONS)


__all__ = [
    "REASON_CODES_VERSION",
    "SELECTED_INCLUDED",
    "EXCLUDED_PATTERN",
    "DISABLED_CROSS_FILE_MODE",
    "DISABLED_REQUIRES_PRO",
    "DISABLED_NOT_SELECTED",
    "PRESERVED_DUNDER",
    "PRESERVED_IMPORTED",
    "PRESERVED_CONFIG_EXCLUDE",
    "PRESERVED_PUBLIC_API",
    "PRESERVED_OTHER",
    "ALL_REASON_CODES",
    "describe",
    "is_known",
    "catalog",
]
