# pyobfus vs Nuitka

Nuitka compiles Python into a native binary. Like Cython it protects source by
leaving the source behind entirely, and like Cython that costs you portability
and readable tracebacks.

| Feature | pyobfus | Nuitka |
|---------|---------|--------|
| **Output** | `.py` files | Standalone binary |
| **Distribution** | Requires Python installed | Self-contained |
| **Build time** | Instant | Minutes to hours |
| **File size** | Original size | Large (includes Python) |
| **Commercial price** | $45 | ~$270/year |
| **License model** | One-time | Annual subscription |
| **Traceback protection** | RSA-2048-OAEP + AES-256-GCM hybrid, reversible via `pyobfus-unscrub` | Symmetric encryption only ([per Nuitka's own docs](https://nuitka.net/doc/commercial/traceback-encryption.html), asymmetric "planned" as of 2026-08) |

## Traceback Protection: Hybrid vs Symmetric-Only

Both tools ship a feature for the same real problem — a production traceback
can leak internal file/function/variable names to whoever sees it. Nuitka
Commercial's "Traceback Encryption" (part of its ~$270/year tier) encrypts
tracebacks so only the vendor can decode them, but as of this writing its own
documentation states the encryption is symmetric only, with asymmetric
support still on the roadmap. pyobfus's `--scrub-traceback` (Pro) already
uses a hybrid RSA-2048-OAEP + AES-256-GCM scheme — the production side never
holds a key capable of decrypting what it just encrypted, only the
private-key holder can, via the separate `pyobfus-unscrub` CLI. Symmetric
encryption is not insecure by itself, but it does mean whichever process
performs the encryption necessarily holds a key capable of reversing it too
— a meaningfully different key-management story than asymmetric encryption's
one-way trapdoor.

## When to Choose pyobfus

- You're distributing **Python libraries** (not executables)
- You want **one-time payment** vs subscription
- You need **fast builds** (no compilation)
- **File size** matters

## When to Choose Nuitka

- You need **standalone executables**
- Users shouldn't need Python installed
- You want **maximum binary protection**

> **Want a standalone executable without Nuitka's price or compile times?**
> pyobfus pairs with the free, MIT-licensed [PyInstaller](https://pyinstaller.org/)
> to ship a single-file binary with mangled identifiers — obfuscate first,
> then bundle. See the [PyInstaller Cookbook](../PYINSTALLER_COOKBOOK.md) for a
> full worked example, including verification that the original names never
> reach the compiled binary.

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool.
