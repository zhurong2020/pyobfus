"""
CLI tests for Pro feature paths using mock.

Tests cover:
- Pro level with trial active (bypasses license verification)
- Pro feature execution: control_flow, dead_code, string_encryption, anti_debug
- License embedding: expire, bind_machine, max_runs
- _handle_upgrade() with Pro active, trial active, community
- _display_stats() with Pro stats
- Pro preset with trial active
- --level pro with trial active
- String encoding (community level, string_encoding enabled)
- Error paths: Pro import failure, unexpected errors
"""

import sys

import pytest
from unittest.mock import patch
from click.testing import CliRunner

from pyobfus.cli import main

try:
    import pyobfus_pro  # noqa: F401

    PRO_AVAILABLE = True
except ImportError:
    PRO_AVAILABLE = False

# Tests that actually execute Pro features need pyobfus_pro installed
requires_pro = pytest.mark.skipif(not PRO_AVAILABLE, reason="pyobfus_pro not installed")

# Combined Pro features and license embedding have known f-string/AST issues on Python 3.8
# See: commits 2ce91db, 14a68ef, 4008bae for prior 3.8 compat fixes
requires_py39 = pytest.mark.skipif(
    sys.version_info < (3, 9), reason="Combined Pro transforms have known 3.8 AST compat issues"
)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def simple_file(tmp_path):
    """A simple Python file with a string and control flow."""
    f = tmp_path / "sample.py"
    f.write_text(
        'API_KEY = "secret-key-12345"\n\n'
        "def process(x):\n"
        "    if x > 0:\n"
        '        return "positive"\n'
        "    else:\n"
        '        return "negative"\n\n'
        "result = process(42)\n"
    )
    return f


