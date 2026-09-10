"""Build marker emitted at the top of generated output.

A *build marker* is a short comment block identifying a file as pyobfus
output. It is transparent attribution and generated-file identification --
never a license check, an authenticity proof, or an anti-piracy measure.
Anyone holding the output can delete it, and that is fine by design.

Three marker layers exist in this project and must not be conflated:

===================  ==========  ==========================================
Layer                Edition     Purpose
===================  ==========  ==========================================
Build marker         Core/free   Attribution + "this file is generated"
Trace marker         Core        How to reverse a traceback via a mapping
Forensic watermark   Pro         Buyer-specific leak evidence
===================  ==========  ==========================================

This module owns the first, and owns the prologue-safe insertion helper
that the trace marker (``pyobfus.cli``) shares, so both agree on where a
shebang and a PEP 263 encoding cookie must stay.

The marker carries no absolute path, buyer id, license key, device id,
mapping digest, source hash or other identifier -- see
``docs/COMMUNITY_BUILD_MARKER_DESIGN.md``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from pyobfus.constants import BUILD_MARKER_FORMAT, BUILD_MARKER_PREFIX, GITHUB_REPO

# Valid values for the ``community_marker`` config key.
MARKER_MODES = ("auto", "on", "off")

# PEP 263 encoding cookie -- must stay within a file's first two lines, so a
# marker is inserted *after* it (and after any shebang) rather than above,
# which would silently disable the declared source encoding.
_CODING_COOKIE_RE = re.compile(r"coding[:=]\s*([-\w.]+)")

# How far into a file to look when checking whether a marker is already
# present. Generous enough to sit below a shebang, an encoding cookie and
# another marker block, small enough to stay O(1) on large files.
_MARKER_SCAN_WINDOW = 512


def insert_after_prologue(text: str, block: str) -> str:
    """Prepend ``block``, keeping a shebang first and an encoding cookie
    within the first two lines."""
    lines = text.splitlines(keepends=True)
    idx = 0
    if idx < len(lines) and lines[idx].startswith("#!"):
        idx += 1
    if idx < len(lines) and idx < 2 and _CODING_COOKIE_RE.search(lines[idx]):
        idx += 1
    return "".join(lines[:idx]) + block + "".join(lines[idx:])


def safe_source_label(source: Path, root: Optional[Path]) -> Optional[str]:
    """Return a project-relative POSIX label for ``source``, or its basename.

    Never returns an absolute path: an absolute build path leaks the
    maintainer's directory layout (and often a username) into every shipped
    file. When ``source`` is not under ``root`` -- a sibling directory, a
    different drive, a symlink pointing outside -- the basename is used, and
    when even that is unavailable the field is omitted.

    ``root`` is the base directory to make ``source`` relative to. Passing the
    input *file* of a single-file build works too: an existing file resolves to
    its parent. A path that does not exist is taken at face value as a
    directory, so callers are not forced to create it first.
    """
    try:
        name = source.name
    except (AttributeError, TypeError):
        return None
    if not name:
        return None
    if root is None:
        return name
    try:
        base = root.parent if root.is_file() else root
        return source.resolve().relative_to(base.resolve()).as_posix()
    except (ValueError, OSError):
        return name


def marker_enabled(mode: Optional[str]) -> bool:
    """Resolve a ``community_marker`` mode to an emit/skip decision.

    ``auto`` (the default) emits, matching what the design calls the
    transparent free-tier promise. ``off`` is for environments that forbid
    generated banners. An unrecognized value is treated as ``auto`` rather
    than raising: a cosmetic comment must never fail a build.
    """
    if mode is None:
        return True
    return str(mode).strip().lower() != "off"


def build_marker_block(
    *,
    tool_version: str,
    edition: str,
    source_label: Optional[str] = None,
) -> str:
    """Build the marker comment block (trailing newline included).

    Deterministic for identical tool version, edition and relative source, so
    two builds of the same input produce byte-identical markers.
    """
    lines: List[str] = [
        f"{BUILD_MARKER_PREFIX} format={BUILD_MARKER_FORMAT} edition={edition}",
        f"# Tool: pyobfus {tool_version} - {GITHUB_REPO}",
    ]
    if source_label:
        lines.append(f"# Source: {source_label}")
    lines.append("# DO NOT EDIT - generated output")
    return "\n".join(lines) + "\n"


def has_marker(text: str) -> bool:
    """True if ``text`` already carries a build marker near the top."""
    return BUILD_MARKER_PREFIX in text[:_MARKER_SCAN_WINDOW]


def apply_marker(
    text: str,
    *,
    tool_version: str,
    edition: str,
    source_label: Optional[str] = None,
) -> str:
    """Stamp ``text`` with a build marker. Idempotent."""
    if has_marker(text):
        return text
    block = build_marker_block(
        tool_version=tool_version,
        edition=edition,
        source_label=source_label,
    )
    return insert_after_prologue(text, block)


def marker_state(*, mode: Optional[str], edition: str, emitted: bool) -> dict:
    """Additive record of marker state for the dry-run plan and manifest.

    Reports build provenance only. It must never be read as proof that an
    artifact is authentic -- sign or attest the artifact for that.
    """
    normalized = (mode or "auto").strip().lower()
    if normalized not in MARKER_MODES:
        normalized = "auto"
    return {
        "format": BUILD_MARKER_FORMAT,
        "edition": edition,
        "mode": normalized,
        "emitted": emitted,
    }
