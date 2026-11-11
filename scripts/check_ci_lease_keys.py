"""Static Core release precondition; not proof of deployment/key ownership."""

import ast
from pathlib import Path
import re
import sys


def check(source: Path) -> bool:
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
        assignments = [
            node
            for node in tree.body
            if isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "TRUSTED_PUBLIC_KEYS"
        ]
        if len(assignments) != 1 or assignments[0].value is None:
            return False
        ring = ast.literal_eval(assignments[0].value)
        return (
            isinstance(ring, dict)
            and bool(ring)
            and all(
                isinstance(kid, str)
                and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", kid, re.ASCII)
                and isinstance(key, bytes)
                and len(key) == 32
                for kid, key in ring.items()
            )
        )
    except (OSError, ValueError, SyntaxError, TypeError):
        return False


def main() -> int:
    if not check(Path(__file__).resolve().parents[1] / "pyobfus_pro" / "ci_lease.py"):
        print(
            "Core release blocked: provision and independently review CI issuer public keys first.",
            file=sys.stderr,
        )
        return 2
    print(
        "CI public-key table is populated; server/key-pair rollout verification is still required."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
