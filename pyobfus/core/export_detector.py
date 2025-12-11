"""
Export Detection for Python Modules.

This module provides the ExportDetector class which identifies all names
exported by a Python module using AST analysis.
"""

import ast
from typing import Set


class ExportDetector(ast.NodeVisitor):
    """
    Detect all names exported by a module.

    A module exports names through:
    1. Explicit __all__ list (if present, only these are exported)
    2. Top-level definitions (classes, functions, variables) without leading underscore
    3. Re-exported imports (if in __all__)

    Example:
        >>> import ast
        >>> tree = ast.parse('def public(): pass\\ndef _private(): pass')
        >>> detector = ExportDetector()
        >>> detector.visit(tree)
        >>> detector.get_exports()
        {'public'}
    """

    def __init__(self):
        """Initialize export detector."""
        # All potential exports (top-level definitions)
        self.potential_exports: Set[str] = set()

        # Whether __all__ is explicitly defined
        self.has_all: bool = False

        # Names in __all__ list
        self.all_names: Set[str] = set()

        # Track nesting level (only process top-level)
        self._nesting_level: int = 0

        # Track if we're inside a class (for nested class detection)
        self._in_class: bool = False

    def visit_Module(self, node: ast.Module) -> None:
        """Visit module node."""
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visit class definition.

        Only top-level classes are potential exports.
        """
        if self._is_top_level():
            # Top-level class
            if not node.name.startswith("_"):
                self.potential_exports.add(node.name)

        # Track nesting for nested classes
        old_in_class = self._in_class
        self._in_class = True
        self._nesting_level += 1

        self.generic_visit(node)

        self._nesting_level -= 1
        self._in_class = old_in_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Visit function definition.

        Only top-level functions are potential exports.
        """
        if self._is_top_level():
            # Top-level function
            if not node.name.startswith("_"):
                self.potential_exports.add(node.name)

        # Don't visit nested functions as exports
        self._nesting_level += 1
        self.generic_visit(node)
        self._nesting_level -= 1

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """
        Visit async function definition.

        Treat same as regular function.
        """
        if self._is_top_level():
            if not node.name.startswith("_"):
                self.potential_exports.add(node.name)

        self._nesting_level += 1
        self.generic_visit(node)
        self._nesting_level -= 1

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        Visit assignment statement.

        Check for:
        1. __all__ = [...]
        2. Top-level variable assignments
        """
        if self._is_top_level():
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Check for __all__
                    if target.id == "__all__":
                        self.has_all = True
                        self.all_names = self._extract_all_names(node.value)
                    else:
                        # Regular variable assignment
                        if not target.id.startswith("_"):
                            self.potential_exports.add(target.id)

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """
        Visit annotated assignment (e.g., x: int = 5).

        Treat same as regular assignment.
        """
        if self._is_top_level():
            if isinstance(node.target, ast.Name):
                name = node.target.id
                if name == "__all__" and node.value:
                    self.has_all = True
                    self.all_names = self._extract_all_names(node.value)
                elif not name.startswith("_"):
                    self.potential_exports.add(name)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        Visit from ... import ... statement.

        Re-exported imports are potential exports (if in __all__).
        """
        if self._is_top_level():
            for alias in node.names:
                # Get the name as it appears in the importing module
                name = alias.asname if alias.asname else alias.name

                if name != "*" and not name.startswith("_"):
                    # This could be a re-export
                    self.potential_exports.add(name)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """
        Visit import ... statement.

        Imported modules can be re-exported.
        """
        if self._is_top_level():
            for alias in node.names:
                # Get the name as it appears in the importing module
                name = alias.asname if alias.asname else alias.name.split(".")[0]

                if not name.startswith("_"):
                    self.potential_exports.add(name)

        self.generic_visit(node)

    def _is_top_level(self) -> bool:
        """
        Check if current context is top-level (module level).

        Returns:
            True if at module level, False otherwise
        """
        return self._nesting_level == 0

    def _extract_all_names(self, node: ast.expr) -> Set[str]:
        """
        Extract names from __all__ definition.

        Supports:
        - __all__ = ["name1", "name2"]
        - __all__ = ("name1", "name2")
        - __all__ = ["name1"] + ["name2"]  (simple cases)

        Args:
            node: AST node representing __all__ value

        Returns:
            Set of names in __all__
        """
        names: Set[str] = set()

        if isinstance(node, (ast.List, ast.Tuple)):
            # __all__ = ["name1", "name2"]
            for elt in node.elts:
                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                    names.add(elt.value)
                elif isinstance(elt, ast.Str):  # Python 3.7 compatibility
                    names.add(str(elt.s))

        elif isinstance(node, ast.BinOp):
            # __all__ = ["name1"] + ["name2"]
            if isinstance(node.op, ast.Add):
                names.update(self._extract_all_names(node.left))
                names.update(self._extract_all_names(node.right))

        return names

    def get_exports(self) -> Set[str]:
        """
        Get final list of exported names.

        If __all__ is defined, only return names in __all__.
        Otherwise, return all potential exports (non-private top-level names).

        Returns:
            Set of exported names
        """
        if self.has_all:
            # Only export names explicitly listed in __all__
            return self.all_names.copy()
        else:
            # Export all non-private top-level definitions
            return self.potential_exports.copy()

    def get_statistics(self) -> dict:
        """
        Get statistics about detected exports.

        Returns:
            Dictionary with:
            - has_all: Whether __all__ is defined
            - all_count: Number of names in __all__ (0 if not defined)
            - potential_exports: Number of potential exports
            - final_exports: Number of final exports
        """
        return {
            "has_all": self.has_all,
            "all_count": len(self.all_names),
            "potential_exports": len(self.potential_exports),
            "final_exports": len(self.get_exports()),
        }


def detect_exports(source: str) -> Set[str]:
    """
    Convenience function to detect exports from source code.

    Args:
        source: Python source code as string

    Returns:
        Set of exported names

    Example:
        >>> source = '''
        ... def public_func():
        ...     pass
        ... def _private_func():
        ...     pass
        ... class PublicClass:
        ...     pass
        ... '''
        >>> exports = detect_exports(source)
        >>> 'public_func' in exports
        True
        >>> '_private_func' in exports
        False
    """
    tree = ast.parse(source)
    detector = ExportDetector()
    detector.visit(tree)
    return detector.get_exports()


def detect_exports_from_file(file_path: str) -> Set[str]:
    """
    Convenience function to detect exports from a file.

    Args:
        file_path: Path to Python file

    Returns:
        Set of exported names
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    return detect_exports(source)
