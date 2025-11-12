"""
Anti-Debugging Injector (Pro Feature)

Injects anti-debugging checks into obfuscated code to detect and prevent
debugging attempts. Makes reverse engineering significantly harder.

Techniques:
1. sys.gettrace() detection - Detects Python debuggers
2. Periodic runtime checks - Continuous monitoring
3. Immediate exit on detection - Prevents analysis
"""

import ast
from typing import Optional, cast

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.transformer import BaseTransformer


class AntiDebugInjector(BaseTransformer):
    """
    Injects anti-debugging checks into Python code.

    Features:
    - Debugger detection via sys.gettrace()
    - Injected at module start and function entries
    - Immediate exit on detection
    - Configurable behavior
    """

    def __init__(self, config: ObfuscationConfig, analyzer: Optional[SymbolAnalyzer] = None):
        """
        Initialize anti-debug injector.

        Args:
            config: Obfuscation configuration
            analyzer: Symbol analyzer (optional)
        """
        super().__init__(config, analyzer)
        self.check_function_name = "_check_debugger"
        self.injected_functions = 0

    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform AST by injecting anti-debugging checks.

        Args:
            tree: Input AST

        Returns:
            ast.Module: Transformed AST with anti-debug checks
        """
        # Step 1: Inject anti-debug check function at top
        tree = self._inject_check_function(tree)

        # Step 2: Visit and inject calls
        transformed = cast(ast.Module, self.visit(tree))

        # Fix missing locations
        ast.fix_missing_locations(transformed)

        return transformed

    def visit_Module(self, node: ast.Module) -> ast.Module:
        """
        Visit Module node. Don't inject at module level.

        Module-level check is problematic with multiple transformers.
        Only inject in functions.

        Args:
            node: Module AST node

        Returns:
            ast.Module: Module node
        """
        # Don't inject at module level - it conflicts with other transformers
        # Only inject in functions

        # Continue visiting
        self.generic_visit(node)
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """
        Visit FunctionDef and inject check at function start.

        Args:
            node: FunctionDef AST node

        Returns:
            ast.FunctionDef: Function with anti-debug check
        """
        # Skip the check function itself
        if node.name == self.check_function_name:
            return node

        # Skip infrastructure functions (start with _)
        # These are injected by other transformers and might have ordering issues
        if node.name.startswith("_"):
            return node

        # Skip very small functions (likely trivial)
        if len(node.body) < 2:
            return node

        # Inject check at function start
        check_call = self._create_check_call()
        node.body.insert(0, check_call)
        self.injected_functions += 1

        # Continue visiting
        self.generic_visit(node)
        return node

    def _inject_check_function(self, tree: ast.Module) -> ast.Module:
        """
        Inject anti-debugging check function at top of module.

        Args:
            tree: AST module

        Returns:
            ast.Module: Module with check function prepended
        """
        check_function = self._create_check_function()
        tree.body.insert(0, check_function)
        return tree

    def _create_check_function(self) -> ast.FunctionDef:
        """
        Create the anti-debugging check function.

        Returns:
            ast.FunctionDef: Check function AST node
        """
        # Function code:
        # def _check_debugger():
        #     import sys
        #     if sys.gettrace() is not None:
        #         sys.exit(1)

        function_body = [
            # import sys
            ast.Import(names=[ast.alias(name="sys", asname=None)]),
            # if sys.gettrace() is not None:
            ast.If(
                test=ast.Compare(
                    left=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id="sys", ctx=ast.Load()),
                            attr="gettrace",
                            ctx=ast.Load(),
                        ),
                        args=[],
                        keywords=[],
                    ),
                    ops=[ast.IsNot()],
                    comparators=[ast.Constant(value=None)],
                ),
                # sys.exit(1)
                body=[
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id="sys", ctx=ast.Load()),
                                attr="exit",
                                ctx=ast.Load(),
                            ),
                            args=[ast.Constant(value=1)],
                            keywords=[],
                        )
                    )
                ],
                orelse=[],
            ),
        ]

        return ast.FunctionDef(
            name=self.check_function_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=function_body,
            decorator_list=[],
            returns=None,
        )

    def _create_check_call(self) -> ast.Expr:
        """
        Create a call to the check function.

        Returns:
            ast.Expr: Expression statement calling check function
        """
        return ast.Expr(
            value=ast.Call(
                func=ast.Name(id=self.check_function_name, ctx=ast.Load()),
                args=[],
                keywords=[],
            )
        )

    def get_statistics(self) -> dict:
        """
        Get injection statistics.

        Returns:
            dict: Statistics dictionary
        """
        return {
            "injected_functions": self.injected_functions,
        }
