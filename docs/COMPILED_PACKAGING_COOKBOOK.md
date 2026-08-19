# Compiled packaging Cookbook: obfuscate, then compile (Nuitka / Cython)

Teams that want to ship **compiled** Python — [Nuitka](https://nuitka.net/)
(native code) or [Cython](https://cython.org/) (C extension modules) — are
solving a *delivery format* problem. pyobfus solves a different, earlier
problem: AST-level identifier renaming applied to the *source* before it is
compiled.

The two compose rather than compete: **obfuscate the pure-Python source
first, then compile the obfuscated output.** Neither replaces the other, and
the ordering matters (see below).

## The workflow

```bash
# 1. Obfuscate the pure-Python module(s), keeping the map private.
pyobfus src/module.py -o obf/module.py --save-mapping module.map.json

# 2. Compile the OBFUSCATED file (not the original).
#    Cython:
#        cythonize -i obf/module.py
#    Nuitka:
#        python -m nuitka --module obf/module.py
```

The mapping file (`module.map.json`) is what lets you reverse a production
stack trace later with `pyobfus --unmap` — keep it out of the shipped
artifact.

## Why obfuscate before compiling

Nuitka and Cython preserve the original Python **identifier names** in the
compiled artifact's symbol table and debug strings unless you specifically
strip them. If you compile the *original* source, a determined reader
recovers your original function/class/variable names straight out of the
binary. Run pyobfus first, and what gets compiled is already-mangled source,
so the recovered symbol names are the obfuscated ones, not your originals.

> Note: also pass the compiler's own name-stripping flags (e.g. Nuitka
> `--remove-output` + your strip step, Cython `--no-docstrings`) for defense
> in depth — pyobfus handles the *source* names; the compiler handles the
> *binary* symbols.

## Multi-module projects

Obfuscate the whole project directory before compiling, via a project-level
[`pyobfus.yaml`](../pyobfus.yaml):

```bash
pyobfus src/ -o obf/ --save-mapping module.map.json
# then cythonize / nuitka the obfuscated tree
```

pyobfus output is still ordinary importable Python, so the compiler's
dependency analysis works against the obfuscated modules exactly as it would
against the originals.

## When this is (and isn't) enough

This pairing gives you compiled delivery **plus** AST-level name protection,
for free (Community Edition) or with AES-256 string encryption added (Pro
Edition, `--string-encryption`). It does **not** give you PyArmor's
bytecode-level encryption or SOURCEdefender's load-time `.pye` encryption —

if a single module is your crown jewel, layering one of those on that module
on top of this pipeline is a reasonable escalation. See
[`COMPARISON.md`](COMPARISON.md) for the full tool-by-tool tradeoff table.

A runnable end-to-end reproduction (using Cython, which is free) is in
[`examples/compiled_packaging/`](../examples/compiled_packaging). That
example was run end-to-end (not just described) to produce this page.
