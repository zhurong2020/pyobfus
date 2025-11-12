"""
Name mangling transformer for obfuscating identifiers.

Renames variables, functions, and classes to short, meaningless names
like I0, I1, I2, etc.
"""

import ast
from typing import Dict, Optional, cast

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.transformer import BaseTransformer


class NameMangler(BaseTransformer):
    """
    Obfuscates names by replacing them with short indexed identifiers.

    Example:
        calculate_risk -> I0
        patient_age -> I1
        risk_factor -> I2
    """

    def __init__(self, config: ObfuscationConfig, analyzer: Optional[SymbolAnalyzer] = None):
        """
        Initialize name mangler.

        Args:
            config: Obfuscation configuration
            analyzer: Symbol analyzer with pre-analyzed names
        """
        super().__init__(config, analyzer)

        # Name mapping: original_name -> obfuscated_name
        self._name_map: Dict[str, str] = {}
        self._counter = 0

    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform all obfuscatable names in the AST.

        Args:
            tree: AST module to transform

        Returns:
            ast.Module: Transformed AST with mangled names
        """
        # Build name mapping
        if self.analyzer:
            for name in sorted(self.analyzer.obfuscatable_names):
                self._name_map[name] = self._generate_obfuscated_name()

        # Transform the tree
        transformed = cast(ast.Module, self.visit(tree))

        # Fix missing locations
        ast.fix_missing_locations(transformed)

        # Validate
        self._validate_tree(transformed)

        return transformed

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Transform function definition."""
        # Transform function name
        if self._should_transform_name(node.name):
            node.name = self._get_mangled_name(node.name)
            self._increment_transform_count()

        # Transform arguments
        for arg in node.args.args:
            if self._should_transform_name(arg.arg):
                arg.arg = self._get_mangled_name(arg.arg)
                self._increment_transform_count()

        # Transform kwonlyargs
        for arg in node.args.kwonlyargs:
            if self._should_transform_name(arg.arg):
                arg.arg = self._get_mangled_name(arg.arg)
                self._increment_transform_count()

        # Transform posonlyargs (Python 3.8+)
        for arg in node.args.posonlyargs:
            if self._should_transform_name(arg.arg):
                arg.arg = self._get_mangled_name(arg.arg)
                self._increment_transform_count()

        # Transform vararg and kwarg
        if node.args.vararg and self._should_transform_name(node.args.vararg.arg):
            node.args.vararg.arg = self._get_mangled_name(node.args.vararg.arg)
            self._increment_transform_count()

        if node.args.kwarg and self._should_transform_name(node.args.kwarg.arg):
            node.args.kwarg.arg = self._get_mangled_name(node.args.kwarg.arg)
            self._increment_transform_count()

        # Remove docstring if configured
        if self.config.remove_docstrings and node.body:
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                if isinstance(node.body[0].value.value, str):
                    # Remove docstring
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]

        # Visit children
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Transform async function definition."""
        # Same logic as regular function
        if self._should_transform_name(node.name):
            node.name = self._get_mangled_name(node.name)
            self._increment_transform_count()

        for arg in node.args.args:
            if self._should_transform_name(arg.arg):
                arg.arg = self._get_mangled_name(arg.arg)
                self._increment_transform_count()

        for arg in node.args.kwonlyargs:
            if self._should_transform_name(arg.arg):
                arg.arg = self._get_mangled_name(arg.arg)
                self._increment_transform_count()

        for arg in node.args.posonlyargs:
            if self._should_transform_name(arg.arg):
                arg.arg = self._get_mangled_name(arg.arg)
                self._increment_transform_count()

        if node.args.vararg and self._should_transform_name(node.args.vararg.arg):
            node.args.vararg.arg = self._get_mangled_name(node.args.vararg.arg)
            self._increment_transform_count()

        if node.args.kwarg and self._should_transform_name(node.args.kwarg.arg):
            node.args.kwarg.arg = self._get_mangled_name(node.args.kwarg.arg)
            self._increment_transform_count()

        if self.config.remove_docstrings and node.body:
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                if isinstance(node.body[0].value.value, str):
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]

        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Transform class definition."""
        if self._should_transform_name(node.name):
            node.name = self._get_mangled_name(node.name)
            self._increment_transform_count()

        # Remove class docstring
        if self.config.remove_docstrings and node.body:
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                if isinstance(node.body[0].value.value, str):
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]

        self.generic_visit(node)
        return node

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Transform name reference."""
        if self._should_transform_name(node.id):
            node.id = self._get_mangled_name(node.id)
            self._increment_transform_count()

        self.generic_visit(node)
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        """
        Transform attribute access.

        Transforms both the object and the attribute name if it's a method or class attribute.
        Examples:
        - obj.method -> I0.I1 (if method is obfuscatable)
        - ClassName.attr -> I2.I3 (if class attribute)
        - cls.attr -> I4.I5 (in classmethods)
        - self.__class__.attr -> self.__class__.I6
        """
        # Visit the value (object) first
        self.visit(node.value)

        if self.analyzer:
            # Check if this is a method call
            if node.attr in self.analyzer.method_names:
                if self._should_transform_name(node.attr):
                    node.attr = self._get_mangled_name(node.attr)
                    self._increment_transform_count()
            # Check if this is a class attribute access
            elif node.attr in self.analyzer.all_class_attributes:
                if self._should_transform_name(node.attr):
                    node.attr = self._get_mangled_name(node.attr)
                    self._increment_transform_count()

        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        """Transform function argument."""
        if self._should_transform_name(node.arg):
            node.arg = self._get_mangled_name(node.arg)
            self._increment_transform_count()

        self.generic_visit(node)
        return node

    def _generate_obfuscated_name(self) -> str:
        """
        Generate a new obfuscated name.

        Returns:
            str: Obfuscated name (e.g., "I0", "I1", "I2", ...)
        """
        name = f"{self.config.name_prefix}{self._counter}"
        self._counter += 1
        return name

    def _get_mangled_name(self, original_name: str) -> str:
        """
        Get or create mangled name for an original name.

        Args:
            original_name: Original identifier name

        Returns:
            str: Mangled name
        """
        if original_name not in self._name_map:
            self._name_map[original_name] = self._generate_obfuscated_name()
        return self._name_map[original_name]

    def get_name_mapping(self) -> Dict[str, str]:
        """
        Get the name mapping dictionary.

        Returns:
            Dict[str, str]: Original name -> Obfuscated name
        """
        return self._name_map.copy()
