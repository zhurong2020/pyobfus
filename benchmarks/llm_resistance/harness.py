"""Orchestrator for the LLM-deobfuscation-resistance benchmark.

Runs every eligible (sample x condition) pair through the chosen attacker and
scorer, then writes ``results/results.json`` and ``results/report.md``.

Usage::

    python benchmarks/llm_resistance/harness.py --attacker stub
    python benchmarks/llm_resistance/harness.py --attacker anthropic --judge
    python benchmarks/llm_resistance/harness.py --attacker codex-cli \
        --sample luhn --condition C0 --condition C1
    python benchmarks/llm_resistance/harness.py --attacker stub --limit 2

The default ``stub`` attacker runs offline (no API key) and exists to prove the
pipeline end-to-end; ``anthropic`` runs the real measurement. See
``docs/LLM_RESISTANCE_BENCHMARK.md``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import conditions as C  # noqa: E402
import report as R  # noqa: E402
import scorer as S  # noqa: E402
from attacker import (  # noqa: E402
    AnthropicAttacker,
    CodexCliAttacker,
    StubAttacker,
    make_anthropic_judge,
)

CORPUS = _HERE / "corpus"
RESULTS = _HERE / "results"


def load_corpus(limit: int | None = None) -> list[dict]:
    samples = []
    for jf in sorted(CORPUS.glob("*.json")):
        meta = json.loads(jf.read_text(encoding="utf-8"))
        meta["name"] = jf.stem
        meta["source"] = jf.with_suffix(".py").read_text(encoding="utf-8")
        samples.append(meta)
    return samples[:limit] if limit else samples


def entrypoints_for(meta: dict) -> list[dict]:
    """Unique entrypoints referenced by the sample's IO vectors, with arity."""
    default_ep = meta["entrypoint"]
    seen: dict[str, int] = {}
    for v in meta["io_vectors"]:
        ep = v.get("entrypoint", default_ep)
        if ep not in seen:
            seen[ep] = len(v.get("args", []))
    return [{"name": name, "arity": arity} for name, arity in seen.items()]


def run(
    attacker,
    judge=None,
    limit=None,
    sample_names: set[str] | None = None,
    condition_ids: set[str] | None = None,
    *,
    executor: str = "host",
    docker_image: str | None = None,
    sandbox_python_zip: str | None = None,
    codex_command: str | None = None,
) -> dict:
    samples = load_corpus()
    if sample_names is not None:
        samples = [sample for sample in samples if sample["name"] in sample_names]
    if limit:
        samples = samples[:limit]
    if not samples:
        raise ValueError("no benchmark samples matched the requested selection")
    conditions = C.CONDITIONS
    if condition_ids is not None:
        conditions = [condition for condition in conditions if condition.cid in condition_ids]
    if not conditions:
        raise ValueError("no benchmark conditions matched the requested selection")

    rows = []
    for meta in samples:
        eps = entrypoints_for(meta)
        pk = bool(meta.get("public_knowledge", False))
        prev_artifact: dict[str, str] = {}
        for cond in conditions:
            if not C.eligible(cond, meta):
                rows.append(
                    {
                        "sample": meta["name"],
                        "condition": cond.cid,
                        "condition_name": cond.name,
                        "eligible": False,
                        "recovered": None,
                        "comprehension": None,
                        "note": "ineligible for this condition",
                        "public_knowledge": pk,
                    }
                )
                continue

            try:
                obf = C.obfuscate(cond, meta["source"], meta)
            except C.ConditionError as e:
                rows.append(
                    {
                        "sample": meta["name"],
                        "condition": cond.cid,
                        "condition_name": cond.name,
                        "eligible": True,
                        "recovered": None,
                        "comprehension": None,
                        "note": f"obfuscation error: {e}",
                        "public_knowledge": pk,
                    }
                )
                continue

            if cond.builds_on and prev_artifact.get(cond.builds_on) == obf:
                rows.append(
                    {
                        "sample": meta["name"],
                        "condition": cond.cid,
                        "condition_name": cond.name,
                        "eligible": True,
                        "recovered": None,
                        "comprehension": None,
                        "note": (
                            f"no-op vs {cond.builds_on}: transform produced an identical "
                            "artifact for this sample; attacker call skipped"
                        ),
                        "skip_reason": "noop",
                        "artifact_chars": len(obf),
                        "artifact_sha256_16": hashlib.sha256(obf.encode("utf-8")).hexdigest()[:16],
                        "public_knowledge": pk,
                    }
                )
                prev_artifact[cond.cid] = obf
                continue

            result = attacker.deobfuscate(obf, eps)
            rec = S.score_recovery(
                result.reimplementation,
                meta,
                executor=executor,
                docker_image=docker_image,
                sandbox_python_zip=sandbox_python_zip,
                codex_command=codex_command,
            )
            comp = S.score_comprehension(result.explanation, meta, judge)
            rows.append(
                {
                    "sample": meta["name"],
                    "condition": cond.cid,
                    "condition_name": cond.name,
                    "eligible": True,
                    "recovered": rec["recovered"],
                    "recovery_note": rec["note"],
                    "comprehension": comp["comprehension"],
                    "artifact_chars": len(obf),
                    "artifact_sha256_16": hashlib.sha256(obf.encode("utf-8")).hexdigest()[:16],
                    "public_knowledge": pk,
                }
            )
            prev_artifact[cond.cid] = obf

    return {
        "meta": {
            "attacker": attacker.descriptor(),
            "judge": judge is not None,
            "sample_count": len(samples),
            "conditions": [c.cid for c in conditions],
            "pyobfus_version": _pyobfus_version(),
            "python": sys.version.split()[0],
            "run_utc": datetime.now(timezone.utc).isoformat(),
            "execution": {
                "executor": executor,
                "docker_image": docker_image,
                "sandbox_python_zip": (
                    Path(sandbox_python_zip).name if sandbox_python_zip else None
                ),
                "sandbox_python_sha256_16": (
                    hashlib.sha256(Path(sandbox_python_zip).read_bytes()).hexdigest()[:16]
                    if sandbox_python_zip
                    else None
                ),
                "network": (
                    "none" if executor in {"docker", "codex-windows"} else "host-accessible"
                ),
            },
        },
        "rows": rows,
    }


