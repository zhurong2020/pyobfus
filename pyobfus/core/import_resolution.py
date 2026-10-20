"""Shared lexical import candidates. These are observations, never identity proofs."""

from __future__ import annotations

import ast
from typing import Callable, Dict, List, Optional, Set, Union


class _Bindings(ast.NodeVisitor):
    """Collect one lexical scope without borrowing imports from child scopes."""

    def __init__(self, resolve_from: Callable[[ast.ImportFrom], Optional[str]]) -> None:
        self.resolve_from = resolve_from
        self.imports: Dict[str, str] = {}
        self.import_candidates: Dict[str, Set[str]] = {}
        self.shadowed: Set[str] = set()

    def _bind(self, name: str, source: str) -> None:
        self.import_candidates.setdefault(name, set()).add(source)
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

    def visit_MatchAs(self, node: ast.AST) -> None:
        name = getattr(node, "name", None)
        if name:
            self.shadowed.add(name)
        self.generic_visit(node)

    visit_MatchStar = visit_MatchAs

    def visit_MatchMapping(self, node: ast.AST) -> None:
        rest = getattr(node, "rest", None)
        if rest:
            self.shadowed.add(rest)
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
        scope = self._candidate_scope(body, bindings)
        previous_scopes, previous_kinds = self.scopes, self.scope_kinds
        # A child lexical scope cannot close over a class namespace.
        self.scopes = [s for s, k in zip(previous_scopes, previous_kinds) if k != "class"]
        self.scope_kinds = [k for k in previous_kinds if k != "class"]
        self.scopes.append(scope)
        self.scope_kinds.append(kind)
        for statement in body:
            self.visit(statement)
        self.scopes, self.scope_kinds = previous_scopes, previous_kinds

    def _candidate_scope(
        self, body: List[ast.stmt], bindings: _Bindings
    ) -> Dict[str, Optional[str]]:
        scope: Dict[str, Optional[str]] = dict(bindings.imports)
        scope.update({name: None for name in bindings.shadowed})
        return scope

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
            if node.key is not None:
                self.visit(node.key)
            if node.value is not None:
                self.visit(node.value)
        else:
            self.visit(node.elt)
        self.scopes, self.scope_kinds = previous_scopes, previous_kinds

    visit_SetComp = visit_ListComp
    visit_DictComp = visit_ListComp
    visit_GeneratorExp = visit_ListComp


def discover_accesses(
    tree: ast.AST, resolve_from: Callable[[ast.ImportFrom], Optional[str]]
) -> List[tuple]:
    """Return legacy lexical candidates without making runtime identity claims."""
    accesses: List[tuple] = []
    ImportedAccessVisitor(
        resolve_from, lambda node, module: accesses.append((node, module)), lambda node: None
    ).visit(tree)
    return accesses


class _UncertainAccessVisitor(ImportedAccessVisitor):
    """Diagnostic observations only; competing stores cannot supply an edit.

    Keep imports in their own lexical scope despite competing bindings. An
    unrelated local/parameter still blocks borrowing an outer import. Literal
    dynamic-import results are candidates, never statically proved identities.
    """

    def __init__(self, *args, resolve_member=None) -> None:
        super().__init__(*args)
        self.resolve_member = resolve_member
        self.alternatives: Dict[int, Dict[str, Set[str]]] = {}
        self.observed_scopes: List[Dict[str, Optional[str]]] = []

    def _members(self, bases: Set[str], name: str) -> Set[str]:
        candidates = {f"{base}.{name}" for base in bases}
        if self.resolve_member is not None:
            for base in bases:
                candidates.update(self.resolve_member(base, name))
        return candidates

    def _resolve_candidates(self, node: ast.expr) -> Set[str]:
        if isinstance(node, ast.Name):
            for scope in reversed(self.scopes):
                if node.id in scope:
                    candidates = self.alternatives.get(id(scope), {}).get(node.id)
                    if candidates is not None:
                        return candidates
                    target = scope[node.id]
                    return {target} if target else set()
        if isinstance(node, ast.Attribute):
            return self._members(self._resolve_candidates(node.value), node.attr)
        return set()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        for module in sorted(self._resolve_candidates(node.value)):
            self.attribute(node, module)
        self.generic_visit(node)

    def _candidate_scope(
        self, body: List[ast.stmt], bindings: _Bindings
    ) -> Dict[str, Optional[str]]:
        scope = super()._candidate_scope(body, bindings)
        scope.update(bindings.imports)
        alternatives = {name: set(targets) for name, targets in bindings.import_candidates.items()}

        def candidates(node: ast.expr) -> Set[str]:
            if isinstance(node, ast.Name):
                if node.id in scope:
                    return alternatives.get(node.id, set())
                for outer, kind in reversed(list(zip(self.scopes, self.scope_kinds))):
                    if kind != "class" and node.id in outer:
                        known = self.alternatives.get(id(outer), {}).get(node.id)
                        target = outer[node.id]
                        return known if known is not None else ({target} if target else set())
            if isinstance(node, ast.Attribute):
                return self._members(candidates(node.value), node.attr)
            return set()

        def walk(node: ast.AST) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                return
            if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                observed = candidates(value)
                if (
                    isinstance(value, ast.Call)
                    and value.args
                    and "importlib.import_module" in candidates(value.func)
                ):
                    name = value.args[0]
                    if (
                        isinstance(name, ast.Constant)
                        and isinstance(name.value, str)
                        and not name.value.startswith(".")
                    ):
                        observed.add(name.value)
                for assigned in targets:
                    if isinstance(assigned, ast.Name) and observed:
                        scope[assigned.id] = sorted(observed)[0]
                        alternatives.setdefault(assigned.id, set()).update(observed)
            for child in ast.iter_child_nodes(node):
                walk(child)

        for statement in body:
            walk(statement)
        self.observed_scopes.append(scope)
        self.alternatives[id(scope)] = alternatives
        return scope


def discover_uncertain_accesses(
    tree: ast.AST,
    resolve_from: Callable[[ast.ImportFrom], Optional[str]],
    resolve_member: Optional[Callable[[str, str], Set[str]]] = None,
) -> List[tuple]:
    """Broader same-scope import candidates exclusively for preservation advice."""
    accesses: List[tuple] = []
    _UncertainAccessVisitor(
        resolve_from,
        lambda node, module: accesses.append((node, module)),
        lambda node: None,
        resolve_member=resolve_member,
    ).visit(tree)
    return accesses


def discover_module_bindings(
    tree: ast.Module, resolve_from: Callable[[ast.ImportFrom], Optional[str]]
) -> Dict[str, Set[str]]:
    """Observe module-scope import/assignment candidates, never identity proofs."""
    bindings = _Bindings(resolve_from)
    for statement in tree.body:
        bindings.visit(statement)
    visitor = _UncertainAccessVisitor(resolve_from, lambda node, module: None, lambda node: None)
    scope = visitor._candidate_scope(tree.body, bindings)
    return visitor.alternatives[id(scope)]
