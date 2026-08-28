"""
Tests for the trial management system.
"""

import json
import sys
import pytest
from datetime import datetime, timedelta
from pathlib import Path

import pyobfus.trial as trial_module

from pyobfus.trial import (
    start_trial,
    get_trial_status,
    is_trial_active,
    get_trial_expiry_message,
    get_device_id,
    TRIAL_FILE,
    TRIAL_DURATION,
)


@pytest.fixture(autouse=True)
def isolated_trial_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep trial tests away from the developer's real ~/.pyobfus state."""
    trial_dir = tmp_path / ".pyobfus"
    trial_file = trial_dir / "trial.json"
    monkeypatch.setattr(trial_module, "TRIAL_DIR", trial_dir)
    monkeypatch.setattr(trial_module, "TRIAL_FILE", trial_file)
    monkeypatch.setattr(sys.modules[__name__], "TRIAL_FILE", trial_file)
    assert trial_module.TRIAL_FILE.is_relative_to(tmp_path)


class TestTrialDeviceId:
    """Tests for device ID generation."""

    def test_device_id_is_string(self):
        """Device ID should be a string."""
        device_id = get_device_id()
        assert isinstance(device_id, str)

    def test_device_id_length(self):
        """Device ID should be 16 characters."""
        device_id = get_device_id()
        assert len(device_id) == 16

    def test_device_id_is_hex(self):
        """Device ID should be hexadecimal."""
        device_id = get_device_id()
        int(device_id, 16)  # Should not raise

    def test_device_id_is_consistent(self):
        """Device ID should be the same on repeated calls."""
        id1 = get_device_id()
        id2 = get_device_id()
        assert id1 == id2


class TestTrialManagement:
    """Tests for trial start and status."""

    def test_no_trial_initially(self):
        """Should return None when no trial exists."""
        status = get_trial_status()
        assert status is None

    def test_is_trial_active_initially_false(self):
        """is_trial_active should return False when no trial exists."""
        assert is_trial_active() is False

    def test_start_trial_success(self):
        """Starting a trial should succeed."""
        result = start_trial()
        assert result["success"] is True
        assert "Trial started" in result["message"]
        assert result["days_remaining"] == TRIAL_DURATION.days

    def test_trial_file_created(self):
        """Trial file should be created after starting."""
        start_trial()
        assert TRIAL_FILE.exists()

    def test_get_trial_status_after_start(self):
        """Should return active status after starting trial."""
        start_trial()
        status = get_trial_status()
        assert status is not None
        assert status["active"] is True
        assert status["days_remaining"] >= 0

    def test_is_trial_active_after_start(self):
        """is_trial_active should return True after starting trial."""
        start_trial()
        assert is_trial_active() is True

    def test_start_trial_twice(self):
        """Starting trial twice should return existing trial info."""
        result1 = start_trial()
        result2 = start_trial()
        assert result1["success"] is True
        assert result2["success"] is True
        assert "already active" in result2["message"]

    def test_trial_expiry_message_active(self):
        """Should return expiry message when trial is active."""
        start_trial()
        message = get_trial_expiry_message()
        assert message is not None
        assert "expires" in message.lower()

    def test_trial_expiry_message_no_trial(self):
        """Should return None when no trial exists."""
        message = get_trial_expiry_message()
        assert message is None


class TestTrialExpiration:
    """Tests for trial expiration behavior."""

    def test_expired_trial_not_active(self):
        """Expired trial should not be active."""
        # Create an expired trial
        device_id = get_device_id()
        expired_time = datetime.now() - timedelta(days=10)
        trial_data = {
            "v": 1,
            "device_id": device_id,
            "started": expired_time.isoformat(),
            "expires": (expired_time + TRIAL_DURATION).isoformat(),
        }
        TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRIAL_FILE, "w") as f:
            json.dump(trial_data, f)

        assert is_trial_active() is False

    def test_expired_trial_cannot_restart(self):
        """Cannot restart an expired trial."""
        # Create an expired trial
        device_id = get_device_id()
        expired_time = datetime.now() - timedelta(days=10)
        trial_data = {
            "v": 1,
            "device_id": device_id,
            "started": expired_time.isoformat(),
            "expires": (expired_time + TRIAL_DURATION).isoformat(),
        }
        TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRIAL_FILE, "w") as f:
            json.dump(trial_data, f)

        result = start_trial()
        assert result["success"] is False
        assert "already been used" in result["message"]

    def test_expired_trial_message(self):
        """Expired trial should show purchase message."""
        # Create an expired trial
        device_id = get_device_id()
        expired_time = datetime.now() - timedelta(days=10)
        trial_data = {
            "v": 1,
            "device_id": device_id,
            "started": expired_time.isoformat(),
            "expires": (expired_time + TRIAL_DURATION).isoformat(),
        }
        TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRIAL_FILE, "w") as f:
            json.dump(trial_data, f)

        message = get_trial_expiry_message()
        assert message is not None
        assert "expired" in message.lower()


class TestTrialTrustBoundary:
    """Pins the documented trust boundary of the trial (issues #20, #21).

    The trial is a convenience control, not a security boundary: state is an
    unsigned JSON file and ``TRIAL_DURATION`` is a plain module constant in
    readable source. These tests assert that tampering *succeeds*, so that the
    limitation stays explicit. If someone later adds signing or a server-issued
    entitlement, these tests are expected to fail — that is the signal to
    re-read SECURITY.md and update the documented boundary deliberately rather
    than shipping a change that only looks like enforcement.
    """

    def test_trial_state_is_unsigned_plaintext(self):
        """State carries no signature or MAC that could detect edits."""
        start_trial()
        with open(TRIAL_FILE, "r", encoding="utf-8") as f:
            trial_data = json.load(f)

        assert set(trial_data) == {"v", "device_id", "started", "expires"}
        assert not any(k in trial_data for k in ("sig", "signature", "hmac", "mac"))

    def test_hand_edited_expiry_is_accepted(self):
        """Issue #20: editing the expiry date extends the trial."""
        start_trial()
        with open(TRIAL_FILE, "r", encoding="utf-8") as f:
            trial_data = json.load(f)

        trial_data["expires"] = datetime(9999, 1, 1).isoformat()
        with open(TRIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(trial_data, f)

        assert is_trial_active() is True

    def test_expired_trial_reactivated_by_editing_state(self):
        """An exhausted trial can be revived by editing the same file."""
        device_id = get_device_id()
        expired_time = datetime.now() - timedelta(days=10)
        TRIAL_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TRIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "v": 1,
                    "device_id": device_id,
                    "started": expired_time.isoformat(),
                    "expires": (expired_time + TRIAL_DURATION).isoformat(),
                },
                f,
            )
        assert is_trial_active() is False

        with open(TRIAL_FILE, "r", encoding="utf-8") as f:
            trial_data = json.load(f)
        trial_data["expires"] = (datetime.now() + timedelta(days=30)).isoformat()
        with open(TRIAL_FILE, "w", encoding="utf-8") as f:
            json.dump(trial_data, f)

        assert is_trial_active() is True

    def test_trial_duration_is_a_patchable_constant(self):
        """Issue #21: TRIAL_DURATION is module state, editable at runtime."""
        import pyobfus.trial as trial_module

        original = trial_module.TRIAL_DURATION
        try:
            trial_module.TRIAL_DURATION = timedelta(days=100_000)
            result = start_trial()
            assert result["success"] is True
            assert result["days_remaining"] == 100_000
        finally:
            trial_module.TRIAL_DURATION = original
