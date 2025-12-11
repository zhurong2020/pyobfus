"""
Code generator for converting AST back to Python source code.

Uses ast.unparse (Python 3.9+) or fallback for older versions.
Includes validation and fixing of f-string quote conflicts.
"""

import ast
import re
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
                source_code = ast.unparse(tree)
            else:
                # Fallback for Python 3.8
                source_code = CodeGenerator._unparse_fallback(tree)

            # Validate and fix any f-string quote conflicts
            source_code = CodeGenerator._fix_fstring_quotes(source_code)

            return source_code
        except Exception as e:
            raise GenerationError(f"Failed to generate code: {e}") from e

    @staticmethod
    def _fix_fstring_quotes(source_code: str) -> str:
        """
        Fix f-string quote conflicts in generated code.

        When an f-string uses single quotes and contains a subscript with single quotes,
        this causes a syntax error. This method detects and fixes such conflicts.

        Example:
            Invalid: f'Value: {data['key']}'
            Fixed:   f'Value: {data["key"]}'

        Args:
            source_code: Generated source code

        Returns:
            str: Source code with fixed f-string quotes
        """
        # First, check if the code compiles without issues
        try:
            compile(source_code, "<string>", "exec")
            return source_code  # No issues, return as-is
        except SyntaxError:
            pass  # Continue to fix

        # Use a more robust approach: find f-strings and fix quote conflicts
        # within each one individually
        fixed_code = CodeGenerator._fix_single_quote_fstrings(source_code)
        fixed_code = CodeGenerator._fix_double_quote_fstrings(fixed_code)

        # Verify the fix worked
        try:
            compile(fixed_code, "<string>", "exec")
            return fixed_code
        except SyntaxError:
            # If still failing, return original code and let the error propagate
            # during actual execution
            return source_code

    @staticmethod
    def _fix_single_quote_fstrings(source_code: str) -> str:
        """
        Fix f-strings that use single quotes but have single-quoted subscripts inside.

        Example: f'Value: {d['key']}' -> f'Value: {d["key"]}'
        """
        result = []
        i = 0
        n = len(source_code)

        while i < n:
            # Look for f' pattern
            if i < n - 1 and source_code[i] == "f" and source_code[i + 1] == "'":
                # Found start of single-quoted f-string
                i += 2  # Skip f'

                # Track brace depth to find expressions
                content = []
                while i < n:
                    char = source_code[i]

                    if char == "'" and (i == 0 or source_code[i - 1] != "\\"):
                        # End of f-string
                        break
                    elif char == "{":
                        # Start of expression - need to handle subscripts
                        brace_depth = 1
                        i += 1
                        expr_chars = ["{"]

                        while i < n and brace_depth > 0:
                            c = source_code[i]
                            if c == "{":
                                brace_depth += 1
                            elif c == "}":
                                brace_depth -= 1
                            expr_chars.append(c)
                            i += 1

                        # Fix single quotes to double quotes within subscripts in expr
                        expr = "".join(expr_chars)
                        fixed_expr = re.sub(r"\['([^']*?)'\]", r'["\1"]', expr)
                        content.append(fixed_expr)
                        continue
                    else:
                        content.append(char)
                    i += 1

                # Reconstruct the f-string
                result.append("f'")
                result.append("".join(content))
                result.append("'")
                i += 1  # Skip closing quote
            else:
                result.append(source_code[i])
                i += 1

        return "".join(result)

    @staticmethod
    def _fix_double_quote_fstrings(source_code: str) -> str:
        """
        Fix f-strings that use double quotes but have double-quoted subscripts inside.

        Example: f"Value: {d["key"]}" -> f"Value: {d['key']}"
        """
        result = []
        i = 0
        n = len(source_code)

        while i < n:
            # Look for f" pattern
            if i < n - 1 and source_code[i] == "f" and source_code[i + 1] == '"':
                # Found start of double-quoted f-string
                i += 2  # Skip f"

                # Track brace depth to find expressions
                content = []
                while i < n:
                    char = source_code[i]

                    if char == '"' and (i == 0 or source_code[i - 1] != "\\"):
                        # End of f-string
                        break
                    elif char == "{":
                        # Start of expression - need to handle subscripts
                        brace_depth = 1
                        i += 1
                        expr_chars = ["{"]

                        while i < n and brace_depth > 0:
                            c = source_code[i]
                            if c == "{":
                                brace_depth += 1
                            elif c == "}":
                                brace_depth -= 1
                            expr_chars.append(c)
                            i += 1

                        # Fix double quotes to single quotes within subscripts in expr
                        expr = "".join(expr_chars)
                        fixed_expr = re.sub(r'\["([^"]*?)"\]', r"['\1']", expr)
                        content.append(fixed_expr)
                        continue
                    else:
                        content.append(char)
                    i += 1

                # Reconstruct the f-string
                result.append('f"')
                result.append("".join(content))
                result.append('"')
                i += 1  # Skip closing quote
            else:
                result.append(source_code[i])
                i += 1

        return "".join(result)

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
