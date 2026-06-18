"""Runtime integrity-seal verifier for @seal_code.

Build-time the obfuscator emits:

    _SEAL_<funcname> = b"<32-byte-sha256>"

    @_verify_seal(_SEAL_<funcname>)
    def <funcname>(...):
        ...

At first call, the wrapper recomputes the seal from the function's code
object and compares against the baked-in expected hash. Mismatch ->
IntegrityError.

Hashing strategy: SHA-256 over a marshal-serialized tuple of the code
object's *behavior-determining* fields:

    (co_code, co_consts*, co_names, co_varnames, co_freevars, co_cellvars,
     co_flags, co_argcount, co_posonlyargcount, co_kwonlyargcount,
     co_stacksize, co_exceptiontable)

    * co_consts is recursively normalized: any nested code object is
      replaced by its own hash before serialization.

Compilation-context fields (co_filename, co_firstlineno, co_lnotab,
co_linetable, co_qualname) are deliberately EXCLUDED so the seal is stable
across different build/runtime compilation environments while remaining
sensitive to:

  - bytecode rewrites (co_code)
  - constant swaps (co_consts) -- this is the case a co_code-only seal
    would miss, since constants are stored in a separate table indexed
    from co_code
  - global-name redirects (co_names)
  - local-variable renames (co_varnames / co_freevars / co_cellvars)
  - signature changes (argcount fields)
  - exception-handler table changes (co_exceptiontable, 3.11+)

Caching: the verified state is held in a closure cell (not as an attribute
on the wrapper or the wrapped function), so an attacker cannot bypass
verification by pre-setting any attribute on the target. After the first
successful verify, subsequent calls are O(1).

Cross-version constraint: build Python version must match deployment Python
version, because bytecode shape and exception-table format vary across
versions. Documented in docs/P2-9_DESIGN.md.

Patent-gated. See PATENT_NOTES.md and docs/P2-9_DESIGN.md.
"""

from __future__ import annotations

import functools
import hashlib
import marshal
import types
from typing import Any, Callable, TypeVar

_F = TypeVar("_F", bound=Callable)


class IntegrityError(RuntimeError):
    """Raised when a sealed function's code-object hash does not match the build-time seal.

    Indicates in-memory tampering: monkey-patching of `__code__`, debugger
    rewrites, or compromised import hooks. Surfaces in the normal exception
    path so AI debuggers can reason about the failure (preserves pyobfus's
    AI-debug promise).
    """


def _hash_code(code: types.CodeType) -> bytes:
    """Recursively hash a code object on its behavior-determining fields only.

    Excludes context metadata so the seal is stable across compilation
    environments. Nested code objects (in ``co_consts``) are hashed
    recursively and substituted by their hash bytes in the parent tuple.
    """
    consts_normalized = tuple(
        _hash_code(c) if isinstance(c, types.CodeType) else c for c in code.co_consts
    )
    behavioral = (
        code.co_code,
        consts_normalized,
        code.co_names,
        code.co_varnames,
        code.co_freevars,
        code.co_cellvars,
        code.co_flags,
        code.co_argcount,
        code.co_posonlyargcount,
        code.co_kwonlyargcount,
        code.co_stacksize,
        # 3.11+ zero-cost exceptions live here, not in co_code; older
        # versions don't have it -- fall back to empty bytes so the tuple
        # shape stays stable across Python versions.
        getattr(code, "co_exceptiontable", b""),
    )
    return hashlib.sha256(marshal.dumps(behavioral)).digest()


def _compute_seal(func_or_code: Any) -> bytes:
    """Compute the integrity seal for a function or code object.

    Used by both the build-time pass (to bake the expected hash) and runtime
    (to verify), ensuring build/runtime stay in lockstep with a single
    hashing rule.
    """
    code = getattr(func_or_code, "__code__", func_or_code)
    return _hash_code(code)


def _compute_seal_bytes(blob: bytes | bytearray) -> bytes:
    """Compute a SHA-256 seal over an opaque byte blob.

    Used by P2-9.1 layer-aware sealing: when a function is in P2-1's L3
    (encrypted) layer, its body has been replaced with a stub at build time
    and the protected behavior lives in a ``_CIPHER_<name>`` constant.
    Hashing the cipher bytes directly (rather than the stub's CodeType, which
    is constant ``pass``) lets the seal detect tampering of the cipher
    constant *before* the L3 dispatch even attempts decryption -- a
    defense-in-depth layer above AES-GCM tag verification.

    Plain SHA-256 over raw bytes (no marshal projection) because cipher
    blobs are already a flat opaque byte sequence with no separately-
    addressable behavior-determining sub-fields.

    Patent-relevant: this is the runtime side of the P2-1 ↔ P2-9 coupling
    contract. ``LayerSpec.seal_target == "ciphertext"`` for L3 routes the
    seal target through this function rather than ``_compute_seal``.
    """
    if not isinstance(blob, (bytes, bytearray)):
        raise TypeError(
            f"_compute_seal_bytes expects bytes or bytearray, " f"got {type(blob).__name__}"
        )
    return hashlib.sha256(bytes(blob)).digest()


def _verify_seal(
    expected: bytes,
    target: bytes | bytearray | None = None,
) -> Callable[[_F], _F]:
    """Wrap a function with first-call code-integrity verification.

    Two seal modes:

    - **Plaintext seal (default)**: ``target=None``. The wrapper recomputes
      ``_compute_seal(func)`` (SHA-256 over the behavioral-field marshal
      projection of ``func.__code__``) and compares against ``expected``.
      Used for L0 / L1 / L2 functions and standalone ``@seal_code``.

    - **Ciphertext seal (P2-9.1, layer-aware coupling)**: ``target=<bytes>``.
      The wrapper hashes ``target`` directly via ``_compute_seal_bytes`` and
      compares against ``expected``. Used for L3 functions where ``target``
      is the ``_CIPHER_<name>`` cipher blob; the seal then verifies that the
      embedded ciphertext is unchanged from build time, *before* the
      L3 dispatch attempts decryption. Tampering with the cipher constant
      surfaces here as ``IntegrityError`` rather than as the GCM-tag
      ``OpacityRuntimeError`` that would surface at decrypt time -- two
      independent integrity checks, structurally distinct.

    Args:
        expected: 32-byte SHA-256 of the appropriate seal target at build
            time.
        target: When supplied, the cipher blob to hash directly (P2-9.1).
            When ``None``, hash the wrapped function's CodeType (default).

    Returns:
        A decorator that wraps the target function with verify-on-first-call.

    Raises (at call time):
        IntegrityError: if the runtime hash does not match ``expected``.
    """

    def decorator(func: _F) -> _F:
        # Cached in a closure cell rather than a wrapper attribute so that no
        # external setattr can bypass verification.
        verified = False

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal verified
            if not verified:
                actual = _compute_seal_bytes(target) if target is not None else _compute_seal(func)
                if actual != expected:
                    raise IntegrityError(
                        f"Integrity check failed for {func.__qualname__!r}: "
                        f"{'ciphertext' if target is not None else 'code-object'} "
                        f"hash does not match build-time seal."
                    )
                verified = True
            return func(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator
