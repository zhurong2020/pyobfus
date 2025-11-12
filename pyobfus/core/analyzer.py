"""
Symbol table analyzer for identifying names to obfuscate.

Analyzes AST to build a symbol table of all identifiers,
categorizes them (local, global, import, builtin), and
determines which names can be safely obfuscated.
"""

import ast
from collections import defaultdict
from typing import Dict, Set, Optional

from pyobfus.config import ObfuscationConfig


class SymbolAnalyzer(ast.NodeVisitor):
    """
    Analyzes Python AST to identify symbols that can be obfuscated.

    Collects all name definitions and usages, tracks scope,
    and excludes names that should not be obfuscated.
    """

    def __init__(self, config: ObfuscationConfig):
        """
        Initialize symbol analyzer.

        Args:
            config: Obfuscation configuration
        """
        self.config = config

        # Symbol tables
        self.local_names: Set[str] = set()  # Local variables, functions, classes
        self.global_names: Set[str] = set()  # Global variables
        self.imported_names: Set[str] = set()  # Imported modules/functions
        self.builtin_names: Set[str] = set()  # Python builtins
        self.method_names: Set[str] = set()  # Class method names
        self.class_attributes: Dict[str, Set[str]] = defaultdict(set)  # Class -> {attributes}
        self.all_class_attributes: Set[str] = set()  # All class attribute names

        # Public API detection
        self.public_api_names: Set[str] = set()  # Auto-detected public APIs
        self.names_with_docstrings: Set[str] = set()  # Names with docstrings
        self.names_in_all: Set[str] = set()  # Names in __all__

        # Obfuscatable names (filtered list)
        self.obfuscatable_names: Set[str] = set()

        # Name usage counts (for statistics)
        self.name_usage: Dict[str, int] = defaultdict(int)

        # Track if we're currently inside a class definition
        self._in_class = False
        self._current_class_name: Optional[str] = None  # Track current class being analyzed
        self._auto_detect_public = False  # Enable auto-detection

    def enable_auto_detection(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic public API detection.

        Args:
            enabled: Whether to enable auto-detection
        """
        self._auto_detect_public = enabled

    def analyze(self, tree: ast.Module) -> None:
        """
        Analyze an AST module to build symbol tables.

        Args:
            tree: AST module to analyze
        """
        # Visit all nodes in the tree
        self.visit(tree)

        # Build obfuscatable names set
        self._build_obfuscatable_names()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        # Add function name
        if not self.config.should_exclude_name(node.name):
            self.local_names.add(node.name)
            self.name_usage[node.name] += 1
            # Track method names (functions defined inside classes)
            if self._in_class:
                self.method_names.add(node.name)

            # Auto-detect public API
            if self._auto_detect_public:
                # Public if: has docstring, doesn't start with _, or is called from __main__
                has_docstring = (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                )

                if has_docstring:
                    self.names_with_docstrings.add(node.name)

                # Public methods: don't start with _ (unless __magic__)
                is_public = not node.name.startswith("_") or (
                    node.name.startswith("__") and node.name.endswith("__")
                )

                if is_public or has_docstring:
                    self.public_api_names.add(node.name)

        # Visit arguments
        for arg in node.args.args:
            if not self.config.should_exclude_name(arg.arg):
                self.local_names.add(arg.arg)
                self.name_usage[arg.arg] += 1

        # Visit defaults, decorator, body
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        # Same as regular function
        if not self.config.should_exclude_name(node.name):
            self.local_names.add(node.name)
            self.name_usage[node.name] += 1
            # Track method names (functions defined inside classes)
            if self._in_class:
                self.method_names.add(node.name)

        for arg in node.args.args:
            if not self.config.should_exclude_name(arg.arg):
                self.local_names.add(arg.arg)
                self.name_usage[arg.arg] += 1

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        if not self.config.should_exclude_name(node.name):
            self.local_names.add(node.name)
            self.name_usage[node.name] += 1

        # Set flag to track that we're inside a class
        old_in_class = self._in_class
        old_class_name = self._current_class_name
        self._in_class = True
        self._current_class_name = node.name

        # Analyze class body for class-level attributes
        for item in node.body:
            if isinstance(item, ast.Assign):
                # Class-level assignment
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attr_name = target.id
                        if not self.config.should_exclude_name(attr_name):
                            self.class_attributes[node.name].add(attr_name)
                            self.all_class_attributes.add(attr_name)
            elif isinstance(item, ast.AnnAssign):
                # Annotated class-level assignment
                if isinstance(item.target, ast.Name):
                    attr_name = item.target.id
                    if not self.config.should_exclude_name(attr_name):
                        self.class_attributes[node.name].add(attr_name)
                        self.all_class_attributes.add(attr_name)

        self.generic_visit(node)
        self._in_class = old_in_class
        self._current_class_name = old_class_name

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name reference."""
        name = node.id
        if not self.config.should_exclude_name(name):
            self.name_usage[name] += 1

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment statement."""
        # Extract target names
        for target in node.targets:
            if isinstance(target, ast.Name):
                if not self.config.should_exclude_name(target.id):
                    self.local_names.add(target.id)
                    self.name_usage[target.id] += 1
            elif isinstance(target, ast.Tuple) or isinstance(target, ast.List):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        if not self.config.should_exclude_name(elt.id):
                            self.local_names.add(elt.id)
                            self.name_usage[elt.id] += 1

        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignment."""
        if isinstance(node.target, ast.Name):
            if not self.config.should_exclude_name(node.target.id):
                self.local_names.add(node.target.id)
                self.name_usage[node.target.id] += 1

        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        """Visit for loop."""
        # Extract loop variable
        if isinstance(node.target, ast.Name):
            if not self.config.should_exclude_name(node.target.id):
                self.local_names.add(node.target.id)
                self.name_usage[node.target.id] += 1
        elif isinstance(node.target, ast.Tuple):
            for elt in node.target.elts:
                if isinstance(elt, ast.Name):
                    if not self.config.should_exclude_name(elt.id):
                        self.local_names.add(elt.id)
                        self.name_usage[elt.id] += 1

        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Visit with statement."""
        # Extract context manager variables
        for item in node.items:
            if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                if not self.config.should_exclude_name(item.optional_vars.id):
                    self.local_names.add(item.optional_vars.id)
                    self.name_usage[item.optional_vars.id] += 1

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            # Use alias name if present, otherwise module name
            name = alias.asname if alias.asname else alias.name.split(".")[0]
            self.imported_names.add(name)

        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statement."""
        for alias in node.names:
            if alias.name == "*":
                # Can't track star imports reliably
                continue
            name = alias.asname if alias.asname else alias.name
            self.imported_names.add(name)

        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        """Visit global statement."""
        for name in node.names:
            self.global_names.add(name)

        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        """Visit nonlocal statement."""
        # Treat nonlocal similar to local for obfuscation purposes
        for name in node.names:
            if not self.config.should_exclude_name(name):
                self.local_names.add(name)

        self.generic_visit(node)

    def _build_obfuscatable_names(self) -> None:
        """
        Build the set of names that can be safely obfuscated.

        Excludes:
        - Imported names
        - Names in config.exclude_names
        - Magic methods (__xxx__)
        - Python builtins
        - Auto-detected public APIs (if enabled)
        """
        # Start with all local names
        candidates = self.local_names.copy()

        # Remove imported names
        candidates -= self.imported_names

        # Remove globally excluded names from config
        candidates -= self.config.exclude_names

        # Remove auto-detected public APIs if enabled
        if self._auto_detect_public:
            candidates -= self.public_api_names

        # Remove any remaining magic methods (shouldn't be any, but double-check)
        candidates = {
            name for name in candidates if not (name.startswith("__") and name.endswith("__"))
        }

        self.obfuscatable_names = candidates

    def get_obfuscatable_names(self) -> Set[str]:
        """
        Get the set of names that can be obfuscated.

        Returns:
            Set[str]: Names that can be safely obfuscated
        """
        return self.obfuscatable_names.copy()

    def get_statistics(self) -> Dict[str, int]:
        """
        Get analysis statistics.

        Returns:
            Dict with counts of various name categories
        """
        return {
            "total_names": len(self.local_names),
            "obfuscatable_names": len(self.obfuscatable_names),
            "imported_names": len(self.imported_names),
            "global_names": len(self.global_names),
            "excluded_names": len(self.local_names) - len(self.obfuscatable_names),
        }
