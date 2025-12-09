"""
Imported Name Transformer for Cross-file Obfuscation.

This module provides the ImportedNameTransformer class which updates
references to imported names throughout the file body.
"""

import ast
from typing import Optional, Set, Dict, Tuple, List
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable


class ImportCollector(ast.NodeVisitor):
    """
    Collect imported names from the original source before transformation.

    This visitor analyzes import statements to build a mapping of:
    original_name -> obfuscated_name for all imported symbols.
    """

    def __init__(self, global_table: GlobalSymbolTable, current_module: str):
        """
        Initialize import collector.

        Args:
            global_table: Global symbol table with name mappings
            current_module: Name of current module
        """
        self.global_table = global_table
        self.current_module = current_module

        # Mapping: original_name -> obfuscated_name
        self.import_mappings: Dict[str, str] = {}

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        Visit ImportFrom statement and collect imported names.

        Args:
            node: ImportFrom AST node
        """
        module = node.module

        # Handle relative imports
        if node.level > 0:
            module = self._resolve_relative_import(node.module, node.level)

        if module is None:
            return

        # Collect each imported name
        for alias in node.names:
            if alias.name == "*":
                continue

            original_name = alias.name
            local_name = alias.asname if alias.asname else original_name

            # Look up obfuscated name
            obfuscated_name = self.global_table.get_obfuscated_import(module, original_name)

            if obfuscated_name:
                # Map: local_name -> obfuscated_name
                self.import_mappings[local_name] = obfuscated_name

        self.generic_visit(node)

    def _resolve_relative_import(self, module: Optional[str], level: int) -> Optional[str]:
        """
        Resolve relative import to absolute module name.

        Args:
            module: Module name from ImportFrom
            level: Number of dots in relative import

        Returns:
            Absolute module name, or None if can't be resolved
        """
        if not self.current_module:
            return None

        parts = self.current_module.split(".")

        if level > len(parts):
            return None

        parent_parts = parts[:-level] if level > 0 else parts

        if module:
            parent_parts.append(module)

        return ".".join(parent_parts) if parent_parts else None


class ImportedNameTransformer(ast.NodeTransformer):
    """
    Transform references to imported names throughout the file body.

    This transformer updates all Name nodes that reference imported symbols
    to use their obfuscated names.

    Example:
        Original:
            from calculator import Calculator
            calc = Calculator()  # Reference to imported name

        After ImportRewriter:
            from calculator import I0
            calc = Calculator()  # Still references old name!

        After ImportedNameTransformer:
            from calculator import I0
            calc = I0()  # Reference updated!

    Usage:
        >>> from pyobfus.core.global_table import GlobalSymbolTable
        >>> import ast
        >>>
        >>> # Setup
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>>
        >>> # Parse original source
        >>> source = "from calculator import Calculator\\ncalc = Calculator()"
        >>> tree = ast.parse(source)
        >>>
        >>> # Transform
        >>> transformer = ImportedNameTransformer(tree, table, "main")
        >>> new_tree = transformer.visit(tree)
        >>> # Result: calc = I0()
    """

    def __init__(
        self,
        original_tree: ast.AST,
        global_table: GlobalSymbolTable,
        current_module: str,
        current_file: Optional[Path] = None,
    ):
        """
        Initialize imported name transformer.

        Args:
            original_tree: Original AST before any transformations
            global_table: Global symbol table with name mappings
            current_module: Name of current module
            current_file: Path to current file (optional)
        """
        self.global_table = global_table
        self.current_module = current_module
        self.current_file = current_file

        # Collect import mappings from original tree
        collector = ImportCollector(global_table, current_module)
        collector.visit(original_tree)
        self.import_mappings = collector.import_mappings

        # Track statistics
        self.references_updated: int = 0
        self.references_unchanged: int = 0

        # Track scope (don't rename function parameters, local variables, etc.)
        self._local_names: Set[str] = set()
        self._scope_stack: List[Set[str]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Visit function definition and track local scope.

        Args:
            node: FunctionDef AST node

        Returns:
            Transformed FunctionDef node
        """
        # Collect function parameter names (don't transform these)
        param_names = set()
        for arg in node.args.args:
            param_names.add(arg.arg)
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            param_names.add(node.args.kwarg.arg)

        # Push new scope
        self._scope_stack.append(param_names)

        # Visit children
        self.generic_visit(node)

        # Pop scope
        self._scope_stack.pop()

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Visit async function definition."""
        # Same logic as FunctionDef
        param_names = set()
        for arg in node.args.args:
            param_names.add(arg.arg)
        if node.args.vararg:
            param_names.add(node.args.vararg.arg)
        if node.args.kwarg:
            param_names.add(node.args.kwarg.arg)

        self._scope_stack.append(param_names)
        self.generic_visit(node)
        self._scope_stack.pop()

        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """
        Visit class definition and track scope.

        Args:
            node: ClassDef AST node

        Returns:
            Transformed ClassDef node
        """
        # Push new scope for class
        self._scope_stack.append(set())
        self.generic_visit(node)
        self._scope_stack.pop()

        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """
        Visit Name node and replace if it references an imported name.

        Args:
            node: Name AST node

        Returns:
            Modified or original Name node
        """
        # Check if this name is in local scope (don't transform)
        for scope in self._scope_stack:
            if node.id in scope:
                self.references_unchanged += 1
                return node

        # Check if this name is an imported name
        if node.id in self.import_mappings:
            obfuscated_name = self.import_mappings[node.id]

            # Create new Name node with obfuscated name
            new_node = ast.Name(id=obfuscated_name, ctx=node.ctx)
            ast.copy_location(new_node, node)
            self.references_updated += 1
            return new_node

        self.references_unchanged += 1
        return node

    def get_statistics(self) -> dict:
        """
        Get statistics about name transformation.

        Returns:
            Dictionary with:
            - references_updated: Number of references updated
            - references_unchanged: Number of references left unchanged
            - import_mappings: Mapping of imported names
        """
        return {
            "references_updated": self.references_updated,
            "references_unchanged": self.references_unchanged,
            "import_mappings": self.import_mappings.copy(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ImportedNameTransformer(module={self.current_module}, "
            f"updated={self.references_updated}, "
            f"mappings={len(self.import_mappings)})"
        )


def transform_imported_names(
    source: str,
    global_table: GlobalSymbolTable,
    current_module: str,
    current_file: Optional[Path] = None,
) -> Tuple[str, dict]:
    """
    Convenience function to transform imported name references in source code.

    Args:
        source: Python source code
        global_table: Global symbol table with name mappings
        current_module: Name of current module
        current_file: Path to current file (optional)

    Returns:
        Tuple of (transformed_source, statistics)

    Example:
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>> source = "from calculator import Calculator\\ncalc = Calculator()"
        >>> new_source, stats = transform_imported_names(source, table, "main")
        >>> # Result: from calculator import Calculator\\ncalc = Calculator()
        >>> # Note: Run AFTER ImportRewriter to get final result
    """
    # Parse original source (before any transformations)
    original_tree = ast.parse(source)

    # Parse again for transformation
    tree = ast.parse(source)

    # Transform
    transformer = ImportedNameTransformer(original_tree, global_table, current_module, current_file)
    new_tree = transformer.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source (use CodeGenerator for Python 3.8 compatibility)
    new_source = CodeGenerator.generate(new_tree)

    return new_source, transformer.get_statistics()
