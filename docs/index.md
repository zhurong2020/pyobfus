---
layout: default
title: pyobfus - Modern Python Code Obfuscator
---

# pyobfus

**Modern Python Code Obfuscator**

A Python code obfuscator built with AST-based transformations for Python 3.8+. Provides reliable name mangling, string encoding, and code protection features.

## Features

- **Name Obfuscation**: Rename variables, functions, and classes to I0, I1, I2...
- **Comment Removal**: Strip comments and docstrings
- **String Encoding**: Protect string literals with encoding
- **Multi-file Support**: Obfuscate entire projects
- **YAML Configuration**: Flexible configuration system

## Installation

**From PyPI** (recommended):

```bash
pip install pyobfus
```

**From source** (for development):

```bash
git clone https://github.com/zhurong2020/pyobfus.git
cd pyobfus
pip install -e .
```

## Quick Start

Obfuscate a single file:

```bash
pyobfus input.py -o output.py
```

Obfuscate a directory:

```bash
pyobfus src/ -o obfuscated/
```

With configuration:

```bash
pyobfus src/ -o obfuscated/ --config pyobfus.yaml
```

## Example

**Before obfuscation:**

```python
def calculate_total(price, quantity):
    """Calculate total price."""
    tax_rate = 0.1
    subtotal = price * quantity
    tax = subtotal * tax_rate
    return subtotal + tax
```

**After obfuscation:**

```python
def I0(I1, I2):
    I3 = 0.1
    I4 = I1 * I2
    I5 = I4 * I3
    return I4 + I5
```

*Note: Variable names may vary slightly, but functionality is preserved.*

## Documentation

- [README](https://github.com/zhurong2020/pyobfus#readme) - Full documentation
- [Roadmap](https://github.com/zhurong2020/pyobfus/blob/main/ROADMAP.md) - Future features
- [Changelog](https://github.com/zhurong2020/pyobfus/blob/main/CHANGELOG.md) - Version history
- [Security Policy](https://github.com/zhurong2020/pyobfus/blob/main/SECURITY.md) - Report vulnerabilities

## Community & Support

- [GitHub Issues](https://github.com/zhurong2020/pyobfus/issues) - Bug reports and feature requests
- [GitHub Discussions](https://github.com/zhurong2020/pyobfus/discussions) - Questions and ideas
- [Contributing](https://github.com/zhurong2020/pyobfus/blob/main/CONTRIBUTING.md) - How to contribute

## License

Apache License 2.0 - See [LICENSE](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE)

---

**Built with Python 3.8+ • AST-based Transformations • Open Source**
