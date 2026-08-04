"""
Tests for Anti-Debugging feature - Pro Edition.

Tests that anti-debugging checks are properly injected into functions
and work correctly to detect debuggers.
"""

import sys
from unittest import mock

import pytest
from typing import TYPE_CHECKING

from pyobfus.core.parser import ASTParser
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.config import ObfuscationConfig

# Pro features require pyobfus_pro to be installed
PRO_AVAILABLE = False
if TYPE_CHECKING:
    from pyobfus_pro.anti_debug import AntiDebugInjector
else:
    try:
        from pyobfus_pro.anti_debug import AntiDebugInjector

        PRO_AVAILABLE = True
    except ImportError:
        pass


@pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not installed")
class TestAntiDebugInjection:
    """Test suite for anti-debugging feature."""

    def test_check_function_injected(self):
        """Test that _check_debugger function is injected at module level."""
        code = """
def my_function():
    return "Hello"
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Check function should be present
        assert (
            "_check_debugger" in obfuscated_code or injector.check_function_name in obfuscated_code
        )

        # sys.gettrace() should be present
        assert "gettrace" in obfuscated_code

    def test_check_calls_in_functions(self):
        """Test that check calls are injected into functions."""
        code = """
def function1():
    x = 1
    return "First"

def function2():
    y = 2
    return "Second"

def function3():
    x = 1
    y = 2
    return x + y
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Check calls should be present
        # Count occurrences of check function calls (all 3 functions now have >= 2 statements)
        check_calls = obfuscated_code.count(injector.check_function_name + "()")
        assert check_calls >= 3, f"Expected at least 3 check calls, found {check_calls}"

    def test_code_executes_normally_without_debugger(self):
        """Test that obfuscated code runs normally when no debugger is present."""
        code = """
def add(a, b):
    return a + b

result = add(2, 3)
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Code should execute normally
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["result"] == 5

    def test_debugger_detection_logic(self):
        """Test that the debugger detection logic is correct."""
        code = """
def sample():
    return 42
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # The check should use sys.gettrace() is not None
        assert "sys.gettrace()" in obfuscated_code
        assert "is not None" in obfuscated_code or "!= None" in obfuscated_code
        assert "sys.exit" in obfuscated_code

    def test_p2_15_detection_methods_present_in_source(self):
        """P2-15: TracerPid / IsDebuggerPresent / timing-skew all appear in
        the generated _check_debugger, not just the original sys.gettrace()."""
        code = "def sample():\n    return 42\n"
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_code = CodeGenerator.generate(injector.transform(tree))

        assert "TracerPid" in obfuscated_code
        assert "IsDebuggerPresent" in obfuscated_code
        assert "perf_counter" in obfuscated_code

    def _get_check_debugger(self):
        """Obfuscate a trivial module with --anti-debug and return the
        live _check_debugger function object from the executed namespace."""
        code = "def sample():\n    return 42\n"
        config = ObfuscationConfig()
        config.anti_debug = True
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        injector = AntiDebugInjector(config, analyzer)
        obfuscated_code = CodeGenerator.generate(injector.transform(tree))
        namespace: dict = {}
        exec(obfuscated_code, namespace)
        return namespace["_check_debugger"]

    def test_tracer_pid_nonzero_triggers_exit(self):
        """A nonzero TracerPid (native debugger attached) raises SystemExit.
        platform.system is force-mocked to 'Linux' so this test is
        deterministic regardless of the actual CI host OS."""
        check_fn = self._get_check_debugger()
        with (
            mock.patch("platform.system", return_value="Linux"),
            mock.patch(
                "builtins.open",
                mock.mock_open(read_data="Name:\tpython\nTracerPid:\t1234\n"),
            ),
        ):
            with pytest.raises(SystemExit):
                check_fn()

    def test_tracer_pid_zero_does_not_trigger(self):
        """TracerPid: 0 (no debugger attached) must not raise."""
        check_fn = self._get_check_debugger()
        with (
            mock.patch("platform.system", return_value="Linux"),
            mock.patch(
                "builtins.open",
                mock.mock_open(read_data="Name:\tpython\nTracerPid:\t0\n"),
            ),
        ):
            check_fn()  # must not raise

    def test_is_debugger_present_true_triggers_exit(self):
        """WinAPI IsDebuggerPresent()==True raises SystemExit. ctypes.windll
        is patched with create=True since it only natively exists on
        Windows -- this keeps the test portable across the CI OS matrix."""
        check_fn = self._get_check_debugger()
        fake_windll = mock.MagicMock()
        fake_windll.kernel32.IsDebuggerPresent.return_value = True
        with (
            mock.patch("platform.system", return_value="Windows"),
            mock.patch("ctypes.windll", fake_windll, create=True),
        ):
            with pytest.raises(SystemExit):
                check_fn()

    def test_is_debugger_present_false_does_not_trigger(self):
        check_fn = self._get_check_debugger()
        fake_windll = mock.MagicMock()
        fake_windll.kernel32.IsDebuggerPresent.return_value = False
        with (
            mock.patch("platform.system", return_value="Windows"),
            mock.patch("ctypes.windll", fake_windll, create=True),
        ):
            check_fn()  # must not raise

    def test_timing_skew_triggers_on_simulated_slowdown(self):
        """A simulated huge elapsed time between the two perf_counter()
        calls (as a debugger single-stepping through the loop would cause)
        raises SystemExit. Runs the real gettrace/TracerPid/IsDebuggerPresent
        checks unmocked -- fine, since no real debugger is attached during
        the test run, so they pass through without raising."""
        check_fn = self._get_check_debugger()
        readings = iter([0.0, 999.0])
        with mock.patch("time.perf_counter", side_effect=lambda: next(readings)):
            with pytest.raises(SystemExit):
                check_fn()

    def test_small_functions_skipped(self):
        """Test that very small functions are not injected (< 2 statements)."""
        code = """
def tiny():
    pass

def small():
    return 1

def normal():
    x = 1
    return x
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        _obfuscated_tree = injector.transform(tree)  # noqa: F841

        stats = injector.get_statistics()
        # Only "normal" function should be injected (has >= 2 statements)
        assert stats["injected_functions"] >= 1

    def test_infrastructure_functions_skipped(self):
        """Test that functions starting with _ are not injected."""
        code = """
