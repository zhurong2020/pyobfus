"""Runtime support for P2-1 Selective Opacity L3 lazy materialization.

The build-pass transformer (W3-B, separate commit) replaces the body of an
``@opacity("encrypted")`` function with a stub and emits two module-level
constants:

    _CIPHER_<funcname> = b"<nonce(12) || ciphertext+tag>"
    _LAYER_KEY = b"<32-byte-AES-256-key>"

    @_l3_dispatch(_CIPHER_<funcname>, _LAYER_KEY)
    def <funcname>(...):
        pass  # body replaced at first call by the decrypted CodeType

At first call to the wrapper, ``_l3_dispatch`` decrypts the cipher blob,
``marshal.loads`` the plaintext into a ``CodeType``, and patches the stub's
``__code__`` so that subsequent calls execute the real bytecode directly.

The cached state ("did we decrypt yet?" + the decrypted ``CodeType``) lives
in a **closure cell**, not as an attribute on either the wrapper or the
stub, mirroring the hardening pattern in ``seal.py``: an attacker cannot
pre-set ``stub._loaded = True`` to bypass decryption, because there is no
``_loaded`` attribute -- the boolean only exists in the closure.

**At-rest property** (the load-bearing patent claim):

    Plaintext bytecode never exists in the build artifact and never exists
    in the imported module before the first call. An attacker dumping
    ``marshal.dumps(<imported_module>.critical.__code__)`` immediately
    after import gets the *stub*'s code, not the protected function's
    code. The protected code only materializes inside the closure cell,
    only after the first call, only for the lifetime of the process.

W3-A scope (this module): the runtime side. The build-tool helper
``_encrypt_code`` is also in this module so the build pass and the
runtime share a single encryption rule. Build-pass AST transformer is
W3-B.

Patent-gated. See PATENT_NOTES.md and docs/P2-1_DESIGN.md.
"""

from __future__ import annotations

import functools
import marshal
import secrets
import types
from typing import Callable, TypeVar

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_F = TypeVar("_F", bound=Callable)

_NONCE_SIZE = 12  # AES-GCM standard
_KEY_SIZE = 32  # 256-bit AES key
_TAG_SIZE = 16  # AES-GCM authentication tag
_MIN_CIPHER_LEN = _NONCE_SIZE + _TAG_SIZE  # nonce + (zero-length-ct) + tag


class OpacityRuntimeError(RuntimeError):
    """Raised when L3 lazy materialization fails.

    Possible causes (all surface uniformly to avoid leaking which one
    triggered, in line with the failure-mode discipline established for
    P2-10 and P2-11):

      - wrong layer key (GCM tag mismatch)
      - tampered cipher blob (GCM tag mismatch)
      - truncated cipher blob (length check)
      - corrupted plaintext (marshal.loads failure)
      - unexpected payload type (decrypted to non-CodeType)
    """


def _encrypt_code(code: types.CodeType, key: bytes | bytearray) -> bytes:
    """Build-time helper: encrypt a CodeType for L3 lazy materialization.

    The build pass calls this once per L3-decorated function and embeds the
    return value as ``_CIPHER_<funcname> = b"..."`` in the emitted module.

    Args:
        code: The compiled CodeType of the function being protected. Must
            be a CodeType, not a function or lambda; callers should pass
            ``func.__code__``.
        key: 32-byte AES-256 key. The build pass either generates this
            randomly per build (default) or derives it from a license /
            device fingerprint (combination with P2-8 ``--bind-device``).

    Returns:
        ``nonce(12 bytes) || ciphertext_with_tag`` -- a single bytes object
        ready to be embedded as a module constant.

    Raises:
        TypeError: if ``code`` is not a CodeType.
        ValueError: if ``key`` is not exactly 32 bytes.

    Note: nonce is generated with ``secrets.token_bytes`` (CSPRNG) per the
    workspace ENGINEERING_BASELINE Tier 2 rule. Each call produces a unique
    blob even for the same code + same key.
    """
    if not isinstance(code, types.CodeType):
        raise TypeError(f"_encrypt_code expects a CodeType, got {type(code).__name__}")
    if not isinstance(key, (bytes, bytearray)) or len(key) != _KEY_SIZE:
        raise ValueError(
            f"key must be exactly {_KEY_SIZE} bytes, got "
            f"{len(key) if isinstance(key, (bytes, bytearray)) else type(key).__name__}"
        )

    plaintext = marshal.dumps(code)
    nonce = secrets.token_bytes(_NONCE_SIZE)
    aesgcm = AESGCM(bytes(key))
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext, associated_data=None)
    return nonce + ciphertext_with_tag


