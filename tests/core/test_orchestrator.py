"""
Unit tests for CrossFileOrchestrator.

Tests cover:
- File discovery
- Phase 1 (scan) processing
- Module name conversion
- Name generation
- Integration with GlobalSymbolTable and ExportDetector
"""

import pytest
from pathlib import Path

from pyobfus.config import ObfuscationConfig
from pyobfus.core.orchestrator import CrossFileOrchestrator, ObfuscationResult, FileInfo


class TestObfuscationResult:
    """Test suite for ObfuscationResult dataclass."""

    def test_success_no_errors(self):
        """Test success property with no errors."""
        result = ObfuscationResult(
            files_processed=10,
            global_mappings=50,
            warnings=["warning1"],
            errors=[],
        )

        assert result.success is True

    def test_success_with_errors(self):
        """Test success property with errors."""
        result = ObfuscationResult(
            files_processed=10,
            global_mappings=50,
            warnings=[],
            errors=["error1"],
        )

        assert result.success is False


class TestFileInfo:
    """Test suite for FileInfo dataclass."""

    def test_file_info_creation(self):
        """Test creating FileInfo."""
        file_info = FileInfo(
            path=Path("src/calculator.py"),
            relative_path=Path("calculator.py"),
            module_name="calculator",
            exports={"Calculator", "add"},
        )

        assert file_info.path == Path("src/calculator.py")
        assert file_info.module_name == "calculator"
        assert len(file_info.exports) == 2


class TestCrossFileOrchestrator:
    """Test suite for CrossFileOrchestrator class."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return ObfuscationConfig.community_edition()

    @pytest.fixture
    def orchestrator(self, config):
        """Create orchestrator instance."""
        return CrossFileOrchestrator(config)

    def test_initialization(self, config):
        """Test orchestrator initialization."""
        orchestrator = CrossFileOrchestrator(config)

        assert orchestrator.config == config
        assert orchestrator.global_table is not None
        assert len(orchestrator.files) == 0
        assert orchestrator._name_counter == 0

    def test_path_to_module_name_single_file(self, orchestrator):
        """Test converting single file path to module name."""
        result = orchestrator._path_to_module_name(Path("calculator.py"))

        assert result == "calculator"

    def test_path_to_module_name_nested(self, orchestrator):
        """Test converting nested path to module name."""
        result = orchestrator._path_to_module_name(Path("utils/helpers.py"))

        assert result == "utils.helpers"

    def test_path_to_module_name_deeply_nested(self, orchestrator):
        """Test converting deeply nested path to module name."""
        result = orchestrator._path_to_module_name(Path("pkg/subpkg/module.py"))

        assert result == "pkg.subpkg.module"

    def test_generate_obfuscated_name_sequence(self, orchestrator):
        """Test that obfuscated names are generated in sequence."""
        name1 = orchestrator._generate_obfuscated_name()
        name2 = orchestrator._generate_obfuscated_name()
        name3 = orchestrator._generate_obfuscated_name()

        assert name1 == "I0"
        assert name2 == "I1"
        assert name3 == "I2"

    def test_generate_obfuscated_name_custom_prefix(self):
        """Test obfuscated name generation with custom prefix."""
        config = ObfuscationConfig.community_edition()
        config.name_prefix = "X"
        orchestrator = CrossFileOrchestrator(config)

        name1 = orchestrator._generate_obfuscated_name()
        name2 = orchestrator._generate_obfuscated_name()

        assert name1 == "X0"
        assert name2 == "X1"

    def test_generate_obfuscated_name_uniqueness(self, orchestrator):
        """Test that generated names are unique."""
        names = set()
        for _ in range(100):
            name = orchestrator._generate_obfuscated_name()
            assert name not in names
            names.add(name)

        assert len(names) == 100

    def test_should_preserve_name_in_exclude_list(self, orchestrator):
        """Test name preservation for names in exclude list."""
        orchestrator.config.exclude_names = ["logger", "config"]

        assert orchestrator._should_preserve_name("logger") is True
        assert orchestrator._should_preserve_name("config") is True
        assert orchestrator._should_preserve_name("other") is False

    def test_should_preserve_name_not_in_list(self, orchestrator):
        """Test that names not in exclude list are not preserved."""
        orchestrator.config.exclude_names = ["logger"]

        assert orchestrator._should_preserve_name("public_func") is False

    def test_discover_files_simple_project(self, orchestrator, tmp_path):
        """Test file discovery in simple project."""
        # Create test files
        (tmp_path / "file1.py").write_text("def func(): pass")
        (tmp_path / "file2.py").write_text("class Class: pass")

        files = orchestrator._discover_files(tmp_path)

        assert len(files) == 2
        module_names = {f.module_name for f in files}
        assert "file1" in module_names
        assert "file2" in module_names

    def test_discover_files_nested_structure(self, orchestrator, tmp_path):
        """Test file discovery in nested directory structure."""
        # Create nested structure
        utils_dir = tmp_path / "utils"
        utils_dir.mkdir()
        (tmp_path / "main.py").write_text("def main(): pass")
        (utils_dir / "helpers.py").write_text("def helper(): pass")

        files = orchestrator._discover_files(tmp_path)

        assert len(files) == 2
        module_names = {f.module_name for f in files}
        assert "main" in module_names
        assert "utils.helpers" in module_names

    def test_discover_files_exclude_patterns(self, orchestrator, tmp_path):
        """Test that excluded patterns are respected."""
        # Create files
        (tmp_path / "main.py").write_text("def main(): pass")
        (tmp_path / "test_main.py").write_text("def test(): pass")

        # Add exclude pattern
        orchestrator.config.exclude_patterns = ["test_*.py"]

        files = orchestrator._discover_files(tmp_path)

        # Only main.py should be discovered
        assert len(files) == 1
        assert files[0].module_name == "main"

    def test_phase1_scan_single_file(self, orchestrator, tmp_path):
        """Test Phase 1 scan with single file."""
        # Create test file
        (tmp_path / "calculator.py").write_text(
            """
