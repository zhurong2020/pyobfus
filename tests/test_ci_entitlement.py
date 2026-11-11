"""Build lifetime and online-only CI licensing regressions (synthetic keys)."""

import asyncio
from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
import io
import json
import multiprocessing
import urllib.error
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from pyobfus import _entitlement as gate
from pyobfus.cli import main
from pyobfus.config import ObfuscationConfig
from pyobfus.core import orchestrator
from pyobfus_pro import license as licensing

KEY = "PYOB-AAAA-BBBB-CCCC-DDDD"


@pytest.mark.parametrize("exception", [False, True])
def test_copied_context_expires(monkeypatch, exception):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: True)
    try:
        with gate.entitlement_session():
            gate.require_pro_access()
            context = copy_context()
            if exception:
                raise RuntimeError("exit")
    except RuntimeError:
        pass
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    monkeypatch.setattr(licensing, "get_license_status", lambda **kw: None)
    with pytest.raises(gate.ProAccessError):
        context.run(gate.require_pro_access)


@pytest.mark.parametrize("after_exit", [False, True])
def test_foreign_thread_denied(monkeypatch, after_exit):
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: True)

    def check(context):
        monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
        monkeypatch.setattr(licensing, "get_license_status", lambda **kw: None)
        with ThreadPoolExecutor(1) as pool:
            with pytest.raises(gate.ProAccessError):
                pool.submit(context.run, gate.require_pro_access).result()

    with gate.entitlement_session():
        gate.require_pro_access()
        context = copy_context()
        if not after_exit:
            check(context)
    if after_exit:
        check(context)


def test_copied_task_denied(monkeypatch):
    async def run():
        ready = asyncio.Event()

        async def child():
            await ready.wait()
            gate.require_pro_access()

        with gate.entitlement_session():
            gate.require_pro_access()
            task = asyncio.create_task(child())
        monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
        monkeypatch.setattr(licensing, "get_license_status", lambda **kw: None)
        ready.set()
        with pytest.raises(gate.ProAccessError):
            await task

    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: True)
    asyncio.run(run())


def _isolated_pool_initializer(capability):
    """A regression must fail locally rather than contact the live service."""

    def unexpected_verification(*args, **kwargs):
        raise AssertionError("worker attempted an independent verification")

    licensing.verify_license = unexpected_verification
    licensing.verify_ci_license = unexpected_verification
    orchestrator._init_build_worker(capability)


@pytest.mark.parametrize("method", ["spawn", "forkserver"])
@pytest.mark.parametrize("mode", ["registered", "ci"])
def test_owned_pool_verifies_once(tmp_path, monkeypatch, method, mode, ci_issuer):
    if method not in multiprocessing.get_all_start_methods():
        pytest.skip("start method unavailable")
    from concurrent.futures import ProcessPoolExecutor

    monkeypatch.setattr(
        orchestrator,
        "ProcessPoolExecutor",
        lambda **kw: ProcessPoolExecutor(
            mp_context=multiprocessing.get_context(method),
            **{**kw, "initializer": _isolated_pool_initializer},
        ),
    )
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    monkeypatch.setattr(licensing, "get_license_status", lambda **kw: {"key": KEY})
    licensing.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    licensing.CACHE_FILE.write_text(
        json.dumps({"key": KEY, "type": "pro", "expires": "2099-12-31", "verified": "2020-01-01"})
    )
    online = Mock(side_effect=licensing.LicenseServerUnreachableError("offline"))
    monkeypatch.setattr(licensing, "_verify_online", online)
    if mode == "ci":
        monkeypatch.setenv("PYOBFUS_LICENSE_KEY", KEY)
        online = Mock(
            side_effect=lambda req, **kw: io.BytesIO(
                json.dumps(ci_issuer.response(KEY, json.loads(req.data)["nonce"])).encode()
            )
        )
        monkeypatch.setattr(licensing.urllib.request, "urlopen", online)
    src = tmp_path / "src"
    src.mkdir()
    for n in range(3):
        (src / f"mod{n}.py").write_text('print("hello")\n')
    for n in range(2):
        result = orchestrator.CrossFileOrchestrator(
            ObfuscationConfig(level="pro", string_encryption=True, max_workers=2)
        ).obfuscate(src, tmp_path / f"out{n}")
        assert not result.errors
        assert online.call_count == n + 1
    monkeypatch.delenv("PYOBFUS_LICENSE_KEY", raising=False)
    monkeypatch.setattr(licensing, "get_license_status", lambda **kw: None)
    with pytest.raises(gate.ProAccessError):
        orchestrator.CrossFileOrchestrator(
            ObfuscationConfig(level="pro", string_encryption=True, max_workers=2)
        ).obfuscate(src, tmp_path / "denied")
    assert not (tmp_path / "denied").exists()


