"""
Unit tests for ExportedNameTransformer.

Tests cover:
- Class definition renaming
- Function definition renaming
- Variable assignment renaming
- Nested definitions (not renamed)
- Statistics tracking
"""

import ast

from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.transformers.exported_name_transformer import (
    ExportedNameTransformer,
    transform_exported_names,
    transform_exported_names_from_file,
)
from pyobfus.core.generator import CodeGenerator


class TestExportedNameTransformer:
    """Test suite for ExportedNameTransformer class."""

    def test_initialization(self):
        """Test ExportedNameTransformer initialization."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        transformer = ExportedNameTransformer(table, "calculator")

        assert transformer.global_table is table
        assert transformer.current_module == "calculator"
        assert transformer.name_mappings == {"Calculator": "I0"}
        assert transformer.definitions_renamed == 0
        assert transformer.definitions_unchanged == 0

    def test_rename_simple_class(self):
        """Test renaming simple class definition."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
class Calculator:
    pass
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "calculator")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # astunparse produces "class I0():" while ast.unparse produces "class I0:"
        assert "class I0" in new_source and (
            "class I0:" in new_source or "class I0():" in new_source
        )
        assert "class Calculator" not in new_source
        assert transformer.definitions_renamed == 1

    def test_rename_class_with_methods(self):
        """Test renaming class with methods."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
class Calculator:
    def add(self, a, b):
        return a + b
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "calculator")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # astunparse produces "class I0():" while ast.unparse produces "class I0:"
        assert "class I0" in new_source and (
            "class I0:" in new_source or "class I0():" in new_source
        )
        assert "def add" in new_source  # Method names not renamed

    def test_rename_function(self):
        """Test renaming function definition."""
        table = GlobalSymbolTable()
        table.register_export("utils", "format_result", "I0")

        source = """
def format_result(value):
    return str(value)
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "def I0(value):" in new_source
        assert "def format_result" not in new_source
        assert transformer.definitions_renamed == 1

    def test_rename_async_function(self):
        """Test renaming async function definition."""
        table = GlobalSymbolTable()
        table.register_export("utils", "async_helper", "I0")

        source = """
async def async_helper():
    return 42
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "async def I0():" in new_source
        assert transformer.definitions_renamed == 1

    def test_rename_variable_assignment(self):
        """Test renaming variable assignment."""
        table = GlobalSymbolTable()
        table.register_export("config", "API_KEY", "I0")

        source = """
API_KEY = "secret123"
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "config")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0 = 'secret123'" in new_source
        assert transformer.definitions_renamed == 1

    def test_rename_annotated_assignment(self):
        """Test renaming annotated assignment."""
        table = GlobalSymbolTable()
        table.register_export("config", "API_KEY", "I0")

        source = """
API_KEY: str = "secret123"
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "config")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0: str = 'secret123'" in new_source
        assert transformer.definitions_renamed == 1

    def test_multiple_definitions(self):
        """Test renaming multiple definitions."""
        table = GlobalSymbolTable()
        table.register_export("utils", "format_result", "I0")
        table.register_export("utils", "validate_number", "I1")

        source = """
def format_result(value):
    return str(value)

def validate_number(value):
    return isinstance(value, (int, float))
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "def I0(value):" in new_source
        assert "def I1(value):" in new_source
        assert transformer.definitions_renamed == 2

    def test_dont_rename_unexported(self):
        """Test that unexported definitions are not renamed."""
        table = GlobalSymbolTable()
        table.register_export("utils", "public_func", "I0")

        source = """
def public_func():
    pass

def private_func():
    pass
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "def I0():" in new_source
        assert "def private_func():" in new_source  # Not renamed
        assert transformer.definitions_renamed == 1
        assert transformer.definitions_unchanged == 1

    def test_dont_rename_nested_classes(self):
        """Test that nested classes are not renamed."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
class Calculator:
    class Inner:
        pass
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "calculator")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        # astunparse produces "class X():" while ast.unparse produces "class X:"
        assert "class I0" in new_source and (
            "class I0:" in new_source or "class I0():" in new_source
        )
        assert "class Inner" in new_source  # Nested class not renamed

    def test_dont_rename_nested_functions(self):
        """Test that nested functions are not renamed."""
        table = GlobalSymbolTable()
        table.register_export("utils", "outer", "I0")

        source = """
def outer():
    def inner():
        pass
    return inner
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "def I0():" in new_source
        assert "def inner():" in new_source  # Nested function not renamed

    def test_preserve_decorators(self):
        """Test that decorators are preserved."""
        table = GlobalSymbolTable()
        table.register_export("utils", "my_func", "I0")

        source = """
@decorator
def my_func():
    pass
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "utils")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "@decorator" in new_source
        assert "def I0():" in new_source

    def test_get_statistics(self):
        """Test get_statistics method."""
        table = GlobalSymbolTable()
        table.register_export("utils", "func1", "I0")

        source = """
def func1():
    pass

def func2():
    pass
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "utils")
        transformer.visit(tree)

        stats = transformer.get_statistics()
        assert stats["definitions_renamed"] == 1
        assert stats["definitions_unchanged"] == 1

    def test_repr(self):
        """Test string representation."""
        table = GlobalSymbolTable()
        transformer = ExportedNameTransformer(table, "calculator")

        repr_str = repr(transformer)
        assert "ExportedNameTransformer" in repr_str
        assert "module=calculator" in repr_str
        assert "renamed=0" in repr_str

    def test_transform_exported_names_convenience_function(self):
        """Test transform_exported_names convenience function."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = "class Calculator:\n    pass"
        new_source, stats = transform_exported_names(source, table, "calculator")

        # astunparse produces "class I0():" while ast.unparse produces "class I0:"
        assert "class I0" in new_source and (
            "class I0:" in new_source or "class I0():" in new_source
        )
        assert stats["definitions_renamed"] == 1

    def test_empty_module(self):
        """Test transformation of empty module."""
        table = GlobalSymbolTable()

        source = ""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "calculator")
        _new_tree = transformer.visit(tree)  # noqa: F841

        assert transformer.definitions_renamed == 0
        assert transformer.definitions_unchanged == 0

    def test_module_without_exports(self):
        """Test module without exported names."""
        table = GlobalSymbolTable()

        source = """
def helper():
    pass
"""
        tree = ast.parse(source)

        transformer = ExportedNameTransformer(table, "calculator")
        new_tree = transformer.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "def helper():" in new_source  # Not renamed
        assert transformer.definitions_unchanged == 1

    def test_transform_exported_names_from_file(self, tmp_path):
        """Test transform_exported_names_from_file convenience function."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        # Create temporary file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("class Calculator:\n    pass\n")

        new_source, stats = transform_exported_names_from_file(test_file, table, "calculator")

        # astunparse produces "class I0():" while ast.unparse produces "class I0:"
        assert "class I0" in new_source and (
            "class I0:" in new_source or "class I0():" in new_source
        )
        assert stats["definitions_renamed"] == 1
