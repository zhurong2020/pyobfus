"""Resolve imported bindings on the original AST, before any renaming.

The compiler symbol table supplies binding ownership; AST traversal supplies
execution scopes for signatures and the first comprehension iterable. Plans
use source coordinates so separate worker parses and earlier edits are safe.
"""

import ast
import symtable
from collections import defaultdict
from typing import Any, Dict, Set, Tuple

from pyobfus.core.class_bindings import mark_class_bindings

Key = Tuple[int, int, str]
# (statement coordinate, alias position): one statement may import the same
# original name twice (`from m import f, f as g`), so the name is not unique.
ImportKey = Tuple[Key, int]


class ScopeResolutionError(ValueError):
    """The AST could not be paired with compiler scopes; preserve this module."""


def key(node: ast.AST) -> Key:
    return (getattr(node, "lineno", -1), getattr(node, "col_offset", -1), type(node).__name__)


def import_plan(
    tree: ast.AST, table: Any, module: str
) -> Tuple[Dict[Key, Any], Dict[ImportKey, Tuple[str, str]], Dict[str, str], Set[Key]]:
    """Return reference edits, imports needing preserved aliases, and the union.

    Uncertain binding changes keep the original local spelling via an explicit
    alias. Export names still change, so merely skipping reference edits would
    leave an unbound name. No executable input is evaluated here.
    """
    # symtable accepts text only. Reparse the canonical text and pair the
    # relevant nodes in AST walk order, retaining the caller's coordinates.
    if not any(
        isinstance(n, ast.ImportFrom)
        and any(
            table.get_obfuscated_import(
                (
                    ".".join(module.split(".")[: -n.level] + ([n.module] if n.module else []))
                    if n.level
                    else n.module or ""
                ),
                a.name,
            )
            for a in n.names
        )
        for n in ast.walk(tree)
    ):
        return {}, {}, {}, set()
    source = ast.unparse(tree)
    normalized = ast.parse(source)
    string_binders = (ast.ExceptHandler,) + tuple(
        getattr(ast, name)
        for name in ("MatchAs", "MatchStar", "MatchMapping")
        if hasattr(ast, name)
    )
    relevant = (ast.Name, ast.Global, ast.Nonlocal, ast.ImportFrom) + string_binders
    originals = [n for n in ast.walk(tree) if isinstance(n, relevant)]
    copies = [n for n in ast.walk(normalized) if isinstance(n, relevant)]
    if len(originals) != len(copies):
        raise ScopeResolutionError("Cannot correlate import binding scopes")
    coordinates = {id(n): key(o) for o, n in zip(originals, copies)}
    mark_class_bindings(normalized)
    root = symtable.symtable(source, "<imports>", "exec")
    future_annotations = any(
        isinstance(n, ast.ImportFrom)
        and n.module == "__future__"
        and any(a.name == "annotations" for a in n.names)
        for n in normalized.body
    )
    scopes = [root]
    parents: Dict[int, Any] = {}
    mappings: Dict[int, Dict[str, str]] = defaultdict(dict)
    imports = []
    other_imports = []
    references = []
    used = set()
    dynamic = set()
    synthetic = []
    # Module names rebound other than by import or `del`. symtable reports a
    # deleted import as assigned; `del X` alone leaves the import binding sound.
    rebinds: Set[str] = set()

    def bind(name):
        if owner(scopes[-1], name) is root:
            rebinds.add(name)

    class ComprehensionScope:
        """PEP 709 omits tables for inlined comprehensions on Python 3.12+."""

        def __init__(self, parent: Any, node: Any):
            self.parent = parent
            self.targets = {
                n.id
                for g in node.generators
                for n in ast.walk(g.target)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
            }

        def get_id(self):
            return -id(self)

        def get_type(self):
            return "function"

        def get_children(self):
            return self.parent.get_children()

        def lookup(self, name):
            local = name in self.targets

            class Symbol:
                def is_global(self):
                    return False

                def is_local(self):
                    return local

            return Symbol()

    def owner(scope, name):
        if scope is root:
            return root
        try:
            symbol = scope.lookup(name)
        except KeyError:
            symbol = None
        if symbol is not None and symbol.is_global():
            return root
        if symbol is not None and symbol.is_local():
            return scope
        parent = parents.get(scope.get_id())
        while parent is not None and str(parent.get_type()) == "class":
            parent = parents.get(parent.get_id())
        return owner(parent, name) if parent is not None else root

    class Scan(ast.NodeVisitor):
        def enter(self, node, name, body):
            parent = scopes[-1]
            child = next(
                (
                    c
                    for c in parent.get_children()
                    if c.get_name() == name
                    and c.get_lineno() == node.lineno
                    and c.get_id() not in used
                ),
                None,
            )
            if child is None:
                if not isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
                    raise ScopeResolutionError("Cannot resolve import scope: " + name)
                child = ComprehensionScope(parent, node)
                synthetic.append(child)
            used.add(child.get_id())
            parents[child.get_id()] = parent
            scopes.append(child)
            body()
            scopes.pop()

        def visit_Name(self, node):
            references.append((node, scopes[-1]))
            if isinstance(node.ctx, ast.Store):
                bind(node.id)
            if node.id in {"locals", "globals"}:
                dynamic.update(s.get_id() for s in scopes if s is not root)

        def visit_Call(self, node):
            def globals_call(expr):
                return (
                    isinstance(expr, ast.Call)
                    and isinstance(expr.func, ast.Name)
                    and expr.func.id == "globals"
                )

            if (isinstance(node.func, ast.Name) and node.func.id in {"exec", "eval"}) or (
                isinstance(node.func, ast.Attribute)
                and globals_call(node.func.value)
                and node.func.attr
                not in {
                    "keys",
                    "values",
                    "items",
                    "get",
                    "copy",
                    "__contains__",
                    "__getitem__",
                    "__iter__",
                    "__len__",
                }
            ):
                dynamic.update(s.get_id() for s in scopes if s is not root or scopes[-1] is root)
            self.generic_visit(node)

        def visit_Subscript(self, node):
            if (
                isinstance(node.ctx, (ast.Store, ast.Del))
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "globals"
            ):
                dynamic.update(s.get_id() for s in scopes if s is not root or scopes[-1] is root)
            self.generic_visit(node)

        def visit_Global(self, node):
            references.append((node, scopes[-1]))

        visit_Nonlocal = visit_Global

        def visit_ExceptHandler(self, node):
            if node.name:
                bind(node.name)
                references.append((node, scopes[-1]))
            self.generic_visit(node)

        def visit_MatchAs(self, node):
            if node.name:
                bind(node.name)
                references.append((node, scopes[-1]))
            self.generic_visit(node)

        visit_MatchStar = visit_MatchAs

        def visit_MatchMapping(self, node):
            if node.rest:
                bind(node.rest)
                references.append((node, scopes[-1]))
            self.generic_visit(node)

        def defaults(self, node):
            args = node.args
            for default in args.defaults + [d for d in args.kw_defaults if d is not None]:
                self.visit(default)

        def signature(self, node):
            args = node.args
            annotations = [
                a.annotation
                for a in args.posonlyargs + args.args + [args.vararg, args.kwarg] + args.kwonlyargs
                if a is not None and a.annotation is not None
            ]
            if getattr(node, "returns", None) is not None:
                annotations.append(node.returns)
            self.annotations(node, annotations, signature=True)

        def annotations(self, node, annotations, signature=False):
            annotation_scope = next(
                (
                    c
                    for c in scopes[-1].get_children()
                    if c.get_name() == "__annotate__"
                    and (not signature or c.get_lineno() == node.lineno)
                ),
                None,
            )
            if annotation_scope is not None:
                parents[annotation_scope.get_id()] = scopes[-1]
                scopes.append(annotation_scope)
            for annotation in annotations:
                if future_annotations:
                    # These expressions are stored as text and have no compiler
                    # child scopes. Preserve the existing name spelling policy.
                    for part in ast.walk(annotation):
                        if isinstance(part, ast.Name):
                            references.append((part, scopes[-1]))
                else:
                    self.visit(annotation)
            if annotation_scope is not None:
                scopes.pop()

        def visit_AnnAssign(self, node):
            self.visit(node.target)
            if node.value is not None:
                self.visit(node.value)
            # Function-local variable annotations are never evaluated.
            if str(scopes[-1].get_type()) in {"module", "class"}:
                self.annotations(node, [node.annotation])

        def type_parameters(self, node, name):
            if not getattr(node, "type_params", []):
                return None
            child = next(
                (
                    c
                    for c in scopes[-1].get_children()
                    if c.get_name() == name
                    and c.get_lineno() == node.lineno
                    and str(c.get_type()) in {"type parameter", "type parameters"}
                ),
                None,
            )
            if child is None:
                raise ScopeResolutionError("Cannot resolve import type-parameter scope")
            parents[child.get_id()] = scopes[-1]
            scopes.append(child)
            return child

        def visit_TypeAlias(self, node):
            self.visit(node.name)
            type_scope = self.type_parameters(node, node.name.id)
            self.enter(node, node.name.id, lambda: self.visit(node.value))
            if type_scope is not None:
                scopes.pop()

        def definition(self, node):
            bind(node.name)
            for expr in node.decorator_list:
                self.visit(expr)
            if not isinstance(node, ast.ClassDef):
                self.defaults(node)
            type_scope = self.type_parameters(node, node.name)
            if isinstance(node, ast.ClassDef):
                for expr in node.bases:
                    self.visit(expr)
                for kw in node.keywords:
                    self.visit(kw.value)
            else:
                self.signature(node)
            self.enter(node, node.name, lambda: [self.visit(n) for n in node.body])
            if type_scope is not None:
                scopes.pop()

        visit_FunctionDef = definition
        visit_AsyncFunctionDef = definition
        visit_ClassDef = definition

        def visit_Lambda(self, node):
            self.defaults(node)
            self.signature(node)
            self.enter(node, "lambda", lambda: self.visit(node.body))

        def comprehension(self, node):
            self.visit(node.generators[0].iter)

            def body():
                for i, gen in enumerate(node.generators):
                    self.visit(gen.target)
                    if i:
                        self.visit(gen.iter)
                    for cond in gen.ifs:
                        self.visit(cond)
                if isinstance(node, ast.DictComp):
                    self.visit(node.value)
                    self.visit(node.key)
                else:
                    self.visit(node.elt)

            self.enter(
                node,
                {
                    ast.ListComp: "listcomp",
                    ast.SetComp: "setcomp",
                    ast.DictComp: "dictcomp",
                    ast.GeneratorExp: "genexpr",
                }[type(node)],
                body,
            )

        visit_ListComp = comprehension
        visit_SetComp = comprehension
        visit_DictComp = comprehension
        visit_GeneratorExp = comprehension

        def visit_Import(self, node):
            for alias in node.names:
                name = alias.asname or alias.name.split(".")[0]
                other_imports.append((owner(scopes[-1], name), name))

        def visit_ImportFrom(self, node):
            target = node.module
            if node.level:
                parts = module.split(".")
                target = ".".join(parts[: -node.level] + ([target] if target else []))
            for alias in node.names:
                name = alias.asname or alias.name
                replacement = table.get_obfuscated_import(target, alias.name) if target else None
                if replacement:
                    binding = owner(scopes[-1], name)
                    imports.append((node, alias, name, replacement, binding, scopes[-1]))
                elif alias.name != "*":
                    other_imports.append((owner(scopes[-1], name), name))

    Scan().visit(normalized)
    preserve = {}
    # Conflicting imports, assignments, dynamic namespaces, and imports into
    # another scope preserve spelling. The identity mapping is deliberate.
    candidates: Dict[Tuple[int, str], Set[str]] = defaultdict(set)
    for node, alias, name, replacement, binding, scope in imports:
        candidates[(binding.get_id(), name)].add(name if alias.asname else replacement)
    for binding, name in other_imports:
        candidates[(binding.get_id(), name)].add(name)
    uncertain = set()

    def rebound(binding, name):
        assigned = binding.lookup(name).is_assigned()
        return name in rebinds if binding is root else assigned

    for node, alias, name, replacement, binding, scope in imports:
        sid = binding.get_id()
        symbol = binding.lookup(name)
        # Read-only module globals() and standalone del retain normal rewriting.
        # Dynamic execution and namespace writes must preserve bindings.
        if (
            (sid in dynamic)
            or binding is not scope
            or str(binding.get_type()) in {"class", "function"}
            or rebound(binding, name)
            or symbol.is_parameter()
            or len(candidates[(sid, name)]) > 1
        ):
            uncertain.add((sid, name))
    for node, alias, name, replacement, binding, scope in imports:
        sid = binding.get_id()
        spelling = name if alias.asname or (sid, name) in uncertain else replacement
        # Module assignments are already rewritten by the export pass. Keep
        # the import and all references on that same registered spelling.
        if binding is root and rebound(binding, name):
            if sid in dynamic:
                raise ValueError(
                    f"Cannot safely synchronize dynamic module import binding {name!r}; "
                    "preserve it with exclude_names"
                )
            spelling = table.get_obfuscated_import(module, name) or name
        mappings[sid][name] = spelling
        if spelling != replacement or alias.asname is not None:
            preserve[(coordinates[id(node)], node.names.index(alias))] = (name, spelling)
    edits = {}
    protected = set()
    for node, scope in references:
        if (
            isinstance(node, ast.Name)
            and str(scope.get_type()) == "class"
            and not getattr(node, "_pyobfus_class_binding", False)
        ):
            scope = parents.get(scope.get_id(), root)
            while str(scope.get_type()) == "class":
                scope = parents.get(scope.get_id(), root)
        if isinstance(node, ast.Name):
            binding = owner(scope, node.id)
            if binding is not root and str(binding.get_type()) == "function":
                protected.add(coordinates[id(node)])
        binder = isinstance(node, string_binders)
        names = (
            [node.id]
            if isinstance(node, ast.Name)
            else (
                [node.rest if type(node).__name__ == "MatchMapping" else node.name]
                if binder
                else node.names
            )
        )
        replacements = [mappings[owner(scope, name).get_id()].get(name, name) for name in names]
        if any(name in mappings[owner(scope, name).get_id()] for name in names):
            edits[coordinates[id(node)]] = (
                replacements[0] if isinstance(node, ast.Name) or binder else replacements
            )
    union = {name: value for mapping in mappings.values() for name, value in mapping.items()}
    return edits, preserve, union, protected