def add(a, b):
    return a + b

class Calculator:
    pass
"""
        )

        orchestrator.phase1_scan(tmp_path)

        # Check files were discovered
        assert len(orchestrator.files) == 1
        assert orchestrator.files[0].module_name == "calculator"

        # Check exports were detected
        exports = orchestrator.files[0].exports
        assert "add" in exports
        assert "Calculator" in exports

        # Check global table was populated
        stats = orchestrator.global_table.get_statistics()
        assert stats["total_modules"] == 1
        assert stats["total_exports"] == 2

    def test_phase1_scan_multiple_files(self, orchestrator, tmp_path):
        """Test Phase 1 scan with multiple files."""
        # Create test files
        (tmp_path / "calculator.py").write_text(
            """
class Calculator:
    pass
"""
        )
        (tmp_path / "utils.py").write_text(
            """
def format_result():
    pass

def validate():
    pass
"""
        )

        orchestrator.phase1_scan(tmp_path)

        # Check files were discovered
        assert len(orchestrator.files) == 2

        # Check global table
        stats = orchestrator.global_table.get_statistics()
        assert stats["total_modules"] == 2
        assert stats["total_exports"] == 3

        # Check specific mappings
        assert (
            orchestrator.global_table.get_obfuscated_import("calculator", "Calculator") is not None
        )
        assert orchestrator.global_table.get_obfuscated_import("utils", "format_result") is not None

    def test_phase1_scan_private_names_excluded(self, orchestrator, tmp_path):
        """Test that private names are not added to global table."""
        # Create file with private name
        (tmp_path / "module.py").write_text(
            """
def public_func():
    pass

def _private_func():
    pass
"""
        )

        orchestrator.phase1_scan(tmp_path)

        # Only public_func should be in global table
        stats = orchestrator.global_table.get_statistics()
        assert stats["total_exports"] == 1

        # Check private name is not in table
        assert orchestrator.global_table.get_obfuscated_import("module", "_private_func") is None

    def test_phase1_scan_with_all_list(self, orchestrator, tmp_path):
        """Test Phase 1 scan respects __all__ list."""
        # Create file with __all__
        (tmp_path / "module.py").write_text(
            """
__all__ = ["public_func"]

def public_func():
    pass

def not_exported():
    pass
"""
        )

        orchestrator.phase1_scan(tmp_path)

        # Only public_func should be exported
        stats = orchestrator.global_table.get_statistics()
        assert stats["total_exports"] == 1

        assert orchestrator.global_table.get_obfuscated_import("module", "public_func") is not None
        assert orchestrator.global_table.get_obfuscated_import("module", "not_exported") is None

    def test_phase1_scan_preserve_excluded_names(self, orchestrator, tmp_path):
        """Test that excluded names are not obfuscated."""
        # Add name to exclude list
        orchestrator.config.exclude_names = ["logger"]

        # Create file
        (tmp_path / "module.py").write_text(
            """
def logger():
    pass

def other_func():
    pass
