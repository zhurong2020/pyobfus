"""Tests for the developer-side ``pyobfus unscrub`` CLI.

The CLI wraps :func:`pyobfus_pro.runtime.scrub.unscrub_error_id` with
argparse + file IO + stdin / stdout plumbing. Tests drive ``main(argv)``
directly and capture stdout / stderr.
"""

import io
import sys
import textwrap

import pytest

from pyobfus_pro.unscrub import main
from pyobfus_pro.runtime.scrub import (
    generate_keypair,
    scrub_traceback_text,
)


# Test-only RSA key size: 1024 bits is fast enough for fixtures while still
# exercising the real RSA-OAEP code path. Production builds use 2048+.
@pytest.fixture(scope="module")
def keypair():
    return generate_keypair(key_size=1024)


@pytest.fixture
def private_key_file(tmp_path, keypair):
    private_pem, _ = keypair
    path = tmp_path / "test.key.pem"
    path.write_bytes(private_pem)
    return path


@pytest.fixture
def sample_traceback():
    return textwrap.dedent("""\
        Traceback (most recent call last):
          File "/app/main.py", line 42, in <module>
            do_thing()
          File "/app/main.py", line 17, in do_thing
            raise ValueError("internal detail")
        ValueError: internal detail
        """)


@pytest.fixture
def scrubbed_id(keypair, sample_traceback):
    _, public_pem = keypair
    return f"PYOBFUS-ERR:{scrub_traceback_text(sample_traceback, public_pem)}"


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestPositionalErrorId:
    def test_round_trip_decrypt_succeeds(
        self, capsys, private_key_file, sample_traceback, scrubbed_id
    ):
        rc = main(["--key", str(private_key_file), scrubbed_id])
        captured = capsys.readouterr()
        assert rc == 0
        assert sample_traceback.rstrip("\n") in captured.out
        assert captured.err == ""

    def test_decrypt_with_explicit_prefix_succeeds(
        self, capsys, private_key_file, sample_traceback, scrubbed_id
    ):
        rc = main(
            [
                "--key",
                str(private_key_file),
                "--prefix",
                "PYOBFUS-ERR",
                scrubbed_id,
            ]
        )
        assert rc == 0
        assert sample_traceback.rstrip("\n") in capsys.readouterr().out


class TestErrorIdFile:
    def test_decrypt_from_file(
        self, capsys, tmp_path, private_key_file, sample_traceback, scrubbed_id
    ):
        id_file = tmp_path / "id.txt"
        id_file.write_text(scrubbed_id, encoding="utf-8")
        rc = main(
            [
                "--key",
                str(private_key_file),
                "--error-id-file",
                str(id_file),
            ]
        )
        assert rc == 0
        assert sample_traceback.rstrip("\n") in capsys.readouterr().out

    def test_file_with_trailing_newline_handled(
        self, capsys, tmp_path, private_key_file, sample_traceback, scrubbed_id
    ):
        id_file = tmp_path / "id.txt"
        id_file.write_text(scrubbed_id + "\n\n", encoding="utf-8")
        rc = main(
            [
                "--key",
                str(private_key_file),
                "--error-id-file",
                str(id_file),
            ]
        )
        assert rc == 0
        assert sample_traceback.rstrip("\n") in capsys.readouterr().out


class TestStdin:
    def test_dash_reads_from_stdin(
        self,
        capsys,
        monkeypatch,
        private_key_file,
        sample_traceback,
        scrubbed_id,
    ):
        monkeypatch.setattr(sys, "stdin", io.StringIO(scrubbed_id))
        rc = main(["--key", str(private_key_file), "-"])
        assert rc == 0
        assert sample_traceback.rstrip("\n") in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


class TestDecryptFailures:
    def test_wrong_key_returns_exit_code_1(self, capsys, tmp_path, scrubbed_id):
        # Use a freshly generated key that does NOT match the encryption key
        bad_priv, _ = generate_keypair(key_size=1024)
        bad_key_file = tmp_path / "bad.key.pem"
        bad_key_file.write_bytes(bad_priv)

        rc = main(["--key", str(bad_key_file), scrubbed_id])
        captured = capsys.readouterr()
        assert rc == 1
        assert "decrypt failed" in captured.err

    def test_malformed_base64_returns_exit_code_1(self, capsys, private_key_file):
        malformed = "PYOBFUS-ERR:!!!not-base64!!!"
        rc = main(["--key", str(private_key_file), malformed])
        captured = capsys.readouterr()
        assert rc == 1
        assert "decrypt failed" in captured.err

    def test_prefix_mismatch_returns_exit_code_1(self, capsys, private_key_file, scrubbed_id):
        rc = main(
            [
                "--key",
                str(private_key_file),
                "--prefix",
                "OTHER-PREFIX",
                scrubbed_id,
            ]
        )
        captured = capsys.readouterr()
        assert rc == 1
        assert "prefix" in captured.err.lower()


# ---------------------------------------------------------------------------
# Usage / argument parsing
# ---------------------------------------------------------------------------


class TestUsageErrors:
    def test_missing_error_id_returns_exit_code_2(self, capsys, private_key_file):
        with pytest.raises(SystemExit) as exc:
            main(["--key", str(private_key_file)])
        assert exc.value.code == 2
        assert "required" in capsys.readouterr().err.lower()

    def test_positional_and_file_are_mutually_exclusive(
        self, capsys, tmp_path, private_key_file, scrubbed_id
    ):
        id_file = tmp_path / "id.txt"
        id_file.write_text(scrubbed_id, encoding="utf-8")
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "--key",
                    str(private_key_file),
                    "--error-id-file",
                    str(id_file),
                    scrubbed_id,
                ]
            )
        assert exc.value.code == 2
        assert "mutually exclusive" in capsys.readouterr().err.lower()

    def test_missing_key_argument_argparse_error(self, capsys, scrubbed_id):
        with pytest.raises(SystemExit):
            main([scrubbed_id])
        # argparse writes the usage error to stderr; we just confirm it ran.
        assert "key" in capsys.readouterr().err.lower()

    def test_unreadable_key_path_returns_exit_code_2(self, capsys, tmp_path, scrubbed_id):
        with pytest.raises(SystemExit) as exc:
            main(
                [
                    "--key",
                    str(tmp_path / "does-not-exist.pem"),
                    scrubbed_id,
                ]
            )
        assert exc.value.code == 2
        assert "cannot read --key" in capsys.readouterr().err

    def test_empty_error_id_returns_exit_code_2(self, capsys, monkeypatch, private_key_file):
        # Empty stdin -> "empty error ID" error (returned, not raised, by
        # the explicit branch in main()).
        monkeypatch.setattr(sys, "stdin", io.StringIO("   \n"))
        rc = main(["--key", str(private_key_file), "-"])
        assert rc == 2
        assert "empty" in capsys.readouterr().err.lower()
