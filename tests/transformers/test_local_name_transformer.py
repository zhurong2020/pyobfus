"""
Unit tests for LocalNameTransformer.

Tests cover:
- Local function call renaming
- Local class instantiation renaming
- Local variable reference renaming
- Not renaming imported names
- Not renaming parameter names
- Not renaming definitions
- Nested function handling
"""

import ast
import pytest
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.transformers.local_name_transformer import (
    LocalNameTransformer,
    transform_local_names,
)


class TestLocalNameTransformer:
    """Test suite for LocalNameTransformer class."""

    def test_initialization(self):
        """Test LocalNameTransformer initialization."""
        table = GlobalSymbolTable()
        table.register_export("main", "run_demo", "I2")

        transformer = LocalNameTransformer(table, "main")

        assert transformer.global_table is table
        assert transformer.current_module == "main"
        assert transformer.local_export_mappings == {"run_demo": "I2"}
        assert transformer.names_renamed == 0
        assert transformer.names_unchanged == 0

    def test_rename_local_function_call(self):
        """Test renaming local function call."""
        table = GlobalSymbolTable()
        table.register_export("main", "run_demo", "I2")

        source = """
def I2():
    pass

if __name__ == "__main__":
    run_demo()
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "main")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I2()" in new_source
        assert "run_demo()" not in new_source
        assert transformer.names_renamed == 1

    def test_rename_local_class_instantiation(self):
        """Test renaming local class instantiation."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
class I0:
    pass

def create():
    return Calculator()
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "calculator")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0()" in new_source
        assert "Calculator()" not in new_source
        assert transformer.names_renamed == 1

    def test_rename_local_variable_reference(self):
        """Test renaming local variable reference."""
        table = GlobalSymbolTable()
        table.register_export("config", "API_KEY", "I0")

        source = """
I0 = "secret"

def get_key():
    return API_KEY
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "config")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "return I0" in new_source
        assert "return API_KEY" not in new_source
        assert transformer.names_renamed == 1

    def test_dont_rename_imported_names(self):
        """Test that imported names are not renamed."""
        table = GlobalSymbolTable()
        table.register_export("main", "run_demo", "I2")
        table.register_export("calculator", "Calculator", "I0")

        # Calculator is imported, should not be renamed
        imported_names = {"Calculator"}

        source = """
from calculator import Calculator

def I2():
    calc = Calculator()
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "main", imported_names)
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # Calculator should NOT be renamed (it's imported)
        assert "Calculator()" in new_source
        # But the import statement still has the old name (ImportRewriter handles that)
        assert transformer.names_renamed == 0  # No local references renamed

    def test_dont_rename_parameter_names(self):
        """Test that parameter names are not renamed."""
        table = GlobalSymbolTable()
        table.register_export("utils", "result", "I0")

        source = """
def format_value(result):
    return str(result)
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # Parameter name should not be renamed
        assert "def format_value(result):" in new_source
        # Reference to parameter should not be renamed either
        assert "str(result)" in new_source

    def test_rename_multiple_references(self):
        """Test renaming multiple references to same name."""
        table = GlobalSymbolTable()
        table.register_export("main", "run_demo", "I2")

        source = """
def I2():
    pass

def wrapper():
    run_demo()
    run_demo()
    return run_demo
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "main")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # Count "I2()" appears in function calls (2 calls + 1 definition = 3 total)
        assert new_source.count("I2()") >= 2  # At least 2 calls
        assert "return I2" in new_source
        assert "run_demo" not in new_source
        assert transformer.names_renamed == 3

    def test_rename_multiple_local_exports(self):
        """Test renaming references to multiple local exports."""
        table = GlobalSymbolTable()
        table.register_export("utils", "format_result", "I0")
        table.register_export("utils", "validate_number", "I1")

        source = """
def I0(value):
    pass

def I1(value):
    pass

def process(x):
    if validate_number(x):
        return format_result(x)
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I1(x)" in new_source
        assert "I0(x)" in new_source
        assert "validate_number" not in new_source
        assert "format_result" not in new_source
        assert transformer.names_renamed == 2

    def test_nested_function_handling(self):
        """Test that nested functions work correctly."""
        table = GlobalSymbolTable()
        table.register_export("utils", "helper", "I0")

        source = """
