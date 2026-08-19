# Model-serving Cookbook: keep the mapping for reverse stack traces

ML / model-serving projects (PyTorch, TensorFlow, Keras, scikit-learn,
transformers, joblib) are a first-class supported scenario in pyobfus — the
`ml` preset and the automatic model-artifact detection exist precisely for
this case. This cookbook focuses on the one thing that surprises teams
*after* shipping: **debugging a production traceback from obfuscated
serving code.**

## The core rule: save the mapping, ship the obfuscated model code

```bash
# Obfuscate the serving module with the ML preset and a trace marker.
pyobfus serve.py -o obf_serve.py \
    --preset ml \
    --save-mapping serve.map.json \
    --trace-marker
```

- `--preset ml` preserves the framework's reflection-sensitive names so the
  model still loads and predicts.
- `--save-mapping` produces `serve.map.json` — the private key to reversing
  a traceback. **Do not ship it.**
- `--trace-marker` writes a recoverable hint into the output file so an AI
  agent or developer can locate the mapping file selector when a traceback
  arrives.

## Reversing a production traceback

When a crash is captured from the *serving* process, its frames reference
obfuscated names. Reverse them with:

```bash
pyobfus --unmap traceback.txt --mapping serve.map.json
```

The output maps each obfuscated symbol back to its original, readable name.
This is what makes pyobfus "AI-debuggable" — the workflow survives
obfuscation instead of fighting it. See
[`pyobfus --unmap`](../README.md) and the VS Code *Reverse Stack Trace*
command (which auto-locates the mapping via the trace marker).

## Hide weight / model paths (Pro)

Model artifact paths embedded in source (`weights/classifier.safetensors`,
`checkpoints/...`) are detected by `--check` as
`model_artifact_literal`. On Pro, wrap them so they route through the
Runtime String Vault instead of sitting as plaintext in the binary:

```python
from pyobfus_pro import vault_secrets

MODEL_PATH = vault_secrets({"path": "weights/classifier.safetensors"})
```

then run with `--vault`. See
[`PROVENANCE_MANIFEST.md`](PROVENANCE_MANIFEST.md) for the surrounding
supply-chain record.

## Unsafe deserialization is still your job

`--check` separately flags `pickle.load` / `torch.load` without
`weights_only=True` as `unsafe_deserialization` (high severity) — obfuscation
does nothing to make loading untrusted artifacts safe. Prefer `safetensors`
or ONNX where possible, and validate artifact provenance before loading.

## When this is (and isn't) enough

This pairing gives you AST-level name protection on model-serving code with
working reverse-debugging, for free (Community Edition) or with string
vaulting added (Pro Edition). It does **not** encrypt the model *weights*
themselves (use the framework's own encryption or a vault for that) — see
[`COMPARISON.md`](COMPARISON.md) for the full tool-by-tool tradeoff table.
