"""Read-only compatibility checks for statically imported module objects.

Bindings are lexical candidates, not runtime identity proofs. Reassigned names
are deliberately ignored; dynamic imports and star imports are not resolved.
"""

from __future__ import annotations

import ast
from typing import Callable, Dict, List, Optional, Set, Union


class _Bindings(ast.NodeVisitor):
    """Collect one lexical scope without borrowing imports from child scopes."""

    def __init__(self, resolve_from: Callable[[ast.ImportFrom], Optional[str]]) -> None:
        self.resolve_from = resolve_from
        self.imports: Dict[str, str] = {}
        self.shadowed: Set[str] = set()

    def _bind(self, name: str, source: str) -> None:
        if name in self.imports and self.imports[name] != source:
            self.shadowed.add(name)
        self.imports[name] = source

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._bind(
                alias.asname or alias.name.split(".")[0],
                alias.name if alias.asname else alias.name.split(".")[0],
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = self.resolve_from(node)
        for alias in node.names:
            if alias.name != "*":
                name = alias.asname or alias.name
                if module is not None:
                    self._bind(name, f"{module}.{alias.name}" if module else alias.name)
                else:
                    self.shadowed.add(name)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.shadowed.add(node.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.shadowed.add(node.id)

    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        self.shadowed.add(node.name)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.shadowed.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        pass

    def visit_ListComp(
        self, node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]
    ) -> None:
        pass

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp


class ImportedAccessVisitor(ast.NodeVisitor):
    """Resolve dotted expressions through explicit imports in lexical scopes."""

    def __init__(
        self,
        resolve_from: Callable[[ast.ImportFrom], Optional[str]],
        attribute: Callable[[ast.Attribute, str], None],
        decorated_class: Callable[[ast.ClassDef], None],
    ) -> None:
        self.resolve_from = resolve_from
        self.attribute = attribute
        self.decorated_class = decorated_class
        self.scopes: List[Dict[str, Optional[str]]] = []
        self.scope_kinds: List[str] = []

    def resolve(self, node: ast.expr) -> Optional[str]:
        if isinstance(node, ast.Name):
            for scope in reversed(self.scopes):
                if node.id in scope:
                    return scope[node.id]
        elif isinstance(node, ast.Attribute):
            base = self.resolve(node.value)
            if base is not None:
                return f"{base}.{node.attr}"
        return None

    def _enter(self, body: List[ast.stmt], kind: str, args: Optional[ast.arguments] = None) -> None:
        bindings = _Bindings(self.resolve_from)
        for statement in body:
            bindings.visit(statement)
        if args:
            bindings.shadowed.update(a.arg for a in ast.walk(args) if isinstance(a, ast.arg))
        scope: Dict[str, Optional[str]] = dict(bindings.imports)
        scope.update({name: None for name in bindings.shadowed})
        previous_scopes, previous_kinds = self.scopes, self.scope_kinds
        # A child lexical scope cannot close over a class namespace.
        self.scopes = [s for s, k in zip(previous_scopes, previous_kinds) if k != "class"]
        self.scope_kinds = [k for k in previous_kinds if k != "class"]
        self.scopes.append(scope)
        self.scope_kinds.append(kind)
        for statement in body:
            self.visit(statement)
        self.scopes, self.scope_kinds = previous_scopes, previous_kinds

    def visit_Module(self, node: ast.Module) -> None:
        self._enter(node.body, "module")

    def visit_Attribute(self, node: ast.Attribute) -> None:
        module = self.resolve(node.value)
        if module is not None:
            self.attribute(node, module)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.decorated_class(node)
        for expression in [*node.decorator_list, *node.bases, *(k.value for k in node.keywords)]:
            self.visit(expression)
        self._enter(node.body, "class")

    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        for expression in [*node.decorator_list, *node.args.defaults, *node.args.kw_defaults]:
            if expression is not None:
                self.visit(expression)
        for argument in [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
            node.args.vararg,
            node.args.kwarg,
        ]:
            if argument is not None and argument.annotation is not None:
                self.visit(argument.annotation)
        if node.returns is not None:
            self.visit(node.returns)
        self._enter(node.body, "function", node.args)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for expression in [*node.args.defaults, *node.args.kw_defaults]:
            if expression is not None:
                self.visit(expression)
        previous_scopes, previous_kinds = self.scopes, self.scope_kinds
        self.scopes = [s for s, k in zip(previous_scopes, previous_kinds) if k != "class"]
        self.scope_kinds = [k for k in previous_kinds if k != "class"]
        self.scopes.append({a.arg: None for a in ast.walk(node.args) if isinstance(a, ast.arg)})
        self.scope_kinds.append("function")
        self.visit(node.body)
        self.scopes, self.scope_kinds = previous_scopes, previous_kinds

    def visit_ListComp(
        self, node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]
    ) -> None:
        # The first iterable is evaluated outside the comprehension scope.
        self.visit(node.generators[0].iter)
        names = {
            n.id for g in node.generators for n in ast.walk(g.target) if isinstance(n, ast.Name)
        }
        previous_scopes, previous_kinds = self.scopes, self.scope_kinds
        self.scopes = [s for s, k in zip(previous_scopes, previous_kinds) if k != "class"]
        self.scope_kinds = [k for k in previous_kinds if k != "class"]
        self.scopes.append({name: None for name in names})
        self.scope_kinds.append("function")
        for index, generator in enumerate(node.generators):
            if index:
                self.visit(generator.iter)
            for condition in generator.ifs:
                self.visit(condition)
        if isinstance(node, ast.DictComp):
            self.visit(node.key)
            self.visit(node.value)
        else:
            self.visit(node.elt)
        self.scopes, self.scope_kinds = previous_scopes, previous_kinds

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp


def enum_members(node: ast.ClassDef) -> List[str]:
    """List statically assigned public member candidates, in source order."""
    members: List[str] = []
    ignored: Set[str] = set()
    for statement in node.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
            if any(isinstance(t, ast.Name) and t.id == "_ignore_" for t in targets):
                try:
                    value = ast.literal_eval(statement.value)
                    ignored.update(value.split() if isinstance(value, str) else value)
                except (ValueError, TypeError):
                    pass
        elif isinstance(statement, ast.AnnAssign) and statement.value is not None:
            targets = [statement.target]
        else:
            continue
        for target in targets:
            for name in ast.walk(target):
                if (
                    isinstance(name, ast.Name)
                    and isinstance(name.ctx, ast.Store)
                    and not (name.id.startswith("_") and name.id.endswith("_") and len(name.id) > 1)
                    and name.id not in members
                ):
                    members.append(name.id)
    return [name for name in members if name not in ignored]
