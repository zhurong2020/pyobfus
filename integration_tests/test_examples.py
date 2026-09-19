"""First-batch example execution, end to end.

`docs/SUPPORT_MATRIX.md` used to say no example was executed by CI at all.
The `integration` job now runs the cheap, stdlib-only examples for real on
Ubuntu and Windows: obfuscate, *execute* the generated output, and assert the
behavior the example exists to demonstrate — not just exit codes.

Covered here (first batch — `pyinstaller/` and `compiled_packaging/` need
external toolchains and stay advisory-only):

- `string_encoding.py` — output must match the original run's stdout exactly.
- `keyword_arguments.py` — same, obfuscated with `--preserve-param-names`.
- `ai_debugging/` — obfuscated build crashes with mangled names; `--unmap`
  restores the originals from the saved mapping.
- `import_hook/` — the stdlib loader loads the obfuscated module, and the
  original identifiers never reach the loaded source.

`examples/simple.py` and `examples/multifile/` are executed by
`test_cli_end_to_end.py` in this same pytest root.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "examples"

UTF8_ENV = {**os.environ, "PYTHONUTF8": "1"}


def run_cli(*args: str) -> subprocess.CompletedProcess:
    """Invoke the CLI through the current interpreter's -m entry point."""
    return subprocess.run(
        [sys.executable, "-m", "pyobfus", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env=UTF8_ENV,
    )


def run_script(path: Path, cwd: Path = None) -> subprocess.CompletedProcess:
    """Run a Python script with UTF-8 stdio so Unicode output survives Windows."""
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(cwd) if cwd else None,
        env=UTF8_ENV,
    )


class TestStringEncodingExample:
    def test_obfuscated_output_matches_original(self, tmp_path):
        source = EXAMPLES / "string_encoding.py"
        if not source.exists():
            pytest.skip("examples/string_encoding.py not present")

        baseline = run_script(source)
        assert baseline.returncode == 0, baseline.stderr

        output = tmp_path / "obfuscated.py"
        result = run_cli(str(source), "-o", str(output))
        assert result.returncode == 0, result.stderr

        obfuscated = run_script(output)
        assert obfuscated.returncode == 0, obfuscated.stderr
        assert obfuscated.stdout == baseline.stdout


class TestKeywordArgumentsExample:
    def test_preserved_param_names_keep_output_identical(self, tmp_path):
        source = EXAMPLES / "keyword_arguments.py"
        if not source.exists():
            pytest.skip("examples/keyword_arguments.py not present")

        baseline = run_script(source)
        assert baseline.returncode == 0, baseline.stderr

        output = tmp_path / "obfuscated.py"
        result = run_cli(str(source), "-o", str(output), "--preserve-param-names")
        assert result.returncode == 0, result.stderr

        obfuscated = run_script(output)
        assert obfuscated.returncode == 0, obfuscated.stderr
        assert obfuscated.stdout == baseline.stdout


class TestAiDebuggingExample:
    """Obfuscated crash -> `--unmap` restores the original names."""

    def test_unmap_recovers_original_identifiers(self, tmp_path):
        source = EXAMPLES / "ai_debugging" / "pricing.py"
        if not source.exists():
            pytest.skip("examples/ai_debugging not present")

        output = tmp_path / "pricing.py"
        mapping = tmp_path / "pricing.map.json"
        result = run_cli(
            str(source),
            "-o",
            str(output),
            "--save-mapping",
            str(mapping),
            "--trace-marker",
        )
        assert result.returncode == 0, result.stderr
        assert mapping.exists()

        # The latent bug crashes the obfuscated build with mangled names.
        crashed = run_script(output)
        assert crashed.returncode != 0
        assert "KeyError: 'discount_rate'" in crashed.stderr
        assert (
            "order_total" not in crashed.stderr
        ), "the obfuscated traceback should not leak the original function name"

        trace_file = tmp_path / "obf_trace.txt"
        trace_file.write_text(crashed.stderr, encoding="utf-8")

        unmapped = run_cli("--unmap", "--trace", str(trace_file), "--mapping", str(mapping))
        assert unmapped.returncode == 0, unmapped.stderr
        for original_name in ("order_total", "subtotal", "line_items"):
            assert (
                original_name in unmapped.stdout
            ), f"--unmap did not restore {original_name!r}:\n{unmapped.stdout}"


class TestImportHookExample:
    def test_stdlib_loader_loads_obfuscated_module(self, tmp_path):
        app_source = EXAMPLES / "import_hook" / "app.py"
        loader_source = EXAMPLES / "import_hook" / "loader.py"
        if not app_source.exists() or not loader_source.exists():
            pytest.skip("examples/import_hook not present")

        # loader.py resolves its obfuscated directory relative to its own
        # location, so it has to sit next to obf/.
        shutil.copy2(loader_source, tmp_path / "loader.py")
        output = tmp_path / "obf" / "app.py"
        mapping = tmp_path / "app.map.json"
        result = run_cli(str(app_source), "-o", str(output), "--save-mapping", str(mapping))
        assert result.returncode == 0, result.stderr
        assert mapping.exists()

        loaded = run_script(tmp_path / "loader.py", cwd=tmp_path)
        assert loaded.returncode == 0, loaded.stderr
        assert "loaded obfuscated module via custom import hook" in loaded.stdout

        # The hook only ever sees the obfuscated module: the deliberately
        # obvious identifiers from app.py must be gone from what it loads.
        obfuscated_source = output.read_text(encoding="utf-8")
        for original_name in ("top_secret_algorithm", "ConfidentialService", "API_TOKEN"):
            assert (
                original_name not in obfuscated_source
            ), f"{original_name!r} survived obfuscation and reached the import hook"
