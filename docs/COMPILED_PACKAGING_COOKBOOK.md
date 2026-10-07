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
#    Cython (Python 3.12+ also needs setuptools, which cythonize imports):
#        pip install cython setuptools
#        cythonize -i obf/module.py
#    Nuitka:
#        pip install nuitka
#        python -m nuitka --module obf/module.py --no-pyi-file --remove-output
```

The mapping file (`module.map.json`) is what lets you reverse a production
stack trace later with `pyobfus --unmap --trace <file> --mapping module.map.json`.
Keep it out of the shipped artifact.

## What compiling alone leaves in the binary

Compilers have to keep Python-visible names, because Python code calls
functions, reads attributes and builds tracebacks by name at runtime. Those
names end up as string data inside the compiled module, and stripping the
native symbol table does not remove them.

We measured this on the [`examples/compiled_packaging/`](../examples/compiled_packaging)
module on 2026-10-07 (Linux x86_64, CPython 3.12.3, pyobfus 0.5.30 from PyPI,
Cython 3.3.0, Nuitka 4.2.2 `--module`). The numbers count matching lines in
`strings` output for the compiled `.so`:

| Name in the source | Cython, original | Cython, original, after `strip` | Nuitka, original | Cython or Nuitka, obfuscated first |
|---|---|---|---|---|
| `proprietary_transform` (function) | 7 | 2 | 2 | 0 |
| `ConfidentialEngine` (class) | 7 | 2 | 3 | 0 |
| `"super-secret-value"` (string literal) | 1 | 1 | 1 | 1 |

So obfuscating first is what keeps the original identifiers out of the
binary. It does not hide string literals: Community output keeps them as
written, and a compiler stores them as constants. Do not ship secrets in a
client artifact at all; obfuscation and compilation are not a key-management
scheme.

A scan that finds nothing is not proof that a value cannot be recovered.
Compilers may store constants in encoded or compressed blobs, so treat the
table as a check on these builds, not a guarantee for other versions or modes.

## Nuitka: the `.pyi` stub and `--remove-output`

- **Nuitka writes a `.pyi` stub next to the compiled module by default.** In
  our run it contained every public function and class signature and the
  module-level string constants, in plain text. If you compile the original
  source, that file alone gives your API and constants away. Pass
  `--no-pyi-file`, or do not ship the `.pyi`.
- **`--remove-output` only deletes Nuitka's build directory** after the
  module or executable is produced. It does not strip names or symbols.

## Calling the compiled module

The compiled module exposes the *obfuscated* names, so callers outside the
obfuscated tree have to use those names. If other code imports this module,
either obfuscate those callers in the same run (multi-module below), or keep
the public entry points readable with `exclude_names` in a project config
(see [`pyobfus.yaml.example`](https://github.com/zhurong2020/pyobfus/blob/main/pyobfus.yaml.example)).
Any name you keep that way is also readable in the binary.

## Multi-module projects

Obfuscate the whole project directory before compiling:

```bash
pyobfus src/ -o obf/ --save-mapping module.map.json
# then cythonize / nuitka the obfuscated tree
```

pyobfus output is ordinary importable Python, so the compiler's dependency
analysis runs on it the same way it runs on any source. What we have not
verified is a whole project: reflection (`getattr` with string names),
dynamic imports, data files and plugin entry points can break after renaming
or be missed by the compiler. Run your own tests against the compiled output,
not only against the obfuscated source.

## Tracebacks from compiled code

Nuitka-compiled modules still produce Python tracebacks, with the obfuscated
names in them. In the run above, a `TypeError` raised inside the compiled
module named the function `I4`; `pyobfus --unmap --trace tb.txt --mapping
module.map.json` turned that back into `proprietary_transform`. Nuitka also
reports the module's file as `module.py` even though only the `.so` was
present.

## When this is (and isn't) enough

This pairing gives you compiled delivery **plus** AST-level name protection,
for free (Community Edition) or with AES-256 string encryption added (Pro
Edition, `--string-encryption`). It does **not** give you PyArmor's
bytecode-level encryption or SOURCEdefender's load-time `.pye` encryption.
If a single module is your crown jewel, layering one of those on that module
on top of this pipeline is a reasonable escalation. See
[`COMPARISON.md`](COMPARISON.md) for the tool-by-tool tradeoff table.

## Evidence and status

- One manual run on the date and versions above, Linux only, single-module
  example, Nuitka `--module` mode. Standalone/onefile executables, macOS,
  Windows and multi-module projects were not part of it.
- The compiled modules returned the same results as the pure-Python originals
  for the example's functions.
- The 2026-10-07 manual measurements above remain historical evidence.
- The new `packaging-lane.yml` runs `integration_tests/test_packaging.py` with
  pinned Cython 3.3.0 / Nuitka 4.2.2 on Linux CPython 3.12, weekly on main and
  on relevant fixture/workflow PRs. Local execution passed on 2026-10-08; the
  first hosted run is pending. The tests hide the generated source, require
  native-module execution, compare both fixture outcomes and reverse a
  TypeError traceback via `--unmap --json`. They also check the two original
  function/class identifiers are absent in these binaries and no `.pyi` is
  emitted. This scope excludes multi-module and Nuitka standalone/onefile builds.