def _pyobfus_version() -> str:
    try:
        import pyobfus

        return getattr(pyobfus, "__version__", "unknown")
    except Exception:  # noqa: BLE001
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description="LLM-deobfuscation-resistance benchmark")
    ap.add_argument("--attacker", choices=["stub", "anthropic", "codex-cli"], default="stub")
    ap.add_argument(
        "--model",
        default=os.environ.get("ANTHROPIC_MODEL"),
        help="explicit model id for a real attacker (or set ANTHROPIC_MODEL)",
    )
    ap.add_argument("--judge", action="store_true", help="score comprehension (anthropic only)")
    ap.add_argument("--limit", type=int, default=None, help="limit number of samples")
    ap.add_argument(
        "--sample",
        action="append",
        default=None,
        help="run only this named corpus sample (repeatable)",
    )
    ap.add_argument(
        "--condition",
        action="append",
        default=None,
        help="run only this condition id, such as C0 (repeatable)",
    )
    ap.add_argument(
        "--executor",
        choices=["host", "docker", "codex-windows"],
        default=None,
        help="scoring executor (default: host for stub, docker for real attackers)",
    )
    ap.add_argument(
        "--docker-image",
        default=os.environ.get("PYOBFUS_BENCHMARK_DOCKER_IMAGE"),
        help="pre-pulled image tag/digest used by the docker scoring executor",
    )
    ap.add_argument(
        "--sandbox-python-zip",
        default=os.environ.get("PYOBFUS_BENCHMARK_PYTHON_ZIP"),
        help="pinned Python embeddable ZIP used by the codex-windows executor",
    )
    ap.add_argument(
        "--codex-command",
        default=os.environ.get("PYOBFUS_BENCHMARK_CODEX_COMMAND"),
        help="explicit codex executable path (normally auto-detected)",
    )
    ap.add_argument(
        "--unsafe-host-execution",
        action="store_true",
        help="allow real model-generated code to execute on this host (not recommended)",
    )
    args = ap.parse_args()

    if args.attacker == "stub":
        attacker = StubAttacker()
        judge = None
    elif args.attacker == "anthropic":
        if not args.model:
            ap.error("--model is required for the anthropic attacker")
        attacker = AnthropicAttacker(model=args.model)
        judge = make_anthropic_judge(args.model) if args.judge else None
    else:
        if not args.model:
            ap.error("--model is required for the codex-cli attacker")
        if args.judge:
            ap.error("--judge is not implemented for codex-cli; omit it for the pilot")
        if not args.sample or not args.condition:
            ap.error(
                "codex-cli requires explicit --sample and --condition selections "
                "to prevent an accidental full-matrix subscription run"
            )
        command = (args.codex_command,) if args.codex_command else None
        attacker = CodexCliAttacker(model=args.model, command=command)
        judge = None

    known_conditions = {condition.cid for condition in C.CONDITIONS}
    unknown_conditions = set(args.condition or ()) - known_conditions
    if unknown_conditions:
        ap.error(f"unknown --condition value(s): {', '.join(sorted(unknown_conditions))}")

    if args.executor:
        executor = args.executor
    elif args.attacker == "stub":
        executor = "host"
    elif args.attacker == "codex-cli" and os.name == "nt":
        executor = "codex-windows"
    else:
        executor = "docker"
    if args.attacker != "stub" and executor == "host" and not args.unsafe_host_execution:
        ap.error(
            "real attacker output defaults to --executor docker; "
            "host execution requires --unsafe-host-execution"
        )
    if executor == "docker" and not args.docker_image:
        ap.error("--docker-image is required with --executor docker")
    if executor == "codex-windows" and not args.sandbox_python_zip:
        ap.error("--sandbox-python-zip is required with --executor codex-windows")

    data = run(
        attacker,
        judge=judge,
        limit=args.limit,
        sample_names=set(args.sample) if args.sample else None,
        condition_ids=set(args.condition) if args.condition else None,
        executor=executor,
        docker_image=args.docker_image,
        sandbox_python_zip=args.sandbox_python_zip,
        codex_command=args.codex_command,
    )

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "results.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    report_md = R.build_report(data)
    (RESULTS / "report.md").write_text(report_md, encoding="utf-8")

    # Windows commonly inherits a GBK console. Keep the UTF-8 report file
    # authoritative, but never crash after a successful run merely because a
    # Markdown glyph is not representable on stdout.
    try:
        sys.stdout.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass
    print(report_md)
    print(f"\nWrote {RESULTS / 'results.json'} and {RESULTS / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
