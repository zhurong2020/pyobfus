"""Runtime import obfuscation for Pro builds.

Rewrites top-level import statements into runtime importlib calls. The pass is
intended to run after name mangling and before AES string encryption, so imported
binding names still match the rest of the transformed module while module and
attribute string constants are encrypted by the existing string pass.
"""

from __future__ import annotations

import ast
from typing import Dict, List, Optional


class ImportObfuscator(ast.NodeTransformer):
    """Rewrite module-level imports into importlib-based assignments."""

    def __init__(self) -> None:
        self.imports_obfuscated = 0
        self._needs_helper = False

    def transform(self, tree: ast.Module) -> ast.Module:
        transformed = self.visit(tree)
        assert isinstance(transformed, ast.Module)
        if self._needs_helper:
            self._ensure_runtime_helpers(transformed)
        ast.fix_missing_locations(transformed)
        return transformed

    def visit_Module(self, node: ast.Module) -> ast.Module:
        new_body: List[ast.stmt] = []
        for stmt in node.body:
            replacement = self._rewrite_top_level_import(stmt)
            if replacement is None:
                new_body.append(stmt)
            else:
                new_body.extend(replacement)
        node.body = new_body
        return node

    def _rewrite_top_level_import(self, stmt: ast.stmt) -> Optional[List[ast.stmt]]:
        if isinstance(stmt, ast.Import):
            rewritten: List[ast.stmt] = []
            for alias in stmt.names:
                rewritten.extend(self._rewrite_import_alias(alias))
            return rewritten

        if isinstance(stmt, ast.ImportFrom):
            if stmt.module == "__future__" or stmt.level != 0:
                return None
            if any(alias.name == "*" for alias in stmt.names):
                return None
            rewritten = [self._rewrite_from_alias(stmt.module or "", alias) for alias in stmt.names]
            return rewritten

        return None

    def _rewrite_import_alias(self, alias: ast.alias) -> List[ast.stmt]:
        self._needs_helper = True
        self.imports_obfuscated += 1

        full_name = alias.name
        if alias.asname:
            return [
                ast.Assign(
                    targets=[ast.Name(id=alias.asname, ctx=ast.Store())],
                    value=self._import_module_call(full_name),
                )
            ]

        bound_name = full_name.split(".", 1)[0]
        if "." not in full_name:
            return [
                ast.Assign(
                    targets=[ast.Name(id=bound_name, ctx=ast.Store())],
                    value=self._import_module_call(full_name),
                )
            ]

        # `import pkg.sub` binds `pkg` but also loads `pkg.sub`.
        return [
            ast.Expr(value=self._import_module_call(full_name)),
            ast.Assign(
                targets=[ast.Name(id=bound_name, ctx=ast.Store())],
                value=self._import_module_call(bound_name),
            ),
        ]

    def _rewrite_from_alias(self, module_name: str, alias: ast.alias) -> ast.Assign:
        self._needs_helper = True
        self.imports_obfuscated += 1
        return ast.Assign(
            targets=[ast.Name(id=alias.asname or alias.name, ctx=ast.Store())],
            value=ast.Call(
                func=ast.Name(id="_pyobfus_import_from", ctx=ast.Load()),
                args=[
                    ast.Constant(value=module_name),
                    ast.Constant(value=alias.name),
                ],
                keywords=[],
            ),
        )

    @staticmethod
    def _import_module_call(module_name: str) -> ast.Call:
        return ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="_pyobfus_importlib", ctx=ast.Load()),
                attr="import_module",
                ctx=ast.Load(),
            ),
            args=[ast.Constant(value=module_name)],
            keywords=[],
        )

    def _ensure_runtime_helpers(self, tree: ast.Module) -> None:
        insert_at = _module_header_end(tree)
        tree.body[insert_at:insert_at] = [
            ast.Import(names=[ast.alias(name="importlib", asname="_pyobfus_importlib")]),
            _create_import_from_helper(),
        ]

    def get_statistics(self) -> Dict[str, int]:
        return {"imports_obfuscated": self.imports_obfuscated}


def _module_header_end(tree: ast.Module) -> int:
    """Return insertion index after module docstring and future imports."""
    idx = 0
    if (
        tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)
    ):
        idx = 1

    while idx < len(tree.body):
        node = tree.body[idx]
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            idx += 1
            continue
        break
    return idx


def _create_import_from_helper() -> ast.FunctionDef:
    return ast.FunctionDef(
        name="_pyobfus_import_from",
        args=ast.arguments(
            posonlyargs=[],
            args=[
                ast.arg(arg="module_name", annotation=None),
                ast.arg(arg="attr_name", annotation=None),
            ],
            vararg=None,
            kwonlyargs=[],
            kw_defaults=[],
            kwarg=None,
            defaults=[],
        ),
        body=[
            ast.Assign(
                targets=[ast.Name(id="module", ctx=ast.Store())],
                value=ast.Call(
                    func=ast.Name(id="__import__", ctx=ast.Load()),
                    args=[ast.Name(id="module_name", ctx=ast.Load())],
                    keywords=[
                        ast.keyword(
                            arg="fromlist",
                            value=ast.List(
                                elts=[ast.Name(id="attr_name", ctx=ast.Load())],
                                ctx=ast.Load(),
                            ),
                        )
                    ],
                ),
            ),
            ast.Return(
                value=ast.Call(
                    func=ast.Name(id="getattr", ctx=ast.Load()),
                    args=[
                        ast.Name(id="module", ctx=ast.Load()),
                        ast.Name(id="attr_name", ctx=ast.Load()),
                    ],
                    keywords=[],
                )
            ),
        ],
        decorator_list=[],
        returns=None,
    )
