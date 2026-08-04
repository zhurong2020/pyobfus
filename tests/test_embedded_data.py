"""Tests for P2-14 embedded-data runtime primitives.

``encrypt_data_file``/``get_embedded_data`` are the pure functions; build-
fusion injection (the actual ``--embed-data`` CLI flag) is exercised
end-to-end in test_build_fusion.py.
"""

import base64

import pytest

from pyobfus_pro import EmbeddedDataError, encrypt_data_file, get_embedded_data


class TestRoundTrip:
    def test_encrypt_then_decrypt_returns_original_bytes(self):
        key = b"\x01" * 32
        original = b"some binary resource file content \x00\xff\x10"
        blob = encrypt_data_file(original, key)
        blob_b85 = base64.b85encode(blob).decode("ascii")
        recovered = get_embedded_data(blob_b85, key)
        assert recovered == original

    def test_empty_bytes_round_trip(self):
        key = b"\x02" * 32
        blob = encrypt_data_file(b"", key)
        blob_b85 = base64.b85encode(blob).decode("ascii")
        assert get_embedded_data(blob_b85, key) == b""

    def test_different_nonce_each_call(self):
        # Same plaintext + key encrypted twice must produce different
        # ciphertexts (random nonce) -- prevents byte-equality leaking
        # "this file matches that file" to an attacker.
        key = b"\x03" * 32
        blob1 = encrypt_data_file(b"same content", key)
        blob2 = encrypt_data_file(b"same content", key)
        assert blob1 != blob2


class TestKeyValidation:
    def test_encrypt_rejects_short_key(self):
        with pytest.raises(EmbeddedDataError, match="32 bytes"):
            encrypt_data_file(b"data", b"too short")

    def test_decrypt_rejects_short_key(self):
        with pytest.raises(EmbeddedDataError, match="32 bytes"):
            get_embedded_data("doesn't matter", b"too short")


class TestTamperingAndCorruption:
    def test_wrong_key_raises(self):
        key = b"\x04" * 32
        wrong_key = b"\x05" * 32
        blob = encrypt_data_file(b"secret payload", key)
        blob_b85 = base64.b85encode(blob).decode("ascii")
        with pytest.raises(EmbeddedDataError, match="wrong key or tampered"):
            get_embedded_data(blob_b85, wrong_key)

    def test_tampered_ciphertext_raises(self):
        key = b"\x06" * 32
        blob = bytearray(encrypt_data_file(b"secret payload", key))
        blob[-1] ^= 0xFF  # flip a bit in the GCM tag
        blob_b85 = base64.b85encode(bytes(blob)).decode("ascii")
        with pytest.raises(EmbeddedDataError, match="wrong key or tampered"):
            get_embedded_data(blob_b85, key)

    def test_malformed_base85_raises(self):
        key = b"\x07" * 32
        with pytest.raises(EmbeddedDataError, match="not valid base85"):
            get_embedded_data("not valid base85 !!! @@@", key)

    def test_too_short_blob_raises(self):
        key = b"\x08" * 32
        short_blob_b85 = base64.b85encode(b"\x00\x01").decode("ascii")
        with pytest.raises(EmbeddedDataError, match="too short"):
            get_embedded_data(short_blob_b85, key)
