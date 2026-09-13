#!/usr/bin/env python3
"""Fail if README.md carries a link that will 404 on PyPI.

README.md is the package's long_description. PyPI renders it at
`https://pypi.org/project/pyobfus/`, and resolves every relative link against
*that* URL rather than against the repository. So `](pyobfus_mcp/)` renders on
GitHub as the source directory and on PyPI as
`https://pypi.org/project/pyobfus/pyobfus_mcp/`, which does not exist.

Forty-six such links shipped before anyone noticed, because the GitHub view of
the same file is flawless and that is the view maintainers look at. This check
exists so the next one fails here instead of on the package page.

Relative links are also verified to exist on disk, which catches a rename that
silently points the README at nothing.

    python scripts/check_readme_links.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
REPO_PREFIX = "https://github.com/zhurong2020/pyobfus/"

RELATIVE = re.compile(r"\]\((?!https?://|#|mailto:)([^)\s]+)\)")
ABSOLUTE_REPO = re.compile(r"\]\(" + re.escape(REPO_PREFIX) + r"(blob|tree)/main/([^)#\s]+)")


def main() -> int:
    text = README.read_text(encoding="utf-8")
    problems: list[str] = []

    for match in RELATIVE.finditer(text):
        target = match.group(1)
        problems.append(
            f"relative link {target!r} resolves to "
            f"https://pypi.org/project/pyobfus/{target} on PyPI; "
            f"use {REPO_PREFIX}blob/main/{target} instead"
        )

    # An absolute repository link is only useful if it still points at something.
    for match in ABSOLUTE_REPO.finditer(text):
        path = (ROOT / match.group(2)).resolve()
        if not path.exists():
            problems.append(f"link points at {match.group(2)!r}, which no longer exists")

    if problems:
        print(f"{README.name}: {len(problems)} problem(s)")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"{README.name}: no relative links, every repository link resolves")
    return 0


if __name__ == "__main__":
    sys.exit(main())
