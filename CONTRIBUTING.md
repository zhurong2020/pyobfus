# Contributing to pyobfus

Thank you for your interest in contributing to pyobfus! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions. We're building this together.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title**: Descriptive summary of the issue
- **Environment**: Python version, OS, pyobfus version
- **Steps to reproduce**: Minimal code example
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Error messages**: Full traceback if applicable

Example:
```
### Bug: Name collision in obfuscated code

**Environment**: Python 3.11, Windows 11, pyobfus 0.1.0

**Steps to reproduce**:
```python
def foo(): pass
def bar(): pass
```

**Expected**: Different obfuscated names
**Actual**: Both become `I0`
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. Provide:

- **Use case**: Why is this feature needed?
- **Proposed solution**: How should it work?
- **Alternatives**: Other ways to solve the problem
- **Examples**: Code showing the feature in use

### Pull Requests

1. **Fork the repository** and create a branch from `main`
2. **Make your changes** following our coding standards
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run tests** and ensure they pass
6. **Submit a pull request** with clear description

#### PR Guidelines

- One feature/fix per PR
- Follow existing code style (black, ruff)
- Include tests for new code
- Update README if adding user-facing features
- Keep commits focused and well-described

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Getting Started

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pyobfus.git
cd pyobfus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests to verify setup
pytest tests/ -v
```

Tests that exercise trial state, license caching, or generated run counters
must isolate those files with pytest's `tmp_path`. Never let a test touch the
developer's real `~/.pyobfus` directory or HOME, and do not make contributors
override `HOME` merely to run the suite. See `AGENTS.md` for the canonical test
isolation rule.

### Development Workflow

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, add tests
# ...

# Run tests
pytest tests/ -v --cov=pyobfus

# Check code style
black pyobfus/
ruff check pyobfus/

# Type checking (optional but recommended)
mypy pyobfus/

# Commit changes
git add .
git commit -m "feat: add awesome feature"

# Push to your fork
git push origin feature/your-feature-name

# Open pull request on GitHub
```

## Coding Standards

### Python Style

- **Formatter**: black (line length: 100)
- **Linter**: ruff
- **Type hints**: Preferred (Python 3.9+ compatible)
- **Docstrings**: Google style for public APIs

### Example

```python
def obfuscate_name(original_name: str, prefix: str = "I") -> str:
    """
    Generate an obfuscated name from the original.

    Args:
        original_name: The original identifier name
        prefix: Prefix for obfuscated names (default: "I")

    Returns:
        str: Obfuscated name

    Example:
        >>> obfuscate_name("calculate_risk")
        'I0'
    """
    # Implementation here
    pass
```

### Type Annotation Best Practices

Follow these guidelines to ensure code passes Pylance type checking:

#### 1. Optional Parameters Must Use Union Types

❌ **Incorrect** - Will fail type checking:
```python
def process_file(path: Path, output: Path = None):
    pass
```

✅ **Correct** - Use `| None` for optional parameters:
```python
def process_file(path: Path, output: Path | None = None):
    pass
```

#### 2. AST Node Type Assertions

When accessing specific AST node attributes, add type assertions:

❌ **Incorrect** - Will fail with "Attribute is unknown":
```python
func_def = tree.body[0]
param_name = func_def.args.args[0].arg  # Error: stmt has no args
```

✅ **Correct** - Use isinstance() for type narrowing:
```python
func_def = tree.body[0]
assert isinstance(func_def, ast.FunctionDef)
param_name = func_def.args.args[0].arg  # OK: type is narrowed
```

For async functions:
```python
func_def = tree.body[0]
assert isinstance(func_def, ast.AsyncFunctionDef)
param_name = func_def.args.args[0].arg
```

#### 3. Optional AST Attributes

Some AST attributes can be None. Add explicit checks:

❌ **Incorrect** - Will fail if attribute is None:
```python
assert func_def.args.vararg.arg == "args"  # Error: vararg can be None
```

✅ **Correct** - Check for None first:
```python
assert func_def.args.vararg is not None
assert func_def.args.vararg.arg == "args"
```

#### 4. General Type Annotation Rules

- Use `|` for union types (Python 3.10+): `str | int | None`
- For older Python, import from typing: `from typing import Union, Optional`
- Prefer specific types over `Any` whenever possible
- Use `list[Type]` and `dict[Key, Value]` over `List`, `Dict` (Python 3.9+)
- Always annotate function parameters and return types

#### Common Pylance Error Resolutions

| Error | Cause | Solution |
|-------|-------|----------|
| `reportArgumentType` | Type mismatch in arguments | Use union types for optional params |
| `reportAttributeAccessIssue` | Accessing attribute on base class | Add isinstance() type assertion |
| `"arg" is not a known attribute of "None"` | Optional attribute not checked | Add `is not None` check before access |
| `reportOptionalMemberAccess` | Accessing member on Optional type | Check for None first |

These practices improve both type safety and code clarity while eliminating false positives from static analysis tools.

### Testing Standards

- **Framework**: pytest
- **Coverage target**: 80%+ for new code
- **Test types**: Unit, integration, end-to-end

#### Python 3.8 Caveat (obsolete since 0.5.0)

Python 3.8 was dropped in **0.5.0** (EOL 2024-10; `requires-python` is now
`>=3.9`). The old `astunparse`-on-3.8 flakiness for Pro-feature CLI integration
tests no longer applies, and the `@requires_py39` decorator in
`tests/test_cli_pro_paths.py` is now a no-op (safe to remove during cleanup).
[`docs/PYTHON38_COMPATIBILITY.md`](docs/PYTHON38_COMPATIBILITY.md) is retained as
historical record only.

#### Test Structure

```python
def test_feature_name():
    """Test what the feature does."""
    # Arrange
    input_data = "test"

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

