"""Application-supplied key provider (Y-3).

An artifact built with ``--bind-key-env NAME`` calls ``provided_key("NAME")``
at import. The key comes from a registered provider (preferred) or the named
environment variable (base64), and must be exactly 32 bytes; anything else
raises ``LicenseBindingError`` so a missing key fails loudly.
"""

from __future__ import annotations

import base64

import pytest

from pyobfus_runtime import provided_key, set_key_provider
from pyobfus_runtime.binding import LicenseBindingError

KEY = b"k" * 32
KEY_B64 = base64.b64encode(KEY).decode()
ENV = "PYOBFUS_TEST_L3_KEY"


@pytest.fixture(autouse=True)
def _clear_provider():
    # Never leak provider state between tests (it is process-global).
    set_key_provider(None)
    yield
    set_key_provider(None)


def test_env_var_channel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV, KEY_B64)
    assert provided_key(ENV) == KEY


def test_registered_provider_takes_precedence(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV, KEY_B64)
    set_key_provider(lambda: b"p" * 32)
    assert provided_key(ENV) == b"p" * 32


def test_registered_provider_without_env() -> None:
    set_key_provider(lambda: KEY)
    assert provided_key("UNSET_VARIABLE_NAME") == KEY


def test_unset_and_unregistered_raises() -> None:
    with pytest.raises(LicenseBindingError) as exc:
        provided_key("DEFINITELY_UNSET_VAR_XYZ")
    assert "set_key_provider" in str(exc.value)


def test_undecodable_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV, "not!valid!base64!")
    with pytest.raises(LicenseBindingError) as exc:
        provided_key(ENV)
    assert "base64" in str(exc.value)


def test_wrong_length_env_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV, base64.b64encode(b"short").decode())
    with pytest.raises(LicenseBindingError) as exc:
        provided_key(ENV)
    assert "32 bytes" in str(exc.value)


def test_provider_returning_wrong_length_raises() -> None:
    set_key_provider(lambda: b"tooshort")
    with pytest.raises(LicenseBindingError) as exc:
        provided_key("IGNORED")
    assert "32 bytes" in str(exc.value)


def test_provider_returning_non_bytes_raises() -> None:
    set_key_provider(lambda: "a string, not bytes")  # type: ignore[arg-type,return-value]
    with pytest.raises(LicenseBindingError) as exc:
        provided_key("IGNORED")
    assert "bytes" in str(exc.value)


def test_non_callable_provider_rejected() -> None:
    with pytest.raises(LicenseBindingError):
        set_key_provider(b"not callable")  # type: ignore[arg-type]


def test_bytearray_key_is_accepted_and_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    set_key_provider(lambda: bytearray(KEY))
    result = provided_key("IGNORED")
    assert result == KEY
    assert isinstance(result, bytes)
