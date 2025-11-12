# pyobfus

**Modern Python Code Obfuscator**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python code obfuscator built with AST-based transformations for Python 3.8+. Provides reliable name mangling, string encoding, and code protection features.

## Features

### ✅ Free Edition (Current Version)

The following features are **fully implemented and available** in the current version:

- **Name Mangling**: Rename variables, functions, classes, and class attributes to obfuscated names (I0, I1, I2...)
- **Comment Removal**: Strip comments and docstrings
- **String Encoding**: Base64 encoding for string literals with automatic decoder injection
- **Parameter Preservation**: Preserve function parameter names for keyword argument compatibility (`--preserve-param-names`)
- **Multi-file Support**: Obfuscate entire projects with preserved import relationships
- **File Filtering**: Exclude files using glob patterns (test files, config files, etc.)
- **Configuration Files**: YAML-based configuration for repeatable builds
- **Selective Obfuscation**: Preserve specific names (builtins, magic methods, custom exclusions)

### 🔒 Pro Edition (Planned for v0.1.6+)

The following advanced features are **planned but not yet implemented**:

- **String Encryption** (Coming in v0.1.6)
  - AES-256 encryption for strings
  - Runtime decryption
  - Custom encryption schemes

- **Control Flow Obfuscation** (Coming in v0.3.0)
  - If-to-while conversion
  - Loop unrolling
  - Jump tables
  - False branch injection

- **Dead Code Injection** (Coming in v0.3.0)
  - Insertion of unreachable code paths
  - Complexity increase

- **Opaque Predicates** (Coming in v0.3.0)
  - Always-true/false conditions that are hard to detect
  - Control flow obscuring

