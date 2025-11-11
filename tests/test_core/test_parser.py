"""
Unit tests for AST parser.
"""

import ast
from pathlib import Path

import pytest

from pyobfus.core.parser import ASTParser
from pyobfus.exceptions import ParseError


def test_parse_string_valid():
    """Test parsing valid Python code."""
    code = "x = 1 + 2"
    tree = ASTParser.parse_string(code)

    assert isinstance(tree, ast.Module)
    assert len(tree.body) == 1


def test_parse_string_invalid():
    """Test parsing invalid Python code."""
    code = "def invalid syntax here"

    with pytest.raises(ParseError):
        ASTParser.parse_string(code)


def test_parse_file_not_found():
    """Test parsing non-existent file."""
    with pytest.raises(FileNotFoundError):
        ASTParser.parse_file("nonexistent_file.py")


def test_parse_file_valid(tmp_path):
    """Test parsing a valid Python file."""
    # Create temp file
    test_file = tmp_path / "test.py"
    test_file.write_text("x = 42\nprint(x)")

    tree = ASTParser.parse_file(test_file)

    assert isinstance(tree, ast.Module)
    assert len(tree.body) == 2


def test_validate_ast():
    """Test AST validation."""
    code = "x = 1"
    tree = ASTParser.parse_string(code)

    # Should validate successfully
    assert ASTParser.validate_ast(tree) is True


def test_count_lines():
    """Test line counting."""
    code = """
x = 1
y = 2
z = x + y
print(z)
"""
    tree = ASTParser.parse_string(code)
    line_count = ASTParser.count_lines(tree)

    assert line_count >= 4  # At least 4 lines of code
