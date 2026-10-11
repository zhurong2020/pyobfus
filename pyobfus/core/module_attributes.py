"""Conservative module identity proofs and immutable original-AST edit plans.

PR 1 accepts only absolute from-package submodules and dotted imports with an
explicit alias. Lexical candidates remain a separate, deliberately broader API.
No target code is imported, and no names are allocated here.
"""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.core.import_resolution import ImportedAccessVisitor, _Bindings, discover_accesses

Span = Tuple[int, int, int, int]


def span(node: ast.Attribute) -> Span:
    return (node.lineno, node.col_offset, node.end_lineno or 0, node.end_col_offset or 0)


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class AttributeEdit:
    scope: str
    binding: str
    location: Span
    expected: str
    module: str
    emitted: str


@dataclass(frozen=True)
class AttributePlan:
    relative_file: str
    digest: str
    edits: Tuple[AttributeEdit, ...] = ()


def apply_attribute_plan(
    tree: ast.AST, source: str, relative_file: str, plan: AttributePlan
) -> None:
    """Validate every site before changing any node; failure is a build error."""
    if plan.relative_file != relative_file or source_hash(source) != plan.digest:
        raise ValueError("Module attribute plan source/path mismatch")
    nodes = {span(n): n for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    matched = []
    seen: Set[Span] = set()
    for edit in plan.edits:
        node = nodes.get(edit.location)
        if (
            edit.location in seen
            or node is None
            or node.attr != edit.expected
            or not isinstance(node.ctx, ast.Load)
            or not isinstance(node.value, ast.Name)
            or node.value.id != edit.binding
        ):
            raise ValueError("Module attribute plan coordinate/binding mismatch")
        seen.add(edit.location)
        matched.append((node, edit.emitted))
    for node, emitted in matched:
        node.attr = emitted


def _scope_nodes(body: List[ast.stmt]) -> List[ast.AST]:
    """Walk one binding scope; nested scopes are collected separately."""
    nodes: List[ast.AST] = []

    def walk(node: ast.AST) -> None:
        nodes.append(node)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            return
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            return
        for child in ast.iter_child_nodes(node):
            walk(child)

    for statement in body:
        walk(statement)
    return nodes


def _inert(statement: ast.stmt) -> bool:
    if isinstance(statement, ast.Pass):
        return True
    if isinstance(statement, ast.Expr):
        return isinstance(statement.value, ast.Constant)
    if isinstance(statement, (ast.Assign, ast.AnnAssign)):
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        try:
            ast.literal_eval(statement.value)  # type: ignore[arg-type]
            return all(isinstance(t, ast.Name) for t in targets)
        except (ValueError, TypeError):
            return False
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return (
            not statement.decorator_list
            and not statement.args.defaults
            and not any(statement.args.kw_defaults)
            and not statement.returns
            and not any(a.annotation for a in ast.walk(statement.args) if isinstance(a, ast.arg))
            and not getattr(statement, "type_params", [])
        )
    return False


@dataclass(frozen=True)
class _Binding:
    scope: str
    module: str
    position: Tuple[int, int]
    global_ready: bool


class ModuleInventory:
    """Selected project files, ordinary package roots, cycles and hazards."""

    def __init__(
        self, sources: Dict[str, str], resolve_from: Callable[[str, ast.ImportFrom], Optional[str]]
    ) -> None:
        self.trees = {module: ast.parse(source) for module, source in sources.items()}
        self.packages = {
            module[: -len(".__init__")]: tree
            for module, tree in self.trees.items()
            if module.endswith(".__init__")
        }
        self.resolve_from = resolve_from
        self.unsafe: Set[str] = set()
        self.edges: Dict[str, Set[str]] = {module: set() for module in self.trees}
        for module, tree in self.trees.items():
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.edges[module].update(a.name for a in node.names if a.name in self.trees)
                elif isinstance(node, ast.ImportFrom):
                    base = resolve_from(module, node)
                    if base:
                        for name in [base, *(f"{base}.{a.name}" for a in node.names)]:
                            canonical = f"{name}.__init__" if name in self.packages else name
                            if canonical in self.trees:
                                self.edges[module].add(canonical)
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "__getattr__"
                ):
                    self.unsafe.add(module)
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id in {"exec", "eval"}
                ):
                    self.unsafe.add(module)
            parts = module.split(".")
            for index in range(1, len(parts)):
                package = ".".join(parts[:index]) + ".__init__"
                if package in self.trees and package != module:
                    self.edges[module].add(package)
        self.cyclic: Set[str] = set()
        for module in self.trees:
            pending = list(self.edges[module])
            visited: Set[str] = set()
            while pending:
                target = pending.pop()
                if target == module:
                    self.cyclic.add(module)
                    break
                if target not in visited:
                    visited.add(target)
                    pending.extend(self.edges.get(target, ()))
        # Observe mutation/escape hazards using lexical candidates, without
        # upgrading any such candidate to a proof. Escapes get new advice in PR 2.
        for module, tree in self.trees.items():
            parents = {
                child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)
            }
            inventory = self

            class Hazards(ImportedAccessVisitor):
                def visit_Name(self, node: ast.Name) -> None:
                    target = self.resolve(node)
                    parent = parents.get(node)
                    if target in inventory.trees and isinstance(node.ctx, ast.Load):
                        if not isinstance(parent, ast.Attribute) or parent.attr == "__dict__":
                            inventory.unsafe.add(target)

                def visit_Attribute(self, node: ast.Attribute) -> None:
                    target = self.resolve(node.value)
                    if target in inventory.trees and not isinstance(node.ctx, ast.Load):
                        inventory.unsafe.add(target)
                    path = self.resolve(node)
                    if path in inventory.trees and not isinstance(node.ctx, ast.Load):
                        inventory.unsafe.add(path)
                    self.generic_visit(node)

            Hazards(
                lambda node: resolve_from(module, node), lambda n, m: None, lambda n: None
            ).visit(tree)
            # Recognizable module registry replacement defeats every direct proof.
            if any(
                isinstance(n, ast.Subscript)
                and not isinstance(n.ctx, ast.Load)
                and isinstance(n.value, ast.Attribute)
                and n.value.attr == "modules"
                for n in ast.walk(tree)
            ):
                self.unsafe.update(self.trees)

    def eligible(self, module: str, importer: str) -> bool:
        if module not in self.trees or module.endswith(".__init__") or module in self.packages:
            return False
        if (
            module in self.unsafe
            or importer in self.unsafe
            or module in self.cyclic
            or importer in self.cyclic
        ):
            return False
        parts = module.split(".")
        # Namespace packages and colliding file/package roots are unsupported.
        for index in range(1, len(parts)):
            package = ".".join(parts[:index])
            tree = self.packages.get(package)
            if tree is None or package in self.trees or f"{package}.__init__" in self.cyclic:
                return False
            # PR 1 does not prove re-exporting or executable package initializers.
            if any(
                not _inert(n) or isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                for n in tree.body
            ):
                return False
            child = parts[index]
            if any(
                isinstance(n, ast.Name)
                and isinstance(n.ctx, (ast.Store, ast.Del))
                and n.id == child
                for n in ast.walk(tree)
            ):
                return False
        return True


