"""Orchestrator for the LLM-deobfuscation-resistance benchmark.

Runs every eligible (sample x condition) pair through the chosen attacker and
scorer, then writes ``results/results.json`` and ``results/report.md``.

Usage::

    python benchmarks/llm_resistance/harness.py --attacker stub
    python benchmarks/llm_resistance/harness.py --attacker anthropic --judge
    python benchmarks/llm_resistance/harness.py --attacker stub --limit 2

The default ``stub`` attacker runs offline (no API key) and exists to prove the
pipeline end-to-end; ``anthropic`` runs the real measurement. See
``docs/LLM_RESISTANCE_BENCHMARK.md``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import conditions as C  # noqa: E402
import report as R  # noqa: E402
import scorer as S  # noqa: E402
from attacker import AnthropicAttacker, StubAttacker, make_anthropic_judge  # noqa: E402

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


def run(attacker, judge=None, limit=None) -> dict:
    samples = load_corpus(limit)
    rows = []
    for meta in samples:
        eps = entrypoints_for(meta)
        for cond in C.CONDITIONS:
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
                    }
                )
                continue

            result = attacker.deobfuscate(obf, eps)
            rec = S.score_recovery(result.reimplementation, meta)
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
                }
            )

    return {
        "meta": {
            "attacker": attacker.descriptor(),
            "judge": judge is not None,
            "sample_count": len(samples),
            "conditions": [c.cid for c in C.CONDITIONS],
            "pyobfus_version": _pyobfus_version(),
            "python": sys.version.split()[0],
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
    ap.add_argument("--attacker", choices=["stub", "anthropic"], default="stub")
    ap.add_argument("--model", default="claude-sonnet-5", help="model id for anthropic attacker")
    ap.add_argument("--judge", action="store_true", help="score comprehension (anthropic only)")
    ap.add_argument("--limit", type=int, default=None, help="limit number of samples")
    args = ap.parse_args()

    if args.attacker == "stub":
        attacker = StubAttacker()
        judge = None
    else:
        attacker = AnthropicAttacker(model=args.model)
        judge = make_anthropic_judge(args.model) if args.judge else None

    data = run(attacker, judge=judge, limit=args.limit)

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "results.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    report_md = R.build_report(data)
    (RESULTS / "report.md").write_text(report_md, encoding="utf-8")

    print(report_md)
    print(f"\nWrote {RESULTS / 'results.json'} and {RESULTS / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
