"""The CI allowlist must fail open for unknown or executable paths."""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.ci_changed_paths import code_changed, test_matrix as build_matrix


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


@pytest.mark.parametrize("event", ["push", "pull_request", "schedule", "workflow_dispatch"])
def test_matrix_versions(event):
    cells = build_matrix(event)["include"]
    assert len(cells) == (21 if event in ("schedule", "workflow_dispatch") else 13)
    assert len({(cell["os"], cell["python-version"]) for cell in cells}) == len(cells)
    for os_name in ("ubuntu-latest", "windows-latest", "macos-latest"):
        versions = {cell["python-version"] for cell in cells if cell["os"] == os_name}
        expected = {"3.9", "3.10", "3.11", "3.12", "3.13", "3.14", "3.15"}
        if event not in ("schedule", "workflow_dispatch") and os_name != "ubuntu-latest":
            expected = {"3.9", "3.14", "3.15"}
        assert versions == expected
