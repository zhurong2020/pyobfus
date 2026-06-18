"""Runtime tests for the String Vault (P2-11)."""

import os

import pytest

from pyobfus_pro import Vault, VaultError


@pytest.fixture
def key():
    return os.urandom(32)


class TestRoundTrip:
    def test_single_entry(self, key):
        encrypted = Vault.encrypt_entries({"STRIPE_KEY": "sk_test_xxx"}, key)
        vault = Vault(encrypted, key)
        assert vault.get("STRIPE_KEY") == "sk_test_xxx"

    def test_multiple_entries(self, key):
        plaintext = {
            "STRIPE_KEY": "sk_test_111",
            "DATABASE_URL": "postgres://user:pw@host/db",
            "JWT_SECRET": "supersecret",
        }
        encrypted = Vault.encrypt_entries(plaintext, key)
        vault = Vault(encrypted, key)
        for name, value in plaintext.items():
            assert vault.get(name) == value

    def test_unicode_value(self, key):
        encrypted = Vault.encrypt_entries({"TOKEN": "中文密钥"}, key)
        vault = Vault(encrypted, key)
        assert vault.get("TOKEN") == "中文密钥"

    def test_each_encryption_is_distinct(self, key):
        """Same plaintext + same key + different invocations -> different ciphertexts."""
        a = Vault.encrypt_entries({"X": "value"}, key)
        b = Vault.encrypt_entries({"X": "value"}, key)
        assert a["X"] != b["X"]

    def test_empty_vault(self, key):
        vault = Vault({}, key)
        assert vault.names() == []
        assert not vault.has("anything")


class TestKeyConstraints:
    def test_constructor_rejects_wrong_key_size(self):
        with pytest.raises(VaultError, match="must be 32 bytes"):
            Vault({}, b"short")

    def test_encrypt_rejects_wrong_key_size(self):
        with pytest.raises(VaultError, match="must be 32 bytes"):
            Vault.encrypt_entries({"X": "v"}, b"short")


class TestFailureModes:
    def test_missing_entry_raises(self, key):
        vault = Vault({}, key)
        with pytest.raises(VaultError, match="no entry"):
            vault.get("MISSING")

    def test_wrong_key_fails_decryption(self, key):
        encrypted = Vault.encrypt_entries({"X": "secret"}, key)
        wrong_key = os.urandom(32)
        vault = Vault(encrypted, wrong_key)
        with pytest.raises(VaultError, match="wrong master key"):
            vault.get("X")

    def test_tampered_blob_fails_decryption(self, key):
        encrypted = Vault.encrypt_entries({"X": "secret"}, key)
        # Flip a byte in the ciphertext (after the 12-byte nonce)
        blob = encrypted["X"]
        tampered = blob[:12] + bytes([blob[12] ^ 0x01]) + blob[13:]
        vault = Vault({"X": tampered}, key)
        with pytest.raises(VaultError, match="wrong master key or tampered"):
            vault.get("X")

    def test_too_short_entry_raises(self, key):
        vault = Vault({"X": b"short"}, key)
        with pytest.raises(VaultError, match="too short"):
            vault.get("X")


class TestSchemaWithoutDecryption:
    """has() and names() expose schema, never decrypt."""

    def test_has_works(self, key):
        encrypted = Vault.encrypt_entries({"X": "v"}, key)
        vault = Vault(encrypted, key)
        assert vault.has("X")
        assert not vault.has("Y")

    def test_names_returns_all(self, key):
        encrypted = Vault.encrypt_entries({"X": "1", "Y": "2"}, key)
        vault = Vault(encrypted, key)
        assert sorted(vault.names()) == ["X", "Y"]

    def test_has_with_wrong_key_still_works(self):
        """A wrong key must not block schema introspection."""
        good_key = os.urandom(32)
        encrypted = Vault.encrypt_entries({"X": "v"}, good_key)
        wrong_key = os.urandom(32)
        vault = Vault(encrypted, wrong_key)
        # has() succeeds (no decryption); only get() should fail.
        assert vault.has("X")
        assert vault.names() == ["X"]
        with pytest.raises(VaultError):
            vault.get("X")


class TestDeriveKey:
    def test_same_passphrase_and_salt_give_same_key(self):
        salt = b"saltvaluesixteen"
        key1 = Vault.derive_key("mypass", salt)
        key2 = Vault.derive_key("mypass", salt)
        assert key1 == key2
        assert len(key1) == 32

    def test_different_salt_gives_different_key(self):
        key1 = Vault.derive_key("mypass", b"saltsalt12345678")
        key2 = Vault.derive_key("mypass", b"saltsalt87654321")
        assert key1 != key2

    def test_different_passphrase_gives_different_key(self):
        salt = b"sharedsalt123456"
        key1 = Vault.derive_key("password1", salt)
        key2 = Vault.derive_key("password2", salt)
        assert key1 != key2

    def test_short_salt_rejected(self):
        with pytest.raises(VaultError, match="salt must"):
            Vault.derive_key("p", b"short")  # 5 bytes, below 8

    def test_low_iterations_rejected(self):
        with pytest.raises(VaultError, match="iterations too low"):
            Vault.derive_key("p", b"saltvaluelong", iterations=1000)

    def test_derived_key_works_for_round_trip(self):
        salt = b"saltvalue1234567"
        key = Vault.derive_key("mypass", salt)
        encrypted = Vault.encrypt_entries({"X": "secret"}, key)
        # Re-derive on a different code path
        key2 = Vault.derive_key("mypass", salt)
        vault = Vault(encrypted, key2)
        assert vault.get("X") == "secret"


class TestLazyDecryption:
    """Construction must not decrypt any value; get() must do so on demand.

    Behavioral test: with a wrong key, construction succeeds (no decryption
    happens) and only get() raises. This is the patent-relevant property
    -- see PATENT_NOTES.md P2-11.
    """

    def test_construction_with_wrong_key_does_not_raise(self, key):
        encrypted = Vault.encrypt_entries({"X": "secret"}, key)
        wrong_key = os.urandom(32)
        # Construction succeeds; failure deferred to access time.
        vault = Vault(encrypted, wrong_key)
        # And schema introspection still works:
        assert vault.has("X")
        # Only the actual decrypt path raises:
        with pytest.raises(VaultError):
            vault.get("X")
