"""SARIF 2.1.0 projection of a pre-flight ``PreflightReport``.

Turns the findings that ``pyobfus --check`` already computes into a SARIF
2.1.0 document for GitHub Code Scanning and other SARIF consumers, **without**
rescanning source or recomputing severity/category. This is a pure projection
layer: ``preflight.py`` stays the single source of finding facts and exit
semantics.

Privacy is a hard requirement. The projection never emits:

* source snippets or literals (result messages are static, category-level),
* absolute or ``file://`` paths (artifact URIs are input-root-relative POSIX),
* dependency-index credentials, license state, mappings, buyer/device IDs, or
  any generated output.

See ``docs/V0.5.21_RELEASE_PLAN.md`` and ``docs/SARIF_CODE_SCANNING.md`` for the
contract and the CI recipe.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional, Tuple

from pyobfus.core.preflight import (
    CAT_ALL_EXPORT,
    CAT_COMPAT_ADVISORY,
    CAT_DEPENDENCY_ADVISORY,
    CAT_DYNAMIC_ATTR,
    CAT_DYNAMIC_EXEC,
    CAT_DYNAMIC_IMPORT,
    CAT_ENTRY_POINT,
    CAT_FRAMEWORK,
    CAT_INTROSPECTION,
    CAT_MODEL_ARTIFACT_LITERAL,
    CAT_NAME_STRING,
    CAT_UNSAFE_DESERIALIZATION,
    SEVERITY_HIGH,
    SEVERITY_INFO,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    PreflightReport,
    Risk,
)

# The SARIF 2.1.0 schema URI. Matches the vendored test fixture
# (tests/fixtures/sarif-schema-2.1.0.json) so offline schema validation and the
# emitted `$schema` field stay in lock-step.
SARIF_SCHEMA_URI = (
    "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/"
    "Schemata/sarif-schema-2.1.0.json"
)
SARIF_VERSION = "2.1.0"
TOOL_NAME = "pyobfus"
TOOL_INFORMATION_URI = "https://github.com/zhurong2020/pyobfus"
AUTOMATION_ID = "pyobfus/check"

# Rule-id prefix. IDs reuse the stable public category strings rather than
# inventing a second numbering registry.
RULE_ID_PREFIX = "PYOBFUS/"

# Fingerprint scheme version. v1 is stable for an unchanged finding at a stable
# structural location; it is NOT stable across arbitrary source-line moves.
FINGERPRINT_KEY = "pyobfusPreflightV1"

# Severity -> SARIF result level.
_LEVEL_BY_SEVERITY: Dict[str, str] = {
    SEVERITY_HIGH: "error",
    SEVERITY_MEDIUM: "warning",
    SEVERITY_LOW: "note",
    SEVERITY_INFO: "note",
}

# Static, category-level rule metadata. `default_level` is only the rule's
# defaultConfiguration; every result also carries an explicit `level` derived
# from the finding's severity, so this default is a fallback, not the source of
# truth. Descriptions are safe (no source content) and double as the result
# message text.
_CATEGORY_META: Dict[str, Tuple[str, str, str]] = {
    CAT_DYNAMIC_EXEC: (
        "DynamicExec",
        "Dynamic code execution (eval/exec/compile) may reference names that "
        "obfuscation renames.",
        "error",
    ),
    CAT_DYNAMIC_ATTR: (
        "DynamicAttributeAccess",
        "Dynamic attribute access (getattr/setattr/hasattr by name) may target "
        "obfuscated identifiers.",
        "warning",
    ),
    CAT_DYNAMIC_IMPORT: (
        "DynamicImport",
        "Dynamic import (importlib/__import__ by string) may reference module "
        "or member names that obfuscation changes.",
        "warning",
    ),
    CAT_INTROSPECTION: (
        "RuntimeIntrospection",
        "Runtime introspection (globals/locals/vars/__dict__) may depend on " "original names.",
        "warning",
    ),
    CAT_NAME_STRING: (
        "NameStringReference",
        "A string literal appears to reference an identifier that obfuscation " "may rename.",
        "warning",
    ),
    CAT_ALL_EXPORT: (
        "AllExport",
        "An __all__ export list may need to track obfuscated names.",
        "note",
    ),
    CAT_FRAMEWORK: (
        "FrameworkReflection",
        "A framework reflection point may rely on original names; consider a "
        "framework-aware preset.",
        "note",
    ),
    CAT_ENTRY_POINT: (
        "EntryPoint",
        "An entry point may be referenced by name outside the obfuscated code.",
        "note",
    ),
    CAT_UNSAFE_DESERIALIZATION: (
        "UnsafeDeserialization",
        "Unsafe deserialization (pickle/torch.load and similar) was detected.",
        "error",
    ),
    CAT_MODEL_ARTIFACT_LITERAL: (
        "ModelArtifactLiteral",
        "A model/artifact path literal was detected; keep it excluded from " "obfuscation.",
        "note",
    ),
    CAT_COMPAT_ADVISORY: (
        "CompatibilityAdvisory",
        "A delivery-combination compatibility advisory was raised for this " "project.",
        "note",
    ),
    CAT_DEPENDENCY_ADVISORY: (
        "DependencyAdvisory",
        "A declared dependency name did not resolve on public PyPI "
        "(possible hallucinated or typo'd package).",
        "warning",
    ),
}

# Stable rule order for deterministic output.
_RULE_ORDER: List[str] = [
    CAT_DYNAMIC_EXEC,
    CAT_DYNAMIC_ATTR,
    CAT_DYNAMIC_IMPORT,
    CAT_INTROSPECTION,
    CAT_NAME_STRING,
    CAT_ALL_EXPORT,
    CAT_FRAMEWORK,
    CAT_ENTRY_POINT,
    CAT_UNSAFE_DESERIALIZATION,
    CAT_MODEL_ARTIFACT_LITERAL,
    CAT_COMPAT_ADVISORY,
    CAT_DEPENDENCY_ADVISORY,
]


def _rule_id(category: str) -> str:
    return f"{RULE_ID_PREFIX}{category}"


def _level_for(risk: Risk) -> str:
    return _LEVEL_BY_SEVERITY.get(risk.severity, "warning")


def _relative_uri(file_str: str, root_str: str) -> str:
    """Return an input-root-relative POSIX artifact URI, never absolute.

    Falls back to the basename if the finding path is not under the root (or if
    relativisation fails), so an absolute path can never leak into SARIF.
    """
    fp = Path(file_str)
    rp = Path(root_str)

    # A finding attached to the root itself (project-level advisory, or a
    # single-file scan) points at the root's own name.
    if file_str == root_str:
        name = rp.name
        return name if name else "."

    try:
        rel = fp.relative_to(rp)
        rel_posix = PurePosixPath(*rel.parts).as_posix()
        return rel_posix if rel_posix else rp.name or "."
    except ValueError:
        # Not under root (e.g. absolute vs relative mismatch): use basename only.
        return fp.name or "."


def _fingerprint(rule_id: str, uri: str, line: int, column: int) -> str:
    """Deterministic hash of a versioned (rule, safe path, location) tuple."""
    payload = f"v1|{rule_id}|{uri}|{line}|{column}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _region(risk: Risk) -> Optional[Dict[str, int]]:
    """Build a 1-based SARIF region, or None for project-level (line<=0).

    ``Risk.col`` is a 0-based AST ``col_offset``; SARIF columns are 1-based.
    ``Risk.line`` is already 1-based; project-level advisories use line 0 and
    get no region (only an artifact location).
    """
    if risk.line <= 0:
        return None
    region: Dict[str, int] = {"startLine": risk.line}
    if risk.col >= 0:
        region["startColumn"] = risk.col + 1
    return region


def _result_for(risk: Risk, root: str, suppressed: bool) -> Dict[str, Any]:
    rule_id = _rule_id(risk.category)
    uri = _relative_uri(risk.file, root)
    _name, description, _default = _CATEGORY_META.get(
        risk.category, (risk.category, "Pre-flight finding.", "warning")
    )
    region = _region(risk)
    physical_location: Dict[str, Any] = {"artifactLocation": {"uri": uri}}
    if region is not None:
        physical_location["region"] = region

    result: Dict[str, Any] = {
        "ruleId": rule_id,
        "level": _level_for(risk),
        # Static, category-level message: never the per-finding message, which
        # can contain source names/literals.
        "message": {"text": description},
        "locations": [{"physicalLocation": physical_location}],
        "partialFingerprints": {
            FINGERPRINT_KEY: _fingerprint(
                rule_id,
                uri,
                region["startLine"] if region else 0,
                region.get("startColumn", 0) if region else 0,
            )
        },
    }
    if suppressed:
        result["suppressions"] = [
            {
                "kind": "external",
                "justification": "Excluded by the effective pyobfus configuration.",
            }
        ]
        result["properties"] = {"pyobfus.excluded": True}
    return result


def _rules() -> List[Dict[str, Any]]:
    rules: List[Dict[str, Any]] = []
    for category in _RULE_ORDER:
        name, description, default_level = _CATEGORY_META[category]
        rules.append(
            {
                "id": _rule_id(category),
                "name": name,
                "shortDescription": {"text": description},
                "defaultConfiguration": {"level": default_level},
                "properties": {"category": category},
            }
        )
    return rules


def _invocation(report: PreflightReport) -> Dict[str, Any]:
    """Invocation metadata. Parse failures become tool-execution notifications
    with a safe relative path and a generic message — never the raw exception
    text (which can contain source) or an absolute path."""
    exit_code = report.exit_code()
    notifications: List[Dict[str, Any]] = []
    for entry in report.parse_errors:
        # Stored as "{file_path}: {exception}". Split on the first ": " (a
        # colon-space never occurs inside a filesystem path, including
        # Windows "C:\\..."), take the path half only, and relativise it.
        path_part = entry.split(": ", 1)[0]
        uri = _relative_uri(path_part, report.root)
        notifications.append(
            {
                "level": "error",
                "message": {"text": "A source file could not be parsed and was skipped."},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": uri}}}],
            }
        )

    invocation: Dict[str, Any] = {
        "executionSuccessful": exit_code != 2,
        "exitCode": exit_code,
    }
    if notifications:
        invocation["toolExecutionNotifications"] = notifications
    return invocation


def build_sarif(report: PreflightReport, tool_version: str) -> Dict[str, Any]:
    """Project a completed ``PreflightReport`` into a SARIF 2.1.0 document.

    Pure function: no filesystem or network access, no rescanning. ``report``
    is the authority for findings, severity and exit code.
    """
    results: List[Dict[str, Any]] = [
        _result_for(risk, report.root, suppressed=False) for risk in report.risks
    ]
    # Config-excluded findings are included as suppressed results so reviewers
    # can see them without them affecting the scan exit code.
    results.extend(
        _result_for(risk, report.root, suppressed=True) for risk in report.excluded_risks
    )

    run: Dict[str, Any] = {
        "tool": {
            "driver": {
                "name": TOOL_NAME,
                "informationUri": TOOL_INFORMATION_URI,
                "version": tool_version,
                "semanticVersion": tool_version,
                "rules": _rules(),
            }
        },
        "automationDetails": {"id": AUTOMATION_ID},
        "columnKind": "unicodeCodePoints",
        "invocations": [_invocation(report)],
        "results": results,
    }

    return {
        "$schema": SARIF_SCHEMA_URI,
        "version": SARIF_VERSION,
        "runs": [run],
    }


def write_sarif(report: PreflightReport, path: Path, tool_version: str) -> None:
    """Atomically write the SARIF projection of ``report`` to ``path``.

    Writes to a temporary file in the same directory and ``os.replace`` it into
    place, so a CI job never uploads a partially written result.
    """
    import json

    document = build_sarif(report, tool_version)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(document, f, indent=2, ensure_ascii=False)
            f.write("\n")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
