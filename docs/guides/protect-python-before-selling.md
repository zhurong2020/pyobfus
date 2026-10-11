---
title: Protect Python code before selling software
description: Choose a delivery approach, check compatibility, obfuscate locally, test the output, and keep debugging maps private.
---

# How to protect Python code before selling software

You wrote a Python tool, possibly with an AI coding assistant, and now a
customer will run it on their machine. Python ships as readable source by
default, so the first question is not which tool to use but **what you are
delivering and what you need to keep from the customer**.

## Start with what you deliver

| You deliver | What protects the code | Where pyobfus fits |
|---|---|---|
| `.py` files or a library the customer runs with their own Python | Obfuscation makes the source hard to read; the customer still runs real Python | Good first tool to evaluate: free, local, output stays portable Python, and you can still read production tracebacks |
| A double-click app; the customer should not need Python | A packager or compiler: [PyInstaller](../PYINSTALLER_COOKBOOK.md), [Nuitka or Cython](../COMPILED_PACKAGING_COOKBOOK.md) | Optional first step: obfuscate, then package, so the packaged code carries obfuscated names |
| Logic that must never be on the customer's machine (a core algorithm, a model, a prompt) | Run it on your server and give the customer an API client | Not the answer. Anything you ship can be studied, however it is protected |
| API keys, licence signing keys, database passwords | Keep them off the client: server-side calls, per-customer credentials, asymmetric licence signatures | Not the answer. Obfuscation is not key management |

Two things hold in every row:

- **Protection on the customer's machine raises the cost of reading your
  code; it does not make reading impossible.** pyobfus output can be studied,
  and name obfuscation alone does not stop a capable reader or a language
  model from working out what code does.
- **The licence terms of every tool in your chain matter.** pyobfus
  Community is Apache-2.0 and may be used for commercial products; check the
  terms of anything else you add.

The rest of this page covers the first row, with pointers for the others.

## Step 1: check the project

```bash
pip install pyobfus
pyobfus --check src/
```

`--check` reads your code and lists patterns that obfuscation can break, such
as `getattr` with string names, `__name__` comparisons, or framework
conventions. Fix or exclude what it reports before building. It runs locally;
by default it also looks up your dependencies on PyPI, and `--offline` skips
that.

