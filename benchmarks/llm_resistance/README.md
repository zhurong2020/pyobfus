# LLM resistance benchmark

This directory measures whether an attacker model can reconstruct a clean,
functionally equivalent implementation from a pyobfus artifact. The complete
method and threat model are in
[`docs/LLM_RESISTANCE_BENCHMARK.md`](../../docs/LLM_RESISTANCE_BENCHMARK.md).

## Offline validation

The stub attacker proves that corpus transformation, functional scoring, and
report generation work without an API key:

```bash
pytest benchmarks/llm_resistance/test_smoke.py -v --no-cov
python benchmarks/llm_resistance/harness.py --attacker stub
```

Stub numbers are a harness self-test, not evidence about an LLM, and must never
be published as model-resistance results.

## Real measurement

Install the Anthropic SDK in an isolated environment, set
`ANTHROPIC_API_KEY`, choose and pre-pull a pinned Python container image, and
pass an explicit currently available model id. Model-generated code is
untrusted, so the real-attacker path defaults to a no-network, read-only Docker
executor:

```bash
pip install anthropic
docker pull python:3.12-alpine
python benchmarks/llm_resistance/harness.py \
  --attacker anthropic --model MODEL_ID --judge \
  --docker-image python:3.12-alpine
```

For a publication run, replace the floating image tag with an immutable digest.
Host execution of real model output is rejected unless
`--unsafe-host-execution` is supplied explicitly.

Outputs are written to the ignored `results/` directory. Before publishing,
verify that C0 is near 100% recovery, inspect every failure, and deliberately
copy the reviewed report/result into a versioned documentation location. Never
commit an API key or raw provider response that may contain sensitive data.

## Current scope

- Five seed samples and six conditions (C0-C5).
- Static source analysis only; runtime memory extraction is out of scope.
- Functional equivalence is the primary score. The optional judge only scores
  the prose explanation.
- Real attacker output is scored with Docker networking disabled, a read-only
  filesystem, dropped capabilities, and CPU/memory/process limits.
- A credible public result still requires a real attacker run, ideally across
  at least two model families and a larger corpus.
