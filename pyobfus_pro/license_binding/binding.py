"""License binding combo runtime: device / expire / period.

Three primitives, intentionally orthogonal so they can be used standalone
or composed.

**Device binding** — :func:`current_machine_id` + :func:`bind_device_key`:
A stable per-machine identifier (DMI ``/etc/machine-id`` on Linux,
``IOPlatformUUID`` on macOS, ``MachineGuid`` registry value on Windows,
deterministic fallback to ``sha256(hostname || username)`` everywhere)
fed through PBKDF2-HMAC-SHA256 with a build-time random salt yields a
32-byte AES-256 key. The build orchestrator emits this derivation as a
runtime statement that *replaces* the baked ``_LAYER_KEY = b"..."``
constant in P2-1 / ``_VAULT_KEY_<name>`` in P2-11. **Wrong device →
wrong derived key → GCM tag mismatch → decrypt fails → license gate
enforced inside the existing decryption path with no per-call check**.

**Calendar expiry** — :func:`expire_check`: reads an ISO-format date,
compares to ``date.today()``, raises :class:`LicenseExpired` if past.
Build orchestrator emits ``expire_check("2027-01-01")`` at module top.

**Run-counter expiry** — :func:`period_check`: atomic-rename file
counter incremented on each call; raises :class:`LicenseExpired` when
the counter exceeds ``max_runs``. The counter file lives at a path the
build orchestrator chooses (typically under ``~/.cache/pyobfus/<artifact-id>/runs``
or similar); its existence + contents are the user-visible runtime state.

The combination claim shape (P2-8 main inventive step): the layer key
is derived at runtime via :func:`bind_device_key` AND the calendar /
counter checks happen at module import. **The license check is
distributed across the cryptographic decryption path AND the explicit
guard calls** — neither single mechanism is the license; the combination
is. An attacker patching out one mechanism still hits the other
(plaintext code patches the calendar check away; cipher-cracking can't
patch out the device-key derivation without also having the device).

Patent-gated. See PATENT_NOTES.md and docs/P2-8_DESIGN.md.
"""

from __future__ import annotations

import datetime as _datetime
import hashlib
import os
import platform
import shutil
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_PBKDF2_DEFAULT_ITERATIONS = 200_000  # OWASP 2024 recommendation lower bound
_MIN_ITERATIONS = 100_000  # absolute floor
_MIN_SALT_BYTES = 16  # NIST SP 800-132 recommends 128-bit salts for password-derived keys
_DERIVED_KEY_SIZE = 32  # AES-256


class LicenseBindingError(RuntimeError):
    """Raised on invalid license-binding inputs (bad salt, bad iterations, etc.).

    Distinct from :class:`LicenseExpired` so callers can distinguish "the
    license check infrastructure is broken" from "the license has expired".
    """


class LicenseExpired(RuntimeError):
    """Raised when a calendar / counter / device check determines the license
    has expired or does not apply to the current environment.

    Caught by the build orchestrator's emitted module-top guard call to
    abort module import cleanly. Surfaces in the application's normal
    exception path so customers see a meaningful error rather than a
    cryptic decryption failure.
    """


# ---------------------------------------------------------------------------
# Device binding
# ---------------------------------------------------------------------------


def current_machine_id() -> str:
    """Return a stable per-machine identifier as a UTF-8 string.

    Source priority:

    1. **Linux / FreeBSD**: ``/etc/machine-id`` (systemd) or
       ``/var/lib/dbus/machine-id`` (older systems). 32-character hex.
    2. **macOS**: ``ioreg`` query for ``IOPlatformUUID``. UUID format.
    3. **Windows**: ``MachineGuid`` value under
       ``HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography``.
    4. **Fallback** (any platform; container-portable):
       ``sha256("pyobfus-machine-id-fallback-v1" || hostname || ":" || username).hexdigest()``.
       Stable per-(host,user) but derivable, so weaker against attackers
       who can spoof those values. Documented as a fallback and not the
       preferred path.

    Returns:
        A UTF-8 string. Length / format depends on the source path; opaque
        to callers (only fed back into :func:`bind_device_key`).

    Notes:
        Caching is NOT applied — each call re-reads the source. This is
        deliberate: machine_id is a read-once-per-process value the
        orchestrator-emitted code captures into the AESGCM cipher object
        at module import, so per-call cost doesn't matter and we'd rather
        not hold OS-specific cached state across forks.
    """
    system = platform.system()

    if system in ("Linux", "FreeBSD"):
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                content = Path(path).read_text(encoding="ascii").strip()
            except (OSError, UnicodeDecodeError):
                continue
            if content:
                return content

    elif system == "Darwin":
        ioreg = shutil.which("ioreg")
        if ioreg:
            try:
                import subprocess  # noqa: S404 -- ioreg is a system tool

                # S603: argv is fully-controlled list of constants + the
                # absolute path to ioreg from `shutil.which`; no shell, no
                # untrusted input. ioreg is a macOS system binary.
                result = subprocess.run(  # noqa: S603
                    [ioreg, "-rd1", "-c", "IOPlatformExpertDevice"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    check=False,
                )
                for line in result.stdout.splitlines():
                    if "IOPlatformUUID" in line:
                        # Format: '    "IOPlatformUUID" = "11111111-..."'
                        parts = line.split('"')
                        if len(parts) >= 4:
                            return parts[-2]
            except (OSError, subprocess.SubprocessError):
                pass

    elif system == "Windows":
        try:
            import winreg  # type: ignore[import-not-found,unused-ignore]

            with winreg.OpenKey(  # type: ignore[attr-defined]
                winreg.HKEY_LOCAL_MACHINE,  # type: ignore[attr-defined]
                r"SOFTWARE\Microsoft\Cryptography",
            ) as k:
                value, _ = winreg.QueryValueEx(k, "MachineGuid")  # type: ignore[attr-defined]
                if value:
                    return str(value)
        except (OSError, ImportError):
            pass

    # Fallback path: deterministic but weak. UTF-8 string suitable for
    # PBKDF2 input; documented limitation.
    hostname = platform.node() or "unknown-host"
    username = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown-user"
    h = hashlib.sha256()
    h.update(b"pyobfus-machine-id-fallback-v1")
    h.update(b"\x00")
    h.update(hostname.encode("utf-8"))
    h.update(b":")
    h.update(username.encode("utf-8"))
    return h.hexdigest()


def bind_device_key(
    machine_id: str,
    build_salt: bytes,
    *,
    iterations: int = _PBKDF2_DEFAULT_ITERATIONS,
) -> bytes:
    """Derive a 32-byte AES-256 key from a machine ID + build-time salt.

    PBKDF2-HMAC-SHA256 over UTF-8 ``machine_id`` with the supplied
    ``build_salt`` and ``iterations``. The build orchestrator generates
    a fresh random ``build_salt`` per build (32 bytes minimum
    recommended), embeds it as a module-level constant in the emitted
    artifact, and emits a runtime call to this function whose result
    replaces the baked ``_LAYER_KEY`` / ``_VAULT_KEY_<name>`` constants.

    Args:
        machine_id: Output of :func:`current_machine_id` (or any stable
            UTF-8 string identifying the target device).
        build_salt: At least :data:`_MIN_SALT_BYTES` (16) bytes of random
            data generated at build time. Persisted in the artifact.
            Different artifacts must use different salts.
        iterations: PBKDF2 iteration count. Default
            :data:`_PBKDF2_DEFAULT_ITERATIONS` (200,000) per OWASP 2024.
            Minimum :data:`_MIN_ITERATIONS` (100,000); raise as hardware
            speeds increase.

    Returns:
        32-byte AES-256 key.

    Raises:
        LicenseBindingError: on invalid machine_id type, salt too short,
            or iterations below the floor.

    **Patent-relevant**: the derived key is byte-identical iff the device
    matches AND the salt matches. An attacker on the wrong device
    derives a different key and AES-GCM tag verification fails on every
    L3 cipher and Vault entry — the license check is the *AES-GCM tag
    check itself*. No separate license-check call to patch out.
    """
    if not isinstance(machine_id, str):
        raise LicenseBindingError(f"machine_id must be a string, got {type(machine_id).__name__}")
    if not machine_id:
        raise LicenseBindingError("machine_id must be non-empty")
    if not isinstance(build_salt, (bytes, bytearray)) or len(build_salt) < _MIN_SALT_BYTES:
        raise LicenseBindingError(
            f"build_salt must be at least {_MIN_SALT_BYTES} bytes, got "
            f"{len(build_salt) if isinstance(build_salt, (bytes, bytearray)) else type(build_salt).__name__}"
        )
    if not isinstance(iterations, int) or iterations < _MIN_ITERATIONS:
        raise LicenseBindingError(
            f"iterations must be int >= {_MIN_ITERATIONS}, got {iterations!r}"
        )

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=_DERIVED_KEY_SIZE,
        salt=bytes(build_salt),
        iterations=iterations,
    )
    return kdf.derive(machine_id.encode("utf-8"))


