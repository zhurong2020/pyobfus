"""Smoke test: prove the benchmark pipeline runs end-to-end offline.

Uses the deterministic StubAttacker so it needs no API key and no cost. It
asserts the scorer *discriminates* — the control condition (C0) recovers, and
core obfuscation (C1) does not — which is the property that makes any real
attacker number trustworthy. It also asserts the Pro L3 opacity condition (C4)
builds without error.

Run with::  pytest benchmarks/llm_resistance/test_smoke.py -v

Not collected by the core ``pytest tests/`` run (separate root, exercises the
CLI + pyobfus_pro as a subprocess).
"""

from __future__ import annotations

import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import harness  # noqa: E402
from attacker import StubAttacker  # noqa: E402


def _rows_for(data, sample):
    return {r["condition"]: r for r in data["rows"] if r["sample"] == sample}


def test_stub_pipeline_discriminates():
    # limit=1 -> just luhn (c4-eligible, not c5), keeps the subprocess count low.
    data = harness.run(StubAttacker(), judge=None, limit=1)
    rows = _rows_for(data, "luhn")

    # Control recovers (echoed source == original); the sanity gate in the design.
    assert rows["C0"]["recovered"] is True

    # Core obfuscation defeats the echo attacker (entrypoint name is mangled).
    assert rows["C1"]["recovered"] is False

    # Pro L3 opacity must BUILD (no obfuscation error) and not recover.
    assert rows["C4"]["eligible"] is True
    assert rows["C4"].get("recovery_note", "").startswith("obfuscation error") is False
    assert rows["C4"]["recovered"] is False

    # luhn is not vault-eligible: C5 is reported ineligible, never silently dropped.
    assert rows["C5"]["eligible"] is False


def test_report_renders():
    import report

    data = harness.run(StubAttacker(), judge=None, limit=1)
    md = report.build_report(data)
    assert "Resistance" in md and "C0" in md and "C4" in md
