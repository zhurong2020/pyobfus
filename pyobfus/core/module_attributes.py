"""Conservative module identity proofs and immutable original-AST edit plans.

Static package edges, relative imports and re-exports extend the PR 1 proofs.
Lexical candidates remain a separate, deliberately broader API.
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
            or _expression_binding(node.value) != edit.binding
        ):
            raise ValueError("Module attribute plan coordinate/binding mismatch")
        seen.add(edit.location)
        matched.append((node, edit.emitted))
    for node, emitted in matched:
        node.attr = emitted


def _expression_binding(node: ast.expr) -> Optional[str]:
    """An exact Name/Attribute path for plan validation, never an identity proof."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
        base = _expression_binding(node.value)
        return f"{base}.{node.attr}" if base else None
    return None


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
    if isinstance(statement, ast.ClassDef):
        return (
            not statement.bases
            and not statement.keywords
            and not statement.decorator_list
            and all(_inert(s) for s in statement.body)
            and not getattr(statement, "type_params", [])
        )
    if isinstance(statement, (ast.Assign, ast.AnnAssign)):
        if isinstance(statement, ast.AnnAssign) and not isinstance(
            statement.annotation, (ast.Name, ast.Constant)
        ):
            return False
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
    paths: Tuple[Tuple[str, Tuple[int, int]], ...] = ()


