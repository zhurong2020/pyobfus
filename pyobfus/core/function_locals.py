"""Plan lexical local-name edits before cross-file workers are started.

Python's symbol table supplies bindings, including comprehension walrus and
closure rules. Plans contain only source coordinates and strings (pickleable).
"""

import ast
import symtable
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Set, Tuple, Any

from pyobfus.config import ObfuscationConfig

# Nested match captures can share a start position; the full span and node
# type identify the binding across the planner's and worker's parses.
EditKey = Tuple[int, int, int, int, str, str]


def _edit_key(node: ast.AST, attr: str) -> EditKey:
    return (
        getattr(node, "lineno", -1),
        getattr(node, "col_offset", -1),
        getattr(node, "end_lineno", -1),
        getattr(node, "end_col_offset", -1),
        type(node).__name__,
        attr,
    )


@dataclass
class LocalPlan:
    edits: Dict[EditKey, str] = field(default_factory=dict)
    mappings: Dict[str, str] = field(default_factory=dict)
    protected_references: Set[Tuple[int, int]] = field(default_factory=set)
    skipped: int = 0
    files_skipped: int = 0


def plan_locals(
    source: str,
    config: ObfuscationConfig,
    allocate: Callable[[], str],
    module_exports: Dict[str, str],
    filename: str = "<crossfile>",
) -> LocalPlan:
    """Allocate in deterministic AST order, without changing module exports."""
    tree = ast.parse(source, filename)
    plan = LocalPlan()
    # Generic annotation scopes vary across 3.12-3.14. Preserve these files
    # until their separate lazy-evaluation scope semantics are supported.
    if any(getattr(n, "type_params", []) for n in ast.walk(tree)):
        plan.skipped = sum(
            isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree)
        )
        return plan
    protected: Set[str] = set()
    future_annotations = any(
        isinstance(n, ast.ImportFrom)
        and n.module == "__future__"
        and any(a.name == "annotations" for a in n.names)
        for n in tree.body
    )
    # String annotations cannot be rewritten. Keep local type names they may
    # resolve, as well as class names that determine Python private mangling.
    for node in ast.walk(tree):
        annotation = getattr(node, "annotation", None)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotation = node.returns
        if annotation is not None:
            for part in ast.walk(annotation):
                if isinstance(part, ast.Name) and future_annotations:
                    protected.add(part.id)
                if isinstance(part, ast.Constant) and isinstance(part.value, str):
                    try:
                        expr = ast.parse(part.value, mode="eval")
                    except SyntaxError:
                        continue
                    protected.update(n.id for n in ast.walk(expr) if isinstance(n, ast.Name))
        if isinstance(node, ast.ClassDef) and any(
            isinstance(n, ast.Attribute)
            and n.attr.startswith("__")
            and not n.attr.endswith("__")
            or isinstance(n, ast.Name)
            and n.id.startswith("__")
            and not n.id.endswith("__")
            for n in ast.walk(node)
        ):
            protected.add(node.name)
    root = symtable.symtable(source, filename, "exec")
    scopes: List[Any] = [root]
    parents: Dict[int, Any] = {}
    nodes: Dict[int, ast.AST] = {}
    names: Dict[int, Dict[str, str]] = {}
    blocked: Set[int] = set()
    references: List[Tuple[ast.AST, str, str, Any]] = []
    used: Set[int] = set()

    class ComprehensionScope:
        """Restore lexical scope for PEP 709's inlined symbol tables."""

        def __init__(self, parent: Any, node: Any) -> None:
            self.parent = parent
            self.targets = {
                n.id
                for g in node.generators
                for n in ast.walk(g.target)
                if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
            }

        def get_id(self) -> int:
            return -id(self)

        def get_type(self) -> str:
            return "function"

        def get_children(self) -> Any:
            return self.parent.get_children()

        def lookup(self, name: str) -> Any:
            local = name in self.targets

            class Symbol:
                def is_local(self) -> bool:
                    return local

                def is_global(self) -> bool:
                    return False

            return Symbol()

    synthetic: List[Any] = []
    # One shared table per scope holds its variable annotations on 3.14+.
    variable_annotations: Dict[int, Any] = {}

    class Scan(ast.NodeVisitor):
        # Unevaluated annotations still own symbol tables before Python 3.14.
        # Passive traversal consumes those tables without recording names.
        passive = 0

        def record(self, node: ast.AST, attr: str, name: str) -> None:
            if not self.passive:
                references.append((node, attr, name, scopes[-1]))

        def enter(self, node: ast.AST, name: str, body: Callable[[], Any]) -> None:
            parent = scopes[-1]
            child = next(
                (
                    c
                    for c in parent.get_children()
                    if c.get_name() == name
                    and c.get_lineno() == getattr(node, "lineno", -1)
                    and c.get_id() not in used
                ),
                None,
            )
            if child is None:
                if self.passive and not isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
                    return
                if not isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp)):
                    raise ValueError(f"Cannot resolve lexical scope: {name}")
                child = ComprehensionScope(parent, node)
                synthetic.append(child)
            used.add(child.get_id())
            parents[child.get_id()] = parent
            nodes[child.get_id()] = node
            scopes.append(child)
            body()
            scopes.pop()

        def visit_Name(self, node: ast.Name) -> None:
            if node.id in {"eval", "exec", "locals"} and not self.passive:
                blocked.update(s.get_id() for s in scopes[1:])
            self.record(node, "id", node.id)

        def visit_Nonlocal(self, node: ast.Nonlocal) -> None:
            for i, name in enumerate(node.names):
                self.record(node, f"names:{i}", name)

        def visit_Global(self, node: ast.Global) -> None:
            for i, name in enumerate(node.names):
                self.record(node, f"names:{i}", name)

        def visit_Call(self, node: ast.Call) -> None:
            name = (
                node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            )
            if not self.passive and (
                name in {"eval", "exec", "locals"}
                or (name in {"vars", "dir"} and not node.args and not node.keywords)
            ):
                # Introspection in a child can observe captured outer names.
                blocked.update(s.get_id() for s in scopes[1:])
            self.generic_visit(node)

        def definition(self, node: Any) -> None:
            self.record(node, "name", node.name)
            for expr in node.decorator_list:
                self.visit(expr)
            if isinstance(node, ast.ClassDef):
                for expr in node.bases:
                    self.visit(expr)
                for kw in node.keywords:
                    self.visit(kw.value)
            else:
                self.visit_signature(node)
            self.enter(node, node.name, lambda: [self.visit(n) for n in node.body])

        def visit_signature(self, node: Any) -> None:
            for default in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
                self.visit(default)
            if future_annotations:
                return
            # CPython's symbol-table order: positional, *args, **kwargs,
            # keyword-only, then return. Same-line lambdas depend on it.
            args = node.args
            ordered = args.posonlyargs + args.args + [args.vararg, args.kwarg] + args.kwonlyargs
            annotations = [a.annotation for a in ordered if a is not None and a.annotation]
            if node.returns is not None:
                annotations.append(node.returns)
            table = next(
                (
                    c
                    for c in scopes[-1].get_children()
                    if c.get_name() == "__annotate__" and c.get_lineno() == node.lineno
                ),
                None,
            )
            if table is not None:
                parents[table.get_id()] = scopes[-1]
                scopes.append(table)
            for annotation in annotations:
                self.visit(annotation)
            if table is not None:
                scopes.pop()

        visit_FunctionDef = definition
        visit_AsyncFunctionDef = definition
        visit_ClassDef = definition

        def visit_Lambda(self, node: ast.Lambda) -> None:
            for default in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
                self.visit(default)
            self.enter(node, "lambda", lambda: self.visit(node.body))

        def comprehension(self, node: Any) -> None:
            self.visit(node.generators[0].iter)

            def body() -> None:
                for i, gen in enumerate(node.generators):
                    self.visit(gen.target)
                    if i:
                        self.visit(gen.iter)
                    for cond in gen.ifs:
                        self.visit(cond)
                if isinstance(node, ast.DictComp):
                    # CPython symbol-table traversal visits the value first.
                    # Same-line lambdas must consume their matching child table.
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

        def visit_Import(self, node: ast.Import) -> None:
            for i, alias in enumerate(node.names):
                if "." in alias.name and not alias.asname:
                    # `import a.b as x` binds b, whereas `import a.b` binds a.
                    blocked.add(scopes[-1].get_id())
                else:
                    self.record(node, f"aliases:{i}", alias.asname or alias.name)

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            for i, alias in enumerate(node.names):
                if alias.name != "*":
                    self.record(node, f"aliases:{i}", alias.asname or alias.name)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            # CPython visits target, annotation, then value.
            self.visit(node.target)
            if not future_annotations:
                scope = scopes[-1]
                table = variable_annotations.get(scope.get_id())
                if table is None:
                    # The shared table takes the first annotation's line number.
                    table = next(
                        (
                            c
                            for c in scope.get_children()
                            if c.get_name() == "__annotate__"
                            and c.get_lineno() == node.lineno
                            and c.get_id() not in used
                        ),
                        None,
                    )
                    if table is not None:
                        used.add(table.get_id())
                        variable_annotations[scope.get_id()] = table
                        parents[table.get_id()] = scope
                if table is not None:
                    scopes.append(table)
                # Function-local variable annotations are never evaluated.
                unevaluated = str(scope.get_type()) == "function"
                self.passive += unevaluated
                self.visit(node.annotation)
                self.passive -= unevaluated
                if table is not None:
                    scopes.pop()
            if node.value is not None:
                self.visit(node.value)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            if node.name:
                self.record(node, "name", node.name)
            self.generic_visit(node)

        def visit_MatchAs(self, node: Any) -> None:
            if node.name:
                self.record(node, "name", node.name)
            self.generic_visit(node)

        visit_MatchStar = visit_MatchAs

        def visit_MatchMapping(self, node: Any) -> None:
            if node.rest:
                self.record(node, "rest", node.rest)
            self.generic_visit(node)

    Scan().visit(tree)

    def owner(scope: Any, name: str) -> Any:
        try:
            symbol = scope.lookup(name)
        except KeyError:
            return None
        if symbol.is_global():
            return None
        if symbol.is_local():
            return scope
        parent = parents.get(scope.get_id())
        while parent is not None and str(parent.get_type()) == "class":
            parent = parents.get(parent.get_id())
        return owner(parent, name) if parent is not None else None

    tables = {root.get_id(): root}

    def collect(table: Any) -> None:
        tables[table.get_id()] = table
        for child in table.get_children():
            collect(child)

    collect(root)
    tables.update({s.get_id(): s for s in synthetic})
    bindings = set()
    # Nested def/class names are observable through __name__/__qualname__:
    # Flask endpoints, Click commands and name-keyed registries depend on them.
    definitions = set()
    for ref_node, attr, ref_name, scope in references:
        binding = owner(scope, ref_name)
        if binding is not None and (
            attr != "id" or isinstance(getattr(ref_node, "ctx", None), (ast.Store, ast.Del))
        ):
            bindings.add((binding.get_id(), ref_name))
            if attr == "name" and isinstance(
                ref_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ):
                definitions.add((binding.get_id(), ref_name))
    for sid, node in nodes.items():
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if sid in blocked:
            plan.skipped += 1
            continue
        names[sid] = {}
        for symbol in sorted(tables[sid].get_symbols(), key=lambda s: s.get_name()):
            name = symbol.get_name()
            if (
                (sid, name) in bindings
                and (sid, name) not in definitions
                and symbol.is_local()
                and not symbol.is_parameter()
                and not symbol.is_global()
                and not symbol.is_nonlocal()
                and name not in protected
                and name not in config.exclude_names
                and name not in {"super", "__class__"}
                and not (name.startswith("__") and name.endswith("__"))
            ):
                replacement = allocate()
                names[sid][name] = replacement
                plan.mappings[replacement] = name
    for node, attr, name, scope in references:
        binding = owner(scope, name)
        if attr == "id" and binding is not None and str(binding.get_type()) == "function":
            plan.protected_references.add(
                (getattr(node, "lineno", -1), getattr(node, "col_offset", -1))
            )
        local_replacement = (
            names.get(binding.get_id(), {}).get(name) if binding is not None else None
        )
        if (
            attr.startswith("aliases:")
            and binding is not None
            and str(binding.get_type()) == "function"
        ):
            # Internal import rewriting may change the imported symbol spelling.
            # An explicit alias retains even skipped/excluded local bindings.
            local_replacement = local_replacement or name
        # Explicit globals must keep their declarations and references in
        # sync with the existing module mapping, even inside nested closures.
        if binding is None and scope is not root:
            local_replacement = module_exports.get(name)
        if local_replacement:
            plan.edits[_edit_key(node, attr)] = local_replacement
    return plan


def apply_local_plan(tree: ast.Module, plan: LocalPlan) -> ast.Module:
    """Apply the frozen plan to the original parsed tree."""
    for node in ast.walk(tree):
        if getattr(node, "_pyobfus_class_binding", False):
            continue
        line, col = getattr(node, "lineno", -1), getattr(node, "col_offset", -1)
        if isinstance(node, ast.Name) and (line, col) in plan.protected_references:
            # Legacy module/import passes must not rename skipped lexical locals.
            setattr(node, "_pyobfus_local_binding", True)
        for attr in ("id", "name", "asname", "rest"):
            replacement = plan.edits.get(_edit_key(node, attr))
            if replacement is not None:
                setattr(node, attr, replacement)
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for i, alias in enumerate(node.names):
                replacement = plan.edits.get(_edit_key(node, f"aliases:{i}"))
                if replacement is not None:
                    alias.asname = replacement
        if isinstance(node, (ast.Nonlocal, ast.Global)):
            node.names = [
                plan.edits.get(_edit_key(node, f"names:{i}"), name)
                for i, name in enumerate(node.names)
            ]
    return tree
