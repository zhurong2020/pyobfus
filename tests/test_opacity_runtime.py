"""Tests for P2-1 Selective Opacity L3 lazy-materialization runtime.

Covers ``_encrypt_code`` (build-tool helper) + ``_decrypt_code`` (internal
inverse) + ``_l3_dispatch`` (the closure-cell-cached wrapper that the
build pass emits around every L3 stub).

Build-pass AST transformer tests live separately in
``test_opacity_transformer.py`` (W3-B, not yet written).
"""

from __future__ import annotations

import marshal
import secrets
import types

import pytest

from pyobfus_pro import OpacityRuntimeError, _encrypt_code, _l3_dispatch
from pyobfus_pro.runtime.opacity import _decrypt_code

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_code(src: str, name: str = "_test_fn") -> types.CodeType:
    """Compile ``src`` and return the inner FunctionDef's code object.

    ``src`` must contain exactly one top-level def with name ``name``. The
    helper extracts that function's CodeType so tests can encrypt + decrypt
    + execute it without needing to plumb a real def through the test body.
    """
    module_code = compile(src, "<test>", "exec")
    namespace: dict[str, object] = {}
    exec(module_code, namespace)  # noqa: S102 -- test helper
    fn = namespace[name]
    assert callable(fn)
    return fn.__code__  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# _encrypt_code -- build-tool helper
# ---------------------------------------------------------------------------


class TestEncryptCode:
    def test_encrypt_returns_nonce_plus_ciphertext_with_tag(self):
        code = _make_code("def _test_fn(x):\n    return x * 2\n")
        key = secrets.token_bytes(32)
        blob = _encrypt_code(code, key)
        # Layout: 12-byte nonce + ciphertext + 16-byte GCM tag
        # plaintext = marshal.dumps(code) is non-empty, so the blob is
        # strictly longer than nonce + tag alone.
        assert isinstance(blob, bytes)
        assert len(blob) > 12 + 16
        # First 12 bytes are nonce, the rest is ciphertext_with_tag
        # (length = ct_len + tag_len = ct_len + 16)
        assert len(blob) - 12 - 16 == len(marshal.dumps(code))

    def test_encrypt_produces_unique_blob_each_call(self):
        """Per-call random nonce -> same code+key never produces same blob."""
        code = _make_code("def _test_fn():\n    return 'static'\n")
        key = secrets.token_bytes(32)
        a = _encrypt_code(code, key)
        b = _encrypt_code(code, key)
        assert a != b

    def test_encrypt_requires_codetype(self):
        key = secrets.token_bytes(32)

        def regular(x):  # noqa: ARG001
            return 0

        # Must pass __code__, not the function itself
        with pytest.raises(TypeError, match="CodeType"):
            _encrypt_code(regular, key)  # type: ignore[arg-type]

    def test_encrypt_requires_32_byte_key(self):
        code = _make_code("def _test_fn():\n    return 1\n")
        for bad_key in (b"", b"short", secrets.token_bytes(16), secrets.token_bytes(64)):
            with pytest.raises(ValueError, match="32 bytes"):
                _encrypt_code(code, bad_key)


# ---------------------------------------------------------------------------
# _decrypt_code -- inverse + failure modes
# ---------------------------------------------------------------------------


