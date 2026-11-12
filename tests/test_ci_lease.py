"""Signed admission negative vectors, independent signatures and no state I/O."""

import io
import json
import secrets
import time
import urllib.error

import pytest

from pyobfus import _entitlement as gate
from pyobfus_pro import ci_lease
from pyobfus_pro import license as licensing

KEY = "PYOB-AAAA-BBBB-CCCC-DDDD"


def test_valid_and_nonce_license_binding(ci_issuer):
    nonce = secrets.token_urlsafe(32)
    response = ci_issuer.response(KEY, nonce)
    assert ci_lease.verify_response(response, KEY, nonce) is None
    for key, other_nonce in [
        (KEY, secrets.token_urlsafe(32)),
        (KEY.replace("AAAA", "EEEE"), nonce),
    ]:
        with pytest.raises(ci_lease.CILeaseError):
            ci_lease.verify_response(response, key, other_nonce)


@pytest.mark.parametrize(
    "field,value",
    [
        ("v", True),
        ("v", 2),
        ("iss", "wrong"),
        ("aud", [ci_lease.AUDIENCE]),
        ("activation", "offline"),
        ("entitlements", ["build:pro", "unknown"]),
        ("iat", True),
        ("nbf", 1.0),
        ("exp", float("inf")),
        ("exp", "300"),
        ("sub", []),
        ("nonce", "not-a-nonce"),
    ],
)
def test_claim_types_and_purpose(ci_issuer, field, value):
    nonce = secrets.token_urlsafe(32)
    claims = ci_issuer.claims(KEY, nonce)
    claims[field] = value
    with pytest.raises(ci_lease.CILeaseError):
        ci_lease.verify_response(ci_issuer.response(KEY, nonce, payload=claims), KEY, nonce)


@pytest.mark.parametrize(
    "changes",
    [
        {"exp": 939, "iat": 639, "nbf": 639},  # one second outside allowed skew
        {"exp": 940, "iat": 640, "nbf": 640},  # exact expiry boundary
        {"iat": 1061, "nbf": 1061, "exp": 1361},
        {"iat": 1000, "nbf": 1001, "exp": 1300},
        {"iat": 1000, "nbf": 1000, "exp": 1301},
        {"iat": 1000, "nbf": 1000, "exp": 1000},
        {"iat": -1, "nbf": -1, "exp": 299},
    ],
)
def test_time_boundaries(ci_issuer, monkeypatch, changes):
    monkeypatch.setattr(ci_lease.time, "time", lambda: 1000)
    nonce = secrets.token_urlsafe(32)
    claims = ci_issuer.claims(KEY, nonce)
    claims.update(changes)
    with pytest.raises(ci_lease.CILeaseError):
        ci_lease.verify_response(ci_issuer.response(KEY, nonce, payload=claims), KEY, nonce)


@pytest.mark.parametrize(
    "header",
    [
        {"alg": "none"},
        {"alg": "HS256"},
        {"alg": "EdDSA"},
        {"kid": "unknown"},
        {"kid": []},
        {"kid": "../key"},
        {"typ": "workstation+jwt"},
        {"jku": "https://invalid.example/key"},
        {"jwk": {}},
        {"crit": []},
        {"b64": False},
    ],
)
def test_header_policy(ci_issuer, header):
    nonce = secrets.token_urlsafe(32)
    with pytest.raises(ci_lease.CILeaseError):
        ci_lease.verify_response(ci_issuer.response(KEY, nonce, header=header), KEY, nonce)


def test_key_rotation_and_no_environment_override(ci_issuer, monkeypatch):
    nonce = secrets.token_urlsafe(32)
    response = ci_issuer.response(KEY, nonce)
    monkeypatch.setattr(ci_lease, "TRUSTED_PUBLIC_KEYS", {"other-key": ci_issuer.public})
    monkeypatch.setenv("PYOBFUS_CI_PUBLIC_KEY", ci_issuer.public.hex())
    with pytest.raises(ci_lease.CILeaseError):
        ci_lease.verify_response(response, KEY, nonce)


