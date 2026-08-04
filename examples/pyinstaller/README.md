# Obfuscate, then bundle to a single executable

This example pairs pyobfus with [PyInstaller](https://pyinstaller.org/) to
ship a **single-file, name-mangled executable** — the workflow teams reach
for Nuitka Commercial or Sourcedefender for. pyobfus doesn't compile to
native code, so it can't replace PyInstaller's bundling step; it runs
*before* it, protecting the source PyInstaller then freezes.

[`app.py`](app.py) is a small stdlib-only pricing CLI (no third-party
imports, so the only thing that can go wrong in this example is the
obfuscate → bundle → run pipeline itself, not dependency discovery).

## Reproduce

```bash
# 1. Obfuscate, saving the de-obfuscation map (keep it private!).
pyobfus app.py -o obf_app.py --save-mapping app.map.json

# 2. Bundle the OBFUSCATED file, not the original.
pip install pyinstaller
pyinstaller --onefile --name app obf_app.py

# 3. Run the single-file binary.
./dist/app enterprise
```

Output:

```
List price: $100.00
Tier: enterprise
Final price: $70.00
```

## What actually ends up in the binary

The obfuscated source is what PyInstaller freezes, so the original
identifier `apply_discount` never reaches the binary — only the mangled
name (`I0` in a typical run; pyobfus's mangling is per-build) does:

```bash
$ strings dist/app | grep -c apply_discount
0
$ strings dist/app | grep -c I0
22
```

## The obfuscation survives the bundle, and so does reverse-mapping

A crash from the *bundled binary* still produces a traceback with mangled
names — bundling doesn't change that:

```
Traceback (most recent call last):
  File "obf_app.py", line 20, in main
    I2 = I0(I3, I4)
  File "obf_app.py", line 14, in I0
    raise ValueError(f'Unknown pricing tier: {I4}')
ValueError: Unknown pricing tier: bogus_tier
```

`pyobfus --unmap` reverses it exactly as it would for a non-bundled
deployment — the mapping file doesn't care whether the `.py` it was
generated from ever got frozen into an executable:

```bash
pyobfus --unmap --trace crash_trace.txt --mapping app.map.json
```

```
  File "obf_app.py", line 20, in main
    final_price = apply_discount(price, tier)
  File "obf_app.py", line 14, in apply_discount
    raise ValueError(f'Unknown pricing tier: {tier}')
ValueError: Unknown pricing tier: bogus_tier
```

This is the same AI-debuggable-in-production story as the
[`ai_debugging`](../ai_debugging/) example — bundling to a single exe for
distribution doesn't cost you the ability to reverse a production
traceback back to readable names.

## Notes

- Obfuscate the *entire project* before pointing PyInstaller at the entry
  script, not just the entry file, if your app spans multiple modules —
  see the [`multifile`](../multifile/) example for a project-level
  `pyobfus.yaml` config.
- PyInstaller's own name-mangling-adjacent option (`--strip`) only strips
  debug symbols from the compiled bootloader; it does not touch your
  Python source's identifier names. pyobfus and PyInstaller solve
  different problems and are not substitutes for each other.
- This example was verified end-to-end with pyobfus 0.5.7 and PyInstaller
  6.21.0 on Linux (`--onefile`); Windows/macOS builds follow the same
  two-step obfuscate-then-bundle order, only the PyInstaller invocation
  differs per PyInstaller's own platform docs.
