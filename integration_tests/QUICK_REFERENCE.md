# 🚀 Integration Testing Quick Reference

## One-Line Commands

```bash
# Simplest - test a single file
python scripts/test_ml_research.py your_module.py

# Verbose output
python scripts/test_ml_research.py your_module.py -v

# Batch testing
python scripts/test_ml_research.py --all
```

## Common Commands

```bash
# 1. Test and save results
python scripts/test_ml_research.py module.py -o output.py

# 2. Test multiple files
python scripts/test_ml_research.py --all --max-files 20

# 3. Using pytest
pytest integration_tests/ -v

# 4. Launch Jupyter
jupyter notebook integration_tests/interactive_testing.ipynb
```

## Using in Python

```python
# Import
from integration_tests.test_external_projects import obfuscate_ml_research_module

# Obfuscate
code = obfuscate_ml_research_module("module.py")

# Obfuscate and save
code = obfuscate_ml_research_module("module.py", "output.py")
```

## Typical Workflow

```bash
# 1. Modify pyobfus code
vim pyobfus/transformers/...

# 2. Test immediately (no reinstall needed!)
python scripts/test_ml_research.py test.py -v

# 3. Full testing
python scripts/test_ml_research.py --all
```

## Configuration

Only need to modify once:

```python
# scripts/test_ml_research.py (line 17)
ML_RESEARCH_PATH = Path(r"c:\your\path\to\ml-research")
```

## Troubleshooting

```bash
# Cannot find pyobfus
pip install -e .

# Cannot find ml-research
# Update ML_RESEARCH_PATH above

# Changes not taking effect
# Make sure you used pip install -e .
```

## Advantages ✅

- No need to upload to PyPI
- Changes take effect immediately
- Test with real projects
- Fast iteration

## Comparison with Traditional Approach

Traditional: Modify → Package → Upload to PyPI → pip install → Test → Find issues → Repeat
New approach: Modify → Test ✅

## Example Output

```
🧪 pyobfus Integration Testing
📁 ml-research: c:\...\ml-research

🔄 Processing: data_loader.py
=====================================
📄 Original: 150 lines, 4523 bytes
🔍 Analysis:
   - Total names: 45
   - Obfuscatable: 38
   - Excluded: 7
🔧 Name transformations: 38
🔐 String encoding:
   - Encoded: 12
   - Skipped f-strings: 3
📝 Obfuscated: 153 lines, 5421 bytes
✅ Compilation check: PASSED

✅ Successfully obfuscated data_loader.py
```
