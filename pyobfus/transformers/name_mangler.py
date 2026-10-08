"""
Name mangling transformer for obfuscating identifiers.

Renames variables, functions, and classes to short, meaningless names
like I0, I1, I2, etc.
"""

import ast
from typing import Dict, Optional, Set, cast

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.transformer import BaseTransformer


def _function_nested_definition_names(tree: ast.Module) -> Set[str]:
    """Collect definitions whose immediate lexical parent is a function.

    Control-flow suites do not introduce scopes. A class body does, so its
    methods/nested classes remain eligible even if that class is in a function.
    Definitions inside a method's body are function-local and are preserved.
    """
    names: Set[str] = set()

    class Scan(ast.NodeVisitor):
        scope = "module"

        def definition(self, node, scope: str) -> None:
            if self.scope == "function":
                names.add(node.name)
            previous = self.scope
            self.scope = scope
            self.generic_visit(node)
            self.scope = previous

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.definition(node, "function")

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.definition(node, "function")

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.definition(node, "class")

    Scan().visit(tree)
    return names


def _class_annotated_field_names(tree: ast.Module) -> Set[str]:
    """Preserve annotation-driven APIs without a framework allowlist.

    Only Name targets evaluated in a class body qualify. Method-local and
    module annotations, and Attribute/Subscript targets, keep their policy.
    Control-flow suites retain their scope; nested classes start a class scope.
    """
    names: Set[str] = set()

    class Scan(ast.NodeVisitor):
        in_class = False

        def scope(self, node: ast.AST, in_class: bool) -> None:
            previous = self.in_class
            self.in_class = in_class
            self.generic_visit(node)
            self.in_class = previous

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            self.scope(node, True)

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            self.scope(node, False)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            self.scope(node, False)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if self.in_class and isinstance(node.target, ast.Name):
                names.add(node.target.id)
            self.generic_visit(node)

    Scan().visit(tree)
    return names


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
        self._preserved_names: Set[str] = set()

    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform all obfuscatable names in the AST.

        Args:
            tree: AST module to transform

        Returns:
            ast.Module: Transformed AST with mangled names
        """
        # __name__ is observable in Flask endpoints, Click commands and
        # registries. The mapping is file-wide, so preserve each such spelling
        # everywhere, including same-named module definitions and references.
        # Class annotation names also define generated field/serialization APIs.
        self._preserved_names = _function_nested_definition_names(
            tree
        ) | _class_annotated_field_names(tree)

        # Build name mapping
        if self.analyzer:
            # Filter out parameter names if preserve_param_names is enabled
            names_to_obfuscate = self.analyzer.obfuscatable_names - self._preserved_names
            if self.config.preserve_param_names:
                names_to_obfuscate = names_to_obfuscate - self.analyzer.parameter_names

            for name in sorted(names_to_obfuscate):
                self._name_map[name] = self._generate_obfuscated_name()

        # Transform the tree
        transformed = cast(ast.Module, self.visit(tree))

        # Fix missing locations
        ast.fix_missing_locations(transformed)

        # Validate
        self._validate_tree(transformed)

        return transformed

    def _should_transform_name(self, name: str) -> bool:
        """Enforce preservation for visits and analyzer-free transforms too."""
        return name not in self._preserved_names and super()._should_transform_name(name)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Transform function definition."""
        # Transform function name
        if self._should_transform_name(node.name):
            node.name = self._get_mangled_name(node.name)
            self._increment_transform_count()

        # Remove docstring if configured
        if self.config.remove_docstrings and node.body:
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                if isinstance(node.body[0].value.value, str):
                    # Remove docstring
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]

        # Visit children (including args, which will be handled by visit_arg)
        self.generic_visit(node)
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """Transform async function definition."""
        # Transform function name
        if self._should_transform_name(node.name):
            node.name = self._get_mangled_name(node.name)
            self._increment_transform_count()

        # Remove docstring if configured
        if self.config.remove_docstrings and node.body:
            if isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                if isinstance(node.body[0].value.value, str):
                    node.body = node.body[1:] if len(node.body) > 1 else [ast.Pass()]

        # Visit children (including args, which will be handled by visit_arg)
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
        """Transform function argument (skip if preserve_param_names is enabled)."""
        if not self.config.preserve_param_names:
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
        while True:
            name = f"{self.config.name_prefix}{self._counter}"
            self._counter += 1
            if name not in self._preserved_names:
                return name

    def _get_mangled_name(self, original_name: str) -> str:
        """
        Get or create mangled name for an original name.

        Args:
            original_name: Original identifier name

        Returns:
            str: Mangled name or original name if it's a preserved parameter
        """
        # If preserve_param_names is enabled and this is a parameter, return original name
        if (
            self.config.preserve_param_names
            and self.analyzer
            and original_name in self.analyzer.parameter_names
        ):
            return original_name

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
