"""
pyobfus Pro Edition - Commercial Features

This module contains proprietary features for pyobfus Professional Edition.
Not included in the open-source Community Edition.

License: Proprietary - Commercial Use Only
Copyright 2025 Rong Zhu
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("pyobfus")
except PackageNotFoundError:
    # Package not installed (development mode)
    __version__ = "0.0.0-dev"

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

# --- v0.5 Pro mechanisms (patent CN 202610712171X, priority 2026-05-22) ---
# P2-1 Selective Opacity / P2-7 Forensic watermarking / P2-8 License binding /
# P2-9 @seal_code / P2-10 --scrub-traceback / P2-11 Runtime String Vault.
from .forensic import (
    WatermarkError,
    WatermarkRNG,
    derive_layer_key,
    forensic_seed,
    verify_layer_key_match,
)
from .license_binding import (
    LicenseBindingError,
    LicenseExpired,
    bind_device_key,
    current_machine_id,
    expire_check,
    period_check,
)
from .opacity import (
    LAYER_SPECS,
    Layer,
    LayerSpec,
    OpacityConfig,
    OpacityConfigError,
    OpacityRule,
    Resolver,
    opacity,
)
from .runtime.opacity import OpacityRuntimeError, _encrypt_code, _l3_dispatch
from .runtime.scrub import (
    ScrubError,
    generate_keypair,
    install_scrub_excepthook,
    unscrub_error_id,
)
from .runtime.seal import IntegrityError, _verify_seal
from .runtime.vault import Vault, VaultError, vault_secrets


def seal_code(func):
    """Marker decorator for build-time bytecode sealing (P2-9).

    During obfuscation, the build pass replaces this decorator with
    ``@_verify_seal(<sha256-of-co_code>)`` and emits the expected hash as a
    module-level constant. Outside the build pass (development, testing against
    unobfuscated code), this is a no-op that returns the function unchanged.
    """
    return func


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
    # --- v0.5 Pro mechanisms ---
    "LAYER_SPECS",
    "IntegrityError",
    "Layer",
    "LayerSpec",
    "LicenseBindingError",
    "LicenseExpired",
    "OpacityConfig",
    "OpacityConfigError",
    "OpacityRule",
    "OpacityRuntimeError",
    "Resolver",
    "ScrubError",
    "Vault",
    "VaultError",
    "WatermarkError",
    "WatermarkRNG",
    "_encrypt_code",
    "_l3_dispatch",
    "_verify_seal",
    "bind_device_key",
    "current_machine_id",
    "derive_layer_key",
    "expire_check",
    "forensic_seed",
    "generate_keypair",
    "install_scrub_excepthook",
    "opacity",
    "period_check",
    "seal_code",
    "unscrub_error_id",
    "vault_secrets",
    "verify_layer_key_match",
]