class ModuleInventory:
    """Selected project files, ordinary package roots, cycles and hazards."""

    def __init__(
        self,
        sources: Dict[str, str],
        resolve_from: Callable[[str, ast.ImportFrom], Optional[str]],
        table: Optional[GlobalSymbolTable] = None,
    ) -> None:
        self.trees = {module: ast.parse(source) for module, source in sources.items()}
        self.packages = {
            module[: -len(".__init__")]: tree
            for module, tree in self.trees.items()
            if module.endswith(".__init__")
        }
        self.resolve_from = resolve_from
        self._package_static: Dict[str, bool] = {}
        self._module_edges: Dict[Tuple[str, str], Optional[str]] = {}
        self.unsafe: Set[str] = set()
        self.edges: Dict[str, Set[str]] = {module: set() for module in self.trees}
        for module, tree in self.trees.items():
            bindings = _Bindings(lambda n: resolve_from(module, n))
            for statement in tree.body:
                bindings.visit(statement)
            # I/D can live in the module supplying an export, not just in
            # its consumer. Do not promise H correctness over those existing
            # flat-import/global-store failures, even for package re-exports.
            for node in ast.walk(tree):
                if isinstance(node, (ast.Global, ast.Nonlocal)) and set(node.names) & set(
                    bindings.imports
                ):
                    self.unsafe.add(module)
                if (
                    isinstance(node, ast.ImportFrom)
                    and node not in tree.body
                    and any(
                        (a.asname or a.name) in bindings.imports
                        and (
                            table is None
                            or table.get_obfuscated_import(resolve_from(module, node) or "", a.name)
                        )
                        for a in node.names
                    )
                ):
                    self.unsafe.add(module)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.edges[module].update(
                        self.canonical(a.name) for a in node.names if self.selected(a.name)
                    )
                elif isinstance(node, ast.ImportFrom):
                    base = resolve_from(module, node)
                    if base:
                        for name in [base, *(f"{base}.{a.name}" for a in node.names)]:
                            canonical = f"{name}.__init__" if name in self.packages else name
                            if canonical in self.trees and not (
                                canonical == module and node.module is None
                            ):
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
        # Keep PR 1's project-wide guard: an escape anywhere defeats all
        # proofs for that module, including consumers in other selected files.
        self.hazards: Dict[str, Tuple[ModuleHazard, ...]] = {}
        for module, tree in self.trees.items():
            events = discover_module_hazards(tree, module, self)
            self.hazards[module] = events
            self.unsafe.update(self.canonical(e.module) for e in events)
            if any(
                isinstance(n, ast.Subscript)
                and not isinstance(n.ctx, ast.Load)
                and isinstance(n.value, ast.Attribute)
                and n.value.attr == "modules"
                for n in ast.walk(tree)
            ):
                self.unsafe.update(self.trees)

    def canonical(self, module: str) -> str:
        return f"{module}.__init__" if module in self.packages else module

    def selected(self, module: str) -> bool:
        return self.canonical(module) in self.trees

    def _static_package(self, package: str) -> bool:
        if package not in self._package_static:
            self._package_static[package] = self._compute_static_package(package)
        return self._package_static[package]

    def _compute_static_package(self, package: str) -> bool:
        tree = self.packages.get(package)
        if tree is None:
            return False
        bindings = _Bindings(lambda n: self.resolve_from(f"{package}.__init__", n))
        for statement in tree.body:
            bindings.visit(statement)
        writes: Set[str] = set()
        for statement in tree.body:
            names: Set[str] = set()
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                names.update(a.asname or a.name.split(".")[0] for a in statement.names)
            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.add(statement.name)
            else:
                names.update(
                    n.id
                    for n in _scope_nodes([statement])
                    if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del))
                )
            if writes & names:
                return False
            writes.update(names)
        for statement in tree.body:
            if _inert(statement):
                continue
            if isinstance(statement, ast.ImportFrom):
                base = self.resolve_from(f"{package}.__init__", statement)
                if (
                    not base
                    or not self.selected(base)
                    or any(a.name == "*" for a in statement.names)
                ):
                    return False
                continue
            if isinstance(statement, ast.Import) and all(
                self.selected(a.name) for a in statement.names
            ):
                continue
            # Static module attribute reads into a package definition do not
            # call arbitrary initializer code. The worker uses the same access
            # plan for the RHS. Module __getattr__/mutation hazards still win.
            if isinstance(statement, (ast.Assign, ast.AnnAssign)) and isinstance(
                statement.value, ast.Attribute
            ):
                value = statement.value
                targets = (
                    statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                )
                if not all(isinstance(t, ast.Name) for t in targets):
                    return False
                if isinstance(statement, ast.AnnAssign) and not isinstance(
                    statement.annotation, (ast.Name, ast.Constant)
                ):
                    return False
                if any(
                    isinstance(n, ast.Name) and n.id == "__all__"
                    for t in targets
                    for n in ast.walk(t)
                ):
                    return False
                if isinstance(value.value, ast.Name):
                    target = bindings.imports.get(value.value.id)
                    if (
                        target
                        and self.selected(target)
                        and target not in self.packages
                        and target not in self.unsafe
                    ):
                        continue
            return False
        return True

    def edge(self, package: str, child: str) -> Optional[str]:
        key = (package, child)
        if key not in self._module_edges:
            self._module_edges[key] = self._compute_edge(package, child)
        return self._module_edges[key]

    def _compute_edge(self, package: str, child: str) -> Optional[str]:
        """Prove a package member is its child module, never just a filename."""
        target = f"{package}.{child}"
        if not self.selected(target) or not self._static_package(package):
            return None
        tree = self.packages[package]
        bindings = _Bindings(lambda n: self.resolve_from(f"{package}.__init__", n))
        for statement in tree.body:
            bindings.visit(statement)
        if any(
            isinstance(n, (ast.Global, ast.Nonlocal)) and child in n.names for n in ast.walk(tree)
        ):
            return None
        if child in bindings.shadowed:
            return None
        imported = bindings.imports.get(child)
        if imported is not None and imported != target:
            return None
        # A matching imported symbol can still be a value exported by the
        # package supplying it. Reject it unless it is the relative child edge.
        for statement in tree.body:
            if isinstance(statement, ast.ImportFrom):
                for alias in statement.names:
                    if (alias.asname or alias.name) == child:
                        base = self.resolve_from(f"{package}.__init__", statement)
                        if base != package or alias.name != child:
                            return None
        return target

    def eligible(self, module: str, importer: str) -> bool:
        canonical = self.canonical(module)
        if module.endswith(".__init__") or module == "__init__" or not self.selected(module):
            return False
        if any(m in self.unsafe or m in self.cyclic for m in (canonical, importer)):
            return False
        parts = module.removesuffix(".__init__").split(".")
        for index in range(1, len(parts)):
            package = ".".join(parts[:index])
            if package in self.trees or self.edge(package, parts[index]) is None:
                return False
            if self.canonical(package) in self.unsafe or self.canonical(package) in self.cyclic:
                return False
        return module not in self.packages or self._static_package(module)


