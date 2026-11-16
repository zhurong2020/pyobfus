# pyobfus vs Nuitka

Nuitka compiles Python into a native binary. Like Cython it protects source by
leaving ordinary source behind. The trade-off is a compiled, platform-specific
distribution workflow rather than source-to-source transformation.

> **Partial refresh — checked 2026-11-15.** Version and Commercial feature/
> price facts use official documentation in the
> [2026-11-15 research record](../COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md).
> No new hands-on compilation, performance or protection tests were run.
> Other comparison claims retain the **2026-10-02** baseline; the
> traceback key-management discussion retains its **2026-08** review date.

The [official download page](https://nuitka.net/doc/download.html) lists
**4.3.5** as the stable version (**checked 2026-11-15**). The
[4.3 release notes](https://nuitka.net/posts/nuitka-release-43.html) describe
continued **experimental Python 3.15 support**; that does not imply full
compatibility testing here.

| Feature | pyobfus | Nuitka |
|---------|---------|--------|
| **Output** | `.py` files | Native code: a standalone executable or an extension module (`--module`) |
| **Distribution** | Requires Python installed | Standalone mode is self-contained; `--module` output still needs a matching Python |
| **Build time** | No native compilation | Native compilation; measure on your project |
| **File size** | Transformed source | Standalone distributions include runtime dependencies |
| **Commercial offering** | $45 one-time Pro | From **EUR 250/year**; code/constant protection, data-file embedding and traceback encryption ([official download page](https://nuitka.net/doc/download.html), checked 2026-11-15) |
| **Traceback protection** | RSA-2048-OAEP + AES-256-GCM hybrid, reversible via `pyobfus-unscrub` | Commercial [traceback encryption](https://nuitka.net/doc/commercial/traceback-encryption.html) (availability checked 2026-11-15; key-management details below retain the 2026-08 date) |

**Commercial resource protection — checked 2026-11-15.** The official
[data-file protection documentation](https://nuitka.net/doc/commercial/protect-data-files.html)
describes embedding with both standard file access and `importlib.resources`.
It distinguishes ordinary onefile temporary extraction from Commercial
embedded protection. Together with code/constant protection and traceback
encryption, this gives Commercial explicit protection capabilities beyond
compilation alone.

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

The 2026-11-15 assessment treats the tools as complementary: pyobfus provides
project-level name protection, checks, private mapping and verifiable build
evidence; Nuitka provides final native-binary delivery
([research record](../COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md)). This is a
workflow choice, not new validation of a packaging combination.

The retained compilation observation (2026-10-02) is that Nuitka keeps
Python-visible names (functions, classes, attributes) in the
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
