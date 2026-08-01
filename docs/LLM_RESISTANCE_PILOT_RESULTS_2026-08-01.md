# P2-18 LLM-Deobfuscation-Resistance — Pilot Results (2026-08-01)

Reviewed, versioned copy of the P2-18 benchmark pilots run 2026-08-01, per
`benchmarks/llm_resistance/README.md`'s instruction to copy a reviewed
report/result out of the gitignored `results/` directory before treating a
run as evidence. Design and methodology: `docs/LLM_RESISTANCE_BENCHMARK.md`.
Status/next-step tracking: `docs/POST_V0.4_TODO.md` § P2-18.

## Scope

Two model families, five corpus samples, six conditions (C0-C5) each where
eligible. Two model families were chosen deliberately as the endpoint, not an
interim step — see "Why two model families is enough" below.

- **Codex CLI** (`--attacker codex-cli`), model `gpt-5.6-sol`, saved ChatGPT
  subscription login (no API account).
- **Claude Code CLI** (`--attacker claude-code-cli`), model `sonnet`, saved
  Claude subscription login (no API account).
- Both runs used `--executor docker --docker-image python:3.12-alpine` on the
  same Linux machine (this repo's dev environment) — no separate Windows
  machine was needed for this round, since both CLIs and Docker are installed
  locally.
- Conditions: C0 plaintext (control) · C1 core mangling · C2 +string
  encryption · C3 +control-flow flattening · C4 Pro L3 Selective Opacity · C5
  Pro L3 Runtime String Vault.

## Corpus

| Sample | Public knowledge? | c4_eligible | c5_eligible |
|---|---|:---:|:---:|
| `luhn` | Yes (Luhn checksum) | ✓ | ✗ |
| `caesar` | Yes (Caesar cipher) | ✓ | ✗ |
| `roman` | Yes (Roman numerals) | ✓ | ✗ |
| `billing_auth` | No (custom auth logic) | ✗ | ✓ |
| `price_rules` | No (custom tiered pricing) | ✓ | ✗ |

Public-knowledge samples let an attacker recall a correct implementation from
the function name/signature alone, without engaging the obfuscation at all —
a `recovered=true` on one of these above C1 is not evidence a layer failed.
Only `billing_auth` and `price_rules` are credible signal for C2 and up.

## Results

### Codex CLI (`gpt-5.6-sol`) — `luhn` + `billing_auth`

Ran in an earlier session the same day; summarized here from
`docs/POST_V0.4_TODO.md`'s existing record (raw log not preserved locally —
gitignored `results/` is overwritten by each run). C0/C1 fully recovered on
both samples. `billing_auth` held at C2/C3/C5 (0% SRR / 100% resistance
each). `luhn` (public-knowledge) was the only C4-eligible sample in this
pair and was recovered — inconclusive, not a finding.

### Claude Code CLI (`sonnet`) — `luhn` + `billing_auth`

| Condition | Eligible | Recovered | SRR | Resistance |
|---|:---:|:---:|:---:|:---:|
| C0 plaintext | 2 | 2 | 100% | 0% |
| C1 core mangling | 2 | 2 | 100% | 0% |
| C2 +string encryption | 1 (`billing_auth`; `luhn` no-op) | 0 | 0% | 100% |
| C3 +control-flow flattening | 2 | 1 (`luhn`, public-knowledge) | 50% | 50% |
| C4 Pro L3 opacity | 1 (`luhn` only) | 1 (public-knowledge) | 100% | 0% |
| C5 Pro L3 vault | 1 (`billing_auth` only) | 0 | 0% | 100% |

`billing_auth` (the only non-public-knowledge sample in this pair):
recovered at C0/C1, held at C2/C3/C5 — **identical pattern to Codex**.

### Codex CLI (`gpt-5.6-sol`) — `caesar` + `roman` + `price_rules`