### Commit Message Format

Follow conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, no logic change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(core): add control flow flattening transformer

Implements basic control flow flattening for if/else statements.
Converts branching logic to state machine pattern.

Closes #42
```

```
fix(cli): handle non-existent config file gracefully

Previously would crash with FileNotFoundError.
Now shows user-friendly error message.
```

## Project Structure

```
pyobfus/
├── pyobfus/              # Main package (Community Edition)
│   ├── core/             # Core obfuscation engine
│   │   ├── parser.py     # AST parsing
│   │   ├── analyzer.py   # Symbol analysis
│   │   ├── transformer.py
│   │   └── generator.py
│   ├── transformers/     # Community transformers
│   │   ├── name_mangler.py
│   │   └── string_encoder.py
│   ├── plugins/          # Plugin system
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration management
│   ├── config_templates.py  # Config templates (django, flask, etc.)
│   ├── config_validator.py  # Config validation
│   ├── constants.py      # Centralized URLs and constants
│   ├── exceptions.py     # Custom exceptions
│   └── utils.py          # Utility functions
├── pyobfus_pro/          # Pro Edition (proprietary)
│   ├── license.py        # License verification
│   ├── fingerprint.py    # Device fingerprinting
│   ├── string_aes.py     # AES-256 encryption
│   └── anti_debug.py     # Anti-debugging
├── cloudflare-worker/    # License server
├── tests/                # Test suite (366 tests)
├── integration_tests/    # External project testing
├── examples/             # Example scripts
└── docs/                 # Documentation
```

## Areas for Contribution

### Good First Issues

- Add more test cases
- Improve error messages
- Fix typos in documentation
- Add examples for specific use cases

### Advanced Contributions

- New obfuscation transformers
- Performance optimizations
- Cross-file import mapping
- Integration with build tools

### Documentation

- API documentation improvements
- Tutorial content
- Use case examples
- Translation to other languages

## Community Edition vs Pro Edition

This repository contains only Community Edition features (Apache 2.0 licensed).

**Community Features** (open source):
- Name mangling
- Comment/docstring removal
- Basic string encoding
- Configuration management
- CLI interface

**Pro Features** (proprietary, not in repo):
- AES-256 string encryption
- Control flow flattening
- Anti-debugging
- Advanced dead code injection

**Contributing to Pro features**: Contact maintainers directly.

## Getting Help

- **Questions**: Use [GitHub Discussions](https://github.com/zhurong2020/pyobfus/discussions)
- **Bugs**: Open an [issue](https://github.com/zhurong2020/pyobfus/issues)
- **Security**: Email security@pyobfus.dev (do not open public issues)

## Recognition

Contributors will be:
- Listed in README.md
- Credited in release notes
- Given co-author attribution in commits (if significant contribution)

## License

**Dual License Model**: pyobfus uses an Open Core model:
- **pyobfus** (Core): Apache 2.0 - Open source
- **pyobfus_pro** (Pro): Proprietary - Requires paid license

By contributing, you agree that your contributions to the Community Edition (pyobfus) will be licensed under the Apache License 2.0. Pro features (pyobfus_pro) are not open source and not accepting external contributions.

---

Thank you for making pyobfus better! 🎉
