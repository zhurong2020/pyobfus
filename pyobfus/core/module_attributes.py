"""Conservative module identity proofs and immutable original-AST edit plans.

Static package edges, relative imports and re-exports extend the PR 1 proofs.
Lexical candidates remain a separate, deliberately broader API.
No target code is imported, and no names are allocated here.
"""

from __future__ import annotations

import ast
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from pyobfus.core.global_table import GlobalSymbolTable
from pyobfus.core.import_resolution import (
    ImportedAccessVisitor,
    _UncertainAccessVisitor,
    discover_uncertain_accesses,
    _Bindings,
    discover_accesses,
    discover_module_bindings,
)

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


def _namespace_scope_nodes(body: List[ast.stmt]) -> List[ast.AST]:
    """Include definition-time expressions evaluated in the containing scope."""
    nodes = _scope_nodes(body)
    for node in list(nodes):
        expressions: List[ast.AST] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            expressions.extend(node.decorator_list)
            expressions.extend(node.args.defaults)
            expressions.extend(e for e in node.args.kw_defaults if e is not None)
            expressions.extend(
                a.annotation
                for a in ast.walk(node.args)
                if isinstance(a, ast.arg) and a.annotation is not None
            )
            if node.returns is not None:
                expressions.append(node.returns)
        elif isinstance(node, ast.ClassDef):
            expressions.extend(node.decorator_list)
            expressions.extend(node.bases)
            expressions.extend(k.value for k in node.keywords)
        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            # A comprehension can expose its containing function on interpreters
            # that inline it; conservatively reject that function too.
            expressions.extend(ast.iter_child_nodes(node))
        for expression in expressions:
            nodes.extend(ast.walk(expression))
    return nodes


