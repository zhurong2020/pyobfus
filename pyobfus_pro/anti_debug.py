"""
Anti-Debugging Injector (Pro Feature)

Injects anti-debugging checks into obfuscated code to detect and prevent
debugging attempts. Makes reverse engineering significantly harder.

Techniques (P2-15, 2026-08-04 extended the original sys.gettrace()-only
check with three more, closing the roadmap's originally-scoped gap):
1. sys.gettrace() detection - Python-level debuggers/tracers (original)
2. TracerPid (Linux) - reads /proc/self/status; a nonzero TracerPid means
   a native debugger (gdb, strace, a debugger extension) is attached, which
   sys.gettrace() alone cannot see since it only observes the CPython trace
   hook, not OS-level ptrace attachment.
3. IsDebuggerPresent (Windows) - the standard WinAPI check via ctypes,
   detects a native Windows debugger attached to the process.
4. Timing-skew - times a trivial tight loop; a debugger single-stepping or
   evaluating breakpoints per line adds overhead orders of magnitude above
   normal execution. Threshold is deliberately generous (see
   _create_check_function's docstring) to avoid false positives under CPU
   throttling / heavy load, which would kill a legitimate customer process.
5. Immediate exit on detection - Prevents analysis

Known limitation, documented rather than hidden: all four checks are
best-effort heuristics, not a security boundary -- a sufficiently determined
attacker can patch them out of the obfuscated source before running it, the
same limitation this project's trial/license mechanisms already document.
"""

import ast
import textwrap
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
        insert_at = _module_header_end(tree)
        tree.body.insert(insert_at, check_function)
        return tree

    # Timing-skew threshold, in seconds, for a 10,000-iteration trivial
    # Python loop. Deliberately generous: normal execution (even on a
    # throttled CI runner or a loaded shared host) completes in low
    # milliseconds at worst; only line-by-line single-stepping or
    # per-line breakpoint evaluation by a debugger pushes it into the
    # hundreds-of-milliseconds-to-seconds range. A tight threshold here
    # would risk false-positive-killing a legitimate customer process
    # under heavy load, which is worse than missing a real debugger.
    _TIMING_THRESHOLD_SECONDS = 1.0
    _TIMING_LOOP_ITERATIONS = 10_000

    def _create_check_function(self) -> ast.FunctionDef:
        """
        Create the anti-debugging check function.

        Built by parsing a source template (`ast.parse`) rather than
        hand-constructing every node -- the four checks below (gettrace +
        P2-15's TracerPid/IsDebuggerPresent/timing-skew) are enough
        platform-conditional logic that hand-built nodes would be far more
        error-prone to write and review than a readable template.

        Returns:
            ast.FunctionDef: Check function AST node
        """
        template = textwrap.dedent(f"""
            def {self.check_function_name}():
                import sys
                if sys.gettrace() is not None:
                    sys.exit(1)
                import platform
                if platform.system() == 'Linux':
                    try:
                        with open('/proc/self/status', 'r') as _pyobfus_ad_f:
                            for _pyobfus_ad_line in _pyobfus_ad_f:
                                if _pyobfus_ad_line.startswith('TracerPid:'):
                                    if int(_pyobfus_ad_line.split(':')[1].strip()) != 0:
                                        sys.exit(1)
                                    break
                    except OSError:
                        pass
                if platform.system() == 'Windows':
                    try:
                        import ctypes
                        if ctypes.windll.kernel32.IsDebuggerPresent():
                            sys.exit(1)
                    except (AttributeError, OSError):
                        pass
                import time
                _pyobfus_ad_t0 = time.perf_counter()
                _pyobfus_ad_x = 0
                for _pyobfus_ad_i in range({self._TIMING_LOOP_ITERATIONS}):
                    _pyobfus_ad_x += _pyobfus_ad_i
                if time.perf_counter() - _pyobfus_ad_t0 > {self._TIMING_THRESHOLD_SECONDS}:
                    sys.exit(1)
            """).strip()

        parsed = ast.parse(template)
        func_def = parsed.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        return func_def

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
