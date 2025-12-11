"""
__all__ List Updater for Cross-file Obfuscation.

This module provides the AllListUpdater class which updates __all__ lists
to use obfuscated names from the GlobalSymbolTable.
"""

import ast
from typing import Optional, Set, Tuple
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable


class AllListUpdater(ast.NodeTransformer):
    """
    Update __all__ lists to use obfuscated names.

    This transformer updates __all__ assignments by looking up obfuscated
    names in the GlobalSymbolTable. It handles:
    - List form: __all__ = ["Name1", "Name2"]
    - Tuple form: __all__ = ("Name1", "Name2")
    - Annotated form: __all__: list[str] = ["Name1"]

    Example:
        >>> from pyobfus.core.global_table import GlobalSymbolTable
        >>> import ast
        >>>
        >>> # Setup global table
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>>
        >>> # Parse and update code
        >>> source = '__all__ = ["Calculator"]'
        >>> tree = ast.parse(source)
        >>> updater = AllListUpdater(table, current_module="calculator")
        >>> new_tree = updater.visit(tree)
        >>> # Result: __all__ = ["I0"]
    """

    def __init__(
        self,
        global_table: GlobalSymbolTable,
        current_module: str,
        current_file: Optional[Path] = None,
    ):
        """
        Initialize __all__ list updater.

        Args:
            global_table: Global symbol table with name mappings
            current_module: Name of current module (e.g., "calculator", "utils")
            current_file: Path to current file (optional, for tracking)
        """
        self.global_table = global_table
        self.current_module = current_module
        self.current_file = current_file

        # Track statistics
        self.all_lists_updated: int = 0
        self.names_updated: int = 0
        self.names_not_found: Set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        """
        Visit assignment statement and update __all__ if found.

        Args:
            node: Assign AST node

        Returns:
            Modified or original Assign node
        """
        # Check if this is __all__ assignment
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "__all__":
                # This is __all__ assignment
                new_value = self._update_all_value(node.value)
                if new_value is not None:
                    # Create new assignment with updated value
                    new_node = ast.Assign(targets=node.targets, value=new_value)
                    ast.copy_location(new_node, node)
                    self.all_lists_updated += 1
                    return new_node

        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        """
        Visit annotated assignment and update __all__ if found.

        Args:
            node: AnnAssign AST node

        Returns:
            Modified or original AnnAssign node
        """
        # Check if this is __all__ assignment
        if isinstance(node.target, ast.Name) and node.target.id == "__all__":
            if node.value is not None:
                # This is __all__ assignment with value
                new_value = self._update_all_value(node.value)
                if new_value is not None:
                    # Create new assignment with updated value
                    new_node = ast.AnnAssign(
                        target=node.target,
                        annotation=node.annotation,
                        value=new_value,
                        simple=node.simple,
                    )
                    ast.copy_location(new_node, node)
                    self.all_lists_updated += 1
                    return new_node

        return node

    def _update_all_value(self, value: ast.expr) -> Optional[ast.expr]:
        """
        Update value of __all__ assignment.

        Args:
            value: AST expression representing __all__ value

        Returns:
            Updated AST expression, or None if can't update

        Examples:
            ["Name1", "Name2"] -> ["I0", "I1"]
            ("Name1", "Name2") -> ("I0", "I1")
        """
        if isinstance(value, ast.List):
            # __all__ = ["Name1", "Name2"]
            new_elts = []
            for elt in value.elts:
                new_elt = self._update_string_constant(elt)
                if new_elt is not None:
                    new_elts.append(new_elt)
                else:
                    # Can't update, keep original
                    new_elts.append(elt)

            return ast.List(elts=new_elts, ctx=value.ctx)

        elif isinstance(value, ast.Tuple):
            # __all__ = ("Name1", "Name2")
            new_elts = []
            for elt in value.elts:
                new_elt = self._update_string_constant(elt)
                if new_elt is not None:
                    new_elts.append(new_elt)
                else:
                    # Can't update, keep original
                    new_elts.append(elt)

            return ast.Tuple(elts=new_elts, ctx=value.ctx)

        elif isinstance(value, ast.BinOp) and isinstance(value.op, ast.Add):
            # __all__ = ["Name1"] + ["Name2"]
            # Recursively update left and right
            new_left = self._update_all_value(value.left)
            new_right = self._update_all_value(value.right)

            if new_left is not None and new_right is not None:
                return ast.BinOp(left=new_left, op=value.op, right=new_right)

        # Can't handle this form
        return None

    def _update_string_constant(self, node: ast.expr) -> Optional[ast.expr]:
        """
        Update string constant with obfuscated name.

        Args:
            node: AST expression (should be string constant)

        Returns:
            Updated string constant, or None if can't update
        """
        original_name = None

        # Extract string value
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            original_name = node.value
        elif isinstance(node, ast.Str):  # Python 3.7 compatibility
            original_name = str(node.s)

        if original_name is None:
            return None

        # Look up obfuscated name
        obfuscated_name = self.global_table.get_obfuscated_import(
            self.current_module, original_name
        )

        if obfuscated_name:
            # Found mapping - create new string constant
            self.names_updated += 1
            return ast.Constant(value=obfuscated_name, kind=None)
        else:
            # Not found - keep original (might be intentional)
            self.names_not_found.add(original_name)
            return None

    def get_statistics(self) -> dict:
        """
        Get statistics about __all__ list updating.

        Returns:
            Dictionary with:
            - all_lists_updated: Number of __all__ lists updated
            - names_updated: Number of names updated in __all__ lists
            - names_not_found: Set of names not found in global table
        """
        return {
            "all_lists_updated": self.all_lists_updated,
            "names_updated": self.names_updated,
            "names_not_found": self.names_not_found.copy(),
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"AllListUpdater(module={self.current_module}, "
            f"updated={self.all_lists_updated}, "
            f"names={self.names_updated})"
        )


def update_all_list(
    source: str,
    global_table: GlobalSymbolTable,
    current_module: str,
    current_file: Optional[Path] = None,
) -> Tuple[str, dict]:
    """
    Convenience function to update __all__ list in source code.

    Args:
        source: Python source code
        global_table: Global symbol table with name mappings
        current_module: Name of current module
        current_file: Path to current file (optional)

    Returns:
        Tuple of (updated_source, statistics)

    Example:
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>> source = '__all__ = ["Calculator"]'
        >>> new_source, stats = update_all_list(source, table, "calculator")
        >>> print(new_source)
        __all__ = ["I0"]
    """
    tree = ast.parse(source)
    updater = AllListUpdater(global_table, current_module, current_file)
    new_tree = updater.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source (use CodeGenerator for Python 3.8 compatibility)
    new_source = CodeGenerator.generate(new_tree)

    return new_source, updater.get_statistics()


def update_all_list_from_file(
    file_path: Path,
    global_table: GlobalSymbolTable,
    current_module: str,
) -> Tuple[str, dict]:
    """
    Convenience function to update __all__ list in a file.

    Args:
        file_path: Path to Python file
        global_table: Global symbol table with name mappings
        current_module: Name of current module

    Returns:
        Tuple of (updated_source, statistics)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    return update_all_list(source, global_table, current_module, file_path)
