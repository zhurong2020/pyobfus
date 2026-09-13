# pyobfus vs Cython

Cython compiles Python to C. Obfuscation is a side effect of that, not its
purpose, which shapes every trade-off below.

Cython compiles Python to C code, providing both performance benefits and obfuscation.

| Feature | pyobfus | Cython |
|---------|---------|--------|
| **Approach** | AST transformation | Compile to C |
| **Output** | `.py` files | `.so`/`.pyd` (platform-specific) |
| **Cross-platform** | Yes (single output) | No (compile per platform) |
| **Build complexity** | None | Requires C compiler |
| **Development workflow** | Unchanged | Compilation step required |
| **Performance** | Python speed | Near-C speed |
| **Reversibility** | Names irreversible | Binary harder to reverse |

## When to Choose pyobfus

- You need **cross-platform** distribution
- You want to **avoid compilation** complexity
- You need **fast iteration** during development
- Your users don't have C compilers

## When to Choose Cython

- **Performance** is critical (CPU-bound code)
- You can handle **per-platform builds**
- You want **binary-level** protection

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool.
