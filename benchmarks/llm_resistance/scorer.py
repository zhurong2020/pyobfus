"""Scoring for the LLM-resistance benchmark.

Primary metric (objective): Semantic-Recovery -- execute the attacker's
reimplementation against the sample's ground-truth IO vectors. Real model
output uses a locked-down Docker executor; the host executor is only for
trusted fixtures. Recovered iff ALL vectors pass (functional equivalence).
Timeouts, exceptions, and empty outputs count as NOT recovered.

Secondary metric (subjective, optional): Comprehension -- an auxiliary judge
scores the attacker's free-text explanation against the ground-truth
description on a 0-3 rubric, normalized to 0-1. Skipped when no judge is given.

See ``docs/LLM_RESISTANCE_BENCHMARK.md``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Driver executed in a subprocess: imports the reimplementation, runs each
# vector, prints a JSON list of {"ok": bool, "got": repr|null, "error": str|null}.
_DRIVER = r"""
import importlib.util, json, sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("reimpl", sys.argv[1])
results = []
try:
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    load_error = None
except BaseException as e:  # noqa: BLE001 - report, don't crash the driver
    mod = None
    load_error = f"{type(e).__name__}: {e}"

vectors = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
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
"""


def score_recovery(
    reimplementation: str,
    meta: dict,
    *,
    timeout: float = 10.0,
    executor: str = "host",
    docker_image: str | None = None,
) -> dict:
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
        work = Path(td)
        reimpl = work / "reimpl.py"
        driver = work / "driver.py"
        vectors_file = work / "vectors.json"
        reimpl.write_text(reimplementation, encoding="utf-8")
        driver.write_text(_DRIVER, encoding="utf-8")
        vectors_file.write_text(json.dumps(vectors), encoding="utf-8")
        try:
            if executor == "host":
                proc = _run_on_host(driver, reimpl, vectors_file, timeout)
            elif executor == "docker":
                proc = _run_in_docker(work, timeout, docker_image)
            else:
                raise ValueError(f"unknown benchmark executor: {executor}")
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


def _run_on_host(
    driver: Path, reimpl: Path, vectors_file: Path, timeout: float
) -> subprocess.CompletedProcess[str]:
    """Execute trusted benchmark code locally; this is not a security sandbox."""
    return subprocess.run(
        [sys.executable, "-I", "-B", str(driver), str(reimpl), str(vectors_file)],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _run_in_docker(
    work: Path, timeout: float, image: str | None
) -> subprocess.CompletedProcess[str]:
    """Execute untrusted model output in a locked-down, offline container."""
    docker = shutil.which("docker")
    if docker is None:
        raise RuntimeError("Docker is required to score real attacker output")
    if not image:
        raise RuntimeError("an explicit --docker-image is required for reproducibility")

    # Refuse an implicit network pull during a measurement. The operator must
    # pull and inspect the chosen image beforehand, then record that exact tag
    # (preferably a digest) in the run metadata.
    inspected = subprocess.run(
        [docker, "image", "inspect", image], capture_output=True, text=True, timeout=30
    )
    if inspected.returncode != 0:
        raise RuntimeError(
            f"Docker image {image!r} is not available locally; pull it before the run"
        )

    return subprocess.run(
        [
            docker,
            "run",
            "--rm",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--memory",
            "128m",
            "--pids-limit",
            "64",
            "--cpus",
            "0.5",
            "--user",
            "65534:65534",
            "--mount",
            f"type=bind,src={work.resolve()},dst=/work,readonly",
            image,
            "python",
            "-I",
            "-B",
            "/work/driver.py",
            "/work/reimpl.py",
            "/work/vectors.json",
        ],
        capture_output=True,
        text=True,
        timeout=timeout + 5,
    )


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
