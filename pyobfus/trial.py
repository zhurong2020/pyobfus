"""
Trial Management System for pyobfus Professional Edition.

This module implements a 5-day trial for Pro features without requiring
registration or payment.

Trust boundary — read before relying on this for enforcement
------------------------------------------------------------
The trial is a **convenience control, not a security boundary**. It records
state in an unsigned JSON file under the user's home directory, and this
module ships as readable Apache-2.0 source. A user who controls the machine
can edit either the state file or ``TRIAL_DURATION`` below, and no
client-side arrangement can prevent that: an open-source verifier is always
patchable by the person running it.

The device ID is therefore a *scoping* mechanism (it keeps a trial record
from being copied between machines by accident), not an anti-tamper one.
Deliberate bypass is expected and accepted; the trial exists to give honest
evaluators a frictionless five days, not to stop determined ones.

Making Pro enforcement a genuine boundary would require not shipping Pro as
readable source in the public wheel — a distribution-model change, not a
change to this file. See GitHub issues #20 and #21 for the full discussion.

Design goals:
- No registration required (reduce friction)
- 5-day duration
- Per-machine trial record (scoping, not enforcement)
- Clear, honest messaging about trial status
"""

import hashlib
import json
import platform
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

# Trial configuration
TRIAL_DIR = Path.home() / ".pyobfus"
TRIAL_FILE = TRIAL_DIR / "trial.json"
TRIAL_DURATION = timedelta(days=5)


def get_device_id() -> str:
    """
    Get a device identifier used to scope a trial record to one machine.

    Uses a combination of hostname and MAC address to create a stable ID.
    This is not a security control: both inputs are user-controllable, and
    the value only decides whether an existing trial record applies here.

    Returns:
        str: 16-character hex device ID
    """
    try:
        # Get MAC address
        mac = hex(uuid.getnode())[2:].upper()
    except Exception:
        mac = "UNKNOWN"

    # Get hostname
    hostname = platform.node() or "UNKNOWN"

    # Create hash
    data = f"{mac}:{hostname}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def start_trial() -> Dict[str, Any]:
    """
    Start a 5-day trial of Pro features.

    Returns:
        dict: Trial status with keys:
            - success: bool
            - message: str
            - expires: str (ISO format date)
            - days_remaining: int

    Never raises for an already-used trial; it returns ``success: False``
    with an explanatory message instead.
    """
    # Check if trial already exists
    existing = get_trial_status()

    if existing:
        if existing["active"]:
            return {
                "success": True,
                "message": "Trial already active",
                "expires": existing["expires"],
                "days_remaining": existing["days_remaining"],
            }
        else:
            # Trial expired - cannot restart
            return {
                "success": False,
                "message": "Trial has already been used on this device. "
                "Purchase a license to continue using Pro features.",
                "expires": existing["expires"],
                "days_remaining": 0,
            }

    # Start new trial
    device_id = get_device_id()
    start_time = datetime.now()
    expires = start_time + TRIAL_DURATION

    trial_data = {
        "v": 1,  # Schema version
        "device_id": device_id,
        "started": start_time.isoformat(),
        "expires": expires.isoformat(),
    }

    # Save trial data
    TRIAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(trial_data, f, indent=2)

    return {
        "success": True,
        "message": "Trial started successfully! You can now use Pro features.",
        "expires": expires.strftime("%Y-%m-%d %H:%M"),
        "days_remaining": TRIAL_DURATION.days,
    }


def get_trial_status() -> Optional[Dict[str, Any]]:
    """
    Get current trial status.

    Returns:
        dict: Trial status or None if no trial exists
            - active: bool (True if trial is currently valid)
            - expires: str (ISO format date)
            - days_remaining: int (negative if expired)
            - device_id: str
    """
    if not TRIAL_FILE.exists():
        return None

    try:
        with open(TRIAL_FILE, "r", encoding="utf-8") as f:
            trial_data = json.load(f)

        # Verify device ID
        current_device = get_device_id()
        if trial_data.get("device_id") != current_device:
            # Different device - trial not valid here
            return None

        # Calculate remaining time
        expires = datetime.fromisoformat(trial_data["expires"])
        now = datetime.now()
        remaining = expires - now
        days_remaining = remaining.days

        return {
            "active": remaining.total_seconds() > 0,
            "expires": trial_data["expires"],
            "expires_formatted": expires.strftime("%Y-%m-%d %H:%M"),
            "started": trial_data["started"],
            "days_remaining": max(0, days_remaining),
            "device_id": trial_data["device_id"],
        }

    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def is_trial_active() -> bool:
    """
    Check if a valid trial is currently active.

    This is the main function used by the CLI to determine if
    Pro features should be enabled.

    Returns:
        bool: True if trial is active and valid
    """
    status = get_trial_status()
    return status is not None and status["active"]


def get_trial_expiry_message() -> Optional[str]:
    """
    Get a user-friendly message about trial expiration.

    Returns:
        str: Message about trial status, or None if no trial
    """
    status = get_trial_status()
    if not status:
        return None

    if status["active"]:
        days = status["days_remaining"]
        if days == 0:
            return "Trial expires today!"
        elif days == 1:
            return "Trial expires tomorrow!"
        else:
            return f"Trial expires in {days} days"
    else:
        return "Trial has expired. Purchase a license to continue using Pro features."


__all__ = [
    "start_trial",
    "get_trial_status",
    "is_trial_active",
    "get_trial_expiry_message",
    "TRIAL_DURATION",
]