def I0():
    pass

def outer():
    def inner():
        helper()
    return inner
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # Reference inside nested function should be renamed
        assert "I0()" in new_source
        assert "helper()" not in new_source

    def test_class_method_handling(self):
        """Test that references inside class methods are renamed."""
        table = GlobalSymbolTable()
        table.register_export("utils", "helper", "I0")

        source = """
def I0():
    pass

class MyClass:
    def method(self):
        return helper()
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0()" in new_source
        assert "helper()" not in new_source

    def test_dont_rename_in_store_context(self):
        """Test that names in Store context are not renamed."""
        table = GlobalSymbolTable()
        table.register_export("module", "value", "I0")

        source = """
I0 = 42

def func():
    value = 100  # This is a local assignment, not a reference
    return value
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "module")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # Local assignment should not be renamed
        assert "value = 100" in new_source

    def test_attribute_access_not_renamed(self):
        """Test that attribute names are not renamed."""
        table = GlobalSymbolTable()
        table.register_export("module", "value", "I0")

        source = """
I0 = 42

def func(obj):
    return obj.value  # Attribute access, not name reference
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "module")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # Attribute should not be renamed
        assert "obj.value" in new_source

    def test_get_statistics(self):
        """Test get_statistics method."""
        table = GlobalSymbolTable()
        table.register_export("main", "run_demo", "I2")

        source = """
def I2():
    pass

def wrapper():
    run_demo()
    other_func()
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "main")
        transformer.visit(tree)

        stats = transformer.get_statistics()
        assert stats["names_renamed"] == 1  # run_demo
        assert stats["names_unchanged"] >= 1  # other_func and others

    def test_repr(self):
        """Test string representation."""
        table = GlobalSymbolTable()
        transformer = LocalNameTransformer(table, "main")

        repr_str = repr(transformer)
        assert "LocalNameTransformer" in repr_str
        assert "module=main" in repr_str
        assert "renamed=0" in repr_str

    def test_transform_local_names_convenience_function(self):
        """Test transform_local_names convenience function."""
        table = GlobalSymbolTable()
        table.register_export("main", "run_demo", "I2")

        source = """
def I2():
    pass

if __name__ == "__main__":
    run_demo()
"""
        new_source, stats = transform_local_names(source, table, "main")

        assert "I2()" in new_source
        assert "run_demo()" not in new_source
        assert stats["names_renamed"] == 1

    def test_empty_module(self):
        """Test transformation of empty module."""
        table = GlobalSymbolTable()

        source = ""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "module")
        new_tree = transformer.visit(tree)

        assert transformer.names_renamed == 0
        assert transformer.names_unchanged == 0

    def test_module_without_local_exports(self):
        """Test module without local exported names."""
        table = GlobalSymbolTable()

        source = """
def helper():
    pass

def wrapper():
    helper()
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "module")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # Nothing should be renamed
        assert "helper()" in new_source
        assert transformer.names_renamed == 0

    def test_complex_reference_patterns(self):
        """Test complex reference patterns."""
        table = GlobalSymbolTable()
        table.register_export("utils", "calculate", "I0")

        source = """
def I0():
    pass

def test():
    # Function call
    result = calculate()

    # In expression
    x = calculate() + 10

    # In conditional
    if calculate():
        pass

    # In list
    items = [calculate(), calculate()]

    # As argument
    process(calculate())

    # Return
    return calculate
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # All references should be renamed
        assert "calculate()" not in new_source
        assert new_source.count("I0()") >= 5
        assert "return I0" in new_source

    def test_if_main_idiom(self):
        """Test the common if __name__ == '__main__' pattern."""
        table = GlobalSymbolTable()
        table.register_export("main", "main", "I0")
        table.register_export("main", "run_tests", "I1")

        source = """
def I0():
    pass

def I1():
    pass

if __name__ == '__main__':
    main()
    run_tests()
"""
        tree = ast.parse(source)

        transformer = LocalNameTransformer(table, "main")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0()" in new_source
        assert "I1()" in new_source
        assert "main()" not in new_source
        assert "run_tests()" not in new_source
        assert transformer.names_renamed == 2
