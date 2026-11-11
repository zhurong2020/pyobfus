"""Shared test isolation.

Trial status, license caches and the device identifier live under the caller's
home directory, where a test could quietly read, create or overwrite them. Tests
must never touch a developer's own pyobfus state, so bind it to pytest's
per-test directory everywhere, not only in the test modules that happen to
think about licences.
"""

from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def isolated_device_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import pyobfus.trial as trial

    # CLI/generated-code subprocesses must inherit an isolated home too.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    state_dir = tmp_path / ".pyobfus"
    monkeypatch.setattr(trial, "TRIAL_DIR", state_dir)
    monkeypatch.setattr(trial, "TRIAL_FILE", state_dir / "trial.json")
    try:
        import pyobfus_pro.license as license_module
        import pyobfus_pro.fingerprint as fingerprint
    except ImportError:  # pragma: no cover - Pro edition not installed
        return

    monkeypatch.setattr(license_module, "CACHE_DIR", state_dir)
    monkeypatch.setattr(license_module, "CACHE_FILE", state_dir / "license.json")
    device_file = state_dir / "device_id"
    monkeypatch.setattr(fingerprint, "DEVICE_ID_FILE", device_file)
    assert fingerprint.DEVICE_ID_FILE.is_relative_to(tmp_path)


@pytest.fixture
def active_pro_trial(isolated_device_id):
    """Explicit authorization for transform tests, including spawned builders."""
    from pyobfus.trial import start_trial

    assert start_trial()["success"]


@pytest.fixture
def ci_issuer(monkeypatch):
    """Independent ephemeral JWS signer; no private key committed or persisted."""
    import base64
    import hashlib
    import json
    import time
    from types import SimpleNamespace

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from pyobfus_pro import ci_lease

    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw
    )
    monkeypatch.setattr(ci_lease, "TRUSTED_PUBLIC_KEYS", {"test-issuer": public})

    def claims(license_key, nonce):
        now = int(time.time())
        return {
            "v": 1,
            "iss": ci_lease.ISSUER,
            "aud": ci_lease.AUDIENCE,
            "sub": "sha256:" + hashlib.sha256(license_key.encode()).hexdigest(),
            "activation": "ci",
            "entitlements": ["build:pro"],
            "nonce": nonce,
            "iat": now,
            "nbf": now,
            "exp": now + 300,
        }

    def response(
        license_key, nonce, *, payload=None, header=None, payload_bytes=None, header_bytes=None
    ):
        def encode(raw):
            return base64.urlsafe_b64encode(raw).rstrip(b"=")

        h = {"alg": "Ed25519", "typ": ci_lease.TOKEN_TYPE, "kid": "test-issuer"}
        h.update(header or {})
        p = claims(license_key, nonce) if payload is None else payload
        message = (
            encode(header_bytes if header_bytes is not None else json.dumps(h).encode())
            + b"."
            + encode(payload_bytes if payload_bytes is not None else json.dumps(p).encode())
        )
        token = message + b"." + encode(key.sign(message))
        return {"protocol": ci_lease.PROTOCOL, "lease": token.decode()}

    return SimpleNamespace(claims=claims, response=response, public=public)
