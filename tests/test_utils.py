"""
Unit tests for utility functions.
"""

from pathlib import Path

from pyobfus.utils import should_exclude_file, filter_python_files, count_total_lines


def test_should_exclude_file_basic():
    """Test basic file exclusion with simple patterns."""
    # Test excluding test files
    assert should_exclude_file(Path("test_foo.py"), ["test_*.py"]) is True
    assert should_exclude_file(Path("foo.py"), ["test_*.py"]) is False

    # Test excluding specific files
    assert should_exclude_file(Path("setup.py"), ["setup.py"]) is True
    assert should_exclude_file(Path("main.py"), ["setup.py"]) is False


def test_should_exclude_file_directory_patterns():
    """Test exclusion with directory patterns."""
    # Test **/tests/** pattern
    assert should_exclude_file(Path("src/tests/test_foo.py"), ["**/tests/**"]) is True
    assert should_exclude_file(Path("tests/test_foo.py"), ["**/tests/**"]) is True
    assert should_exclude_file(Path("src/main.py"), ["**/tests/**"]) is False

    # Test **/__init__.py pattern
    assert should_exclude_file(Path("src/__init__.py"), ["**/__init__.py"]) is True
    assert should_exclude_file(Path("src/tests/__init__.py"), ["**/__init__.py"]) is True
    assert should_exclude_file(Path("src/main.py"), ["**/__init__.py"]) is False


def test_should_exclude_file_multiple_patterns():
    """Test exclusion with multiple patterns."""
    patterns = ["test_*.py", "**/tests/**", "__init__.py"]

    assert should_exclude_file(Path("test_foo.py"), patterns) is True
    assert should_exclude_file(Path("src/tests/foo.py"), patterns) is True
    assert should_exclude_file(Path("__init__.py"), patterns) is True
    assert should_exclude_file(Path("main.py"), patterns) is False


def test_should_exclude_file_with_base_path():
    """Test exclusion with base path for relative matching."""
    base = Path("/project")
    file_path = Path("/project/src/tests/test_foo.py")

    assert should_exclude_file(file_path, ["**/tests/**"], base) is True
    assert should_exclude_file(file_path, ["test_*.py"], base) is True


def test_should_exclude_file_no_patterns():
    """Test that no patterns means no exclusion."""
    assert should_exclude_file(Path("any_file.py"), []) is False
    assert should_exclude_file(Path("test_file.py"), None) is False


def test_filter_python_files(tmp_path):
    """Test filtering Python files with exclusion patterns."""
    # Create test directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('main')")
    (tmp_path / "src" / "utils.py").write_text("print('utils')")

    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_main.py").write_text("# test")

    (tmp_path / "__init__.py").write_text("# init")

    # Filter without exclusions
    all_files = filter_python_files(tmp_path, [])
    assert len(all_files) == 4  # All .py files

    # Filter excluding test files
    filtered = filter_python_files(tmp_path, ["test_*.py"])
    file_names = [f.name for f in filtered]
    assert "test_main.py" not in file_names
    assert "main.py" in file_names

    # Filter excluding tests directory and __init__.py
    filtered = filter_python_files(tmp_path, ["**/tests/**", "__init__.py"])
    file_names = [f.name for f in filtered]
    assert "test_main.py" not in file_names
    assert "__init__.py" not in file_names
    assert "main.py" in file_names
    assert "utils.py" in file_names


def test_filter_python_files_empty_directory(tmp_path):
    """Test filtering in empty directory."""
    filtered = filter_python_files(tmp_path, [])
    assert len(filtered) == 0


def test_count_total_lines(tmp_path):
    """Test counting total lines across files."""
    # Create test files
    file1 = tmp_path / "file1.py"
    file1.write_text("line1\nline2\nline3\n")  # 3 lines

    file2 = tmp_path / "file2.py"
    file2.write_text("line1\nline2\n")  # 2 lines

    files = [file1, file2]
    total = count_total_lines(files)
    assert total == 5


def test_count_total_lines_empty_list():
    """Test counting lines with empty file list."""
    assert count_total_lines([]) == 0


def test_count_total_lines_nonexistent_file(tmp_path):
    """Test counting lines with non-existent file (should skip)."""
    nonexistent = tmp_path / "nonexistent.py"
    total = count_total_lines([nonexistent])
    assert total == 0


def test_exclude_patterns_case_behavior():
    """Test pattern matching case behavior (OS-dependent)."""
    import sys

    # fnmatch behaves differently on Windows (case-insensitive) vs Unix (case-sensitive)
    result = should_exclude_file(Path("Test_foo.py"), ["test_*.py"])

    if sys.platform == "win32":
        # Windows file systems are case-insensitive
        assert result is True
    else:
        # Unix file systems are case-sensitive
        assert result is False

    # Exact case should always match
    assert should_exclude_file(Path("test_foo.py"), ["test_*.py"]) is True
