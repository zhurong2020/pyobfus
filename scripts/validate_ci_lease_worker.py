"""Local workerd/Python signed CI conformance; no live services or real keys.

Install pinned Miniflare into a temporary npm prefix, then pass that prefix via
--miniflare-root. Run from the WSL repository. Output contains only test status.
"""

import argparse
import base64
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile

from pyobfus_pro import ci_lease


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--miniflare-root", required=True)
    args = parser.parse_args()
    synthetic_key = "PYOB-AAAA-BBBB-CCCC-DDDD"
    nonce = secrets.token_urlsafe(32)
    request = {
        "license_key": synthetic_key,
        "activation": "ci",
        "protocol": ci_lease.PROTOCOL,
        "nonce": nonce,
    }
    with tempfile.TemporaryDirectory(prefix="ci-lease-canary-") as isolated_home:
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("PYOBFUS_", "CLOUDFLARE_", "CF_"))
        }
        env.update(HOME=isolated_home, USERPROFILE=isolated_home)
        result = subprocess.run(
            ["node", "cloudflare-worker/test/ci_lease_workerd.mjs", args.miniflare_root],
            input=json.dumps(request),
            text=True,
            capture_output=True,
            env=env,
            timeout=90,
        )
        if result.returncode:
            # Preserve harness errors but never print the signing response/key.
            raise RuntimeError("Local workerd CI lease canary failed; inspect the test harness")
        data = ci_lease.strict_json(result.stdout.encode())
        public = base64.urlsafe_b64decode(data["public_key"] + "=")
        old_ring = ci_lease.TRUSTED_PUBLIC_KEYS
        try:
            ci_lease.TRUSTED_PUBLIC_KEYS = {"workerd-canary": public}
            ci_lease.verify_response(data["response"], synthetic_key, nonce)
            try:
                ci_lease.verify_response(data["response"], synthetic_key, secrets.token_urlsafe(32))
            except ci_lease.CILeaseError:
                pass
            else:
                raise AssertionError("cross-request replay accepted")
        finally:
            ci_lease.TRUSTED_PUBLIC_KEYS = old_ring
        if (Path(isolated_home) / ".pyobfus").exists():
            raise AssertionError("CI canary persisted license state")
    print(
        "workerd -> Python: signed CI admission, replay rejection, revocation and no KV/state writes passed"
    )


if __name__ == "__main__":
    main()
