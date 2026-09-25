#!/usr/bin/env python3
"""Self-dogfooding lanes for pyobfus.

Implements the staged lanes from ``docs/SELF_DOGFOODING_BEST_PRACTICES.md`` in
observation mode: each lane produces evidence and fails only on a genuine
problem (a crash, a parse error, an output that no longer runs, a leaked
absolute path). None of them mutate the repository, publish anything, or claim
that self-use proves trustworthiness.

Lanes:

* ``lane-a`` — run the current checkout's ``--check`` over pyobfus's own source
  (offline), writing JSON (and SARIF when supported). Fails on a parse error or
  a crash, never merely on findings.
* ``lane-b`` — obfuscate the canary with a given pyobfus entry point, then
  assert semantic outcomes: the output compiles, the obfuscated app prints the
  same result as the original, the provenance manifest validates, and a build
  report is written. ``--entry`` selects the pyobfus to test (the checkout, or
  an installed ``N-1`` wheel for a two-lane comparison).
* ``lane-c`` — build the wheel, ``twine check`` it, install it in a fresh venv,
  run lane-b through the *installed* entry point, and inspect the wheel for
  unexpected files or leaked identifiers.
* ``lane-d`` — obfuscate the canary twice under varied TMPDIR / locale /
  timezone / hash seed / traversal order and compare the bytes of the
  deterministic community output, classifying any difference.

This is not a blocking gate by itself; the CI workflow runs it for evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from pathlib import Path
from typing import List, Optional, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
CANARY = REPO_ROOT / "dogfood" / "canary"
EXPECTED_CANARY_STDOUT = "25"

# Absolute-path shapes that must never appear in a distributed wheel or in
# generated output (the reproducibility/privacy leak 0.5.23 fixed). Personal-
# identifier PII is guarded separately by the repo pre-commit hook, so this
# file does not hard-code any name (doing so would reintroduce it here).
LEAK_MARKERS = ("/home/", "/Users/", "\\Users\\", "C:\\Users")


class LaneError(RuntimeError):
    """A genuine dogfood failure (crash, non-running output, leak)."""


def _run(
    cmd: Sequence[str],
    *,
    env: Optional[dict] = None,
    cwd: Optional[Path] = None,
    check: bool = True,
) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        list(cmd),
        env=env,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise LaneError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def _pyobfus_cmd(entry: str) -> List[str]:
    """Resolve a pyobfus invocation from an --entry spec.

    ``module`` runs ``<this python> -m pyobfus`` (the checkout). Anything else is
    treated as a path to a pyobfus console script (e.g. an installed wheel's
    ``venv/bin/pyobfus``).
    """
    if entry == "module":
        return [sys.executable, "-m", "pyobfus"]
    return [entry]


def _log(msg: str) -> None:
    print(f"[dogfood] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Lane A — current-source self-analysis
# ---------------------------------------------------------------------------


def lane_a(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    # --check takes a single INPUT_PATH, so scan each target on its own.
    targets = ["pyobfus", str(Path("pyobfus_mcp") / "pyobfus_mcp")]
    total_parse_errors = 0
    for target in targets:
        slug = target.replace("/", "_").replace("\\", "_")
        _log(f"Lane A: --check {target} (offline)")
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pyobfus",
                "--check",
                target,
                "--offline",
                "--no-config",
                "--json",
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        # --check exits non-zero when high findings exist; that is not a lane
        # failure in observation mode. A crash (no JSON) is.
        stdout = proc.stdout.strip()
        if not stdout:
            raise LaneError(f"Lane A produced no JSON for {target}. stderr:\n{proc.stderr}")
        try:
            report = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise LaneError(
                f"Lane A JSON for {target} did not parse: {exc}\n{stdout[:400]}"
            ) from exc
        (out_dir / f"self_check_{slug}.json").write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )

        parse_errors = report.get("parse_errors") or report.get("parse_error_count") or 0
        files_scanned = report.get("files_scanned") or report.get("scanned") or 0
        summary = report.get("summary") or report.get("severity_counts") or {}
        _log(
            f"Lane A: {target}: scanned={files_scanned} parse_errors={parse_errors} summary={summary}"
        )
        total_parse_errors += int(parse_errors)

        # SARIF is a pure projection since 0.5.21; capture it as evidence.
        sarif_path = out_dir / f"self_check_{slug}.sarif"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pyobfus",
                "--check",
                target,
                "--offline",
                "--no-config",
                "--sarif",
                str(sarif_path),
            ],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if sarif_path.exists():
            _log(f"Lane A: {target}: SARIF written to {sarif_path.name}")

    if total_parse_errors:
        raise LaneError(f"Lane A found {total_parse_errors} parse error(s) in pyobfus's own source")
    _log("Lane A: OK (observation mode, findings not gated)")


# ---------------------------------------------------------------------------
# Lane B — canary obfuscate + semantic-outcome checks
# ---------------------------------------------------------------------------


def _obfuscate_canary(pyobfus: List[str], work: Path) -> dict:
    """Obfuscate the canary in deterministic community mode; return artifact paths."""
    out = work / "obf"
    mapping = work / "mapping.json"
    provenance = work / "provenance.json"
    report = work / "build_report.json"
    if out.exists():
        shutil.rmtree(out)
    proc = _run(
        [
            *pyobfus,
            str(CANARY),
            "-o",
            str(out),
            "--save-mapping",
            str(mapping),
            "--provenance-manifest",
            str(provenance),
            "--build-report",
            str(report),
            "--verify-syntax",
            "--json",
            "--no-config",
        ],
        cwd=REPO_ROOT,
    )
    return {
        "out": out,
        "mapping": mapping,
        "provenance": provenance,
        "report": report,
        "stdout": proc.stdout,
    }


def _canary_stdout(python: str, canary_root: Path) -> str:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(canary_root)
    proc = _run([python, str(canary_root / "app.py")], env=env)
    return proc.stdout.strip()


def lane_b(pyobfus: List[str], out_dir: Path, *, python_for_output: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dogfood_b_") as td:
        work = Path(td)
        _log(f"Lane B: obfuscating canary with {' '.join(pyobfus)}")
        art = _obfuscate_canary(pyobfus, work)

        # 1. original and obfuscated must print the same result.
        original = _canary_stdout(python_for_output, CANARY)
        if original != EXPECTED_CANARY_STDOUT:
            raise LaneError(
                f"canary baseline changed: expected {EXPECTED_CANARY_STDOUT}, got {original}"
            )
        obfuscated = _canary_stdout(python_for_output, art["out"])
        if obfuscated != original:
            raise LaneError(
                f"obfuscated canary output differs: original={original!r} obfuscated={obfuscated!r}"
            )
        _log(f"Lane B: execution outcome preserved ({obfuscated})")

        # 2. provenance manifest must validate through the same tool.
        vproc = _run(
            [*pyobfus, "--verify-provenance-manifest", str(art["provenance"]), "--json"],
            cwd=REPO_ROOT,
        )
        vres = json.loads(vproc.stdout)
        if not vres.get("valid"):
            raise LaneError(f"provenance manifest did not validate: {vres}")
        _log("Lane B: provenance manifest valid")

        # 3. build report must exist and name a version.
        if not art["report"].exists():
            raise LaneError("build report was not written")
        report = json.loads(art["report"].read_text(encoding="utf-8"))
        _log(
            f"Lane B: build report OK (pyobfus {report.get('pyobfus_version') or report.get('tool', {})})"
        )

        # 4. no absolute-path / PII leak in the generated tree.
        _assert_no_leaks(art["out"])
        _log("Lane B: no path/PII leak in output")

        # persist evidence
        shutil.copy(art["provenance"], out_dir / "canary_provenance.json")
        shutil.copy(art["report"], out_dir / "canary_build_report.json")
    _log("Lane B: OK")


def _assert_no_leaks(tree: Path) -> None:
    for path in tree.rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        for marker in LEAK_MARKERS:
            if marker in text:
                raise LaneError(f"leak marker {marker!r} found in generated {path.name}")


# ---------------------------------------------------------------------------
# Lane C — release-candidate artifact verification
# ---------------------------------------------------------------------------


def lane_c(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="dogfood_c_") as td:
        work = Path(td)
        dist = work / "dist"
        _log("Lane C: building wheel + sdist")
        _run([sys.executable, "-m", "build", "-o", str(dist), str(REPO_ROOT)], cwd=REPO_ROOT)
        wheels = list(dist.glob("pyobfus-*.whl"))
        if not wheels:
            raise LaneError("no pyobfus wheel was built")
        wheel = wheels[0]
        _log(f"Lane C: built {wheel.name}")

        _log("Lane C: twine check")
        _run([sys.executable, "-m", "twine", "check", *[str(p) for p in dist.iterdir()]])

        # inspect wheel contents for unexpected files / leaks
        _inspect_wheel(wheel)
        _log("Lane C: wheel content inspection OK")

        # fresh venv install + run lane B through the installed entry point
        env_dir = work / "venv"
        _log("Lane C: creating fresh venv and installing the built wheel")
        venv.create(env_dir, with_pip=True)
        vpy = env_dir / "bin" / "python"
        vpyobfus = env_dir / "bin" / "pyobfus"
        _run([str(vpy), "-m", "pip", "install", "-q", str(wheel)])
        installed_version = _run(
            [str(vpy), "-c", "import pyobfus; print(pyobfus.__version__)"]
        ).stdout.strip()
        _log(f"Lane C: installed pyobfus {installed_version} in fresh venv")
        lane_b([str(vpyobfus)], out_dir / "lane_b_from_wheel", python_for_output=str(vpy))
    _log("Lane C: OK")


def _inspect_wheel(wheel: Path) -> None:
    import zipfile

    with zipfile.ZipFile(wheel) as zf:
        names = zf.namelist()
        # Core wheel must not bundle the separately-distributed runtime.
        bundled_runtime = [n for n in names if n.startswith("pyobfus_runtime/")]
        if bundled_runtime:
            raise LaneError(
                f"Core wheel unexpectedly bundles pyobfus_runtime: {bundled_runtime[:3]}"
            )
        # No stray test or repo-only files.
        stray = [n for n in names if n.endswith((".pyc",)) or "/tests/" in n]
        if stray:
            raise LaneError(f"wheel contains unexpected files: {stray[:5]}")
        # No leaked absolute paths / PII in text members.
        for name in names:
            if name.endswith((".py", ".txt", ".md", ".cfg", "METADATA", "RECORD")):
                data = zf.read(name).decode("utf-8", errors="replace")
                for marker in LEAK_MARKERS:
                    if marker in data:
                        raise LaneError(f"leak marker {marker!r} in wheel member {name}")


# ---------------------------------------------------------------------------
# Lane D — reproducibility probe
# ---------------------------------------------------------------------------


def _obfuscate_for_repro(work: Path, extra_env: dict) -> bytes:
    out = work / "obf"
    if out.exists():
        shutil.rmtree(out)
    env = dict(os.environ)
    env.update(extra_env)
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    _run(
        [sys.executable, "-m", "pyobfus", str(CANARY), "-o", str(out), "--no-config", "--json"],
        env=env,
        cwd=REPO_ROOT,
    )
    # Concatenate every generated .py in sorted order into one digest input.
    blob = bytearray()
    for path in sorted(out.rglob("*.py")):
        blob += path.relative_to(out).as_posix().encode("utf-8")
        blob += b"\0"
        blob += path.read_bytes()
        blob += b"\0"
    return bytes(blob)


def lane_d(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with (
        tempfile.TemporaryDirectory(prefix="dogfood_d1_") as td1,
        tempfile.TemporaryDirectory(prefix="dogfood_d2_zzz_") as td2,
    ):
        _log("Lane D: building canary twice under varied environment")
        first = _obfuscate_for_repro(
            Path(td1),
            {"LC_ALL": "C", "TZ": "UTC", "PYTHONHASHSEED": "0"},
        )
        second = _obfuscate_for_repro(
            Path(td2),
            {"LC_ALL": "en_US.UTF-8", "TZ": "Asia/Tokyo", "PYTHONHASHSEED": "12345"},
        )
        (out_dir / "repro_first.sha").write_text(_sha(first), encoding="utf-8")
        (out_dir / "repro_second.sha").write_text(_sha(second), encoding="utf-8")
        if first != second:
            raise LaneError(
                "deterministic community output differs across environments "
                f"(sha {_sha(first)} vs {_sha(second)}); classify as an "
                "environmental/order/locale leak before shipping"
            )
    _log(f"Lane D: OK — byte-identical under varied environment (sha {_sha(first)})")


def _sha(data: bytes) -> str:
    import hashlib

    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="pyobfus self-dogfooding lanes")
    parser.add_argument(
        "lane",
        choices=["lane-a", "lane-b", "lane-c", "lane-d", "all"],
        help="which lane to run ('all' runs A, B, D; C is opt-in / release-time)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "dogfood_out",
        help="directory for evidence artifacts",
    )
    parser.add_argument(
        "--entry",
        default="module",
        help="Lane B pyobfus entry: 'module' (checkout) or a path to a pyobfus script",
    )
    args = parser.parse_args(argv)

    try:
        if args.lane == "lane-a":
            lane_a(args.out / "lane_a")
        elif args.lane == "lane-b":
            lane_b(_pyobfus_cmd(args.entry), args.out / "lane_b", python_for_output=sys.executable)
        elif args.lane == "lane-c":
            lane_c(args.out / "lane_c")
        elif args.lane == "lane-d":
            lane_d(args.out / "lane_d")
        elif args.lane == "all":
            lane_a(args.out / "lane_a")
            lane_b(_pyobfus_cmd("module"), args.out / "lane_b", python_for_output=sys.executable)
            lane_d(args.out / "lane_d")
    except LaneError as exc:
        _log(f"FAIL: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
