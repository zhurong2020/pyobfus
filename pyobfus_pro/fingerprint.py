"""
Device fingerprinting for license verification.

Generates unique device identifier based on hardware characteristics.
"""

import hashlib
import platform
import uuid


def get_device_fingerprint() -> str:
    """
    Generate unique device fingerprint.

    Uses:
    - MAC address (uuid.getnode())
    - Hostname (platform.node())
    - OS platform (platform.system() + platform.release())

    Returns:
        str: 16-character hex fingerprint

    Example:
        >>> fp = get_device_fingerprint()
        >>> len(fp)
        16
        >>> fp.isalnum()
        True
    """
    try:
        # Get MAC address
        mac = uuid.getnode()

        # Get hostname
        hostname = platform.node()

        # Get OS info
        os_info = f"{platform.system()}-{platform.release()}"

        # Combine into fingerprint
        fingerprint_str = f"{mac}-{hostname}-{os_info}"

        # Hash to fixed length
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]

    except Exception:
        # Fallback to random UUID if fingerprinting fails
        # (e.g., in sandboxed environments)
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]


def get_device_name() -> str:
    """
    Get human-readable device name.

    Returns:
        str: Device name (e.g., "MacBook-Pro.local")
    """
    try:
        return platform.node()
    except Exception:
        return "Unknown Device"


def get_device_info() -> dict:
    """
    Get detailed device information.

    Returns:
        dict: Device info including OS, architecture, etc.
    """
    return {
        "fingerprint": get_device_fingerprint(),
        "name": get_device_name(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }
