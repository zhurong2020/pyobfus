"""Build-time entitlement routing shared by CLI and library callers.

Importability is capability discovery, never authorization. Read-only inspection,
configuration generation, marker decorators and redistributable runtimes do not
need entitlement. No authorization state is carried into generated artifacts.
"""

import asyncio
import os
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator, Optional, Tuple

from pyobfus.exceptions import PyObfusError
from pyobfus.core.fusion_options import FUSION_FIELDS

# Include auxiliary fields as well as switches: YAML/API callers need the same
# decision even if level remains "community" or a parent flag was omitted.
PRO_CONFIG_FIELDS: Tuple[str, ...] = (
    "string_encryption",
    "import_obfuscation",
    "anti_debug",
    "control_flow_flattening",
    "dead_code_injection",
    "license_expire",
    "license_bind_machine",
    "license_max_runs",
    "crossfile_opacity",
    "bind_device_id",
    "expire_warn_days",
) + FUSION_FIELDS


class ProAccessError(PyObfusError, ValueError):
    """The requested build needs a license or an active trial."""


_GUIDANCE = (
    "Pro features require a license or active trial. "
    "Register with 'pyobfus-license register YOUR-LICENSE-KEY', "
    "check 'pyobfus-license status', or start a free 5-day trial "
    "with 'pyobfus-trial start'."
)


def _owner() -> Tuple[Any, ...]:
    try:
        task = asyncio.current_task()
    except RuntimeError:
        task = None
    return os.getpid(), threading.get_ident(), task


class _BuildSession:
    def __init__(self) -> None:
        self.owner = _owner()
        self.active = True
        self.approved = False

    def usable(self) -> bool:
        return self.active and self.owner == _owner()


_session: ContextVar[Optional[_BuildSession]] = ContextVar("pyobfus_build_session", default=None)


@contextmanager
def entitlement_session() -> Iterator[None]:
    """Reuse only a live session owned by this process, thread and task."""
    current = _session.get()
    if current is not None and current.usable():
        yield
        return
    session = _BuildSession()
    token = _session.set(session)
    try:
        yield
    finally:
        session.active = False
        session.approved = False
        _session.reset(token)


def _approve_session() -> None:
    session = _session.get()
    if session is not None and session.usable():
        session.approved = True


def _worker_capability() -> Optional[bytes]:
    """Mint a pool-only capability after the parent has authorized its build."""
    import secrets

    session = _session.get()
    if session is not None and session.usable() and session.approved:
        return secrets.token_bytes(32)
    return None


def require_pro_access() -> None:
    """Allow an active trial or the existing license verifier's valid result.

    Delegating to verify_license preserves its three-day cache, legacy/offline
    registration and fallback for an unreachable server. Revoked/expired
    licenses remain denied. Never echo verifier exceptions: they may contain
    the full license key or a server response with private information.
    """
    session = _session.get()
    if session is not None and session.usable() and session.approved:
        return

    from pyobfus.trial import is_trial_active

    try:
        from pyobfus_pro import license as licensing
    except ImportError:
        raise ProAccessError(
            "Pro components could not be imported. Reinstall pyobfus. " + _GUIDANCE
        ) from None

    ci_key = os.environ.get("PYOBFUS_LICENSE_KEY", "").strip()
    if ci_key:
        try:
            licensing.verify_ci_license(ci_key)
        except licensing.LicenseError as exc:
            # CI verifier emits only fixed diagnostics, never response/key text.
            raise ProAccessError(
                str(exc) + " Check PYOBFUS_LICENSE_KEY or use a registered runner."
            ) from None
        _approve_session()
        return

    if is_trial_active():
        _approve_session()
        return

    try:
        status = licensing.get_license_status(masked=False)
        if not status or not status.get("key"):
            raise ProAccessError("No license key found. " + _GUIDANCE)
        result = licensing.verify_license(status["key"])
        if result.get("valid") is not True:
            raise ProAccessError("License verification failed. " + _GUIDANCE)
        _approve_session()
    except licensing.LicenseRevokedError:
        raise ProAccessError("License has been revoked. " + _GUIDANCE) from None
    except licensing.LicenseExpiredError:
        raise ProAccessError("License has expired. " + _GUIDANCE) from None
    except licensing.LicenseError:
        raise ProAccessError("License verification failed. " + _GUIDANCE) from None


def require_config_access(config: Any) -> None:
    """Check the merged build configuration; Community never reads user state."""
    if getattr(config, "level", "community") == "pro" or any(
        (
            getattr(config, field, None) is not None
            if field == "expire_warn_days"
            else bool(getattr(config, field, None))
        )
        for field in PRO_CONFIG_FIELDS
    ):
        require_pro_access()
