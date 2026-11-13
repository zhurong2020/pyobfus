"""Strict, issuer-signed CI build admission. Proprietary; no workstation state.

Only the active build session retains approval. The signed response, nonce and
license reference never enter generated code, reports or persistent caches.
"""

import base64
import hashlib
import hmac
import json
import re
import time
from typing import Any, Dict, cast

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from jwt.algorithms import OKPAlgorithm
from jwt.api_jws import PyJWS

PROTOCOL = "pyobfus-ci-lease-v1"
ISSUER = "pyobfus-license"
AUDIENCE = "pyobfus:ci:build"
TOKEN_TYPE = "pyobfus-ci-lease+jwt"
MAX_LEASE_SECONDS = 300
CLOCK_SKEW_SECONDS = 60
MAX_RESPONSE_BYTES = 20 * 1024
MAX_TOKEN_BYTES = 16 * 1024

# Release gate: populate with reviewed issuer public keys before shipping a
# client that requires signed CI admission. Never trust an environment variable,
# token-supplied key/URL, or a synthetic test key here. Unknown keys fail closed.
TRUSTED_PUBLIC_KEYS: Dict[str, bytes] = {
    # Production issuer key provisioned 2026-11-11; JWK x = S32KKUFjobvQLXkIIuuw6YxSQqndPRj1MXFl-BHCeyU
    "ci-2026-11": (
        b"\x4b\x7d\x8a\x29\x41\x63\xa1\xbb\xd0\x2d\x79\x08\x22\xeb\xb0\xe9"
        b"\x8c\x52\x42\xa9\xdd\x3d\x18\xf5\x31\x71\x65\xf8\x11\xc2\x7b\x25"
    ),
    # Standby issuer key generated 2026-11-13; not configured on the Worker. Shipped in
    # advance so a later signer switch does not lock out clients that include it.
    # JWK x = EbCWYNYRI3lPiHlflUk5mvPOjR4FbH7j6ZC96NGSTbE
    "ci-2026-11b": (
        b"\x11\xb0\x96\x60\xd6\x11\x23\x79\x4f\x88\x79\x5f\x95\x49\x39\x9a"
        b"\xf3\xce\x8d\x1e\x05\x6c\x7e\xe3\xe9\x90\xbd\xe8\xd1\x92\x4d\xb1"
    ),
}

_SEGMENT = re.compile(r"[A-Za-z0-9_-]+\Z", re.ASCII)
_KID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z", re.ASCII)
_CLAIMS = {"v", "iss", "aud", "sub", "activation", "entitlements", "nonce", "iat", "nbf", "exp"}


class CILeaseError(ValueError):
    """Fixed diagnostic only: never include received bytes or private values."""

    def __init__(self) -> None:
        super().__init__("CI signed authorization is invalid or expired.")


class CILeaseUntrustedKeyError(CILeaseError):
    """Fixed upgrade diagnostic; admission remains denied."""

    def __init__(self) -> None:
        ValueError.__init__(
            self,
            "CI signed authorization uses an issuer key this pyobfus version does not "
            "trust; upgrade pyobfus (pip install -U pyobfus) and retry.",
        )


def _reject_constant(value: str) -> Any:
    raise CILeaseError()


def _unique_object(pairs: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CILeaseError()
        result[key] = value
    return result


def strict_json(data: bytes) -> Dict[str, Any]:
    """Bounded UTF-8 object; reject duplicate keys and non-JSON numeric values."""
    try:
        if len(data) > MAX_RESPONSE_BYTES:
            raise CILeaseError()
        result = json.loads(
            data.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_reject_constant
        )
        if not isinstance(result, dict):
            raise CILeaseError()
        return cast(Dict[str, Any], result)
    except Exception:
        raise CILeaseError() from None


def _segment(value: str, maximum: int) -> bytes:
    if not value or len(value) > maximum or not _SEGMENT.fullmatch(value):
        raise CILeaseError()
    decoded = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
    if base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii") != value:
        raise CILeaseError()
    return decoded


class _Ed25519Only(OKPAlgorithm):
    def prepare_key(self, key: Any) -> Ed25519PublicKey:
        # Verification accepts only a locally constructed public key. In
        # particular, never import a token-supplied JWK/private key or Ed448 key.
        if not isinstance(key, Ed25519PublicKey):
            raise CILeaseError()
        return key


def verify_response(response: Dict[str, Any], license_key: str, nonce: str) -> None:
    """Verify a v1 JWS and this request's admission claims, with no fallback."""
    try:
        if set(response) != {"protocol", "lease"} or response["protocol"] != PROTOCOL:
            raise CILeaseError()
        token = response["lease"]
        if not isinstance(token, str) or len(token) > MAX_TOKEN_BYTES:
            raise CILeaseError()
        parts = token.split(".")
        if len(parts) != 3:
            raise CILeaseError()
        header = strict_json(_segment(parts[0], 1024))
        payload = _segment(parts[1], MAX_TOKEN_BYTES)
        if len(_segment(parts[2], 86)) != 64:
            raise CILeaseError()
        if set(header) != {"alg", "typ", "kid"}:
            raise CILeaseError()
        if header["alg"] != "Ed25519" or header["typ"] != TOKEN_TYPE:
            raise CILeaseError()
        kid = header["kid"]
        if not isinstance(kid, str) or not _KID.fullmatch(kid):
            raise CILeaseError()
        if kid not in TRUSTED_PUBLIC_KEYS:
            # The unverified kid is attacker-controlled; this hint still denies admission.
            raise CILeaseUntrustedKeyError()
        raw_key = TRUSTED_PUBLIC_KEYS.get(kid)
        if not isinstance(raw_key, bytes) or len(raw_key) != 32:
            raise CILeaseError()
        engine = PyJWS(algorithms=[])
        engine.register_algorithm("Ed25519", _Ed25519Only())
        verified = engine.decode(
            token, Ed25519PublicKey.from_public_bytes(raw_key), algorithms=["Ed25519"]
        )
        if verified != payload:
            raise CILeaseError()
        claims = strict_json(payload)
        if set(claims) != _CLAIMS or type(claims["v"]) is not int or claims["v"] != 1:
            raise CILeaseError()
        if (
            claims["iss"] != ISSUER
            or claims["aud"] != AUDIENCE
            or claims["activation"] != "ci"
            or claims["entitlements"] != ["build:pro"]
        ):
            raise CILeaseError()
        expected_sub = "sha256:" + hashlib.sha256(license_key.encode("utf-8")).hexdigest()
        sub = claims["sub"]
        received_nonce = claims["nonce"]
        if (
            not isinstance(sub, str)
            or not isinstance(received_nonce, str)
            or len(_segment(received_nonce, 43)) != 32
            or not hmac.compare_digest(sub, expected_sub)
            or not hmac.compare_digest(received_nonce, nonce)
        ):
            raise CILeaseError()
        for field in ("iat", "nbf", "exp"):
            if type(claims[field]) is not int or not 0 <= claims[field] <= 2**53 - 1:
                raise CILeaseError()
        issued, not_before, expires = (claims[field] for field in ("iat", "nbf", "exp"))
        now = int(time.time())
        if (
            issued != not_before
            or not 0 < expires - issued <= MAX_LEASE_SECONDS
            or issued > now + CLOCK_SKEW_SECONDS
            or expires <= now - CLOCK_SKEW_SECONDS
        ):
            raise CILeaseError()
    except CILeaseUntrustedKeyError:
        raise
    except Exception:
        raise CILeaseError() from None