@dataclass(frozen=True)
class ModuleHazard:
    location: Tuple[int, int]
    module: str
    names: Tuple[str, ...]
    kind: str


def discover_module_hazards(
    tree: ast.AST, importer: str, inventory: ModuleInventory
) -> Tuple[ModuleHazard, ...]:
    """Observe escapes/mutation through the shared lexical candidate traversal.

    These are candidates rather than runtime proofs. No assignment propagation
    or dynamic-import rewrite is introduced. Helper import aliases are resolved
    by the same lexical resolver as module candidates.
    """
    parents = {c: n for n in ast.walk(tree) for c in ast.iter_child_nodes(n)}
    events: Dict[Tuple[int, int, str], ModuleHazard] = {}

    class Hazards(ImportedAccessVisitor):
        def record(self, node: ast.AST, module: str, names: Tuple[str, ...], kind: str) -> None:
            if inventory.selected(module):
                key = (node.lineno, node.col_offset, module)  # type: ignore[attr-defined]
                events[key] = ModuleHazard(key[:2], module, names, kind)

        def dynamic(self, node: ast.expr) -> Optional[str]:
            if isinstance(node, ast.Subscript) and self.resolve(node.value) == "sys.modules":
                key = node.slice
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    return key.value
            if isinstance(node, ast.Call) and self.resolve(node.func) == "importlib.import_module":
                if node.args and isinstance(node.args[0], ast.Constant):
                    target = node.args[0].value
                    if isinstance(target, str):
                        if target.startswith("."):
                            return None  # Dynamic package argument remains unsupported.
                        return target
            return None

        def observe(self, node: ast.expr) -> None:
            module = self.resolve(node)
            if not module or not inventory.selected(module) or not isinstance(node.ctx, ast.Load):  # type: ignore[attr-defined]
                return
            parent = parents.get(node)
            if isinstance(parent, ast.Attribute) and parent.value is node:
                if parent.attr == "__dict__":
                    names: Tuple[str, ...] = ()
                    grandparent = parents.get(parent)
                    if isinstance(grandparent, ast.Subscript) and isinstance(
                        grandparent.slice, ast.Constant
                    ):
                        if isinstance(grandparent.slice.value, str):
                            names = (grandparent.slice.value,)
                    self.record(parent, module, names, "reflection")
                return
            if isinstance(parent, (ast.withitem, ast.comprehension)):
                return
            # Calls, tuple/container storage, assignment, return/yield and a
            # bare reference are all opaque module consumption.
            site = (
                parent
                if isinstance(
                    parent,
                    (ast.Assign, ast.AnnAssign, ast.Return, ast.Yield, ast.YieldFrom, ast.Call),
                )
                else node
            )
            self.record(site or node, module, (), "module escape")

        def visit_Name(self, node: ast.Name) -> None:
            self.observe(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            target = self.resolve(node.value) or self.dynamic(node.value)
            if target and inventory.selected(target):
                if not isinstance(node.ctx, ast.Load):
                    self.record(node, target, (node.attr,), "module mutation")
                elif self.dynamic(node.value):
                    self.record(node, target, (node.attr,), "dynamic module access")
            path = self.resolve(node)
            if path and inventory.selected(path) and not isinstance(node.ctx, ast.Load):
                self.record(node, path, (), "module path mutation")
            self.observe(node)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            helpers = {"getattr", "hasattr", "setattr", "delattr", "vars"}
            helper = self.resolve(node.func)
            if node.args and (
                (isinstance(node.func, ast.Name) and node.func.id in helpers)
                or helper in {f"builtins.{name}" for name in helpers}
            ):
                target = self.resolve(node.args[0])
                if target:
                    names: Tuple[str, ...] = ()
                    if (
                        len(node.args) > 1
                        and isinstance(node.args[1], ast.Constant)
                        and isinstance(node.args[1].value, str)
                    ):
                        names = (node.args[1].value,)
                    self.record(node, target, names, "reflection")
                    # Avoid a second, less specific escape at the first arg.
                    for argument in [*node.args[1:], *(k.value for k in node.keywords)]:
                        self.visit(argument)
                    return
            self.generic_visit(node)

    Hazards(
        lambda node: inventory.resolve_from(importer, node), lambda n, m: None, lambda n: None
    ).visit(tree)
    return tuple(events.values())


@dataclass(frozen=True)
class AccessResolution:
    """Separate a lexical candidate from a proved identity and optional edit."""

    location: Span
    candidate_module: str
    proved_module: Optional[str]
    reason: str
    edit: Optional[AttributeEdit] = None


class _ProofVisitor(ImportedAccessVisitor):
    """Reuse candidate traversal and prove stable bindings and explicit module edges."""

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
                if name in bindings.shadowed or name in self.forbidden:
                    continue
                competing = imports[name]
                # Multiple plain imports bind the same top package. Every
                # member import must be unconditional; unrelated explicit
                # aliases/from imports remain competing writes.
                if len(competing) != 1 and not all(
                    isinstance(n, ast.Import)
                    and n in body
                    and all(a.asname is None for a in n.names if a.name.split(".")[0] == name)
                    for n in competing
                ):
                    continue
                target = None
                paths: Tuple[Tuple[str, Tuple[int, int]], ...] = ()
                if isinstance(statement, ast.Import):
                    target = alias.name if alias.asname else alias.name.split(".")[0]
                    paths = tuple(
                        (a.name, (n.lineno, n.col_offset))
                        for n in competing
                        if isinstance(n, ast.Import)
                        for a in n.names
                        if a.asname is None and a.name.split(".")[0] == name
                    )
                elif (
                    isinstance(statement, ast.ImportFrom)
                    and alias.name != "*"
                    and statement.level < len(self.module.split("."))
                ):
                    base = self.resolve_from(statement)
                    if base and self.table.get_obfuscated_import(base, alias.name) is None:
                        target = self.inventory.edge(base, alias.name)
                if target and self.inventory.eligible(target, self.module):
                    scope[name] = target
                    first = competing[0]
                    prefix = body[: body.index(first)]
                    ready = all(
                        _inert(s) or isinstance(s, (ast.Import, ast.ImportFrom)) for s in prefix
                    )
                    self.details[(id(scope), name)] = _Binding(
                        scope_id, target, (first.lineno, first.col_offset), ready, paths
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

    def _root(self, node: ast.expr) -> Optional[ast.Name]:
        while isinstance(node, ast.Attribute):
            node = node.value
        return node if isinstance(node, ast.Name) else None

    def _attribute(self, node: ast.Attribute, module: str) -> None:
        if self.unsupported or not isinstance(node.ctx, ast.Load):
            return
        root = self._root(node.value)
        binding = self._binding(root) if root else None
        path = _expression_binding(node.value)
        emitted = self.table.get_obfuscated_import(module, node.attr)
        if (
            binding
            and path
            and self.inventory.eligible(module, self.module)
            and not self.inventory.selected(f"{module}.{node.attr}")
        ):
            edit = (
                AttributeEdit(binding.scope, path, span(node), node.attr, module, emitted)
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
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            base = self.resolve(node.value)
            root = self._root(node)
            binding = self._binding(root) if root else None
            if base and binding:
                target = self.inventory.edge(base, node.attr)
                if not target or not self.inventory.eligible(target, self.module):
                    return None
                # Each path segment must have been loaded by an explicit
                # dotted import in this binding's scope, reaching this use.
                position = (node.lineno, node.col_offset)
                if self.function_positions and binding.scope.startswith("module:"):
                    position = min(position, self.function_positions[0])
                if any(
                    (path == target or path.startswith(target + ".")) and imported < position
                    for path, imported in binding.paths
                ):
                    return target
        return None

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
