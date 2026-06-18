"""License binding combo runtime primitives for P2-8.

Three orthogonal binding axes that combine in build-time CLI flags:

- ``--expire <ISO-date>`` — calendar-based expiry. Wraps
  :func:`expire_check`.
- ``--bind-device`` — hardware-fingerprint-derived runtime key. Wraps
  :func:`current_machine_id` + :func:`bind_device_key`. The key replaces
  the build-baked ``_LAYER_KEY`` constant for P2-1 L3 ciphertext and the
  ``_VAULT_KEY_<name>`` constants for P2-11 vaults: wrong device produces
  wrong derived key, GCM tag fails, ``OpacityRuntimeError`` /
  ``VaultError`` surfaces. License-gated decryption built in without a
  per-call check.
- ``--period <max_runs>`` — usage-counter-based expiry via atomic file
  counter. Wraps :func:`period_check`.

Each axis can be used standalone or composed with the others: e.g.,
``--expire 2027-01-01 --bind-device --period 100`` produces an artifact
that decrypts only on the issued device, only before 2027-01-01, and only
for the first 100 runs.

Patent novelty (PATENT_NOTES.md P2-8): the combination semantics + the
runtime-key-derivation-instead-of-baked-constant approach for
``--bind-device``. Each individual flag is prior art (PyArmor 9.2.x has
each); the combination claim hangs on the L3-coupling that lets license
gating happen "for free" inside the existing decryption path.

Patent-gated. See PATENT_NOTES.md and docs/P2-8_DESIGN.md (TBD).
"""

from pyobfus_pro.license_binding.binding import (
    LicenseBindingError,
    LicenseExpired,
    bind_device_key,
    current_machine_id,
    expire_check,
    period_check,
)

__all__ = [
    "LicenseBindingError",
    "LicenseExpired",
    "bind_device_key",
    "current_machine_id",
    "expire_check",
    "period_check",
]
