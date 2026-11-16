# Other AST, loader, and online tools

Smaller or more specialised tools that come up when evaluating Python source
protection, and how each relates to pyobfus.

> **Partial refresh — checked 2026-11-15.** Only SOURCEdefender’s
> encryption approach, pricing and licence scope below were rechecked, using
> its official site as recorded in the
> [2026-11-15 research](../COMPETITIVE_ROADMAP_RESEARCH_2026-11-15.md).
> Other claims retain the **2026-10-02** comparison baseline unless a linked
> test gives a separate date; no new hands-on tests were run.

**CodeEnigma** compiles, compresses, encrypts, and wraps Python bytecode behind
an AES-GCM/Cython loader. It shares pyobfus's transparent-alternative
positioning, but serves a different workflow: pyobfus is AST source-to-source,
emits ordinary `.py` files, and retains a reverse mapping for production
tracebacks instead of requiring a custom encrypted loader.

**`python-obfuscator` by davidteather** is a small MIT-licensed AST tool with
independent toggles for renaming, hexadecimal strings, dead code, and an exec
wrapper. It is useful for experiments and simple scripts (see the
[multi-module test](open-source-obfuscators.md)); pyobfus adds
scope-aware multi-file rewriting, framework presets, configuration, stable JSON
interfaces, reverse mapping, and MCP integration.

**SOURCEdefender** encrypts selected modules into `.pye` files loaded through an
import hook. It can be composed after pyobfus when encryption at rest is the
priority; it is not a source-to-source replacement for pyobfus's project-wide
mapping and debugging workflow. This integration suggestion retains the
2026-10-02 baseline and was not tested in this refresh.

**SOURCEdefender facts — checked 2026-11-15.** The
[official site](https://www.sourcedefender.co.uk/) describes **AES-256**
encryption and a dedicated import path. Public pricing is **GBP 15/month or
GBP 150/year per developer system**, or **Enterprise GBP 1500/year**.
Development systems and CI encryption nodes need a licence; end users need
no licence to run the encrypted code. This is a focused option for encrypting
selected modules.

**Browser-based Python obfuscators** have their own section above.

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool. Its dated scope and disclaimer apply here as well.
