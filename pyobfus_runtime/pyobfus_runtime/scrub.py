"""Production-side traceback scrubbing for --scrub-traceback.

When installed as ``sys.excepthook``, an unhandled exception in production
code no longer prints the traceback to stderr. Instead, the traceback is
serialized, encrypted asymmetrically with a build-time-baked public key,
and emitted as an opaque error identifier of the form::

    PYOBFUS-ERR:eyJhbGc...

Customers report this identifier; the developer who has the corresponding
private key reverses it back to the original traceback via
:func:`unscrub_error_id`.

This is the inverse of pyobfus Core's ``unmap`` flow (which deobfuscates a
customer-visible traceback). ``unmap`` assumes the customer sends a trace
that contains obfuscated names; ``scrub`` removes the assumption that the
customer sees a trace at all.

Encryption: hybrid asymmetric. RSA-2048-OAEP wraps a per-error random
AES-256-GCM key; the AES key encrypts the traceback payload. This bounds
RSA work to one short blob per error regardless of payload size, while the
asymmetric envelope ensures the customer cannot decrypt errors emitted on
their own machine.

Patent-gated. See PATENT_NOTES.md and docs/P2-10_DESIGN.md.
"""

from __future__ import annotations

import base64
import os
import sys
import traceback as _traceback
from typing import cast

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_SIZE = 12  # AES-GCM standard
_AES_KEY_SIZE = 32  # 256-bit
_KEY_LENGTH_BYTES = 2  # length-prefix for the RSA-encrypted AES key (uint16)
_DEFAULT_PREFIX = "PYOBFUS-ERR"
_MIN_BLOB_LEN = _NONCE_SIZE + _KEY_LENGTH_BYTES


class ScrubError(RuntimeError):
    """Raised when scrubbing or unscrubbing fails (corrupt input, wrong key)."""


def generate_keypair(*, key_size: int = 2048) -> tuple[bytes, bytes]:
    """Generate a fresh RSA keypair for scrub/unscrub.

    Args:
        key_size: RSA modulus size. 2048 for production (default); smaller
            sizes acceptable only for testing.

    Returns:
        ``(private_pem, public_pem)`` -- PEM-serialized PKCS#8 private key
        and SubjectPublicKeyInfo public key. Bytes, not strings.
    """
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=key_size)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def _scrub_payload(payload: bytes, public_key_pem: bytes) -> str:
    """Hybrid-encrypt ``payload`` to a URL-safe base64 string.

    Blob format inside the b64::

        nonce(12) | enc_key_len(2 BE) | enc_key | ciphertext
    """
    public_key = serialization.load_pem_public_key(public_key_pem)
    if not isinstance(public_key, rsa.RSAPublicKey):
        raise ScrubError("public_key_pem must be an RSA public key")

    aes_key = os.urandom(_AES_KEY_SIZE)
    nonce = os.urandom(_NONCE_SIZE)

    aesgcm = AESGCM(aes_key)
    ciphertext = aesgcm.encrypt(nonce, payload, associated_data=None)

    enc_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    blob = nonce + len(enc_key).to_bytes(_KEY_LENGTH_BYTES, "big") + enc_key + ciphertext
    return base64.urlsafe_b64encode(blob).decode("ascii")


