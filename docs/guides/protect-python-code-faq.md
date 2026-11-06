---
title: Can you protect Python code from being read? FAQ
description: What .pyc files, PyInstaller, Cython, Nuitka, obfuscation and bytecode encryption leave recoverable, why local licence checks can be removed, and what to keep on a server.
---

# Can you protect Python code from being read? FAQ

Short answers to the questions people ask before shipping Python to a
customer. For the step-by-step workflow, see
[How to protect Python code before selling software](protect-python-before-selling.md).

> **Scope.** Statements about other tools are dated and limited to the
> sources linked next to them; versions, modes and prices change. See the
> [comparison scope note](../COMPARISON.md). pyobfus is maintained by the
> authors of this page.

## Can any tool make Python code impossible to read?

No. Anything that runs on the customer's machine can be studied by someone
with enough time, including native code. The tools below differ in how much
effort they add and what they leave behind. If a piece of logic must never be
seen, keep it on a server you control and ship a client that calls it.

## Can I enforce a time-limited licence in the code I ship?

Not robustly. These are two separate problems: making code harder to read,
and making a licence check impossible to remove. Compiling or obfuscating
helps with the first, not the second.

- **A check that runs locally can be bypassed.** Someone can patch it out,
  roll the system clock back, or copy a valid licence to another machine.
  Obfuscation or compilation makes the check harder to find; it does not make
  it binding.
- **Signing the licence protects its fields, not its enforcement.** Sign the
  expiry date and entitlements with a private key that never ships, and
  verify with the public key in the client. An unmodified client then detects
  edited fields. It does not stop clock rollback, copying, or a modified
  client that skips verification.
- **Enforcement that holds needs a server.** The expiry must be checked where
  you control the clock, and the product must keep depending on that server
  (for example, for a computation or data it needs on each use). A one-time
  download that keeps working offline is not enforcement after expiry.

pyobfus Community adds no licence checks. Pro offers build-time expiry and
binding options. Offline expiry trusts the machine's clock, renewing a fixed
expiry needs a new build, and these checks can still be bypassed; see
[Ship Python offline](ship-python-offline.md#5-expiry-renewal-and-revocation-offline).

## What does each option leave recoverable?

| Approach | What a customer can still recover |
|---|---|
| Shipping `.pyc` files | Bytecode keeps identifier names and can be disassembled; a decompiler that supports that Python version can reconstruct source-like Python. Comments and formatting are lost. |
| PyInstaller | It bundles an interpreter and your bytecode; it is not a protection layer. Tools such as `pyinstxtractor` extract the bytecode. PyInstaller 6.0 removed the old `--key` option. [Details](../PYINSTALLER_COOKBOOK.md#does-pyinstaller-protect-your-source-code). |
| Cython or Nuitka | Compiled modules contain native code instead of ordinary Python bytecode. Names that Python needs at runtime can remain in the binary, and constants may be recoverable. [Measurement](../COMPILED_PACKAGING_COOKBOOK.md#should-i-obfuscate-before-compiling-with-nuitka). |
| Renaming identifiers (pyobfus) | Output is still Python, so structure stays readable. Renamed names reveal less intent; public APIs, reflection-sensitive names and anything you exclude keep their names. No extra runtime. |
| Bytecode protection with a native runtime (for example PyArmor) | Stronger than plain renaming against casual inspection, at the cost of a per-platform runtime. Our 2026-10-02 review cites public research tooling that targets standard encrypted bytecode in PyArmor 8.0–9.2.x; its reconstructed source may be incomplete, and coverage of the VMC/ECC modes documented for 9.2.7 was not verified. [Dated review](../compare/pyarmor.md#bytecode-protection-is-not-magic). |

## Does compiling with Cython or Nuitka remove my function names?

Not in the builds we tested. On 2026-10-07 (Linux x86_64, CPython 3.12.3,
Cython 3.3.0, Nuitka 4.2.2 `--module`, pyobfus 0.5.30) we counted lines of
`strings` output matching two identifiers in a small module:

| Identifier | Cython | Cython after `strip` | Nuitka | Either compiler, renamed first |
|---|---:|---:|---:|---:|
| function `proprietary_transform` | 7 | 2 | 2 | 0 |
| class `ConfidentialEngine` | 7 | 2 | 3 | 0 |
| string literal `"super-secret-value"` | 1 | 1 | 1 | 1 |

After renaming and then compiling, `strings` found no matches for the two
tested identifiers; that does not prove the original names cannot be
recovered. The string literal was found in every build. This is one module, one platform and one
mode; it shows which names were present, not how resistant the result is to
reverse engineering. Full method in the
[compiled packaging cookbook](../COMPILED_PACKAGING_COOKBOOK.md#should-i-obfuscate-before-compiling-with-nuitka).

## Does obfuscation or compilation protect an API key in my code?

No. String literals stayed readable in every build above, and a running
program has to hold the key in memory to use it. Keep high-privilege keys on
a server and give clients per-customer, limited credentials.

## Should I rename before packaging or compiling?

Yes, if you want the shipped artifact to contain renamed identifiers: rename
first, then package with PyInstaller or compile with Nuitka or Cython, and
keep secrets and licence decisions on a server. The
[delivery workflow](protect-python-before-selling.md) covers the steps.

## How do I debug a customer's traceback after obfuscation?

Keep a private identifier map for every build you ship, and never put it in
the shipped artifact. With pyobfus, `--save-mapping` writes the map at build
time and `--unmap` restores original names in a traceback; see
[How to debug an obfuscated Python traceback](debug-obfuscated-python.md).

## Is pyobfus free for commercial use?

The Community/Core edition is Apache-2.0 and can be used in commercial
products. Pro features are separately licensed; see the
[Community / Pro boundary](../EDITION_BOUNDARY_POLICY.md).
