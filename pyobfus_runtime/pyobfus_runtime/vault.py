"""Runtime String Vault for v0.5 Pro features.

Stores a set of named secret values, each AES-256-GCM encrypted at rest
with a single master key. Decryption is **lazy**: a value is only decrypted
when the caller invokes :meth:`Vault.get`, not during vault construction
or any other observation. This narrows the in-memory plaintext lifetime
to the actual usage window, reducing exposure to memory dumps taken
between obtain-secret and use-secret moments.

Per-entry random nonce: the same plaintext encrypted twice produces
different ciphertexts. An attacker reading the embedded vault cannot
identify "which two entries hold the same value" from byte equality.

Schema-without-decryption: :meth:`has` and :meth:`names` work even with
the wrong master key. This deliberately exposes which names are present
(useful for application logic) while keeping values opaque -- and it
prevents the vault from being used as an oracle that distinguishes "wrong
key" from "no such name" via timing.

Build-time pairing (handled by a future build-pass transformer, P2-11.1):
the obfuscator generates encrypted entries via :meth:`encrypt_entries`,
embeds the resulting dict as a module constant, and emits a Vault
construction at runtime keyed against either an environment variable, a
license-derived key (combination with P2-8), or a hardware fingerprint
(also combination with P2-8). For W0 the runtime accepts any
caller-supplied 32-byte master key.

Patent-gated. See PATENT_NOTES.md and docs/P2-11_DESIGN.md.
"""

from __future__ import annotations

import os
import secrets as _secrets
from collections.abc import Mapping
from typing import cast

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_NONCE_SIZE = 12  # AES-GCM standard
_KEY_SIZE = 32  # 256-bit AES key
_DEFAULT_ITERATIONS = 480_000  # OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
_MIN_ITERATIONS = 100_000
_MIN_SALT_BYTES = 8  # NIST SP 800-132 minimum


class VaultError(RuntimeError):
    """Raised on vault construction or access failures."""


class Vault:
    """Lazy-decrypt encrypted KV store.

    Each entry's plaintext is decrypted on demand inside :meth:`get` and
    discarded as soon as the caller stops referencing the returned string.
    The cipher object holding the master key stays for the life of the
    Vault instance.

    Args:
        encrypted_entries: Map of name -> encrypted blob. Each blob is a
            12-byte nonce prefix followed by AES-GCM
            ciphertext-with-authentication-tag. Produced by
            :meth:`encrypt_entries`.
        key: 32-byte AES key. Derive from a passphrase via
            :meth:`derive_key` if needed.

    Raises:
        VaultError: when ``key`` is not exactly 32 bytes.
    """

    def __init__(
        self,
        encrypted_entries: Mapping[str, bytes],
        key: bytes,
    ) -> None:
        if len(key) != _KEY_SIZE:
            raise VaultError(f"vault key must be {_KEY_SIZE} bytes; got {len(key)}")
        self._entries: dict[str, bytes] = dict(encrypted_entries)
        self._aesgcm = AESGCM(key)

    @staticmethod
    def encrypt_entries(
        plaintext_entries: Mapping[str, str],
        key: bytes,
    ) -> dict[str, bytes]:
        """Encrypt a name->plaintext map for embedding in obfuscated source.

        Each entry gets its own random 12-byte nonce; the resulting blob
        is ``nonce || aes_gcm_ciphertext_with_tag``.

        Returns:
            ``{name: encrypted_blob}`` -- ready to embed.

        Raises:
            VaultError: when ``key`` is not exactly 32 bytes.
        """
        if len(key) != _KEY_SIZE:
            raise VaultError(f"vault key must be {_KEY_SIZE} bytes; got {len(key)}")
        aesgcm = AESGCM(key)
        result: dict[str, bytes] = {}
        for name, value in plaintext_entries.items():
            nonce = os.urandom(_NONCE_SIZE)
            ciphertext = aesgcm.encrypt(nonce, value.encode("utf-8"), associated_data=None)
            result[name] = nonce + ciphertext
        return result

    @staticmethod
    def derive_key(
        passphrase: str,
        salt: bytes,
        *,
        iterations: int = _DEFAULT_ITERATIONS,
    ) -> bytes:
        """Derive a 32-byte AES key from a passphrase via PBKDF2-HMAC-SHA256.

        Args:
            passphrase: Caller-supplied passphrase. UTF-8 encoded internally.
            salt: At least 8 bytes (NIST SP 800-132 minimum). Must be
                persisted alongside the vault to allow re-derivation.
            iterations: PBKDF2 iteration count. Default is the OWASP 2023
                recommendation; raise as hardware speeds increase.

        Raises:
            VaultError: when ``salt`` is shorter than 8 bytes or
                ``iterations`` is below 100,000.
        """
        if len(salt) < _MIN_SALT_BYTES:
            raise VaultError(f"salt must be at least {_MIN_SALT_BYTES} bytes; got {len(salt)}")
        if iterations < _MIN_ITERATIONS:
            raise VaultError(
                f"iterations too low for password-based key derivation; "
                f"got {iterations}, minimum {_MIN_ITERATIONS}"
            )
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=_KEY_SIZE,
            salt=salt,
            iterations=iterations,
        )
        return cast(bytes, kdf.derive(passphrase.encode("utf-8")))

    def get(self, name: str) -> str:
        """Decrypt and return the value for ``name``.

        Raises:
            VaultError: when ``name`` is not in the vault, or when
                decryption fails (wrong master key, corrupted entry).
        """
        if name not in self._entries:
            raise VaultError(f"vault has no entry named {name!r}")
        blob = self._entries[name]
        if len(blob) < _NONCE_SIZE:
            raise VaultError(f"entry {name!r} is too short to contain a valid nonce")
        nonce = blob[:_NONCE_SIZE]
        ciphertext = blob[_NONCE_SIZE:]
        try:
            plaintext = cast(bytes, self._aesgcm.decrypt(nonce, ciphertext, associated_data=None))
            return plaintext.decode("utf-8")
        except InvalidTag as exc:
            raise VaultError(
                f"unable to decrypt entry {name!r} " f"(wrong master key or tampered blob)"
            ) from exc

    def has(self, name: str) -> bool:
        """Return True if ``name`` is present. Does NOT decrypt."""
        return name in self._entries

    def names(self) -> list[str]:
        """Return all entry names. Does NOT decrypt any value."""
        return list(self._entries.keys())


