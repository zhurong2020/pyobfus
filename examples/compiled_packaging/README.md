# Obfuscate, then compile (Cython / Nuitka)

This example pairs pyobfus with **compiled packaging** — Cython (free) here,
Nuitka as a drop-in alternative. pyobfus renames identifiers in the *source*;
the compiler turns that source into a C extension / native binary. The two
run *in series*, not as competitors — see
[`docs/COMPILED_PACKAGING_COOKBOOK.md`](../../docs/COMPILED_PACKAGING_COOKBOOK.md).

[`module.py`](module.py) is a tiny stdlib-only module with deliberately
obvious names.

## Reproduce (Cython)

```bash
# 1. Obfuscate the pure-Python source, saving the map (keep it private!).
pyobfus module.py -o obf_module.py --save-mapping module.map.json

# 2. Compile the OBFUSCATED file, not the original.
pip install cython
cythonize -i obf_module.py
```

## Verify original names don't survive into the compiled artifact

The compiler only ever sees the obfuscated source, so the original
identifiers never reach the generated C:

```bash
$ grep -c proprietary_transform obf_module.py
0
$ grep -c proprietary_transform obf_module.c
0
```

## Nuitka variant

```bash
pip install nuitka
python -m nuitka --module obf_module.py
```

The obfuscate-first ordering is identical — only the compiler changes.

## Reverse a traceback from the compiled module

If the compiled module crashes, its frames reference obfuscated names.
Reverse them with the saved mapping:

```bash
pyobfus --unmap traceback.txt --mapping module.map.json
```
