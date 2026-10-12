#!/usr/bin/env python3
"""Fail when pyobfus_runtime changed but its version did not.

``pyobfus-runtime`` is released from tags named ``runtime-v<version>``. If the
package source differs from the tag of the version declared in
``pyobfus_runtime/pyproject.toml``, the published wheel of that version is not
the code the builder is tested against (2026-10-12: Core 0.5.30 emitted
runtime calls that the published 0.1.0 lacked). Bump the runtime version when
this fails. A version with no tag yet is an unreleased bump and passes.

Needs the release tags locally (CI checks out with ``fetch-depth: 0``).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = "pyobfus_runtime"
# Files whose content is what users install; tests and docs may change freely.
WATCHED = (f"{RUNTIME_DIR}/pyobfus_runtime", f"{RUNTIME_DIR}/pyproject.toml")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    )


def declared_version() -> str:
    text = (REPO_ROOT / RUNTIME_DIR / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not match:
        raise SystemExit(f"{RUNTIME_DIR}/pyproject.toml has no version line")
    return match.group(1)


def main() -> int:
    version = declared_version()
    tag = f"runtime-v{version}"
    if _git("rev-parse", "--verify", "--quiet", f"refs/tags/{tag}").returncode != 0:
        if not _git("tag", "--list", "runtime-v*").stdout.strip():
            print("check_runtime_version: no runtime-v* tags available; fetch tags first.")
            return 2
        print(f"check_runtime_version: {tag} not tagged yet (unreleased version); OK.")
        return 0
    diff = _git("diff", "--name-only", tag, "--", *WATCHED)
    if diff.returncode != 0:
        print(diff.stderr.strip())
        return 2
    changed = [line for line in diff.stdout.splitlines() if line.strip()]
    if changed:
        print(
            f"check_runtime_version: {RUNTIME_DIR} differs from {tag} but still "
            f"declares version {version}. Bump the version in "
            f"{RUNTIME_DIR}/pyproject.toml (and the builder floor if generated "
            "code needs the change). Changed:"
        )
        for name in changed:
            print(f"  {name}")
        return 1
    print(f"check_runtime_version: {RUNTIME_DIR} matches {tag}; OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
