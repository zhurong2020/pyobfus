# pyobfus

**Modern Python Code Obfuscator - Enterprise-Grade Protection at 50% Lower Cost**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Born from medical AI research, **pyobfus** provides robust, transparent, and community-driven code obfuscation for Python 3.8+. Protect your intellectual property without breaking the bank.

## Why pyobfus?

- **Transparent**: Open-core model with clear Community Edition limits (no vague "big script" errors)
- **Affordable**: $49-149 vs PyArmor $99-199+ (50% cost savings)
- **Reliable**: Predictable behavior, comprehensive error messages
- **Modern**: Built for Python 3.8+, leveraging AST-based transformation
- **AI/ML Optimized**: Works reliably with PyTorch, TensorFlow, and medical imaging code

### Real-World Problem We Solve

PyArmor trial version fails unpredictably on AI/ML code (tested with cardiac imaging projects). pyobfus Community Edition has clear, documented limits - and actually works within those limits.

## Features

### Community Edition (Free)

- **Name Mangling**: Variable/function/class names → `I0`, `I1`, `I2`, ...
- **Comment Removal**: Strip all comments and docstrings
- **Simple String Encoding**: Basic obfuscation for string literals
- **Multi-file Support**: Obfuscate entire projects (up to 5 files or 1000 LOC)
- **File Filtering**: Exclude files using glob patterns (test files, config, etc.)
- **Configuration Files**: YAML-based configuration for repeatable builds
- **Selective Obfuscation**: Preserve specific names (logger, config, main)

### Pro Edition ($49-149)

- **Unlimited Files/LOC**: No restrictions on project size
- **AES-256 String Encryption**: Military-grade string protection
- **Control Flow Flattening**: Advanced logic obfuscation
- **Anti-Debugging**: Detect and prevent debugger attachment
- **Priority Support**: Direct assistance for integration issues

## Quick Start

### Installation

```bash
pip install pyobfus
```

### Basic Usage

```bash
# Obfuscate a single file
pyobfus examples/simple.py -o examples/simple_obf.py

# Obfuscate a directory
pyobfus src/ -o dist/

# With configuration file
pyobfus src/ -o dist/ --config pyobfus.yaml
```

### Example

**Before obfuscation** (`examples/simple.py`):

```python
def calculate_risk(age, calcium_score):
    """Calculate cardiovascular risk."""
    risk_factor = 0.1
    if calcium_score > 100:
        risk_factor = 0.5
    return age * risk_factor

patient_age = 55
patient_calcium = 150
risk = calculate_risk(patient_age, patient_calcium)
print(f"Risk score: {risk}")
```

**After obfuscation** (Community Edition):

```python
def I0(I1, I2):
    I3 = 0.1
    if I2 > 100:
        I3 = 0.5
    return I1 * I3
I4 = 55
I5 = 150
I6 = I0(I4, I5)
print(f'Risk score: {I6}')
```

## Configuration

Create `pyobfus.yaml`:

```yaml
obfuscation:
  level: community  # or 'pro'
  exclude_patterns:
    - "test_*.py"
    - "**/tests/**"
    - "__init__.py"
  exclude_names:
    - "logger"
    - "config"
    - "main"
  remove_docstrings: true
  remove_comments: true
  string_encoding: false  # Pro feature
```

### File Filtering Examples

Exclude patterns support glob syntax:

- `test_*.py` - Exclude files starting with "test_"
- `**/tests/**` - Exclude all files in "tests" directories
- `**/__init__.py` - Exclude all `__init__.py` files
- `setup.py` - Exclude specific files

See [`pyobfus.yaml.example`](pyobfus.yaml.example) for more configuration examples.

## Community Edition Limits

To maintain a sustainable open-core model:

- **Max 5 files** OR **Max 1000 total lines of code**
- Clear error messages when limits exceeded
- Upgrade path to Pro Edition

Unlike PyArmor trial's vague "Can't obfuscate big script" errors, pyobfus tells you exactly what the limit is:

```
Community Edition limit exceeded: file_count
  Current: 8
  Limit: 5

Upgrade to pyobfus Pro for unlimited files:
  https://github.com/zhurong2020/pyobfus#pricing
```

## Pricing

| Edition | Price | Use Case | Limits |
|---------|-------|----------|--------|
| **Community** | **Free** | Students, hobbyists, open-source | 5 files OR 1000 LOC |
| **Starter** | **$49/product** | Indie developers | Unlimited |
| **Professional** | **$149/product** | Small teams | + Pro features |
| **Enterprise** | **$399/product** | Corporations | + Priority support |

**Fair Use Policy**: If your product generates revenue < 100x the license fee, the Pro license is free. Example: $149 license → Free if revenue < $14,900.

## Comparison

| Feature | pyobfus | PyArmor | Nuitka | Opy |
|---------|---------|---------|--------|-----|
| **Open Source** | ✅ Core | ❌ | ✅ | ✅ |
| **Active Development** | ✅ | ✅ | ✅ | ❌ 2017 |
| **AI/ML Compatible** | ✅ | ⚠️ Hit-or-miss | ✅ | ❌ |
| **Predictable Free Tier** | ✅ | ❌ | N/A | ✅ |
| **Price** | $49-149 | $99-199 | €250/year | Free |
| **Python 3.12+** | ✅ | ✅ | ✅ | ❌ 3.5 |

## Development

### Setup

```bash
git clone https://github.com/zhurong2020/pyobfus.git
cd pyobfus
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

### Testing

```bash
pytest tests/ -v --cov=pyobfus
```

### Code Quality

```bash
black pyobfus/
mypy pyobfus/
ruff check pyobfus/
```

## Use Cases

### Medical AI Protection

pyobfus was born from [cardiac-ml-research](https://github.com/zhurong2020/cardiac-ml-research), a medical imaging AI project requiring code protection for commercial distribution.

```bash
# Obfuscate medical AI modules
pyobfus applications/periaortic_adipose/ \
    --output dist/applications/periaortic_adipose/ \
    --config cardiac_obfus.yaml
```

### SaaS Distribution

Protect proprietary algorithms before distributing Python apps to clients.

### Educational Institutions

Use Community Edition for teaching code protection concepts.

## Roadmap

- [x] **Phase 1** (Week 1-6): MVP with name mangling
- [ ] **Phase 2** (Week 7-12): Pro features (AES encryption, control flow)
- [ ] **Phase 3** (Week 13-24): VSCode extension, CI/CD plugins

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Contributors

- Rong Zhu ([@zhurong2020](https://github.com/zhurong2020)) - Creator & Maintainer

## License

- **Community Edition**: Apache License 2.0 (see [LICENSE](LICENSE))
- **Pro Edition**: Proprietary license (contact for details)

## Support

- **Documentation**: [GitHub Wiki](https://github.com/zhurong2020/pyobfus/wiki)
- **Issues**: [GitHub Issues](https://github.com/zhurong2020/pyobfus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/zhurong2020/pyobfus/discussions)

## Acknowledgments

- Inspired by [Opy](https://github.com/QQuick/Opy) (ideas only, clean room implementation)
- Market research validated by PyArmor trial limitations
- Born from real-world needs in medical AI research
