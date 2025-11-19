"""
Unit tests for ExportDetector.

Tests cover:
- __all__ detection
- Top-level definitions (functions, classes, variables)
- Private name exclusion
- Nested structures
- Import re-exports
- Edge cases
"""

import ast
import pytest

from pyobfus.core.export_detector import ExportDetector, detect_exports


class TestExportDetector:
    """Test suite for ExportDetector class."""

    def test_empty_module(self):
        """Test detection in empty module."""
        source = ""
        exports = detect_exports(source)

        assert len(exports) == 0

    def test_single_function(self):
        """Test detection of single top-level function."""
        source = """
def public_function():
    pass
"""
        exports = detect_exports(source)

        assert "public_function" in exports
        assert len(exports) == 1

    def test_multiple_functions(self):
        """Test detection of multiple functions."""
        source = """
def func1():
    pass

def func2():
    pass

def func3():
    pass
"""
        exports = detect_exports(source)

        assert exports == {"func1", "func2", "func3"}

    def test_private_function_excluded(self):
        """Test that private functions (starting with _) are excluded."""
        source = """
def public_func():
    pass

def _private_func():
    pass

def __double_private():
    pass
"""
        exports = detect_exports(source)

        assert "public_func" in exports
        assert "_private_func" not in exports
        assert "__double_private" not in exports
        assert len(exports) == 1

    def test_class_definition(self):
        """Test detection of class definitions."""
        source = """
class PublicClass:
    pass

class AnotherClass:
    def method(self):
        pass
"""
        exports = detect_exports(source)

        assert "PublicClass" in exports
        assert "AnotherClass" in exports
        assert len(exports) == 2

    def test_private_class_excluded(self):
        """Test that private classes are excluded."""
        source = """
class PublicClass:
    pass

class _PrivateClass:
    pass
"""
        exports = detect_exports(source)

        assert "PublicClass" in exports
        assert "_PrivateClass" not in exports
        assert len(exports) == 1

    def test_variable_assignment(self):
        """Test detection of top-level variable assignments."""
        source = """
public_var = 42
another_var = "hello"
"""
        exports = detect_exports(source)

        assert "public_var" in exports
        assert "another_var" in exports
        assert len(exports) == 2

    def test_private_variable_excluded(self):
        """Test that private variables are excluded."""
        source = """
public_var = 42
_private_var = 100
"""
        exports = detect_exports(source)

        assert "public_var" in exports
        assert "_private_var" not in exports
        assert len(exports) == 1

    def test_annotated_assignment(self):
        """Test detection of annotated assignments."""
        source = """
public_var: int = 42
another_var: str = "hello"
_private_var: int = 100
"""
        exports = detect_exports(source)

        assert "public_var" in exports
        assert "another_var" in exports
        assert "_private_var" not in exports
        assert len(exports) == 2

    def test_async_function(self):
        """Test detection of async functions."""
        source = """
async def async_public():
    pass

async def _async_private():
    pass
"""
        exports = detect_exports(source)

        assert "async_public" in exports
        assert "_async_private" not in exports
        assert len(exports) == 1

    def test_nested_function_not_exported(self):
        """Test that nested functions are not exported."""
        source = """
def outer():
    def inner():
        pass
    return inner
"""
        exports = detect_exports(source)

        assert "outer" in exports
        assert "inner" not in exports
        assert len(exports) == 1

    def test_nested_class_not_exported(self):
        """Test that nested classes are not exported."""
        source = """
class Outer:
    class Inner:
        pass
"""
        exports = detect_exports(source)

        assert "Outer" in exports
        assert "Inner" not in exports
        assert len(exports) == 1

    def test_method_not_exported(self):
        """Test that class methods are not exported."""
        source = """
class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass
"""
        exports = detect_exports(source)

        assert "MyClass" in exports
        assert "method1" not in exports
        assert "method2" not in exports
        assert len(exports) == 1

    def test_all_list_explicit(self):
        """Test detection of explicit __all__ list."""
        source = """
__all__ = ["func1", "ClassA"]

def func1():
    pass

def func2():
    pass

class ClassA:
    pass

class ClassB:
    pass
"""
        exports = detect_exports(source)

        # Only names in __all__ should be exported
        assert exports == {"func1", "ClassA"}
        assert "func2" not in exports
        assert "ClassB" not in exports

    def test_all_tuple(self):
        """Test __all__ as tuple."""
        source = """
__all__ = ("func1", "ClassA")

def func1():
    pass

def func2():
    pass

class ClassA:
    pass
"""
        exports = detect_exports(source)

        assert exports == {"func1", "ClassA"}

    def test_all_with_private_names(self):
        """Test that __all__ can include private names."""
        source = """
__all__ = ["_private_func"]

def _private_func():
    pass

def public_func():
    pass
"""
        exports = detect_exports(source)

        # __all__ overrides private name convention
        assert "_private_func" in exports
        assert "public_func" not in exports
        assert len(exports) == 1

    def test_all_empty(self):
        """Test empty __all__ list."""
        source = """
__all__ = []

def func():
    pass
"""
        exports = detect_exports(source)

        # Empty __all__ means nothing is exported
        assert len(exports) == 0

    def test_import_from_statement(self):
        """Test that imported names can be re-exported."""
        source = """
from other_module import imported_func, ImportedClass

def local_func():
    pass
"""
        exports = detect_exports(source)

        assert "imported_func" in exports
        assert "ImportedClass" in exports
        assert "local_func" in exports

    def test_import_with_alias(self):
        """Test import with alias."""
        source = """
from other_module import original_name as alias_name

def local_func():
    pass
"""
        exports = detect_exports(source)

        # Alias name is what's available in this module
        assert "alias_name" in exports
        assert "original_name" not in exports
        assert "local_func" in exports

    def test_import_statement(self):
        """Test import statement."""
        source = """
import os
import sys

def local_func():
    pass
"""
        exports = detect_exports(source)

        assert "os" in exports
        assert "sys" in exports
        assert "local_func" in exports

    def test_import_module_with_alias(self):
        """Test import module with alias."""
        source = """
import os.path as ospath
"""
        exports = detect_exports(source)

        assert "ospath" in exports
        assert "os" not in exports

    def test_wildcard_import_ignored(self):
        """Test that wildcard imports are ignored."""
        source = """
from other_module import *
"""
        exports = detect_exports(source)

        # Wildcard doesn't add specific exports
        assert len(exports) == 0

    def test_mixed_definitions(self):
        """Test module with mixed definitions."""
        source = """
def func():
    pass

class MyClass:
    def method(self):
        pass

variable = 42

async def async_func():
    pass
"""
        exports = detect_exports(source)

        assert exports == {"func", "MyClass", "variable", "async_func"}

    def test_get_statistics(self):
        """Test get_statistics method."""
        source = """
__all__ = ["func1", "ClassA"]

def func1():
    pass

def func2():
    pass

class ClassA:
    pass
"""
        tree = ast.parse(source)
        detector = ExportDetector()
        detector.visit(tree)

        stats = detector.get_statistics()

        assert stats["has_all"] is True
        assert stats["all_count"] == 2
        assert stats["potential_exports"] >= 2
        assert stats["final_exports"] == 2

    def test_no_all_statistics(self):
        """Test statistics when __all__ is not defined."""
        source = """
def func():
    pass

class MyClass:
    pass
"""
        tree = ast.parse(source)
        detector = ExportDetector()
        detector.visit(tree)

        stats = detector.get_statistics()

        assert stats["has_all"] is False
        assert stats["all_count"] == 0
        assert stats["potential_exports"] == 2
        assert stats["final_exports"] == 2

    def test_complex_all_expression(self):
        """Test __all__ with list concatenation."""
        source = """
__all__ = ["func1"] + ["func2"]

def func1():
    pass

def func2():
    pass

def func3():
    pass
"""
        exports = detect_exports(source)

        assert "func1" in exports
        assert "func2" in exports
        assert "func3" not in exports
        assert len(exports) == 2

    def test_decorator_on_function(self):
        """Test that decorated functions are still detected."""
        source = """
def decorator(f):
    return f

@decorator
def decorated_func():
    pass
"""
        exports = detect_exports(source)

        assert "decorator" in exports
        assert "decorated_func" in exports

    def test_decorator_on_class(self):
        """Test that decorated classes are still detected."""
        source = """
def decorator(cls):
    return cls

@decorator
class DecoratedClass:
    pass
"""
        exports = detect_exports(source)

        assert "decorator" in exports
        assert "DecoratedClass" in exports

    def test_multiple_assignment(self):
        """Test multiple assignment (a = b = c = value)."""
        source = """
a = b = c = 42
"""
        exports = detect_exports(source)

        assert "a" in exports
        assert "b" in exports
        assert "c" in exports

    def test_class_with_private_methods(self):
        """Test that private methods don't affect class export."""
        source = """
class MyClass:
    def public_method(self):
        pass

    def _private_method(self):
        pass
"""
        exports = detect_exports(source)

        # Only class should be exported, not methods
        assert exports == {"MyClass"}

    def test_detect_exports_from_file(self, tmp_path):
        """Test detect_exports_from_file function."""
        from pyobfus.core.export_detector import detect_exports_from_file

        # Create temporary Python file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("""
def public_func():
    pass

def _private_func():
    pass

class PublicClass:
    pass
""")

        exports = detect_exports_from_file(str(test_file))

        assert "public_func" in exports
        assert "PublicClass" in exports
        assert "_private_func" not in exports
