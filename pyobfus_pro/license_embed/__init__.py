"""
License Embedding Module - Embed license restrictions into obfuscated code.

This module provides functionality to embed license verification code
directly into the obfuscated output, enabling:
- Expiration dates
- Hardware binding (machine fingerprint)
- Run count limits

Unlike online license verification, these checks run entirely offline
and are embedded directly into the protected code.
"""

from .embedder import (
    LicenseEmbedder,
    LicenseEmbedConfig,
    embed_license_checks,
)

__all__ = [
    "LicenseEmbedder",
    "LicenseEmbedConfig",
    "embed_license_checks",
]
