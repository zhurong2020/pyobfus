"""
License Verification System for pyobfus Professional Edition.

This module implements GitHub-based license verification with local caching.
Design specification: docs/internal/LICENSE_VERIFICATION_SPEC.md

License: Proprietary - Commercial Use Only
Copyright 2025 Rong Zhu
"""

import json
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, cast
import urllib.request
import urllib.error

from .fingerprint import get_device_fingerprint

# Cloudflare Worker API for license verification
LICENSE_API_BASE = "https://pyobfus-license-server.zhurong0525.workers.dev"
LICENSE_API_URL = f"{LICENSE_API_BASE}/api/verify"
DEACTIVATE_API_URL = f"{LICENSE_API_BASE}/api/deactivate"

# Legacy: GitHub repository for license data (deprecated, kept for reference)
LICENSE_REPO_URL = "https://raw.githubusercontent.com/zhurong2020/pyobfus-licenses/main"

# Local cache configuration
CACHE_DIR = Path.home() / ".pyobfus"
CACHE_FILE = CACHE_DIR / "license.json"
CACHE_DURATION = timedelta(days=3)  # Reduced from 30 days to 3 days in v0.1.4

# Timeout for network requests
REQUEST_TIMEOUT = 5  # seconds


def _package_version() -> str:
    """Best-effort package version, never raising during import."""
    try:
        from importlib.metadata import version

        return version("pyobfus")
    except Exception:  # pragma: no cover - metadata missing or unreadable
        return "unknown"


# Identify ourselves on every outbound request. urllib's default
# "Python-urllib/X.Y" User-Agent is blocked at the Cloudflare edge with
# HTTP 403 "error code: 1010" (browser integrity check / banned signature),
# so the request never reaches the Worker and every verification fails with
# an opaque "Access denied". Confirmed 2026-09-12: identical requests differing
# only in User-Agent get 403 (Python-urllib) vs the Worker's own JSON response
# (anything else, including no User-Agent at all).
USER_AGENT = f"pyobfus-license/{_package_version()} (+https://github.com/zhurong2020/pyobfus)"

# License secret for HMAC signing
LICENSE_SECRET = os.getenv(
    "PYOBFUS_LICENSE_SECRET",
    "pyobfus-v0.1.4-default-secret-change-in-production",
)


class LicenseError(Exception):
    """Base exception for license-related errors."""

    pass


class LicenseVerificationError(LicenseError):
    """Raised when license verification fails."""

    pass


class LicenseServerUnreachableError(LicenseVerificationError):
    """Raised when no definitive answer could be obtained from the server.

    This is deliberately distinct from an answer the server actually gave.
    A network failure, an edge that blocks the request before it arrives, or
    an unparseable response all mean "we do not know", not "this licence is
    bad". A paying customer must not be blocked because of our own
    infrastructure, so callers treat this as a warning rather than a refusal.
    """

    pass


class LicenseExpiredError(LicenseError):
    """Raised when license has expired."""

    pass


class LicenseRevokedError(LicenseError):
    """Raised when license has been revoked."""

    pass