class TestDecryptCode:
    def test_round_trip_recovers_codetype(self):
        original = _make_code("def _test_fn(x):\n    return x + 100\n")
        key = secrets.token_bytes(32)
        blob = _encrypt_code(original, key)
        recovered = _decrypt_code(blob, key)
        assert isinstance(recovered, types.CodeType)
        # marshal.dumps is not byte-stable across re-marshalling on
        # CPython 3.12 (string interning / ref-id structure can shift),
        # so we compare on the behavior-determining fields directly.
        assert recovered.co_code == original.co_code
        assert recovered.co_consts == original.co_consts
        assert recovered.co_names == original.co_names
        assert recovered.co_varnames == original.co_varnames
        assert recovered.co_argcount == original.co_argcount
        assert recovered.co_flags == original.co_flags

    def test_round_trip_executes_correctly(self):
        original = _make_code("def _test_fn(x):\n    return x * 3 + 7\n")
        key = secrets.token_bytes(32)
        blob = _encrypt_code(original, key)
        recovered = _decrypt_code(blob, key)
        # Build a fresh function from the recovered code and call it.
        fn = types.FunctionType(recovered, {}, "_test_fn")
        assert fn(5) == 22

    def test_wrong_key_raises_opacity_error(self):
        original = _make_code("def _test_fn():\n    return 1\n")
        key = secrets.token_bytes(32)
        wrong_key = secrets.token_bytes(32)
        blob = _encrypt_code(original, key)
        with pytest.raises(OpacityRuntimeError):
            _decrypt_code(blob, wrong_key)

    def test_tampered_ciphertext_raises_opacity_error(self):
        original = _make_code("def _test_fn():\n    return 1\n")
        key = secrets.token_bytes(32)
        blob = bytearray(_encrypt_code(original, key))
        # Flip a byte in the ciphertext region (after the 12-byte nonce).
        blob[20] ^= 0xFF
        with pytest.raises(OpacityRuntimeError):
            _decrypt_code(bytes(blob), key)

    def test_truncated_blob_raises_opacity_error(self):
        key = secrets.token_bytes(32)
        with pytest.raises(OpacityRuntimeError, match="too short"):
            _decrypt_code(b"\x00" * 8, key)

    def test_invalid_key_size_raises_opacity_error(self):
        original = _make_code("def _test_fn():\n    return 1\n")
        good_key = secrets.token_bytes(32)
        blob = _encrypt_code(original, good_key)
        with pytest.raises(OpacityRuntimeError, match="invalid key size"):
            _decrypt_code(blob, b"shortkey")

    def test_failure_modes_dont_leak_which_one_via_message(self):
        """Wrong key, tampered cipher, and corrupted payload all surface as
        OpacityRuntimeError. Their *type* is uniform; only the wrapped
        ``__cause__`` chain differs. Examiners reading the runtime should
        not be able to distinguish key-mismatch from cipher-tamper from
        message text alone -- both surface as 'key mismatch or tampered
        ciphertext' from the same except-block.
        """
        original = _make_code("def _test_fn():\n    return 1\n")
        key = secrets.token_bytes(32)
        wrong_key = secrets.token_bytes(32)

        blob_wrong_key = _encrypt_code(original, key)
        blob_tampered = bytearray(_encrypt_code(original, key))
        blob_tampered[20] ^= 0xAA

        with pytest.raises(OpacityRuntimeError) as e_wrong_key:
            _decrypt_code(blob_wrong_key, wrong_key)
        with pytest.raises(OpacityRuntimeError) as e_tampered:
            _decrypt_code(bytes(blob_tampered), key)

        # Same message text from the same except branch.
        assert str(e_wrong_key.value) == str(e_tampered.value)


# ---------------------------------------------------------------------------
# _l3_dispatch -- the wrapper the build pass emits
# ---------------------------------------------------------------------------


