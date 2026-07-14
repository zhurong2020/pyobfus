# Project Structure

This document describes the organization of the pyobfus codebase.

## Directory Layout

```
pyobfus/
├── .github/              # GitHub configuration
│   └── workflows/        # CI/CD pipelines
│       └── ci.yml        # Test and code quality checks
│
├── pyobfus/              # Main package (Community Edition)
│   ├── __init__.py       # Package version and exports
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration management
│   ├── config_templates.py  # Configuration templates (django, flask, etc.)
│   ├── config_validator.py  # Configuration validation with typo detection
│   ├── constants.py      # Centralized URLs and configuration
│   ├── exceptions.py     # Custom exception classes
│   ├── trial.py          # Trial system for Pro features
│   ├── trial_cli.py      # Trial CLI commands
│   ├── utils.py          # Utility functions
│   │
│   ├── core/             # Core obfuscation engine
│   │   ├── parser.py     # AST parsing
│   │   ├── analyzer.py   # Symbol table and scope analysis
│   │   ├── transformer.py# Base transformer class
│   │   └── generator.py  # Code generation with f-string handling
│   │
│   ├── transformers/     # Obfuscation transformers
│   │   ├── name_mangler.py    # Variable/function name obfuscation
│   │   ├── string_encoder.py  # Base64 string encoding
│   │   └── ...           # Additional transformers
│   │
│   └── plugins/          # Plugin system
│       ├── base.py       # Plugin base classes
│       └── ...           # Plugin implementations
│
├── pyobfus_pro/          # Pro Edition (proprietary)
│   ├── __init__.py       # Pro package initialization
│   ├── cli.py            # License management CLI (pyobfus-license)
│   ├── license.py        # License verification system
│   ├── fingerprint.py    # Device fingerprinting
│   ├── string_aes.py     # AES-256 string encryption
│   └── anti_debug.py     # Anti-debugging protection
│
├── cloudflare-worker/    # License server (Cloudflare Workers)
│   ├── src/index.js      # Worker code (license verification + Stripe webhook)
│   ├── wrangler.toml     # Worker configuration
│   └── README.md         # Worker management guide
│
├── tests/                # Test suite (1033 tests, 90% coverage)
│   ├── test_core/        # Tests for core modules
│   ├── test_transformers/# Tests for transformers
│   ├── integration/      # Integration tests
│   ├── fixtures/         # Test fixtures
│   ├── test_license_verification.py  # License system tests
│   ├── test_fingerprint.py     # Device fingerprint tests
│   ├── test_string_aes.py      # AES encryption tests
│   ├── test_anti_debug.py      # Anti-debugging tests
│   ├── test_generator.py       # Code generator tests
│   ├── test_config_features.py # Config template/validation tests
│   └── test_trial.py           # Trial system tests
│
├── integration_tests/    # External project testing
│   ├── test_external_projects.py  # pytest suite
│   ├── interactive_testing.ipynb  # Jupyter notebook
│   ├── README.md         # Detailed instructions
│   └── QUICK_REFERENCE.md # Quick command reference
│
├── examples/             # Example files
│   ├── simple.py         # Basic obfuscation example
│   ├── string_encoding.py      # String encoding demo
│   ├── keyword_arguments.py    # Parameter preservation demo
│   └── multifile/        # Multi-file project example
│
├── scripts/              # Utility scripts
│   ├── test_ml_research.py     # CLI testing tool
│   ├── setup_stripe_webhook.py # Stripe webhook configuration
│   └── test_license_server.py  # License server integration tests
│
├── pyproject.toml        # Project configuration and dependencies
├── README.md             # Project documentation
├── CHANGELOG.md          # Version history
├── CONTRIBUTING.md       # Contribution guidelines
├── SECURITY.md           # Security policy
├── LICENSE               # Dual license (Apache 2.0 for core, Proprietary for Pro)
├── .gitignore            # Git ignore patterns
├── .editorconfig         # Editor configuration
└── docs/                 # Documentation
    ├── index.md          # GitHub Pages homepage
    ├── ROADMAP.md        # Development roadmap
    ├── COMPARISON.md     # Tool comparison (vs PyArmor, etc.)
    ├── PROJECT_STRUCTURE.md    # This file
    ├── LICENSE_ACTIVATION_GUIDE.md  # Pro license activation
    ├── INTEGRATION_TESTING.md  # Integration testing guide
    ├── internal/         # Internal docs (git-ignored)
    └── legal/            # Legal documents
        ├── TERMS_OF_SERVICE.md
        ├── REFUND_POLICY.md
        └── PRIVACY_POLICY.md

```

## Module Descriptions

### Core Modules

**`pyobfus/cli.py`**
- Command-line interface using Click framework
- Handles argument parsing and command execution
- Entry point for the `pyobfus` command

