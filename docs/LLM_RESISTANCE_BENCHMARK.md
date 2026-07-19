# LLM-Deobfuscation-Resistance Benchmark (P2-18)

**Status**: design + first-cut harness (v0, benchmark-only). Roadmap item P2-18.

**One-line goal**: publish a reproducible *semantic-recovery rate* — the fraction
of obfuscated code samples whose original behavior an LLM can reconstruct — for
pyobfus across a ladder of obfuscation strengths, and show that the Pro L3
mechanisms (Selective Opacity / String Vault) drive it toward zero because the
semantics are no longer present in the shipped artifact.

This is the "benchmark-only first cut" the ROADMAP scopes at 2–3 days. It is
both launch content ("no competitor can credibly quantify resistance *to AI*")
and the seed for a separate research paper (SPRO / ESORICS / ACSAC or JSS/EMSE +
an arXiv cs.CR preprint) — distinct from the desk-rejected JOSS software paper.

---

## Why this is on-brand and defensible

pyobfus is an **AST-based, AI-native** obfuscator. Every competitor markets
against human reverse-engineering; none quantifies resistance against an LLM
analyst, which is the 2025–26 threat that actually matters:

- LLM code-deobfuscation moved from fringe to a research hotspot: fine-tuned
  models unwind up to 7 chained transforms and beat compiler-based deobfuscation
  ([CISPA/Springer 2025](https://link.springer.com/content/pdf/10.1007/978-3-031-97620-9_15.pdf);
  [arXiv 2505.19887](https://arxiv.org/pdf/2505.19887)).
- **Acoda** ([arXiv 2606.11755](https://arxiv.org/pdf/2606.11755), 2026-06) —
  *Adversarial Code Obfuscation for Defending against LLM-based Analysis* — is
  direct same-lane prior art. It reports an **Attack Success Rate (ASR)** up to
  70% using a genetic-algorithm search over 8 semantics-preserving transforms,
  scored by an **auxiliary-LLM evaluation framework** across 7 target models
  (GPT-4o, DeepSeek, Qwen, Llama, Gemma). We align our metric vocabulary with it
  and cite it.
- **arXiv 2512.16538** measures obfuscation's effect on LLM code analysis across
  a taxonomy (layout / data-flow / control-flow; 11 subcategories, 19
  techniques), 15 LLMs, 4 languages. Useful for the taxonomy framing.
- **CodeCipher** ([arXiv 2410.05797](https://arxiv.org/abs/2410.05797)) —
  token-level perturbation to hide code from LLMs; a related but different
  (privacy-of-prompt) angle worth citing for completeness.

The pyobfus angle Acoda cannot claim: its transforms are all
*semantics-preserving source rewrites* — the meaning is still in the artifact,
just harder to read, so a strong enough model recovers it. pyobfus L3 (Selective
Opacity, String Vault) **removes the semantics from the artifact**: the function
body / secret ships as AES-256-GCM ciphertext that only materializes at runtime.
There is nothing in the source for an LLM to recover. The benchmark is designed
to make that difference measurable, not rhetorical.

---

## Threat model

- **Attacker**: an LLM analyst given only the obfuscated artifact and the task
  "recover a clean, readable, functionally-equivalent reimplementation, and
  explain what this code does." Static analysis only — the attacker does **not**
  execute the artifact and does **not** possess the mapping file, the layer key,
  or the bound device. (Running the artifact is a separate, out-of-scope threat;
  L3 defends the *source*, not the runtime process.)
- **Defender**: pyobfus, at a chosen condition on the ladder below.
- **Out of scope for v0**: dynamic analysis / memory dumping of a running
  process, key extraction from a bound device, and multi-file whole-project
  recovery (v0 scores per-module; whole-project is a v1 extension).

---

## Obfuscation conditions (the ladder)

Each corpus sample is transformed under every condition, then handed to the
attacker. All conditions are real `pyobfus` CLI invocations (see
`benchmarks/llm_resistance/conditions.py`), so the ladder is reproducible from a
pip install.

| ID | Name | Invocation (essentials) | What is hidden |
|----|------|-------------------------|----------------|
| **C0** | plaintext (control) | *none* | nothing — establishes the attacker's ceiling |
| **C1** | core mangling | `pyobfus --preset aggressive` | identifiers, docstrings |
| **C2** | + string encryption | `pyobfus --preset aggressive --string-encryption` | + string literals (AES) |
| **C3** | + control-flow flattening | `pyobfus --preset aggressive --string-encryption --control-flow` | + control structure |
| **C4** | Pro L3 opacity | `pyobfus SRC -o OUT --level pro --preset maximum --selective-opacity` (marked fns) | **the function body itself** (ciphertext) |
| **C5** | Pro L3 vault | `pyobfus SRC -o OUT --level pro --preset maximum --vault` (marked secrets) | **string secrets** (ciphertext) |

C0–C3 are the "make it harder to read" ladder that Acoda-style semantic recovery
attacks the strongest; C4–C5 are the "not there to read" step-change. The report
plots recovery rate across the ladder so the C3→C4 cliff is the headline figure.

> Note: C4/C5 require the sample to carry an `@opacity(Layer.ENCRYPTED)` marker
> or a `vault_secrets({...})` block. The corpus tags which samples are
> C4/C5-eligible; ineligible samples are scored only on C0–C3 and excluded from
> the C4/C5 aggregates (reported honestly, never silently dropped).

---

## Metrics

### Primary — Semantic-Recovery Rate (SRR), objective

For each (sample, condition, attacker) triple:

1. The attacker returns a clean Python reimplementation.
2. The harness **executes** that reimplementation against the sample's
   ground-truth IO test vectors in an isolated subprocess (timeout + no network).
3. **Recovered = passes ALL vectors** (functional equivalence). Partial credit is
   *not* given for the primary metric — semantic recovery is binary per sample.

`SRR(condition) = recovered_samples / eligible_samples`. Lower is better for the
defender. We report **Resistance = 1 − SRR** as the headline number
("pyobfus reduces LLM semantic-recovery to X%"). This is objective and
LLM-judge-free — the core defensibility property. It is the inverse framing of
Acoda's ASR (their "attack" succeeds when the *defender's* obfuscation defeats
the analyst; our SRR succeeds when the *attacker* defeats the obfuscation).

### Secondary — Comprehension Score (CS), auxiliary-LLM-judged

Aligns with Acoda's auxiliary-LLM framework and captures partial understanding
that functional equivalence misses (the attacker "gets the gist" without a
runnable reimplementation). An auxiliary judge model scores the attacker's
free-text explanation against the sample's ground-truth description on a 0–3
rubric (0 = wrong/no idea, 3 = names purpose + key logic correctly), normalized
to 0–1. Reported per condition as a mean, clearly labeled as the subjective
secondary metric. **CS never overrides SRR** in the headline.

### Reported artifacts

- `results.json` — every triple's raw outcome (deterministic, versioned).
- `report.md` — the ladder table, the C3→C4 cliff figure (as a text/markdown
  chart or a generated PNG), per-model breakdown, and every honest caveat
  (sample count, ineligible-sample exclusions, attacker model + date + params).

---

## Attacker protocol (reproducibility)

- **Pluggable `Attacker` interface** (`attacker.py`): `deobfuscate(obfuscated_src)
  -> AttackResult{reimplementation, explanation}`. Model-agnostic by design.
- **Implementations**:
  - `StubAttacker` — deterministic, offline. Returns the input unchanged; used
    to prove the harness end-to-end and to run in CI without API keys or cost.
    (On C0 it "recovers" trivially since input==original; on C1+ it fails —
    which validates that the scorer actually discriminates.)
  - `AnthropicAttacker` — the real analyst, via the Anthropic API. Fixed model
    id, temperature 0, a frozen prompt (stored in `prompts/`), logged verbatim
    into `results.json` so a run is fully reproducible.
  - (future) `OpenAIAttacker` / others — to reproduce Acoda's multi-model table.
- Every run records: attacker class, model id, prompt hash, pyobfus version,
  Python version, UTC date, per-sample seeds. No `Math.random`/wall-clock
  nondeterminism in the harness itself.

### Fairness rules (so the number is honest, not marketing)

- The attacker gets a strong, neutral prompt (recover + explain), not a
  hobbled one. We are trying to *maximize* recovery, then measure what survives.
- C0 must score near-100% recovery, or the harness/prompt is broken — it is a
  built-in sanity gate, asserted before any C1+ number is trusted (mirrors the
  workspace "pilot gate asserts on success content" rule).
- Timeouts, exceptions, and empty attacker outputs count as **not recovered**,
  never as errors that drop the sample from the denominator.

---

## Directory layout

```
benchmarks/llm_resistance/
  README.md            # how to run (stub + real), how to read results
  conditions.py        # C0-C5 as real pyobfus CLI invocations
  attacker.py          # Attacker ABC + StubAttacker + AnthropicAttacker
  scorer.py            # functional-equivalence executor + comprehension judge
  harness.py           # orchestrator: corpus x conditions x attacker -> results
  report.py            # results.json -> report.md (+ optional PNG)
  prompts/             # frozen attacker + judge prompts (hashed into results)
  corpus/
    <sample>.py        # self-contained module under test
    <sample>.json      # {description, entrypoint, io_vectors, c4_eligible, ...}
  results/             # gitignored run outputs (results.json, report.md)
```

## Roadmap after v0

1. **v0 (this cut)**: harness + scorer + stub proof + 4–6 seed samples +
   `AnthropicAttacker` interface. End-to-end green with the stub.
2. **Measurement run**: expand corpus to ~30 samples across categories, run
   `AnthropicAttacker` (and ≥1 other family for the multi-model table), publish
   `report.md` with real numbers → launch content.
3. **`--llm-resistant` preset** (the "mode" half, 1–2 weeks): a preset the
   benchmark shows moves the needle, if C0–C3 numbers justify it (the ROADMAP
   flags the *mode* as separable from and later than the benchmark).
4. **Research paper**: formalize, add baselines (Acoda transforms, PyArmor,
   Nuitka), scale corpus, arXiv cs.CR preprint → venue.

## Honesty guardrails (non-negotiable)

- Report the exact sample count; never imply a broader corpus than was run.
- Exclude C4/C5-ineligible samples from C4/C5 aggregates *visibly*.
- State the attacker model + date; LLM capability moves, so every number is
  stamped and re-runnable.
- The primary number is functional-equivalence-based, not LLM-judge-based.
- Do not claim resistance the artifact does not have: L3 defends *source
  recovery*, not a running process — say so in the report.
