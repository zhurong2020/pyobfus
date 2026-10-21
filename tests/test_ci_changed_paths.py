"""The CI allowlist must fail open for unknown or executable paths."""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci_changed_paths import code_changed


@pytest.mark.parametrize("path", ["docs/TODO.md", "docs/guide/usage.md"])
def test_docs_only(path):
    assert not code_changed([path])


@pytest.mark.parametrize(
    "path",
    [
        "README.md",
        "llms.txt",
        "AGENTS.md",
        "CITATION.cff",
        "server.json",
        "skills/review/SKILL.md",
        "templates/example.md",
        "docs/llms.txt",
        "docs/.well-known/ai-catalog.json",
        "docs/.well-known/readme.md",
        "docs/example.py",
        "docs/assets/image.png",
        "docs/requirements.txt",
        ".github/workflows/ci.yml",
        "scripts/guide.md",
        "pyproject.toml",
        "unknown",
        "docs/../README.md",
        "docs\\guide.md",
    ],
)
def test_code_or_unknown(path):
    assert code_changed(["docs/TODO.md", path])


def test_empty_diff():
    assert not code_changed([])


def test_cli_handles_nul_separated_paths():
    script = Path(__file__).resolve().parents[1] / "scripts" / "ci_changed_paths.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        input=b"docs/a b.md\0docs/new\nline.md\0",
        capture_output=True,
        check=True,
    )
    assert result.stdout == b"code=false\n"
