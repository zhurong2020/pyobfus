"""
Device fingerprinting for license verification.

Generates unique device identifier based on hardware characteristics.
"""

import hashlib
import platform
import secrets
import uuid
from pathlib import Path

# Where this machine's identity is kept. Created on first use.
DEVICE_ID_FILE = Path.home() / ".pyobfus" / "device_id"

_FINGERPRINT_LENGTH = 16


def _derive_from_hardware() -> str:
    """Last-resort identity for a machine that cannot keep a file.

    Deliberately excludes the OS release. Including it is what made the old
    fingerprint change under a routine update.
    """
    try:
        parts = f"{uuid.getnode()}-{platform.node()}-{platform.system()}"
    except Exception:  # pragma: no cover - platform lookups failing is rare
        parts = str(uuid.uuid4())
    return hashlib.sha256(parts.encode()).hexdigest()[:_FINGERPRINT_LENGTH]


def get_device_fingerprint() -> str:
    """
    Return this machine's stable identifier, creating it on first use.

    A licence allows a limited number of devices, so this value decides
    whether a customer can keep working. It used to be derived from the MAC
    address, the hostname and **the OS release**, which meant a routine
    operating-system update changed the machine's identity: the local licence
    cache stopped matching, the CLI reported no licence, and re-registering
    consumed another slot. A customer reported exactly that in June 2026.
    ``uuid.getnode()`` made it worse, since Python returns a *random* number
    when no hardware address can be read, and modern systems randomise MACs
    anyway.

    So identity is no longer guessed from hardware. A random value is
    generated once and kept in ``~/.pyobfus/device_id``, which survives OS
    upgrades, virtual environments and containers rebuilt from the same home.

    That file can of course be copied to another machine. So could the licence
    cache next to it, and `pyobfus-license register --no-verify` already
    registers a licence without contacting the server at all, so nothing here
    was resisting a determined copy. Pretending otherwise cost real customers
    their licences while stopping nobody. Device limits exist to keep one key
    from spreading across an organisation, and revocation handles abuse.

    Returns:
        str: 16-character hex identifier

    Example:
        >>> fp = get_device_fingerprint()
        >>> len(fp)
        16
        >>> fp.isalnum()
        True
    """
    try:
        existing = DEVICE_ID_FILE.read_text(encoding="utf-8").strip()
        if len(existing) == _FINGERPRINT_LENGTH and all(c in "0123456789abcdef" for c in existing):
            return existing
    except (OSError, ValueError):
        pass

    device_id = secrets.token_hex(_FINGERPRINT_LENGTH // 2)

    try:
        DEVICE_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        DEVICE_ID_FILE.write_text(device_id, encoding="utf-8")
        try:
            DEVICE_ID_FILE.chmod(0o600)
        except OSError:  # pragma: no cover - filesystems without POSIX modes
            pass
        return device_id
    except OSError:
        # Read-only or absent home directory. Falling back to a fresh random
        # value every run would register a new device on every single
        # verification, so derive something repeatable instead.
        return _derive_from_hardware()


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