**`pyobfus/config.py`**
- Configuration data classes
- YAML file loading and validation
- Default configuration settings

**`pyobfus/exceptions.py`**
- Custom exception hierarchy
- Error types for parsing, analysis, and transformation

### Core Engine

**`pyobfus/core/parser.py`**
- Wraps Python's `ast` module
- Handles syntax errors and Python version compatibility
- Provides AST parsing functionality

**`pyobfus/core/analyzer.py`**
- Symbol table construction
- Scope analysis (module, class, function)
- Determines which names can be obfuscated

**`pyobfus/core/transformer.py`**
- Base class for all transformers
- AST visitor pattern implementation
- Transformer pipeline management

**`pyobfus/core/generator.py`**
- Code generation from AST
- Uses `ast.unparse()` for Python 3.9+
- Ensures syntactically correct output

### Transformers

**`pyobfus/transformers/name_mangler.py`**
- Renames variables, functions, classes
- Uses index-based naming (I0, I1, I2...)
- Respects scope rules and exclusion lists
- Supports cross-file consistent naming (v0.2.0+)

**`pyobfus/transformers/string_encoder.py`**
- Base64 encoding for string literals
- Automatic decoder function injection
- F-string expression preservation

Additional transformers can be added following the same pattern.

### Pro Edition Modules

**`pyobfus_pro/license.py`**
- License verification against Cloudflare Worker API
- Local caching with HMAC-SHA256 signing
- Device fingerprint validation
- 3-day cache duration with offline fallback

**`pyobfus_pro/fingerprint.py`**
- Device fingerprinting (MAC + hostname + OS)
- Cross-platform support (Windows, macOS, Linux)
- Tamper-resistant design

**`pyobfus_pro/string_aes.py`**
- AES-256 string encryption
- Runtime decryption infrastructure
- Automatic key management

**`pyobfus_pro/anti_debug.py`**
- Anti-debugging checks injection
- Debugger detection techniques
- Runtime protection

### Plugins

**`pyobfus/plugins/base.py`**
- Plugin interface definition
- Plugin discovery and loading
- Extension point for custom transformers

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/zhurong2020/pyobfus.git
cd pyobfus

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pyobfus --cov-report=html

# Run specific test file
pytest tests/test_core/test_parser.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black pyobfus/ tests/

# Type checking
mypy pyobfus/

# Linting
ruff check pyobfus/ tests/

# Run all checks (same as CI)
black pyobfus/ tests/
mypy pyobfus/
ruff check pyobfus/ tests/
pytest --cov=pyobfus
```

## Adding New Features

### Adding a New Transformer

1. Create a new file in `pyobfus/transformers/`
2. Inherit from `BaseTransformer`
3. Implement the `transform()` method
4. Add visitor methods for specific AST nodes
5. Register in `pyobfus/transformers/__init__.py`
6. Add tests in `tests/test_transformers/`
7. Update documentation

Example:

```python
# pyobfus/transformers/my_transformer.py
from pyobfus.core.transformer import BaseTransformer

class MyTransformer(BaseTransformer):
    def transform(self, tree):
        # Your transformation logic
        return self.visit(tree)

    def visit_FunctionDef(self, node):
        # Transform function definitions
        self.generic_visit(node)
        return node
```

### Adding Tests

1. Create test file following naming convention `test_*.py`
2. Use pytest fixtures for common setup
3. Test both success and failure cases
4. Ensure test coverage > 80%
5. Run tests locally before submitting PR

## Configuration Files

**`pyproject.toml`**
- Project metadata and dependencies
- Tool configurations (black, mypy, ruff, pytest)
- Build system settings

**`.editorconfig`**
- Editor settings for consistent code style
- Indentation, line endings, encoding

**`.gitignore`**
- Files to exclude from version control
- Generated files, virtual environments, etc.

## Release Process

**Version is defined in ONE place**: `pyproject.toml`

1. Update version in `pyproject.toml` (single source of truth)
2. Update `CHANGELOG.md` with release notes
3. Run full test suite: `pytest tests/ -v`
4. Create git tag: `git tag vX.Y.Z`
5. Push tag: `git push origin vX.Y.Z`
6. Build distribution: `python -m build`
7. Upload to PyPI: `python -m twine upload dist/*`

Note: `pyobfus.__version__` is automatically read from package metadata via `importlib.metadata`.

## Troubleshooting

### Common Issues

**Import errors**: Ensure package is installed in editable mode: `pip install -e .`

**Test failures**: Check Python version compatibility and dependencies

**Type checking errors**: Update type hints or adjust mypy configuration

**Coverage too low**: Add tests for uncovered code paths

## Additional Resources

- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
- [Green Tree Snakes (AST Tutorial)](https://greentreesnakes.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)
- [Click Documentation](https://click.palletsprojects.com/)
