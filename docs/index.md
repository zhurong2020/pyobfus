---
layout: default
title: pyobfus - Modern Python Code Obfuscator
---

# pyobfus

**Modern Python Code Obfuscator**

A Python code obfuscator built with AST-based transformations for Python 3.8+. Provides reliable name mangling, string encoding, and code protection features.

## Features

- **Name Obfuscation**: Rename variables, functions, and classes
- **Comment Removal**: Strip comments and docstrings
- **String Encoding**: Protect string literals with encoding
- **Multi-file Support**: Obfuscate entire projects
- **YAML Configuration**: Flexible configuration system

## Quick Start

Install via pip:

```bash
pip install pyobfus
```

Obfuscate a single file:

```bash
pyobfus input.py -o output.py
```

Obfuscate a directory:

```bash
pyobfus src/ -o obfuscated/
```

## Documentation

- [README](https://github.com/zhurong2020/pyobfus#readme)
- [Project Structure](./PROJECT_STRUCTURE.md)
- [Roadmap](../ROADMAP.md)
- [Security Policy](../SECURITY.md)

## Installation

### From PyPI (Recommended)

```bash
pip install pyobfus
```

### From Source

```bash
git clone https://github.com/zhurong2020/pyobfus.git
cd pyobfus
pip install -e .
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

## License

Apache License 2.0 - See [LICENSE](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE)

## Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/zhurong2020/pyobfus/issues)
- **GitHub Discussions**: [Ask questions or share ideas](https://github.com/zhurong2020/pyobfus/discussions)

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](https://github.com/zhurong2020/pyobfus/blob/main/CONTRIBUTING.md).

---

**Built with Python 3.8+ • AST-based Transformations • Open Source**
