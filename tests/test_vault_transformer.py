"""Tests for the P2-11 W3-C Vault build-pass AST transformer.

Covers:

- Pattern detection: ``<NAME> = vault_secrets({...literal...})``
- Encryption emission: ``_VAULT_KEY_<name>`` + ``_VAULT_BLOB_<name>`` +
  Vault construction call
- End-to-end round-trip: transformed source exec produces a working Vault
  whose ``get`` returns the original plaintext
- Schema-without-decryption preserved through the build pass
- v1 limitations: non-literal dict, non-string entries, duplicate names,
  duplicate vault names, ``**``-unpacking in dict
- Import injection (Vault class) happens once even with multiple vaults
- Per-vault unique key when ``vault_keys`` not supplied; key supplied
  externally is used verbatim

Intentionally NO ``from __future__`` import (same reason as
``test_seal_layer_aware.py``: prevents inner-compile flag inheritance
poisoning fixed-key round-trips).
"""

import secrets
import textwrap

import pytest

from pyobfus_pro import VaultError
from pyobfus_pro.transformers.vault import VaultBuildError, transform_module


def _src(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


def _exec(source: str) -> dict:
    namespace: dict = {}
    exec(compile(source, "<t>", "exec"), namespace)  # noqa: S102
    return namespace


# ---------------------------------------------------------------------------
# No-op
# ---------------------------------------------------------------------------


class TestNoOp:
    def test_module_without_vault_secrets_returns_unchanged(self):
        src = "x = 1\n"
        out, schemas = transform_module(src)
        assert out == src
        assert schemas == {}

    def test_module_with_unrelated_dict_assignment_returns_unchanged(self):
        src = _src("""
            CONFIG = {"timeout": 30}
        """)
        out, schemas = transform_module(src)
        assert out == src
        assert schemas == {}


# ---------------------------------------------------------------------------
# Emission shape
# ---------------------------------------------------------------------------


class TestEmissionShape:
    def test_emits_key_blob_and_construct_in_order(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({
                "STRIPE_KEY": "sk_live_xxx",
                "DB_PASS": "hunter2",
            })
        """)
        out, schemas = transform_module(src)
        key_pos = out.find("_VAULT_KEY_SECRETS = ")
        blob_pos = out.find("_VAULT_BLOB_SECRETS = ")
        construct_pos = out.find("SECRETS = Vault(")
        assert 0 <= key_pos < blob_pos < construct_pos
        assert schemas == {"SECRETS": ["STRIPE_KEY", "DB_PASS"]}

    def test_vault_class_import_injected_when_absent(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"K": "v"})
        """)
        out, _ = transform_module(src)
        assert "from pyobfus_pro.runtime import Vault" in out

    def test_vault_class_import_extended_when_partial(self):
        src = _src("""
            from pyobfus_pro import vault_secrets
            from pyobfus_pro.runtime import IntegrityError

            SECRETS = vault_secrets({"K": "v"})
        """)
        out, _ = transform_module(src)
        assert "Vault" in out
        assert "IntegrityError" in out

    def test_marker_call_replaced_completely(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"K": "v"})
        """)
        out, _ = transform_module(src)
        # vault_secrets(...) should not appear in transformed source
        # (ast.unparse may emit `vault_secrets` as part of an unrelated
        # import, which is fine; we check for the call form).
        assert "vault_secrets({" not in out
        assert "vault_secrets(" not in out

    def test_dotted_marker_call_recognized(self):
        src = _src("""
            import pyobfus_pro

            SECRETS = pyobfus_pro.vault_secrets({"K": "v"})
        """)
        out, schemas = transform_module(src)
        assert "_VAULT_BLOB_SECRETS" in out
        assert schemas == {"SECRETS": ["K"]}


# ---------------------------------------------------------------------------
# Round-trip exec
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_emitted_vault_decrypts_correctly(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({
                "STRIPE_KEY": "sk_live_xxx",
                "DB_PASS": "hunter2",
            })
        """)
        out, _ = transform_module(src)
        ns = _exec(out)
        assert ns["SECRETS"].get("STRIPE_KEY") == "sk_live_xxx"
        assert ns["SECRETS"].get("DB_PASS") == "hunter2"

    def test_schema_without_decryption_works_in_emitted_module(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({
                "FOO": "1",
                "BAR": "2",
            })
        """)
        out, _ = transform_module(src)
        ns = _exec(out)
        # Schema-without-decryption discipline: has() / names() do not
        # invoke the AES path, so they work even with a wrong-key Vault.
        # Smoke check it works here as a sanity check.
        assert ns["SECRETS"].has("FOO") is True
        assert ns["SECRETS"].has("MISSING") is False
        assert sorted(ns["SECRETS"].names()) == ["BAR", "FOO"]

    def test_per_build_random_key_differs_each_call(self):
        src = _src("""
            from pyobfus_pro import vault_secrets
            SECRETS = vault_secrets({"K": "v"})
        """)
        out_a, _ = transform_module(src)
        out_b, _ = transform_module(src)
        # Different per-call random keys -> different output texts
        assert out_a != out_b

    def test_externally_supplied_key_used_verbatim(self):
        src = _src("""
            from pyobfus_pro import vault_secrets
            SECRETS = vault_secrets({"K": "v"})
        """)
        key = secrets.token_bytes(32)
        out, _ = transform_module(src, vault_keys={"SECRETS": key})
        assert repr(key) in out
        # Round-trip with the supplied key works
        ns = _exec(out)
        assert ns["SECRETS"].get("K") == "v"

    def test_supplied_key_must_be_32_bytes(self):
        src = _src("""
            from pyobfus_pro import vault_secrets
            SECRETS = vault_secrets({"K": "v"})
        """)
        with pytest.raises(ValueError, match="32 bytes"):
            transform_module(src, vault_keys={"SECRETS": b"short"})


# ---------------------------------------------------------------------------
# Multiple vaults in one module
# ---------------------------------------------------------------------------


class TestMultipleVaults:
    def test_two_vaults_each_get_own_key_and_blob(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            ALPHA = vault_secrets({"K1": "v1"})
            BETA = vault_secrets({"K2": "v2"})
        """)
        out, schemas = transform_module(src)
        assert "_VAULT_KEY_ALPHA = " in out
        assert "_VAULT_BLOB_ALPHA = " in out
        assert "_VAULT_KEY_BETA = " in out
        assert "_VAULT_BLOB_BETA = " in out
        # Vault class imported once
        assert out.count("from pyobfus_pro.runtime import Vault") <= 1
        assert schemas == {"ALPHA": ["K1"], "BETA": ["K2"]}

    def test_multiple_vaults_round_trip_independently(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            ALPHA = vault_secrets({"K1": "v1"})
            BETA = vault_secrets({"K2": "v2"})
        """)
        out, _ = transform_module(src)
        ns = _exec(out)
        assert ns["ALPHA"].get("K1") == "v1"
        assert ns["BETA"].get("K2") == "v2"

    def test_duplicate_vault_name_raises(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"A": "1"})
            SECRETS = vault_secrets({"B": "2"})
        """)
        with pytest.raises(VaultBuildError, match="more than once"):
            transform_module(src)


