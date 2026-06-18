"""Tests for the --scrub-traceback build-pass AST transformer."""

import sys
import textwrap

import pytest

from pyobfus_pro import generate_keypair, unscrub_error_id
from pyobfus_pro.transformers.scrub import (
    ScrubBuildError,
    load_or_generate_keypair,
    transform_module,
)


@pytest.fixture(scope="module")
def keypair():
    return generate_keypair(key_size=2048)


@pytest.fixture
def restore_excepthook():
    original = sys.excepthook
    yield
    sys.excepthook = original


def _src(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


class TestTransformInjection:
    def test_install_call_emitted_after_imports(self, keypair):
        _priv, pub = keypair
        src = _src("""
            import os
            from pathlib import Path

            def main():
                pass
        """)
        out = transform_module(src, pub)
        # The marker constant + install call should appear in the output.
        assert "_PYOBFUS_SCRUB_PUBLIC_KEY" in out
        assert "install_scrub_excepthook(_PYOBFUS_SCRUB_PUBLIC_KEY" in out
        # And it should be after the import lines but before `def main`.
        path_pos = out.find("from pathlib import Path")
        install_pos = out.find("install_scrub_excepthook(")
        def_pos = out.find("def main():")
        assert path_pos < install_pos < def_pos

    def test_install_call_uses_specified_prefix(self, keypair):
        _priv, pub = keypair
        src = _src("def main(): pass\n")
        out = transform_module(src, pub, prefix="MYAPP-ERR")
        assert "prefix='MYAPP-ERR'" in out

    def test_default_prefix_is_pyobfus_err(self, keypair):
        _priv, pub = keypair
        src = _src("def main(): pass\n")
        out = transform_module(src, pub)
        assert "prefix='PYOBFUS-ERR'" in out

    def test_module_with_no_imports_gets_install_at_top(self, keypair):
        _priv, pub = keypair
        src = "def main():\n    pass\n"
        out = transform_module(src, pub)
        install_pos = out.find("install_scrub_excepthook(")
        def_pos = out.find("def main():")
        assert 0 <= install_pos < def_pos


class TestIdempotency:
    def test_already_transformed_module_returns_unchanged(self, keypair):
        _priv, pub = keypair
        src = _src("""
            def main():
                pass
        """)
        once = transform_module(src, pub)
        twice = transform_module(once, pub)
        assert once == twice


class TestEndToEnd:
    def test_transformed_module_installs_excepthook(self, keypair, restore_excepthook):
        _priv, pub = keypair
        original_hook = sys.excepthook
        src = _src("def main(): pass\n")
        out = transform_module(src, pub)
        ns: dict = {}
        exec(compile(out, "<test>", "exec"), ns)  # noqa: S102
        assert sys.excepthook is not original_hook

    def test_transformed_module_excepthook_scrubs_real_exception(
        self, keypair, restore_excepthook, capsys
    ):
        priv, pub = keypair
        src = _src("def main(): pass\n")
        out = transform_module(src, pub, prefix="E2E-TEST")
        ns: dict = {}
        exec(compile(out, "<test>", "exec"), ns)  # noqa: S102

        try:
            raise ValueError("end-to-end secret detail")
        except ValueError as e:
            sys.excepthook(type(e), e, e.__traceback__)

        emitted = capsys.readouterr().err.strip()
        assert emitted.startswith("E2E-TEST:")
        assert "end-to-end secret detail" not in emitted

        recovered = unscrub_error_id(emitted, priv, prefix="E2E-TEST")
        assert "ValueError: end-to-end secret detail" in recovered


class TestKeypairFile:
    def test_generates_new_key_when_file_missing(self, tmp_path):
        path = tmp_path / "scrub.key.pem"
        priv, pub = load_or_generate_keypair(path, key_size=2048)
        assert path.exists()
        assert path.read_bytes() == priv
        assert pub.startswith(b"-----BEGIN PUBLIC KEY-----")

    def test_loads_existing_key_when_present(self, tmp_path):
        path = tmp_path / "scrub.key.pem"
        priv1, pub1 = load_or_generate_keypair(path, key_size=2048)
        priv2, pub2 = load_or_generate_keypair(path, key_size=2048)
        assert priv1 == priv2
        assert pub1 == pub2

    def test_regenerate_overwrites_existing(self, tmp_path):
        path = tmp_path / "scrub.key.pem"
        priv1, _pub1 = load_or_generate_keypair(path, key_size=2048)
        priv2, _pub2 = load_or_generate_keypair(path, key_size=2048, regenerate=True)
        assert priv1 != priv2
        assert path.read_bytes() == priv2

    def test_invalid_existing_key_raises(self, tmp_path):
        path = tmp_path / "scrub.key.pem"
        path.write_bytes(b"not a valid PEM")
        with pytest.raises(ScrubBuildError, match="not valid PEM"):
            load_or_generate_keypair(path)

    def test_keypair_pair_works_for_round_trip(self, tmp_path):
        from pyobfus_pro.runtime.scrub import scrub_traceback_text

        path = tmp_path / "scrub.key.pem"
        priv, pub = load_or_generate_keypair(path, key_size=2048)
        scrubbed = scrub_traceback_text("payload", pub)
        assert unscrub_error_id(scrubbed, priv) == "payload"
