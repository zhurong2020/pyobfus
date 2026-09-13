# Other AST, loader, and online tools

Smaller or more specialised tools that come up when evaluating Python source
protection, and how each relates to pyobfus.

**CodeEnigma** compiles, compresses, encrypts, and wraps Python bytecode behind
an AES-GCM/Cython loader. It shares pyobfus's transparent-alternative
positioning, but serves a different workflow: pyobfus is AST source-to-source,
emits ordinary `.py` files, and retains a reverse mapping for production
tracebacks instead of requiring a custom encrypted loader.

**`python-obfuscator` by davidteather** is a small MIT-licensed AST tool with
independent toggles for renaming, hexadecimal strings, dead code, and an exec
wrapper. It is useful for experiments and simple scripts; pyobfus adds
scope-aware multi-file rewriting, framework presets, configuration, stable JSON
interfaces, reverse mapping, and MCP integration.

**SOURCEdefender** encrypts selected modules into `.pye` files loaded through an
import hook. It can be composed after pyobfus when encryption at rest is the
priority; it is not a source-to-source replacement for pyobfus's project-wide
mapping and debugging workflow.

**Browser-based Python obfuscators** have their own section above.

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool.
