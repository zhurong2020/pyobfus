#!/usr/bin/env python3
"""
Report every CHANGELOG.md in the repo (root `pyobfus`, `pyobfus_mcp/`,
`vscode-extension/` -- three independently versioned/released packages
sharing one repo) that has non-empty content sitting under `## [Unreleased]`.

Exists because "content already committed but never cut into a version"
silently accumulates across sibling packages with their own release cadence:
a docs-only entry can sit in `pyobfus_mcp/CHANGELOG.md` for a week because
attention was on the main `pyobfus` package's release, and nothing surfaces
that gap again until someone happens to open that file. The `[Unreleased]`
section is already the source of truth for "what's pending" per Keep a
Changelog convention -- this script just makes it impossible to forget to
look, instead of relying on a hand-written to-do note (which goes stale in
exactly the same way the content it's tracking does).

Not wired into CI: a non-empty [Unreleased] section is the *normal* resting
state between releases, not a failure. Run this by hand as a pre-release
checklist step (see docs/internal/PYPI_RELEASE_GUIDE.md) -- either right
before you cut any one package's release (to decide whether to bundle a
sibling's pending content into the same session) or periodically as part of
a channel/health recheck.

Usage:
    python scripts/check_unreleased_changelogs.py            # human-readable report
    python scripts/check_unreleased_changelogs.py --check    # exit 1 if any found
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Known package CHANGELOGs, in release-checklist order. Add a new entry here
# when a new independently-versioned package/sub-package is added to the repo.
CHANGELOG_PATHS = [
    REPO_ROOT / "CHANGELOG.md",
    REPO_ROOT / "pyobfus_mcp" / "CHANGELOG.md",
    REPO_ROOT / "vscode-extension" / "CHANGELOG.md",
]

UNRELEASED_RE = re.compile(r"^## \[Unreleased\]\s*$", re.MULTILINE)
NEXT_HEADER_RE = re.compile(r"^## \[", re.MULTILINE)


def unreleased_content(text: str) -> str:
    """Return the raw text between '## [Unreleased]' and the next '## [' header."""
    m = UNRELEASED_RE.search(text)
    if not m:
        return ""
    rest = text[m.end():]
    next_m = NEXT_HEADER_RE.search(rest)
    section = rest[: next_m.start()] if next_m else rest
    return section.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if any CHANGELOG has non-empty [Unreleased] content",
    )
    args = parser.parse_args()

    pending: list[tuple[Path, str]] = []
    for path in CHANGELOG_PATHS:
        if not path.exists():
            print(f"[skip] {path.relative_to(REPO_ROOT)} not found", file=sys.stderr)
            continue
        content = unreleased_content(path.read_text(encoding="utf-8"))
        if content:
            pending.append((path, content))

    if not pending:
        print("No pending [Unreleased] content in any tracked CHANGELOG.md. Clean.")
        return 0

    print(f"{len(pending)} of {len(CHANGELOG_PATHS)} CHANGELOGs have pending [Unreleased] content:\n")
    for path, content in pending:
        rel = path.relative_to(REPO_ROOT)
        line_count = len(content.splitlines())
        print(f"### {rel} ({line_count} lines)")
        preview = "\n".join(content.splitlines()[:6])
        print(preview)
        if line_count > 6:
            print("  ...")
        print()

    if args.check:
        print("--check: pending content found, exiting 1.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
