"""Scoring for the LLM-resistance benchmark.

Primary metric (objective): Semantic-Recovery -- execute the attacker's
reimplementation against the sample's ground-truth IO vectors. Real model
output uses a locked-down Docker executor or the native Codex Windows sandbox;
the host executor is only for trusted fixtures. Recovered iff ALL vectors pass
(functional equivalence).
Timeouts, exceptions, and empty outputs count as NOT recovered.

Secondary metric (subjective, optional): Comprehension -- an auxiliary judge
scores the attacker's free-text explanation against the ground-truth
description on a 0-3 rubric, normalized to 0-1. Skipped when no judge is given.

See ``docs/LLM_RESISTANCE_BENCHMARK.md``.
"""

from __future__ import annotations

import json
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PYTHON_EMBED_VERSION = "3.11.9"
PYTHON_EMBED_SHA256 = "009d6bf7e3b2ddca3d784fa09f90fe54336d5b60f0e0f305c37f400bf83cfd3b"

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
    sandbox_python_zip: str | None = None,
    codex_command: str | None = None,
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
            elif executor == "codex-windows":
                proc = _run_in_codex_windows_sandbox(
                    work,
                    timeout,
                    sandbox_python_zip,
                    codex_command=codex_command,
                )
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

    # tempfile.TemporaryDirectory() defaults to mode 0700 (owner-only). The
    # container runs as the unprivileged --user 65534:65534 below, which
    # cannot even traverse an 0700 directory it doesn't own, regardless of the
    # (already world-readable, 0644) file permissions inside it -- surfaces as
    # a driver "Permission denied" with every row scored not-recovered. The
    # bind mount is already read-only and network-isolated, so widening this
    # does not weaken the sandbox -- but grant the minimum needed rather than
    # a blanket world-readable directory: the driver only ever opens
    # driver.py/reimpl.py/vectors.json by their known, hardcoded paths (see
    # score_recovery above), it never lists the directory, so 0o711 (execute
    # -- traverse -- for group/other, no read bit) is enough to open those
    # files without also making the directory's contents enumerable to any
    # other local user on a shared host.
    os.chmod(work, 0o711)
    for entry in work.iterdir():
        os.chmod(entry, 0o644)

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


def _run_in_codex_windows_sandbox(
    work: Path,
    timeout: float,
    runtime_zip: str | None,
    *,
    codex_command: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Execute untrusted output with Codex's native read-only Windows sandbox."""
    if os.name != "nt":
        raise RuntimeError("the codex-windows executor is available only on Windows")
    if not runtime_zip:
        raise RuntimeError("--sandbox-python-zip is required for codex-windows")

    archive = Path(runtime_zip).expanduser().resolve()
    if not archive.is_file():
        raise RuntimeError(f"sandbox Python archive does not exist: {archive}")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != PYTHON_EMBED_SHA256:
        raise RuntimeError(
            "sandbox Python archive SHA-256 mismatch; expected the pinned "
            f"Python {PYTHON_EMBED_VERSION} embeddable package"
        )

    runtime = work / "python-runtime"
    runtime.mkdir()
    with zipfile.ZipFile(archive) as zf:
        root = runtime.resolve()
        for info in zf.infolist():
            target = (runtime / info.filename).resolve()
            if target != root and root not in target.parents:
                raise RuntimeError("unsafe path in sandbox Python archive")
        zf.extractall(runtime)

    python_exe = runtime / "python.exe"
    if not python_exe.is_file():
        raise RuntimeError("sandbox Python archive has no python.exe")

    codex = codex_command or shutil.which("codex.cmd") or shutil.which("codex")
    if not codex:
        raise RuntimeError("Codex CLI was not found for the codex-windows executor")

    # :read-only is essential for benchmark integrity: candidate code cannot
    # rewrite driver.py or vectors.json to forge a passing result. The profile
    # also blocks direct network access. The portable interpreter lives inside
    # the same temporary root, so no personal Python installation is exposed.
    return subprocess.run(
        [
            codex,
            "sandbox",
            "-P",
            ":read-only",
            "-C",
            str(work),
            str(python_exe),
            "-I",
            "-B",
            "-S",
            str(work / "driver.py"),
            str(work / "reimpl.py"),
            str(work / "vectors.json"),
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