def vault_secrets(plaintext_entries: Mapping[str, str]) -> Vault:
    """Source-side marker for a Vault-protected secret bundle.

    Recommended usage at the top of a module that needs encrypted secrets::

        from pyobfus_pro import vault_secrets

        SECRETS = vault_secrets({
            "STRIPE_KEY": "sk_live_xxx",
            "DB_PASS": "hunter2",
        })

        # ... later
        api_key = SECRETS.get("STRIPE_KEY")

    **Outside the build pass** (development, testing against unobfuscated
    source) this constructs a real :class:`Vault` with a per-process
    random 32-byte master key. The vault is fully functional -- ``get``
    decrypts on demand, ``has``/``names`` work without decryption -- but
    the master key lives only in the current process. Restarting the
    program produces a different key for the same source.

    **Inside the build pass** (P2-11 W3-C ``transformers/vault.py``) this
    call is replaced with three statements that bake the encrypted entries
    + key as module-level constants and construct the Vault directly::

        _VAULT_KEY_SECRETS = b"<32 random bytes>"
        _VAULT_BLOB_SECRETS = {"STRIPE_KEY": b"<nonce||cipher||tag>", ...}
        SECRETS = Vault(_VAULT_BLOB_SECRETS, _VAULT_KEY_SECRETS)

    The build-baked key persists across process restarts so the same
    obfuscated artifact decrypts the same secrets every run. With P2-8
    ``--bind-device`` (0.5.4) the baked ``_VAULT_KEY_<name>`` literal is
    replaced with a runtime ``bind_device_key(current_machine_id(), salt)``
    re-derivation, eliminating the at-rest key constant entirely so the vault
    decrypts only on the bound device.

    Patent-relevant: this is the analogue of P2-1's ``@opacity("encrypted")``
    decorator for the *constant* materialization channel rather than the
    *function-body* channel. Both share the ``LayerSpec.materialization``
    contract from ``pyobfus_pro.opacity.layers`` and use the same
    AES-256-GCM construction (12-byte nonce, 32-byte key, GCM tag) for
    build/runtime parity.

    Args:
        plaintext_entries: ``{name: plaintext}`` map. Both names and values
            must be strings; the build pass enforces this statically.

    Returns:
        A constructed :class:`Vault` instance (development behavior).

    Raises:
        VaultError: if any value is not a string (the build pass enforces
            this on the AST side; the runtime helper enforces it for the
            development path so the dev/build behaviors stay consistent).
    """
    for name, value in plaintext_entries.items():
        if not isinstance(name, str):
            raise VaultError(
                f"vault_secrets entry key must be a string; got " f"{type(name).__name__}"
            )
        if not isinstance(value, str):
            raise VaultError(
                f"vault_secrets entry {name!r} value must be a string; got "
                f"{type(value).__name__}"
            )
    key = _secrets.token_bytes(_KEY_SIZE)
    return Vault(Vault.encrypt_entries(plaintext_entries, key), key)
