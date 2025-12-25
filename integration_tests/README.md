# Integration Tests for External Projects

This directory contains integration tests for testing pyobfus on real projects (e.g., ml-research).

## Setup

### 1. Configure ml-research Path

Edit the path configuration in the test file:

```python
# integration_tests/test_external_projects.py
ML_RESEARCH_PATH = Path(r"c:\path\to\your\ml-research")
```

Or in the script:

```python
# scripts/test_ml_research.py
ML_RESEARCH_PATH = Path(r"c:\path\to\your\ml-research")
```

### 2. Install pyobfus (Development Mode)

```bash
pip install -e .
```

## Usage

### Method 1: Using Convenience Script (Recommended)

```bash
# Test a single file
python scripts/test_ml_research.py your_module.py

# Test a file at a specific path
python scripts/test_ml_research.py "utils/preprocessing.py"

# Test all files (first 10)
python scripts/test_ml_research.py --all

# Test more files
python scripts/test_ml_research.py --all --max-files 20

# Verbose output
python scripts/test_ml_research.py module.py -v

# Save obfuscated code
python scripts/test_ml_research.py module.py -o obfuscated/module_obf.py
```

### Method 2: Using pytest

```bash
# Run all integration tests
pytest integration_tests/ -v

# Run specific test
pytest integration_tests/test_external_projects.py::TestMLResearchModules::test_obfuscation_preserves_functionality -v

# Batch testing
pytest integration_tests/test_external_projects.py::TestMLResearchModules::test_batch_obfuscation -v
```

### Method 3: Using in Python Script

```python
from integration_tests.test_external_projects import obfuscate_ml_research_module

# Obfuscate a single module
obfuscated_code = obfuscate_ml_research_module(
    "data_processing.py",
    output_path="obf/data_processing_obf.py",
    enable_string_encoding=True
)

print(obfuscated_code)
```

### Method 4: Interactive Testing (Python REPL)

```python
# In the pyobfus project root directory
python

>>> from pathlib import Path
>>> from integration_tests.test_external_projects import obfuscate_ml_research_module

>>> # Test your module
>>> code = obfuscate_ml_research_module("your_module.py")
>>> print(code)

>>> # Save to file
>>> Path("obf_output.py").write_text(code)
```

## Test Scenarios

### Scenario 1: Quick Validation (Single File)

After modifying pyobfus code, quickly validate:

```bash
# 1. Modify pyobfus code
vim pyobfus/transformers/string_encoder.py

# 2. Test immediately
python scripts/test_ml_research.py test_module.py -v

# 3. Review output, identify issues
# 4. Modify pyobfus
# 5. Retest (no reinstall needed)
```

### Scenario 2: Full Regression Testing

Before releasing a new version, test all modules:

```bash
# Test all files
python scripts/test_ml_research.py --all --max-files 50

# View summary
# ✅ Successful: 45/50
# ❌ Failed: 5/50
```

### Scenario 3: Debugging Specific Issues

When a module fails to obfuscate:

```bash
# Use verbose mode to see details
python scripts/test_ml_research.py problematic_module.py -v

# Output shows:
# - Code analysis statistics
# - Name transformation count
# - String encoding statistics
# - Compilation check result
# - Detailed error messages
```

### Scenario 4: Comparison Testing

Test functional equivalence before and after obfuscation:

```python
# integration_tests/test_external_projects.py
def test_obfuscate_and_execute(self):
    # Execute original code
    original_namespace = {}
    exec(original_code, original_namespace)

    # Execute obfuscated code
    obfuscated_namespace = {}
    exec(obfuscated_code, obfuscated_namespace)

    # Compare results
    assert original_namespace['result'] == obfuscated_namespace['result']
```

## Custom Tests

### Adding Specific Module Tests

Edit `integration_tests/test_external_projects.py`:

```python
def test_specific_ml_modules(self):
    modules_to_test = [
        "data_loader.py",
        "model_trainer.py",
        "utils/preprocessing.py",
    ]

    for module_name in modules_to_test:
        # ... test logic ...
```

### Custom Obfuscation Configuration

```python
from pyobfus.config import ObfuscationConfig

# Create custom configuration
config = ObfuscationConfig()
config.string_encoding = True
config.preserve_param_names = True
config.add_exclude_name("important_function")

# Test with custom configuration
obfuscated_code = self.obfuscate_file(file_path, config)
```

## Workflow Example

### Typical Development Flow

```bash
# 1. Develop new feature in pyobfus
cd /path/to/pyobfus
vim pyobfus/transformers/new_feature.py

# 2. Unit tests
pytest tests/test_new_feature.py -v

# 3. Integration tests (using ml-research)
python scripts/test_ml_research.py --all

# 4. If issues found, view details
python scripts/test_ml_research.py problematic_file.py -v

# 5. Fix issues
vim pyobfus/transformers/new_feature.py

# 6. Retest (no reinstall needed!)
python scripts/test_ml_research.py problematic_file.py -v

# 7. Commit after all tests pass
git add .
git commit -m "feat: Add new feature"
```

## Advantages

✅ **Fast Iteration**: Test immediately after changes, no reinstall needed
✅ **Real Scenarios**: Test with actual project code
✅ **No PyPI Pollution**: No need to publish to PyPI for testing
✅ **Easy Debugging**: Detailed error messages and statistics
✅ **Batch Testing**: Test multiple files at once
✅ **Flexible Configuration**: Customizable obfuscation settings

## Troubleshooting

### Problem: Cannot find ml-research

```
❌ ml-research project not found at: ...
```

**Solution**: Update `ML_RESEARCH_PATH` in the test file

### Problem: Import error

```
ModuleNotFoundError: No module named 'pyobfus'
```

**Solution**: Install development version
```bash
pip install -e .
```

### Problem: Compilation error

```
❌ Syntax error in obfuscated code
```

**Solution**: Use verbose mode for details
```bash
python scripts/test_ml_research.py module.py -v
```

## Next Steps

- Fix issues based on test results
- Add more specific scenario tests
- Automate testing (CI/CD)
- Performance benchmarking
