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

## Codex Plus pilot on Windows (no API key or Docker Desktop)

The Windows pilot can use the Codex CLI's saved ChatGPT sign-in for model
generation and the CLI's native read-only sandbox for scoring generated code.
The adapter removes `OPENAI_API_KEY`, `CODEX_API_KEY`, and
`ANTHROPIC_API_KEY` from the child process, so this path deliberately uses the
interactive `codex login` session rather than API billing.

Install/login once, then download the official Python 3.11.9 embeddable ZIP:

```powershell
npm install --global @openai/codex
codex login

$runtimeZip = "$env:TEMP\python-3.11.9-embed-amd64.zip"
Invoke-WebRequest `
  -Uri "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip" `
  -OutFile $runtimeZip
(Get-FileHash $runtimeZip -Algorithm SHA256).Hash
```

The expected SHA-256 is
`009d6bf7e3b2ddca3d784fa09f90fe54336d5b60f0e0f305c37f400bf83cfd3b`.
The executor rejects any other digest. After the Codex weekly allowance has
reset, start with the explicitly bounded two-call pilot:

```powershell
python benchmarks/llm_resistance/harness.py `
  --attacker codex-cli `
  --model gpt-5.6-sol `
  --sample luhn `
  --condition C0 `
  --condition C1 `
  --executor codex-windows `
  --sandbox-python-zip $runtimeZip
```

Real Codex runs require explicit `--sample` and `--condition` selections to
prevent an accidental full-matrix subscription run. `--judge` is not supported
by this pilot. The generated program runs with a read-only workspace, blocked
network access, isolated Python flags, and an outer timeout. The native Windows
path does not yet impose Docker-equivalent CPU, memory, or process-count caps;
review a one-sample pilot before expanding it and disclose that limitation with
any result.

## Anthropic API alternative

For maintainers who choose that provider, install the Anthropic SDK, set
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
- Docker scoring uses disabled networking, a read-only filesystem, dropped
  capabilities, and CPU/memory/process limits. The Codex Windows alternative
  uses the native read-only/network-blocked sandbox plus an outer timeout, with
  the resource-cap limitation noted above.
- A credible public result still requires a real attacker run, ideally across
  at least two model families and a larger corpus.
