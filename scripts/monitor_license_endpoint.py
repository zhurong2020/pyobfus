#!/usr/bin/env python3
"""Synthetic monitor for the production licence-verification endpoint.

Why this exists
---------------
Between 2026-07-08 and 2026-09-12 every Pro licence activation failed and
nobody noticed. Cloudflare's edge began rejecting urllib's default
``Python-urllib/X.Y`` User-Agent with HTTP 403 and a plain-text
``error code: 1010`` body, so requests never reached the Worker. The outage
surfaced only when a paying customer wrote in, two months later.

What it checks
--------------
It drives the *real client code path* (``pyobfus_pro.license._verify_online``)
rather than reimplementing the request. A reimplementation drifts from the
client and stops reflecting what customers actually send; this cannot, because
it is the same function, with the same headers and the same User-Agent.

It probes with a deliberately nonexistent licence key, so it has no side
effects at all: it touches no customer record, consumes none of anyone's three
device slots, and needs no real licence key in CI secrets. A healthy server
answers with its own JSON 404. Anything else, a plain-text edge block, an
unparseable body, a connection failure, means customers cannot activate.

The client maps *any* HTTP 404 to "License key not found" without reading the
body, so the client path alone would also pass a 404 from a missing Worker
route or from a proxy. A second request with the same User-Agent therefore
checks that the 404 body is the Worker's own JSON (found in review on
2026-10-11).

It covers the rejection path only: it does not prove that a valid key can
activate.

Exit codes: 0 healthy, 1 unhealthy.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# Format-valid (PYOB + four hex groups) so it passes client-side validation and
# actually reaches the network. Never generated in practice: keys are random
# hex, and an all-zero draw is ~1 in 2**64.
PROBE_KEY = "PYOB-0000-0000-0000-0000"

# What a healthy server says about a key it does not have. The Worker answers
# HTTP 404 with {"valid": false, "error": "Invalid license key"}, which the
# client surfaces as this message.
HEALTHY_MESSAGE = "License key not found"

# The Worker's machine-readable reason for an unknown key, and the text it sent
# before the ``code`` field existed.
WORKER_CODE = "invalid_key"
WORKER_ERROR = "Invalid license key"


def check_worker_404(url: str, user_agent: str, timeout: float = 15.0) -> tuple[bool, str]:
    """Ask for the unknown key directly and check the Worker itself said 404.

    Returns ``(healthy, detail)``. Sends the same headers as the client, so an
    edge rule keyed on the User-Agent treats both requests alike.
    """
    payload = json.dumps({"license_key": PROBE_KEY, "device_id": "monitor-probe"}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": user_agent},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return False, f"HTTP {resp.status} for a nonexistent key, expected 404"
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read()
    except Exception as exc:  # noqa: BLE001 - a monitor must report, not raise
        return False, f"{type(exc).__name__}: {exc}"

    snippet = body[:200].decode("utf-8", "replace")
    if status != 404:
        return False, f"HTTP {status}, expected 404; body starts: {snippet!r}"
    try:
        data = json.loads(body)
    except ValueError:
        return False, f"HTTP 404 with a non-JSON body (not the Worker): {snippet!r}"
    if not isinstance(data, dict):
        return False, f"HTTP 404 with unexpected JSON: {snippet!r}"
    if data.get("code") == WORKER_CODE or data.get("error") == WORKER_ERROR:
        return True, "HTTP 404 with the Worker's JSON for an unknown key"
    return False, f"HTTP 404 with JSON that is not the Worker's unknown-key answer: {snippet!r}"


def main() -> int:
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        from pyobfus_pro.license import (
            LICENSE_API_URL,
            USER_AGENT,
            LicenseVerificationError,
            _verify_online,
        )
    except ImportError as exc:
        print(f"[{stamp}] UNHEALTHY: cannot import the licence client: {exc}")
        return 1

    print(f"[{stamp}] endpoint:   {LICENSE_API_URL}")
    print(f"[{stamp}] user-agent: {USER_AGENT}")

    try:
        result = _verify_online(PROBE_KEY)
    except LicenseVerificationError as exc:
        message = str(exc)
        if HEALTHY_MESSAGE in message:
            healthy, detail = check_worker_404(LICENSE_API_URL, USER_AGENT)
            if healthy:
                print(f"[{stamp}] HEALTHY: server answered with its own 404 for an unknown key.")
                return 0
            print(f"[{stamp}] UNHEALTHY: the client saw a 404, but not from the licence server.")
            print(f"[{stamp}]   got: {detail}")
            print(
                f"[{stamp}]   Customers cannot activate: the request reaches something "
                "other than the Worker (missing route, proxy or edge page)."
            )
            return 1
        print(f"[{stamp}] UNHEALTHY: the server did not answer as itself.")
        print(f"[{stamp}]   got: {message}")
        print(
            f"[{stamp}]   Customers cannot activate. If this names a network block, "
            "the edge is rejecting the client's request before it arrives."
        )
        return 1
    except Exception as exc:  # noqa: BLE001 - a monitor must report, not raise
        print(f"[{stamp}] UNHEALTHY: {type(exc).__name__}: {exc}")
        return 1

    # Reaching here means a key that does not exist was reported as valid.
    print(f"[{stamp}] UNHEALTHY: the server accepted a nonexistent licence key.")
    print(f"[{stamp}]   response: {result}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