# ---------------------------------------------------------------------------
# Calendar expiry
# ---------------------------------------------------------------------------


def expire_check(expire_iso: str, *, now: _datetime.date | None = None) -> None:
    """Raise :class:`LicenseExpired` if the current date is past ``expire_iso``.

    Args:
        expire_iso: ISO-8601 calendar date string (``"YYYY-MM-DD"``).
            Parsed via :meth:`datetime.date.fromisoformat`.
        now: Override for the "current date" — testing aid; production
            calls leave this ``None`` and use :meth:`datetime.date.today`.

    The check is *date-only* (not datetime); a user on UTC+8 and a user
    on UTC-8 see the same expiry behavior on the boundary day. For
    sub-day precision a future API addition would take a datetime + tz.

    **Pattern**: build orchestrator emits ``expire_check("2027-01-01")``
    at module top. If expired, module import fails with
    :class:`LicenseExpired` rather than producing a partially-loaded
    module that crashes mysteriously elsewhere.

    Raises:
        LicenseBindingError: on malformed ``expire_iso``.
        LicenseExpired: when ``now > expire_date``.
    """
    try:
        expire_date = _datetime.date.fromisoformat(expire_iso)
    except ValueError as exc:
        raise LicenseBindingError(
            f"expire_iso must be ISO-8601 calendar date 'YYYY-MM-DD'; got {expire_iso!r}: {exc}"
        ) from exc

    today = now if now is not None else _datetime.date.today()
    if not isinstance(today, _datetime.date):
        raise LicenseBindingError(f"now must be a datetime.date, got {type(today).__name__}")

    if today > expire_date:
        raise LicenseExpired(
            f"license expired on {expire_date.isoformat()}; today is {today.isoformat()}"
        )


# ---------------------------------------------------------------------------
# Run-counter expiry
# ---------------------------------------------------------------------------


