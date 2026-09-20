"""Tests for the server-registered (opt-in --email) trial path."""

import json
import sys
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path

import pytest

import pyobfus.trial as trial_module
from pyobfus.trial import _parse_server_iso, _request_online_trial, start_trial


@pytest.fixture(autouse=True)
def isolated_trial_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trial_dir = tmp_path / ".pyobfus"
    monkeypatch.setattr(trial_module, "TRIAL_DIR", trial_dir)
    monkeypatch.setattr(trial_module, "TRIAL_FILE", trial_dir / "trial.json")
    assert trial_module.TRIAL_FILE.is_relative_to(tmp_path)


def _iso_z(dt: datetime) -> str:
    """Emit a UTC 'Z' timestamp the way the Worker's toISOString() does."""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def test_parse_server_iso_handles_trailing_Z_on_all_supported_pythons():
    # datetime.fromisoformat can't take a bare 'Z' on 3.9/3.10 — this must still work.
    parsed = _parse_server_iso("2026-09-25T12:00:00.000Z")
    assert parsed.tzinfo is None  # normalized to naive local for comparison
    # round-trips as a naive isoformat that get_trial_status can parse
    assert datetime.fromisoformat(parsed.isoformat())


def test_start_trial_with_email_issued(monkeypatch):
    now = datetime.now()
    expires = now + timedelta(days=5)
    monkeypatch.setattr(
        trial_module, "_request_online_trial",
        lambda email, device_id, timeout=10.0: {
            "status": "issued", "active": True,
            "started": _iso_z(now), "expires": _iso_z(expires),
            "token": "a" * 64,
        },
    )
    result = start_trial(email="you@example.com")
    assert result["success"] is True
    assert result["registered"] is True
    saved = json.loads(trial_module.TRIAL_FILE.read_text())
    assert saved["token"] == "a" * 64
    assert saved["email"] == "you@example.com"
    assert saved["v"] == 2
    assert trial_module.is_trial_active() is True


def test_start_trial_email_already_used_is_refused_without_local_grant(monkeypatch):
    monkeypatch.setattr(
        trial_module, "_request_online_trial",
        lambda email, device_id, timeout=10.0: {
            "status": "already_issued", "active": False,
            "expires": "2020-01-01T00:00:00.000Z",
            "message": "This email has already used its trial.",
        },
    )
    result = start_trial(email="used@example.com")
    assert result["success"] is False
    assert result["registered"] is True
    # dedup respected: no local trial file was written to hand out a fresh 5 days
    assert not trial_module.TRIAL_FILE.exists()
    assert trial_module.is_trial_active() is False


def test_start_trial_email_offline_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(
        trial_module, "_request_online_trial",
        lambda email, device_id, timeout=10.0: None,  # server unreachable
    )
    result = start_trial(email="offline@example.com")
    assert result["success"] is True
    assert result["registered"] is False
    assert "note" in result
    saved = json.loads(trial_module.TRIAL_FILE.read_text())
    assert "token" not in saved  # local-only record
    assert trial_module.is_trial_active() is True


def test_no_email_makes_no_network_call(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("network must not be touched without --email")
    monkeypatch.setattr(trial_module, "_request_online_trial", _boom)
    result = start_trial()  # no email
    assert result["success"] is True
    assert "registered" not in result


def test_request_online_trial_sets_explicit_user_agent(monkeypatch):
    """Regression guard: the Cloudflare edge rejects urllib's default UA
    (403 / error code 1010). Every request from this package must carry an
    explicit pyobfus User-Agent."""
    captured = {}

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return json.dumps({"status": "issued", "active": True}).encode()

    def fake_urlopen(request, timeout=None):
        captured["ua"] = request.headers.get("User-agent")
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        return _Resp()

    monkeypatch.setattr(trial_module.urllib.request, "urlopen", fake_urlopen)
    out = _request_online_trial("a@b.co", "dev-1")
    assert out["status"] == "issued"
    assert captured["ua"] and captured["ua"].startswith("pyobfus/")
    assert "Python-urllib" not in captured["ua"]
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/api/trial/request")


def test_request_online_trial_returns_none_on_network_error(monkeypatch):
    def fake_urlopen(request, timeout=None):
        raise urllib.error.URLError("unreachable")
    monkeypatch.setattr(trial_module.urllib.request, "urlopen", fake_urlopen)
    assert _request_online_trial("a@b.co", "dev-1") is None