@pytest.mark.parametrize(
    "data", [b'{"a":1,"a":2}', b'{"a":NaN}', b"[]", b"null", b'"text"', b"\xff", b"[" * 2000]
)
def test_strict_json(data):
    with pytest.raises(ci_lease.CILeaseError):
        ci_lease.strict_json(data)


def test_signed_duplicate_keys_and_payload_shape(ci_issuer):
    nonce = secrets.token_urlsafe(32)
    for payload in [b'{"v":1,"v":1}', b"[]", b'{"exp":NaN}']:
        with pytest.raises(ci_lease.CILeaseError):
            ci_lease.verify_response(
                ci_issuer.response(KEY, nonce, payload_bytes=payload), KEY, nonce
            )
    with pytest.raises(ci_lease.CILeaseError):
        ci_lease.verify_response(
            ci_issuer.response(KEY, nonce, header_bytes=b'{"alg":"none","alg":"Ed25519"}'),
            KEY,
            nonce,
        )


def test_signature_and_size_failures(ci_issuer):
    nonce = secrets.token_urlsafe(32)
    response = ci_issuer.response(KEY, nonce)
    token = response["lease"]
    variants = [
        token + "=",
        token + ".x",
        "x" * (ci_lease.MAX_TOKEN_BYTES + 1),
        token.replace(token.split(".")[1], "e30"),
    ]
    for variant in variants:
        with pytest.raises(ci_lease.CILeaseError):
            ci_lease.verify_response({**response, "lease": variant}, KEY, nonce)


def test_bounded_network_read_and_no_unsigned_fallback(monkeypatch):
    class LargeResponse(io.BytesIO):
        def read(self, size=-1):
            assert size == ci_lease.MAX_RESPONSE_BYTES + 1
            return b"x" * size

    monkeypatch.setattr(licensing.urllib.request, "urlopen", lambda *a, **kw: LargeResponse())
    with pytest.raises(licensing.LicenseVerificationError):
        licensing.verify_ci_license(KEY)


def test_build_admission_outlives_token_but_not_session(monkeypatch, ci_issuer):
    clock = int(time.time())
    monkeypatch.setattr(ci_lease.time, "time", lambda: clock)
    monkeypatch.setenv("PYOBFUS_LICENSE_KEY", KEY)
    calls = []

    def response(req, **kwargs):
        body = json.loads(req.data)
        calls.append(body["nonce"])
        return io.BytesIO(json.dumps(ci_issuer.response(KEY, body["nonce"])).encode())

    monkeypatch.setattr(licensing.urllib.request, "urlopen", response)
    with gate.entitlement_session():
        gate.require_pro_access()
        clock += 1000
        gate.require_pro_access()
        assert len(calls) == 1
    with gate.entitlement_session():
        gate.require_pro_access()
    assert len(calls) == 2 and calls[0] != calls[1]


def test_unsigned_old_response_denied(monkeypatch):
    monkeypatch.setattr(
        licensing.urllib.request,
        "urlopen",
        lambda *a, **kw: io.BytesIO(b'{"valid":true,"activation":"ci"}'),
    )
    with pytest.raises(licensing.LicenseVerificationError, match="signed authorization"):
        licensing.verify_ci_license(KEY)


@pytest.mark.parametrize(
    "status,body,diagnostic",
    [
        (404, b"Not Found", "does not support signed"),
        (404, b'{"code":"invalid_key"}', "denied"),
        (503, b"private server details", "unavailable"),
        (429, b"private server details", "rate limited"),
    ],
)
def test_http_denial_never_retries_unsigned(monkeypatch, status, body, diagnostic):
    calls = []

    def reject(req, **kwargs):
        calls.append(req.full_url)
        raise urllib.error.HTTPError(req.full_url, status, KEY, {}, io.BytesIO(body))

    monkeypatch.setattr(licensing.urllib.request, "urlopen", reject)
    with pytest.raises(licensing.LicenseVerificationError, match=diagnostic) as error:
        licensing.verify_ci_license(KEY)
    assert KEY not in str(error.value) and "private server details" not in str(error.value)
    assert calls == [licensing.CI_LEASE_API_URL]