def verify_license(license_key: str) -> Dict[str, Any]:
    """
    Verify license key against GitHub repository.

    This function:
    1. Checks local cache first (valid for 30 days)
    2. If cache miss or expired, verifies online against GitHub
    3. Falls back to cached license if online verification fails

    Args:
        license_key: License key in format PYOB-XXXX-XXXX-XXXX-XXXX

    Returns:
        dict: {
            "valid": bool,
            "type": str,  # "professional", "enterprise", etc.
            "expires": str,  # ISO format date
            "message": str
        }

    Raises:
        LicenseVerificationError: If license is invalid
        LicenseExpiredError: If license has expired
        LicenseRevokedError: If license has been revoked
    """
    # Validate license key format
    if not _validate_license_format(license_key):
        raise LicenseVerificationError(
            "Invalid license key format. Expected: PYOB-XXXX-XXXX-XXXX-XXXX"
        )

    # Check cache first
    cached = load_cached_license()
    if cached and cached.get("key") == license_key:
        cache_time = datetime.fromisoformat(cached["verified"])
        cache_age = datetime.now() - cache_time

        if cache_age < CACHE_DURATION:
            # Cache is still valid
            return {
                "valid": True,
                "type": cached["type"],
                "expires": cached["expires"],
                "message": f"License valid (cached, verified {cache_age.days} days ago)",
            }

    # Verify online
    try:
        license_data = _verify_online(license_key)

        # Check license status
        if license_data["status"] == "active":
            # Check expiration
            expires_date = datetime.fromisoformat(license_data["expires"])
            if datetime.now() > expires_date:
                raise LicenseExpiredError(f"License expired on {license_data['expires']}")

            # Cache the result
            cache_license(
                {
                    "key": license_key,
                    "type": license_data["type"],
                    "expires": license_data["expires"],
                    "verified": datetime.now().isoformat(),
                }
            )

            return {
                "valid": True,
                "type": license_data["type"],
                "expires": license_data["expires"],
                "message": "License verified successfully",
            }

        elif license_data["status"] == "revoked":
            raise LicenseRevokedError("License has been revoked")
        else:
            raise LicenseVerificationError(f"License status: {license_data['status']}")

    except (LicenseExpiredError, LicenseRevokedError):
        # Re-raise specific license errors
        raise

    except Exception as e:
        # Network error or other failure - use cached license if available
        if cached and cached.get("key") == license_key:
            # Check if cached license is expired
            expires_date = datetime.fromisoformat(cached["expires"])
            if datetime.now() > expires_date:
                raise LicenseExpiredError(
                    f"License expired on {cached['expires']} (offline verification)"
                )

            return {
                "valid": True,
                "type": cached["type"],
                "expires": cached["expires"],
                "message": f"License valid (cached, verification failed: {str(e)[:50]})",
            }

        # No cached license and verification failed. Keep the distinction
        # between "the server rejected this licence" and "we never got an
        # answer": the caller decides very differently on each.
        failure = (
            LicenseServerUnreachableError
            if isinstance(e, LicenseServerUnreachableError)
            else LicenseVerificationError
        )
        raise failure(f"License verification failed and no valid cache available: {str(e)}")


def _definitive_failure(code: Optional[str], message: Optional[str]) -> LicenseError:
    """Map an answer the server actually gave onto the right exception.

    Revocation is the one control that must survive a cached licence, so it has
    to arrive as ``LicenseRevokedError``: ``verify_license`` re-raises that
    without consulting the cache, while anything else falls back to the cache
    and keeps the customer working. Before this mapping existed the server
    could answer "License is revoked" and the client would carry on, reporting
    the licence as valid, because the rejection arrived as a generic error and
    was swallowed by that same fallback.

    ``code`` is the stable machine-readable field. The text fallback is not
    decoration: a newly released client reaches whatever Worker is deployed at
    the time, which may predate the field.
    """
    text = (message or "").lower()
    if code == "revoked" or (not code and "revoked" in text):
        return LicenseRevokedError(message or "License has been revoked")
    if code == "expired" or (not code and "expired" in text):
        return LicenseExpiredError(message or "License has expired")
    return LicenseVerificationError(message or "License verification failed")


def _verify_online(license_key: str) -> Dict[str, Any]:
    """
    Verify license key against Cloudflare Worker API.

    Args:
        license_key: License key to verify

    Returns:
        dict: License data from API

    Raises:
        LicenseVerificationError: If license not found or network error
    """
    device_id = get_device_fingerprint()

    # Prepare request data
    request_data = json.dumps({"license_key": license_key, "device_id": device_id}).encode("utf-8")

    # Create request
    req = urllib.request.Request(
        LICENSE_API_URL,
        data=request_data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read())

        # Check if verification was successful
        if data.get("valid"):
            # Calculate expiration: lifetime licenses expire in 100 years
            expires_at = data.get("expires_at")
            if expires_at is None:
                # Lifetime license - set far future date
                expires_at = (datetime.now() + timedelta(days=36500)).isoformat()

            return {
                "key": license_key,
                "status": "active",  # Worker only returns valid licenses
                "type": "pro",
                "expires": expires_at,
                "email": data.get("email", ""),
                "created_at": data.get("created_at", ""),
                "features": data.get("features", {}),
            }
        else:
            raise _definitive_failure(data.get("code"), data.get("error"))

    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise LicenseVerificationError("License key not found")
        elif e.code == 403:
            # A 403 from the license server itself always carries a JSON
            # "error" field naming the reason (revoked, expired, device limit).
            # A 403 with any other body did not come from the server: something
            # between the client and the Worker rejected the request, and the
            # license itself may be perfectly valid. Say so, and point at the
            # offline path, instead of reporting a bare "Access denied".
            server_code = None
            server_msg = None
            try:
                error_data = json.loads(e.read())
                server_code = error_data.get("code")
                server_msg = error_data.get("error")
            except (json.JSONDecodeError, ValueError, IOError):
                pass
            if server_msg:
                raise _definitive_failure(server_code, server_msg)
            raise LicenseServerUnreachableError(
                "blocked by the network before reaching the license server "
                "(HTTP 403, non-server response body). Your license may still be "
                "valid. Try another network, or register offline with: "
                f"pyobfus-license register {license_key} --no-verify"
            )
        raise LicenseServerUnreachableError(f"HTTP error: {e.code}")
    except urllib.error.URLError as e:
        raise LicenseServerUnreachableError(f"Network error: {e.reason}")
    except json.JSONDecodeError:
        raise LicenseServerUnreachableError("Invalid response from license server")


