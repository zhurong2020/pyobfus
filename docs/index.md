---
layout: default
title: pyobfus - Modern Python Code Obfuscator
---

<div style="text-align: center; margin: 2em 0;">
  <img src="assets/logo.jpeg" alt="pyobfus Logo" style="max-width: 600px; width: 100%; height: auto; border-radius: 8px;">
</div>

# pyobfus

**Modern Python Code Obfuscator**

A Python code obfuscator built with AST-based transformations for Python 3.8+. Provides reliable name mangling, string encoding, and code protection features.

## Features

### Community Edition (Free)
- **Name Obfuscation**: Rename variables, functions, and classes to I0, I1, I2...
- **Comment Removal**: Strip comments and docstrings
- **String Encoding**: Base64 encoding for string literals
- **Multi-file Support**: Obfuscate entire projects
- **YAML Configuration**: Flexible configuration system
- **Parameter Preservation**: Keep function parameter names for keyword arguments

### Professional Edition ($45 USD)
- **All Community Features** +
- **AES-256 String Encryption**: Military-grade encryption for strings
- **Anti-Debugging Checks**: Detect and prevent debugging attempts
- **Lifetime Updates**: All future Pro features included
- **Up to 3 Devices**: Use on multiple machines
- **Priority Email Support**

[**Purchase Professional Edition →**](#purchase-professional-edition)

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

## Purchase Professional Edition

**Price**: $45.00 USD (one-time payment)

### What's Included
- ✅ AES-256 String Encryption
- ✅ Anti-Debugging Checks
- ✅ Lifetime Updates
- ✅ Up to 3 Devices
- ✅ Email Support (zhurong0525@gmail.com)

### How to Purchase

**Step 1**: Email us your purchase request
- **To**: zhurong0525@gmail.com
- **Subject**: "pyobfus Professional License Request"
- **Include**: Your email address for license delivery

**Step 2**: We'll send you a secure payment link (Stripe)

**Step 3**: Complete payment and receive your license key via email within minutes

**Step 4**: Activate your license
```bash
pip install --upgrade pyobfus
pyobfus-license register PYOBFUS-XXXX-XXXX-XXXX-XXXX
```

### Activation Guide
Full activation instructions: [License Activation Guide](https://github.com/zhurong2020/pyobfus/blob/main/docs/LICENSE_ACTIVATION_GUIDE.md)

### Legal & Policies

By purchasing pyobfus Professional Edition, you agree to our:
- [Terms of Service & EULA](https://github.com/zhurong2020/pyobfus/blob/main/TERMS_OF_SERVICE.md)
- [Refund Policy](https://github.com/zhurong2020/pyobfus/blob/main/REFUND_POLICY.md) - 30-day money-back guarantee
- [Privacy Policy](https://github.com/zhurong2020/pyobfus/blob/main/PRIVACY_POLICY.md) - GDPR compliant

---

## License

Apache License 2.0 - See [LICENSE](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE)

---

**Built with Python 3.8+ • AST-based Transformations • Open Source**
