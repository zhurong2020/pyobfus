"""Tests for P2-9.1 layer-aware seal coupling (P2-1 ↔ P2-9).

Covers the runtime-side ``_compute_seal_bytes`` + ``_verify_seal(target=...)``
extension and the transformer-side ``layer_assignments`` parameter that
routes L3-assigned sealed functions through the ciphertext seal path.

The combined-pipeline tests exercise the documented pass-order rule:
opacity transformer MUST run before seal transformer when both apply.

Intentionally NO ``from __future__ import annotations`` at the top of this
file: the inner ``compile()`` calls in ``_exec`` would inherit future-flag
bits from this test module, polluting the runtime CodeType for plaintext-
sealed functions and breaking the seal verification (the seal-time
``compile()`` uses ``dont_inherit=True``, but the runtime ``compile()`` does
not). Same regression class as P2-9 W1 -- a property of how Python's
``compile()`` inherits flags from the surrounding compile context.
"""

import secrets
import textwrap

import pytest

from pyobfus_pro import IntegrityError
from pyobfus_pro.opacity import Layer
from pyobfus_pro.runtime.seal import _compute_seal_bytes, _verify_seal
from pyobfus_pro.transformers.opacity import transform_module as opacity_transform
from pyobfus_pro.transformers.seal import SealBuildError
from pyobfus_pro.transformers.seal import transform_module as seal_transform


