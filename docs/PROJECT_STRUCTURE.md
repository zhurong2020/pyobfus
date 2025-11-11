# Project Structure

This document describes the organization of the pyobfus codebase.

## Directory Layout

```
pyobfus/
├── .github/              # GitHub configuration
│   └── workflows/        # CI/CD pipelines
│       └── ci.yml        # Test and code quality checks
│
├── pyobfus/              # Main package
│   ├── __init__.py       # Package version and exports
│   ├── cli.py            # Command-line interface
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exception classes
│   ├── utils.py          # Utility functions
│   │
│   ├── core/             # Core obfuscation engine
│   │   ├── parser.py     # AST parsing
│   │   ├── analyzer.py   # Symbol table and scope analysis
│   │   ├── transformer.py# Base transformer class
│   │   └── generator.py  # Code generation
│   │
│   ├── transformers/     # Obfuscation transformers
│   │   ├── name_mangler.py  # Variable/function name obfuscation
│   │   └── ...           # Additional transformers
│   │
│   └── plugins/          # Plugin system
│       ├── base.py       # Plugin base classes
│       └── ...           # Plugin implementations
│
├── tests/                # Test suite
│   ├── test_core/        # Tests for core modules
│   │   ├── test_parser.py
│   │   └── test_analyzer.py
│   ├── test_transformers/# Tests for transformers
│   │   └── test_name_mangler.py
│   ├── integration/      # Integration tests
│   │   └── test_simple_obfuscation.py
│   ├── fixtures/         # Test fixtures
│   └── test_utils.py     # Utility tests
│
├── examples/             # Example files
│   ├── simple.py         # Basic obfuscation example
│   └── multifile/        # Multi-file project example
│       ├── calculator.py
│       ├── utils.py
│       ├── main.py
│       └── pyobfus.yaml
│
├── pyproject.toml        # Project configuration and dependencies
├── README.md             # Project documentation
├── CHANGELOG.md          # Version history
├── ROADMAP.md            # Development roadmap
├── CONTRIBUTING.md       # Contribution guidelines
├── LICENSE               # Apache 2.0 license
├── .gitignore            # Git ignore patterns
└── .editorconfig         # Editor configuration

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

Additional transformers can be added following the same pattern.

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

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Run full test suite
4. Create git tag: `git tag v0.1.0`
5. Push tag: `git push origin v0.1.0`
6. Build distribution: `python -m build`
7. Upload to PyPI: `python -m twine upload dist/*`

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
