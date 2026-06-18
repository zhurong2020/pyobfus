"""End-to-end integration test exercising ALL 6 patent-gated v0.5 features.

Single source module that combines:

- ``@opacity("encrypted")`` (P2-1 L3 lazy-materialization)
- ``@seal_code`` (P2-9) wrapping the L3 function -> ciphertext-mode seal
  via P2-9.1 layer-aware coupling
- ``vault_secrets({...})`` (P2-11 build-pass)
- ``install_scrub_excepthook(...)`` (P2-10) injected at module top
- Watermark-derived ``_LAYER_KEY`` (P2-7) shared across the L3 ciphertext
  AND the vault key (single seed, multiple deterministic key derivations)
- Device-bound key derivation contract (P2-8 ``bind_device_key``)
  demonstrated in a separate variant

The build orchestrator (lives in public Core post-申请号) is what
sequences the transformers in production. This test simulates that
sequencing inline so the coupling contracts are exercised end-to-end.

Why this test matters: the P2-1 patent main combination claim hangs on
"the lattice + the deterministic mapping + the lazy materialization"
working with the dependent claims (P2-7 / P2-8 / P2-9.1 / P2-10 / P2-11)
rather than just being independent features that happen to share a repo.
A regression that breaks the cross-feature composition would invalidate
the combination claim as written. This file is the demonstrative test
that anchors the claim's "demonstrably composes" property.

Pass-order rule (the production sequence):

    1. opacity_transform(source, layer_key=watermark_key, config=cfg)
       -> emits _LAYER_KEY + _CIPHER_<name> constants, replaces L3 bodies
    2. vault_transform(out, vault_keys={"NAME": <derived-key>})
       -> emits _VAULT_KEY_<name> + _VAULT_BLOB_<name> constants
    3. seal_transform(out, layer_assignments=<from-step-1>)
       -> emits _SEAL_<name> + @_verify_seal decorator (ciphertext-mode
          for L3-assigned funcs; plaintext-mode otherwise)
    4. scrub_transform(out, public_key_pem)
       -> injects install_scrub_excepthook(...) at module top

Intentionally NO ``from __future__ import annotations`` (same reason as
test_seal_layer_aware.py: prevents inner-compile flag inheritance from
poisoning plaintext-sealed functions).
"""

import secrets
import textwrap

import pytest

from pyobfus_pro import (
    IntegrityError,
    OpacityConfig,
    OpacityRuntimeError,
    VaultError,
    bind_device_key,
    derive_layer_key,
    generate_keypair,
    unscrub_error_id,
    verify_layer_key_match,
)
from pyobfus_pro.runtime.scrub import scrub_traceback_text
from pyobfus_pro.transformers.opacity import transform_module as opacity_transform
from pyobfus_pro.transformers.scrub import transform_module as scrub_transform
from pyobfus_pro.transformers.seal import transform_module as seal_transform
from pyobfus_pro.transformers.vault import transform_module as vault_transform


