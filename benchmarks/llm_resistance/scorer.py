"""Scoring for the LLM-resistance benchmark.

Primary metric (objective): Semantic-Recovery -- execute the attacker's
reimplementation against the sample's ground-truth IO vectors in an isolated
subprocess. Recovered iff ALL vectors pass (functional equivalence). Timeouts,
exceptions, and empty outputs count as NOT recovered, never as dropped samples.

Secondary metric (subjective, optional): Comprehension -- an auxiliary judge
scores the attacker's free-text explanation against the ground-truth
description on a 0-3 rubric, normalized to 0-1. Skipped when no judge is given.

See ``docs/LLM_RESISTANCE_BENCHMARK.md``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Driver executed in a subprocess: imports the reimplementation, runs each
# vector, prints a JSON list of {"ok": bool, "got": repr|null, "error": str|null}.
_DRIVER = r'''
import importlib.util, json, sys

spec = importlib.util.spec_from_file_location("reimpl", sys.argv[1])
results = []
try:
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    load_error = None
except BaseException as e:  # noqa: BLE001 - report, don't crash the driver
    mod = None
    load_error = f"{type(e).__name__}: {e}"

vectors = json.loads(sys.argv[2])
for v in vectors:
    if mod is None:
        results.append({"ok": False, "got": None, "error": f"module load failed: {load_error}"})
        continue
    try:
        fn = getattr(mod, v["entrypoint"])
        got = fn(*v.get("args", []), **v.get("kwargs", {}))
        results.append({"ok": got == v["expect"], "got": repr(got), "error": None})
    except BaseException as e:  # noqa: BLE001
        results.append({"ok": False, "got": None, "error": f"{type(e).__name__}: {e}"})
print(json.dumps(results))
'''


def score_recovery(reimplementation: str, meta: dict, *, timeout: float = 10.0) -> dict:
    """Run the attacker's reimplementation against the sample's IO vectors.

    Returns ``{"recovered": bool, "vectors": [...per-vector...], "note": str}``.
    """
    default_ep = meta["entrypoint"]
    vectors = [
        {
            "entrypoint": v.get("entrypoint", default_ep),
            "args": v.get("args", []),
            "kwargs": v.get("kwargs", {}),
            "expect": v["expect"],
        }
        for v in meta["io_vectors"]
    ]

    if not reimplementation.strip():
        return {"recovered": False, "vectors": [], "note": "empty attacker output"}

    with tempfile.TemporaryDirectory() as td:
        reimpl = Path(td) / "reimpl.py"
        reimpl.write_text(reimplementation, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-c", _DRIVER, str(reimpl), json.dumps(vectors)],
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return {"recovered": False, "vectors": [], "note": "execution timeout"}

    try:
        per_vector = json.loads(proc.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {
            "recovered": False,
            "vectors": [],
            "note": f"driver produced no result (stderr: {proc.stderr[-300:].strip()})",
        }

    recovered = len(per_vector) == len(vectors) and all(r["ok"] for r in per_vector)
    return {"recovered": recovered, "vectors": per_vector, "note": ""}


def score_comprehension(explanation: str, meta: dict, judge) -> dict:
    """Score the attacker's explanation with an auxiliary judge (0-1), or skip.

    ``judge`` is a callable ``(explanation, ground_truth) -> int in 0..3`` or
    None. Kept deliberately separate from and subordinate to recovery.
    """
    if judge is None:
        return {"comprehension": None, "note": "no judge configured"}
    if not explanation.strip():
        return {"comprehension": 0.0, "note": "empty explanation"}
    raw = int(judge(explanation, meta["description"]))
    raw = max(0, min(3, raw))
    return {"comprehension": raw / 3.0, "note": ""}
