"""Runtime platform-policy guard (P2-16).

Generalizes PyArmor BCC's platform-restriction mode in pure Python: refuse
to import an obfuscated module unless the running environment satisfies
build-time-baked constraints on OS, minimum Python version, and/or CPU
architecture (e.g. "this build is licensed for Linux production only").

Follows the same module-top-guard-call shape as :func:`expire_check` /
:func:`period_check` in :mod:`pyobfus_pro.license_binding` — a plain
function call the build orchestrator injects at the top of the emitted
module, raising a distinct error class on mismatch so the failure surfaces
in the normal exception path rather than as a cryptic import error.

Not part of the patent-gated P2-1/7/8/9/10/11 combination claims — this is
a standalone environment check with no cryptographic binding, so unlike
``--bind-device`` it does not affect ciphertext keys.
"""

from __future__ import annotations

import platform
import sys
from typing import Optional, Sequence, Tuple


class RuntimePolicyError(RuntimeError):
    """Raised when the running environment violates a build-time runtime policy.

    Distinct from :class:`pyobfus_pro.license_binding.LicenseExpired` — this
    is an environment mismatch (wrong OS / Python version / architecture),
    not a time- or count-based license expiry.
    """


def _parse_python_min(python_min: str) -> Tuple[int, int]:
    """Parse an ``"X.Y"`` minimum-Python-version string into a comparable tuple."""
    parts = python_min.split(".")
    if len(parts) < 2 or not all(p.isdigit() for p in parts[:2]):
        raise RuntimePolicyError(
            f"requires_runtime: python_min must be 'X.Y' (e.g. '3.10'), got {python_min!r}"
        )
    return (int(parts[0]), int(parts[1]))


def requires_runtime(
    os_allowed: Optional[Sequence[str]] = None,
    python_min: Optional[str] = None,
    arch_allowed: Optional[Sequence[str]] = None,
    *,
    current_os: Optional[str] = None,
    current_python: Optional[Tuple[int, int]] = None,
    current_arch: Optional[str] = None,
) -> None:
    """Enforce build-time platform constraints at import time.

    Args:
        os_allowed: Allowed :func:`platform.system` values (e.g.
            ``("Linux", "Darwin")``). Case-insensitive. ``None``/empty means
            no OS restriction.
        python_min: Minimum required Python version as ``"X.Y"`` (e.g.
            ``"3.10"``), compared against ``sys.version_info[:2]``. ``None``
            means no minimum.
        arch_allowed: Allowed :func:`platform.machine` values (e.g.
            ``("x86_64", "arm64")``). Case-insensitive. Common aliases are
            NOT normalized (``"x86_64"`` on Linux vs ``"AMD64"`` on Windows
            are different strings) — list every alias your target platforms
            actually report.
        current_os: Override for :func:`platform.system` — testing aid;
            production calls leave this ``None`` and use the real value.
        current_python: Override for ``sys.version_info[:2]`` — testing aid;
            production calls leave this ``None``.
        current_arch: Override for :func:`platform.machine` — testing aid;
            production calls leave this ``None``.

    Raises:
        RuntimePolicyError: if any supplied constraint is violated, or if
            ``python_min`` is not a valid ``"X.Y"`` string.
    """
    if os_allowed:
        resolved_os = current_os if current_os is not None else platform.system()
        allowed_lower = {o.lower() for o in os_allowed}
        if resolved_os.lower() not in allowed_lower:
            raise RuntimePolicyError(
                f"This build requires one of {tuple(os_allowed)!r}, "
                f"but the current OS is {resolved_os!r}."
            )

    if python_min:
        min_version = _parse_python_min(python_min)
        resolved_version = current_python if current_python is not None else sys.version_info[:2]
        if resolved_version < min_version:
            raise RuntimePolicyError(
                f"This build requires Python >= {python_min}, "
                f"but the running interpreter is "
                f"{resolved_version[0]}.{resolved_version[1]}."
            )

    if arch_allowed:
        resolved_arch = current_arch if current_arch is not None else platform.machine()
        allowed_lower = {a.lower() for a in arch_allowed}
        if resolved_arch.lower() not in allowed_lower:
            raise RuntimePolicyError(
                f"This build requires one of {tuple(arch_allowed)!r}, "
                f"but the current architecture is {resolved_arch!r}."
            )


__all__ = ["RuntimePolicyError", "requires_runtime"]