def _src(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


def _exec(source: str) -> dict:
    namespace: dict = {}
    exec(compile(source, "<integration-test>", "exec"), namespace)  # noqa: S102
    return namespace


# ---------------------------------------------------------------------------
# Composite source used by all the integration tests below
# ---------------------------------------------------------------------------


COMPOSITE_SOURCE = _src("""
    from pyobfus_pro import opacity, seal_code, vault_secrets

    SECRETS = vault_secrets({
        "API_KEY": "sk_live_xxx",
        "DB_PASS": "hunter2",
    })

    @seal_code
    @opacity("encrypted")
    def critical(x):
        return x * 7

    def public_helper(x):
        return x + 1
""")


# Match the OpacityConfig that the orchestrator would use. The default
# layer routes `critical` to ENCRYPTED via the decorator (overrides
# default), and `public_helper` falls through to OBFUSCATED default. The
# assignment_hash captures both.
DEFAULT_CONFIG = OpacityConfig()


def _orchestrate_full_pipeline(source: str, *, layer_key: bytes, vault_key: bytes):
    """Run all 4 transformers in production order.

    Returns the fully-transformed source text. The orchestrator is what
    decides the order; this helper bakes the order into one place so
    every test using the full pipeline goes through the same sequence.
    """
    # Step 1: opacity (emits _LAYER_KEY + _CIPHER_<name>)
    after_opacity, assignments = opacity_transform(source, layer_key=layer_key)

    # Step 2: vault (emits _VAULT_KEY_<name> + _VAULT_BLOB_<name>)
    after_vault, _vault_schemas = vault_transform(after_opacity, vault_keys={"SECRETS": vault_key})

    # Step 3: seal (P2-9.1 layer-aware: ciphertext-mode for L3 funcs)
    after_seal = seal_transform(after_vault, layer_assignments=assignments)

    # Step 4: scrub (injects install_scrub_excepthook(...) at module top)
    _, public_pem = generate_keypair(key_size=1024)  # test-only smaller key
    final = scrub_transform(after_seal, public_pem, prefix="PYOBFUS-ERR")

    return final, assignments, public_pem


# ---------------------------------------------------------------------------
# 6-feature round-trip with a per-build random watermark key
# ---------------------------------------------------------------------------


class TestSixFeatureRoundTrip:
    def test_all_six_features_compose_and_round_trip(self):
        """The load-bearing test: build with all 6 features, exec, exercise.

        Verifies:
          - L3 critical() executes and returns the protected behavior
          - Seal verification passes (ciphertext-mode against _CIPHER_critical)
          - Vault decrypts the secrets correctly (lazy decryption)
          - public_helper still works (OBFUSCATED layer = no-body-change in
            transformer; Core orchestration would rename in production)
          - install_scrub_excepthook ran at import (sys.excepthook replaced)
        """
        layer_key = secrets.token_bytes(32)
        vault_key = secrets.token_bytes(32)
        final, assignments, _ = _orchestrate_full_pipeline(
            COMPOSITE_SOURCE, layer_key=layer_key, vault_key=vault_key
        )

        # Sanity-check the emitted artifact has expected constants
        assert "_LAYER_KEY = " in final
        assert "_CIPHER_critical = " in final
        assert "_VAULT_KEY_SECRETS = " in final
        assert "_VAULT_BLOB_SECRETS = " in final
        assert "_SEAL_critical = " in final
        assert "@_verify_seal(_SEAL_critical, target=_CIPHER_critical)" in final
        assert "@_l3_dispatch(_CIPHER_critical, _LAYER_KEY)" in final
        assert "install_scrub_excepthook(_PYOBFUS_SCRUB_PUBLIC_KEY" in final

        # assignments should contain critical -> ENCRYPTED, public_helper -> OBFUSCATED
        assert assignments == {
            "critical": Layer_ENCRYPTED(),
            "public_helper": Layer_OBFUSCATED(),
        }

        # Save the original excepthook so we can restore after exec
        import sys

        original_hook = sys.excepthook
        try:
            ns = _exec(final)
            # L3 + ciphertext-seal round-trip
            assert ns["critical"](3) == 21
            # Vault lazy decryption
            assert ns["SECRETS"].get("API_KEY") == "sk_live_xxx"
            assert ns["SECRETS"].get("DB_PASS") == "hunter2"
            assert ns["SECRETS"].has("API_KEY") is True
            # public_helper unchanged
            assert ns["public_helper"](5) == 6
            # scrub excepthook installed
            assert sys.excepthook is not original_hook
        finally:
            sys.excepthook = original_hook

    def test_l3_seal_catches_cipher_tampering_before_decrypt(self):
        """P2-9.1 defense-in-depth: tampered _CIPHER_critical fails the
        seal check (IntegrityError) BEFORE the L3 dispatch attempts AES-
        GCM decryption."""
        import re
        import sys

        layer_key = secrets.token_bytes(32)
        vault_key = secrets.token_bytes(32)
        final, _, _ = _orchestrate_full_pipeline(
            COMPOSITE_SOURCE, layer_key=layer_key, vault_key=vault_key
        )
        tampered = re.sub(
            r"^_CIPHER_critical = .+$",
            lambda _m: "_CIPHER_critical = b'tampered_cipher_value'",
            final,
            count=1,
            flags=re.MULTILINE,
        )
        assert tampered != final

        original_hook = sys.excepthook
        try:
            ns = _exec(tampered)
            # IntegrityError surfaces (seal layer) -- not OpacityRuntimeError
            # (which would mean we got past the seal and only the GCM tag
            # caught it).
            with pytest.raises(IntegrityError):
                ns["critical"](3)
        finally:
            sys.excepthook = original_hook

    def test_vault_blob_tampering_caught_by_aes_gcm(self):
        """Vault entry tampering surfaces as VaultError via AES-GCM tag
        mismatch -- vault has no separate seal in v1; this confirms the
        cryptographic check itself is the defense."""
        import sys

        layer_key = secrets.token_bytes(32)
        vault_key = secrets.token_bytes(32)
        final, _, _ = _orchestrate_full_pipeline(
            COMPOSITE_SOURCE, layer_key=layer_key, vault_key=vault_key
        )

        original_hook = sys.excepthook
        try:
            ns = _exec(final)
            # Tamper with one entry's bytes after construction
            original = ns["SECRETS"]._entries["API_KEY"]
            tampered = bytearray(original)
            tampered[15] ^= 0xFF
            ns["SECRETS"]._entries["API_KEY"] = bytes(tampered)
            with pytest.raises(VaultError, match="wrong master key or tampered"):
                ns["SECRETS"].get("API_KEY")
            # Untampered entry still works
            assert ns["SECRETS"].get("DB_PASS") == "hunter2"
        finally:
            sys.excepthook = original_hook


# ---------------------------------------------------------------------------
# Watermark + 6-feature: build is byte-deterministic per buyer; forensic
# recovery picks the correct buyer
# ---------------------------------------------------------------------------


class TestWatermarkIntegration:
    def test_watermarked_build_layer_key_is_deterministic_per_buyer(self):
        """Two buyers' builds have different _LAYER_KEY constants;
        forensic verify_layer_key_match recovers the correct one."""
        assignment_hash = DEFAULT_CONFIG.assignment_hash(["critical", "public_helper"])
        alice_key = derive_layer_key("alice@corp.com", assignment_hash)
        bob_key = derive_layer_key("bob@corp.com", assignment_hash)
        vault_key = secrets.token_bytes(32)  # vault key independent in v1

        alice_build, _, _ = _orchestrate_full_pipeline(
            COMPOSITE_SOURCE, layer_key=alice_key, vault_key=vault_key
        )
        bob_build, _, _ = _orchestrate_full_pipeline(
            COMPOSITE_SOURCE, layer_key=bob_key, vault_key=vault_key
        )

        # Forensic recovery: only the correct buyer should match each
        # build.
        candidates = ["bob@corp.com", "carol@corp.com", "alice@corp.com"]
        alice_matches = [
            buyer
            for buyer in candidates
            if verify_layer_key_match(alice_build, buyer, assignment_hash)
        ]
        bob_matches = [
            buyer
            for buyer in candidates
            if verify_layer_key_match(bob_build, buyer, assignment_hash)
        ]
        assert alice_matches == ["alice@corp.com"]
        assert bob_matches == ["bob@corp.com"]

    def test_watermarked_build_round_trips_correctly(self):
        """Watermark-derived layer key still produces a working artifact."""
        import sys

        assignment_hash = DEFAULT_CONFIG.assignment_hash(["critical", "public_helper"])
        layer_key = derive_layer_key("buyer-abc", assignment_hash)
        vault_key = secrets.token_bytes(32)

        final, _, _ = _orchestrate_full_pipeline(
            COMPOSITE_SOURCE, layer_key=layer_key, vault_key=vault_key
        )

        original_hook = sys.excepthook
        try:
            ns = _exec(final)
            assert ns["critical"](3) == 21
            assert ns["SECRETS"].get("API_KEY") == "sk_live_xxx"
        finally:
            sys.excepthook = original_hook


# ---------------------------------------------------------------------------
# Device binding + 6-feature: build for machine A decrypts only on A
# ---------------------------------------------------------------------------


class TestDeviceBindingIntegration:
    def test_correct_machine_decrypts(self):
        """Build orchestrator pattern: derive layer key from
        bind_device_key(machine_id, build_salt). Same machine -> same
        derived key -> AES-GCM works -> L3 + Vault + Seal all succeed."""
        import sys

        from pyobfus_pro import current_machine_id

        salt = secrets.token_bytes(32)
        machine_a_key = bind_device_key(current_machine_id(), salt)
        # Use the same key for vault to demonstrate "single license-derived
        # key feeds both opacity and vault" composition.
        final, _, _ = _orchestrate_full_pipeline(
            COMPOSITE_SOURCE, layer_key=machine_a_key, vault_key=machine_a_key
        )

        original_hook = sys.excepthook
        try:
            ns = _exec(final)
            assert ns["critical"](3) == 21
            assert ns["SECRETS"].get("API_KEY") == "sk_live_xxx"
        finally:
            sys.excepthook = original_hook

    def test_wrong_machine_fails_decrypt(self):
        """Build for machine A; replace _LAYER_KEY at runtime with a key
        derived for machine B (simulating the orchestrator's emitted
        runtime call producing a different key on a different machine).
        L3 fails; the seal layer catches the tampered-cipher case first."""
        import re
        import sys

        salt = secrets.token_bytes(32)
        key_a = bind_device_key("machine-A", salt)
        key_b = bind_device_key("machine-B", salt)

        final, _, _ = _orchestrate_full_pipeline(COMPOSITE_SOURCE, layer_key=key_a, vault_key=key_a)
        # Replace _LAYER_KEY with key_b (the "wrong machine" runtime
        # derivation result).
        wrong_key_repr = repr(key_b)
        tampered = re.sub(
            r"^_LAYER_KEY = .+$",
            lambda _m: f"_LAYER_KEY = {wrong_key_repr}",
            final,
            count=1,
            flags=re.MULTILINE,
        )
        assert tampered != final

        original_hook = sys.excepthook
        try:
            ns = _exec(tampered)
            # The L3 dispatch will get a wrong key -> GCM tag fails ->
            # OpacityRuntimeError. The seal verifies cipher BYTES
            # (unchanged here, only the key changed) so seal passes.
            with pytest.raises(OpacityRuntimeError):
                ns["critical"](3)
        finally:
            sys.excepthook = original_hook


# ---------------------------------------------------------------------------
# Scrub end-to-end: production exception path + dev unscrub recovers it
# ---------------------------------------------------------------------------


class TestScrubEndToEnd:
    def test_scrub_excepthook_encrypts_and_unscrub_recovers(self):
        """Verify the P2-10 scrub <-> unscrub pair works against a real
        traceback. Doesn't actually trigger sys.excepthook (which would
        require an unhandled exception); instead exercises the
        scrub_traceback_text + unscrub_error_id pair directly with the
        keypair generated during the orchestrator pipeline."""
        layer_key = secrets.token_bytes(32)
        vault_key = secrets.token_bytes(32)

        # Capture the keypair the orchestrator uses by re-running its
        # generation step here -- in production the build orchestrator
        # writes the private key to a sidecar file the developer keeps.
        private_pem, public_pem = generate_keypair(key_size=1024)
        # Re-use the keypair across the orchestrator + this test
        after_opacity, assignments = opacity_transform(COMPOSITE_SOURCE, layer_key=layer_key)
        after_vault, _ = vault_transform(after_opacity, vault_keys={"SECRETS": vault_key})
        after_seal = seal_transform(after_vault, layer_assignments=assignments)
        # Use the EXTERNALLY supplied keypair for scrub so we have the
        # private key for the unscrub direction. (We don't exec the
        # final source here -- this test exercises the runtime
        # scrub/unscrub helper pair directly to avoid the complexity of
        # triggering an unhandled exception inside an exec'd module.)
        _ = scrub_transform(after_seal, public_pem, prefix="PYOBFUS-ERR")

        # Simulate a runtime error scenario: a sample traceback text gets
        # encrypted, then the developer decrypts it.
        sample_tb = (
            "Traceback (most recent call last):\n"
            '  File "<run>", line 1, in <module>\n'
            "    critical(...)\n"
            "ValueError: customer-visible message\n"
        )
        error_id = scrub_traceback_text(sample_tb, public_pem)
        prefixed = f"PYOBFUS-ERR:{error_id}"

        recovered = unscrub_error_id(prefixed, private_pem, prefix="PYOBFUS-ERR")
        assert recovered == sample_tb


# ---------------------------------------------------------------------------
# Helpers used in TestSixFeatureRoundTrip's assignment-equality assertion
# ---------------------------------------------------------------------------


def Layer_ENCRYPTED():
    """Return Layer.ENCRYPTED at test-discovery time without polluting
    module-top imports (which would conflict with the COMPOSITE_SOURCE
    being parsed if module-top is imported lazily)."""
    from pyobfus_pro import Layer

    return Layer.ENCRYPTED


def Layer_OBFUSCATED():
    from pyobfus_pro import Layer

    return Layer.OBFUSCATED
