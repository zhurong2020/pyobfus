"""Deterministic limits of L3 protection, measured without any model.

The agent experiments (docs/AI_ERA_PROTECTION_ROADMAP_2026-10-12.md §13) should
not spend subscription quota rediscovering two facts that a short script can
show for any artifact built from the maintained synthetic corpus:

1. **Static, key in the artifact.** Default L3 builds (and ``--fingerprint``)
   emit ``_LAYER_KEY = b"..."`` beside the ``_CIPHER_<name>`` blobs. Anyone who
   has the file can decrypt every protected function without running it.
   ``static_recover`` does exactly that and returns the recovered code objects'
   names, constants and disassembly.
2. **Runtime, key supplied by the application or device.** With
   ``--bind-key-env`` or ``--bind-device`` the key is not in the file, so (1)
   fails. But whoever runs the artifact with a valid key can observe the
   decrypted bytecode, because the runtime unmarshals it in-process and Python
   raises a ``marshal.loads`` audit event with the plaintext bytes.
   ``runtime_capture`` runs the artifact under such a hook in a subprocess.

So L3 protects against people who hold the artifact but not the key; it does
not protect against a legitimate operator of the program. The experiments
measure everything else (how far a model gets from the obfuscated text, at
what cost), and report these two results as fixed baselines instead.

Only run this on artifacts you built from the synthetic corpus: step (1)
unmarshals bytes from the file, and step (2) executes the artifact.

Usage::

    python -m benchmarks.llm_resistance.key_exposure ARTIFACT.py
    python -m benchmarks.llm_resistance.key_exposure ARTIFACT.py --run --env NAME=VALUE
"""

from __future__ import annotations

import argparse
import ast
import dis
import io
import json
import marshal
import os
import subprocess
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Optional

_NONCE_SIZE = 12
_KEY_NAME = "_LAYER_KEY"
_CIPHER_PREFIX = "_CIPHER_"


def _bytes_assignments(tree: ast.Module) -> Dict[str, bytes]:
    found: Dict[str, bytes] = {}
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, bytes)
        ):
            found[node.targets[0].id] = node.value.value
    return found


def _describe(code: types.CodeType) -> Dict[str, Any]:
    out = io.StringIO()
    dis.dis(code, file=out)
    return {
        "co_name": code.co_name,
        "names": list(code.co_names),
        "constants": [repr(c) for c in code.co_consts if not isinstance(c, types.CodeType)],
        "disassembly": out.getvalue(),
    }


def static_recover(artifact: Path) -> Dict[str, Any]:
    """Decrypt every L3 function using only the file's own contents."""
    from cryptography.exceptions import InvalidTag
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    tree = ast.parse(artifact.read_text(encoding="utf-8"))
    literals = _bytes_assignments(tree)
    ciphers = {
        k[len(_CIPHER_PREFIX) :]: v for k, v in literals.items() if k.startswith(_CIPHER_PREFIX)
    }
    key = literals.get(_KEY_NAME)
    result: Dict[str, Any] = {
        "artifact": artifact.name,
        "protected_functions": sorted(ciphers),
        "key_in_artifact": key is not None,
        "recovered": {},
    }
    if key is None:
        return result
    aesgcm = AESGCM(key)
    for name, blob in sorted(ciphers.items()):
        try:
            plain = aesgcm.decrypt(blob[:_NONCE_SIZE], blob[_NONCE_SIZE:], None)
        except InvalidTag:
            result["recovered"][name] = {"error": "key literal does not decrypt this blob"}
            continue
        result["recovered"][name] = _describe(marshal.loads(plain))  # noqa: S302 - own fixture
    return result


_CAPTURE_BOOTSTRAP = r"""
import json, marshal, runpy, sys, types
captured = []
capturing = [True]  # audit hooks cannot be removed; switch this one off instead
def hook(event, args):
    if capturing[0] and event == "marshal.loads" and args and isinstance(args[0], (bytes, bytearray)):
        captured.append(bytes(args[0]))
sys.addaudithook(hook)
status = "ran"
try:
    runpy.run_path(sys.argv[1], run_name="__main__")
except BaseException as exc:  # report, do not hide, a failed run
    status = "failed: " + type(exc).__name__
capturing[0] = False
names = []
for blob in captured:
    try:
        obj = marshal.loads(blob)
    except Exception:
        continue
    if isinstance(obj, types.CodeType):
        names.append(obj.co_name)
sys.stderr.write("\n__KEY_EXPOSURE__" + json.dumps({"status": status, "captured": names}) + "\n")
"""


def runtime_capture(
    artifact: Path,
    *,
    python: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """Run the artifact under a ``marshal.loads`` hook; list protected functions seen in plaintext."""
    run_env = {k: v for k, v in os.environ.items() if k not in ("PYTHONPATH", "PYTHONHOME")}
    run_env.update(env or {})
    proc = subprocess.run(
        [python or sys.executable, "-E", "-s", "-c", _CAPTURE_BOOTSTRAP, str(artifact)],
        cwd=str(artifact.parent),
        env=run_env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    marker = "__KEY_EXPOSURE__"
    for line in reversed(proc.stderr.splitlines()):
        if line.startswith(marker):
            data: Dict[str, Any] = json.loads(line[len(marker) :])
            # The hook also sees every .pyc import; keep only the functions the
            # artifact encrypted (named by its _CIPHER_<name> constants).
            protected = set(static_recover(artifact)["protected_functions"])
            data["captured"] = sorted(set(data["captured"]) & protected)
            data["artifact"] = artifact.name
            return data
    return {
        "artifact": artifact.name,
        "status": "no report",
        "captured": [],
        "stderr": proc.stderr[-500:],
    }


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--run", action="store_true", help="also run it under a marshal.loads hook")
    parser.add_argument("--env", action="append", default=[], metavar="NAME=VALUE")
    parser.add_argument("--python", help="interpreter for --run (default: this one)")
    args = parser.parse_args(argv)
    report: Dict[str, Any] = {"static": static_recover(args.artifact)}
    if args.run:
        env = dict(item.split("=", 1) for item in args.env)
        report["runtime"] = runtime_capture(args.artifact, python=args.python, env=env)
    json.dump(report, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
