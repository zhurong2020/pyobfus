# pyobfus Examples

This directory contains example code demonstrating pyobfus obfuscation features.

## Examples Overview

### 1. Simple Example (`simple.py`)

**Purpose**: Basic single-file obfuscation demonstration

**What it does**: A simple cardiovascular risk calculator that demonstrates:
- Function name obfuscation
- Variable name obfuscation
- Docstring removal
- Comment removal

**How to use**:
```bash
# Run the original
python examples/simple.py

# Obfuscate it
pyobfus examples/simple.py -o examples/simple_obfuscated.py

# Run the obfuscated version
python examples/simple_obfuscated.py

# Compare the two files
diff examples/simple.py examples/simple_obfuscated.py
```

**Expected output**: Both versions produce identical results, but the obfuscated code has renamed variables and removed comments.

### 2. Multi-file Project (`multifile/`)

**Purpose**: Demonstrates obfuscating a multi-file Python project

**Structure**:
```
multifile/
├── pyobfus.yaml      # Configuration file
├── calculator.py     # Main calculation logic
├── utils.py          # Utility functions
├── main.py           # Entry point
└── test_calculator.py # Test file (excluded from obfuscation)
```

**How to use**:
```bash
# Obfuscate the entire directory
pyobfus examples/multifile/ -o examples/multifile_obfuscated/ --config examples/multifile/pyobfus.yaml

# Run the original
python examples/multifile/main.py

# Run the obfuscated version
python examples/multifile_obfuscated/main.py
```

**Configuration highlights** (`pyobfus.yaml`):
- Excludes test files: `test_*.py`
- Preserves specific names: `logger`, `config`, `main`
- Removes docstrings and comments

### 3. Pro Features Examples (`pro_example.py`, `pro_example_full_pro.py`)

**Purpose**: Demonstrates Pro Edition features (requires `pyobfus[pro]`)

**Note**: These examples use advanced features:
- AES-256 string encryption (requires `cryptography` package)
- Anti-debugging checks
- Runtime decryption infrastructure

**Installation for Pro features**:
```bash
pip install pyobfus[pro]
```

**Usage**: Similar to basic examples, but produces more heavily obfuscated code.

## General Usage Pattern

1. **Choose your example**: Start with `simple.py` for basic understanding
2. **Run the original**: Verify the example works
3. **Obfuscate**: Use `pyobfus` command to obfuscate
4. **Verify functionality**: Run obfuscated code to ensure it works
5. **Compare**: Examine differences between original and obfuscated code

## Common Commands

```bash
# Basic obfuscation
pyobfus <input> -o <output>

# With configuration file
pyobfus <input> -o <output> --config pyobfus.yaml

# Obfuscate a directory
pyobfus <directory> -o <output_directory> --config pyobfus.yaml

# See all options
pyobfus --help
```

## Tips for Using Examples

1. **Test first**: Always test the original code works before obfuscating
2. **Use configuration**: The `multifile` example shows best practices for configuration
3. **Exclude tests**: Use `exclude_patterns` to skip test files
4. **Preserve imports**: Built-in and imported names are automatically preserved
5. **Keep originals**: Never overwrite your source code - always use `-o` to specify output

## Creating Your Own Examples

To obfuscate your own code:

1. Create a configuration file (`pyobfus.yaml`):
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
  remove_docstrings: true
  remove_comments: true
```

2. Run obfuscation:
```bash
pyobfus your_project/ -o obfuscated/ --config pyobfus.yaml
```

3. Test thoroughly:
```bash
# Run your test suite on obfuscated code
pytest obfuscated/tests/
```

## Troubleshooting

**Issue**: Obfuscated code doesn't run
- **Solution**: Check if you excluded necessary files (like `__init__.py`)
- **Solution**: Verify all imports are preserved

**Issue**: Variables you want to keep are obfuscated
- **Solution**: Add them to `exclude_names` in configuration

**Issue**: Test files are obfuscated
- **Solution**: Add test patterns to `exclude_patterns`

## Learn More

- [Main README](../README.md) - Project overview and installation
- [Configuration Guide](../README.md#configuration) - Detailed config options
- [Project Structure](../docs/PROJECT_STRUCTURE.md) - For contributors

## Support

- [GitHub Issues](https://github.com/zhurong2020/pyobfus/issues) - Report problems
- [GitHub Discussions](https://github.com/zhurong2020/pyobfus/discussions) - Ask questions
