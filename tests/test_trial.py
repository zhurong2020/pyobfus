"""
Tests for the trial management system.
"""

import json
import pytest
from datetime import datetime, timedelta

from pyobfus.trial import (
    start_trial,
    get_trial_status,
    is_trial_active,
    get_trial_expiry_message,
    get_device_id,
    TRIAL_FILE,
    TRIAL_DURATION,
)


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

    @pytest.fixture(autouse=True)
    def cleanup_trial(self):
        """Clean up trial file before and after each test."""
        if TRIAL_FILE.exists():
            TRIAL_FILE.unlink()
        yield
        if TRIAL_FILE.exists():
            TRIAL_FILE.unlink()

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

    @pytest.fixture(autouse=True)
    def cleanup_trial(self):
        """Clean up trial file before and after each test."""
        if TRIAL_FILE.exists():
            TRIAL_FILE.unlink()
        yield
        if TRIAL_FILE.exists():
            TRIAL_FILE.unlink()

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
