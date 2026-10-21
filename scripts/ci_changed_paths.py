"""Conservatively classify NUL-separated git paths for the CI heavy-job gate."""

import sys
from pathlib import PurePosixPath
from typing import Iterable

# Read-path audit (2026-10-21): rg over tests/, integration_tests/,
# pyobfus_mcp/tests/, pyobfus_runtime/tests/, benchmarks/, scripts/ and all
# four packages for read_text/read_bytes/open/Path and named repo assets.
# scripts/check.sh reads docs/llms.txt and docs/.well-known/ai-catalog.json;
# check_readme_links.py reads README.md and resolves linked repository paths;
# MCP metadata tests read server.json. Keep these, AGENTS.md, CITATION.cff,
# llms.txt, skills/, templates/, assets and every unknown path as code.
# Allowlist: only non-hidden docs/**/*.md prose (including docs/*.md).
# All .py, scripts/**, .github/** and pyproject.toml paths stay code.
# Full grep evidence: maintainer's gitignored ci-speed-evidence/path-read-audit.txt.


def docs_only(path: str) -> bool:
    parts = PurePosixPath(path).parts
    return (
        len(parts) >= 2
        and parts[0] == "docs"
        and all(not part.startswith(".") and part != ".." for part in parts)
        and path.endswith(".md")
        and "\\" not in path
    )


def code_changed(paths: Iterable[str]) -> bool:
    return any(not docs_only(path) for path in paths)


def main() -> None:
    paths = sys.stdin.buffer.read().decode("utf-8", errors="surrogateescape").split("\0")
    # git terminates every path with NUL. Empty input means no changed files.
    if paths[-1] == "":
        paths.pop()
    print("code=" + str(code_changed(paths)).lower())


if __name__ == "__main__":
    main()