def period_check(
    counter_path: str | os.PathLike,
    max_runs: int,
    *,
    advance: bool = True,
) -> int:
    """Atomic file counter; raise :class:`LicenseExpired` when ``> max_runs``.

    Reads the existing run count from ``counter_path`` (creates with 0 if
    absent), and if ``advance`` is True (default), atomically increments
    + persists the new value via tempfile + rename. Returns the
    *post-increment* counter value (or, when ``advance=False``, the
    current value).

    The atomic rename pattern survives crashes mid-update: either the
    old value is intact or the new value is fully written. There is no
    partial-write window where the counter could be corrupted.

    Args:
        counter_path: Filesystem path to the counter file. Build
            orchestrator chooses (typically under
            ``~/.cache/pyobfus/<artifact-id>/runs``).
        max_runs: Inclusive upper bound. ``period_check(p, 100)`` allows
            run #1 through #100 and raises on the 101st.
        advance: When True (default), increment + persist. When False,
            read-only check (useful for diagnostics or testing without
            consuming a run).

    Returns:
        Post-increment counter value (or current value when ``advance=False``).

    Raises:
        LicenseBindingError: on invalid ``max_runs`` or unreadable /
            unwritable ``counter_path`` parent dir, or on corrupted
            counter file (non-integer content).
        LicenseExpired: when post-(read or increment) counter > max_runs.

    **Threat model**: the counter file is on a filesystem the user owns;
    they can manually reset it to 0 at any time. That's a *known
    limitation* of the period-check axis used standalone. The
    *combination* with ``--bind-device`` makes counter reset useless on a
    different machine (the AES key is wrong); the combination with
    ``--expire`` makes counter reset useless past the expire date. The
    patent claim is the *combination*, not period-check in isolation.
    """
    if not isinstance(max_runs, int) or max_runs < 1:
        raise LicenseBindingError(f"max_runs must be int >= 1, got {max_runs!r}")
    counter_path = Path(counter_path)

    try:
        counter_path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise LicenseBindingError(
            f"unable to create counter directory {counter_path.parent}: {exc}"
        ) from exc

    current = 0
    if counter_path.exists():
        try:
            text = counter_path.read_text(encoding="ascii").strip()
        except OSError as exc:
            raise LicenseBindingError(f"unable to read counter file {counter_path}: {exc}") from exc
        if text:
            try:
                current = int(text)
            except ValueError as exc:
                raise LicenseBindingError(
                    f"counter file {counter_path} is corrupted (not an int): {text!r}"
                ) from exc
            if current < 0:
                raise LicenseBindingError(
                    f"counter file {counter_path} contains negative value: {current}"
                )

    new_value = current + 1 if advance else current

    if advance:
        # Atomic write via tempfile + rename. NamedTemporaryFile is in the
        # same directory so rename is guaranteed atomic on POSIX (same
        # filesystem). delete=False because we move it explicitly; we
        # also clean up on failure.
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(counter_path.parent), prefix=".counter.", suffix=".tmp"
        )
        try:
            with os.fdopen(tmp_fd, "w", encoding="ascii") as f:
                f.write(str(new_value))
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, counter_path)
        except OSError as exc:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise LicenseBindingError(
                f"unable to persist counter increment to {counter_path}: {exc}"
            ) from exc

    if new_value > max_runs:
        raise LicenseExpired(
            f"license run-counter exceeded: ran {new_value} times, max allowed is {max_runs}"
        )

    return new_value


_COUNTER_ENV_VAR = "PYOBFUS_COUNTER_DIR"


def default_counter_path(artifact_id: str) -> Path:
    """Resolve the run-counter file path for an artifact, at *runtime*.

    The build orchestrator emits ``period_check(default_counter_path("<id>"), N)``
    at module top so the counter path is resolved on the **end-user's** machine
    at import time, never baked in at build time (a build-time absolute path
    would point at the *builder's* home). Honors ``$PYOBFUS_COUNTER_DIR`` (for a
    read-only ``$HOME`` or to relocate runtime state); otherwise defaults to
    ``~/.cache/pyobfus/<artifact_id>/runs``.

    Args:
        artifact_id: Stable per-artifact identifier (the orchestrator uses a
            truncated sha256 of the module qualname). Sanitized to a single
            ``[A-Za-z0-9_]`` path segment before use, so a crafted value cannot
            traverse out of the counter root.

    Returns:
        The ``Path`` to the counter file (its parent is created lazily by
        :func:`period_check`).

    Raises:
        LicenseBindingError: if ``artifact_id`` is not a non-empty string.
    """
    if not isinstance(artifact_id, str) or not artifact_id:
        raise LicenseBindingError("artifact_id must be a non-empty string")
    # Reduce to a single safe path segment (alnum or underscore). This alone
    # neutralizes '..' and path separators — no traversal reaches the FS.
    safe = "".join(c if c.isalnum() else "_" for c in artifact_id)
    base = os.environ.get(_COUNTER_ENV_VAR)
    root = Path(base) if base else Path.home() / ".cache" / "pyobfus"
    return root / safe / "runs"


__all__ = [
    "LicenseBindingError",
    "LicenseExpired",
    "bind_device_key",
    "current_machine_id",
    "default_counter_path",
    "expire_check",
    "period_check",
]
