"""Plan internal wildcard imports without importing or executing target code."""

import ast
from typing import Dict, List, Optional, Set, Tuple, Union

from pyobfus.transformers.scoped_imports import Key, key


class UnknownExports(ValueError):
    """The runtime namespace cannot be enumerated statically."""


class _ModuleEffects(ast.NodeVisitor):
    """Detect executable namespace effects without traversing function bodies."""

    def __init__(self) -> None:
        self.dynamic = False

    def visit_Call(self, node: ast.Call) -> None:
        self.dynamic = True

    def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
        self.dynamic = True

    def visit_FunctionDef(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef]) -> None:
        if node.decorator_list:
            self.dynamic = True  # Applying a decorator is an implicit call.
        for expr in (
            node.decorator_list
            + node.args.defaults
            + [d for d in node.args.kw_defaults if d is not None]
        ):
            self.visit(expr)
        for arg in (
            node.args.posonlyargs
            + node.args.args
            + node.args.kwonlyargs
            + [a for a in (node.args.vararg, node.args.kwarg) if a is not None]
        ):
            if arg.annotation is not None:
                self.visit(arg.annotation)
        if node.returns is not None:
            self.visit(node.returns)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.decorator_list or node.bases or node.keywords or getattr(node, "type_params", []):
            # Decorators, metaclasses and inherited __init_subclass__ can
            # mutate the defining module while constructing the class.
            self.dynamic = True
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        # A class body can bind module globals without a visible module store.
        self.dynamic = True

    def visit_Lambda(self, node: ast.Lambda) -> None:
        for expr in node.args.defaults + [d for d in node.args.kw_defaults if d is not None]:
            self.visit(expr)


def plan_stars(sources: Dict[str, str]) -> Tuple[Dict[str, Dict[Key, List[str]]], bool]:
    """Expand only unconditional, acyclic, statically enumerable namespaces.

    Unknown namespaces retain wildcard execution and trigger preservation of
    project globals. External wildcard statements are never changed.
    """
    trees = {module: ast.parse(source) for module, source in sources.items()}
    aliases = {m[:-9]: m for m in trees if m.endswith(".__init__")}
    if "__init__" in trees:
        aliases[""] = "__init__"
    plans: Dict[str, Dict[Key, List[str]]] = {m: {} for m in trees}
    cache: Dict[str, Set[str]] = {}
    active: Set[str] = set()

    def target(module: str, node: ast.ImportFrom) -> str:
        name = (
            ".".join(module.split(".")[: -node.level] + ([node.module] if node.module else []))
            if node.level
            else node.module or ""
        )
        return aliases.get(name, name)

    def literal_all(node: Optional[ast.AST]) -> Set[str]:
        if isinstance(node, (ast.List, ast.Tuple)) and all(
            isinstance(n, ast.Constant) and isinstance(n.value, str) for n in node.elts
        ):
            return {
                n.value
                for n in node.elts
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
            }
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            return literal_all(node.left) | literal_all(node.right)
        raise UnknownExports("dynamic __all__")

    def exports(module: str) -> Set[str]:
        if module.endswith(".__init__") and module[:-9] in trees:
            raise UnknownExports("ambiguous package/module root")
        if module in cache:
            return cache[module]
        if module in active:
            raise UnknownExports("cyclic wildcard namespace")
        active.add(module)
        try:
            effects = _ModuleEffects()
            effects.visit(trees[module])
            if effects.dynamic:
                raise UnknownExports("executable module namespace effects")
            if any(
                isinstance(n, ast.Call)
                and isinstance(n.func, ast.Name)
                and n.func.id in {"exec", "eval", "globals", "locals", "vars", "setattr", "delattr"}
                for n in ast.walk(trees[module])
            ):
                raise UnknownExports("dynamic namespace access")
            names: Set[str] = set()
            explicit: Optional[Set[str]] = None
            for node in trees[module].body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if node.name == "__getattr__":
                        raise UnknownExports("module __getattr__")
                    names.add(node.name)
                elif isinstance(node, ast.Import):
                    names.update(a.asname or a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.names[0].name == "*":
                        source = target(module, node)
                        if source not in trees:
                            raise UnknownExports("external wildcard namespace")
                        imported = exports(source)
                        names.update(imported)
                        if imported:
                            plans[module][key(node)] = sorted(imported)
                    else:
                        if any((a.asname or a.name) == "__all__" for a in node.names):
                            raise UnknownExports("imported __all__")
                        names.update(a.asname or a.name for a in node.names)
                elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                    if isinstance(node, ast.AnnAssign) and node.value is None:
                        continue  # An annotation alone creates no runtime binding.
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if any(
                        isinstance(n, (ast.Attribute, ast.Subscript))
                        for t in targets
                        for n in ast.walk(t)
                    ):
                        raise UnknownExports("namespace mutation")
                    bound = {
                        n.id
                        for t in targets
                        for n in ast.walk(t)
                        if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)
                    }
                    names.update(bound)
                    if "__all__" in bound:
                        explicit = literal_all(node.value)
                elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                    continue  # docstrings
                elif isinstance(node, ast.Pass):
                    continue
                else:
                    raise UnknownExports("conditional or dynamic module namespace")
            if "__getattr__" in names:
                raise UnknownExports("bound module __getattr__")
            if explicit is not None and not explicit <= names:
                raise UnknownExports("unproven __all__ binding")
            result = (
                explicit if explicit is not None else {n for n in names if not n.startswith("_")}
            )
            cache[module] = result
            return result
        finally:
            active.remove(module)

    unknown = False
    for module, tree in trees.items():
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.names[0].name == "*":
                source = target(module, node)
                if source not in trees:
                    continue
                try:
                    names = exports(source)
                    if node not in tree.body:
                        raise UnknownExports("conditional wildcard binding")
                    if names:
                        plans[module][key(node)] = sorted(names)
                except UnknownExports:
                    unknown = True
    if unknown:
        # Partial expansion could still rewrite a dynamic __all__ producer.
        return {m: {} for m in trees}, True
    return plans, False


def expand_stars(tree: ast.AST, plan: Dict[Key, List[str]]) -> ast.AST:
    """Keep source coordinates for local, attribute, and line-map plans."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and key(node) in plan:
            node.names = [ast.alias(name=name) for name in plan[key(node)]]
    return tree
