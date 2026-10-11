"""Execute directory builds after applying the compatibility suggestions."""

import enum
import json
import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("case", ["module-from", "module-exclude", "global-enum"])
def test_suggested_workaround(tmp_path, case):
    if case == "global-enum" and not hasattr(enum, "global_enum"):
        pytest.skip("enum.global_enum is unavailable on this interpreter")
    source = tmp_path / "src"
    (source / "pkg").mkdir(parents=True)
    (source / "pkg/__init__.py").write_text("", encoding="utf-8")
    config = tmp_path / "config.yaml"
    if case == "global-enum":
        core = "import enum\n@enum.global_enum\nclass Color(enum.Enum):\n    RED = 7\n__all__ = ['Color', 'RED']\nprint(RED)\n"
        entry = "from pkg.core import RED\nprint(RED)\n"
        config.write_text("obfuscation:\n  exclude_names: [RED]\n", encoding="utf-8")
    else:
        core = "LIMIT = 7\n"
        entry = "from pkg import core\nprint(core.LIMIT)\n"
        config.write_text("obfuscation:\n  exclude_names: [LIMIT]\n", encoding="utf-8")
    (source / "pkg/core.py").write_text(core, encoding="utf-8")
    (source / "entry.py").write_text(entry, encoding="utf-8")
    env = dict(os.environ, HOME=str(tmp_path / "home"), USERPROFILE=str(tmp_path / "home"))

    def run(*args):
        return subprocess.run(
            [sys.executable, *map(str, args)], env=env, capture_output=True, text=True, timeout=60
        )

    baseline = run(source / "entry.py")
    assert baseline.returncode == 0, baseline.stderr
    checked = run("-m", "pyobfus", source, "--check", "--json", "--no-config", "--offline")
    assert checked.returncode == 0, checked.stderr
    findings = [
        r for r in json.loads(checked.stdout)["risks"] if r["category"] == "compatibility_advisory"
    ]
    assert len(findings) == 1
    assert "exclude_names" in findings[0]["suggestion"]
    flags = ["--config", config]
    if case == "module-from":
        assert "from pkg.core import LIMIT" in findings[0]["suggestion"]
        (source / "entry.py").write_text(
            "from pkg.core import LIMIT\nprint(LIMIT)\n", encoding="utf-8"
        )
        flags = ["--no-config"]
    output = tmp_path / "out"
    built = run("-m", "pyobfus", source, "-o", output, *flags)
    assert built.returncode == 0, built.stdout + built.stderr
    product = run(output / "entry.py")
    assert product.returncode == 0, product.stderr
    assert product.stdout == baseline.stdout