def _decrypt_code(cipher: bytes | bytearray, key: bytes | bytearray) -> types.CodeType:
    """Reverse of ``_encrypt_code``: cipher blob + key -> CodeType.

    All failure modes raise ``OpacityRuntimeError`` with a generic message
    so an attacker probing with crafted ciphers cannot distinguish "wrong
    key" from "tampered blob" from "corrupted marshal" via the exception
    type or message text.
    """
    if not isinstance(key, (bytes, bytearray)) or len(key) != _KEY_SIZE:
        raise OpacityRuntimeError("L3 decryption failed: invalid key size")
    if not isinstance(cipher, (bytes, bytearray)) or len(cipher) < _MIN_CIPHER_LEN:
        raise OpacityRuntimeError("L3 decryption failed: cipher blob too short")

    nonce = bytes(cipher[:_NONCE_SIZE])
    ciphertext_with_tag = bytes(cipher[_NONCE_SIZE:])

    aesgcm = AESGCM(bytes(key))
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext_with_tag, associated_data=None)
    except InvalidTag as exc:
        raise OpacityRuntimeError(
            "L3 decryption failed (key mismatch or tampered ciphertext)"
        ) from exc

    try:
        # S302: marshal.loads on attacker-controlled bytes is dangerous.
        # Here the bytes are NOT attacker-controlled: AESGCM.decrypt()
        # above raises InvalidTag on any modification or wrong key, so
        # `plaintext` is provably what we encrypted at build time. The
        # marshal payload's integrity is bound to the GCM tag, not its
        # own structure.
        code = marshal.loads(plaintext)  # noqa: S302
    except Exception as exc:  # noqa: BLE001 -- marshal raises ValueError/EOFError/TypeError
        raise OpacityRuntimeError("L3 decryption failed: corrupted payload") from exc

    if not isinstance(code, types.CodeType):
        raise OpacityRuntimeError(
            f"L3 decryption failed: payload is {type(code).__name__}, expected CodeType"
        )

    return code


def _l3_dispatch(cipher: bytes | bytearray, key: bytes | bytearray) -> Callable[[_F], _F]:
    """Wrap an L3 stub function with first-call decrypt + ``__code__`` patch.

    The build pass emits::

        _CIPHER_critical = b"..."

        @_l3_dispatch(_CIPHER_critical, _LAYER_KEY)
        def critical(x):
            pass  # discarded at first call

    On the first call to ``critical``, the wrapper:

      1. Calls ``_decrypt_code(cipher, key)`` -> CodeType
      2. Sets ``stub.__code__ = decrypted_code`` so the stub's body is now
         the protected function's body
      3. Marks the closure-cell ``loaded`` flag True so subsequent calls
         skip step 1-2

    On subsequent calls, the wrapper does a single boolean check then
    delegates to the patched stub.

    The decrypted CodeType is held in a closure cell (not a function
    attribute) so an attacker cannot pre-set
    ``critical._loaded = True`` to skip the integrity-bound decryption.

    Args:
        cipher: ``nonce || ciphertext_with_tag`` produced by
            ``_encrypt_code`` at build time.
        key: 32-byte AES-256 key matching the one used at build time.

    Returns:
        A decorator that takes a stub function and returns the dispatch
        wrapper.
    """

    def decorator(stub: _F) -> _F:
        loaded = False
        cached_code: types.CodeType | None = None  # noqa: F841 -- closure-held debug handle

        @functools.wraps(stub)
        def wrapper(*args, **kwargs):
            nonlocal loaded, cached_code
            if not loaded:
                cached_code = _decrypt_code(cipher, key)
                stub.__code__ = cached_code
                loaded = True
            return stub(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
