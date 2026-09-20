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
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta
from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
from typing import Any, Dict, Optional

from pyobfus.constants import TRIAL_API_URL

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


def _online_user_agent() -> str:
    """Explicit UA. urllib's default ``Python-urllib/X.Y`` is refused at the
    Cloudflare edge (403 / error code 1010) — the license endpoint hit exactly
    this in 2026-09, so any request from this package must identify itself."""
    try:
        ver = _pkg_version("pyobfus")
    except PackageNotFoundError:
        ver = "0.0.0"
    return f"pyobfus/{ver} (+https://github.com/zhurong2020/pyobfus)"


def _parse_server_iso(value: str) -> datetime:
    """Parse a server ISO-8601 timestamp into a *naive local* datetime.

    The trial record stores naive local times (``datetime.now().isoformat()``)
    and ``get_trial_status`` compares against ``datetime.now()``. The server
    emits UTC with a trailing ``Z``, which ``datetime.fromisoformat`` cannot
    parse on Python 3.9/3.10; a tz-aware value would also break the naive
    comparison. Normalise both here so the stored record stays comparable.
    """
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def _request_online_trial(
    email: str, device_id: str, timeout: float = 10.0
) -> Optional[Dict[str, Any]]:
    """POST an email + device id to the trial server.

    Returns the parsed JSON dict on an HTTP response (any status the server
    itself produced, including a 4xx it chose), or ``None`` when the server
    could not be reached at all — the caller then falls back to a purely local
    trial so offline evaluators are never blocked. This is lead capture and
    per-email dedup, not enforcement (see the module docstring / issue #20-21).
    """
    payload = json.dumps({"email": email, "device_id": device_id}).encode("utf-8")
    request = urllib.request.Request(
        TRIAL_API_URL,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": _online_user_agent()},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, dict) else None
    except urllib.error.HTTPError as exc:
        # The server answered with an error status; its body is still the
        # machine-readable contract, so parse it rather than treating it as
        # unreachable.
        try:
            data = json.loads(exc.read().decode("utf-8"))
            return data if isinstance(data, dict) else None
        except Exception:
            return None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None


def _write_trial_record(
    device_id: str,
    started: datetime,
    expires: datetime,
    token: Optional[str] = None,
    email: Optional[str] = None,
) -> None:
    """Persist the local trial record (schema v2 adds optional server fields)."""
    trial_data: Dict[str, Any] = {
        "v": 2,
        "device_id": device_id,
        "started": started.isoformat(),
        "expires": expires.isoformat(),
    }
    if token is not None:
        trial_data["token"] = token
    if email is not None:
        trial_data["email"] = email
    TRIAL_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRIAL_FILE, "w", encoding="utf-8") as f:
        json.dump(trial_data, f, indent=2)


def start_trial(email: Optional[str] = None) -> Dict[str, Any]:
    """
    Start a 5-day trial of Pro features.

    Args:
        email: Optional. When given, the trial is registered with the license
            server (per-email deduplication + follow-up) and the local record
            carries the returned token. Omitted, the trial is purely local and
            behaves exactly as before — no network call is made. If the server
            cannot be reached, an ``--email`` request falls back to a local
            trial so offline evaluators are never blocked.

    Returns:
        dict: keys ``success`` (bool), ``message`` (str), ``expires`` (str),
            ``days_remaining`` (int), and — for the email path — ``registered``
            (bool: reached the server) and optionally ``note``.

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

    device_id = get_device_id()

    # Server-registered path (opt-in). Deduplication lives on the server; a
    # network failure degrades gracefully to a local trial.
    if email is not None:
        online = _request_online_trial(email, device_id)
        if online is not None and online.get("status") in ("issued", "already_issued"):
            if not online.get("active", True):
                # Server: this email already spent its trial.
                return {
                    "success": False,
                    "message": online.get(
                        "message",
                        "This email has already used its trial. "
                        "Purchase a license to continue using Pro features.",
                    ),
                    "expires": online.get("expires", ""),
                    "days_remaining": 0,
                    "registered": True,
                }
            started_dt = _parse_server_iso(online["started"])
            expires_dt = _parse_server_iso(online["expires"])
            _write_trial_record(
                device_id,
                started_dt,
                expires_dt,
                token=online.get("token"),
                email=email,
            )
            remaining = max(0, (expires_dt - datetime.now()).days)
            return {
                "success": True,
                "message": "Trial started and registered! You can now use Pro features.",
                "expires": expires_dt.strftime("%Y-%m-%d %H:%M"),
                "days_remaining": remaining,
                "registered": True,
            }
        # Unreachable / unexpected response: fall through to a local trial.

    # Local trial (no email, or the server could not be reached).
    start_time = datetime.now()
    expires = start_time + TRIAL_DURATION
    _write_trial_record(device_id, start_time, expires)

    result: Dict[str, Any] = {
        "success": True,
        "message": "Trial started successfully! You can now use Pro features.",
        "expires": expires.strftime("%Y-%m-%d %H:%M"),
        "days_remaining": TRIAL_DURATION.days,
    }
    if email is not None:
        result["registered"] = False
        result["note"] = "Could not reach the trial server; started a local trial instead."
    return result


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
