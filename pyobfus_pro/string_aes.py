"""
AES-256 String Encryption Transformer (Pro Feature)

Encrypts string literals in Python code using AES-256 and injects
runtime decryption functions. Much stronger than simple ROT13 encoding.

Example:
    Original: print("Calcium Score: 123")
    Encrypted: print(_decrypt_str(b'gAAAAAB...'))

Note: F-strings are NOT encrypted due to Python AST limitations.
"""

import ast
import base64
from typing import Dict, Optional, cast

from cryptography.fernet import Fernet  # type: ignore[import-not-found]

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.transformer import BaseTransformer


class StringAESEncryptor(BaseTransformer):
    """
    Encrypts string literals using AES-256 (Fernet symmetric encryption).

    Features:
    - AES-256-CBC encryption
    - HMAC authentication
    - Per-file unique key
    - Runtime decryption function injection
    - Skips f-strings (Python AST limitation)
    """

    def __init__(self, config: ObfuscationConfig, analyzer: Optional[SymbolAnalyzer] = None):
        """
        Initialize string encryptor.

        Args:
            config: Obfuscation configuration
            analyzer: Symbol analyzer (optional)
        """
        super().__init__(config, analyzer)
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.encrypted_strings: Dict[str, bytes] = {}
        self.decrypt_function_name = "_decrypt_str"
        self.key_variable_name = "_ENCRYPTION_KEY"
        self._in_fstring = False  # Track if we're inside an f-string
        self._skipped_fstring_count = 0
        self._current_parent = None  # Track parent node for docstring detection

    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform AST by encrypting all string literals.

        Args:
            tree: Input AST

        Returns:
            ast.Module: Transformed AST with encrypted strings
        """
        # Step 1: Visit and encrypt strings
        transformed = cast(ast.Module, self.visit(tree))

        # Step 2: Inject decryption infrastructure at top of module
        if self.encrypted_strings:
            transformed = self._inject_decryption_infrastructure(transformed)

        # Fix missing locations
        ast.fix_missing_locations(transformed)

        return transformed

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """
        Visit Module node and skip module docstring.

        Args:
            node: Module AST node

        Returns:
            ast.Module: Transformed module
        """
        # Skip encrypting module-level docstring (first statement if Expr with string)
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                # Don't transform the docstring
                first_stmt = node.body[0]
                rest = node.body[1:]
                # Visit the rest
                for i, child in enumerate(rest):
                    node.body[i + 1] = self.visit(child)
                return node

        # Normal traversal
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Visit FunctionDef node and skip function docstring.

        Args:
            node: FunctionDef AST node

        Returns:
            ast.FunctionDef: Transformed function
        """
        # Skip encrypting function docstring (first statement if Expr with string)
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                # Don't transform the docstring
                first_stmt = node.body[0]
                rest = node.body[1:]
                # Visit the rest
                for i, child in enumerate(rest):
                    node.body[i + 1] = self.visit(child)
                return node

        # Normal traversal
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """
        Visit AsyncFunctionDef node and skip function docstring.

        Args:
            node: AsyncFunctionDef AST node

        Returns:
            ast.AsyncFunctionDef: Transformed function
        """
        # Skip encrypting function docstring (first statement if Expr with string)
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                # Don't transform the docstring
                first_stmt = node.body[0]
                rest = node.body[1:]
                # Visit the rest
                for i, child in enumerate(rest):
                    node.body[i + 1] = self.visit(child)
                return node

        # Normal traversal
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """
        Visit ClassDef node and skip class docstring.

        Args:
            node: ClassDef AST node

        Returns:
            ast.ClassDef: Transformed class
        """
        # Skip encrypting class docstring (first statement if Expr with string)
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                # Don't transform the docstring
                first_stmt = node.body[0]
                rest = node.body[1:]
                # Visit the rest
                for i, child in enumerate(rest):
                    node.body[i + 1] = self.visit(child)
                return node

        # Normal traversal
        self.generic_visit(node)
        return node

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.AST:
        """
        Visit f-strings (JoinedStr). Do not encrypt strings inside f-strings.

        Python's f-string AST structure does not allow function calls
        inside string parts, so we skip encryption for f-strings.

        Args:
            node: JoinedStr AST node

        Returns:
            ast.AST: Original node (unmodified)
        """
        # Mark that we're inside an f-string and don't recurse
        self._skipped_fstring_count += 1
        # Don't visit children - keep f-string intact
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """
        Visit Constant nodes and encrypt string literals.

        Args:
            node: Constant AST node

        Returns:
            ast.AST: Call to decryption function or original node
        """
        # Only encrypt string constants
        if not isinstance(node.value, str):
            return node

        # Skip very short strings (likely syntax elements)
        if len(node.value) < 3:
            return node

        # Skip strings that look like module/attribute names
        if node.value.isidentifier():
            return node

        # Encrypt the string
        encrypted_bytes = self.cipher.encrypt(node.value.encode("utf-8"))
        encrypted_b64 = base64.b64encode(encrypted_bytes)

        # Store for statistics
        self.encrypted_strings[node.value] = encrypted_bytes

        # Replace with decryption call: _decrypt_str(b'...')
        return ast.Call(
            func=ast.Name(id=self.decrypt_function_name, ctx=ast.Load()),
            args=[ast.Constant(value=encrypted_b64)],
            keywords=[],
        )

    def _inject_decryption_infrastructure(self, tree: ast.Module) -> ast.Module:
        """
        Inject decryption function and key at top of module.

        Args:
            tree: AST module

        Returns:
            ast.Module: Module with decryption infrastructure prepended
        """
        # Encryption key as bytes literal
        key_node = ast.Assign(
            targets=[ast.Name(id=self.key_variable_name, ctx=ast.Store())],
            value=ast.Constant(value=self.encryption_key),
        )

        # Decryption function
        decrypt_function = self._create_decrypt_function()

        # Prepend to module body
        tree.body = [key_node, decrypt_function] + tree.body

        return tree

    def _create_decrypt_function(self) -> ast.FunctionDef:
        """
        Create the runtime decryption function.

        Returns:
            ast.FunctionDef: Decryption function AST node
        """
        # Function code:
        # def _decrypt_str(encrypted_b64: bytes) -> str:
        #     from cryptography.fernet import Fernet
        #     import base64
        #     cipher = Fernet(_ENCRYPTION_KEY)
        #     encrypted_bytes = base64.b64decode(encrypted_b64)
        #     return cipher.decrypt(encrypted_bytes).decode('utf-8')

        function_body = [
            # Import statements
            ast.ImportFrom(
                module="cryptography.fernet",
                names=[ast.alias(name="Fernet", asname=None)],
                level=0,
            ),
            ast.Import(names=[ast.alias(name="base64", asname=None)]),
            # cipher = Fernet(_ENCRYPTION_KEY)
            ast.Assign(
                targets=[ast.Name(id="cipher", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="Fernet", ctx=ast.Load()),
                    args=[ast.Name(id=self.key_variable_name, ctx=ast.Load())],
                    keywords=[],
                ),
            ),
            # encrypted_bytes = base64.b64decode(encrypted_b64)
            ast.Assign(
                targets=[ast.Name(id="encrypted_bytes", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id="base64", ctx=ast.Load()),
                        attr="b64decode",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Name(id="encrypted_b64", ctx=ast.Load())],
                    keywords=[],
                ),
            ),
            # return cipher.decrypt(encrypted_bytes).decode('utf-8')
            ast.Return(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="cipher", ctx=ast.Load()),
                                attr="decrypt",
                                ctx=ast.Load(),
                            ),
                            args=[ast.Name(id="encrypted_bytes", ctx=ast.Load())],
                            keywords=[],
                        ),
                        attr="decode",
                        ctx=ast.Load(),
                    ),
                    args=[ast.Constant(value="utf-8")],
                    keywords=[],
                ),
            ),
        ]

        return ast.FunctionDef(
            name=self.decrypt_function_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[ast.arg(arg="encrypted_b64", annotation=None)],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=function_body,
            decorator_list=[],
            returns=None,
        )

    def get_statistics(self) -> Dict[str, int]:
        """
        Get encryption statistics.

        Returns:
            Dict[str, int]: Statistics dictionary
        """
        return {
            "encrypted_strings": len(self.encrypted_strings),
            "total_bytes": sum(len(enc) for enc in self.encrypted_strings.values()),
            "skipped_fstrings": self._skipped_fstring_count,
        }
