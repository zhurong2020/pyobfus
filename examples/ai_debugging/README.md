# Reverse-mapping demo: debugging an obfuscated traceback

This example reproduces pyobfus's signature feature end to end: a crash in
**obfuscated** code produces a traceback with mangled names, and `pyobfus
--unmap` translates it back to the original names so a developer — or an AI
assistant working on their behalf — can locate the bug without the
de-obfuscation map being shipped to the recipient.

[`pricing.py`](pricing.py) has a latent bug: `order_total` reads a
`discount_rate` key that the cart items do not contain, raising `KeyError`.

## Reproduce

```bash
# 1. Obfuscate, saving the de-obfuscation map (keep it private!) and stamping
#    a trace marker so a future reader knows the file is pyobfus-obfuscated.
pyobfus pricing.py -o dist/pricing.py --save-mapping dist/pricing.map.json --trace-marker

# 2. Run the obfuscated build until it crashes; capture the traceback.
python dist/pricing.py 2> obf_trace.txt

# 3. Reverse the obfuscated identifiers back to the originals.
pyobfus --unmap --trace obf_trace.txt --mapping dist/pricing.map.json
```

## What you see

The **obfuscated** traceback is opaque — every name is mangled:

```
  File "dist/pricing.py", line 14, in I5
    I1 = I7 * I3[0]['discount_rate']
KeyError: 'discount_rate'
```

After `--unmap`, the original names are restored, pointing straight at the bug:

```
  File "dist/pricing.py", line 14, in order_total
    discount = subtotal * line_items[0]['discount_rate']
KeyError: 'discount_rate'
```

`I5 → order_total`, `I7 → subtotal`, `I3 → line_items`. The shipped artifact
stays obfuscated; only the holder of `pricing.map.json` can perform this
reversal. This keeps the AI-assisted debugging loop intact on protected code.
