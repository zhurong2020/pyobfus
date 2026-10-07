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
# 1. Obfuscate, saving the de-obfuscation map OUTSIDE the folder you ship,
#    and stamping a trace marker so a future reader knows the file is
#    pyobfus-obfuscated.
pyobfus pricing.py -o dist/pricing.py --save-mapping private/pricing.map.json --trace-marker

# 2. Run the obfuscated build until it crashes; capture the traceback.
python dist/pricing.py 2> obf_trace.txt

# 3. Reverse the obfuscated identifiers back to the originals.
pyobfus --unmap --trace obf_trace.txt --mapping private/pricing.map.json
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

## Use the mapping from the same build

Every build writes a new mapping, and names like `I5` mean something different
in each one. Keep each release's mapping next to its version number. The
`# pyobfus:obfuscated id=...` header at the top of each shipped file matches
the `marker_id` field of the mapping that build produced.

If you pass a mapping from another build, the names it does not know are left
as they are, and the ones it does know may be replaced with the wrong
originals. From the next release, `--unmap` prints a warning when the trace
contains obfuscated names that are missing from the mapping:

```
Warning: 3 obfuscated name(s) in the trace are not in this mapping (I3, I5, I7).
The trace may come from a different build; ...
```

No warning does not prove the mapping is right: a different build that happens
to use the same names would pass. The marker id is the reliable check.

## What it does not recover

Only names come back. Line numbers and source lines in the traceback still
refer to the obfuscated file, and string values, comments and the original
source text are not restored. Before pasting a customer's traceback into a
cloud AI assistant, remove any customer data it contains.