def test_release_key_gate_is_static_and_rejects_empty_table(tmp_path, ci_issuer):
    from scripts.check_ci_lease_keys import check

    source = tmp_path / "ci_lease.py"
    source.write_text("TRUSTED_PUBLIC_KEYS: dict = {}\n")
    assert not check(source)
    source.write_text("TRUSTED_PUBLIC_KEYS: dict = " + repr({"issuer": ci_issuer.public}) + "\n")
    assert check(source)
    source.write_text("TRUSTED_PUBLIC_KEYS: dict = " + repr({"issuer": b"short"}) + "\n")
    assert not check(source)
    # A source expression is not executed while checking a publish prerequisite.
    source.write_text("TRUSTED_PUBLIC_KEYS: dict = dict()\n")
    assert not check(source)


@pytest.mark.parametrize("signature", ["other-key", "zero"])
def test_untrusted_signatures_under_trusted_kid(ci_issuer, signature):
    import base64
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    nonce = secrets.token_urlsafe(32)
    response = ci_issuer.response(KEY, nonce)
    header, payload, _ = response["lease"].split(".")
    message = f"{header}.{payload}".encode()
    sig = Ed25519PrivateKey.generate().sign(message) if signature == "other-key" else bytes(64)
    response["lease"] = message.decode() + "." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    with pytest.raises(ci_lease.CILeaseError):
        ci_lease.verify_response(response, KEY, nonce)


@pytest.mark.parametrize("now,accepted", [(940, True), (939, False), (1359, True), (1360, False)])
def test_skew_edges(ci_issuer, monkeypatch, now, accepted):
    monkeypatch.setattr(ci_lease.time, "time", lambda: 1000)
    nonce = secrets.token_urlsafe(32)
    response = ci_issuer.response(KEY, nonce)
    monkeypatch.setattr(ci_lease.time, "time", lambda: now)
    if accepted:
        assert ci_lease.verify_response(response, KEY, nonce) is None
    else:
        with pytest.raises(ci_lease.CILeaseError):
            ci_lease.verify_response(response, KEY, nonce)


@pytest.mark.parametrize("failure", ["timeout", "read", "truncated", "dependency"])
def test_ci_failure_denies_without_state_or_trial(monkeypatch, failure):
    import builtins
    import sys
    import pyobfus_pro

    def forbidden(*args, **kwargs):
        pytest.fail("CI accessed local state or trial")

    for name in [
        "get_license_status",
        "load_cached_license",
        "cache_license",
        "get_device_fingerprint",
    ]:
        monkeypatch.setattr(licensing, name, forbidden)
    monkeypatch.setattr("pyobfus.trial.is_trial_active", forbidden)
    monkeypatch.setenv("PYOBFUS_LICENSE_KEY", KEY)
    calls = []

    class BrokenRead(io.BytesIO):
        def read(self, size=-1):
            raise OSError(KEY)

    def open_request(*args, **kwargs):
        calls.append(1)
        if failure == "timeout":
            raise TimeoutError(KEY)
        return BrokenRead() if failure == "read" else io.BytesIO(b'{"lease":')

    monkeypatch.setattr(licensing.urllib.request, "urlopen", open_request)
    if failure == "dependency":
        monkeypatch.delitem(sys.modules, "pyobfus_pro.ci_lease")
        monkeypatch.delattr(pyobfus_pro, "ci_lease")
        original_import = builtins.__import__

        def unavailable(name, *args, **kwargs):
            if name.startswith("cryptography"):
                raise ImportError("cryptography " + KEY)
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", unavailable)
    expected = {
        "timeout": "CI license verification unavailable; online access is required.",
        "read": "CI license verification unavailable; online access is required.",
        "truncated": "CI signed authorization is invalid or expired.",
        "dependency": "CI signing dependencies unavailable; reinstall pyobfus.",
    }[failure]
    with pytest.raises(licensing.LicenseVerificationError) as error:
        licensing.verify_ci_license(KEY)
    assert str(error.value) == expected
    with pytest.raises(gate.ProAccessError) as error:
        gate.require_pro_access()
    assert str(error.value) == expected + " Check PYOBFUS_LICENSE_KEY or use a registered runner."
    assert len(calls) == (0 if failure == "dependency" else 2)