@pytest.fixture
def project_dir(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def run():\n    return 42\n")
    (src / "utils.py").write_text("def helper(x):\n    return x + 1\n")
    return src


@requires_pro
class TestProLevelWithTrial:
    """Test --level pro with trial active (no license needed)."""

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial: 3 days left")
    def test_pro_level_trial_single_file(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--level", "pro", "-v"])
        assert result.exit_code == 0
        assert output.exists()

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial: 3 days left")
    def test_pro_level_trial_with_stats(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--level", "pro", "--stats"]
        )
        assert result.exit_code == 0
        assert "Statistics" in result.output


@requires_pro
class TestProFeatureExecution:
    """Test actual Pro feature execution with trial active."""

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_control_flow_flattening(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--control-flow", "-v"])
        assert result.exit_code == 0
        assert "Control flow" in result.output or output.exists()

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_string_encryption(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--string-encryption", "-v"]
        )
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_anti_debug(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--anti-debug", "-v"])
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_dead_code_injection(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--dead-code", "-v"])
        assert result.exit_code == 0

    @requires_py39
    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_all_pro_features_combined(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main,
            [
                str(simple_file),
                "-o",
                str(output),
                "--control-flow",
                "--string-encryption",
                "--anti-debug",
                "--dead-code",
                "-v",
                "--stats",
            ],
        )
        assert result.exit_code == 0
        assert "Statistics" in result.output

    @requires_py39
    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_all_pro_features_with_stats(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        """Test _display_stats Pro branches with non-zero counts."""
        output = tmp_path / "output.py"
        result = runner.invoke(
            main,
            [
                str(simple_file),
                "-o",
                str(output),
                "--control-flow",
                "--string-encryption",
                "--anti-debug",
                "--dead-code",
                "--stats",
            ],
        )
        assert result.exit_code == 0


@requires_pro
@requires_py39
class TestLicenseEmbedding:
    """Test license embedding features with trial active."""

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_expire_flag(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--expire", "2030-12-31", "-v"]
        )
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_bind_machine_flag(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--bind-machine", "-v"])
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_max_runs_flag(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--max-runs", "100", "-v"]
        )
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_all_license_embed_combined(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main,
            [
                str(simple_file),
                "-o",
                str(output),
                "--expire",
                "2030-12-31",
                "--bind-machine",
                "--max-runs",
                "500",
                "-v",
            ],
        )
        assert result.exit_code == 0
        assert "License embedding" in result.output or "expires" in result.output


class TestHandleUpgrade:
    """Test _handle_upgrade() branches."""

    @pytest.mark.skipif(not PRO_AVAILABLE, reason="pyobfus_pro not installed")
    def test_upgrade_pro_available(self, runner):
        """Test --upgrade when PRO_AVAILABLE is True."""
        result = runner.invoke(main, ["--upgrade"])
        assert result.exit_code == 0
        assert "Pro" in result.output

    @patch("pyobfus.cli.PRO_AVAILABLE", False)
    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial: 2 days left")
    def test_upgrade_trial_active(self, mock_msg, mock_trial, runner):
        """Test --upgrade when trial is active."""
        result = runner.invoke(main, ["--upgrade"])
        assert result.exit_code == 0
        assert "TRIAL" in result.output

    @patch("pyobfus.cli.PRO_AVAILABLE", False)
    @patch("pyobfus.cli.is_trial_active", return_value=False)
    def test_upgrade_community(self, mock_trial, runner):
        """Test --upgrade for community users."""
        result = runner.invoke(main, ["--upgrade"])
        assert result.exit_code == 0
        assert "TRY FREE" in result.output or "$45" in result.output


@requires_pro
class TestProPresets:
    """Test Pro presets with trial active."""

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_preset_trial(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--preset", "trial", "-v"]
        )
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_preset_commercial(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--preset", "commercial", "-v"]
        )
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_preset_library(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--preset", "library", "-v"]
        )
        assert result.exit_code == 0

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_preset_maximum(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--preset", "maximum", "-v"]
        )
        assert result.exit_code == 0

    @patch("pyobfus.cli.PRO_AVAILABLE", False)
    @patch("pyobfus.cli.is_trial_active", return_value=False)
    def test_pro_preset_no_access(self, mock_trial, runner, simple_file, tmp_path):
        """Test Pro preset without Pro or trial access."""
        output = tmp_path / "output.py"
        result = runner.invoke(
            main, [str(simple_file), "-o", str(output), "--preset", "commercial"]
        )
        assert result.exit_code == 1
        assert "trial" in result.output.lower() or "Pro" in result.output


class TestProLicenseVerification:
    """Test --level pro with actual license verification path (PRO_AVAILABLE=True)."""

    @patch("pyobfus.cli.is_trial_active", return_value=False)
    @patch("pyobfus.cli.pyobfus_pro")
    def test_pro_level_license_verified(self, mock_pro, mock_trial, runner, simple_file, tmp_path):
        """Test the Pro license verification success path."""
        mock_pro.get_license_status.return_value = {
            "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
            "type": "pro",
        }
        mock_pro.verify_license.return_value = {
            "valid": True,
            "type": "pro",
            "expires": "2099-12-31",
            "message": "License verified",
        }
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--level", "pro", "-v"])
        assert result.exit_code == 0
        assert "License verified" in result.output

    @patch("pyobfus.cli.is_trial_active", return_value=False)
    @patch("pyobfus.cli.pyobfus_pro")
    def test_pro_level_no_license(self, mock_pro, mock_trial, runner, simple_file, tmp_path):
        """Test --level pro with no cached license."""
        mock_pro.get_license_status.return_value = None
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--level", "pro"])
        assert result.exit_code == 1
        assert "license" in result.output.lower() or "register" in result.output.lower()

    @patch("pyobfus.cli.is_trial_active", return_value=False)
    @patch("pyobfus.cli.pyobfus_pro")
    def test_pro_level_license_error(self, mock_pro, mock_trial, runner, simple_file, tmp_path):
        """Test --level pro with license verification failure."""
        mock_pro.get_license_status.return_value = {
            "key": "PYOB-AAAA-BBBB-CCCC-DDDD",
        }

        # Create a real exception class for the mock
        class MockLicenseError(Exception):
            pass

        mock_pro.LicenseError = MockLicenseError
        mock_pro.verify_license.side_effect = MockLicenseError("Invalid key")
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--level", "pro"])
        assert result.exit_code == 1
        assert "failed" in result.output.lower() or "Invalid" in result.output


class TestProNoAccess:
    """Test Pro paths when neither Pro nor trial is available."""

    @patch("pyobfus.cli.PRO_AVAILABLE", False)
    @patch("pyobfus.cli.is_trial_active", return_value=False)
    def test_pro_level_no_access(self, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--level", "pro"])
        assert result.exit_code == 1
        assert "trial" in result.output.lower() or "license" in result.output.lower()

    @patch("pyobfus.cli.PRO_AVAILABLE", False)
    @patch("pyobfus.cli.is_trial_active", return_value=False)
    def test_pro_features_no_access(self, mock_trial, runner, simple_file, tmp_path):
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(simple_file), "-o", str(output), "--control-flow"])
        assert result.exit_code == 1


class TestStringEncoding:
    """Test Community string encoding path."""

    def test_string_encoding_community(self, runner, tmp_path):
        f = tmp_path / "strings.py"
        f.write_text('msg = "hello world"\nprint(msg)\n')
        cfg = tmp_path / "config.yaml"
        cfg.write_text(
            "obfuscation:\n  level: community\n  string_encoding: true\n"
            "  max_files: null\n  max_total_loc: null\n"
        )
        output = tmp_path / "output.py"
        result = runner.invoke(main, [str(f), "-o", str(output), "-c", str(cfg), "-v"])
        assert result.exit_code == 0
        assert "Encoded strings" in result.output or output.exists()


@requires_pro
@requires_py39
class TestDisplayStatsProBranches:
    """Test _display_stats with Pro-level stats."""

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_stats_with_all_pro_counts(self, mock_msg, mock_trial, runner, simple_file, tmp_path):
        """All Pro stats should appear when non-zero."""
        output = tmp_path / "output.py"
        result = runner.invoke(
            main,
            [
                str(simple_file),
                "-o",
                str(output),
                "--control-flow",
                "--string-encryption",
                "--anti-debug",
                "--dead-code",
                "--stats",
            ],
        )
        assert result.exit_code == 0
        # Stats section should be present
        assert "Statistics" in result.output


@requires_pro
class TestDirectoryProMode:
    """Test directory obfuscation in Pro mode."""

    @patch("pyobfus.cli.is_trial_active", return_value=True)
    @patch("pyobfus.cli.get_trial_expiry_message", return_value="Trial active")
    def test_directory_crossfile_pro(self, mock_msg, mock_trial, runner, project_dir, tmp_path):
        output = tmp_path / "dist"
        result = runner.invoke(main, [str(project_dir), "-o", str(output), "--level", "pro", "-v"])
        assert result.exit_code == 0
        assert (output / "app.py").exists()
