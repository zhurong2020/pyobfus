"""
Exported Name Transformer for Cross-file Obfuscation.

This module provides the ExportedNameTransformer class which renames
exported definitions (classes, functions, variables) to their obfuscated names.
"""

import ast
from typing import List, Optional, Tuple
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable


class ExportedNameTransformer(ast.NodeTransformer):
    """
    Transform exported names to obfuscated names in their definition files.

    This transformer renames top-level definitions that are exported:
    - class Calculator: -> class I0:
    - def my_function(): -> def I1():
    - my_var = 42 -> I2 = 42

    Only names that are in the global symbol table for this module are renamed.

    Example:
        >>> from pyobfus.core.global_table import GlobalSymbolTable
        >>> import ast
        >>>
        >>> # Setup global table
        >>> table = GlobalSymbolTable()
        >>> table.register_export("calculator", "Calculator", "I0")
        >>>
        >>> # Parse and transform code
        >>> source = "class Calculator:\\n    pass"
        >>> tree = ast.parse(source)
        >>> transformer = ExportedNameTransformer(table, current_module="calculator")
        >>> new_tree = transformer.visit(tree)
        >>> # Result: class I0:
        >>>     pass
    """

    def __init__(
        self,
        global_table: GlobalSymbolTable,
        current_module: str,
        current_file: Optional[Path] = None,
    ):
        """
        Initialize exported name transformer.

        Args:
            global_table: Global symbol table with name mappings
            current_module: Name of current module (e.g., "calculator", "utils")
            current_file: Path to current file (optional, for tracking)
        """
        self.global_table = global_table
        self.current_module = current_module
        self.current_file = current_file

        # Get mappings for this module
        self.name_mappings = global_table.get_module_exports(current_module)

        # Track statistics
        self.definitions_renamed: int = 0
        self.definitions_unchanged: int = 0

        # Track nesting level (only rename top-level)
        self._nesting_level: int = 0

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """
        Visit class definition and rename if exported.

        Args:
            node: ClassDef AST node

        Returns:
            Modified or original ClassDef node
        """
        if self._is_top_level():
            # Check if this class should be renamed
            obfuscated_name = self.name_mappings.get(node.name)
            if obfuscated_name:
                # Create new ClassDef with obfuscated name
                new_node = ast.ClassDef(
                    name=obfuscated_name,
                    bases=node.bases,
                    keywords=node.keywords,
                    body=node.body,
                    decorator_list=node.decorator_list,
                )
                ast.copy_location(new_node, node)
                self.definitions_renamed += 1

                # Visit children
                self._nesting_level += 1
                self.generic_visit(new_node)
                self._nesting_level -= 1

                return new_node
            else:
                self.definitions_unchanged += 1

        # Visit children
        self._nesting_level += 1
        self.generic_visit(node)
        self._nesting_level -= 1

        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Visit function definition and rename if exported.

        Args:
            node: FunctionDef AST node

        Returns:
            Modified or original FunctionDef node
        """
        if self._is_top_level():
            # Check if this function should be renamed
            obfuscated_name = self.name_mappings.get(node.name)
            if obfuscated_name:
                # Create new FunctionDef with obfuscated name
                new_node = ast.FunctionDef(
                    name=obfuscated_name,
                    args=node.args,
                    body=node.body,
                    decorator_list=node.decorator_list,
                    returns=node.returns,
                )
                ast.copy_location(new_node, node)
                self.definitions_renamed += 1

                # Visit children
                self._nesting_level += 1
                self.generic_visit(new_node)
                self._nesting_level -= 1

                return new_node
            else:
                self.definitions_unchanged += 1

        # Visit children
        self._nesting_level += 1
        self.generic_visit(node)
        self._nesting_level -= 1

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """
        Visit async function definition and rename if exported.

        Args:
            node: AsyncFunctionDef AST node

        Returns:
            Modified or original AsyncFunctionDef node
        """
        if self._is_top_level():
            # Check if this function should be renamed
            obfuscated_name = self.name_mappings.get(node.name)
            if obfuscated_name:
                # Create new AsyncFunctionDef with obfuscated name
                new_node = ast.AsyncFunctionDef(
                    name=obfuscated_name,
                    args=node.args,
                    body=node.body,
                    decorator_list=node.decorator_list,
                    returns=node.returns,
                )
                ast.copy_location(new_node, node)
                self.definitions_renamed += 1

                # Visit children
                self._nesting_level += 1
                self.generic_visit(new_node)
                self._nesting_level -= 1

                return new_node
            else:
                self.definitions_unchanged += 1

        # Visit children
        self._nesting_level += 1
        self.generic_visit(node)
        self._nesting_level -= 1

        return node

    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        """
        Visit assignment and rename if exported.

        Args:
            node: Assign AST node

        Returns:
            Modified or original Assign node
        """
        if self._is_top_level():
            # Check each target
            new_targets: List[ast.expr] = []
            any_renamed = False

            for target in node.targets:
                if isinstance(target, ast.Name):
                    obfuscated_name = self.name_mappings.get(target.id)
                    if obfuscated_name:
                        # Create new Name with obfuscated name
                        new_target = ast.Name(id=obfuscated_name, ctx=target.ctx)
                        ast.copy_location(new_target, target)
                        new_targets.append(new_target)
                        any_renamed = True
                        self.definitions_renamed += 1
                    else:
                        new_targets.append(target)
                        self.definitions_unchanged += 1
                else:
                    new_targets.append(target)

            if any_renamed:
                # Create new Assign with renamed targets
                new_node = ast.Assign(targets=new_targets, value=node.value)
                ast.copy_location(new_node, node)
                self.generic_visit(new_node)
                return new_node

        self.generic_visit(node)
        return node

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.AnnAssign:
        """
        Visit annotated assignment and rename if exported.

        Args:
            node: AnnAssign AST node

        Returns:
            Modified or original AnnAssign node
        """
        if self._is_top_level():
            if isinstance(node.target, ast.Name):
                obfuscated_name = self.name_mappings.get(node.target.id)
                if obfuscated_name:
                    # Create new Name with obfuscated name
                    new_target = ast.Name(id=obfuscated_name, ctx=node.target.ctx)
                    ast.copy_location(new_target, node.target)

                    # Create new AnnAssign
                    new_node = ast.AnnAssign(
                        target=new_target,
                        annotation=node.annotation,
                        value=node.value,
                        simple=node.simple,
                    )
                    ast.copy_location(new_node, node)
                    self.definitions_renamed += 1
                    self.generic_visit(new_node)
                    return new_node
                else:
                    self.definitions_unchanged += 1

        self.generic_visit(node)
        return node

    def _is_top_level(self) -> bool:
        """
        Check if current context is top-level (module level).

        Returns:
            True if at module level, False otherwise
        """
        return self._nesting_level == 0

    def get_statistics(self) -> dict:
        """
        Get statistics about name transformation.

        Returns:
            Dictionary with:
            - definitions_renamed: Number of definitions renamed
            - definitions_unchanged: Number of definitions left unchanged
        """
        return {
            "definitions_renamed": self.definitions_renamed,
            "definitions_unchanged": self.definitions_unchanged,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExportedNameTransformer(module={self.current_module}, "
            f"renamed={self.definitions_renamed}, "
            f"unchanged={self.definitions_unchanged})"
        )


def transform_exported_names(
    source: str,
    global_table: GlobalSymbolTable,
    current_module: str,
    current_file: Optional[Path] = None,
) -> Tuple[str, dict]:
    """
    Convenience function to transform exported names in source code.

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
        >>> source = "class Calculator:\\n    pass"
        >>> new_source, stats = transform_exported_names(source, table, "calculator")
        >>> print(new_source)
        class I0:
            pass
    """
    tree = ast.parse(source)
    transformer = ExportedNameTransformer(global_table, current_module, current_file)
    new_tree = transformer.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source (use CodeGenerator for Python 3.8 compatibility)
    new_source = CodeGenerator.generate(new_tree)

    return new_source, transformer.get_statistics()


def transform_exported_names_from_file(
    file_path: Path,
    global_table: GlobalSymbolTable,
    current_module: str,
) -> Tuple[str, dict]:
    """
    Convenience function to transform exported names in a file.

    Args:
        file_path: Path to Python file
        global_table: Global symbol table with name mappings
        current_module: Name of current module

    Returns:
        Tuple of (transformed_source, statistics)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    return transform_exported_names(source, global_table, current_module, file_path)
