# Dual License Notice

pyobfus uses a dual licensing model:

1. **pyobfus (Core Module) — Apache License 2.0**
   The core obfuscation engine is open source and free to use.
   See [`LICENSE`](LICENSE) for the full Apache License 2.0 text.

2. **pyobfus_pro (Pro Module) — Proprietary License**
   Pro features require a paid license.
   See [`pyobfus_pro/LICENSE`](pyobfus_pro/LICENSE) for terms.

The f-string unparser methods in `pyobfus/core/unparse.py` are adapted from
CPython 3.13 `Lib/ast.py`, copyright Python Software Foundation, under the
[PSF License Version 2](LICENSE-PSF.txt). They are isolated in a version-gated
subclass and use qualified AST names to backport quote selection to affected
CPython 3.12 builders; the original Python distribution is not modified.