If you use a framework, see which preset fits with `pyobfus --list-presets`
(FastAPI, Django, Flask, Pydantic, Click, SQLAlchemy, ML). The
[support matrix](../SUPPORT_MATRIX.md#framework-presets) says how far each
preset is tested: presets are tested for what they exclude, not by running a
real application.

## Step 2: preview, then build

```bash
pyobfus src/ -o dist/ --dry-run --json      # what would be written, nothing written
pyobfus src/ -o dist/ --save-mapping private/build-map.json --verify-syntax
```

- `dist/` is what you ship. **`private/build-map.json` is not**: it turns
  obfuscated names back into yours. Keep it with your release records, never
  in the shipped folder, a public CI artifact, or an issue.
- `--verify-syntax` compiles the output in memory. It does not run your code,
  so it is not a test of your application.
- Your source in `src/` is not modified.

## Step 3: test the output, not just the source

Run the same checks against `dist/` that you run against `src/`. The simplest
version compares what the program prints:

```bash
(cd src  && python main.py) > expected.txt
(cd dist && python main.py) > actual.txt
diff expected.txt actual.txt && echo "same behaviour"
```

Unit tests that import your modules by name usually cannot run against
`dist/` unchanged, because those names are now obfuscated. Test through the
entry points a customer uses (command line, HTTP endpoints, the public
functions you exclude from renaming) instead.

## What you get, measured

**Since 0.6.0**, default directory builds also rename
function locals, including closure references, without changing parameters,
methods, attributes or the names of nested functions and classes (Flask app
factories and Click command groups keep working). `safe` and framework presets enable this because function
locals are implementation details; reflective functions are conservatively
skipped. Use `--no-crossfile-local-names` (YAML `crossfile_local_names: false`)
to retain the 0.5.32 naming behavior. Rerunning step 2 on the same example
with 0.6.0 (2026-10-08) gave the same program output and renamed 16 function
locals, for example `result` in `Calculator.add` became `I5`; the 0.5.30
measurements below are kept as the historical baseline.


We ran steps 1–3 on 2026-10-07 with pyobfus 0.5.30 from PyPI (Linux, Python
3.12) on [`examples/multifile/`](https://github.com/zhurong2020/pyobfus/tree/main/examples/multifile),
a three-module calculator:

- `--check` reported one low-risk finding (`__name__` use in `utils.py`).
- The build succeeded, syntax verification passed, and the obfuscated
  program printed exactly the same output as the original.
- The mapping was written to `private/` and nothing was added to `dist/`
  besides the three modules.

What the output looked like is the part to read carefully:

- **For a directory, pyobfus 0.5.30 renames module-level names** (classes,
  functions, module variables) consistently across files and rewrites the
  imports. `Calculator` became `I0` in every file that used it.
- **Method names, attributes, function-local variables and parameters kept
  their original names** in 0.5.30 directory builds (0.6.0 renames function
  locals; methods, attributes and parameters still keep their names, because
  renaming them safely across files needs type information pyobfus does not
  have). Single-file
  builds also rename method names and locals; parameters are preserved by default (not instance
  attributes), but building modules one by one breaks the imports between
  them.
- In 0.5.30, directory builds also kept function, method and class
  docstrings. 0.5.31 removes them as configured; on older versions, check your
  output for docstrings that describe your logic.
- Directory builds made with 0.5.10 to 0.5.31 could fail on import with
  `NameError` when a module used its own decorator, base class, metaclass or
  a lambda referring to a module name. 0.5.32 fixes this; if you shipped such
  a build, rebuild and rerun your tests. Step 3 above is what catches this
  kind of problem.
- String literals are kept as written unless you turn on string encoding
  (`string_encoding: true` in a config file; Pro adds AES-256 string
  encryption). Never rely on either to hide secrets.

Open a few files in `dist/` before you ship and decide whether that level of
protection is enough for what you are protecting.

## Step 4: package if needed

If the customer should not need Python, package the obfuscated `dist/`, not
`src/`:

- [PyInstaller cookbook](../PYINSTALLER_COOKBOOK.md) (advisory: not run in
  CI).
- [Nuitka / Cython cookbook](../COMPILED_PACKAGING_COOKBOOK.md): verified
  once on Linux for a single module, including what each compiler leaves in
  the binary.

Re-run your behaviour checks on the packaged result in a clean environment,
ideally the same OS as your customer.

## Step 5: plan for support

When a customer sends a traceback, it will show obfuscated names. With the
mapping from that build you can restore them:
[How to debug an obfuscated Python traceback](debug-obfuscated-python.md).

## Licensing and payment are separate decisions

pyobfus Community does not add licence checks or expiry. If you need those,
build them on asymmetric signatures (your server signs, the app only holds
the public key) or use a licensing service. pyobfus Pro adds build-time
options such as hard expiry and device binding; see the
[Community / Pro boundary](../EDITION_BOUNDARY_POLICY.md) for what each edition
covers.

## FAQ

**Can I use the free Community Edition for a commercial product?**
Yes. Community is Apache-2.0, with no file or line limit and no trial clock.

**Does obfuscation protect my API keys?**
No. A key in a client program can be extracted, obfuscated or not. Keep
high-privilege keys on a server. `pyobfus --check` flags common hardcoded-key
shapes without showing values; see [screening limits and remediation](../SARIF_CODE_SCANNING.md#hardcoded-secret-screening-community).

**Does my customer need to install Python?**
For obfuscated `.py` output, yes. If they should not, add PyInstaller or
Nuitka (step 4).

**My project was written by an AI assistant. Anything different?**
Test the obfuscated output as carefully as the original; generated code often
uses dynamic patterns (`getattr`, string-based dispatch) that `--check`
flags. pyobfus also has an [MCP server](https://pypi.org/project/pyobfus-mcp/)
so an assistant can run the check, build and verification steps for you.
It runs locally; nothing is uploaded by pyobfus.

**Is my source uploaded anywhere?**
No. pyobfus runs on your machine and has no telemetry. `--check` looks up
dependency names on PyPI unless you pass `--offline`. See
[network behavior](../NETWORK_BEHAVIOR.md) for the complete list.
