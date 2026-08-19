# Obfuscate, then load through a custom import hook

This example pairs pyobfus with a **custom import hook** (the same loading
model SOURCEdefender's `.pye` files use). pyobfus renames identifiers in the
source; the import hook loads the (already-obfuscated) module at runtime. The
two run *in series*, not as competitors — see
[`docs/IMPORT_HOOK_COOKBOOK.md`](../../docs/IMPORT_HOOK_COOKBOOK.md).

[`app.py`](app.py) is a tiny stdlib-only module with deliberately obvious
names. [`loader.py`](loader.py) is a minimal `importlib.abc`
`MetaPathFinder` + `Loader` (no third-party dependency) so the example runs
end-to-end without a paid product.

## Reproduce

```bash
# 1. Obfuscate the source, saving the de-obfuscation map (keep it private!).
pyobfus app.py -o obf/app.py --save-mapping app.map.json

# 2. Load the OBFUSCATED file through the custom import hook.
python loader.py
```

Output:

```
loaded obfuscated module via custom import hook
```

## Verify the original names never reach the hook

The hook only ever sees the obfuscated module, so the original identifiers
are gone from what it loads:

```bash
$ grep -c top_secret_algorithm obf/app.py
0
$ grep -c ConfidentialService obf/app.py
0
```

## Reverse a traceback from the loaded module

If the loaded module crashes, its frames reference obfuscated names. Reverse
them with the saved mapping:

```bash
pyobfus --unmap traceback.txt --mapping app.map.json
```

## SOURCEdefender (.pye) variant

To use a real encrypted-file layer instead of this stdlib loader, replace
step 2 with:

```bash
sourcedefender protect obf/app.py   # requires a SOURCEdefender license
python -c "import app"              # loads the .pye through its own hook
```

The obfuscate-first ordering is identical — only the hook implementation
changes.
