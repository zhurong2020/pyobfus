"""Turn ``results.json`` into a human-readable ``report.md``.

Headline: the per-condition Semantic-Recovery Rate (SRR) and its inverse,
Resistance = 1 - SRR, plotted across the C0-C5 ladder so the C3->C4 cliff is
visible. Every honest caveat (sample count, ineligible exclusions, attacker
model + date) is carried through from the run metadata.
"""

from __future__ import annotations


def _aggregate(rows: list[dict]) -> dict[str, dict]:
    """Per-condition aggregates over eligible, scored rows."""
    agg: dict[str, dict] = {}
    for r in rows:
        cid = r["condition"]
        a = agg.setdefault(
            cid, {"name": r["condition_name"], "eligible": 0, "recovered": 0, "comp": []}
        )
        if r.get("eligible") and r.get("recovered") is not None:
            a["eligible"] += 1
            if r["recovered"]:
                a["recovered"] += 1
            if r.get("comprehension") is not None:
                a["comp"].append(r["comprehension"])
    return agg


def _bar(rate: float, width: int = 20) -> str:
    filled = round(rate * width)
    return "█" * filled + "·" * (width - filled)


def build_report(data: dict) -> str:
    meta = data["meta"]
    rows = data["rows"]
    agg = _aggregate(rows)

    lines: list[str] = []
    lines.append("# LLM-Deobfuscation-Resistance — Benchmark Report")
    lines.append("")
    att = meta["attacker"]
    att_desc = att.get("model", att.get("attacker", "?"))
    lines.append(
        f"**Attacker**: `{att.get('attacker')}` ({att_desc}) · "
        f"**pyobfus** {meta.get('pyobfus_version')} · "
        f"**Python** {meta.get('python')} · "
        f"**samples**: {meta['sample_count']}"
    )
    lines.append("")
    lines.append(
        "SRR = Semantic-Recovery Rate (fraction of samples the attacker "
        "reconstructed to functional equivalence). **Resistance = 1 − SRR** "
        "(higher = better protection)."
    )
    lines.append("")

    lines.append("| Condition | Eligible | Recovered | SRR | Resistance | |")
    lines.append("|-----------|:--------:|:---------:|:---:|:----------:|--|")
    for cid in meta["conditions"]:
        a = agg.get(cid)
        if not a or a["eligible"] == 0:
            lines.append(f"| {cid} {a['name'] if a else ''} | 0 | — | — | — | (no eligible samples) |")
            continue
        srr = a["recovered"] / a["eligible"]
        resistance = 1 - srr
        lines.append(
            f"| **{cid}** {a['name']} | {a['eligible']} | {a['recovered']} | "
            f"{srr:.0%} | **{resistance:.0%}** | `{_bar(resistance)}` |"
        )
    lines.append("")

    if meta.get("judge"):
        lines.append("**Comprehension (secondary, LLM-judged 0–1):**")
        lines.append("")
        for cid in meta["conditions"]:
            a = agg.get(cid)
            if a and a["comp"]:
                mean = sum(a["comp"]) / len(a["comp"])
                lines.append(f"- {cid}: {mean:.2f} (n={len(a['comp'])})")
        lines.append("")

    # Ineligible exclusions, stated honestly.
    ineligible = [r for r in rows if r.get("eligible") is False]
    if ineligible:
        lines.append("**Ineligible (excluded from that condition's aggregate):**")
        lines.append("")
        by_cond: dict[str, list[str]] = {}
        for r in ineligible:
            by_cond.setdefault(r["condition"], []).append(r["sample"])
        for cid, names in by_cond.items():
            lines.append(f"- {cid}: {', '.join(sorted(names))}")
        lines.append("")

    # Obfuscation errors, if any.
    errors = [r for r in rows if r.get("recovered") is None and r.get("eligible") is True]
    if errors:
        lines.append("**Run errors (not counted as recovered or resistant):**")
        lines.append("")
        for r in errors:
            lines.append(f"- {r['sample']} / {r['condition']}: {r.get('note', '?')}")
        lines.append("")

    lines.append("---")
    lines.append(
        "_Objective metric: functional equivalence via IO vectors, no LLM-judge. "
        "L3 (C4/C5) defends source recovery, not a running process. Numbers are "
        "stamped to the attacker model + date above and are re-runnable via "
        "`harness.py`._"
    )
    lines.append("")
    return "\n".join(lines)
