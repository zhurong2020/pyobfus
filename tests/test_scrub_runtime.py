"""Runtime-side tests for --scrub-traceback (P2-10).

Build-pass AST transformer + CLI integration land in W2.
"""

import sys

import pytest

from pyobfus_pro import (
    ScrubError,
    generate_keypair,
    install_scrub_excepthook,
    unscrub_error_id,
)
from pyobfus_pro.runtime.scrub import scrub_traceback_text


@pytest.fixture(scope="module")
def keypair():
    """Module-scoped 2048-bit keypair: ~50ms once, then reused across tests."""
    return generate_keypair(key_size=2048)


@pytest.fixture
def restore_excepthook():
    """Restore sys.excepthook after a test that installs ours."""
    original = sys.excepthook
    yield
    sys.excepthook = original


class TestKeypair:
    def test_returns_pem_bytes(self, keypair):
        priv, pub = keypair
        assert priv.startswith(b"-----BEGIN PRIVATE KEY-----")
        assert pub.startswith(b"-----BEGIN PUBLIC KEY-----")


class TestRoundTrip:
    def test_short_payload(self, keypair):
        priv, pub = keypair
        scrubbed = scrub_traceback_text("test", pub)
        assert unscrub_error_id(scrubbed, priv) == "test"

    def test_long_payload(self, keypair):
        priv, pub = keypair
        payload = "x" * 10_000
        scrubbed = scrub_traceback_text(payload, pub)
        assert unscrub_error_id(scrubbed, priv) == payload

    def test_unicode_payload(self, keypair):
        priv, pub = keypair
        payload = "Traceback (most recent call last):\n  File '中文.py'..."
        scrubbed = scrub_traceback_text(payload, pub)
        assert unscrub_error_id(scrubbed, priv) == payload

    def test_each_scrub_is_distinct(self, keypair):
        """Same plaintext -> different ciphertexts (random nonce + AES key)."""
        priv, pub = keypair
        a = scrub_traceback_text("identical", pub)
        b = scrub_traceback_text("identical", pub)
        assert a != b
        assert unscrub_error_id(a, priv) == unscrub_error_id(b, priv) == "identical"


class TestPrefixHandling:
    def test_unscrub_strips_prefix_when_present(self, keypair):
        priv, pub = keypair
        scrubbed = scrub_traceback_text("data", pub)
        prefixed = f"PYOBFUS-ERR:{scrubbed}"
        assert unscrub_error_id(prefixed, priv) == "data"

    def test_unscrub_with_required_prefix_validates(self, keypair):
        priv, pub = keypair
        scrubbed = scrub_traceback_text("data", pub)
        prefixed = f"MY-APP:{scrubbed}"
        assert unscrub_error_id(prefixed, priv, prefix="MY-APP") == "data"
        with pytest.raises(ScrubError, match="prefix mismatch"):
            unscrub_error_id(prefixed, priv, prefix="PYOBFUS-ERR")

    def test_unscrub_requires_prefix_when_specified(self, keypair):
        priv, pub = keypair
        scrubbed = scrub_traceback_text("data", pub)
        with pytest.raises(ScrubError, match="missing required prefix"):
            unscrub_error_id(scrubbed, priv, prefix="MY-APP")


class TestFailureModes:
    def test_wrong_private_key_fails(self, keypair):
        _priv1, pub1 = keypair
        priv2, _pub2 = generate_keypair(key_size=2048)
        scrubbed = scrub_traceback_text("data", pub1)
        with pytest.raises(ScrubError, match="decrypt"):
            unscrub_error_id(scrubbed, priv2)

    def test_corrupted_blob_fails(self, keypair):
        priv, pub = keypair
        scrubbed = scrub_traceback_text("data", pub)
        # Flip a byte in the AES-GCM ciphertext region (near the end).
        flip_at = -10
        replacement = "A" if scrubbed[flip_at] != "A" else "B"
        corrupted = scrubbed[:flip_at] + replacement + scrubbed[flip_at + 1 :]
        with pytest.raises(ScrubError):
            unscrub_error_id(corrupted, priv)

    def test_invalid_base64_fails(self, keypair):
        priv, _pub = keypair
        with pytest.raises(ScrubError, match="not valid base64"):
            unscrub_error_id("!!! not valid base64 !!!", priv)

    def test_too_short_blob_fails(self, keypair):
        priv, _pub = keypair
        # "abc" base64-decodes to 2 bytes, less than nonce + key-length prefix
        with pytest.raises(ScrubError, match="too short"):
            unscrub_error_id("YWJj", priv)


class TestExcepthookInstall:
    def test_install_replaces_sys_excepthook(self, keypair, restore_excepthook):
        _priv, pub = keypair
        original = sys.excepthook
        install_scrub_excepthook(pub)
        assert sys.excepthook is not original

    def test_excepthook_emits_prefixed_id_without_leaking(
        self, keypair, restore_excepthook, capsys
    ):
        _priv, pub = keypair
        install_scrub_excepthook(pub, prefix="MY-PREFIX")

        try:
            raise ValueError("secret detail that must not leak")
        except ValueError as e:
            sys.excepthook(type(e), e, e.__traceback__)

        captured = capsys.readouterr()
        assert captured.err.startswith("MY-PREFIX:")
        assert "secret detail that must not leak" not in captured.err
        assert "ValueError" not in captured.err

    def test_excepthook_output_is_unscrubbable_by_dev(self, keypair, restore_excepthook, capsys):
        priv, pub = keypair
        install_scrub_excepthook(pub, prefix="MY-PREFIX")

        try:
            raise ValueError("secret detail that must not leak")
        except ValueError as e:
            sys.excepthook(type(e), e, e.__traceback__)

        emitted = capsys.readouterr().err.strip()
        recovered = unscrub_error_id(emitted, priv, prefix="MY-PREFIX")
        assert "ValueError: secret detail that must not leak" in recovered

    def test_excepthook_emits_failure_marker_on_bad_key(self, restore_excepthook, capsys):
        # Install with a malformed public key; on first exception, the hook
        # should emit a SCRUB_FAILED marker rather than the original trace.
        install_scrub_excepthook(b"not a real PEM", prefix="P")

        try:
            raise ValueError("must not leak even on internal failure")
        except ValueError as e:
            sys.excepthook(type(e), e, e.__traceback__)

        captured = capsys.readouterr()
        assert captured.err.strip() == "P:SCRUB_FAILED"
        assert "must not leak" not in captured.err
