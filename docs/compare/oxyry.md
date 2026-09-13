# pyobfus vs Oxyry

Oxyry is a browser-hosted name mangler, which makes it the fastest way to
obfuscate a single file and the wrong tool for a codebase you ship repeatedly.

Oxyry is an online Python obfuscation service.

| Feature | pyobfus | Oxyry |
|---------|---------|-------|
| **Deployment** | CLI tool (local) | Web service only |
| **Privacy** | Code never leaves your machine | Code uploaded to server |
| **Python versions** | 3.9 - 3.14 | 3.3 - 3.7 (outdated) |
| **Multi-file support** | Yes (cross-file) | Limited |
| **Configuration** | YAML files | Web interface |
| **CI/CD integration** | Yes | No |
| **Offline usage** | Yes | No |

## When to Choose pyobfus

- You need **modern Python** (3.9+) support
- You want code to **stay local** (privacy/compliance)
- You need **CI/CD integration**
- You're obfuscating **multi-file projects**

## When to Choose Oxyry

- Quick, one-off obfuscation of small scripts
- You're comfortable with Python 3.7 or older

## Migrating from Oxyry

1. **Install locally**:
   ```bash
   pip install pyobfus
   ```

2. **Run from command line**:
   ```bash
   pyobfus your_script.py -o obfuscated.py
   ```

3. **Benefits**:
   - Code stays on your machine
   - Modern Python 3.9-3.14 support
   - Batch processing for directories

---

Part of the [pyobfus tool comparison](../COMPARISON.md), which also carries
the feature matrix, pricing, and the reasoning behind layering more than one
tool.