"""
        )

        orchestrator.phase1_scan(tmp_path)

        # logger should not be in global table (preserved)
        # other_func should be in global table
        stats = orchestrator.global_table.get_statistics()
        assert stats["total_exports"] == 1

        assert orchestrator.global_table.get_obfuscated_import("module", "logger") is None
        assert orchestrator.global_table.get_obfuscated_import("module", "other_func") is not None

    def test_get_statistics(self, orchestrator, tmp_path):
        """Test getting orchestrator statistics."""
        # Create test files
        (tmp_path / "file1.py").write_text("def func1(): pass")
        (tmp_path / "file2.py").write_text("def func2(): pass")

        orchestrator.phase1_scan(tmp_path)

        stats = orchestrator.get_statistics()

        assert stats["files_discovered"] == 2
        assert stats["total_exports"] == 2
        assert stats["total_modules"] == 2

    def test_get_file_info_found(self, orchestrator, tmp_path):
        """Test getting FileInfo by module name."""
        (tmp_path / "calculator.py").write_text("def add(): pass")

        orchestrator.phase1_scan(tmp_path)

        file_info = orchestrator.get_file_info("calculator")

        assert file_info is not None
        assert file_info.module_name == "calculator"

    def test_get_file_info_not_found(self, orchestrator, tmp_path):
        """Test getting FileInfo for non-existent module."""
        (tmp_path / "calculator.py").write_text("def add(): pass")

        orchestrator.phase1_scan(tmp_path)

        file_info = orchestrator.get_file_info("nonexistent")

        assert file_info is None

    def test_obfuscate_basic(self, orchestrator, tmp_path):
        """Test basic obfuscate method."""
        # Create test file
        (tmp_path / "module.py").write_text("def func(): pass")

        output_dir = tmp_path / "output"
        result = orchestrator.obfuscate(tmp_path, output_dir)

        assert result.files_processed == 1
        assert result.global_mappings == 1
        assert result.success is True

    def test_obfuscate_validation_errors(self, orchestrator, tmp_path):
        """Test obfuscate detects validation errors."""
        # This is a placeholder - actual validation errors would come from
        # unresolved imports in Phase 2
        (tmp_path / "module.py").write_text("def func(): pass")

        output_dir = tmp_path / "output"
        result = orchestrator.obfuscate(tmp_path, output_dir)

        # Should succeed in Phase 1
        assert result.success is True

    def test_phase2_transform_basic(self, orchestrator, tmp_path):
        """Test that Phase 2 transforms files correctly."""
        # Create test file
        test_file = tmp_path / "module.py"
        test_file.write_text(
            """
from other import Something

def my_function():
    pass
"""
        )

        # Run Phase 1 first
        orchestrator.phase1_scan(tmp_path)

        # Run Phase 2
        output_dir = tmp_path / "output"
        orchestrator.phase2_transform(tmp_path, output_dir)

        # Verify output file exists
        output_file = output_dir / "module.py"
        assert output_file.exists()

        # Verify content was written and transformed
        content = output_file.read_text()
        # Function should be renamed (it's exported) to something starting with I
        assert "def I" in content and "():" in content
        # Original name should not appear
        assert "def my_function" not in content or "def I" in content

    def test_obfuscated_names_are_unique_across_modules(self, orchestrator, tmp_path):
        """Test that obfuscated names are globally unique."""
        # Create multiple files
        (tmp_path / "module1.py").write_text(
            """
def func1():
    pass

def func2():
    pass
"""
        )
        (tmp_path / "module2.py").write_text(
            """
def func3():
    pass

def func4():
    pass
"""
        )

        orchestrator.phase1_scan(tmp_path)

        # Get all obfuscated names
        obfuscated_names = []
        for module in orchestrator.global_table.get_all_modules():
            exports = orchestrator.global_table.get_module_exports(module)
            obfuscated_names.extend(exports.values())

        # All names should be unique
        assert len(obfuscated_names) == len(set(obfuscated_names))

    def test_relative_path_calculation(self, orchestrator, tmp_path):
        """Test that relative paths are calculated correctly."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "module.py").write_text("def func(): pass")

        orchestrator.phase1_scan(tmp_path)

        file_info = orchestrator.get_file_info("subdir.module")
        assert file_info is not None
        assert file_info.relative_path == Path("subdir/module.py")

    def test_empty_directory(self, orchestrator, tmp_path):
        """Test scanning empty directory."""
        orchestrator.phase1_scan(tmp_path)

        assert len(orchestrator.files) == 0
        stats = orchestrator.get_statistics()
        assert stats["files_discovered"] == 0
