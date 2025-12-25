"""
pyobfus Pro Edition - Commercial Features

This module contains proprietary features for pyobfus Professional Edition.
Not included in the open-source Community Edition.

License: Proprietary - Commercial Use Only
Copyright 2025 Rong Zhu
"""

__version__ = "0.3.0"
__license__ = "Proprietary"

from .string_aes import StringAESEncryptor
from .anti_debug import AntiDebugInjector
from .control_flow import ControlFlowFlattener, StateMachine, State
from .dead_code import DeadCodeInjector, DCIConfig
from .license_embed import LicenseEmbedder, LicenseEmbedConfig, embed_license_checks
from .license import (
    verify_license,
    get_license_status,
    remove_cached_license,
    LicenseError,
    LicenseVerificationError,
    LicenseExpiredError,
    LicenseRevokedError,
)
from .fingerprint import get_device_fingerprint, get_device_info

__all__ = [
    "StringAESEncryptor",
    "AntiDebugInjector",
    "ControlFlowFlattener",
    "StateMachine",
    "State",
    "DeadCodeInjector",
    "DCIConfig",
    "LicenseEmbedder",
    "LicenseEmbedConfig",
    "embed_license_checks",
    "verify_license",
    "get_license_status",
    "remove_cached_license",
    "get_device_fingerprint",
    "get_device_info",
    "LicenseError",
    "LicenseVerificationError",
    "LicenseExpiredError",
    "LicenseRevokedError",
]
