"""
Local Name Transformer for Cross-file Obfuscation.

This module provides the LocalNameTransformer class which updates
references to locally-defined exported names within the same module.

For example, if a function is renamed from `run_demo` to `I2`, all
calls to `run_demo()` within the same file must be updated to `I2()`.
"""

import ast
from typing import Optional, Set, Tuple, List
from pathlib import Path

from pyobfus.core.generator import CodeGenerator
from pyobfus.core.global_table import GlobalSymbolTable


def _target_names(target: ast.expr, out: Set[str]) -> None:
    """Collect the names an assignment/for/with target binds (handles tuples/stars)."""
    if isinstance(target, ast.Name):
        out.add(target.id)
    elif isinstance(target, (ast.Tuple, ast.List)):
        for elt in target.elts:
            _target_names(elt, out)
    elif isinstance(target, ast.Starred):
        _target_names(target.value, out)
    # Attribute / Subscript targets bind no local name


class _ScopeBindingCollector(ast.NodeVisitor):
    """Collect the names bound in ONE function scope (Python function-scope semantics).

    A name assigned anywhere in a function body is local to that function, so it
    shadows a module-level symbol of the same name. This collector gathers those
    names -- assignments, augmented/annotated assignments, walrus targets, for /
    with / except targets, local imports, and the *names* of nested def/class
    definitions -- without descending into nested function/class/lambda or
    comprehension scopes (those are separate scopes). Names declared ``global``
    or ``nonlocal`` are excluded, since they resolve to an outer scope and must
    still be renamed.
    """

    def __init__(self) -> None:
        self.bound: Set[str] = set()
        self.declared_outer: Set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            _target_names(target, self.bound)
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        _target_names(node.target, self.bound)
        if node.value is not None:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        _target_names(node.target, self.bound)
        self.visit(node.value)

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:  # walrus :=
        _target_names(node.target, self.bound)
        self.visit(node.value)

    def visit_For(self, node) -> None:
        _target_names(node.target, self.bound)
        self.visit(node.iter)
        for stmt in node.body + node.orelse:
            self.visit(stmt)

    visit_AsyncFor = visit_For

    def visit_With(self, node) -> None:
        for item in node.items:
            if item.optional_vars is not None:
                _target_names(item.optional_vars, self.bound)
            self.visit(item.context_expr)
        for stmt in node.body:
            self.visit(stmt)

    visit_AsyncWith = visit_With

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.bound.add(node.name)
        for stmt in node.body:
            self.visit(stmt)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.bound.add((alias.asname or alias.name).split(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name != "*":
                self.bound.add(alias.asname or alias.name)

    def visit_Global(self, node: ast.Global) -> None:
        self.declared_outer.update(node.names)

    def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
        self.declared_outer.update(node.names)

    # Nested scopes: record the bound name but do not descend into their bodies.
    def visit_FunctionDef(self, node) -> None:
        self.bound.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.bound.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        pass  # own scope; binds nothing in the enclosing scope

    def visit_ListComp(self, node) -> None:
        pass

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp


def _function_scope_names(node) -> Set[str]:
    """All names local to a function/async-function scope (params + bound - global/nonlocal)."""
    names: Set[str] = set()
    args = node.args
    for arg in args.posonlyargs + args.args + args.kwonlyargs:
        names.add(arg.arg)
    if args.vararg:
        names.add(args.vararg.arg)
    if args.kwarg:
        names.add(args.kwarg.arg)
    collector = _ScopeBindingCollector()
    for stmt in node.body:
        collector.visit(stmt)
    return (names | collector.bound) - collector.declared_outer


class LocalNameTransformer(ast.NodeTransformer):
    """
    Transform local references to exported names.

    This transformer updates Name nodes that reference locally-defined
    exported symbols that have been renamed.

    Example:
        Original:
            def run_demo():
                pass

            if __name__ == "__main__":
                run_demo()  # <- needs to be updated

        After ExportedNameTransformer:
            def I2():
                pass

            if __name__ == "__main__":
                run_demo()  # <- still wrong!

        After LocalNameTransformer:
            def I2():
                pass

            if __name__ == "__main__":
                I2()  # <- correct!
    """

    def __init__(
        self,
        global_table: GlobalSymbolTable,
        current_module: str,
        imported_names: Optional[Set[str]] = None,
        current_file: Optional[Path] = None,
    ):
        """
        Initialize local name transformer.

        Args:
            global_table: Global symbol table with name mappings
            current_module: Name of current module (e.g., "calculator", "utils")
            imported_names: Set of names that were imported (to avoid renaming)
            current_file: Path to current file (optional, for tracking)
        """
        self.global_table = global_table
        self.current_module = current_module
        self.imported_names = imported_names or set()
        self.current_file = current_file

        # Get mappings for locally-defined exports in this module
        self.local_export_mappings = global_table.get_module_exports(current_module)

        # Track statistics
        self.names_renamed: int = 0
        self.names_unchanged: int = 0

        # Track local scopes (stack of sets of locally-bound names)
        self._local_scopes: List[Set[str]] = []

    def visit_Name(self, node: ast.Name) -> ast.Name:
        """
        Visit Name node and rename if it's a local exported name reference.

        Args:
            node: Name AST node

        Returns:
            Modified or original Name node
        """
        # Only rename in Load context (usage, not definition)
        if not isinstance(node.ctx, ast.Load):
            return node

        # Don't rename imported names (those are handled by ImportedNameTransformer)
        if node.id in self.imported_names:
            return node

        # Don't rename if shadowed by a local variable/parameter in any scope
        for local_scope in self._local_scopes:
            if node.id in local_scope:
                return node

        # Check if this is a local exported name
        obfuscated_name = self.local_export_mappings.get(node.id)
        if obfuscated_name:
            # Create new Name with obfuscated name
            new_node = ast.Name(id=obfuscated_name, ctx=node.ctx)
            ast.copy_location(new_node, node)
            self.names_renamed += 1
            return new_node
        else:
            self.names_unchanged += 1
            return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Visit function definition.

        We push a scope holding every name local to this function -- parameters
        AND names bound anywhere in its body -- so a local that reuses the name
        of a renamed module-level symbol is not rewritten (Python function-scope
        semantics; the parameter-only version wrongly renamed such locals).

        Args:
            node: FunctionDef AST node

        Returns:
            Modified or original FunctionDef node
        """
        # Decorators are evaluated in the enclosing scope, before the body scope.
        for decorator in node.decorator_list:
            self.visit(decorator)

        self._local_scopes.append(_function_scope_names(node))
        for stmt in node.body:
            self.visit(stmt)
        self._local_scopes.pop()

        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AsyncFunctionDef:
        """
        Visit async function definition. Same scope handling as visit_FunctionDef.

        Args:
            node: AsyncFunctionDef AST node

        Returns:
            Modified or original AsyncFunctionDef node
        """
        for decorator in node.decorator_list:
            self.visit(decorator)

        self._local_scopes.append(_function_scope_names(node))
        for stmt in node.body:
            self.visit(stmt)
        self._local_scopes.pop()

        return node

    def visit_Lambda(self, node: ast.Lambda) -> ast.Lambda:
        """A lambda is its own scope; its parameters shadow module-level names."""
        args = node.args
        params: Set[str] = {a.arg for a in args.posonlyargs + args.args + args.kwonlyargs}
        if args.vararg:
            params.add(args.vararg.arg)
        if args.kwarg:
            params.add(args.kwarg.arg)
        # Defaults are evaluated in the enclosing scope.
        for default in args.defaults + [d for d in args.kw_defaults if d is not None]:
            self.visit(default)
        self._local_scopes.append(params)
        self.visit(node.body)
        self._local_scopes.pop()
        return node

    def _visit_comprehension(self, node):
        """List/set/dict/generator comprehensions are their own scope in Python 3;
        their loop targets shadow module-level names."""
        targets: Set[str] = set()
        for generator in node.generators:
            _target_names(generator.target, targets)
        self._local_scopes.append(targets)
        self.generic_visit(node)
        self._local_scopes.pop()
        return node

    visit_ListComp = _visit_comprehension
    visit_SetComp = _visit_comprehension
    visit_DictComp = _visit_comprehension
    visit_GeneratorExp = _visit_comprehension

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """
        Visit class definition.

        Args:
            node: ClassDef AST node

        Returns:
            Modified or original ClassDef node
        """
        # Visit body (rename local references in methods)
        for stmt in node.body:
            self.visit(stmt)

        # Visit decorators and base classes
        for decorator in node.decorator_list:
            self.visit(decorator)
        for base in node.bases:
            self.visit(base)
        for keyword in node.keywords:
            self.visit(keyword.value)

        return node

    def get_statistics(self) -> dict:
        """
        Get statistics about name transformation.

        Returns:
            Dictionary with:
            - names_renamed: Number of name references renamed
            - names_unchanged: Number of name references left unchanged
        """
        return {
            "names_renamed": self.names_renamed,
            "names_unchanged": self.names_unchanged,
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"LocalNameTransformer(module={self.current_module}, "
            f"renamed={self.names_renamed}, "
            f"unchanged={self.names_unchanged})"
        )


def transform_local_names(
    source: str,
    global_table: GlobalSymbolTable,
    current_module: str,
    imported_names: Optional[Set[str]] = None,
    current_file: Optional[Path] = None,
) -> Tuple[str, dict]:
    """
    Convenience function to transform local name references in source code.

    Args:
        source: Python source code
        global_table: Global symbol table with name mappings
        current_module: Name of current module
        imported_names: Set of imported names to avoid renaming
        current_file: Path to current file (optional)

    Returns:
        Tuple of (transformed_source, statistics)

    Example:
        >>> table = GlobalSymbolTable()
        >>> table.register_export("main", "run_demo", "I2")
        >>> source = "def I2():\\n    pass\\nif __name__ == '__main__':\\n    run_demo()"
        >>> new_source, stats = transform_local_names(source, table, "main")
        >>> print(new_source)
        def I2():
            pass
        if __name__ == '__main__':
            I2()
    """
    tree = ast.parse(source)
    transformer = LocalNameTransformer(global_table, current_module, imported_names, current_file)
    new_tree = transformer.visit(tree)

    # Fix missing locations
    ast.fix_missing_locations(new_tree)

    # Convert back to source (use CodeGenerator for Python 3.8 compatibility)
    new_source = CodeGenerator.generate(new_tree)

    return new_source, transformer.get_statistics()
