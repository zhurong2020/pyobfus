# Pyobfus v0.1.5 Release Summary

**Release Date**: 2025-11-12
**Version**: 0.1.5
**Type**: Bug Fix & Documentation Release

## Overview

This release addresses three critical issues reported through comprehensive testing:
- **Issue #7**: Critical class attribute renaming bug
- **Issue #8**: Keyword argument limitation documentation
- **Issue #9**: Pro features status clarification

## Issues Resolved

### 🔴 Issue #7: Class Attribute Renaming Inconsistency (CRITICAL)

**Problem**: Class attributes were renamed at declaration but not at reference points, causing `AttributeError` at runtime.

**Example of Bug**:
```python
# Before obfuscation
class Counter:
    _count = 0
    def __init__(self):
        Counter._count += 1  # Reference

# After obfuscation (v0.1.4 - BROKEN)
class I0:
    I1 = 0  # ✅ Declaration renamed
    def __init__(I2):
        I0._count += 1  # ❌ Reference NOT updated - AttributeError!
```

**Solution Implemented**:
- Added class attribute tracking to `SymbolAnalyzer`
  - New `class_attributes` dict: `{class_name: {attribute_names}}`
  - New `all_class_attributes` set for quick lookup
- Enhanced `NameMangler.visit_Attribute()` to rename class attribute references
- Handles all reference patterns:
  - `ClassName.attribute`
  - `cls.attribute` (in classmethods)
  - `self.__class__.attribute`

**Test Coverage**:
- 8 new comprehensive tests
- All patterns verified to work correctly
- Test files: [tests/test_issue_7_class_attributes.py](tests/test_issue_7_class_attributes.py)

**Files Modified**:
- [pyobfus/core/analyzer.py](pyobfus/core/analyzer.py) - Added class attribute tracking
- [pyobfus/transformers/name_mangler.py](pyobfus/transformers/name_mangler.py) - Enhanced attribute visitor

### 🟡 Issue #8: Keyword Argument Limitation (HIGH)

**Problem**: Users were unaware that obfuscated code cannot be called with keyword arguments.

**Example**:
```python
# Before obfuscation
def process(data_path, output_dir):
    pass
process(data_path='./data', output_dir='./output')  # ✅ Works

# After obfuscation
def I0(I1, I2):  # Parameters renamed
    pass
process(data_path='./data', output_dir='./output')  # ❌ TypeError!
process('./data', './output')  # ✅ Works with positional args
```

**Solution Implemented**:
- Added prominent documentation in README
- Clear examples of the issue and workarounds
- Recommendations:
  - Use positional arguments only
  - Exclude public API functions from obfuscation using `exclude_names`
  - Test obfuscated code thoroughly

**Files Modified**:
- [README.md](README.md) - Added "Limitations" section with keyword arguments warning

### 🟢 Issue #9: Pro Features Status Unclear (MEDIUM)

**Problem**: Users couldn't tell which features were implemented vs. planned.

**Solution Implemented**:
- Reorganized README features section into:
  - ✅ **Free Edition (Current Version)** - fully implemented features
  - 🔒 **Pro Edition (Planned for v0.2.0+)** - planned features with timeline
- Added clear note that Pro config options are accepted but have no effect
- Roadmap for Pro features:
  - v0.2.0: String encoding, control flow obfuscation
  - v0.3.0: Dead code injection, opaque predicates

**Files Modified**:
- [README.md](README.md) - Reorganized features section with clear status indicators

## Technical Changes

### Code Changes
1. **pyobfus/core/analyzer.py**
   - Added `class_attributes: Dict[str, Set[str]]` - maps class names to attributes
   - Added `all_class_attributes: Set[str]` - all class attribute names
   - Added `_current_class_name: Optional[str]` - track current class during analysis
   - Enhanced `visit_ClassDef()` to analyze class-level assignments

2. **pyobfus/transformers/name_mangler.py**
   - Enhanced `visit_Attribute()` to handle both methods and class attributes
   - Now checks `analyzer.all_class_attributes` in addition to `method_names`

### Documentation Changes
1. **README.md**
   - Added "Limitations" section with keyword arguments warning
   - Reorganized "Features" section with Free vs Pro distinction
   - Added examples and workarounds

2. **CHANGELOG.md**
   - Added v0.1.5 release notes with detailed changes

### Version Updates
1. **pyobfus/__init__.py**: `__version__ = "0.1.5"`
2. **pyproject.toml**: `version = "0.1.5"`

## Test Results

```
==================== 87 passed, 1 xfailed, 1 xpassed in 2.98s =====================
Code Coverage: 53% (up from 38%)
```

### New Tests Added
- `tests/test_issue_7_class_attributes.py` - 8 tests
  - `test_class_attribute_direct_access`
  - `test_class_attribute_cls_access`
  - `test_class_attribute_instance_access`
  - `test_multiple_class_attributes`
  - `test_class_attribute_with_self_class`
  - `test_class_attribute_analyzer_tracking`
  - `test_class_attribute_vs_method`
  - `test_issue_7_exact_reproduction`

## Migration Guide

### For v0.1.4 Users

**No breaking changes** - this is a bug fix release.

1. **Automatic Benefits**:
   - Class attribute obfuscation now works correctly
   - No code changes needed on your part

2. **Action Required**:
   - Review keyword argument usage in your code
   - If using keyword arguments:
     - Option A: Switch to positional arguments
     - Option B: Exclude public functions with `exclude_names`

3. **Recommended**:
   - Re-test your obfuscated code
   - Review README limitations section

## GitHub Issues

All issues have been closed:
- ✅ [Issue #7](https://github.com/zhurong2020/pyobfus/issues/7) - Class attribute bug - **CLOSED**
- ✅ [Issue #8](https://github.com/zhurong2020/pyobfus/issues/8) - Keyword arguments - **CLOSED**
- ✅ [Issue #9](https://github.com/zhurong2020/pyobfus/issues/9) - Pro features status - **CLOSED**

## What's Next?

### v0.1.6 (Bug Fixes)
- Address any new issues from community testing
- Performance optimizations
- Documentation improvements

### v0.2.0 (Pro Features)
- String encoding implementation
- Control flow obfuscation
- License-gated Pro features
- Enhanced configuration options

### v0.3.0 (Advanced Features)
- Dead code injection
- Opaque predicates
- Anti-debugging enhancements
- Bytecode optimization

## Credits

- Issues discovered and reported through comprehensive testing
- Test cases provided by the community
- All contributors to the pyobfus project

## Links

- **GitHub**: https://github.com/zhurong2020/pyobfus
- **PyPI**: https://pypi.org/project/pyobfus/
- **Documentation**: See README.md
- **Changelog**: See CHANGELOG.md

---

**Released by**: Rong Zhu
**License**: Apache-2.0