def _src(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


def _exec(source: str) -> dict:
    namespace: dict = {}
    exec(compile(source, "<t>", "exec"), namespace)  # noqa: S102
    return namespace


# ---------------------------------------------------------------------------
# _compute_seal_bytes (new runtime helper)
# ---------------------------------------------------------------------------


class TestComputeSealBytes:
    def test_returns_sha256_of_input_bytes(self):
        import hashlib

        blob = b"\x01\x02\x03"
        assert _compute_seal_bytes(blob) == hashlib.sha256(blob).digest()

    def test_accepts_bytearray(self):
        import hashlib

        blob = bytearray(b"hello")
        assert _compute_seal_bytes(blob) == hashlib.sha256(b"hello").digest()

    def test_rejects_non_bytes(self):
        with pytest.raises(TypeError, match="bytes or bytearray"):
            _compute_seal_bytes("not bytes")  # type: ignore[arg-type]

    def test_different_blobs_produce_different_hashes(self):
        a = _compute_seal_bytes(b"alpha")
        b = _compute_seal_bytes(b"alpha\x00")
        assert a != b


# ---------------------------------------------------------------------------
# _verify_seal(target=bytes) -- ciphertext seal mode
# ---------------------------------------------------------------------------


class TestVerifySealCiphertextMode:
    def test_correct_hash_with_matching_target_passes(self):
        blob = b"protected ciphertext"
        expected = _compute_seal_bytes(blob)

        @_verify_seal(expected, target=blob)
        def fn(x):
            return x * 2

        assert fn(3) == 6

    def test_wrong_hash_with_matching_target_raises(self):
        blob = b"protected ciphertext"
        wrong_hash = _compute_seal_bytes(b"different")

        @_verify_seal(wrong_hash, target=blob)
        def fn(x):
            return x * 2

        with pytest.raises(IntegrityError, match="ciphertext"):
            fn(3)

    def test_tampered_target_raises(self):
        blob = b"protected ciphertext"
        expected = _compute_seal_bytes(blob)

        # Build the decorator with a tampered target
        tampered = b"tampered ciphertext"

        @_verify_seal(expected, target=tampered)
        def fn(x):
            return x * 2

        with pytest.raises(IntegrityError, match="ciphertext"):
            fn(3)

    def test_error_message_distinguishes_ciphertext_from_code_object(self):
        blob = b"protected"
        wrong = _compute_seal_bytes(b"other")

        @_verify_seal(wrong, target=blob)
        def fn():
            return 1

        with pytest.raises(IntegrityError) as exc_info:
            fn()
        assert "ciphertext" in str(exc_info.value)
        assert "code-object" not in str(exc_info.value)

    def test_plaintext_mode_unchanged_when_target_omitted(self):
        # No target -> behaves exactly like pre-P2-9.1 _verify_seal.
        # Use the wrong-hash path because we can't easily compute the right
        # one for an arbitrary local function in a test (matches existing
        # test_seal_runtime patterns).
        wrong = b"\x00" * 32

        @_verify_seal(wrong)
        def fn():
            return 1

        with pytest.raises(IntegrityError, match="code-object"):
            fn()


# ---------------------------------------------------------------------------
# Transformer-side: layer_assignments routes sealed funcs to plaintext or
# ciphertext seal mode
# ---------------------------------------------------------------------------


class TestTransformerLayerAware:
    def test_unmapped_function_uses_plaintext_seal(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        # No layer_assignments -> back-compat plaintext path.
        out = seal_transform(src)
        assert "@_verify_seal(_SEAL_critical)" in out
        assert "target=" not in out

    def test_l3_assigned_function_uses_ciphertext_seal(self):
        # Hand-craft the post-opacity source: function body already replaced
        # with stub, _CIPHER_critical present, _LAYER_KEY present, decorator
        # is _l3_dispatch (NOT @opacity any more).
        src = _src("""
            from pyobfus_pro import seal_code
            from pyobfus_pro.runtime import _l3_dispatch

            _LAYER_KEY = b"\\x00" * 32
            _CIPHER_critical = b"<faked-cipher-bytes-for-test>"

            @seal_code
            @_l3_dispatch(_CIPHER_critical, _LAYER_KEY)
            def critical(x):
                pass
        """)
        out = seal_transform(src, layer_assignments={"critical": Layer.ENCRYPTED})
        assert "_SEAL_critical" in out
        # P2-9.1 ciphertext-mode signature
        assert "@_verify_seal(_SEAL_critical, target=_CIPHER_critical)" in out

    def test_l0_l1_l2_assigned_functions_use_plaintext_seal(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def f0(x):
                return x

            @seal_code
            def f1(x):
                return x

            @seal_code
            def f2(x):
                return x
        """)
        assignments = {
            "f0": Layer.TRANSPARENT,
            "f1": Layer.AI_READABLE,
            "f2": Layer.OBFUSCATED,
        }
        out = seal_transform(src, layer_assignments=assignments)
        assert "@_verify_seal(_SEAL_f0)" in out
        assert "@_verify_seal(_SEAL_f1)" in out
        assert "@_verify_seal(_SEAL_f2)" in out
        assert "target=" not in out

    def test_l3_without_cipher_constant_raises_pass_order_violation(self):
        # Layer assignment says L3, but no _CIPHER_<name> in source.
        # That means opacity transformer didn't run first -- pass-order
        # rule violated -- we should raise loudly with a specific message.
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        with pytest.raises(SealBuildError, match="Pass-order rule violated"):
            seal_transform(src, layer_assignments={"critical": Layer.ENCRYPTED})

    def test_module_qualname_routes_correctly(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        # Assignment keyed by qualname -- must match module_qualname + name.
        out = seal_transform(
            src,
            layer_assignments={"myapp.crit.critical": Layer.AI_READABLE},
            module_qualname="myapp.crit",
        )
        # AI_READABLE -> plaintext path
        assert "@_verify_seal(_SEAL_critical)" in out
        assert "target=" not in out

    def test_mixed_plaintext_and_ciphertext_seal_in_one_module(self):
        # f1 = L3 (ciphertext), f2 = unmapped (plaintext), in one module.
        src = _src("""
            from pyobfus_pro import seal_code
            from pyobfus_pro.runtime import _l3_dispatch

            _LAYER_KEY = b"\\x00" * 32
            _CIPHER_f1 = b"<faked>"

            @seal_code
            @_l3_dispatch(_CIPHER_f1, _LAYER_KEY)
            def f1(x):
                pass

            @seal_code
            def f2(x):
                return x + 1
        """)
        out = seal_transform(src, layer_assignments={"f1": Layer.ENCRYPTED})
        # f1 ciphertext mode
        assert "@_verify_seal(_SEAL_f1, target=_CIPHER_f1)" in out
        # f2 plaintext mode
        assert "@_verify_seal(_SEAL_f2)" in out


# ---------------------------------------------------------------------------
# Combined opacity → seal pipeline (the production order)
# ---------------------------------------------------------------------------


class TestCombinedPipeline:
    def test_opacity_then_seal_round_trips(self):
        src = _src("""
            from pyobfus_pro import opacity, seal_code

            @seal_code
            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        # Production order: opacity first, seal second.
        opacity_out, assignments = opacity_transform(src)
        final_out = seal_transform(opacity_out, layer_assignments=assignments)

        # The combined output has both seal + dispatch + cipher.
        assert "_SEAL_critical = " in final_out
        assert "_CIPHER_critical = " in final_out
        assert "_LAYER_KEY = " in final_out
        assert "@_verify_seal(_SEAL_critical, target=_CIPHER_critical)" in final_out
        assert "@_l3_dispatch(_CIPHER_critical, _LAYER_KEY)" in final_out

        ns = _exec(final_out)
        assert ns["critical"](3) == 21

    def test_combined_pipeline_tampered_cipher_caught_by_seal_first(self):
        # Tamper the _CIPHER_critical bytes BEFORE compiling. Both the seal
        # and the GCM tag would catch this; the seal should catch it FIRST
        # (defense in depth). We assert the surfaced exception is
        # IntegrityError from the seal layer, not OpacityRuntimeError from
        # the GCM tag.
        src = _src("""
            from pyobfus_pro import opacity, seal_code

            @seal_code
            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        opacity_out, assignments = opacity_transform(src)
        final_out = seal_transform(opacity_out, layer_assignments=assignments)

        # Tamper: replace the _CIPHER_critical line entirely with a known
        # different bytes value. Re-running the build pipeline would
        # re-compute the seal, so we patch the SOURCE TEXT directly to
        # simulate a post-build tamper. Line-anchored replacement avoids
        # the regex-quote-escape issues that come with parsing emitted
        # bytes literals containing embedded quote chars.
        import re

        tampered_out = re.sub(
            r"^_CIPHER_critical = .+$",
            "_CIPHER_critical = b'tampered_cipher_value'",
            final_out,
            count=1,
            flags=re.MULTILINE,
        )
        assert tampered_out != final_out

        ns = _exec(tampered_out)
        with pytest.raises(IntegrityError, match="ciphertext"):
            ns["critical"](3)

    def test_combined_pipeline_intact_cipher_passes_seal_succeeds(self):
        # Smoke: confirm that without tampering, the seal verifies and the
        # decrypt path executes correctly.
        src = _src("""
            from pyobfus_pro import opacity, seal_code

            @seal_code
            @opacity("encrypted")
            def critical(x):
                return x + 1000
        """)
        opacity_out, assignments = opacity_transform(src)
        final_out = seal_transform(opacity_out, layer_assignments=assignments)
        ns = _exec(final_out)
        # Both seal verification AND L3 decrypt must succeed for this to work
        assert ns["critical"](23) == 1023

    def test_seal_only_function_unaffected_in_combined_module(self):
        # f1 has both decorators, f2 only has @seal_code. After both passes,
        # f2 should be a plaintext seal (no target=) and execute normally.
        src = _src("""
            from pyobfus_pro import opacity, seal_code

            @seal_code
            @opacity("encrypted")
            def f1(x):
                return x * 7

            @seal_code
            def f2(x):
                return x + 100
        """)
        opacity_out, assignments = opacity_transform(src)
        final_out = seal_transform(opacity_out, layer_assignments=assignments)

        assert "@_verify_seal(_SEAL_f1, target=_CIPHER_f1)" in final_out
        assert "@_verify_seal(_SEAL_f2)" in final_out
        # f2 has no cipher constant
        assert "_CIPHER_f2" not in final_out

        ns = _exec(final_out)
        assert ns["f1"](3) == 21
        assert ns["f2"](23) == 123

    def test_layer_key_supplied_externally_to_combined_pipeline(self):
        src = _src("""
            from pyobfus_pro import opacity, seal_code

            @seal_code
            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        key = secrets.token_bytes(32)
        opacity_out, assignments = opacity_transform(src, layer_key=key)
        final_out = seal_transform(opacity_out, layer_assignments=assignments)
        ns = _exec(final_out)
        assert ns["critical"](3) == 21