@dataclass(frozen=True)
class AccessResolution:
    """Separate a lexical candidate from a proved identity and optional edit."""

    location: Span
    candidate_module: str
    proved_module: Optional[str]
    reason: str
    edit: Optional[AttributeEdit] = None


class _ProofVisitor(ImportedAccessVisitor):
    """Reuse candidate traversal, but prove only direct, stable Name bases."""

    def __init__(
        self, tree: ast.Module, module: str, inventory: ModuleInventory, table: GlobalSymbolTable
    ) -> None:
        super().__init__(
            lambda node: inventory.resolve_from(module, node), self._attribute, lambda n: None
        )
        self.module = module
        self.inventory = inventory
        self.table = table
        self.details: Dict[Tuple[int, str], _Binding] = {}
        self.resolutions: Dict[Span, AccessResolution] = {}
        self.function_positions: List[Tuple[int, int]] = []
        self.forbidden = {
            name
            for n in ast.walk(tree)
            if isinstance(n, (ast.Global, ast.Nonlocal))
            for name in n.names
        }
        # Existing flat import synchronization (limitation I) cannot safely
        # share this spelling with a renamed direct-symbol import in a child
        # scope. Reject the H proof rather than claiming that prerequisite fixed.
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                source = self.resolve_from(node)
                if source:
                    self.forbidden.update(
                        alias.name
                        for alias in node.names
                        if alias.asname is None and table.get_obfuscated_import(source, alias.name)
                    )
        self.unsupported = any(
            isinstance(n, ast.NamedExpr)
            or getattr(n, "type_params", [])
            or type(n).__name__ == "TypeAlias"
            or (
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in {"exec", "eval"}
            )
            for n in ast.walk(tree)
        )

    def _enter(self, body: List[ast.stmt], kind: str, args: Optional[ast.arguments] = None) -> None:
        bindings = _Bindings(self.resolve_from)
        for statement in body:
            bindings.visit(statement)
        if args:
            bindings.shadowed.update(a.arg for a in ast.walk(args) if isinstance(a, ast.arg))
        nodes = _scope_nodes(body)
        for n in nodes:
            if type(n).__name__ in {"MatchAs", "MatchStar", "MatchMapping"}:
                bindings.shadowed.update(
                    value for value in [getattr(n, "name", None), getattr(n, "rest", None)] if value
                )
        scope: Dict[str, Optional[str]] = {
            name: None for name in bindings.shadowed | set(bindings.imports)
        }
        imports: Dict[str, List[ast.stmt]] = {}
        for n in nodes:
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for alias in n.names:
                    name = alias.asname or alias.name.split(".")[0]
                    imports.setdefault(name, []).append(n)
                    scope.setdefault(name, None)
        if any(
            isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names) for n in nodes
        ):
            bindings.shadowed.update(bindings.imports)
        scope_id = f"{kind}:{body[0].lineno if body else 0}:{body[0].col_offset if body else 0}"
        for statement in body:
            if not isinstance(statement, (ast.Import, ast.ImportFrom)) or kind == "class":
                continue
            for alias in statement.names:
                name = alias.asname or alias.name.split(".")[0]
                if name in bindings.shadowed or name in self.forbidden or len(imports[name]) != 1:
                    continue
                target = None
                if isinstance(statement, ast.Import) and alias.asname and "." in alias.name:
                    target = alias.name
                elif (
                    isinstance(statement, ast.ImportFrom)
                    and statement.level == 0
                    and statement.module in self.inventory.packages
                    and alias.name != "*"
                    and self.table.get_obfuscated_import(statement.module, alias.name) is None
                ):
                    target = f"{statement.module}.{alias.name}"
                if target and self.inventory.eligible(target, self.module):
                    scope[name] = target
                    prefix = body[: body.index(statement)]
                    ready = all(
                        _inert(s) or isinstance(s, (ast.Import, ast.ImportFrom)) for s in prefix
                    )
                    self.details[(id(scope), name)] = _Binding(
                        scope_id, target, (statement.lineno, statement.col_offset), ready
                    )
        previous_scopes, previous_kinds = self.scopes, self.scope_kinds
        # Function closures need a separate initialization proof (not PR 1).
        keep = [i for i, k in enumerate(previous_kinds) if k != "class"]
        outer_scopes: List[Dict[str, Optional[str]]] = []
        for i in keep:
            outer_scopes.append(
                previous_scopes[i]
                if previous_kinds[i] == "module"
                else {name: None for name in previous_scopes[i]}
            )
        self.scopes = outer_scopes + [scope]
        self.scope_kinds = [previous_kinds[i] for i in keep] + [kind]
        for statement in body:
            self.visit(statement)
        self.scopes, self.scope_kinds = previous_scopes, previous_kinds

    def _binding(self, node: ast.Name) -> Optional[_Binding]:
        for scope in reversed(self.scopes):
            if node.id in scope:
                if scope[node.id] is None:
                    return None
                binding = self.details.get((id(scope), node.id))
                if binding is None:
                    return None
                position = (node.lineno, node.col_offset)
                if scope is not self.scopes[-1]:
                    if not binding.global_ready or not self.function_positions:
                        return None
                    position = min(position, self.function_positions[0])
                return binding if position > binding.position else None
        return None

    def _attribute(self, node: ast.Attribute, module: str) -> None:
        if (
            self.unsupported
            or not isinstance(node.ctx, ast.Load)
            or not isinstance(node.value, ast.Name)
        ):
            return
        binding = self._binding(node.value)
        emitted = self.table.get_obfuscated_import(module, node.attr)
        if binding:
            edit = (
                AttributeEdit(binding.scope, node.value.id, span(node), node.attr, module, emitted)
                if emitted and emitted != node.attr
                else None
            )
            self.resolutions[span(node)] = AccessResolution(
                span(node),
                module,
                module,
                "scheduled" if edit else "no changed export mapping",
                edit,
            )

    def resolve(self, node: ast.expr) -> Optional[str]:
        if isinstance(node, ast.Name):
            binding = self._binding(node)
            return binding.module if binding else None
        return None  # Never concatenate value attributes into module identities.

    def visit_FunctionDef(self, node) -> None:
        self.function_positions.append((node.lineno, node.col_offset))
        super().visit_FunctionDef(node)
        self.function_positions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Lambda(self, node: ast.Lambda) -> None:
        # Deferred execution and walrus locals require another proof.
        for expression in [*node.args.defaults, *node.args.kw_defaults]:
            if expression is not None:
                self.visit(expression)


def prove_accesses(
    source: str, module: str, inventory: ModuleInventory, table: GlobalSymbolTable
) -> Tuple[AccessResolution, ...]:
    """Strict results alongside legacy candidates; uncertainty never supplies an edit."""
    tree = ast.parse(source)
    visitor = _ProofVisitor(tree, module, inventory, table)
    visitor.visit(tree)
    return tuple(
        visitor.resolutions.get(
            span(node),
            AccessResolution(
                span(node), candidate, None, "module identity, scope or execution order not proved"
            ),
        )
        for node, candidate in discover_accesses(
            tree, lambda node: inventory.resolve_from(module, node)
        )
    )


def plan_attributes(
    source: str,
    relative_file: str,
    module: str,
    inventory: ModuleInventory,
    table: GlobalSymbolTable,
) -> AttributePlan:
    resolutions = prove_accesses(source, module, inventory, table)
    return AttributePlan(
        relative_file, source_hash(source), tuple(r.edit for r in resolutions if r.edit is not None)
    )
