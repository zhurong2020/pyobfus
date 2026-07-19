"""End-to-end tests driving the installed `pyobfus` CLI as a subprocess.

These exercise the real entry point rather than importing the package, so they
catch packaging/console-script breakage that the unit suite cannot see. They
were previously a handful of inline `run:` steps in `.github/workflows/ci.yml`;
`AGENTS.md` documents `pytest integration_tests/` as a test root, so they live
here as collectible tests.

Each test obfuscates into a tmp_path and then *executes* the output, because
"obfuscation succeeded" is not the property that matters — "the obfuscated code
still runs and still produces the same answer" is.
"""

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Invoke the CLI through the current interpreter's -m entry point."""
    return subprocess.run(
        [sys.executable, "-m", "pyobfus", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def run_script(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(path)],
        capture_output=True,
        text=True,
        cwd=path.parent,
    )


class TestCliAvailability:
    def test_version_flag(self):
        result = run_cli("--version")
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip()

    def test_help_flag(self):
        result = run_cli("--help")
        assert result.returncode == 0, result.stderr


class TestSingleFileObfuscation:
    def test_obfuscated_output_still_executes(self, tmp_path):
        source = EXAMPLES / "simple.py"
        if not source.exists():
            pytest.skip("examples/simple.py not present")

        baseline = run_script(source)
        output = tmp_path / "obfuscated.py"

        result = run_cli(str(source), "-o", str(output))
        assert result.returncode == 0, result.stderr
        assert output.exists()

        obfuscated = run_script(output)
        assert obfuscated.returncode == 0, obfuscated.stderr
        assert obfuscated.stdout == baseline.stdout

    def test_output_differs_from_source(self, tmp_path):
        source = EXAMPLES / "simple.py"
        if not source.exists():
            pytest.skip("examples/simple.py not present")

        output = tmp_path / "obfuscated.py"
        assert run_cli(str(source), "-o", str(output)).returncode == 0
        assert output.read_text() != source.read_text()

    def test_output_byte_compiles(self, tmp_path):
        source = EXAMPLES / "simple.py"
        if not source.exists():
            pytest.skip("examples/simple.py not present")

        output = tmp_path / "obfuscated.py"
        assert run_cli(str(source), "-o", str(output)).returncode == 0

        compiled = subprocess.run(
            [sys.executable, "-m", "py_compile", str(output)],
            capture_output=True,
            text=True,
        )
        assert compiled.returncode == 0, compiled.stderr


class TestDirectoryObfuscation:
    def test_multifile_with_config(self, tmp_path):
        source_dir = EXAMPLES / "multifile"
        config = source_dir / "pyobfus.yaml"
        if not config.exists():
            pytest.skip("examples/multifile not present")

        output_dir = tmp_path / "out"
        result = run_cli(
            str(source_dir), "-o", str(output_dir), "--config", str(config), "-v"
        )
        assert result.returncode == 0, result.stderr
        assert list(output_dir.rglob("*.py")), "no Python files were emitted"


class TestErrorHandling:
    def test_missing_input_fails_cleanly(self, tmp_path):
        result = run_cli(str(tmp_path / "does_not_exist.py"), "-o", str(tmp_path / "o.py"))
        assert result.returncode != 0
        assert not (tmp_path / "o.py").exists()