| Condition | Eligible | Recovered | SRR | Resistance |
|---|:---:|:---:|:---:|:---:|
| C0 plaintext | 3 | 3 | 100% | 0% |
| C1 core mangling | 3 | 3 | 100% | 0% |
| C2 +string encryption | 3 | 2 (`caesar`, `roman`) | 67% | 33% |
| C3 +control-flow flattening | 3 | 2 (`caesar`, `roman`) | 67% | 33% |
| C4 Pro L3 opacity | 3 | 2 (`caesar`, `roman`) | 67% | 33% |
| C5 Pro L3 vault | 0 | — | — | (no eligible samples) |

`price_rules` (the only non-public-knowledge sample in this trio): **not
recovered at C2, C3, or C4** — 0% SRR / 100% resistance at every rung it was
tested.

### Claude Code CLI (`sonnet`) — `caesar` + `roman` + `price_rules`

| Condition | Eligible | Recovered | SRR | Resistance |
|---|:---:|:---:|:---:|:---:|
| C0 plaintext | 3 | 3 | 100% | 0% |
| C1 core mangling | 3 | 3 | 100% | 0% |
| C2 +string encryption | 3 | 2 (`caesar`, `roman`) | 67% | 33% |
| C3 +control-flow flattening | 3 | 2 (`caesar`, `roman`) | 67% | 33% |
| C4 Pro L3 opacity | 3 | 2 (`caesar`, `roman`) | 67% | 33% |
| C5 Pro L3 vault | 0 | — | — | (no eligible samples) |

Identical per-sample pattern to Codex: `price_rules` not recovered at C2,
C3, or C4 — 0% SRR / 100% resistance at every rung, independently confirmed
by a second model family.

## The headline finding

**Both non-public-knowledge samples, tested against both model families,
held at every condition from C2 upward — 4-for-4, not a single lucky case:**

| Sample | Codex C2/C3/C4/C5 | Claude C2/C3/C4/C5 |
|---|---|---|
| `billing_auth` (not C4-eligible) | held / held / — / held | held / held / — / held |
| `price_rules` (not C5-eligible) | held / held / held / — | held / held / held / — |

This is the project's first *clean, cross-model-validated* C4 data point.
Prior to this run, the only C4-eligible sample exercised was `luhn`
(public-knowledge, recovered by both models — inconclusive). `price_rules`
closes that gap: two independent, current-generation model families both
failed to statically recover custom business logic protected by Pro L3
Selective Opacity, and both also failed against C2 (string encryption) and
C3 (control-flow flattening) on non-public-knowledge samples.

Core mangling alone (C1) provides no resistance against either model —
consistent with this project's own positioning that Core is not a defense
against LLM analysis; only L2 encryption and L3 opacity/vault are marketed
as raising that specific cost.

## Why two model families is enough (decision, 2026-08-01)

The benchmark design left open whether a third model family was needed
before treating this as a *credible public* result. Decision: no — Codex
(OpenAI) and Claude (Anthropic) are, as of this pilot, generally regarded as
two of the current leading model families for code understanding, and they
independently agree on every non-public-knowledge sample and condition
tested. Adding a third family would strengthen the claim further, but the
marginal value is lower than the cost of doing so today; revisit if a
reviewer specifically asks for it during any future publication process.

## What's still open

- This is an internally-verified result, not yet a *published, reviewed*
  one. A future publication effort (the dual-track research paper mentioned
  in `docs/LLM_RESISTANCE_BENCHMARK.md` and `docs/ROADMAP.md`'s P2-18 entry)
  would need a larger sample count per condition for statistical claims — 5
  samples is enough to *demonstrate the method and get a first real signal*,
  not enough for a confidence interval.
- `results.json`/`report.md` for each individual run stay gitignored by
  design (`benchmarks/llm_resistance/README.md`); this file is the
  deliberate, reviewed copy that instruction calls for.
- A `--llm-resistant` preset remains deferred until/unless product demand
  justifies building one; this pilot's purpose was evidence, not to
  greenlight a new CLI flag.
