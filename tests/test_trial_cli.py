"""Tests for trial CLI (pyobfus-trial) commands."""

import pytest
from unittest.mock import patch
from click.testing import CliRunner

from pyobfus.trial_cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestTrialStart:
    @patch("pyobfus.trial_cli.start_trial")
    def test_start_success(self, mock_start, runner):
        mock_start.return_value = {
            "success": True,
            "message": "Trial started!",
            "expires": "2026-03-29",
            "days_remaining": 5,
        }
        result = runner.invoke(cli, ["start"])
        assert result.exit_code == 0
        assert "SUCCESS" in result.output
        assert "5 days" in result.output

    @patch("pyobfus.trial_cli.start_trial")
    def test_start_unavailable(self, mock_start, runner):
        mock_start.return_value = {
            "success": False,
            "message": "Trial already used",
        }
        result = runner.invoke(cli, ["start"])
        assert result.exit_code == 1
        assert "UNAVAILABLE" in result.output


class TestTrialStatus:
    @patch("pyobfus.trial_cli.get_trial_status")
    def test_status_no_trial(self, mock_status, runner):
        mock_status.return_value = None
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "NO TRIAL FOUND" in result.output

    @patch("pyobfus.trial_cli.get_trial_status")
    def test_status_active(self, mock_status, runner):
        mock_status.return_value = {
            "active": True,
            "started": "2026-03-24T00:00:00",
            "expires_formatted": "2026-03-29",
            "days_remaining": 5,
        }
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "ACTIVE" in result.output

    @patch("pyobfus.trial_cli.get_trial_status")
    def test_status_expiring_soon(self, mock_status, runner):
        mock_status.return_value = {
            "active": True,
            "started": "2026-03-22T00:00:00",
            "expires_formatted": "2026-03-25",
            "days_remaining": 1,
        }
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "EXPIRING SOON" in result.output

    @patch("pyobfus.trial_cli.get_trial_status")
    def test_status_expired(self, mock_status, runner):
        mock_status.return_value = {
            "active": False,
            "started": "2026-03-15T00:00:00",
            "expires_formatted": "2026-03-20",
            "days_remaining": 0,
        }
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "EXPIRED" in result.output


class TestTrialFeatures:
    def test_features_command(self, runner):
        result = runner.invoke(cli, ["features"])
        assert result.exit_code == 0
        assert "AES-256" in result.output
        assert "Anti-Debugging" in result.output
        assert "Control Flow" in result.output


class TestTrialVersion:
    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "pyobfus-trial" in result.output
