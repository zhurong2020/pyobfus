"""
Unit tests for ImportRewriter.

Tests cover:
- Simple import rewriting
- Multiple imports
- Imports with aliases
- Relative imports
- Wildcard imports
- Stdlib/external imports (unchanged)
- Statistics tracking
- Edge cases
"""

import ast
import pytest
from pathlib import Path

from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.transformers.import_rewriter import (
    ImportRewriter,
    rewrite_imports,
    rewrite_imports_from_file,
)


class TestImportRewriter:
    """Test suite for ImportRewriter class."""

    def test_initialization(self):
        """Test ImportRewriter initialization."""
        table = GlobalSymbolTable()
        rewriter = ImportRewriter(table, "main")

        assert rewriter.global_table is table
        assert rewriter.current_module == "main"
        assert rewriter.imports_rewritten == 0
        assert rewriter.imports_unchanged == 0
        assert len(rewriter.imports_not_found) == 0

    def test_simple_import_rewrite(self):
        """Test rewriting simple import statement."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = "from calculator import Calculator"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        # Unparse to check result
        new_source = ast.unparse(new_tree)
        assert "from calculator import I0" in new_source
        assert rewriter.imports_rewritten == 1
        assert rewriter.imports_unchanged == 0

    def test_multiple_imports_same_module(self):
        """Test rewriting multiple imports from same module."""
        table = GlobalSymbolTable()
        table.register_export("utils", "format_result", "I0")
        table.register_export("utils", "validate_number", "I1")
        table.register_export("utils", "calculate_percentage", "I2")

        source = "from utils import format_result, validate_number, calculate_percentage"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from utils import I0, I1, I2" in new_source
        assert rewriter.imports_rewritten == 3

    def test_import_with_alias(self):
        """Test that alias is preserved when rewriting."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = "from calculator import Calculator as Calc"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from calculator import I0 as Calc" in new_source
        assert rewriter.imports_rewritten == 1

    def test_multiple_imports_with_aliases(self):
        """Test multiple imports with aliases."""
        table = GlobalSymbolTable()
        table.register_export("utils", "format_result", "I0")
        table.register_export("utils", "validate_number", "I1")

        source = "from utils import format_result as fmt, validate_number as validate"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "I0 as fmt" in new_source
        assert "I1 as validate" in new_source

    def test_wildcard_import_preserved(self):
        """Test that wildcard imports are preserved unchanged."""
        table = GlobalSymbolTable()
        table.register_export("utils", "format_result", "I0")

        source = "from utils import *"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from utils import *" in new_source
        assert rewriter.imports_rewritten == 0
        assert rewriter.imports_unchanged == 1

    def test_stdlib_import_unchanged(self):
        """Test that stdlib imports are left unchanged."""
        table = GlobalSymbolTable()

        source = "from os import path"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from os import path" in new_source
        assert rewriter.imports_unchanged == 1
        assert "os.path" in rewriter.imports_not_found

    def test_import_statement_unchanged(self):
        """Test that import statements (not from...import) are unchanged."""
        table = GlobalSymbolTable()

        source = "import os\nimport sys"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "import os" in new_source
        assert "import sys" in new_source
        assert rewriter.imports_unchanged == 2

    def test_mixed_found_and_not_found(self):
        """Test module with some imports found and some not found."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = "from calculator import Calculator, NonExistent"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "I0" in new_source
        assert "NonExistent" in new_source
        assert rewriter.imports_rewritten == 1
        assert rewriter.imports_unchanged == 1
        assert "calculator.NonExistent" in rewriter.imports_not_found

    def test_relative_import_level_1(self):
        """Test relative import from current package (from .module import)."""
        table = GlobalSymbolTable()
        table.register_export("pkg.utils", "helper", "I0")

        source = "from .utils import helper"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "pkg.main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from .utils import I0" in new_source
        assert rewriter.imports_rewritten == 1

    def test_relative_import_level_2(self):
        """Test relative import from parent package (from ..module import)."""
        table = GlobalSymbolTable()
        table.register_export("pkg.utils", "helper", "I0")

        source = "from ..utils import helper"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "pkg.subpkg.main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from ..utils import I0" in new_source
        assert rewriter.imports_rewritten == 1

    def test_relative_import_current_package(self):
        """Test relative import from current package (from . import)."""
        table = GlobalSymbolTable()
        table.register_export("pkg.subpkg", "helper", "I0")

        source = "from . import helper"
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "pkg.subpkg.main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from . import I0" in new_source
        assert rewriter.imports_rewritten == 1

    def test_relative_import_too_many_levels(self):
        """Test relative import with too many levels (can't resolve)."""
        table = GlobalSymbolTable()

        source = "from ...utils import helper"
        tree = ast.parse(source)

        # Module has only 2 parts, can't go up 3 levels
        rewriter = ImportRewriter(table, "pkg.main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from ...utils import helper" in new_source
        assert rewriter.imports_unchanged == 1

    def test_multiple_import_statements(self):
        """Test file with multiple import statements."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")
        table.register_export("utils", "format_result", "I1")

        source = """
from calculator import Calculator
from utils import format_result
import os
"""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from calculator import I0" in new_source
        assert "from utils import I1" in new_source
        assert "import os" in new_source
        assert rewriter.imports_rewritten == 2
        assert rewriter.imports_unchanged == 1

    def test_import_in_class(self):
        """Test that imports inside classes are also rewritten."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
class MyClass:
    from calculator import Calculator
"""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from calculator import I0" in new_source

    def test_import_in_function(self):
        """Test that imports inside functions are also rewritten."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
def my_function():
    from calculator import Calculator
    return Calculator()
"""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from calculator import I0" in new_source

    def test_get_statistics(self):
        """Test get_statistics method."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
from calculator import Calculator
from utils import NotFound
import os
"""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        rewriter.visit(tree)

        stats = rewriter.get_statistics()
        assert stats["imports_rewritten"] == 1
        assert stats["imports_unchanged"] == 2
        assert "utils.NotFound" in stats["imports_not_found"]

    def test_repr(self):
        """Test string representation."""
        table = GlobalSymbolTable()
        rewriter = ImportRewriter(table, "main")

        repr_str = repr(rewriter)
        assert "ImportRewriter" in repr_str
        assert "module=main" in repr_str
        assert "rewritten=0" in repr_str

    def test_rewrite_imports_convenience_function(self):
        """Test rewrite_imports convenience function."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = "from calculator import Calculator"
        new_source, stats = rewrite_imports(source, table, "main")

        assert "from calculator import I0" in new_source
        assert stats["imports_rewritten"] == 1

    def test_complex_module_structure(self):
        """Test rewriting in complex module structure."""
        table = GlobalSymbolTable()
        table.register_export("pkg.subpkg.calculator", "Calculator", "I0")
        table.register_export("pkg.utils", "helper", "I1")

        source = """
from pkg.subpkg.calculator import Calculator
from pkg.utils import helper
"""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "pkg.main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "from pkg.subpkg.calculator import I0" in new_source
        assert "from pkg.utils import I1" in new_source

    def test_preserve_code_structure(self):
        """Test that non-import code is preserved."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        source = """
from calculator import Calculator

class Main:
    def __init__(self):
        self.calc = Calculator()

    def run(self):
        return self.calc.add(1, 2)
"""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        assert "class Main:" in new_source
        assert "def __init__" in new_source
        assert "def run" in new_source
        assert "from calculator import I0" in new_source

    def test_empty_module(self):
        """Test rewriting empty module."""
        table = GlobalSymbolTable()
        source = ""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        assert rewriter.imports_rewritten == 0
        assert rewriter.imports_unchanged == 0

    def test_module_with_no_imports(self):
        """Test module with no imports."""
        table = GlobalSymbolTable()
        source = """
class MyClass:
    pass

def my_function():
    pass
"""
        tree = ast.parse(source)

        rewriter = ImportRewriter(table, "main")
        new_tree = rewriter.visit(tree)

        assert rewriter.imports_rewritten == 0
        assert rewriter.imports_unchanged == 0

    def test_rewrite_imports_from_file(self, tmp_path):
        """Test rewrite_imports_from_file convenience function."""
        table = GlobalSymbolTable()
        table.register_export("calculator", "Calculator", "I0")

        # Create temporary file
        test_file = tmp_path / "test_module.py"
        test_file.write_text("from calculator import Calculator\n")

        new_source, stats = rewrite_imports_from_file(test_file, table, "main")

        assert "from calculator import I0" in new_source
        assert stats["imports_rewritten"] == 1

    def test_relative_import_without_current_module(self):
        """Test that relative imports are left unchanged when current_module is not set."""
        table = GlobalSymbolTable()
        table.register_export("utils", "helper", "I0")

        source = "from .utils import helper"
        tree = ast.parse(source)

        # No current_module set (empty string)
        rewriter = ImportRewriter(table, "")
        new_tree = rewriter.visit(tree)

        new_source = ast.unparse(new_tree)
        # Should be unchanged since we can't resolve relative import
        assert "from .utils import helper" in new_source
        assert rewriter.imports_unchanged == 1
