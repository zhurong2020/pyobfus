"""
Code generator for converting AST back to Python source code.

Uses ast.unparse (Python 3.9+) or fallback for older versions.
"""

import ast
import sys
from pathlib import Path
from typing import Union, cast

from pyobfus.exceptions import GenerationError


class CodeGenerator:
    """
    Generates Python source code from an AST.

    Handles different Python versions and provides
    clean, readable output.
    """

    @staticmethod
    def generate(tree: ast.Module) -> str:
        """
        Generate Python source code from an AST.

        Args:
            tree: AST module to convert

        Returns:
            str: Generated Python source code

        Raises:
            GenerationError: If code generation fails
        """
        try:
            # Python 3.9+ has ast.unparse
            if sys.version_info >= (3, 9):
                return ast.unparse(tree)
            else:
                # Fallback for Python 3.8
                return CodeGenerator._unparse_fallback(tree)
        except Exception as e:
            raise GenerationError(f"Failed to generate code: {e}") from e

    @staticmethod
    def _unparse_fallback(tree: ast.Module) -> str:
        """
        Fallback unparser for Python 3.8.

        Uses compile + disassembly approach.
        This is a simplified version - ast.unparse is preferred.

        Args:
            tree: AST module

        Returns:
            str: Source code
        """
        # For Python 3.8, we recommend using astunparse package
        # But to keep dependencies minimal, we'll try a basic approach
        try:
            import astunparse  # type: ignore

            return cast(str, astunparse.unparse(tree))
        except ImportError:
            # If astunparse not available, raise error
            # This is a limitation - we can't perfectly reconstruct source
            # Recommend upgrading to Python 3.9+ or installing astunparse
            raise GenerationError(
                "Python 3.8 requires 'astunparse' package for code generation.\n"
                "Install with: pip install astunparse\n"
                "Or upgrade to Python 3.9+ for built-in support."
            )

    @staticmethod
    def generate_to_file(tree: ast.Module, output_path: Union[str, Path]) -> None:
        """
        Generate Python code and write to a file.

        Args:
            tree: AST module
            output_path: Output file path

        Raises:
            GenerationError: If generation or writing fails
        """
        output_path = Path(output_path)

        # Generate code
        source_code = CodeGenerator.generate(tree)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write to file
        try:
            output_path.write_text(source_code, encoding="utf-8")
        except Exception as e:
            raise GenerationError(f"Failed to write to {output_path}: {e}") from e

    @staticmethod
    def format_code(source_code: str, line_length: int = 100) -> str:
        """
        Format Python source code.

        Args:
            source_code: Source code to format
            line_length: Maximum line length

        Returns:
            str: Formatted source code
        """
        # Try to use black for formatting if available
        try:
            import black

            mode = black.Mode(line_length=line_length)
            return black.format_str(source_code, mode=mode)
        except ImportError:
            # If black not available, return as-is
            return source_code

    @staticmethod
    def add_header_comment(source_code: str, original_file: str = "") -> str:
        """
        Add a header comment to obfuscated code.

        Args:
            source_code: Generated source code
            original_file: Original filename (optional)

        Returns:
            str: Source code with header
        """
        header_lines = [
            "# Obfuscated with pyobfus",
            "# https://github.com/zhurong2020/pyobfus",
        ]

        if original_file:
            header_lines.append(f"# Original: {original_file}")

        header_lines.append("# DO NOT EDIT - Generated code")
        header_lines.append("")

        header = "\n".join(header_lines)
        return f"{header}\n{source_code}"
