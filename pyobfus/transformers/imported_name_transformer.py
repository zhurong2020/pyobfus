"""
Imported Name Transformer for Cross-file Obfuscation.

This module provides the ImportedNameTransformer class which updates
references to imported names throughout the file body.
"""

import ast
from typing import Optional, Dict, Tuple, Set, Any
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.transformers.scoped_imports import import_plan, key, Key, ImportKey


class ImportCollector(ast.NodeVisitor):
    """
    Collect imported names from the original source before transformation.

    Resolve each reference to its lexical binding before transformation.
    ``import_mappings`` is a diagnostic union, not a reference lookup table.
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

        self.import_mappings: Dict[str, str] = {}
        self.reference_edits: Dict[Key, Any] = {}
        self.preserved_imports: Dict[ImportKey, Tuple[str, str]] = {}
        self.protected_references: Set[Key] = set()

    def visit_Module(self, node: ast.Module) -> None:
        (
            self.reference_edits,
            self.preserved_imports,
            self.import_mappings,
            self.protected_references,
        ) = import_plan(node, self.global_table, self.current_module)

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
        collector: Optional[ImportCollector] = None,
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
        if collector is None:
            collector = ImportCollector(global_table, current_module)
            collector.visit(original_tree)
        self.original_names = {
            key(n): n.id for n in ast.walk(original_tree) if isinstance(n, ast.Name)
        }
        self.import_mappings = collector.import_mappings

        # Track statistics
        self.references_updated: int = 0
        self.references_unchanged: int = 0

        self.reference_edits = collector.reference_edits
        self.preserved_imports = collector.preserved_imports
        self.protected_references = collector.protected_references

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if key(node) in self.protected_references:
            setattr(node, "_pyobfus_local_binding", True)
        if key(node) in self.reference_edits:
            setattr(node, "_pyobfus_import_binding", True)
        if getattr(node, "_pyobfus_local_binding", False) or getattr(
            node, "_pyobfus_class_binding", False
        ):
            return node
        replacement = self.reference_edits.get(key(node), node.id)
        # Earlier local/export passes may already have changed this node.
        # Only apply an import edit if the original spelling still matches.
        if replacement != node.id and node.id == self.original_names.get(key(node)):
            self.references_updated += 1
            return ast.copy_location(ast.Name(id=replacement, ctx=node.ctx), node)
        self.references_unchanged += 1
        return node

    def visit_Global(self, node: ast.Global) -> ast.Global:
        replacements = self.reference_edits.get(key(node))
        if replacements is not None:
            node.names = [
                replacement if name in self.import_mappings else name
                for name, replacement in zip(node.names, replacements)
            ]
        return node

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Nonlocal:
        replacements = self.reference_edits.get(key(node))
        if replacements is not None:
            node.names = [
                replacement if name in self.import_mappings else name
                for name, replacement in zip(node.names, replacements)
            ]
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
