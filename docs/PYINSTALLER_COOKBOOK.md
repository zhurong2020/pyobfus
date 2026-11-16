# PyInstaller Cookbook: obfuscate, then bundle to a single exe

Teams that want to ship a **single-file executable** protecting their
Python source usually look at Nuitka Commercial (~$270/year, compiles to
native code) or Sourcedefender. pyobfus takes a different, cheaper path to
the same delivery format: obfuscate the source first, then let
[PyInstaller](https://pyinstaller.org/) freeze the *obfuscated* code into a
single binary. PyInstaller uses **GPL-2.0-or-later with a bootloader/bundling
exception permitting distribution of non-free programs**; see its
[official licence](https://pyinstaller.org/en/stable/license.html).

pyobfus and PyInstaller solve different problems and compose rather than
compete: pyobfus renames identifiers and (on Pro) encrypts strings;
PyInstaller bundles a Python interpreter plus your code into one
executable. Neither replaces the other.

## Does PyInstaller protect your source code?

Not by itself. PyInstaller is a packaging tool: it puts your compiled bytecode
and a Python interpreter into one executable so the customer does not need
Python installed. Public tools such as `pyinstxtractor` can extract archive
members. Extracted bytecode retains Python-visible names and can be inspected
or disassembled; reconstructing readable Python with a decompiler depends on
the bytecode version and the decompiler's coverage. PyInstaller 6.0 also removed
the old `--key` bytecode-encryption option, which was easy to undo anyway.

If you want the unpacked code to be harder to read, obfuscate it before you
bundle it. That is the workflow below. Keep secrets such as API keys out of
the executable whichever way you build it.

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
a compressed self-extracting binary), but archive extraction is separate
from bytecode decompilation. The documented bytecode coverage of
[`uncompyle6`](https://github.com/rocky/python-uncompyle6) and
[`decompyle3`](https://github.com/rocky/python-decompile3) targets older versions;
do not assume either reconstructs source for the full Python 3.9–3.15 range.
Extraction and disassembly can still expose names and behavior when source
reconstruction is unsupported. PyInstaller is a distribution tool. Running
pyobfus first means the extracted code is already obfuscated, subject to the
preserved names and protection settings you chose.

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
protection, for free (Community Edition) or with AES-128-CBC with HMAC-SHA256 (Fernet) string encryption
added (Pro Edition, `--string-encryption`). It does **not** give you
Nuitka's native-code compilation or PyArmor's bytecode-level encryption —
if a single algorithm module is your crown jewel, layering PyArmor Pro or
Nuitka on that one module on top of this pipeline is a reasonable
escalation. See [`COMPARISON.md`](COMPARISON.md) for the full
tool-by-tool tradeoff table.


## Automated example checks

`packaging-lane.yml` runs `integration_tests/test_packaging.py` with PyInstaller
6.22.3 on Linux CPython 3.12: the maintained stdlib-only pricing CLI is
obfuscated, bundled with `--onefile`, and run for all three tiers after the
generated source is hidden. Output must match the original; an invalid tier
must raise and its bundled traceback must reverse through `--unmap --json`.
The mapping remains outside the shipped directory. Local execution passed on
2026-10-08; the [first hosted run](https://github.com/zhurong2020/pyobfus/actions/runs/37690761303) also passed. The workflow runs weekly on main
and on PRs that change the obfuscator, the fixtures or the workflow.

Since 2026-10-11 the lane also freezes a multi-module project
([`integration_tests/packaging/multimodule/`](https://github.com/zhurong2020/pyobfus/tree/main/integration_tests/packaging/multimodule):
a package, a subpackage, relative imports and an entry script) obfuscated as a
directory. Every frozen module in the bundle is checked for the renamed
original names, the executable must match the original for three tiers, and a
traceback crossing three modules must reverse through `--unmap --json`
([hosted run](https://github.com/zhurong2020/pyobfus/actions/runs/38107417778)). Other platforms, third-party dependencies and larger
projects remain outside this evidence.
