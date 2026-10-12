# LLM resistance — round-2 static probe (2026-10-12)

Research evidence for choosing techniques, not a marketing claim. Protocol:
[`LLM_RESISTANCE_BENCHMARK.md`](LLM_RESISTANCE_BENCHMARK.md) "Round 2 protocol".
Raw results (reviewed, no model text):
`benchmarks/llm_resistance/published/2026-10-12/`.

## What was run

- **Samples:** six new synthetic samples with custom, non-public logic
  (`freight_quote`, `loyalty_points`, `sensor_calibrate`, `claim_risk`,
  `slot_allocator`, `reorder_plan`), 17 hidden I/O vectors each. No docstrings.
  No multi-module sample yet (the harness scores one module at a time).
- **Conditions:** C0 plaintext · C1 Community `--preset aggressive` · C4 Pro L3
  (`--selective-opacity`, key literal in the artifact) · C4b Pro L3 with
  `--bind-key-env` (no key in the artifact). pyobfus 0.7.0.
- **Attackers (subscriptions only, API-key variables removed):** Codex CLI
  0.162.1 with `gpt-6.1-sol`, reasoning effort low; Claude Code 2.1.296 with
  `claude-sonnet-5-5`, no tools. One attempt per cell, static: the attacker
  sees the artifact text and the entrypoint signatures, nothing else.
- **Scoring:** the reimplementation runs in Docker
  (`python@sha256:1b668429…4ad4ab4`, no network) against the hidden vectors;
  recovered = every vector passes.
- **Cost:** 48 calls plus 2 smoke calls on the maintainer's existing
  subscriptions; no pay-per-use API.

## Results

| Condition | Codex `gpt-6.1-sol` | Claude `claude-sonnet-5-5` |
|---|---|---|
| C0 plaintext (validity control) | 6/6 | 6/6 |
| C1 Community default (aggressive) | **6/6 recovered** | **6/6 recovered** |
| C4 L3, key in the artifact | 0/6 | 0/6 |
| C4b L3, application-provided key | 0/6 | 0/6 |

## What this does and does not show

- **Community renaming does not stop a model from reimplementing custom
  logic.** Both models recovered every C1 sample from one read, consistent with
  published results that models reason over renamed code at close to normal
  accuracy. Community obfuscation's value is against casual reading and cheap
  copying, as the honesty guardrails already say; this probe is first-party
  evidence for that wording, not a reason to add more AST transforms.
- **L3 removes the logic from the text, so a static reader without tools
  recovers nothing.** That is the expected upper bound of a static test, not a
  strength measurement.
- **The static tier cannot tell C4 from C4b,** but the difference is real and
  already measured without a model: with the key in the artifact (C4),
  `key_exposure.py` decrypts every protected function in a few lines; with
  C4b it cannot, and only someone who runs the program with the key sees the
  bytecode. A model with tools would be expected to do the same as the script;
  that is the runnable tier, not yet built.
- One attempt per cell, two models, six samples: enough to see a 6-0 split,
  not enough for rates or confidence intervals.

## Decisions taken from it

1. Do not invest in new Community AST transforms for "AI resistance"
   (roadmap stop rule: no gain for both families).
2. The meaningful next experiment is the **runnable tier** (agent with Python
   and a decompiler in a no-network sandbox) for C4 vs C4b, plus a multi-module
   sample. It needs an agentic adapter; build it before spending more quota.
3. Product messaging stays as documented: L3 with an application-provided key
   protects the file at rest; it does not protect against whoever runs the
   program with the key.