**Note**: Configuration options for Pro features (e.g., `string_encryption: true`, `anti_debug: true`) are accepted for future compatibility but currently have **no effect**. They will be enabled in future releases. See [ROADMAP.md](ROADMAP.md#v020---core-functionality--initial-pro-features-6-8-weeks) for detailed implementation timeline.

## Quick Start

### Installation

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

### Basic Usage

```bash
# Obfuscate a single file
pyobfus input.py -o output.py

# Obfuscate a directory
pyobfus src/ -o dist/

# With configuration file
pyobfus src/ -o dist/ --config pyobfus.yaml

# Preserve parameter names for keyword arguments (v0.1.6+)
pyobfus src/ -o dist/ --preserve-param-names
```

### Example

**Before obfuscation**:

```python
def calculate_risk(age, score):
    """Calculate risk factor."""
    risk_factor = 0.1
    if score > 100:
        risk_factor = 0.5
    return age * risk_factor

patient_age = 55
patient_score = 150
risk = calculate_risk(patient_age, patient_score)
print(f"Risk score: {risk}")
```

**After obfuscation**:

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

*Note: Variable names (I0, I1, etc.) may vary slightly depending on code structure, but functionality is preserved.*

## Configuration

Create `pyobfus.yaml`:

```yaml
obfuscation:
  level: community
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
```

### File Filtering

Exclude patterns support glob syntax:

- `test_*.py` - Exclude files starting with "test_"
- `**/tests/**` - Exclude all files in "tests" directories
- `**/__init__.py` - Exclude all `__init__.py` files
- `setup.py` - Exclude specific files

See `pyobfus.yaml.example` for more configuration examples.

## Architecture

pyobfus uses Python's `ast` module for syntax-aware transformations:

1. **Parser**: Parse Python source to AST
2. **Analyzer**: Build symbol table with scope analysis
3. **Transformers**: Apply obfuscation techniques (name mangling, string encoding, etc.)
4. **Generator**: Generate obfuscated Python code

This approach ensures:
- Syntactically correct output
- Proper handling of Python scoping rules
- Support for modern Python features (f-strings, walrus operator, etc.)

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
# Run unit tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=pyobfus --cov-report=html

# Run integration tests (requires external project)
python scripts/test_ml_research.py --all --max-files 10
pytest integration_tests/ -v
```

**Integration Testing Framework** (v0.1.6+): Test pyobfus on real-world code without uploading to PyPI. See [`INTEGRATION_TESTING.md`](INTEGRATION_TESTING.md) for details.

### Code Quality

```bash
# Format code
black pyobfus/

# Type checking
mypy pyobfus/

# Linting
ruff check pyobfus/
```

## Use Cases

### Protecting Proprietary Algorithms

Obfuscate sensitive business logic before distributing Python applications.

### Educational Purposes

Demonstrate code protection concepts and obfuscation techniques.

### Intellectual Property Protection

Add an additional layer of protection for commercial Python software.

## Limitations

### Current Limitations

- **Keyword Arguments** (✅ Resolved in v0.1.6): By default, parameter names are obfuscated, which breaks keyword arguments. **Solution**: Use the `--preserve-param-names` flag to preserve parameter names while still obfuscating function bodies.

  Example:
  ```python
  # Before obfuscation
  def process(data_path, output_dir):
      temp_file = data_path + ".tmp"
      return temp_file

  result = process(data_path='./data', output_dir='./output')  # ✅ Works

  # After obfuscation (default behavior)
  def I0(I1, I2):
      I3 = I1 + ".tmp"
      return I3

  result = process(data_path='./data', output_dir='./output')  # ❌ TypeError!

  # After obfuscation (with --preserve-param-names)
  def I0(data_path, output_dir):
      I3 = data_path + ".tmp"
      return I3

  result = I0(data_path='./data', output_dir='./output')  # ✅ Works!
  ```

  **When to use `--preserve-param-names`**:
  - Public API functions/libraries where keyword arguments are used by clients
  - Functions with many parameters where keyword arguments improve readability
  - Code that relies heavily on keyword-only arguments (`def func(*, kwonly)`)

  **Trade-off**: Parameter names reveal some information about the function's interface, but function bodies and local variables are still fully obfuscated.

- **Cross-file imports**: Name mapping across files is basic (improvements planned)
- **Dynamic code**: `eval()`, `exec()` with obfuscated code may require adjustments
- **Debugging**: Obfuscated code is harder to debug (by design)
- **Performance**: Some obfuscation techniques may impact runtime performance

### Recommendations

- **Test obfuscated code thoroughly** before deployment
- Keep original source in version control
- Use configuration files for reproducible builds
- For public APIs, use `--preserve-param-names` to maintain keyword argument compatibility
- Consider combining with other protection methods (compilation, etc.)

## Technical Details

- **Python Support**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Naming Scheme**: Index-based (I0, I1, I2...) - simple and effective
- **Architecture**: Modular transformer pipeline
- **Testing**: 57 tests, 54% coverage, multi-OS CI/CD

## Documentation

### For Users
- **[Installation & Quick Start](#installation)** - Get started in minutes
- **[Configuration Guide](#configuration)** - YAML configuration and file filtering
- **[Examples](https://github.com/zhurong2020/pyobfus/tree/main/examples)** - Working code examples demonstrating features
- **[Use Cases](#use-cases)** - Real-world application scenarios

### For Developers
- **[Project Structure](https://github.com/zhurong2020/pyobfus/blob/main/docs/PROJECT_STRUCTURE.md)** - Codebase architecture and development workflow
- **[Contributing Guide](https://github.com/zhurong2020/pyobfus/blob/main/CONTRIBUTING.md)** - How to contribute code and documentation
- **[Development Roadmap](https://github.com/zhurong2020/pyobfus/blob/main/ROADMAP.md)** - Planned features and timeline
- **[Changelog](https://github.com/zhurong2020/pyobfus/blob/main/CHANGELOG.md)** - Version history and release notes

### Community & Support
- **[GitHub Issues](https://github.com/zhurong2020/pyobfus/issues)** - Bug reports and feature requests
- **[GitHub Discussions](https://github.com/zhurong2020/pyobfus/discussions)** - Questions, ideas, and community help
- **[Security Policy](https://github.com/zhurong2020/pyobfus/blob/main/SECURITY.md)** - How to report security vulnerabilities

### Legal & License
- **[Apache 2.0 License](https://github.com/zhurong2020/pyobfus/blob/main/LICENSE)** - Open source license terms

## Support the Project

If you find pyobfus helpful, consider supporting its development:

[Buy Me A Coffee](https://www.buymeacoffee.com/zhurong052Q)

<a href="https://www.buymeacoffee.com/zhurong052Q" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

Your support helps maintain and improve pyobfus. Thank you!

## Acknowledgments

- Inspired by [Opy](https://github.com/QQuick/Opy)'s AST-based approach
- Clean room implementation - no code copying
