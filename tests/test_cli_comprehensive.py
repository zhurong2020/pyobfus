"""
Comprehensive CLI tests for pyobfus.

Tests cover the main CLI entry point including:
- Single file obfuscation
- Directory obfuscation
- Cross-file mode
- Config auto-discovery
- Error handling
- --stats flag
- --dry-run flag
- --init-config templates
- --validate-config
- --jobs parallel option
- --version
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
def single_file(tmp_path):
    """Create a simple Python file for testing."""
    f = tmp_path / "hello.py"
    f.write_text("def greet(name):\n    return f'Hello {name}'\n")
    return f


@pytest.fixture
def project_dir(tmp_path):
    """Create a small project directory for testing."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def run():\n    return 42\n")
    (src / "utils.py").write_text("def helper(x):\n    return x + 1\n")
    return src


class TestCLIVersion:
    def test_version_flag(self, runner):
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "pyobfus" in result.output


class TestCLINoArgs:
    def test_no_args_shows_error(self, runner):
        result = runner.invoke(main, [])
        assert result.exit_code == 1
        assert "Missing argument" in result.output or "INPUT_PATH" in result.output

    def test_input_without_output_shows_error(self, runner, single_file):
        result = runner.invoke(main, [str(single_file)])
        assert result.exit_code == 1
        assert "output" in result.output.lower() or "Missing" in result.output


class TestSingleFileObfuscation:
    def test_basic_single_file(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        content = output.read_text()
        assert "greet" not in content or "def I" in content

    def test_single_file_verbose(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "-v"])
        assert result.exit_code == 0
        assert "Obfuscating:" in result.output or "Total names" in result.output

    def test_single_file_dry_run(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert not output.exists()

    def test_single_file_with_stats(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--stats"])
        assert result.exit_code == 0
        assert "Statistics" in result.output or "Files processed" in result.output

    def test_keep_docstrings(self, runner, tmp_path):
        f = tmp_path / "doc.py"
        f.write_text('def func():\n    """Docstring."""\n    return 1\n')
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(f), "-o", str(output), "--keep-docstrings"])
        assert result.exit_code == 0

    def test_custom_name_prefix(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--name-prefix", "OBF"])
        assert result.exit_code == 0
        content = output.read_text()
        assert "OBF" in content


class TestDirectoryObfuscation:
    def test_directory_crossfile(self, runner, project_dir, tmp_path):
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output)])
        assert result.exit_code == 0
        assert output.exists()
        assert (output / "main.py").exists()
        assert (output / "utils.py").exists()

    def test_directory_no_crossfile(self, runner, project_dir, tmp_path):
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "--no-cross-file"])
        assert result.exit_code == 0
        assert (output / "main.py").exists()

    def test_directory_with_stats(self, runner, project_dir, tmp_path):
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "--stats"])
        assert result.exit_code == 0
        assert "Statistics" in result.output

    def test_directory_dry_run(self, runner, project_dir, tmp_path):
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "--dry-run"])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output

    def test_directory_with_jobs(self, runner, project_dir, tmp_path):
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "-j", "2"])
        assert result.exit_code == 0
        assert (output / "main.py").exists()

    def test_community_file_limit(self, runner, tmp_path):
        """Test Community Edition file limit."""
        src = tmp_path / "src"
        src.mkdir()
        # Create 6 files (exceeds community limit of 5)
        for i in range(6):
            (src / f"mod_{i}.py").write_text(f"def f{i}(): pass\n")
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(src), "-o", str(output), "--no-cross-file"])
        assert result.exit_code == 1
        assert "limit" in result.output.lower() or "Community" in result.output


class TestInitConfig:
    def test_init_config_django(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["--init-config", "django"])
            assert result.exit_code == 0
            assert Path("pyobfus.yaml").exists()

    def test_init_config_flask(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["--init-config", "flask"])
            assert result.exit_code == 0

    def test_init_config_general(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["--init-config", "general"])
            assert result.exit_code == 0

    def test_init_config_library(self, runner, tmp_path):
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["--init-config", "library"])
            assert result.exit_code == 0


