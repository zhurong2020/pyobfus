# pyobfus vs Nuitka

Nuitka compiles Python into a native binary. Like Cython it protects source by
leaving ordinary source behind. The trade-off is a compiled, platform-specific
distribution workflow rather than source-to-source transformation.

| Feature | pyobfus | Nuitka |
|---------|---------|--------|
| **Output** | `.py` files | Native code: a standalone executable or an extension module (`--module`) |
| **Distribution** | Requires Python installed | Standalone mode is self-contained; `--module` output still needs a matching Python |
| **Build time** | No native compilation | Native compilation; measure on your project |
| **File size** | Transformed source | Standalone distributions include runtime dependencies |
| **Commercial offering** | $45 one-time Pro | Separate vendor offering; check current quote and terms |
| **Traceback protection** | RSA-2048-OAEP + AES-256-GCM hybrid, reversible via `pyobfus-unscrub` | Vendor-documented traceback encryption; verify the current edition and key-management design |

## Traceback protection: different key management

Both tools ship a feature for the same real problem — a production traceback
can leak internal file/function/variable names to whoever sees it. Nuitka
Commercial's "Traceback Encryption" encrypts traceback information. In the
[vendor documentation](https://nuitka.net/doc/commercial/traceback-encryption.html)
reviewed in 2026-08, the documented design used symmetric encryption and said
asymmetric support was planned; verify the current design before relying on
that snapshot. pyobfus's `--scrub-traceback` (Pro)
uses a hybrid RSA-2048-OAEP + AES-256-GCM scheme — the production side never
holds a key capable of decrypting what it just encrypted, only the
private-key holder can, via the separate `pyobfus-unscrub` CLI. Symmetric
encryption is not insecure by itself, but it does mean whichever process
performs the encryption necessarily holds a key capable of reversing it too
— a meaningfully different key-management story than asymmetric encryption's
one-way trapdoor.

## When to Choose pyobfus

- You're distributing **Python libraries** (not executables)
- You prefer pyobfus's published one-time price to Nuitka's commercial terms
- You need **fast builds** (no compilation)
- **File size** matters

## When to Choose Nuitka

- You need **standalone executables**
- Users shouldn't need Python installed
- You specifically want a native compiled distribution

## Using both

Nuitka keeps Python-visible names (functions, classes, attributes) in the
compiled output because the program needs them at runtime. Obfuscating with
pyobfus first means those are the obfuscated names. A measured run, the
`.pyi` stub Nuitka writes by default, and the limits are in the
[compiled packaging cookbook](../COMPILED_PACKAGING_COOKBOOK.md).

> **Want a standalone executable without using Nuitka?**
> pyobfus pairs with the free, MIT-licensed [PyInstaller](https://pyinstaller.org/)
> to ship a single-file binary with mangled identifiers — obfuscate first,
> then bundle. See the [PyInstaller Cookbook](../PYINSTALLER_COOKBOOK.md) for a
> full worked example and a check of the bundle for the original names.
> That combination is advisory-only in the [support matrix](../SUPPORT_MATRIX.md).

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool. Its dated scope and disclaimer apply here as well.
