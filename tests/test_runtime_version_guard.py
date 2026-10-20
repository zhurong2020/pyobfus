"""Classifier updates must not waive runtime code or dependency changes."""

import subprocess
from pathlib import Path

import pytest

from scripts import check_runtime_version as guard


@pytest.mark.parametrize(
    "classifiers, dependency, code, expected",
    [
        (True, False, False, 0),
        (False, True, False, 1),
        (True, True, False, 1),
        (True, False, True, 1),
    ],
)
def test_runtime_release_boundary(tmp_path, monkeypatch, classifiers, dependency, code, expected):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    package = tmp_path / "pyobfus_runtime"
    (package / "pyobfus_runtime").mkdir(parents=True)
    module = package / "pyobfus_runtime" / "__init__.py"
    module.write_text("value = 1\n", encoding="utf-8")
    metadata = package / "pyproject.toml"
    initial = (
        '[project]\nname = "pyobfus-runtime"\nversion = "0.1.1"\n'
        'dependencies = ["cryptography>=42.0"]\n'
        'classifiers = ["Programming Language :: Python :: 3.14"]\n'
    )
    metadata.write_text(initial, encoding="utf-8")
    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "base")
    git("tag", "runtime-v0.1.1")
    updated = initial
    if classifiers:
        updated = updated.replace('3.14"', '3.14", "Programming Language :: Python :: 3.15"')
    if dependency:
        updated = updated.replace("cryptography>=42.0", "cryptography>=50.0")
    if code:
        module.write_text("value = 2\n", encoding="utf-8")
    metadata.write_text(updated, encoding="utf-8")
    monkeypatch.setattr(guard, "REPO_ROOT", Path(tmp_path))
    assert guard.main() == expected
