"""
Import Statement Rewriter for Cross-file Obfuscation.

This module provides the ImportRewriter class which rewrites import statements
to use obfuscated names from the GlobalSymbolTable.
"""

import ast
from typing import Optional, Set, Tuple
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable


class ImportRewriter(ast.NodeTransformer):
    """
    Rewrite import statements to use obfuscated names.

    This transformer rewrites ImportFrom statements by looking up obfuscated
    names in the GlobalSymbolTable. It handles:
    - Simple imports: from module import Name -> from module import I0
    - Multiple imports: from module import Name1, Name2 -> from module import I0, I1
    - Aliases: from module import Name as Alias -> from module import I0 as Alias
    - Relative imports: from .module import Name
    - Wildcard imports: from module import * (preserved)

    Example:
        >>> from pyobfus.core.global_table import GlobalSymbolTable
        >>> import ast
        >>>
        >>> # Setup global table
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>>
        >>> # Parse and rewrite code
        >>> source = "from calculator import Calculator"
        >>> tree = ast.parse(source)
        >>> rewriter = ImportRewriter(table, current_module="main")
        >>> new_tree = rewriter.visit(tree)
        >>> # Result: from calculator import I0
    """

    def __init__(
        self,
        global_table: GlobalSymbolTable,
        current_module: str,
        current_file: Optional[Path] = None,
    ):
        """
        Initialize import rewriter.

        Args:
            global_table: Global symbol table with name mappings
            current_module: Name of current module (e.g., "main", "utils.helpers")
            current_file: Path to current file (optional, for tracking)
        """
        self.global_table = global_table
        self.current_module = current_module
        self.current_file = current_file

        # Track statistics
        self.imports_rewritten: int = 0
        self.imports_unchanged: int = 0
        self.imports_not_found: Set[str] = set()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.ImportFrom:
        """
        Visit and potentially rewrite ImportFrom statement.

        Args:
            node: ImportFrom AST node

        Returns:
            Modified or original ImportFrom node
        """
        # Get module name
        module = node.module

        # Handle relative imports
        if node.level > 0:
            # Resolve relative import to absolute module name
            module = self._resolve_relative_import(node.module, node.level)

        # If module is None or can't be resolved, leave unchanged
        if module is None:
            self.imports_unchanged += 1
            return node

        # Check if this is a wildcard import
        if len(node.names) == 1 and node.names[0].name == "*":
            # Wildcard imports are preserved
            self.imports_unchanged += 1
            return node

        # Rewrite each imported name
        new_names = []
        any_rewritten = False

        for alias in node.names:
            original_name = alias.name
            asname = alias.asname

            # Look up obfuscated name in global table
            obfuscated_name = self.global_table.get_obfuscated_import(module, original_name)

            if obfuscated_name:
                # Found mapping - use obfuscated name
                new_alias = ast.alias(name=obfuscated_name, asname=asname)
                new_names.append(new_alias)
                any_rewritten = True
                self.imports_rewritten += 1
            else:
                # Not found - keep original (might be stdlib or external)
                new_names.append(alias)
                self.imports_not_found.add(f"{module}.{original_name}")
                self.imports_unchanged += 1

        # Create new ImportFrom node with rewritten names
        if any_rewritten:
            new_node = ast.ImportFrom(
                module=node.module,  # Keep original module (including relative level)
                names=new_names,
                level=node.level,
            )
            # Copy location info
            ast.copy_location(new_node, node)
            return new_node
        else:
            return node

    def visit_Import(self, node: ast.Import) -> ast.Import:
        """
        Visit Import statement.

        Import statements (import os, import sys) are NOT rewritten since we
        obfuscate names within modules, not module names themselves.

        Args:
            node: Import AST node

        Returns:
            Original Import node
        """
        self.imports_unchanged += 1
        return node

    def _resolve_relative_import(self, module: Optional[str], level: int) -> Optional[str]:
        """
        Resolve relative import to absolute module name.

        Args:
            module: Module name from ImportFrom (may be None for `from . import`)
            level: Number of dots in relative import

        Returns:
            Absolute module name, or None if can't be resolved

        Examples:
            >>> # In module "pkg.subpkg.module"
            >>> self._resolve_relative_import("utils", 1)
            'pkg.subpkg.utils'
            >>> self._resolve_relative_import(None, 1)
            'pkg.subpkg'
            >>> self._resolve_relative_import("helpers", 2)
            'pkg.helpers'
        """
        if not self.current_module:
            return None

        # Split current module into parts
        parts = self.current_module.split(".")

        # Go up 'level' directories
        # level=1 means parent package (remove last part)
        # level=2 means grandparent package (remove last 2 parts)
        if level > len(parts):
            # Can't go up that many levels
            return None

        # Get parent package parts by removing 'level' parts from the end
        parent_parts = parts[:-level] if level > 0 else parts

        # Add module if specified
        if module:
            parent_parts.append(module)

        return ".".join(parent_parts) if parent_parts else None

    def get_statistics(self) -> dict:
        """
        Get statistics about import rewriting.

        Returns:
            Dictionary with:
            - imports_rewritten: Number of imports rewritten
            - imports_unchanged: Number of imports left unchanged
            - imports_not_found: Set of imports not found in global table
        """
        return {
            "imports_rewritten": self.imports_rewritten,
            "imports_unchanged": self.imports_unchanged,
            "imports_not_found": self.imports_not_found.copy(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ImportRewriter(module={self.current_module}, "
            f"rewritten={self.imports_rewritten}, "
            f"unchanged={self.imports_unchanged})"
        )


def rewrite_imports(
    source: str,
    global_table: GlobalSymbolTable,
    current_module: str,
    current_file: Optional[Path] = None,
) -> Tuple[str, dict]:
    """
    Convenience function to rewrite imports in source code.

    Args:
        source: Python source code
        global_table: Global symbol table with name mappings
        current_module: Name of current module
        current_file: Path to current file (optional)

    Returns:
        Tuple of (rewritten_source, statistics)

    Example:
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>> source = "from calculator import Calculator\\nclass Main: pass"
        >>> new_source, stats = rewrite_imports(source, table, "main")
        >>> print(new_source)
        from calculator import I0
        class Main: pass
    """
    tree = ast.parse(source)
    rewriter = ImportRewriter(global_table, current_module, current_file)
    new_tree = rewriter.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source (use CodeGenerator for Python 3.8 compatibility)
    new_source = CodeGenerator.generate(new_tree)

    return new_source, rewriter.get_statistics()


def rewrite_imports_from_file(
    file_path: Path,
    global_table: GlobalSymbolTable,
    current_module: str,
) -> Tuple[str, dict]:
    """
    Convenience function to rewrite imports in a file.

    Args:
        file_path: Path to Python file
        global_table: Global symbol table with name mappings
        current_module: Name of current module

    Returns:
        Tuple of (rewritten_source, statistics)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    return rewrite_imports(source, global_table, current_module, file_path)
