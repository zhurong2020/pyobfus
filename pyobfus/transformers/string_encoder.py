"""
Base64 String Encoding Transformer (Community Edition)

Encodes string literals in Python code using Base64 and injects
runtime decoding functions. Provides basic string obfuscation.

Example:
    Original: print("Hello, World!")
    Encoded: print(_decode_str("SGVsbG8sIFdvcmxkIQ=="))

Note: F-strings are NOT encoded due to Python AST limitations.
      Docstrings are preserved to maintain compatibility.
"""

import ast
import base64
from typing import Dict, Optional, Set, cast

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.transformer import BaseTransformer


class StringEncoder(BaseTransformer):
    """
    Encodes string literals using Base64 encoding.

    Features:
    - Base64 encoding for simple obfuscation
    - Runtime decoding function injection
    - Skips f-strings (Python AST limitation)
    - Preserves docstrings for documentation
    - No external dependencies required
    """

    def __init__(self, config: ObfuscationConfig, analyzer: Optional[SymbolAnalyzer] = None):
        """
        Initialize string encoder.

        Args:
            config: Obfuscation configuration
            analyzer: Symbol analyzer (optional)
        """
        super().__init__(config, analyzer)
        self.encoded_strings: Dict[str, str] = {}
        self.decode_function_name = "_decode_str"
        self._in_fstring = False  # Track if we're inside an f-string
        self._skipped_fstring_count = 0
        self._docstring_nodes: Set[int] = set()  # Track docstring node IDs

    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform AST by encoding all string literals.

        Args:
            tree: Input AST

        Returns:
            ast.Module: Transformed AST with encoded strings
        """
        # Skip if string encoding is disabled
        if not self.config.string_encoding:
            return tree

        # Step 1: Identify docstrings (to preserve them)
        self._identify_docstrings(tree)

        # Step 2: Visit and encode strings
        transformed = cast(ast.Module, self.visit(tree))

        # Step 3: Inject decoding infrastructure at top of module
        if self.encoded_strings:
            transformed = self._inject_decoding_infrastructure(transformed)

        # Fix missing locations
        ast.fix_missing_locations(transformed)

        return transformed

    def _identify_docstrings(self, tree: ast.Module) -> None:
        """
        Identify all docstring nodes to preserve them.

        Docstrings are the first statement in:
        - Modules
        - Functions
        - Classes

        Args:
            tree: AST tree to analyze
        """
        # Module docstring
        if (
            tree.body
            and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)
        ):
            self._docstring_nodes.add(id(tree.body[0].value))

        # Function and class docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    self._docstring_nodes.add(id(node.body[0].value))

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """
        Visit Constant node and encode string literals.

        Args:
            node: Constant node

        Returns:
            ast.AST: Original or encoded constant
        """
        # Skip if not a string
        if not isinstance(node.value, str):
            return node

        # Skip if we're in an f-string (cannot encode)
        if self._in_fstring:
            self._skipped_fstring_count += 1
            return node

        # Skip if this is a docstring (preserve documentation)
        if id(node) in self._docstring_nodes:
            return node

        # Skip empty strings (not worth encoding)
        if not node.value:
            return node

        # Encode the string
        encoded = self._encode_string(node.value)
        self.encoded_strings[node.value] = encoded

        # Create function call: _decode_str("encoded_value")
        decode_call = ast.Call(
            func=ast.Name(id=self.decode_function_name, ctx=ast.Load()),
            args=[ast.Constant(value=encoded, kind=None)],
            keywords=[],
        )

        self._increment_transform_count()
        return decode_call

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:
        """
        Visit f-string node and skip encoding entirely.

        F-strings cannot be encoded because they contain expressions
        that are evaluated at runtime. We return the node unchanged
        without visiting its children to preserve the f-string structure.

        Args:
            node: JoinedStr (f-string) node

        Returns:
            ast.JoinedStr: Unchanged node
        """
        # Count the f-string as skipped
        self._skipped_fstring_count += 1

        # Return the node AS-IS without visiting children
        # This prevents any modifications to the f-string structure
        return node

    def _encode_string(self, text: str) -> str:
        """
        Encode a string using Base64.

        Args:
            text: String to encode

        Returns:
            str: Base64-encoded string
        """
        # Encode string to bytes, then Base64 encode
        text_bytes = text.encode("utf-8")
        encoded_bytes = base64.b64encode(text_bytes)
        return encoded_bytes.decode("ascii")

    def _inject_decoding_infrastructure(self, tree: ast.Module) -> ast.Module:
        """
        Inject decoding function at the top of the module.

        Args:
            tree: AST module

        Returns:
            ast.Module: Module with injected decoding function
        """
        # Create the decoding function
        decode_function = self._create_decode_function()

        # Insert at the beginning of the module
        tree.body.insert(0, decode_function)

        return tree

    def _create_decode_function(self) -> ast.FunctionDef:
        """
        Create the Base64 decoding function.

        Returns:
            ast.FunctionDef: Decoding function AST node
        """
        # Create function:
        # def _decode_str(s):
        #     import base64
        #     return base64.b64decode(s).decode('utf-8')

        function_def = ast.FunctionDef(
            name=self.decode_function_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="s", annotation=None)],
                vararg=None,
                kwonlyargs=[],
                kw_defaults=[],
                kwarg=None,
                defaults=[],
            ),
            body=[
                # import base64
                ast.Import(names=[ast.alias(name="base64", asname=None)]),
                # return base64.b64decode(s).decode('utf-8')
                ast.Return(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="base64", ctx=ast.Load()),
                                    attr="b64decode",
                                    ctx=ast.Load(),
                                ),
                                args=[ast.Name(id="s", ctx=ast.Load())],
                                keywords=[],
                            ),
                            attr="decode",
                            ctx=ast.Load(),
                        ),
                        args=[ast.Constant(value="utf-8", kind=None)],
                        keywords=[],
                    )
                ),
            ],
            decorator_list=[],
            returns=None,
        )

        return function_def

    def get_statistics(self) -> Dict[str, int]:
        """
        Get encoding statistics.

        Returns:
            dict: Statistics about the encoding process
        """
        return {
            "encoded_strings": len(self.encoded_strings),
            "skipped_fstrings": self._skipped_fstring_count,
            "transformations": self._transformation_count,
        }