def deactivate_device(license_key: str) -> Dict[str, Any]:
    """Release this machine's slot on the licence server.

    A licence allows a limited number of devices and nothing used to remove
    one, so retiring a machine meant emailing the maintainer, who then had to
    edit production data by hand. This makes it the customer's own one-line
    operation.

    Returns:
        dict: {"released": bool, "devices_registered": int, "device_id": str}

    Raises:
        LicenseVerificationError: the key is malformed, or the server does not
            know it.
        LicenseServerUnreachableError: no answer was obtained. The caller must
            not clear anything locally in that case: the slot is still taken,
            so discarding the local licence too would leave the customer
            strictly worse off.
    """
    if not _validate_license_format(license_key):
        raise LicenseVerificationError(
            "Invalid license key format. Expected: PYOB-XXXX-XXXX-XXXX-XXXX"
        )

    device_id = get_device_fingerprint()
    request_data = json.dumps({"license_key": license_key, "device_id": device_id}).encode("utf-8")
    req = urllib.request.Request(
        DEACTIVATE_API_URL,
        data=request_data,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            # Two very different things arrive as 404 here: the server saying
            # it has no such licence (JSON), and a server old enough not to
            # have this route at all (plain text). Reporting the second as
            # "License key not found" would send the customer hunting for a
            # problem with their licence that does not exist.
            try:
                code = json.loads(e.read()).get("code")
            except (json.JSONDecodeError, ValueError, IOError):
                code = None
            if code == "invalid_key":
                raise LicenseVerificationError("License key not found")
            raise LicenseServerUnreachableError(
                "this license server does not support releasing a device yet"
            )
        raise LicenseServerUnreachableError(f"HTTP error: {e.code}")
    except urllib.error.URLError as e:
        raise LicenseServerUnreachableError(f"Network error: {e.reason}")
    except json.JSONDecodeError:
        raise LicenseServerUnreachableError("Invalid response from license server")

    return {
        "released": bool(data.get("released")),
        "devices_registered": data.get("devices_registered"),
        "devices_allowed": data.get("devices_allowed"),
        "device_id": device_id,
    }


def _validate_license_format(license_key: str) -> bool:
    """
    Validate license key format: PYOB-XXXX-XXXX-XXXX-XXXX

    Args:
        license_key: License key to validate

    Returns:
        bool: True if format is valid
    """
    if not license_key:
        return False

    parts = license_key.split("-")
    if len(parts) != 5:
        return False

    if parts[0] != "PYOB":
        return False

    # Check that remaining parts are 4-character hex strings
    for part in parts[1:]:
        if len(part) != 4:
            return False
        try:
            int(part, 16)  # Validate hex format
        except ValueError:
            return False

    return True


def load_cached_license() -> Optional[Dict[str, Any]]:
    """
    Load and verify cached license from disk.

    Returns:
        dict: Cached license data or None if invalid/not found

    Verification checks:
    1. File exists and is readable
    2. Schema version is supported (v1 or v2)
    3. HMAC signature is valid (v2 only)
    4. Device fingerprint matches (v2 only)
    """
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)

        # Check schema version
        version = cached.get("v", 1)

        if version == 1:
            # Legacy cache (v0.1.2-0.1.3) - no signature
            # Accept but mark for upgrade
            return cast(Dict[str, Any], cached)

        elif version == 2:
            # Current cache (v0.1.4+) - has signature and device_id

            # Verify signature
            data_str = json.dumps(cached["data"], sort_keys=True)
            expected_sig = hmac.new(
                LICENSE_SECRET.encode(), data_str.encode(), hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(cached["sig"], expected_sig):
                # Signature mismatch - cache tampered
                CACHE_FILE.unlink()  # Delete corrupted cache
                return None

            # The device fingerprint is recorded, but a mismatch is NOT
            # fatal. It used to be, and that reliably locked out paying
            # customers: the fingerprint changes when the machine's identity
            # merely drifts (an OS point update alone is enough), at which
            # point the cache vanished, the CLI announced "No license key
            # found", and re-registering burned another of three device slots
            # that nothing can free. A customer reported exactly this in
            # 2026-06 ("it keeps thinking I'm different devices").
            #
            # Dropping the check costs no protection it was actually
            # providing. The HMAC signature above is what resists tampering,
            # and it still runs. The device check was standing in as an
            # anti-copy measure, which the documented offline path
            # (`pyobfus-license register KEY --no-verify`) already nullifies:
            # anyone willing to copy this file can simply register instead.
            data = cast(Dict[str, Any], cached["data"])
            data["device_changed"] = data.get("device_id") != get_device_fingerprint()
            return data

        else:
            # Unknown version - ignore
            return None

    except (json.JSONDecodeError, KeyError, IOError):
        # Corrupted cache file
        return None


def cache_license(license_data: Dict[str, str]) -> None:
    """
    Cache license data to disk with HMAC signature.

    Args:
        license_data: License data to cache (must include 'key', 'type', 'expires')

    The cache format is:
    {
        "v": 2,  # Schema version (v2 includes signature and device_id)
        "data": {
            "key": "PYOB-...",
            "type": "pro",
            "expires": "2026-01-01",
            "verified": "2025-11-11T10:00:00",
            "device_id": "a1b2c3d4e5f6g7h8"
        },
        "sig": "abc123...",  # HMAC-SHA256 signature
        "ts": "2025-11-11T10:00:00"  # Timestamp when cached
    }
    """
    # Add device_id to license data
    device_id = get_device_fingerprint()
    license_data_with_device = {**license_data, "device_id": device_id}

    # Create signature
    data_str = json.dumps(license_data_with_device, sort_keys=True)
    signature = hmac.new(LICENSE_SECRET.encode(), data_str.encode(), hashlib.sha256).hexdigest()

    # Create cache structure
    cached = {
        "v": 2,  # Schema version
        "data": license_data_with_device,
        "sig": signature,
        "ts": datetime.now().isoformat(),
    }

    # Write to disk
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cached, f, indent=2)


