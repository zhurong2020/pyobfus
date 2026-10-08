"""Mark class-namespace references before cross-file names are rewritten.

Unlike function locals, class LOAD_NAME bindings become visible in execution
order. Conditional suites deliberately use a conservative may-bind policy;
this is not control-flow analysis. Nested callable/class bodies do not inherit
the surrounding class namespace.
"""

import ast
from typing import Optional, Set

from pyobfus.transformers.local_name_transformer import _ScopeBindingCollector


def mark_class_bindings(tree: ast.AST) -> None:
    """Attach preservation markers to the original AST, without changing names."""

    class Scan(ast.NodeVisitor):
        bound: Optional[Set[str]] = None
        outer: Set[str] = set()
        callable_depth = 0

        def bind(self, name: str) -> None:
            if self.bound is not None and name not in self.outer:
                self.bound.add(name)

        def visit_Name(self, node: ast.Name) -> None:
            if self.bound is None or node.id in self.outer:
                return
            if not isinstance(node.ctx, ast.Load) or node.id in self.bound:
                setattr(node, "_pyobfus_class_binding", True)
            if isinstance(node.ctx, ast.Store):
                self.bind(node.id)
            elif isinstance(node.ctx, ast.Del):
                self.bound.discard(node.id)

        def visit_Assign(self, node: ast.Assign) -> None:
            self.visit(node.value)
            for target in node.targets:
                self.visit(target)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if node.value is not None:
                self.visit(node.value)
                self.visit(node.target)
            elif self.bound is not None and isinstance(node.target, ast.Name):
                # Preserve the annotation key without making it a value binding.
                if node.target.id not in self.outer:
                    setattr(node.target, "_pyobfus_class_binding", True)
            else:
                self.visit(node.target)
            # An annotation without a value does not create a LOAD_NAME binding.
            self.visit(node.annotation)

        def visit_NamedExpr(self, node: ast.NamedExpr) -> None:
            self.visit(node.value)
            self.visit(node.target)

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            # The target is loaded before it is stored. Existing class bindings
            # retain their spelling; handling global augmented stores is outside
            # this class-shadow fix.
            self.visit(node.value)
            self.visit(node.target)

        def signature(self, node) -> None:
            self.visit(node.args)
            if getattr(node, "returns", None) is not None:
                self.visit(node.returns)
            for param in getattr(node, "type_params", []):
                self.visit(param)

        def visit_FunctionDef(self, node) -> None:
            for deco in node.decorator_list:
                self.visit(deco)
            self.signature(node)
            saved = self.bound, self.outer
            self.bound, self.outer = None, set()
            self.callable_depth += 1
            for stmt in node.body:
                self.visit(stmt)
            self.callable_depth -= 1
            self.bound, self.outer = saved
            self.bind(node.name)

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Lambda(self, node: ast.Lambda) -> None:
            self.signature(node)
            saved = self.bound
            self.bound = None
            self.visit(node.body)
            self.bound = saved

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            for expr in node.decorator_list + node.bases:
                self.visit(expr)
            for keyword in node.keywords:
                self.visit(keyword.value)
            for param in getattr(node, "type_params", []):
                self.visit(param)
            collector = _ScopeBindingCollector()
            for stmt in node.body:
                collector.visit(stmt)
            saved = self.bound, self.outer
            self.bound, self.outer = set(), collector.declared_outer
            for stmt in node.body:
                self.visit(stmt)
            self.bound, self.outer = saved
            self.bind(node.name)

        def comprehension(self, node) -> None:
            # Only the outermost iterable is evaluated in the enclosing scope.
            self.visit(node.generators[0].iter)
            saved = self.bound
            self.bound = None
            for i, generator in enumerate(node.generators):
                if i:
                    self.visit(generator.iter)
                self.visit(generator.target)
                for condition in generator.ifs:
                    self.visit(condition)
            if isinstance(node, ast.DictComp):
                self.visit(node.key)
                self.visit(node.value)
            else:
                self.visit(node.elt)
            self.bound = saved

        visit_ListComp = comprehension
        visit_SetComp = comprehension
        visit_DictComp = comprehension
        visit_GeneratorExp = comprehension

        def visit_Import(self, node: ast.Import) -> None:
            for alias in node.names:
                self.bind(alias.asname or alias.name.split(".")[0])

        def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
            for alias in node.names:
                if self.bound is None and self.callable_depth and alias.name != "*":
                    # Callable imports keep their local spelling even when
                    # function-local renaming is disabled. The local plan can
                    # still replace this alias when it is enabled.
                    alias.asname = alias.asname or alias.name
                if (
                    self.bound is not None
                    and alias.name != "*"
                    and (alias.asname or alias.name) not in self.outer
                ):
                    # ImportRewriter still updates the exported symbol spelling;
                    # the class attribute must keep its original local name.
                    alias.asname = alias.asname or alias.name
                    self.bind(alias.asname)

        def conditional(self, node: ast.AST) -> None:
            if self.bound is None:
                self.generic_visit(node)
                return
            collector = _ScopeBindingCollector()
            collector.visit(node)
            may_bind = collector.bound - self.outer
            self.bound.update(may_bind)
            self.generic_visit(node)
            self.bound.update(may_bind)

        visit_If = conditional
        visit_Try = conditional
        visit_For = conditional
        visit_AsyncFor = conditional
        visit_While = conditional
        visit_Match = conditional
        visit_TryStar = conditional

        def visit_With(self, node) -> None:
            for item in node.items:
                self.visit(item.context_expr)
                if item.optional_vars is not None:
                    self.visit(item.optional_vars)
            for stmt in node.body:
                self.visit(stmt)

        visit_AsyncWith = visit_With

    Scan().visit(tree)