@pytest.mark.parametrize("failure", [None, "network", 400, 403, 429, "invalid", "expired"])
def test_ci_online_only_and_secret_safe(tmp_path, monkeypatch, capsys, failure, ci_issuer):
    monkeypatch.setenv("PYOBFUS_LICENSE_KEY", KEY)
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: True)

    def forbidden(*args, **kwargs):
        raise AssertionError("CI must not access registration or device state")

    for name in [
        "get_license_status",
        "load_cached_license",
        "cache_license",
        "get_device_fingerprint",
    ]:
        monkeypatch.setattr(licensing, name, forbidden)

    calls = []

    def open_request(req, **kw):
        calls.append(json.loads(req.data))
        assert req.full_url == licensing.CI_LEASE_API_URL
        assert set(calls[-1]) == {"license_key", "activation", "protocol", "nonce"}
        assert calls[-1]["license_key"] == KEY and calls[-1]["activation"] == "ci"
        if failure == "network":
            raise urllib.error.URLError(KEY)
        if isinstance(failure, int):
            raise urllib.error.HTTPError(
                req.full_url,
                failure,
                KEY,
                {},
                io.BytesIO(json.dumps({"error": "Missing license_key or device_id"}).encode()),
            )
        nonce = calls[-1]["nonce"]
        payload = ci_issuer.claims(KEY, nonce)
        if failure == "expired":
            payload.update(iat=0, nbf=0, exp=300)
        envelope = ci_issuer.response(KEY, nonce, payload=payload)
        if failure == "invalid":
            envelope = {"valid": True, "activation": "ci"}
        return io.BytesIO(json.dumps(envelope).encode())

    monkeypatch.setattr(licensing.urllib.request, "urlopen", open_request)
    src = tmp_path / "input.py"
    src.write_text('print("hello")\n')
    result = CliRunner().invoke(
        main, [str(src), "-o", str(tmp_path / "out.py"), "--string-encryption", "--json"]
    )
    assert result.exit_code == (1 if failure else 0), result.output
    assert len(calls) == 1
    assert KEY not in result.output + str(result.exception) + str(capsys.readouterr())
    assert calls[0]["nonce"] not in result.output
    if failure == 400:
        assert "does not support signed CI activation yet" in result.output
    if failure == 429:
        assert "rate limited" in result.output


def test_ci_bad_format_hidden(monkeypatch):
    monkeypatch.setenv("PYOBFUS_LICENSE_KEY", "synthetic-private-value")
    with pytest.raises(gate.ProAccessError) as exc:
        gate.require_pro_access()
    assert "synthetic-private-value" not in str(exc.value)


@pytest.mark.parametrize("value", [" \n" + KEY + "\r\n ", " \t\r\n"])
def test_ci_key_whitespace(monkeypatch, value):
    monkeypatch.setenv("PYOBFUS_LICENSE_KEY", value)
    monkeypatch.setattr("pyobfus.trial.is_trial_active", lambda: False)
    verify = Mock()
    monkeypatch.setattr(licensing, "verify_ci_license", verify)
    registered = Mock(return_value={"key": KEY})
    monkeypatch.setattr(licensing, "get_license_status", registered)
    monkeypatch.setattr(licensing, "verify_license", Mock(return_value={"valid": True}))
    gate.require_pro_access()
    if value.strip():
        verify.assert_called_once_with(KEY)
        registered.assert_not_called()
    else:
        verify.assert_not_called()
        registered.assert_called_once()
