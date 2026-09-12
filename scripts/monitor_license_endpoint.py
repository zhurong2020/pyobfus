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

Exit codes: 0 healthy, 1 unhealthy.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

# Format-valid (PYOB + four hex groups) so it passes client-side validation and
# actually reaches the network. Never generated in practice: keys are random
# hex, and an all-zero draw is ~1 in 2**64.
PROBE_KEY = "PYOB-0000-0000-0000-0000"

# What a healthy server says about a key it does not have. The Worker answers
# HTTP 404 with {"valid": false, "error": "Invalid license key"}, which the
# client surfaces as this message.
HEALTHY_MESSAGE = "License key not found"


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
            print(f"[{stamp}] HEALTHY: server answered with its own 404 for an unknown key.")
            return 0
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
