"""Tests for trial CLI (pyobfus-trial) commands."""

import json

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


class TestTrialStatusJson:
    """M0 (VSCode extension prerequisite, P2-2): --json on `pyobfus-trial status`."""

    @patch("pyobfus.trial_cli.get_trial_status")
    def test_json_no_trial(self, mock_status, runner):
        mock_status.return_value = None
        result = runner.invoke(cli, ["status", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {"version": 1, "trial_status": None}

    @patch("pyobfus.trial_cli.get_trial_status")
    def test_json_active_trial_returns_dict_verbatim(self, mock_status, runner):
        status_dict = {
            "active": True,
            "started": "2026-03-24T00:00:00",
            "expires_formatted": "2026-03-29",
            "days_remaining": 5,
        }
        mock_status.return_value = status_dict
        result = runner.invoke(cli, ["status", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["version"] == 1
        assert payload["trial_status"] == status_dict

    @patch("pyobfus.trial_cli.get_trial_status")
    def test_json_output_has_no_ansi_color_codes(self, mock_status, runner):
        """Unlike the text mode (which uses click.style ANSI colors), --json
        output must be plain machine-parseable JSON with no styling."""
        mock_status.return_value = {
            "active": True,
            "started": "2026-03-24T00:00:00",
            "expires_formatted": "2026-03-29",
            "days_remaining": 5,
        }
        result = runner.invoke(cli, ["status", "--json"])
        assert "\x1b[" not in result.output
        json.loads(result.output)  # must parse cleanly with nothing else on stdout


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
