"""
Unit tests for GlobalSymbolTable.

Tests cover:
- Name registration
- Collision detection
- Import resolution
- Statistics and validation
- Edge cases
"""

import pytest
from pathlib import Path

from pyobfus.core.global_table import GlobalSymbolTable, ImportInfo


class TestGlobalSymbolTable:
    """Test suite for GlobalSymbolTable class."""

    def test_initialization(self):
        """Test that GlobalSymbolTable initializes with empty state."""
        table = GlobalSymbolTable()

        assert len(table.module_exports) == 0
        assert len(table.import_statements) == 0
        assert len(table.used_names) == 0
        assert table.get_statistics()["total_modules"] == 0
        assert table.get_statistics()["total_exports"] == 0

    def test_register_export_single(self):
        """Test registering a single export."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")

        assert "calculator" in table.module_exports
        assert table.module_exports["calculator"]["Calculator"] == "I0"
        assert "I0" in table.used_names

    def test_register_export_multiple_same_module(self):
        """Test registering multiple exports from same module."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        table.register_export("calculator", "add", "I1")
        table.register_export("calculator", "subtract", "I2")

        assert len(table.module_exports["calculator"]) == 3
        assert table.module_exports["calculator"]["Calculator"] == "I0"
        assert table.module_exports["calculator"]["add"] == "I1"
        assert table.module_exports["calculator"]["subtract"] == "I2"
        assert len(table.used_names) == 3

    def test_register_export_multiple_modules(self):
        """Test registering exports from multiple modules."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        table.register_export("utils", "format_result", "I1")
        table.register_export("utils", "validate_number", "I2")

        assert len(table.module_exports) == 2
        assert "calculator" in table.module_exports
        assert "utils" in table.module_exports
        assert table.get_statistics()["total_modules"] == 2
        assert table.get_statistics()["total_exports"] == 3

    def test_name_collision_detection(self):
        """Test that name collisions are detected."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")

        # Try to register same obfuscated name for different symbol
        with pytest.raises(ValueError, match="Name collision"):
            table.register_export("utils", "Utils", "I0")

    def test_name_collision_same_symbol_allowed(self):
        """Test that registering same symbol twice is allowed (idempotent)."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        # Register same mapping again - should not raise
        table.register_export("calculator", "Calculator", "I0")

        assert len(table.used_names) == 1

    def test_get_obfuscated_import_found(self):
        """Test getting obfuscated name for existing import."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        table.register_export("calculator", "add", "I1")

        assert table.get_obfuscated_import("calculator", "Calculator") == "I0"
        assert table.get_obfuscated_import("calculator", "add") == "I1"

    def test_get_obfuscated_import_not_found(self):
        """Test getting obfuscated name for non-existent import."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")

        # Module exists but name doesn't
        assert table.get_obfuscated_import("calculator", "NonExistent") is None

        # Module doesn't exist
        assert table.get_obfuscated_import("nonexistent", "Name") is None

    def test_resolve_import_alias(self):
        """Test resolve_import method (alias for get_obfuscated_import)."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")

        assert table.resolve_import("calculator", "Calculator") == "I0"

    def test_register_import_statement(self):
        """Test registering import statements."""
        table = GlobalSymbolTable()

        file_path = Path("main.py")
        import_info = ImportInfo(
            from_module="calculator",
            import_name="Calculator",
            alias=None,
            is_relative=False,
            level=0,
        )

        table.register_import(file_path, import_info)

        assert file_path in table.import_statements
        assert len(table.import_statements[file_path]) == 1
        assert table.import_statements[file_path][0].from_module == "calculator"
        assert table.import_statements[file_path][0].import_name == "Calculator"

    def test_register_multiple_imports_same_file(self):
        """Test registering multiple imports from same file."""
        table = GlobalSymbolTable()

        file_path = Path("main.py")

        import1 = ImportInfo("calculator", "Calculator")
        import2 = ImportInfo("utils", "format_result")

        table.register_import(file_path, import1)
        table.register_import(file_path, import2)

        assert len(table.import_statements[file_path]) == 2

    def test_get_module_exports(self):
        """Test getting all exports from a module."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        table.register_export("calculator", "add", "I1")

        exports = table.get_module_exports("calculator")

        assert len(exports) == 2
        assert exports["Calculator"] == "I0"
        assert exports["add"] == "I1"

        # Should return copy, not reference
        exports["new_key"] = "value"
        assert "new_key" not in table.module_exports["calculator"]

    def test_get_module_exports_nonexistent(self):
        """Test getting exports from non-existent module."""
        table = GlobalSymbolTable()

        exports = table.get_module_exports("nonexistent")

        assert len(exports) == 0
        assert isinstance(exports, dict)

    def test_get_all_modules(self):
        """Test getting list of all modules."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        table.register_export("utils", "format_result", "I1")
        table.register_export("helpers", "helper", "I2")

        modules = table.get_all_modules()

        assert len(modules) == 3
        assert "calculator" in modules
        assert "utils" in modules
        assert "helpers" in modules

    def test_is_name_used(self):
        """Test checking if obfuscated name is used."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")

        assert table.is_name_used("I0") is True
        assert table.is_name_used("I1") is False

    def test_get_reverse_mapping(self):
        """Test getting reverse mapping (obfuscated -> original)."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        table.register_export("utils", "format_result", "I1")

        assert table.get_reverse_mapping("I0") == ("calculator", "Calculator")
        assert table.get_reverse_mapping("I1") == ("utils", "format_result")
        assert table.get_reverse_mapping("I999") is None

    def test_get_statistics(self):
        """Test getting statistics."""
        table = GlobalSymbolTable()

        # Empty table
        stats = table.get_statistics()
        assert stats["total_modules"] == 0
        assert stats["total_exports"] == 0
        assert stats["total_imports"] == 0

        # Add some exports
        table.register_export("calculator", "Calculator", "I0")
        table.register_export("calculator", "add", "I1")
        table.register_export("utils", "format_result", "I2")

        # Add some imports
        table.register_import(Path("main.py"), ImportInfo("calculator", "Calculator"))

        stats = table.get_statistics()
        assert stats["total_modules"] == 2
        assert stats["total_exports"] == 3
        assert stats["total_imports"] == 1

    def test_validate_all_imports_resolved(self):
        """Test validation with all imports resolved."""
        table = GlobalSymbolTable()

        # Register exports
        table.register_export("calculator", "Calculator", "I0")
        table.register_export("utils", "format_result", "I1")

        # Register imports (all should resolve)
        table.register_import(Path("main.py"), ImportInfo("calculator", "Calculator"))
        table.register_import(Path("main.py"), ImportInfo("utils", "format_result"))

        is_valid, errors = table.validate()

        assert is_valid is True
        assert len(errors) == 0

    def test_validate_unresolved_import(self):
        """Test validation with unresolved import."""
        table = GlobalSymbolTable()

        # Register exports
        table.register_export("calculator", "Calculator", "I0")

        # Register import that cannot be resolved
        table.register_import(
            Path("main.py"), ImportInfo("calculator", "NonExistent")
        )

        is_valid, errors = table.validate()

        assert is_valid is False
        assert len(errors) == 1
        assert "Cannot resolve import 'NonExistent'" in errors[0]

    def test_validate_stdlib_imports_ignored(self):
        """Test that standard library imports are ignored during validation."""
        table = GlobalSymbolTable()

        # Register import from stdlib (not in our table)
        table.register_import(Path("main.py"), ImportInfo("os", "path"))

        is_valid, errors = table.validate()

        # Should be valid (stdlib imports ignored)
        assert is_valid is True
        assert len(errors) == 0

    def test_validate_wildcard_imports(self):
        """Test that wildcard imports are handled in validation."""
        table = GlobalSymbolTable()

        # Register exports
        table.register_export("calculator", "Calculator", "I0")

        # Register wildcard import
        table.register_import(Path("main.py"), ImportInfo("calculator", "*"))

        is_valid, errors = table.validate()

        # Should be valid (wildcards not validated)
        assert is_valid is True
        assert len(errors) == 0

    def test_repr(self):
        """Test string representation."""
        table = GlobalSymbolTable()

        table.register_export("calculator", "Calculator", "I0")
        table.register_export("utils", "format_result", "I1")

        repr_str = repr(table)

        assert "GlobalSymbolTable" in repr_str
        assert "modules=2" in repr_str
        assert "exports=2" in repr_str

    def test_import_info_dataclass(self):
        """Test ImportInfo dataclass."""
        import_info = ImportInfo(
            from_module="calculator",
            import_name="Calculator",
            alias="Calc",
            is_relative=True,
            level=2,
        )

        assert import_info.from_module == "calculator"
        assert import_info.import_name == "Calculator"
        assert import_info.alias == "Calc"
        assert import_info.is_relative is True
        assert import_info.level == 2

    def test_import_info_defaults(self):
        """Test ImportInfo with default values."""
        import_info = ImportInfo(from_module="calculator", import_name="Calculator")

        assert import_info.alias is None
        assert import_info.is_relative is False
        assert import_info.level == 0
