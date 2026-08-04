"""Tests for license CLI (pyobfus-license) `status` command, including the
M0 (VSCode extension prerequisite, P2-2) `--json` addition.

No prior test file exercised `pyobfus_pro/cli.py`'s Click group directly
(existing `test_license_*.py` files test the underlying `license.py`
functions) -- this is the first.
"""

import json

import pytest
from unittest.mock import patch
from click.testing import CliRunner

from pyobfus_pro.cli import cli
from pyobfus_pro.license import LicenseError

_FAKE_DEVICE = {
    "fingerprint": "8df7138666f1f7f0",
    "name": "test-host",
    "system": "Linux",
    "release": "6.6.87.2",
    "machine": "x86_64",
    "processor": "x86_64",
}


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_device_info():
    with patch("pyobfus_pro.fingerprint.get_device_info", return_value=_FAKE_DEVICE):
        yield


class TestLicenseStatusText:
    """Baseline text-mode behavior, unchanged by the --json addition."""

    @patch("pyobfus_pro.cli.get_license_status")
    def test_no_license(self, mock_status, runner):
        mock_status.return_value = None
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 1
        assert "No license key registered" in result.output

    @patch("pyobfus_pro.cli.get_license_status")
    def test_active_license(self, mock_status, runner):
        mock_status.return_value = {
            "key": "PYOB-XXXX-XXXX-XXXX-1234",
            "type": "commercial",
            "expires": "2027-01-01",
            "expired": False,
            "verified_ago_days": 1,
            "cache_valid": True,
        }
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "License Information" in result.output


class TestLicenseStatusJson:
    """M0: --json on `pyobfus-license status`."""

    @patch("pyobfus_pro.cli.get_license_status")
    def test_json_no_license(self, mock_status, runner):
        mock_status.return_value = None
        result = runner.invoke(cli, ["status", "--json"])
        assert result.exit_code == 1  # matches the pre-existing text-mode exit(1)
        payload = json.loads(result.output)
        assert payload["version"] == 1
        assert payload["license_status"] is None
        assert payload["device"] == _FAKE_DEVICE

    @patch("pyobfus_pro.cli.get_license_status")
    def test_json_active_license_exit_zero(self, mock_status, runner):
        license_dict = {
            "key": "PYOB-XXXX-XXXX-XXXX-1234",
            "type": "commercial",
            "expires": "2027-01-01",
            "expired": False,
            "verified_ago_days": 1,
            "cache_valid": True,
        }
        mock_status.return_value = license_dict
        result = runner.invoke(cli, ["status", "--json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["license_status"] == license_dict
        assert "verify_result" not in payload  # --verify not passed

    @patch("pyobfus_pro.cli.get_license_status")
    def test_json_expired_license_exit_one(self, mock_status, runner):
        mock_status.return_value = {
            "key": "PYOB-XXXX-XXXX-XXXX-1234",
            "type": "commercial",
            "expires": "2020-01-01",
            "expired": True,
            "verified_ago_days": 1,
            "cache_valid": True,
        }
        result = runner.invoke(cli, ["status", "--json"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["license_status"]["expired"] is True

    @patch("pyobfus_pro.cli.verify_license")
    @patch("pyobfus_pro.cli.get_license_status")
    def test_json_with_verify_success(self, mock_status, mock_verify, runner):
        masked = {
            "key": "PYOB-XXXX-XXXX-XXXX-1234",
            "type": "commercial",
            "expires": "2027-01-01",
            "expired": False,
            "verified_ago_days": 1,
            "cache_valid": True,
        }
        full = dict(masked, key="PYOB-REAL-KEY-1234")
        # First call (masked=True) returns the masked dict, second (masked=False)
        # returns the full dict, matching get_license_status(masked=...) usage.
        mock_status.side_effect = [masked, full]
        mock_verify.return_value = {"valid": True, "message": "ok"}

        result = runner.invoke(cli, ["status", "--json", "--verify"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["verify_result"] == {"valid": True, "message": "ok"}

    @patch("pyobfus_pro.cli.verify_license")
    @patch("pyobfus_pro.cli.get_license_status")
    def test_json_with_verify_failure_exit_one(self, mock_status, mock_verify, runner):
        masked = {
            "key": "PYOB-XXXX-XXXX-XXXX-1234",
            "type": "commercial",
            "expires": "2027-01-01",
            "expired": False,
            "verified_ago_days": 1,
            "cache_valid": True,
        }
        full = dict(masked, key="PYOB-REAL-KEY-1234")
        mock_status.side_effect = [masked, full]
        mock_verify.return_value = {"valid": False, "message": "revoked"}

        result = runner.invoke(cli, ["status", "--json", "--verify"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["verify_result"]["valid"] is False

    @patch("pyobfus_pro.cli.get_license_status")
    def test_json_output_has_no_ansi_color_codes(self, mock_status, runner):
        mock_status.return_value = {
            "key": "PYOB-XXXX-XXXX-XXXX-1234",
            "type": "commercial",
            "expires": "2027-01-01",
            "expired": False,
            "verified_ago_days": 1,
            "cache_valid": True,
        }
        result = runner.invoke(cli, ["status", "--json"])
        assert "\x1b[" not in result.output
        json.loads(result.output)

    @patch("pyobfus_pro.cli.get_license_status")
    def test_json_error_path_emits_structured_error(self, mock_status, runner):
        mock_status.side_effect = LicenseError("cache corrupted")
        result = runner.invoke(cli, ["status", "--json"])
        assert result.exit_code == 1
        payload = json.loads(result.output)
        assert payload["status"] == "error"
        assert payload["error_type"] == "LicenseError"
        assert "cache corrupted" in payload["message"]