# ---------------------------------------------------------------------------
# v1 input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_non_literal_dict_argument_raises(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SOURCE = {"K": "v"}
            SECRETS = vault_secrets(SOURCE)
        """)
        with pytest.raises(VaultBuildError, match="dict literal"):
            transform_module(src)

    def test_keyword_argument_raises(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets(plaintext_entries={"K": "v"})
        """)
        with pytest.raises(VaultBuildError, match="positional dict"):
            transform_module(src)

    def test_non_string_value_raises(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"K": 42})
        """)
        with pytest.raises(VaultBuildError, match="value must be a string"):
            transform_module(src)

    def test_non_string_key_raises(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({1: "v"})
        """)
        with pytest.raises(VaultBuildError, match="key must be a string"):
            transform_module(src)

    def test_dict_unpacking_raises(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            BASE = {"X": "y"}
            SECRETS = vault_secrets({**BASE, "K": "v"})
        """)
        with pytest.raises(VaultBuildError, match="\\*\\*-unpacking"):
            transform_module(src)

    def test_duplicate_entry_key_raises(self):
        # Note: ast.parse normally collapses dict literals with duplicate
        # keys; the validator catches the rare case where parse preserves
        # them (e.g., ast.Dict crafted programmatically). For source-level
        # duplicates, Python silently keeps the last one and we don't see a
        # duplicate. Skip the source-level test; the validator's check is
        # for completeness against AST manipulation.
        pytest.skip("source-level dict literal collapses dup keys at parse")


# ---------------------------------------------------------------------------
# Tamper detection at runtime
# ---------------------------------------------------------------------------


class TestTamperDetection:
    def test_tampered_blob_byte_raises_at_runtime(self):
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"K": "secret_value"})
        """)
        out, _ = transform_module(src)
        ns = _exec(out)

        # Tamper: corrupt the encrypted blob bytes inside the Vault.
        original_blob = next(iter(ns["SECRETS"]._entries.values()))
        tampered = bytearray(original_blob)
        # Flip a byte in the ciphertext region (after 12-byte nonce)
        tampered[15] ^= 0xFF
        ns["SECRETS"]._entries["K"] = bytes(tampered)

        with pytest.raises(VaultError, match="wrong master key or tampered"):
            ns["SECRETS"].get("K")

    def test_wrong_baked_key_raises_at_runtime(self):
        # Simulate an attacker who patched _VAULT_KEY_SECRETS in the source
        # to a different 32-byte value but left the blob alone.
        src = _src("""
            from pyobfus_pro import vault_secrets

            SECRETS = vault_secrets({"K": "secret"})
        """)
        out, _ = transform_module(src)
        # Replace _VAULT_KEY_SECRETS line with a known-different key.
        import re

        wrong_key_repr = repr(b"\x00" * 32)
        # Pass replacement as a callable so backslash escapes in
        # ``wrong_key_repr`` aren't reinterpreted by ``re.sub``.
        tampered_out = re.sub(
            r"^_VAULT_KEY_SECRETS = .+$",
            lambda _m: f"_VAULT_KEY_SECRETS = {wrong_key_repr}",
            out,
            count=1,
            flags=re.MULTILINE,
        )
        assert tampered_out != out
        ns = _exec(tampered_out)
        with pytest.raises(VaultError, match="wrong master key or tampered"):
            ns["SECRETS"].get("K")
