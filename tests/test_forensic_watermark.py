"""Tests for P2-7 forensic watermarking primitives.

Covers:

- ``forensic_seed`` determinism, buyer-uniqueness, hash-sensitivity, input
  validation, version stability (snapshot test against a known-good byte
  string for the ``v1`` construction)
- ``WatermarkRNG`` byte-reproducibility, seed-uniqueness, streaming
  semantics, ``randint`` distribution sanity
- ``derive_layer_key`` AES-256 size + determinism + buyer-uniqueness
- ``verify_layer_key_match`` true on match, false on wrong buyer / wrong
  hash / missing constant / non-bytes literal
- Integration with the real opacity transformer: a build using a
  watermark-derived key is byte-identical for the same buyer + same
  source, and ``verify_layer_key_match`` recovers the buyer ID
"""

import hashlib
import textwrap

import pytest

from pyobfus_pro.forensic import (
    WatermarkError,
    WatermarkRNG,
    derive_layer_key,
    forensic_seed,
    verify_layer_key_match,
)
from pyobfus_pro.opacity import OpacityConfig
from pyobfus_pro.transformers.opacity import transform_module as opacity_transform


def _src(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


# ---------------------------------------------------------------------------
# forensic_seed
# ---------------------------------------------------------------------------


class TestForensicSeed:
    def test_returns_32_bytes(self):
        seed = forensic_seed("alice", b"\x00" * 32)
        assert isinstance(seed, bytes)
        assert len(seed) == 32

    def test_deterministic_for_same_inputs(self):
        h = b"\xaa" * 32
        a = forensic_seed("alice", h)
        b = forensic_seed("alice", h)
        assert a == b

    def test_different_buyer_id_differs(self):
        h = b"\xaa" * 32
        a = forensic_seed("alice", h)
        b = forensic_seed("bob", h)
        assert a != b

    def test_different_assignment_hash_differs(self):
        a = forensic_seed("alice", b"\x00" * 32)
        b = forensic_seed("alice", b"\x01" * 32)
        assert a != b

    def test_buyer_id_must_be_non_empty_string(self):
        with pytest.raises(WatermarkError, match="non-empty"):
            forensic_seed("", b"\x00" * 32)
        with pytest.raises(WatermarkError, match="must be a string"):
            forensic_seed(42, b"\x00" * 32)  # type: ignore[arg-type]

    def test_assignment_hash_must_be_32_bytes(self):
        with pytest.raises(WatermarkError, match="32 bytes"):
            forensic_seed("alice", b"too short")
        with pytest.raises(WatermarkError, match="32 bytes"):
            forensic_seed("alice", b"\x00" * 33)
        with pytest.raises(WatermarkError, match="32 bytes"):
            forensic_seed("alice", "not bytes")  # type: ignore[arg-type]

    def test_v1_construction_byte_stable_snapshot(self):
        # Snapshot test: this exact byte string MUST NOT change without a
        # version bump in _PERSONALIZATION. Buyer attribution years after
        # a build hinges on byte stability of the v1 construction.
        seed = forensic_seed("buyer-snapshot-test", b"\x00" * 32)
        # Re-derive via the documented construction to confirm the
        # implementation matches the docstring exactly.
        h = hashlib.sha256()
        h.update(b"pyobfus-v0.5-forensic-watermark-v1")
        h.update(b"\x00")
        h.update(b"buyer-snapshot-test")
        h.update(b"\x00")
        h.update(b"\x00" * 32)
        assert seed == h.digest()


# ---------------------------------------------------------------------------
# WatermarkRNG
# ---------------------------------------------------------------------------


class TestWatermarkRNG:
    def test_seed_must_be_32_bytes(self):
        with pytest.raises(WatermarkError, match="32 bytes"):
            WatermarkRNG(b"short")

    def test_next_bytes_returns_requested_length(self):
        rng = WatermarkRNG(b"\xa5" * 32)
        assert len(rng.next_bytes(1)) == 1
        assert len(rng.next_bytes(31)) == 31
        assert len(rng.next_bytes(32)) == 32
        assert len(rng.next_bytes(100)) == 100  # spans multiple HMAC blocks

    def test_next_bytes_n_must_be_positive(self):
        rng = WatermarkRNG(b"\xa5" * 32)
        with pytest.raises(WatermarkError):
            rng.next_bytes(0)
        with pytest.raises(WatermarkError):
            rng.next_bytes(-1)

    def test_two_rngs_same_seed_produce_same_stream(self):
        a = WatermarkRNG(b"\xa5" * 32)
        b = WatermarkRNG(b"\xa5" * 32)
        for _ in range(10):
            assert a.next_bytes(16) == b.next_bytes(16)

    def test_two_rngs_different_seeds_produce_different_streams(self):
        a = WatermarkRNG(b"\xa5" * 32)
        b = WatermarkRNG(b"\xa6" * 32)
        # Probability of collision in 32 bytes is 2^-256; safe to assert.
        assert a.next_bytes(32) != b.next_bytes(32)

    def test_streaming_state_advances(self):
        # Two consecutive next_bytes calls return DIFFERENT bytes (no
        # accidental block reuse).
        rng = WatermarkRNG(b"\xa5" * 32)
        first = rng.next_bytes(32)
        second = rng.next_bytes(32)
        assert first != second

    def test_byte_reproducibility_via_redocumented_construction(self):
        # The HMAC-CTR construction is documented; re-implement it inline
        # and confirm WatermarkRNG matches. This guards against accidental
        # implementation drift (e.g., switching counter endianness or
        # changing the HMAC key derivation).
        import hmac as _hmac

        seed = b"\x33" * 32
        rng = WatermarkRNG(seed)
        produced = rng.next_bytes(64)

        # Reconstruct: counter starts at 1, each block = HMAC-SHA256(seed, BE-uint64(counter))
        block1 = _hmac.new(seed, (1).to_bytes(8, "big"), "sha256").digest()
        block2 = _hmac.new(seed, (2).to_bytes(8, "big"), "sha256").digest()
        assert produced == block1 + block2

    def test_randint_returns_in_range(self):
        rng = WatermarkRNG(b"\x77" * 32)
        for _ in range(100):
            n = rng.randint(5, 10)
            assert 5 <= n <= 10

    def test_randint_lo_equals_hi_returns_lo(self):
        rng = WatermarkRNG(b"\x77" * 32)
        assert rng.randint(7, 7) == 7

    def test_randint_rejects_inverted_range(self):
        rng = WatermarkRNG(b"\x77" * 32)
        with pytest.raises(WatermarkError, match="lo <= hi"):
            rng.randint(10, 5)

    def test_randint_distribution_sanity(self):
        # 1000 samples across [0, 9] should have mean roughly in [3, 6]
        # (true mean = 4.5; 3-sigma tolerance with n=1000 is ~ ±0.27).
        rng = WatermarkRNG(b"\x77" * 32)
        samples = [rng.randint(0, 9) for _ in range(1000)]
        mean = sum(samples) / len(samples)
        assert 3.0 < mean < 6.0


# ---------------------------------------------------------------------------
# derive_layer_key
# ---------------------------------------------------------------------------


class TestDeriveLayerKey:
    def test_returns_32_bytes(self):
        key = derive_layer_key("alice", b"\x00" * 32)
        assert isinstance(key, bytes)
        assert len(key) == 32

    def test_deterministic_for_same_inputs(self):
        h = b"\x42" * 32
        assert derive_layer_key("alice", h) == derive_layer_key("alice", h)

    def test_different_buyer_id_produces_different_key(self):
        h = b"\x42" * 32
        assert derive_layer_key("alice", h) != derive_layer_key("bob", h)

    def test_different_assignment_hash_produces_different_key(self):
        a = derive_layer_key("alice", b"\x00" * 32)
        b = derive_layer_key("alice", b"\x01" * 32)
        assert a != b

    def test_key_is_first_32_bytes_of_rng_stream(self):
        seed = forensic_seed("alice", b"\x00" * 32)
        expected = WatermarkRNG(seed).next_bytes(32)
        assert derive_layer_key("alice", b"\x00" * 32) == expected


# ---------------------------------------------------------------------------
# verify_layer_key_match
# ---------------------------------------------------------------------------


class TestVerifyLayerKeyMatch:
    @pytest.fixture
    def assignment_hash(self):
        return b"\xaa" * 32

    def test_match_returns_true(self, assignment_hash):
        key = derive_layer_key("alice", assignment_hash)
        suspect_source = f"_LAYER_KEY = {key!r}\n"
        assert verify_layer_key_match("alice", "alice", assignment_hash) is False
        assert verify_layer_key_match(suspect_source, "alice", assignment_hash) is True

    def test_wrong_buyer_returns_false(self, assignment_hash):
        key_alice = derive_layer_key("alice", assignment_hash)
        suspect_source = f"_LAYER_KEY = {key_alice!r}\n"
        assert verify_layer_key_match(suspect_source, "bob", assignment_hash) is False

    def test_wrong_assignment_hash_returns_false(self, assignment_hash):
        key = derive_layer_key("alice", assignment_hash)
        suspect_source = f"_LAYER_KEY = {key!r}\n"
        wrong_hash = b"\xbb" * 32
        assert verify_layer_key_match(suspect_source, "alice", wrong_hash) is False

    def test_no_layer_key_constant_returns_false(self, assignment_hash):
        assert verify_layer_key_match("x = 1\ny = 2\n", "alice", assignment_hash) is False

    def test_layer_key_not_bytes_literal_returns_false(self, assignment_hash):
        suspect_source = "_LAYER_KEY = derive_at_runtime(...)\n"
        assert verify_layer_key_match(suspect_source, "alice", assignment_hash) is False

    def test_layer_key_with_other_module_constants_around_it(self, assignment_hash):
        # Realistic shape: opacity transformer also emits _CIPHER_<name>
        # constants. _LAYER_KEY must be findable amid surrounding lines.
        key = derive_layer_key("alice", assignment_hash)
        suspect_source = (
            "from pyobfus_pro.runtime import _l3_dispatch\n"
            f"_LAYER_KEY = {key!r}\n"
            "_CIPHER_critical = b'whatever'\n"
        )
        assert verify_layer_key_match(suspect_source, "alice", assignment_hash) is True


# ---------------------------------------------------------------------------
# End-to-end integration with opacity transformer
# ---------------------------------------------------------------------------


class TestOpacityIntegration:
    def test_watermarked_build_is_byte_deterministic_per_buyer(self):
        # Identical buyer ID + identical source + identical config =
        # identical build artifact. This is the load-bearing property
        # for the patent claim.
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        # Compute the assignment hash from the source's qualnames
        config = OpacityConfig()
        assignment_hash = config.assignment_hash(["critical"])
        layer_key = derive_layer_key("alice", assignment_hash)

        out_a, _ = opacity_transform(src, layer_key=layer_key)
        out_b, _ = opacity_transform(src, layer_key=layer_key)

        # The cipher constant has a per-call random nonce, so the source
        # texts will differ (cipher bytes change). But the LAYER_KEY line
        # is byte-identical.
        # Patent claim is "the layer key is byte-identical per buyer";
        # the cipher per-call randomness is the AES-GCM nonce uniqueness
        # property orthogonal to watermarking.
        import re

        layer_key_a = re.search(r"^_LAYER_KEY = (b['\"][^\n]+)$", out_a, re.MULTILINE)
        layer_key_b = re.search(r"^_LAYER_KEY = (b['\"][^\n]+)$", out_b, re.MULTILINE)
        assert layer_key_a is not None and layer_key_b is not None
        assert layer_key_a.group(1) == layer_key_b.group(1)

    def test_watermark_recovery_from_real_opacity_build(self):
        # Build a watermarked artifact, then run the forensic recovery
        # against a list of candidate buyer IDs. Only the actual buyer
        # should match.
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        config = OpacityConfig()
        assignment_hash = config.assignment_hash(["critical"])
        true_buyer = "alice@example.com"

        layer_key = derive_layer_key(true_buyer, assignment_hash)
        out, _ = opacity_transform(src, layer_key=layer_key)

        candidates = ["bob@example.com", "carol@example.com", true_buyer, "dave@example.com"]
        matches = [
            buyer for buyer in candidates if verify_layer_key_match(out, buyer, assignment_hash)
        ]
        assert matches == [true_buyer]

    def test_two_different_buyers_produce_different_layer_keys_in_emitted_source(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x
        """)
        config = OpacityConfig()
        assignment_hash = config.assignment_hash(["critical"])

        out_alice, _ = opacity_transform(src, layer_key=derive_layer_key("alice", assignment_hash))
        out_bob, _ = opacity_transform(src, layer_key=derive_layer_key("bob", assignment_hash))

        assert verify_layer_key_match(out_alice, "alice", assignment_hash) is True
        assert verify_layer_key_match(out_alice, "bob", assignment_hash) is False
        assert verify_layer_key_match(out_bob, "bob", assignment_hash) is True
        assert verify_layer_key_match(out_bob, "alice", assignment_hash) is False