def _namespace_exposed(
    nodes: List[ast.AST], aliases: Dict[str, Set[str]], *, global_only: bool = False
) -> bool:
    """A namespace capability may escape through aliases and opaque helpers.

    Read-only inspection is conservatively rejected too. Any sys.modules
    reference can expose the importing module, including via a later lookup.
    """
    parents = {id(child): n for n in nodes for child in ast.iter_child_nodes(n)}
    names = {"globals", "exec", "eval"} if global_only else {"locals", "vars", "exec", "eval"}
    for node in nodes:
        path = _expression_binding(node) if isinstance(node, ast.expr) else None
        paths = {path} if path else set()
        if path:
            root, *tail = path.split(".")
            paths.update(".".join([alias, *tail]) for alias in aliases.get(root, set()))
        if global_only and (
            paths & {"sys.modules", "__builtins__"}
            or isinstance(node, ast.Attribute)
            and node.attr in {"__globals__", "f_globals"}
        ):
            return True
        if not global_only and isinstance(node, ast.Attribute) and node.attr == "f_locals":
            return True
        if not paths & (names | {f"builtins.{name}" for name in names}):
            continue
        parent = parents.get(id(node))
        if (
            paths & {"vars", "builtins.vars"}
            and not paths
            & {"locals", "builtins.locals", "globals", "builtins.globals", "exec", "eval"}
            and isinstance(parent, ast.Call)
            and parent.func is node
            and (parent.args or parent.keywords)
        ):
            continue  # vars(obj) inspects obj rather than the current scope.
        return True
    return False


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
        if table is not None:
            from pyobfus.core.star_imports import expand_stars

            for module, tree in self.trees.items():
                expand_stars(tree, table.star_import_plans.get(module, {}))
        self.packages = {
            module[: -len(".__init__")]: tree
            for module, tree in self.trees.items()
            if module.endswith(".__init__")
        }
        self.resolve_from = resolve_from
        self._package_static: Dict[str, bool] = {}
        self._module_edges: Dict[Tuple[str, str], Optional[str]] = {}
        self._export_bindings: Dict[str, _Bindings] = {}
        self._diagnostic_bindings: Optional[Dict[str, Dict[str, Set[str]]]] = None
        self._diagnostic_members: Dict[Tuple[str, str], Set[str]] = {}
        stdlib = getattr(sys, "stdlib_module_names", None)
        if stdlib is None:  # Python 3.9; inspect the tool's stdlib, never target imports.
            root = Path(ast.__file__).parent
            stdlib = {p.stem for p in root.glob("*.py")}
            stdlib.update(p.name for p in root.iterdir() if (p / "__init__.py").is_file())
            stdlib.update(p.name.split(".")[0] for p in (root / "lib-dynload").glob("*"))
        self.stdlib_roots = set(stdlib) | set(sys.builtin_module_names)
        self.unsafe: Set[str] = set()
        self.modules_stores: Dict[str, Tuple[Tuple[int, int, str], ...]] = {}
        self.nested_reimports: Set[str] = set()
        self.edges: Dict[str, Set[str]] = {module: set() for module in self.trees}
        for module, tree in self.trees.items():
            bindings = _Bindings(lambda n: resolve_from(module, n))
            for statement in tree.body:
                bindings.visit(statement)
            self._export_bindings[module] = bindings
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
                    self.nested_reimports.add(module)
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
            stores = discover_modules_stores(tree, lambda n: resolve_from(module, n))
            if stores:
                self.modules_stores[module] = stores
                self.unsafe.update(self.trees)

    def rejection_reasons(self, module: str, importer: str) -> Tuple[str, ...]:
        """All observed blockers, ordered without granting a proof or relaxing B2/B3."""
        if self.modules_stores:
            return ("module_attribute.modules_store",)
        direct = [self.canonical(module), importer]
        parts = module.removesuffix(".__init__").split(".")
        packages = [".".join(parts[:i]) for i in range(1, len(parts))]
        if module in self.packages:
            packages.append(module)
        owners = direct + [self.canonical(p) for p in packages]
        reasons = []
        if any(m in self.nested_reimports for m in owners):
            reasons.append("module_attribute.nested_reimport")
        if any(m in self.unsafe for m in owners):
            reasons.append("module_attribute.module_hazard")
        if any(m in self.cyclic for m in direct):
            reasons.append("module_attribute.import_cycle")
        if any(p in self.packages and not self._static_package(p) for p in packages):
            reasons.append("module_attribute.package_init_not_static")
        if any(m in self.cyclic for m in owners) and "module_attribute.import_cycle" not in reasons:
            reasons.append("module_attribute.import_cycle")
        return tuple(reasons) or ("module_attribute.other",)

    def rejection_reason(self, module: str, importer: str) -> str:
        """Primary refusal reason for the existing per-access result model."""
        return self.rejection_reasons(module, importer)[0]

    def canonical(self, module: str) -> str:
        return f"{module}.__init__" if module in self.packages else module

    def selected(self, module: str) -> bool:
        return self.canonical(module) in self.trees

    def candidate_member(self, module: str, name: str) -> Set[str]:
        """Follow observed module members for advice only, including re-export chains.

        Retain competing candidates and terminate cyclic aliases. Selected
        filenames are observations here; they never authorize an attribute edit.
        """

        key = (module, name)
        if key in self._diagnostic_members:
            return self._diagnostic_members[key]
        if self._diagnostic_bindings is None:
            self._diagnostic_bindings = {}
            for owner, tree in self.trees.items():

                def resolve(node: ast.ImportFrom) -> Optional[str]:
                    return self.resolve_from(owner, node)

                self._diagnostic_bindings[owner] = discover_module_bindings(tree, resolve)
        observed = self._diagnostic_bindings

        def expand(path: str, visited: Set[str], edges: Set[Tuple[str, str]]) -> Set[str]:
            if path in visited:
                return set()
            visited = visited | {path}
            result = {path} if self.selected(path) else set()
            parts = path.split(".")
            for split in range(1, len(parts)):
                for base in expand(".".join(parts[:split]), visited, edges):
                    edge = (self.canonical(base), parts[split])
                    if edge in edges:
                        continue
                    bindings = observed.get(edge[0], {})
                    for target in bindings.get(parts[split], set()):
                        suffix = parts[split + 1 :]
                        result.update(expand(".".join([target, *suffix]), visited, edges | {edge}))
            return result

        result = expand(f"{module}.{name}", set(), set())
        self._diagnostic_members[key] = result
        return result

    def static_export(
        self, module: str, name: str, visited: Optional[Set[Tuple[str, str]]] = None
    ) -> bool:
        """An allocated __all__ slot alone does not prove an emitted binding.

        Reuse lexical binding collection and the existing relative resolver;
        this validates the table's spelling without allocating another name.
        Imported exports require a unique unconditional symbol import, then
        the same proof at its source. Dynamic/star-created exports are refused.
        """
        canonical = self.canonical(module)
        if module in self.packages and module in self.trees:
            return False
        key = (canonical, name)
        visited = set() if visited is None else set(visited)
        if key in visited or canonical in self.unsafe:
            return False
        visited.add(key)
        bindings = self._export_bindings.get(canonical)
        if bindings is None:
            return False
        if name not in bindings.imports:
            for statement in self.trees[canonical].body:
                if (
                    isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    and statement.name == name
                ):
                    return True
                if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    targets = (
                        statement.targets
                        if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                    if any(
                        isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store) and n.id == name
                        for target in targets
                        for n in ast.walk(target)
                    ):
                        return True
            return False
        if name in bindings.shadowed:
            return False
        tree = self.trees[canonical]
        imports = [
            n
            for n in _scope_nodes(tree.body)
            if isinstance(n, (ast.Import, ast.ImportFrom))
            and any((a.asname or a.name.split(".")[0]) == name for a in n.names)
        ]
        if (
            len(imports) != 1
            or imports[0] not in tree.body
            or not isinstance(imports[0], ast.ImportFrom)
        ):
            return False
        statement = imports[0]
        base = self.resolve_from(canonical, statement)
        if not base:
            return False
        alias = next(a for a in statement.names if (a.asname or a.name) == name)
        return self.static_export(base, alias.name, visited)

    def _static_package(self, package: str) -> bool:
        if package not in self._package_static:
            self._package_static[package] = self._compute_static_package(package)
        return self._package_static[package]

    def _compute_static_package(self, package: str) -> bool:
        tree = self.packages.get(package)
        if tree is None:
            return False
        if any(isinstance(n, ast.Name) and n.id == "__lazy_modules__" for n in ast.walk(tree)):
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
            # A lazy package binding does not prove child initialization.
            if getattr(statement, "is_lazy", False):
                return False
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
        if module.split(".")[0] in self.stdlib_roots:
            return False  # A selected filename cannot settle a stdlib import collision.
        if module in self.packages and module in self.trees:
            return False  # The file/package collision is ambiguous even at the root.
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


