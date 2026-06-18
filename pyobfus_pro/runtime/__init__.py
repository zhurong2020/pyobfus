"""Runtime support for v0.5 Pro features.

This module is imported by obfuscated output. Its API surface MUST stay
backward-compatible across v0.5.x point releases -- the obfuscated code
emitted at build time pins the runtime-call shape.
"""

from pyobfus_pro.runtime.opacity import (
    OpacityRuntimeError,
    _encrypt_code,
    _l3_dispatch,
)
from pyobfus_pro.runtime.scrub import (
    ScrubError,
    generate_keypair,
    install_scrub_excepthook,
    scrub_traceback_text,
    unscrub_error_id,
)
from pyobfus_pro.runtime.seal import IntegrityError, _verify_seal
from pyobfus_pro.runtime.vault import Vault, VaultError, vault_secrets

__all__ = [
    "IntegrityError",
    "OpacityRuntimeError",
    "ScrubError",
    "Vault",
    "VaultError",
    "_encrypt_code",
    "_l3_dispatch",
    "_verify_seal",
    "generate_keypair",
    "install_scrub_excepthook",
    "scrub_traceback_text",
    "unscrub_error_id",
    "vault_secrets",
]
