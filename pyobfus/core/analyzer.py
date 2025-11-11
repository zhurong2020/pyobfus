"""
Symbol table analyzer for identifying names to obfuscate.

Analyzes AST to build a symbol table of all identifiers,
categorizes them (local, global, import, builtin), and
determines which names can be safely obfuscated.
"""

import ast
from collections import defaultdict
from typing import Dict, Set

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

        # Obfuscatable names (filtered list)
        self.obfuscatable_names: Set[str] = set()

        # Name usage counts (for statistics)
        self.name_usage: Dict[str, int] = defaultdict(int)

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

        self.generic_visit(node)

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
        """
        # Start with all local names
        candidates = self.local_names.copy()

        # Remove imported names
        candidates -= self.imported_names

        # Remove globally excluded names from config
        candidates -= self.config.exclude_names

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
