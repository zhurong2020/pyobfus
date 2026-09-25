"""Stable, redistributable runtime API for pyobfus-generated artifacts."""

from importlib.metadata import PackageNotFoundError, version

from .binding import (
    LicenseBindingError,
    LicenseExpired,
    LicenseExpiryWarning,
    bind_device_key,
    current_machine_id,
    default_counter_path,
    expire_check,
    period_check,
    provided_key,
    set_key_provider,
)
from .embedded_data import EmbeddedDataError, encrypt_data_file, get_embedded_data
from .opacity import OpacityRuntimeError, _encrypt_code, _l3_dispatch
from .policy import RuntimePolicyError, requires_runtime
from .scrub import (
    ScrubError,
    generate_keypair,
    install_scrub_excepthook,
    scrub_traceback_text,
    unscrub_error_id,
)
from .seal import IntegrityError, _verify_seal
from .vault import Vault, VaultError, vault_secrets

try:
    __version__ = version("pyobfus-runtime")
except PackageNotFoundError:
    __version__ = "0.1.0.dev0"

__all__ = [
    "EmbeddedDataError",
    "IntegrityError",
    "LicenseBindingError",
    "LicenseExpired",
    "LicenseExpiryWarning",
    "OpacityRuntimeError",
    "RuntimePolicyError",
    "ScrubError",
    "Vault",
    "VaultError",
    "_encrypt_code",
    "_l3_dispatch",
    "_verify_seal",
    "bind_device_key",
    "current_machine_id",
    "default_counter_path",
    "encrypt_data_file",
    "expire_check",
    "generate_keypair",
    "get_embedded_data",
    "install_scrub_excepthook",
    "period_check",
    "provided_key",
    "set_key_provider",
    "requires_runtime",
    "scrub_traceback_text",
    "unscrub_error_id",
    "vault_secrets",
]