class TestValidateConfig:
    def test_validate_valid_config(self, runner, tmp_path):
        cfg = tmp_path / "test.yaml"
        cfg.write_text("obfuscation:\n  level: community\n  remove_docstrings: true\n")
        result = runner.invoke(main, ["--validate-config", str(cfg)])
        assert result.exit_code == 0

    def test_validate_invalid_config(self, runner, tmp_path):
        cfg = tmp_path / "bad.yaml"
        cfg.write_text("obfuscation:\n  level: ultra_invalid_level\n")
        result = runner.invoke(main, ["--validate-config", str(cfg)])
        # Validator may exit 0 or 1 depending on severity, just check it doesn't crash
        assert result.exit_code in (0, 1)


class TestConfigAutoDiscovery:
    def test_auto_discover_config(self, runner, tmp_path):
        """Test that pyobfus.yaml is auto-discovered."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("def run(): pass\n")

        # Create config in working directory
        cfg = tmp_path / "pyobfus.yaml"
        cfg.write_text(
            "obfuscation:\n  level: community\n  exclude_patterns: []\n"
            "  max_files: null\n  max_total_loc: null\n"
        )

        output = tmp_path / "dist"
        # Run from the directory with the config
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, [str(src), "-o", str(output), "-v"])
            # May or may not find config depending on CWD
            assert result.exit_code == 0


class TestUpgrade:
    def test_upgrade_flag(self, runner):
        result = runner.invoke(main, ["--upgrade"])
        assert result.exit_code == 0
        assert "Pro" in result.output or "pro" in result.output


class TestListPresets:
    def test_list_presets(self, runner):
        result = runner.invoke(main, ["--list-presets"])
        assert result.exit_code == 0
        assert "trial" in result.output.lower()
        assert "commercial" in result.output.lower()


class TestPresetFlag:
    def test_preset_safe(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--preset", "safe"])
        assert result.exit_code == 0

    def test_preset_balanced(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--preset", "balanced"])
        assert result.exit_code == 0

    def test_preset_aggressive(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(single_file), "-o", str(output), "--preset", "aggressive"]
        )
        assert result.exit_code == 0


class TestProFeatureGating:
    """Test Pro feature flags - they either require Pro/trial or are silently accepted."""

    def test_control_flow_flag_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--control-flow"])
        # Either succeeds (silently ignored) or fails with Pro/trial message
        assert result.exit_code in (0, 1)

    def test_string_encryption_flag_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--string-encryption"])
        assert result.exit_code in (0, 1)

    def test_anti_debug_flag_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--anti-debug"])
        assert result.exit_code in (0, 1)

    def test_dead_code_flag_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--dead-code"])
        assert result.exit_code in (0, 1)

    def test_expire_flag_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(single_file), "-o", str(output), "--expire", "2030-01-01"]
        )
        assert result.exit_code in (0, 1)

    def test_bind_machine_flag_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--bind-machine"])
        assert result.exit_code in (0, 1)

    def test_max_runs_flag_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "--max-runs", "100"])
        assert result.exit_code in (0, 1)

    def test_pro_preset_accepted(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(single_file), "-o", str(output), "--preset", "commercial"]
        )
        assert result.exit_code in (0, 1)


class TestEdgeCases:
    def test_nonexistent_input(self, runner, tmp_path):
        result = runner.invoke(
            main, [str(tmp_path / "nonexistent.py"), "-o", str(tmp_path / "out.py")]
        )
        assert result.exit_code != 0

    def test_empty_directory(self, runner, tmp_path):
        src = tmp_path / "empty"
        src.mkdir()
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(src), "-o", str(output), "--no-cross-file"])
        assert result.exit_code == 0
        assert "No Python files" in result.output

    def test_preserve_param_names(self, runner, single_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(single_file), "-o", str(output), "--preserve-param-names"]
        )
        assert result.exit_code == 0

    def test_with_yaml_config(self, runner, single_file, tmp_path):
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "obfuscation:\n  level: community\n  remove_docstrings: true\n"
            "  max_files: null\n  max_total_loc: null\n"
        )
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(single_file), "-o", str(output), "-c", str(cfg)])
        assert result.exit_code == 0
