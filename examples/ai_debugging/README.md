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

With Core 0.15.0, the crash excerpt looks like this (paths shortened to the
demo directory; parameters such as `line_items` are preserved by default):

```
  File "dist/pricing.py", line 18, in I4
    I1 = I5 * line_items[0]['discount_rate']
KeyError: 'discount_rate'
```

After `--unmap`, the original names are restored, pointing straight at the bug:

```
  File "pricing.py", line 13, in order_total  [obfuscated: dist/pricing.py:18]
    discount = subtotal * line_items[0]['discount_rate']
KeyError: 'discount_rate'
```

`I4 → order_total`, `I5 → subtotal`, `I1 → discount`. The shipped artifact
stays obfuscated; only the holder of `pricing.map.json` can perform this
reversal. This keeps the AI-assisted debugging loop intact on protected code.

## Use the mapping from the same build

Community name mappings are deterministic for unchanged input and
configuration. Changes to the source, configuration or tool version can change
what short names such as `I5` mean, so always use the matching build's mapping.
Keep each release's mapping next to its version number. The
`# pyobfus:obfuscated id=...` header at the top of each shipped file matches
the `marker_id` field of the mapping that build produced.

If you pass a mapping from another build, the names it does not know are left
as they are, and the ones it does know may be replaced with the wrong
originals. From pyobfus 0.5.31, `--unmap` prints a warning when the trace
contains obfuscated names that are missing from the mapping:

```
Warning: 3 obfuscated name(s) in the trace are not in this mapping (I3, I5, I7).
The trace may come from a different build; ...
```

No warning does not prove the mapping is right: a different build that happens
to use the same names would pass. The marker id is the reliable check.

## What it does not recover

Mappings generated since Core 0.7.0 can also restore original relative
files and statement starting lines in standard frames, keeping output positions
visible; older mappings restore names only. Version-1 mappings rewrite excerpt
identifiers but leave caret positions unchanged. Version-2 independent-file
mappings leave excerpts and unframed logs untouched. String values, comments
and the original source text are not reconstructed. Before pasting a customer's
traceback into a cloud AI assistant, remove any customer data it contains.