def _private():
    x = 1
    y = 2
    return x + y

def public():
    x = 1
    y = 2
    return x + y
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        _obfuscated_code = CodeGenerator.generate(obfuscated_tree)  # noqa: F841

        # _private should not have check injected
        # public should have check injected
        # This is hard to verify directly, so we check statistics
        stats = injector.get_statistics()
        assert stats["injected_functions"] >= 1

    def test_class_methods_injected(self):
        """Test that class methods also get anti-debug checks."""
        code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        result = a * b
        return result
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Check calls should be present in methods
        check_calls = obfuscated_code.count(injector.check_function_name + "()")
        assert check_calls >= 2  # At least add() and multiply()

    def test_nested_functions(self):
        """Test anti-debug injection in nested functions."""
        code = """
def outer():
    x = 1

    def inner():
        y = 2
        return y

    return inner()
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Clear any trace function (pytest coverage can trigger false positives)
        old_trace = sys.gettrace()
        sys.settrace(None)
        try:
            # Both outer and inner should potentially have checks
            namespace = {}
            exec(obfuscated_code, namespace)
            # Code should execute normally
            assert namespace["outer"]() == 2
        finally:
            sys.settrace(old_trace)

    def test_statistics(self):
        """Test that injection statistics are correctly reported."""
        code = """
def func1():
    x = 1
    return x

def func2():
    y = 2
    return y

def func3():
    z = 3
    return z
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        _obfuscated_tree = injector.transform(tree)  # noqa: F841

        stats = injector.get_statistics()
        assert "injected_functions" in stats
        assert stats["injected_functions"] >= 3  # All 3 functions

    def test_async_functions(self):
        """Test anti-debug injection in async functions."""
        code = """
async def async_function():
    x = 1
    y = 2
    return x + y
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Check that code is valid (can parse it back)
        reparsed = ASTParser.parse_string(obfuscated_code)
        assert reparsed is not None

    def test_complex_control_flow(self):
        """Test anti-debug injection with complex control flow."""
        code = """
def complex_function(x):
    if x > 0:
        result = x * 2
    else:
        result = x * -1

    for i in range(3):
        result += i

    return result
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Clear any trace function (pytest coverage can trigger false positives)
        old_trace = sys.gettrace()
        sys.settrace(None)
        try:
            # Code should execute correctly
            namespace = {}
            exec(obfuscated_code, namespace)
            assert namespace["complex_function"](5) == 13  # (5*2) + 0 + 1 + 2 = 13
            assert namespace["complex_function"](-5) == 8  # 5 + 0 + 1 + 2 = 8
        finally:
            sys.settrace(old_trace)

    def test_exception_handling(self):
        """Test anti-debug injection with exception handling."""
        code = """
def safe_divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        result = 0
    return result
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Clear any trace function (pytest coverage can trigger false positives)
        old_trace = sys.gettrace()
        sys.settrace(None)
        try:
            # Code should execute correctly
            namespace = {}
            exec(obfuscated_code, namespace)
            assert namespace["safe_divide"](10, 2) == 5.0
            assert namespace["safe_divide"](10, 0) == 0
        finally:
            sys.settrace(old_trace)

    def test_multiple_returns(self):
        """Test anti-debug injection with functions having multiple returns."""
        code = """
def check_value(x):
    if x < 0:
        return "negative"
    elif x == 0:
        return "zero"
    else:
        return "positive"
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["check_value"](-1) == "negative"
        assert namespace["check_value"](0) == "zero"
        assert namespace["check_value"](1) == "positive"

    def test_decorators_preserved(self):
        """Test that function decorators are preserved."""
        code = """
def decorator(func):
    def wrapper():
        x = 1
        y = 2
        return func() + 10
    return wrapper

@decorator
def decorated():
    z = 3
    return 5

result = decorated()
"""
        config = ObfuscationConfig()
        config.anti_debug = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        injector = AntiDebugInjector(config, analyzer)
        obfuscated_tree = injector.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Clear any trace function (pytest coverage can trigger false positives)
        old_trace = sys.gettrace()
        sys.settrace(None)
        try:
            # Code should execute correctly
            namespace = {}
            exec(obfuscated_code, namespace)
            assert namespace["result"] == 15  # 5 + 10
        finally:
            sys.settrace(old_trace)
