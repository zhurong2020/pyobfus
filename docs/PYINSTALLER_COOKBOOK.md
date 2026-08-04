# PyInstaller Cookbook: obfuscate, then bundle to a single exe

Teams that want to ship a **single-file executable** protecting their
Python source usually look at Nuitka Commercial (~$270/year, compiles to
native code) or Sourcedefender. pyobfus takes a different, cheaper path to
the same delivery format: obfuscate the source first, then let
[PyInstaller](https://pyinstaller.org/) — free, MIT-licensed, and already
the most widely used Python bundler — freeze the *obfuscated* code into a
single binary.

pyobfus and PyInstaller solve different problems and compose rather than
compete: pyobfus renames identifiers and (on Pro) encrypts strings;
PyInstaller bundles a Python interpreter plus your code into one
executable. Neither replaces the other.

## The workflow

```bash
# 1. Obfuscate the source, saving a de-obfuscation map you keep private.
pyobfus app.py -o obf_app.py --save-mapping app.map.json

# 2. Bundle the OBFUSCATED file (not the original) with PyInstaller.
pip install pyinstaller
pyinstaller --onefile --name app obf_app.py

# 3. Ship dist/app. The identifier names inside the binary are already
#    mangled — PyInstaller never sees, and therefore can't leak, your
#    original names.
./dist/app
```

For a full working reproduction — including verifying the original
identifier names never make it into the compiled binary, and that a crash
captured from the *bundled* executable still reverses cleanly with
`pyobfus --unmap` — see
[`examples/pyinstaller/`](https://github.com/zhurong2020/pyobfus/tree/main/examples/pyinstaller)
in the repository. That example was run end-to-end (not just described) to
produce this page.

## Why obfuscate before bundling, not after

PyInstaller's `--onefile` output already looks opaque to a casual user (it's
a compressed self-extracting binary), but the *Python bytecode* inside is
trivially recoverable with public tools (`pyinstxtractor` + `uncompyle6` /
`decompyle3` are the standard combination) — PyInstaller was never designed
as a protection mechanism, only a distribution one. Running pyobfus first
means whatever a determined recipient extracts back out is the
already-obfuscated `.py`/bytecode, with mangled identifiers, not your
original source.

## Multi-module projects

If your app spans more than one file, obfuscate the whole project directory
before pointing PyInstaller at the entry script — see the
[`multifile`](https://github.com/zhurong2020/pyobfus/tree/main/examples/multifile)
example for a project-level `pyobfus.yaml` config. PyInstaller's dependency
analysis (`--onefile`'s module discovery) works the same way against
obfuscated modules as against the originals, since the obfuscated output is
still ordinary importable Python.

## When this is (and isn't) enough

This pairing gets you single-binary distribution with AST-level name
protection, for free (Community Edition) or with AES-256 string encryption
added (Pro Edition, `--string-encryption`). It does **not** give you
Nuitka's native-code compilation or PyArmor's bytecode-level encryption —
if a single algorithm module is your crown jewel, layering PyArmor Pro or
Nuitka on that one module on top of this pipeline is a reasonable
escalation. See [`COMPARISON.md`](COMPARISON.md) for the full
tool-by-tool tradeoff table.
