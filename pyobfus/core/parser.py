"""
AST Parser for Python source code.

Handles parsing Python files into Abstract Syntax Trees for analysis
and transformation. Provides clear error messages when parsing fails.
"""

import ast
from pathlib import Path
from typing import Union

from pyobfus.exceptions import ParseError


class ASTParser:
    """
    Parser for converting Python source code to AST.

    Uses Python's built-in ast module to parse source code.
    Provides better error messages and handles different input types.
    """

    @staticmethod
    def parse_file(file_path: Union[str, Path]) -> ast.Module:
        """
        Parse a Python file into an AST.

        Args:
            file_path: Path to Python file

        Returns:
            ast.Module: Parsed AST module

        Raises:
            ParseError: If file cannot be parsed
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        try:
            source_code = file_path.read_text(encoding="utf-8")
            return ASTParser.parse_string(source_code, str(file_path))
        except ParseError:
            raise
        except Exception as e:
            raise ParseError(str(file_path), e) from e

    @staticmethod
    def parse_string(source_code: str, filename: str = "<string>") -> ast.Module:
        """
        Parse a Python source code string into an AST.

        Args:
            source_code: Python source code as string
            filename: Optional filename for error messages

        Returns:
            ast.Module: Parsed AST module

        Raises:
            ParseError: If source code cannot be parsed
        """
        try:
            # Parse with type comments for Python 3.8+ compatibility
            tree = ast.parse(source_code, filename=filename, type_comments=True)
            return tree
        except SyntaxError as e:
            raise ParseError(filename, e) from e
        except Exception as e:
            raise ParseError(filename, e) from e

    @staticmethod
    def validate_ast(tree: ast.Module) -> bool:
        """
        Validate that an AST is well-formed.

        Args:
            tree: AST module to validate

        Returns:
            bool: True if AST is valid

        Raises:
            ValueError: If AST is invalid
        """
        if not isinstance(tree, ast.Module):
            raise ValueError(f"Expected ast.Module, got {type(tree)}")

        try:
            # Try to compile the AST to verify it's valid
            compile(tree, "<ast>", "exec")
            return True
        except Exception as e:
            raise ValueError(f"Invalid AST: {e}") from e

    @staticmethod
    def get_source_segment(source_code: str, node: ast.AST, padded: bool = True) -> str:
        """
        Extract source code segment for an AST node.

        Args:
            source_code: Original source code
            node: AST node
            padded: Include padding whitespace

        Returns:
            str: Source code segment for the node
        """
        try:
            # Python 3.8+ has ast.get_source_segment
            return ast.get_source_segment(source_code, node, padded=padded) or ""
        except AttributeError:
            # Fallback for older Python versions
            return ""

    @staticmethod
    def count_lines(tree: ast.Module) -> int:
        """
        Count lines of code in an AST module.

        Args:
            tree: AST module

        Returns:
            int: Number of lines
        """
        max_lineno = 0
        for node in ast.walk(tree):
            # Use getattr with default to satisfy type checker
            lineno = getattr(node, "lineno", 0)
            if lineno:
                max_lineno = max(max_lineno, lineno)
            end_lineno = getattr(node, "end_lineno", None)
            if end_lineno:
                max_lineno = max(max_lineno, end_lineno)
        return max_lineno