def remove_cached_license() -> bool:
    """
    Remove cached license file.

    Returns:
        bool: True if cache was removed, False if no cache existed
    """
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        return True
    return False


def get_license_status(masked: bool = True) -> Optional[Dict[str, Any]]:
    """
    Get status of currently cached license without verification.

    Args:
        masked: If True, mask the license key for display. If False, return full key.

    Returns:
        dict: License status info or None if no license cached
    """
    cached = load_cached_license()
    if not cached:
        return None

    cache_time = datetime.fromisoformat(cached["verified"])
    cache_age = datetime.now() - cache_time
    expires_date = datetime.fromisoformat(cached["expires"])
    is_expired = datetime.now() > expires_date

    # Return full or masked key based on parameter
    license_key = cached["key"]
    if masked:
        license_key = license_key[:15] + "..." + license_key[-4:]

    result = {
        "key": license_key,
        "type": cached["type"],
        "expires": cached["expires"],
        "expired": is_expired,
        "verified_ago_days": cache_age.days,
        "cache_valid": cache_age < CACHE_DURATION,
    }

    # Add device_id if present (v2 cache)
    if "device_id" in cached:
        result["device_id"] = cached["device_id"]

    return result


def generate_license_key() -> str:
    """
    Generate a unique license key.

    This is a utility function for license administrators.

    Returns:
        str: License key in format PYOB-XXXX-XXXX-XXXX-XXXX
    """
    # Generate random bytes
    random_bytes = secrets.token_bytes(16)

    # Create hash
    hash_obj = hashlib.sha256(random_bytes)
    hash_hex = hash_obj.hexdigest()

    # Format as PYOB-XXXX-XXXX-XXXX-XXXX
    parts = [
        hash_hex[0:4].upper(),
        hash_hex[4:8].upper(),
        hash_hex[8:12].upper(),
        hash_hex[12:16].upper(),
    ]

    return f"PYOB-{'-'.join(parts)}"


__all__ = [
    "verify_license",
    "load_cached_license",
    "cache_license",
    "remove_cached_license",
    "get_license_status",
    "generate_license_key",
    "LicenseError",
    "LicenseVerificationError",
    "LicenseExpiredError",
    "LicenseRevokedError",
]