class TestL3Dispatch:
    def test_first_call_decrypts_and_executes_real_body(self):
        # Simulate what the build pass produces: a stub def + cipher
        # constant + decorator. The stub body is never executed (replaced
        # at first call by the decrypted code).
        original = _make_code("def _test_fn(x):\n    return x * 7\n")
        key = secrets.token_bytes(32)
        cipher = _encrypt_code(original, key)

        @_l3_dispatch(cipher, key)
        def _test_fn(x):  # stub: body discarded at first call
            raise AssertionError("L3 stub body must not execute")

        assert _test_fn(3) == 21

    def test_second_call_skips_decrypt(self):
        # First call decrypts and patches stub.__code__. We can't directly
        # observe "did it skip decrypt" from outside, so we corrupt the
        # cipher AFTER the first call -- if it tried to re-decrypt, it
        # would fail. If the wrapper hits its cached path, the second call
        # succeeds because it doesn't touch cipher again.
        original = _make_code("def _test_fn(x):\n    return x + 1\n")
        key = secrets.token_bytes(32)
        cipher = bytearray(_encrypt_code(original, key))

        @_l3_dispatch(cipher, key)
        def _test_fn(x):  # noqa: ARG001 -- stub
            raise AssertionError("stub")

        assert _test_fn(10) == 11
        # Corrupt the cipher in place. If wrapper re-decrypts on every
        # call, this would now fail.
        for i in range(12, len(cipher)):
            cipher[i] ^= 0xFF
        # Cache hit: still works.
        assert _test_fn(10) == 11
        assert _test_fn(99) == 100

    def test_wrong_key_surfaces_as_runtime_error_on_first_call(self):
        original = _make_code("def _test_fn():\n    return 1\n")
        key = secrets.token_bytes(32)
        wrong_key = secrets.token_bytes(32)
        cipher = _encrypt_code(original, key)

        @_l3_dispatch(cipher, wrong_key)
        def _test_fn():
            raise AssertionError("stub")

        with pytest.raises(OpacityRuntimeError):
            _test_fn()

    def test_tampered_cipher_surfaces_on_first_call(self):
        original = _make_code("def _test_fn():\n    return 1\n")
        key = secrets.token_bytes(32)
        cipher = bytearray(_encrypt_code(original, key))
        cipher[20] ^= 0xFF

        @_l3_dispatch(bytes(cipher), key)
        def _test_fn():
            raise AssertionError("stub")

        with pytest.raises(OpacityRuntimeError):
            _test_fn()

    def test_attribute_tamper_does_not_bypass_decrypt(self):
        """Attacker sets fake _loaded attribute -> still must decrypt.

        The cache state lives in a closure cell, NOT in any function
        attribute. Setting attributes on either the wrapper or any
        plausibly-named flag must not bypass the first-call decrypt.
        """
        original = _make_code("def _test_fn(x):\n    return x * 2\n")
        key = secrets.token_bytes(32)
        wrong_key = secrets.token_bytes(32)
        cipher = _encrypt_code(original, key)

        @_l3_dispatch(cipher, wrong_key)  # wrong key -> would fail if decrypt runs
        def _test_fn(x):
            return x  # stub returns x, would succeed if bypass worked

        # Try every attribute name an attacker might guess.
        for fake_attr in ("_loaded", "loaded", "_cached", "cached_code", "verified"):
            setattr(_test_fn, fake_attr, True)

        # Decrypt still runs; wrong_key still fails. No attribute bypass.
        with pytest.raises(OpacityRuntimeError):
            _test_fn(5)

    def test_multiple_dispatched_functions_have_independent_caches(self):
        """Two L3 functions each get their own closure cell, no crosstalk."""
        code_a = _make_code("def _test_fn(x):\n    return x + 1\n")
        code_b = _make_code("def _test_fn(x):\n    return x + 100\n")
        key = secrets.token_bytes(32)
        cipher_a = _encrypt_code(code_a, key)
        cipher_b = _encrypt_code(code_b, key)

        @_l3_dispatch(cipher_a, key)
        def fn_a(x):  # noqa: ARG001
            raise AssertionError("stub")

        @_l3_dispatch(cipher_b, key)
        def fn_b(x):  # noqa: ARG001
            raise AssertionError("stub")

        assert fn_a(0) == 1
        assert fn_b(0) == 100
        assert fn_a(10) == 11  # second call still uses A's cache
        assert fn_b(10) == 110

    def test_wrapper_preserves_function_metadata(self):
        original = _make_code("def _test_fn(x):\n    '''mydoc'''\n    return x\n")
        key = secrets.token_bytes(32)
        cipher = _encrypt_code(original, key)

        @_l3_dispatch(cipher, key)
        def _test_fn(x):
            """mydoc"""
            return x

        # functools.wraps was applied -> name + docstring preserved.
        assert _test_fn.__name__ == "_test_fn"
        assert _test_fn.__doc__ == "mydoc"

    def test_at_rest_stub_code_is_not_protected_code_before_first_call(self):
        """**Patent-load-bearing property**: before any call, dumping
        ``stub.__code__`` should NOT yield the protected function's code.

        The decrypted code only materializes inside the closure (and
        eventually patches stub.__code__) at first call. Before that, an
        attacker dumping the imported module gets the stub.
        """
        protected = _make_code("def _test_fn(x):\n    return x * 999\n")
        key = secrets.token_bytes(32)
        cipher = _encrypt_code(protected, key)

        @_l3_dispatch(cipher, key)
        def _test_fn(x):
            return x  # stub returns x -- distinct from protected (x*999)

        # Locate the closed-over stub by iterating closure cells (cell
        # ordering follows alphabetical co_freevars order, which is an
        # implementation detail we shouldn't lock down).
        stub_via_closure = None
        for cell in _test_fn.__closure__ or ():
            try:
                contents = cell.cell_contents
            except ValueError:
                continue
            if isinstance(contents, types.FunctionType):
                stub_via_closure = contents
                break
        assert stub_via_closure is not None

        # Build a clean function from stub.__code__ and call it: returns
        # the *stub*'s behavior (x), not the protected's (x*999).
        before_call_fn = types.FunctionType(stub_via_closure.__code__, {}, "before")
        assert before_call_fn(5) == 5  # stub behavior

        # Now trigger first call. After this, stub.__code__ is patched.
        assert _test_fn(5) == 4995  # protected behavior

        after_call_fn = types.FunctionType(stub_via_closure.__code__, {}, "after")
        assert after_call_fn(5) == 4995  # protected behavior post-patch

    def test_kwargs_and_varargs_pass_through(self):
        original = _make_code(
            "def _test_fn(*args, **kwargs):\n" "    return (sum(args), sorted(kwargs.items()))\n"
        )
        key = secrets.token_bytes(32)
        cipher = _encrypt_code(original, key)

        @_l3_dispatch(cipher, key)
        def _test_fn(*args, **kwargs):  # noqa: ARG001 -- stub
            raise AssertionError("stub")

        result = _test_fn(1, 2, 3, foo="bar", baz=42)
        assert result == (6, [("baz", 42), ("foo", "bar")])
