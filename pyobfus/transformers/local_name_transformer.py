"""
Local Name Transformer for Cross-file Obfuscation.

This module provides the LocalNameTransformer class which updates
references to locally-defined exported names within the same module.

For example, if a function is renamed from `run_demo` to `I2`, all
calls to `run_demo()` within the same file must be updated to `I2()`.
"""

import ast
from typing import Optional, Set, Tuple, List
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable


class LocalNameTransformer(ast.NodeTransformer):
    """
    Transform local references to exported names.

    This transformer updates Name nodes that reference locally-defined
    exported symbols that have been renamed.

    Example:
        Original:
            def run_demo():
                pass

            if __name__ == "__main__":
                run_demo()  # <- needs to be updated

        After ExportedNameTransformer:
            def I2():
                pass

            if __name__ == "__main__":
                run_demo()  # <- still wrong!

        After LocalNameTransformer:
            def I2():
                pass

            if __name__ == "__main__":
                I2()  # <- correct!
    """

    def __init__(
        self,
        global_table: GlobalSymbolTable,
        current_module: str,
        imported_names: Optional[Set[str]] = None,
        current_file: Optional[Path] = None,
    ):
        """
        Initialize local name transformer.

        Args:
            global_table: Global symbol table with name mappings
            current_module: Name of current module (e.g., "calculator", "utils")
            imported_names: Set of names that were imported (to avoid renaming)
            current_file: Path to current file (optional, for tracking)
        """
        self.global_table = global_table
        self.current_module = current_module
        self.imported_names = imported_names or set()
        self.current_file = current_file

        # Get mappings for locally-defined exports in this module
        self.local_export_mappings = global_table.get_module_exports(current_module)

        # Track statistics
        self.names_renamed: int = 0
        self.names_unchanged: int = 0

        # Track local scopes (stack of sets of locally-bound names)
        self._local_scopes: List[Set[str]] = []

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """
        Visit Name node and rename if it's a local exported name reference.

        Args:
            node: Name AST node

        Returns:
            Modified or original Name node
        """
        # Only rename in Load context (usage, not definition)
        if not isinstance(node.ctx, ast.Load):
            return node

        # Don't rename imported names (those are handled by ImportedNameTransformer)
        if node.id in self.imported_names:
            return node

        # Don't rename if shadowed by a local variable/parameter in any scope
        for local_scope in self._local_scopes:
            if node.id in local_scope:
                return node

        # Check if this is a local exported name
        obfuscated_name = self.local_export_mappings.get(node.id)
        if obfuscated_name:
            # Create new Name with obfuscated name
            new_node = ast.Name(id=obfuscated_name, ctx=node.ctx)
            ast.copy_location(new_node, node)
            self.names_renamed += 1
            return new_node
        else:
            self.names_unchanged += 1
            return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Visit function definition.

        We collect parameter names and create a new scope to avoid
        renaming references to parameters inside the function.

        Args:
            node: FunctionDef AST node

        Returns:
            Modified or original FunctionDef node
        """
        # Collect all parameter names for this function
        param_names: Set[str] = set()

        # Regular args
        for arg in node.args.args:
            param_names.add(arg.arg)

        # Positional-only args
        for arg in node.args.posonlyargs:
            param_names.add(arg.arg)

        # Keyword-only args
        for arg in node.args.kwonlyargs:
            param_names.add(arg.arg)

        # *args
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)

        # **kwargs
        if node.args.kwarg:
            param_names.add(node.args.kwarg.arg)

        # Push new scope with parameter names
        self._local_scopes.append(param_names)

        # Visit decorators (before entering function body)
        for decorator in node.decorator_list:
            self.visit(decorator)

        # Visit body with parameters in scope
        for stmt in node.body:
            self.visit(stmt)

        # Pop scope
        self._local_scopes.pop()

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """
        Visit async function definition.

        Args:
            node: AsyncFunctionDef AST node

        Returns:
            Modified or original AsyncFunctionDef node
        """
        # Same logic as FunctionDef - collect parameter names
        param_names: Set[str] = set()

        for arg in node.args.args:
            param_names.add(arg.arg)
        for arg in node.args.posonlyargs:
            param_names.add(arg.arg)
        for arg in node.args.kwonlyargs:
            param_names.add(arg.arg)
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            param_names.add(node.args.kwarg.arg)

        # Push new scope
        self._local_scopes.append(param_names)

        # Visit decorators
        for decorator in node.decorator_list:
            self.visit(decorator)

        # Visit body
        for stmt in node.body:
            self.visit(stmt)

        # Pop scope
        self._local_scopes.pop()

        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """
        Visit class definition.

        Args:
            node: ClassDef AST node

        Returns:
            Modified or original ClassDef node
        """
        # Visit body (rename local references in methods)
        for stmt in node.body:
            self.visit(stmt)

        # Visit decorators and base classes
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)

        return node

    def get_statistics(self) -> dict:
        """
        Get statistics about name transformation.

        Returns:
            Dictionary with:
            - names_renamed: Number of name references renamed
            - names_unchanged: Number of name references left unchanged
        """
        return {
            "names_renamed": self.names_renamed,
            "names_unchanged": self.names_unchanged,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LocalNameTransformer(module={self.current_module}, "
            f"renamed={self.names_renamed}, "
            f"unchanged={self.names_unchanged})"
        )


def transform_local_names(
    source: str,
    global_table: GlobalSymbolTable,
    current_module: str,
    imported_names: Optional[Set[str]] = None,
    current_file: Optional[Path] = None,
) -> Tuple[str, dict]:
    """
    Convenience function to transform local name references in source code.

    Args:
        source: Python source code
        global_table: Global symbol table with name mappings
        current_module: Name of current module
        imported_names: Set of imported names to avoid renaming
        current_file: Path to current file (optional)

    Returns:
        Tuple of (transformed_source, statistics)

    Example:
        >>> table = GlobalSymbolTable()
        >>> table.register_export("main", "run_demo", "I2")
        >>> source = "def I2():\\n    pass\\nif __name__ == '__main__':\\n    run_demo()"
        >>> new_source, stats = transform_local_names(source, table, "main")
        >>> print(new_source)
        def I2():
            pass
        if __name__ == '__main__':
            I2()
    """
    tree = ast.parse(source)
    transformer = LocalNameTransformer(global_table, current_module, imported_names, current_file)
    new_tree = transformer.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source (use CodeGenerator for Python 3.8 compatibility)
    new_source = CodeGenerator.generate(new_tree)

    return new_source, transformer.get_statistics()
