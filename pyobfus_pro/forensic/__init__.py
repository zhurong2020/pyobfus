"""Forensic watermarking primitives for P2-7 ``--fingerprint <buyer-id>``.

Public API:

- :func:`forensic_seed` -- deterministic 32-byte master seed from
  ``(buyer_id, OpacityConfig.assignment_hash)``.
- :class:`WatermarkRNG` -- byte-reproducible HMAC-SHA256 counter-mode
  stream cipher seeded from ``forensic_seed``. Replaces
  ``secrets.token_bytes`` in the watermarked-build path.
- :func:`derive_layer_key` -- 32-byte AES-256 layer key derived from a
  buyer's master seed. Feed to ``opacity.transform_module(layer_key=...)``
  and ``vault.transform_module(vault_keys=...)`` so the buyer's build is
  byte-deterministic.
- :func:`verify_layer_key_match` -- forensic recovery: given a leaked
  artifact + a candidate buyer ID + the original assignment hash, check
  whether the buyer's derived key matches the artifact's embedded
  ``_LAYER_KEY``.
- :class:`WatermarkError` -- raised on invalid inputs.

The build-pass transformer side is unchanged: ``opacity.transform_module``
and ``vault.transform_module`` already accept externally-supplied keys
(landed in W3-B / W3-C). The build orchestrator's job is to derive the
keys via this module when ``--fingerprint`` is set, and pass them through.

Patent-gated. See PATENT_NOTES.md and docs/P2-7_DESIGN.md (TBD).
"""

from pyobfus_pro.forensic.watermark import (
    WatermarkError,
    WatermarkRNG,
    derive_layer_key,
    forensic_seed,
    verify_layer_key_match,
)

__all__ = [
    "WatermarkError",
    "WatermarkRNG",
    "derive_layer_key",
    "forensic_seed",
    "verify_layer_key_match",
]
