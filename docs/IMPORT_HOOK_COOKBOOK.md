# Import-hook / encrypted-file Cookbook: obfuscate, then hook

Teams that want to ship Python that loads through a custom **import hook** or
an **encrypted-file** layer (the most visible example being
[SOURCEdefender](https://www.sourcedefender.com/) and its `.pye` files) are
solving a *loading-time* protection problem. pyobfus solves a different,
earlier problem: AST-level identifier renaming (and, on Pro, string
encryption) applied to the *source* before anything else touches it.

The two compose rather than compete: **obfuscate the source first, then hand
the obfuscated file to the import hook / encryption layer.** Neither replaces
the other, and the ordering matters (see below).

## The workflow

```bash
# 1. Obfuscate the pure-Python source, keeping the de-obfuscation map private.
pyobfus src/app.py -o obf/app.py --save-mapping app.map.json

# 2. Pass the OBFUSCATED file (not the original) to the import hook / .pye layer.
#    SOURCEdefender (requires a license):
#        sourcedefender protect obf/app.py
#    or your own custom import hook (see examples/import_hook/):
#        python -m your_loader obf/app.py
```

The mapping file (`app.map.json`) is what lets you reverse a production
stack trace later with `pyobfus --unmap` — keep it out of the shipped
artifact.

## Why obfuscate before the hook / encryption

An import hook decrypts `.pye` (or custom-encrypted) modules back into
ordinary Python *at load time*, then executes them. If you encrypt the
**original** source, whatever the hook recovers is still your original,
fully-readable code — you've paid for encryption but leaked the names it was
supposed to hide. Run pyobfus first, and the hook only ever sees (and only
ever decrypts) already-mangled identifiers, so the recovered-in-memory code
is the obfuscated form, not your originals.

## Multi-module projects

Obfuscate the whole project directory before pointing the import hook at the
entry script — write a project-level [`pyobfus.yaml`](../pyobfus.yaml) and
run:

```bash
pyobfus src/ -o obf/ --save-mapping app.map.json
# then protect/load the obfuscated tree with your hook
```

Because pyobfus output is still ordinary importable Python, the hook's own
dependency analysis works against the obfuscated modules exactly as it would
against the originals.

## When this is (and isn't) enough

This pairing gives you load-time encryption **plus** AST-level name
protection, for free (Community Edition) or with AES-256 string encryption
added (Pro Edition, `--string-encryption`). It does **not** give you
native-code compilation (Nuitka) or bytecode-level encryption (PyArmor) — if
a single module is your crown jewel, layering PyArmor Pro or Nuitka on that
one module on top of this pipeline is a reasonable escalation. See
[`COMPARISON.md`](COMPARISON.md) for the full tool-by-tool tradeoff table.

A runnable end-to-end reproduction (using a stdlib custom import hook, no
paid dependency required) is in
[`examples/import_hook/`](../examples/import_hook). That example was run
end-to-end (not just described) to produce this page.
