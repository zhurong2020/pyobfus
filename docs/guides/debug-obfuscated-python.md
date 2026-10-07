---
title: Debug obfuscated Python tracebacks
description: Keep a private build mapping, restore identifiers from a production traceback, and investigate the failure with your editor or coding assistant.
---

# How to debug an obfuscated Python traceback

You shipped obfuscated Python, a customer hits an error, and the traceback
they send back says `in I5` and `I1 = I7 * I3[0]['discount_rate']`. This page
shows how to turn that back into your own names so you, or a coding
assistant, can find the bug, without giving the customer anything that
reverses the obfuscation.

The short version: save a mapping file when you build, keep it private, and
run `pyobfus --unmap` on the traceback with the mapping from that same build.

## Before you start

- pyobfus installed (`pip install pyobfus`). Everything on this page works in
  the free Community Edition.
- You need the mapping file **from the build the customer is running**.
  Without it, the names cannot be recovered; that is the point of
  obfuscating.

The commands and output below were run on 2026-10-07 with pyobfus 0.5.30
from PyPI on Linux, Python 3.12, using
[`examples/ai_debugging/pricing.py`](https://github.com/zhurong2020/pyobfus/tree/main/examples/ai_debugging).
File paths in the traces are shortened.

## 1. Build with a private mapping

```bash
pyobfus pricing.py -o dist/pricing.py \
  --save-mapping private/pricing.map.json --trace-marker
```

- `dist/` is what you ship. `private/` is not: put the mapping anywhere that
  never ends up in the release archive, a public CI artifact, or an issue.
- `--trace-marker` adds a short header to each shipped file with an id for
  this build and the command for reversing a trace:

  ```
  # pyobfus:obfuscated id=bb23a926 mapping=pricing.map.json
  # Obfuscated with pyobfus (https://github.com/zhurong2020/pyobfus). The original names are recoverable.
  # To de-obfuscate a traceback from this file:
  #   pyobfus --unmap --trace <logfile> --mapping pricing.map.json
  ```

  The same id is stored as `marker_id` inside the mapping file. The header
  tells anyone who opens the file that names can be recovered with the
  mapping; it does not contain the mapping.

Store each release's mapping under its version number, for example
`private/maps/1.4.2/pricing.map.json`. Every build produces new names, so a
mapping only fits the build it came from.

## 2. Get the traceback

The customer, or your error reporting, sends something like this:

```
Traceback (most recent call last):
  File ".../dist/pricing.py", line 22, in <module>
    print(I5(I0))
          ^^^^^^
  File ".../dist/pricing.py", line 18, in I5
    I1 = I7 * I3[0]['discount_rate']
              ~~~~~^^^^^^^^^^^^^^^^^
KeyError: 'discount_rate'
```

Save it to a file, for example `error.log`.

## 3. Restore the names

```bash
pyobfus --unmap --trace error.log --mapping private/pricing.map.json
```

```
Traceback (most recent call last):
  File ".../dist/pricing.py", line 22, in <module>
    print(order_total(cart))
          ^^^^^^
  File ".../dist/pricing.py", line 18, in order_total
    discount = subtotal * line_items[0]['discount_rate']
              ~~~~~^^^^^^^^^^^^^^^^^
KeyError: 'discount_rate'
```

`I5` is `order_total`, `I7` is `subtotal`, `I3` is `line_items`. The bug is
the `discount_rate` lookup in `order_total`.

Add `--json` to get the original and restored trace in one object, which is
easier to hand to a script or an agent.

## What comes back, and what does not

- **Names come back**: functions, classes, methods, variables and parameters
  that pyobfus renamed.
- **Line numbers do not**. They point into the obfuscated file. Above,
  line 18 of `dist/pricing.py` is line 13 of the original, because the
  output has header lines and no comments or docstrings. Search your source
  for the restored line text instead.
- **The `^^^^` markers are not adjusted**. They were placed under the
  obfuscated text, so after renaming they point at the wrong columns.
- **Source text is not restored**. Only identifiers in the trace are
  replaced. Comments, docstrings and your original formatting were removed
  at build time and are not in the mapping.
- If you used string encoding, string values in your code stay encoded in
  the shipped file. Values printed in the traceback (like `'discount_rate'`
  above) are runtime values and already readable.

## Using the wrong mapping

If you pass a mapping from a different build, names it does not know are
left as they are, and names it does know may be replaced with the wrong
originals. For example, running the trace above against a mapping from an
unrelated build produced `something_else = I7 * I3[0]['discount_rate']`:
plausible-looking and wrong.

To avoid this:

1. Read the `id=` in the `# pyobfus:obfuscated` header of the shipped file
   (ask the customer for the first line of the file, or check your release
   archive) and use the mapping whose `marker_id` matches.
2. From pyobfus 0.5.31, `--unmap` also prints a warning when the
   trace contains obfuscated names that are missing from the mapping, and
   `--json` lists them in `unmatched_names`. No warning does not prove the
   mapping is right, so the id check is still the reliable one.

## With a coding assistant or editor

The same reversal is available where you already work. All of them run
locally and read the mapping file from your disk.

- **Any assistant that can run commands**: give it the `--unmap` command
  above. The `--trace-marker` header in the shipped file tells an agent that
  opens it which command to run.
- **MCP** (Claude Code, Cursor and other MCP clients): the
  [`pyobfus-mcp`](https://pypi.org/project/pyobfus-mcp/) server has an
  `unmap_stack_trace` tool that takes the trace text and a mapping path.
- **VS Code**: the [pyobfus extension](https://marketplace.visualstudio.com/items?itemName=zhurong2020.pyobfus)
  has a **pyobfus: Reverse Stack Trace** command.

Once names are restored, debugging is ordinary debugging: reproduce against
your original source, fix it there, and rebuild. Never edit the obfuscated
output.

!!! warning "Customer data in tracebacks"
    Tracebacks often contain values from the customer's run: file paths,
    user names, record contents. If you paste one into a cloud-hosted
    assistant, that text leaves your machine. Remove anything the customer
    would not want shared first. pyobfus itself does not send the trace or
    the mapping anywhere.

## FAQ

**Should the customer get the mapping file?**
No. Anyone with the mapping can read your original names everywhere in the
shipped code. Keep it with your release records.

**What can be recovered without the mapping?**
Nothing from pyobfus. A reader can still work out what the code does by
studying it; obfuscation makes that slower, it does not make it impossible.

**Does `--unmap` restore my source code?**
No. It replaces identifiers in a piece of text. Your source stays where it
was: in your repository.

**I build several versions. Which mapping do I use?**
The one from the build the customer runs. Match the `id=` in the shipped
file's header against `marker_id` in your mappings.

**Can I unmap a traceback from code compiled with Nuitka or Cython after
obfuscation?**
Yes, as long as the traceback shows the obfuscated Python names. A
Nuitka-compiled module tested this way is described in the
[compiled packaging cookbook](../COMPILED_PACKAGING_COOKBOOK.md#tracebacks-from-compiled-code).

## Related

- [Protect Python code before selling software](protect-python-before-selling.md)
- [What is tested, what is assumed](../SUPPORT_MATRIX.md): the reverse-mapping
  workflow is run on every push.