def _unscrub_payload(error_id: str, private_key_pem: bytes) -> bytes:
    """Decrypt an error ID produced by :func:`_scrub_payload`."""
    try:
        blob = base64.urlsafe_b64decode(error_id.encode("ascii"))
    except (ValueError, UnicodeEncodeError) as exc:
        raise ScrubError(f"error_id is not valid base64: {exc}") from exc

    if len(blob) < _MIN_BLOB_LEN:
        raise ScrubError("error_id is too short to contain a valid blob")

    nonce = blob[:_NONCE_SIZE]
    enc_key_len = int.from_bytes(blob[_NONCE_SIZE : _NONCE_SIZE + _KEY_LENGTH_BYTES], "big")
    enc_key_start = _NONCE_SIZE + _KEY_LENGTH_BYTES
    enc_key_end = enc_key_start + enc_key_len
    if enc_key_end > len(blob):
        raise ScrubError("error_id length prefix overruns blob")
    enc_key = blob[enc_key_start:enc_key_end]
    ciphertext = blob[enc_key_end:]

    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    if not isinstance(private_key, rsa.RSAPrivateKey):
        raise ScrubError("private_key_pem must be an RSA private key")

    try:
        aes_key = private_key.decrypt(
            enc_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
    except ValueError as exc:
        raise ScrubError(f"unable to decrypt AES key (wrong private key?): {exc}") from exc

    try:
        return cast(bytes, AESGCM(aes_key).decrypt(nonce, ciphertext, associated_data=None))
    except InvalidTag as exc:
        raise ScrubError(f"unable to decrypt payload (corrupted blob): {exc}") from exc


def scrub_traceback_text(traceback_text: str, public_key_pem: bytes) -> str:
    """Encrypt a traceback string into an opaque base64 error ID (no prefix).

    Args:
        traceback_text: The full traceback text to encrypt.
        public_key_pem: The build-time-embedded RSA public key.
    """
    return _scrub_payload(traceback_text.encode("utf-8"), public_key_pem)


def unscrub_error_id(
    error_id: str,
    private_key_pem: bytes,
    *,
    prefix: str | None = None,
) -> str:
    """Decrypt an error ID back to the original traceback text.

    Args:
        error_id: An ID emitted by :func:`install_scrub_excepthook`. Both
            the bare base64 blob and the prefixed form
            ``"<prefix>:<blob>"`` are accepted.
        private_key_pem: The private key matched to the public key used at
            scrub time.
        prefix: If specified, only IDs with this prefix are accepted; an ID
            without ``:`` is rejected when ``prefix`` is non-None.
            If None (default), any prefix is accepted and stripped, or a
            bare blob is accepted as-is.

    Returns:
        The original traceback text.

    Raises:
        ScrubError: if the ID is malformed, the prefix doesn't match, or
            decryption fails.
    """
    if ":" in error_id:
        observed_prefix, blob = error_id.split(":", 1)
        if prefix is not None and observed_prefix != prefix:
            raise ScrubError(f"prefix mismatch: expected {prefix!r}, got {observed_prefix!r}")
        error_id = blob
    elif prefix is not None:
        raise ScrubError(f"error_id missing required prefix {prefix!r}:")

    return _unscrub_payload(error_id, private_key_pem).decode("utf-8")


def install_scrub_excepthook(
    public_key_pem: bytes,
    *,
    prefix: str = _DEFAULT_PREFIX,
) -> None:
    """Replace ``sys.excepthook`` so unhandled exceptions print only an opaque ID.

    The hook captures the unhandled exception's full traceback, hybrid-
    encrypts it with the supplied public key, and writes
    ``"<prefix>:<base64>"`` to stderr. The customer never sees the original
    traceback; the developer (with the matching private key) recovers it
    via :func:`unscrub_error_id`.

    On internal failure (e.g., malformed key, encryption error), the hook
    emits ``"<prefix>:SCRUB_FAILED"`` rather than falling back to the
    default traceback display -- falling back would leak the very stack
    details we are protecting.

    Args:
        public_key_pem: The build-time-embedded RSA public key.
        prefix: Identifier prepended to the error ID. Customers reporting
            the error see this prefix; it helps them identify which error
            format they are looking at.
    """

    def hook(exc_type, exc_value, exc_traceback):
        try:
            tb_text = "".join(_traceback.format_exception(exc_type, exc_value, exc_traceback))
            error_id = scrub_traceback_text(tb_text, public_key_pem)
            print(f"{prefix}:{error_id}", file=sys.stderr)
        except Exception:  # noqa: BLE001 -- production hook must never re-raise
            print(f"{prefix}:SCRUB_FAILED", file=sys.stderr)

    sys.excepthook = hook
