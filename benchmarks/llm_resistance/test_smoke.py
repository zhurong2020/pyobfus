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

import json
import shutil
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import harness  # noqa: E402
import scorer  # noqa: E402
from attacker import ClaudeCodeCliAttacker, CodexCliAttacker, StubAttacker  # noqa: E402


def _rows_for(data, sample):
    return {r["condition"]: r for r in data["rows"] if r["sample"] == sample}


def test_stub_pipeline_discriminates():
    # Select luhn explicitly. ``limit=1`` used to depend on luhn sorting first,
    # which stopped being true when billing_auth was added.
    data = harness.run(StubAttacker(), judge=None, sample_names={"luhn"})
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


def test_codex_cli_attacker_uses_structured_output_without_api_keys(tmp_path, monkeypatch):
    fake_cli = tmp_path / "fake_codex.py"
    fake_cli.write_text(
        """
import json
import os
import sys
from pathlib import Path

if "--version" in sys.argv:
    print("codex-cli test-0")
    raise SystemExit(0)

prompt = sys.stdin.read()
assert "required_fn(arg1)" in prompt
assert "def hidden" in prompt
assert not any(os.environ.get(k) for k in (
    "OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_API_KEY"
))
output = Path(sys.argv[sys.argv.index("--output-last-message") + 1])
output.write_text(json.dumps({
    "reimplementation": "def required_fn(arg1):\\n    return arg1 + 1\\n",
    "explanation": "Adds one.",
}), encoding="utf-8")
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-child")
    monkeypatch.setenv("CODEX_API_KEY", "must-not-reach-child")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-reach-child")

    attacker = CodexCliAttacker(model="test-model", command=(sys.executable, str(fake_cli)))
    result = attacker.deobfuscate(
        "def hidden(x): return x + 1", [{"name": "required_fn", "arity": 1}]
    )

    assert result.reimplementation.startswith("def required_fn")
    assert result.explanation == "Adds one."
    assert json.loads(result.raw_response)["explanation"] == "Adds one."
    descriptor = attacker.descriptor()
    assert descriptor["model"] == "test-model"
    assert descriptor["codex_cli"] == "codex-cli test-0"


def test_claude_code_cli_attacker_uses_structured_output_without_api_keys(tmp_path, monkeypatch):
    fake_cli = tmp_path / "fake_claude.py"
    fake_cli.write_text(
        """
import json
import os
import sys

if "--version" in sys.argv:
    print("2.1.220 (Claude Code)")
    raise SystemExit(0)

prompt = sys.stdin.read()
assert "required_fn(arg1)" in prompt
assert "def hidden" in prompt
assert not os.environ.get("ANTHROPIC_API_KEY")
assert "--allowedTools" in sys.argv
assert sys.argv[sys.argv.index("--allowedTools") + 1] == ""
assert "--json-schema" in sys.argv
payload = {
    "is_error": False,
    "result": json.dumps({
        "reimplementation": "def required_fn(arg1):\\n    return arg1 + 1\\n",
        "explanation": "Adds one.",
    }),
    "structured_output": {
        "reimplementation": "def required_fn(arg1):\\n    return arg1 + 1\\n",
        "explanation": "Adds one.",
    },
}
print(json.dumps(payload))
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-reach-child")

    attacker = ClaudeCodeCliAttacker(model="test-model", command=(sys.executable, str(fake_cli)))
    result = attacker.deobfuscate(
        "def hidden(x): return x + 1", [{"name": "required_fn", "arity": 1}]
    )

    assert result.reimplementation.startswith("def required_fn")
    assert result.explanation == "Adds one."
    assert json.loads(result.raw_response)["structured_output"]["explanation"] == "Adds one."
    descriptor = attacker.descriptor()
    assert descriptor["model"] == "test-model"
    assert descriptor["claude_cli"] == "2.1.220 (Claude Code)"
    assert descriptor["tool_access"] == 'none (--allowedTools "")'


@pytest.mark.skipif(shutil.which("docker") is None, reason="docker not available")
def test_docker_executor_can_read_mounted_temp_dir():
    # Regression guard: tempfile.TemporaryDirectory() defaults to mode 0700,
    # unreadable by the container's unprivileged --user 65534:65534, which
    # surfaced as every row silently scoring not-recovered (2026-08-01, first
    # real end-to-end docker-executor pilot run -- see scorer.py's fix).
    meta = {"entrypoint": "add_one", "io_vectors": [{"args": [1], "expect": 2}]}
    result = scorer.score_recovery(
        "def add_one(x):\n    return x + 1\n",
        meta,
        executor="docker",
        docker_image="python:3.12-alpine",
    )
    assert result["recovered"] is True, result["note"]


def test_sample_selection_applies_before_limit():
    data = harness.run(
        StubAttacker(),
        judge=None,
        sample_names={"luhn"},
        condition_ids={"C0", "C1"},
        limit=1,
    )
    assert data["meta"]["sample_count"] == 1
    assert data["meta"]["conditions"] == ["C0", "C1"]
    assert {row["sample"] for row in data["rows"]} == {"luhn"}
    assert {row["condition"] for row in data["rows"]} == {"C0", "C1"}
