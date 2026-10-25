#!/usr/bin/env python3
"""Build a private MCP compatibility candidate without changing shipped metadata.

Only the SDK upper bound changes in the copied package. This is test input,
not a release artifact; never publish it. The destination must be a new path.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    destination = arguments.destination.resolve()
    if destination.exists():
        parser.error("Candidate destination must not exist")
    source = Path(__file__).resolve().parents[1] / "pyobfus_mcp"
    shutil.copytree(
        source,
        destination / "source",
        ignore=shutil.ignore_patterns(
            "__pycache__", "*.egg-info", "build", "dist", ".pytest_cache"
        ),
    )
    project = destination / "source" / "pyproject.toml"
    metadata = project.read_text(encoding="utf-8")
    old, candidate = "mcp>=1.27.0,<2.0.0", "mcp>=1.27.0,<3.0.0"
    if metadata.count(old) != 1:
        raise ValueError("Production SDK bound changed; review this candidate builder")
    project.write_text(metadata.replace(old, candidate), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--outdir",
            str(destination / "dist"),
            str(destination / "source"),
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
