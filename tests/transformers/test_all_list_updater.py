"""
Unit tests for AllListUpdater.

Tests cover:
- Simple list form
- Tuple form
- Annotated assignments
- Names not found (preserved)
- List concatenation
- Statistics tracking
- Convenience functions
"""

import ast

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.transformers.all_list_updater import (
    AllListUpdater,
    update_all_list,
    update_all_list_from_file,
)


class TestAllListUpdater:
    """Test suite for AllListUpdater class."""

    def test_initialization(self):
        """Test AllListUpdater initialization."""
        table = GlobalSymbolTable()
        updater = AllListUpdater(table, "calculator")

        assert updater.global_table is table
        assert updater.current_module == "calculator"
        assert updater.all_lists_updated == 0
        assert updater.names_updated == 0
        assert len(updater.names_not_found) == 0

    def test_simple_list_update(self):
        """Test updating simple __all__ list."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = '__all__ = ["Calculator"]'
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert '__all__ = ["I0"]' in new_source or "__all__ = ['I0']" in new_source
        assert updater.all_lists_updated == 1
        assert updater.names_updated == 1

    def test_multiple_names_in_list(self):
        """Test updating __all__ list with multiple names."""
        table = GlobalSymbolTable()
        table.register_export("utils", "format_result", "I0")
        table.register_export("utils", "validate_number", "I1")
        table.register_export("utils", "calculate_percentage", "I2")

        source = '__all__ = ["format_result", "validate_number", "calculate_percentage"]'
        tree = ast.parse(source)

        updater = AllListUpdater(table, "utils")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0" in new_source
        assert "I1" in new_source
        assert "I2" in new_source
        assert updater.all_lists_updated == 1
        assert updater.names_updated == 3

    def test_tuple_form(self):
        """Test updating __all__ as tuple."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")
        table.register_export("calculator", "add", "I1")

        source = '__all__ = ("Calculator", "add")'
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0" in new_source
        assert "I1" in new_source
        assert updater.all_lists_updated == 1
        assert updater.names_updated == 2

    def test_annotated_assignment(self):
        """Test updating annotated __all__ assignment."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = '__all__: list[str] = ["Calculator"]'
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0" in new_source
        assert "list[str]" in new_source
        assert updater.all_lists_updated == 1

    def test_names_not_found(self):
        """Test that names not in global table are preserved."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = '__all__ = ["Calculator", "NotFound"]'
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0" in new_source
        assert "NotFound" in new_source
        assert updater.names_updated == 1
        assert "NotFound" in updater.names_not_found

    def test_list_concatenation(self):
        """Test updating __all__ with list concatenation."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")
        table.register_export("calculator", "add", "I1")

        source = '__all__ = ["Calculator"] + ["add"]'
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0" in new_source
        assert "I1" in new_source
        assert updater.all_lists_updated == 1

    def test_empty_all_list(self):
        """Test that empty __all__ list is preserved."""
        table = GlobalSymbolTable()

        source = "__all__ = []"
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "__all__ = []" in new_source
        assert updater.all_lists_updated == 1
        assert updater.names_updated == 0

    def test_get_statistics(self):
        """Test get_statistics method."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = '__all__ = ["Calculator", "NotFound"]'
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        updater.visit(tree)

        stats = updater.get_statistics()
        assert stats["all_lists_updated"] == 1
        assert stats["names_updated"] == 1
        assert "NotFound" in stats["names_not_found"]

    def test_repr(self):
        """Test string representation."""
        table = GlobalSymbolTable()
        updater = AllListUpdater(table, "calculator")

        repr_str = repr(updater)
        assert "AllListUpdater" in repr_str
        assert "module=calculator" in repr_str
        assert "updated=0" in repr_str

    def test_update_all_list_convenience_function(self):
        """Test update_all_list convenience function."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = '__all__ = ["Calculator"]'
        new_source, stats = update_all_list(source, table, "calculator")

        assert "I0" in new_source
        assert stats["all_lists_updated"] == 1

    def test_preserve_non_all_code(self):
        """Test that code other than __all__ is preserved."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
__all__ = ["Calculator"]

class Calculator:
    def add(self, a, b):
        return a + b
"""
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        new_tree = updater.visit(tree)

        new_source = CodeGenerator.generate(new_tree)
        assert "I0" in new_source
        # astunparse produces "class Calculator():" while ast.unparse produces "class Calculator:"
        assert "class Calculator" in new_source
        assert "def add" in new_source

    def test_module_without_all(self):
        """Test module without __all__ list."""
        table = GlobalSymbolTable()

        source = """
class Calculator:
    pass

def add(a, b):
    return a + b
"""
        tree = ast.parse(source)

        updater = AllListUpdater(table, "calculator")
        _new_tree = updater.visit(tree)  # noqa: F841

        assert updater.all_lists_updated == 0
        assert updater.names_updated == 0

    def test_update_all_list_from_file(self, tmp_path):
        """Test update_all_list_from_file convenience function."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        # Create temporary file
        test_file = tmp_path / "test_module.py"
        test_file.write_text('__all__ = ["Calculator"]\n')

        new_source, stats = update_all_list_from_file(test_file, table, "calculator")

        assert "I0" in new_source
        assert stats["all_lists_updated"] == 1
