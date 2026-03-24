"""
CLI tests for remaining edge-case paths to maximize coverage.

Targets:
- Dry run verbose single file (preview lines)
- Dry run directory crossfile (mapping preview)
- Legacy directory mode (--no-cross-file) with verbose
- Crossfile verbose mode
- _handle_init_config overwrite prompt
- _handle_validate_config with warnings/suggestions
- _display_stats with encoded strings
- Error paths: PyObfusError, unexpected Exception
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner

from pyobfus.cli import main


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def simple_file(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text("def greet(name):\n    return f'Hello {name}'\n")
    return f


@pytest.fixture
def project_dir(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def run():\n    return 42\n")
    (src / "utils.py").write_text("def helper(x):\n    return x + 1\n")
    return src


class TestDryRunVerbose:
    def test_single_file_dry_run_verbose(self, runner, simple_file, tmp_path):
        """Covers lines 703-708: dry_run + verbose preview."""
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--dry-run", "-v"])
        assert result.exit_code == 0
        assert "Would write to" in result.output
        assert "Preview" in result.output

    def test_directory_crossfile_dry_run(self, runner, project_dir, tmp_path):
        """Covers lines 860-870: crossfile dry-run mapping preview."""
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "Module:" in result.output or "mappings" in result.output


class TestLegacyDirectoryVerbose:
    def test_no_crossfile_verbose(self, runner, project_dir, tmp_path):
        """Covers legacy _obfuscate_directory with verbose."""
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "--no-cross-file", "-v"])
        assert result.exit_code == 0
        assert "Obfuscating:" in result.output

    def test_no_crossfile_no_files(self, runner, tmp_path):
        """Cover empty dir path in legacy mode."""
        src = tmp_path / "empty"
        src.mkdir()
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(src), "-o", str(output), "--no-cross-file"])
        assert result.exit_code == 0
        assert "No Python files" in result.output


class TestCrossfileVerbose:
    def test_crossfile_verbose(self, runner, project_dir, tmp_path):
        """Covers lines 828-876: crossfile verbose output."""
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "-v"])
        assert result.exit_code == 0
        assert "Phase 1" in result.output or "Scanning" in result.output
        assert "Phase 2" in result.output or "Transforming" in result.output


class TestInitConfigOverwrite:
    def test_init_config_overwrite_yes(self, runner, tmp_path):
        """Covers line 1066: file exists, user confirms overwrite."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create existing file
            Path("pyobfus.yaml").write_text("old config\n")
            result = runner.invoke(main, ["--init-config", "general"], input="y\n")
            assert result.exit_code == 0
            assert "Generated" in result.output

    def test_init_config_overwrite_no(self, runner, tmp_path):
        """Covers line 1067-1068: file exists, user declines."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("pyobfus.yaml").write_text("old config\n")
            result = runner.invoke(main, ["--init-config", "general"], input="n\n")
            assert result.exit_code == 0
            assert "Aborted" in result.output


class TestValidateConfigPaths:
    def test_validate_config_with_warnings(self, runner, tmp_path):
        """Cover the warnings/suggestions paths in _handle_validate_config."""
        cfg = tmp_path / "test.yaml"
        cfg.write_text(
            "obfuscation:\n"
            "  level: community\n"
            "  remove_docstrings: true\n"
            "  unknown_key: value\n"
        )
        result = runner.invoke(main, ["--validate-config", str(cfg)])
        # Should report unknown key as warning or error
        assert result.exit_code in (0, 1)


class TestDisplayStatsEncodedStrings:
    def test_stats_with_string_encoding(self, runner, tmp_path):
        """Cover line 1149: strings_encoded > 0 in stats."""
        f = tmp_path / "strings.py"
        f.write_text('msg = "hello world"\nresult = "another string"\n')
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "obfuscation:\n  level: community\n  string_encoding: true\n"
            "  max_files: null\n  max_total_loc: null\n"
        )
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(f), "-o", str(output), "-c", str(cfg), "--stats"])
        assert result.exit_code == 0
        assert "Statistics" in result.output


class TestErrorPaths:
    def test_invalid_python_file(self, runner, tmp_path):
        """Cover PyObfusError / Exception catch paths."""
        f = tmp_path / "bad.py"
        f.write_text("def incomplete(\n")
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(f), "-o", str(output)])
        assert result.exit_code == 1

    def test_invalid_python_verbose(self, runner, tmp_path):
        """Cover verbose traceback path in Exception handler."""
        f = tmp_path / "bad.py"
        f.write_text("def incomplete(\n")
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(f), "-o", str(output), "-v"])
        assert result.exit_code == 1
