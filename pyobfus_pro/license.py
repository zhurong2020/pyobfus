"""
License Verification System for pyobfus Professional Edition.

This module implements GitHub-based license verification with local caching.
Design specification: docs/internal/LICENSE_VERIFICATION_SPEC.md

License: Proprietary - Commercial Use Only
Copyright 2025 Rong Zhu
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, cast
import urllib.request
import urllib.error


# GitHub repository for license data
LICENSE_REPO_URL = "https://raw.githubusercontent.com/zhurong2020/pyobfus-licenses/main"

# Local cache configuration
CACHE_DIR = Path.home() / ".pyobfus"
CACHE_FILE = CACHE_DIR / "license.json"
CACHE_DURATION = timedelta(days=30)

# Timeout for network requests
REQUEST_TIMEOUT = 5  # seconds


class LicenseError(Exception):
    """Base exception for license-related errors."""

    pass


class LicenseVerificationError(LicenseError):
    """Raised when license verification fails."""

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
            f"Invalid license key format. Expected: PYOB-XXXX-XXXX-XXXX-XXXX"
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
                raise LicenseExpiredError(
                    f"License expired on {license_data['expires']}"
                )

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
            raise LicenseVerificationError(
                f"License status: {license_data['status']}"
            )

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

        # No cached license and verification failed
        raise LicenseVerificationError(
            f"License verification failed and no valid cache available: {str(e)}"
        )


def _verify_online(license_key: str) -> Dict[str, Any]:
    """
    Verify license key against GitHub repository.

    Args:
        license_key: License key to verify

    Returns:
        dict: License data from repository

    Raises:
        LicenseVerificationError: If license not found or network error
    """
    # Determine which file to check based on current date
    # We'll check the current month's file
    now = datetime.now()

    # Try current year/month first
    for year_offset in [0, -1]:  # Try current year, then previous year
        year = now.year + year_offset
        month = now.month if year_offset == 0 else 12

        url = f"{LICENSE_REPO_URL}/licenses/{year}/{month:02d}.json"

        try:
            with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read())

            # Find license key in this file
            for license in data.get("licenses", []):
                if license["key"] == license_key:
                    return cast(Dict[str, Any], license)

        except urllib.error.HTTPError as e:
            if e.code == 404:
                # File not found, try previous month/year
                continue
            raise LicenseVerificationError(f"HTTP error: {e.code}")
        except urllib.error.URLError as e:
            raise LicenseVerificationError(f"Network error: {e.reason}")
        except json.JSONDecodeError:
            raise LicenseVerificationError("Invalid license data format")

    # License not found in any file
    raise LicenseVerificationError("License key not found in repository")


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
    Load cached license from disk.

    Returns:
        dict: Cached license data or None if no cache exists
    """
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return cast(Optional[Dict[str, Any]], json.load(f))
        except (json.JSONDecodeError, IOError):
            # Corrupted cache file
            return None
    return None


def cache_license(license_data: Dict[str, str]) -> None:
    """
    Cache license data to disk.

    Args:
        license_data: License data to cache
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(license_data, f, indent=2)


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

    return {
        "key": license_key,
        "type": cached["type"],
        "expires": cached["expires"],
        "expired": is_expired,
        "verified_ago_days": cache_age.days,
        "cache_valid": cache_age < CACHE_DURATION,
    }


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
