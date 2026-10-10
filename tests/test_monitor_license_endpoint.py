"""Tests for scripts/monitor_license_endpoint.py, the scheduled probe of the
production licence endpoint. Not part of the pyobfus package, so it is
imported by file path. Every test stubs the network: nothing here contacts
the licence server or touches local licence state.
"""

from __future__ import annotations

import importlib.util
import io
import json
import urllib.error
from pathlib import Path
from typing import Any

import pytest

import pyobfus_pro.license as license_mod

_SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "monitor_license_endpoint.py"

WORKER_404 = json.dumps(
    {"valid": False, "code": "invalid_key", "error": "Invalid license key"}
).encode()


@pytest.fixture(scope="module")
def monitor() -> Any:
    spec = importlib.util.spec_from_file_location("monitor_license_endpoint", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _http_error(status: int, body: bytes) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://example.invalid/api/verify", status, "error", {}, io.BytesIO(body)  # type: ignore[arg-type]
    )


def _raw_response(monkeypatch: pytest.MonkeyPatch, monitor: Any, error: Exception) -> list:
    """Make the monitor's direct request raise ``error``; return captured requests."""
    seen: list = []

    def fake_urlopen(req: Any, timeout: float = 0) -> Any:
        seen.append(req)
        raise error

    monkeypatch.setattr(monitor.urllib.request, "urlopen", fake_urlopen)
    return seen


def _client_raises(monkeypatch: pytest.MonkeyPatch, exc: Exception) -> None:
    def fake_verify(key: str) -> dict:
        raise exc

    monkeypatch.setattr(license_mod, "_verify_online", fake_verify)


def _client_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    _client_raises(monkeypatch, license_mod.LicenseVerificationError("License key not found"))


def test_worker_json_404_is_healthy(monitor: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _client_not_found(monkeypatch)
    seen = _raw_response(monkeypatch, monitor, _http_error(404, WORKER_404))
    assert monitor.main() == 0
    # The direct request must look like the client's, or an edge rule keyed on
    # the User-Agent could treat the two differently.
    assert seen[0].get_header("User-agent") == license_mod.USER_AGENT
    assert json.loads(seen[0].data)["license_key"] == monitor.PROBE_KEY


def test_older_worker_without_code_field_is_healthy(
    monitor: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    _client_not_found(monkeypatch)
    body = json.dumps({"valid": False, "error": "Invalid license key"}).encode()
    _raw_response(monkeypatch, monitor, _http_error(404, body))
    assert monitor.main() == 0


@pytest.mark.parametrize(
    "body",
    [
        b"Not Found",
        b"<html><body><h1>404 Not Found</h1></body></html>",
        b"error code: 1042",
        json.dumps({"error": "route not found"}).encode(),
        b"[]",
    ],
    ids=["plain-text", "html", "edge-code", "other-json", "json-list"],
)
def test_404_not_from_worker_is_unhealthy(
    monitor: Any, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], body: bytes
) -> None:
    # The client reports every 404 as "License key not found", so before the
    # direct check these all passed as healthy.
    _client_not_found(monkeypatch)
    _raw_response(monkeypatch, monitor, _http_error(404, body))
    assert monitor.main() == 1
    assert "not from the licence server" in capsys.readouterr().out


def test_direct_request_blocked_is_unhealthy(monitor: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _client_not_found(monkeypatch)
    _raw_response(monkeypatch, monitor, _http_error(403, b"error code: 1010"))
    assert monitor.main() == 1


def test_direct_request_unreachable_is_unhealthy(
    monitor: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    _client_not_found(monkeypatch)
    _raw_response(monkeypatch, monitor, urllib.error.URLError("connection refused"))
    assert monitor.main() == 1


def test_client_edge_block_is_unhealthy(monitor: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    _client_raises(
        monkeypatch,
        license_mod.LicenseServerUnreachableError("blocked by the network (HTTP 403)"),
    )
    seen = _raw_response(monkeypatch, monitor, AssertionError("must not be called"))
    assert monitor.main() == 1
    assert seen == []


def test_nonexistent_key_accepted_is_unhealthy(
    monitor: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(license_mod, "_verify_online", lambda key: {"valid": True})
    assert monitor.main() == 1