def discover_modules_stores(
    tree: ast.AST, resolve_from: Callable[[ast.ImportFrom], Optional[str]]
) -> Tuple[Tuple[int, int, str], ...]:
    """Use lexical resolution, retaining uncertain imported/possible-sys receivers.

    Candidate propagation is diagnostic only. It can close proofs, never open
    them. Ordinary object parameters and locals have no imported candidate.
    """
    stores: List[Tuple[int, int, str]] = []

    class Stores(_UncertainAccessVisitor):
        def __init__(self, *args) -> None:
            super().__init__(*args)
            self.competing: Dict[int, Set[str]] = {}
            self.imported_roots: Dict[int, Set[str]] = {}

        def _candidate_scope(
            self, body: List[ast.stmt], bindings: _Bindings
        ) -> Dict[str, Optional[str]]:
            scope = super()._candidate_scope(body, bindings)
            self.competing[id(scope)] = bindings.shadowed
            self.imported_roots[id(scope)] = {
                alias.asname or alias.name.split(".")[0]
                for statement in _scope_nodes(body)
                if isinstance(statement, (ast.Import, ast.ImportFrom))
                for alias in statement.names
                if alias.name != "*"
            }
            return scope

        def resolve(self, node: ast.expr) -> Optional[str]:
            path = _expression_binding(node)
            if path:
                root = path.split(".")[0]
                for scope in reversed(self.scopes):
                    if root in scope:
                        if root in self.competing.get(id(scope), set()):
                            return None
                        break
            return super().resolve(node)

        def visit_FunctionDef(self, node) -> None:
            super().visit_FunctionDef(node)
            # Type parameter bounds/defaults can also contain comprehension
            # assignment targets. Observation must not omit these stores.
            for parameter in getattr(node, "type_params", []):
                self.visit(parameter)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            super().visit_ClassDef(node)
            for parameter in getattr(node, "type_params", []):
                self.visit(parameter)

        def visit_ListComp(self, node) -> None:
            # The shared access observer omits assignment targets. Registry
            # stores in a comprehension target still invalidate every proof.
            self.visit(node.generators[0].iter)
            names = {
                n.id
                for g in node.generators
                for n in ast.walk(g.target)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
            }
            previous_scopes, previous_kinds = self.scopes, self.scope_kinds
            self.scopes = [s for s, k in zip(previous_scopes, previous_kinds) if k != "class"]
            self.scope_kinds = [k for k in previous_kinds if k != "class"]
            self.scopes.append({name: None for name in names})
            self.scope_kinds.append("function")
            for index, generator in enumerate(node.generators):
                if index:
                    self.visit(generator.iter)
                self.visit(generator.target)
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

        def mutation(self, receiver: ast.expr, site: ast.AST) -> None:
            resolved = self.resolve(receiver)
            candidates = self._resolve_candidates(receiver)
            path = _expression_binding(receiver)
            if path is None and isinstance(receiver, ast.Attribute):
                # AugAssign attributes carry Store context; retain the lexical
                # root for the same uncertain-import guard as subscript stores.
                lexical_owner = _expression_binding(receiver.value)
                path = f"{lexical_owner}.{receiver.attr}" if lexical_owner else None
            reason = None
            if resolved == "sys.modules":
                reason = "resolved sys.modules store/delete"
            elif "sys.modules" in candidates:
                reason = "possible sys.modules alias with competing or indirect binding"
            elif resolved is None:
                root = path.split(".")[0] if path else None
                imported = False
                for scope in reversed(self.scopes):
                    if root in scope:
                        imported = root in self.imported_roots.get(id(scope), set())
                        break
                if (
                    isinstance(receiver, ast.Attribute)
                    and receiver.attr == "modules"
                    and (candidates or imported or path == "sys.modules")
                ) or (isinstance(receiver, ast.Name) and imported):
                    reason = "unresolved imported or possible sys receiver"
                elif (
                    isinstance(receiver, ast.Call)
                    and isinstance(receiver.func, ast.Name)
                    and receiver.func.id == "getattr"
                    and len(receiver.args) >= 2
                ):
                    # Dynamic lookup is an observation, never an identity proof.
                    owner = receiver.args[0]
                    owner_path = _expression_binding(owner)
                    if (
                        "sys" in self._resolve_candidates(owner)
                        or self.resolve(owner) == "sys"
                        or owner_path == "sys"
                    ):
                        reason = "dynamic attribute lookup on a possible sys receiver"
            if reason:
                stores.append((site.lineno, site.col_offset, reason))  # type: ignore[attr-defined]

        def visit_Subscript(self, node: ast.Subscript) -> None:
            if not isinstance(node.ctx, ast.Load):
                self.mutation(node.value, node)
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute) and node.func.attr in {
                "update",
                "setdefault",
                "pop",
                "popitem",
                "clear",
                "__setitem__",
                "__delitem__",
            }:
                self.mutation(node.func.value, node)
            self.generic_visit(node)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            if isinstance(node.op, ast.BitOr):
                self.mutation(node.target, node)
            self.generic_visit(node)

    Stores(resolve_from, lambda n, m: None, lambda n: None).visit(tree)
    return tuple(stores)


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

        def dynamic_expression(self, node: ast.expr) -> bool:
            return (
                isinstance(node, ast.Subscript) and self.resolve(node.value) == "sys.modules"
            ) or (
                isinstance(node, ast.Call) and self.resolve(node.func) == "importlib.import_module"
            )

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
            if (
                self.dynamic_expression(node.value)
                and self.dynamic(node.value) is None
                and (
                    not (node.attr.startswith("__") and node.attr.endswith("__"))
                    or node.attr == "__dict__"
                )
            ):
                for candidate in inventory.trees:
                    self.record(node, candidate, (), "dynamic module access (unknown target)")
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
            if helper == "enum.global_enum":
                inventory.unsafe.update(inventory.trees)  # A computed class owner is unknown.
            builtin_helper = (
                isinstance(node.func, ast.Name)
                and node.func.id in helpers
                and not any(node.func.id in scope for scope in self.scopes)
            )
            if node.args and (builtin_helper or helper in {f"builtins.{name}" for name in helpers}):
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
        self.lazy_module_control = any(
            isinstance(n, ast.Name) and n.id == "__lazy_modules__" for n in ast.walk(tree)
        )
        self.inventory = inventory
        self.table = table
        self.details: Dict[Tuple[int, str], _Binding] = {}
        self.resolutions: Dict[Span, AccessResolution] = {}
        self.function_positions: List[Tuple[int, int]] = []
        self.namespace_aliases: Dict[str, Set[str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"sys", "builtins"}:
                        self.namespace_aliases.setdefault(alias.asname or alias.name, set()).add(
                            alias.name
                        )
            elif isinstance(node, ast.ImportFrom) and node.module in {"sys", "builtins"}:
                for alias in node.names:
                    self.namespace_aliases.setdefault(alias.asname or alias.name, set()).add(
                        f"{node.module}.{alias.name}" if node.module == "sys" else alias.name
                    )
        self.module_namespace_exposed = _namespace_exposed(
            list(ast.walk(tree)), self.namespace_aliases, global_only=True
        ) or _namespace_exposed(_namespace_scope_nodes(tree.body), self.namespace_aliases)
        self.forbidden = {
            name
            for n in ast.walk(tree)
            if isinstance(n, (ast.Global, ast.Nonlocal))
            for name in n.names
        }
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
        namespace_exposed = (
            self.module_namespace_exposed
            if kind == "module"
            else _namespace_exposed(_namespace_scope_nodes(body), self.namespace_aliases)
        )
        scope_id = f"{kind}:{body[0].lineno if body else 0}:{body[0].col_offset if body else 0}"
        for statement in body:
            if (
                not isinstance(statement, (ast.Import, ast.ImportFrom))
                or kind == "class"
                or namespace_exposed
            ):
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
                        and not getattr(n, "is_lazy", False)
                        and not self.lazy_module_control
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
                    self.details[(id(scope), name)] = _Binding(
                        scope_id, target, (first.lineno, first.col_offset), paths
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
                    if not self.function_positions:
                        return None
                    # A deferred body cannot run before its outermost definition.
                    # Competing writes were rejected when collecting this binding.
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
        if emitted and not self.inventory.static_export(module, node.attr):
            return  # A rename allocation is not a proof of an emitted export binding.
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
        self.function_positions.append((node.lineno, node.col_offset))
        for expression in [*node.args.defaults, *node.args.kw_defaults]:
            if expression is not None:
                self.visit(expression)
        # Reuse function scope collection so parameters shadow imports and
        # enclosing function locals cannot supply an unproved closure binding.
        statement = ast.copy_location(ast.Expr(value=node.body), node.body)
        self._enter([statement], "function", node.args)
        self.function_positions.pop()


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
                span(node), candidate, None, inventory.rejection_reason(candidate, module)
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


def count_unproved_accesses(
    sources: Dict[str, str],
    inventory: ModuleInventory,
    table: GlobalSymbolTable,
    plans: Dict[str, AttributePlan],
) -> int:
    """Count distinct retained access sites with changed project export mappings.

    Candidates never authorize edits. Counts include stores/deletes and dynamic
    hazard accesses, but exclude already-preserved exports and module escapes
    without an attribute access. Multiple candidate identities count once.
    """
    sites: Set[Tuple[str, Span]] = set()
    for importer, source in sources.items():
        tree = ast.parse(source)
        edits = {e.location for e in plans.get(importer, AttributePlan("", "")).edits}
        candidates = discover_uncertain_accesses(
            tree, lambda n: inventory.resolve_from(importer, n), inventory.candidate_member
        )
        attribute_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Attribute)]
        for hazard in inventory.hazards[importer]:
            for node in attribute_nodes:
                if (
                    isinstance(node, ast.Attribute)
                    and (node.lineno, node.col_offset) == hazard.location
                ):
                    candidates.append((node, hazard.module))
        for node, target in candidates:
            changed = table.get_obfuscated_import(target, node.attr)
            if target in inventory.packages and target in inventory.trees:
                changed = changed or table.get_obfuscated_import(
                    inventory.canonical(target), node.attr
                )
            package = inventory.packages.get(target)
            if package is not None and not changed:
                changed = next(
                    (
                        table.get_obfuscated_import(
                            inventory.resolve_from(inventory.canonical(target), n) or "", node.attr
                        )
                        for n in ast.walk(package)
                        if isinstance(n, ast.ImportFrom)
                        and any(a.name == "*" for a in n.names)
                        and table.get_obfuscated_import(
                            inventory.resolve_from(inventory.canonical(target), n) or "", node.attr
                        )
                    ),
                    None,
                )
            if changed and span(node) not in edits:
                sites.add((importer, span(node)))
    return len(sites)
