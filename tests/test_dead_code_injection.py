"""
Unit tests for Dead Code Injection.

Tests the injection of unreachable code blocks to increase complexity.
"""

import ast
import sys
import pytest

# Add pyobfus_pro to path for testing
sys.path.insert(0, str(__file__).replace("tests/test_dead_code_injection.py", ""))

from pyobfus_pro.dead_code import DeadCodeInjector, DCIConfig


class TestDCIConfig:
    """Tests for DCIConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DCIConfig()
        assert config.enabled is True
        assert config.inject_after_return is True
        assert config.inject_false_branches is True
        assert config.inject_opaque_predicates is True
        assert config.inject_decoy_functions is True
        assert config.injection_ratio == 0.3
        assert config.min_statements == 3

    def test_disabled_config(self):
        """Test disabled configuration."""
        config = DCIConfig(enabled=False)
        assert config.enabled is False


class TestDeadCodeInjector:
    """Tests for DeadCodeInjector class."""

    def test_simple_function_unchanged_when_disabled(self):
        """Test that disabled injector doesn't modify code."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    return z
"""
        tree = ast.parse(code)
        config = DCIConfig(enabled=False)
        injector = DeadCodeInjector(config)
        result = injector.visit(tree)

        # Should be unchanged
        func = result.body[0]
        assert len(func.body) == 3

    def test_small_function_skipped(self):
        """Test that small functions are not modified internally."""
        code = """
def tiny(x):
    return x
"""
        tree = ast.parse(code)
        config = DCIConfig(min_statements=3, injection_ratio=1.0, inject_decoy_functions=False)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Find the tiny function (might have decoy functions added)
        tiny_func = None
        for node in result.body:
            if isinstance(node, ast.FunctionDef) and node.name == "tiny":
                tiny_func = node
                break

        assert tiny_func is not None
        # Small function body should be unchanged
        assert len(tiny_func.body) == 1

    def test_injection_after_return(self):
        """Test dead code injection after return statements."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    return z
"""
        tree = ast.parse(code)
        config = DCIConfig(
            inject_after_return=True,
            inject_false_branches=False,
            inject_opaque_predicates=False,
            inject_decoy_functions=False,
            injection_ratio=1.0,  # Always inject
        )
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Should have more statements after return
        func = result.body[0]
        assert len(func.body) > 3

        # Find return and check there's code after it
        for i, stmt in enumerate(func.body):
            if isinstance(stmt, ast.Return):
                assert i < len(func.body) - 1, "Code should be after return"
                break

    def test_false_branch_injection(self):
        """Test if False: block injection."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    w = z - 1
    return w
"""
        tree = ast.parse(code)
        config = DCIConfig(
            inject_after_return=False,
            inject_false_branches=True,
            inject_opaque_predicates=False,
            inject_decoy_functions=False,
            injection_ratio=1.0,
        )
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Should have if False: blocks
        func = result.body[0]
        has_false_branch = any(
            isinstance(stmt, ast.If)
            and isinstance(stmt.test, ast.Constant)
            and stmt.test.value is False
            for stmt in func.body
        )
        assert has_false_branch, "Should have if False: blocks"

    def test_opaque_predicate_injection(self):
        """Test opaque predicate injection."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    w = z - 1
    return w
"""
        tree = ast.parse(code)
        config = DCIConfig(
            inject_after_return=False,
            inject_false_branches=False,
            inject_opaque_predicates=True,
            inject_decoy_functions=False,
            injection_ratio=1.0,
        )
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Should have opaque predicates (if statements with comparisons)
        func = result.body[0]
        has_opaque = any(
            isinstance(stmt, ast.If) and isinstance(stmt.test, ast.Compare) for stmt in func.body
        )
        assert has_opaque, "Should have opaque predicates"

    def test_decoy_function_injection(self):
        """Test decoy function injection at module level."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    w = z - 1
    return w
"""
        tree = ast.parse(code)
        config = DCIConfig(
            inject_after_return=False,
            inject_false_branches=False,
            inject_opaque_predicates=False,
            inject_decoy_functions=True,
            injection_ratio=1.0,
        )
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Should have more functions than original
        func_count = sum(1 for node in result.body if isinstance(node, ast.FunctionDef))
        assert func_count > 1, "Should have decoy functions"

    def test_injected_code_is_syntactically_valid(self):
        """Test that injected code is valid Python."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    w = z - 1
    return w
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Should compile without errors
        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_original_functionality_preserved(self):
        """Test that original code still works correctly."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    return z
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        example = namespace["example"]

        # Original functionality should work
        assert example(5) == 12  # (5 + 1) * 2 = 12
        assert example(0) == 2  # (0 + 1) * 2 = 2
        assert example(-1) == 0  # (-1 + 1) * 2 = 0

    def test_generator_function_skipped(self):
        """Test that generator functions are not modified."""
        code = """
def gen():
    for i in range(10):
        yield i
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Generator should be unchanged (except possible decoy functions)
        func = None
        for node in result.body:
            if isinstance(node, ast.FunctionDef) and node.name == "gen":
                func = node
                break

        assert func is not None
        # Should still have for loop with yield
        assert any(isinstance(stmt, ast.For) for stmt in func.body)

    def test_async_function_injection(self):
        """Test injection in async functions."""
        code = """
async def example(x):
    y = x + 1
    z = y * 2
    w = z - 1
    return w
"""
        tree = ast.parse(code)
        config = DCIConfig(
            inject_false_branches=True,
            inject_decoy_functions=False,
            injection_ratio=1.0,
        )
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        # Should compile
        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_reproducible_with_seed(self):
        """Test that same seed produces same results."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    w = z - 1
    return w
"""
        config = DCIConfig(injection_ratio=0.5)

        tree1 = ast.parse(code)
        injector1 = DeadCodeInjector(config, seed=12345)
        result1 = injector1.visit(tree1)
        # Use ast.dump for comparison (works on Python 3.8+)
        dump1 = ast.dump(result1)

        tree2 = ast.parse(code)
        injector2 = DeadCodeInjector(config, seed=12345)
        result2 = injector2.visit(tree2)
        dump2 = ast.dump(result2)

        assert dump1 == dump2, "Same seed should produce same results"

    def test_statistics(self):
        """Test that statistics are tracked correctly."""
        code = """
def example(x):
    y = x + 1
    z = y * 2
    w = z - 1
    return w
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0)
        injector = DeadCodeInjector(config, seed=42)
        injector.visit(tree)

        stats = injector.get_statistics()
        assert "injected_statements" in stats
        assert "decoy_functions" in stats
        assert "variables_created" in stats
        assert stats["injected_statements"] >= 0
        assert stats["variables_created"] >= 0


class TestComplexScenarios:
    """Tests for complex code scenarios."""

    def test_nested_functions(self):
        """Test injection in nested functions."""
        code = """
def outer(x):
    y = x + 1
    def inner(z):
        a = z * 2
        b = a + 1
        return b
    return inner(y)
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0, inject_decoy_functions=False)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        outer = namespace["outer"]

        # Original functionality preserved
        assert outer(5) == 13  # inner((5+1)) = (6*2)+1 = 13

    def test_class_methods(self):
        """Test injection in class methods."""
        code = """
class Calculator:
    def add(self, a, b):
        x = a + b
        y = x * 2
        z = y - 1
        return x

    def multiply(self, a, b):
        x = a * b
        y = x + 1
        z = y * 2
        return x
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0, inject_decoy_functions=False)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        Calculator = namespace["Calculator"]
        calc = Calculator()

        assert calc.add(2, 3) == 5
        assert calc.multiply(4, 5) == 20

    def test_multiple_returns(self):
        """Test function with multiple return statements."""
        code = """
def classify(x):
    result = 0
    if x > 0:
        category = "positive"
        return category
    elif x < 0:
        category = "negative"
        return category
    else:
        category = "zero"
        return category
"""
        tree = ast.parse(code)
        config = DCIConfig(
            inject_after_return=True,
            injection_ratio=1.0,
            inject_decoy_functions=False,
        )
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        classify = namespace["classify"]

        assert classify(10) == "positive"
        assert classify(-5) == "negative"
        assert classify(0) == "zero"

    def test_with_loops(self):
        """Test injection in code with loops."""
        code = """
def sum_list(items):
    total = 0
    count = 0
    for item in items:
        total += item
        count += 1
    return total
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0, inject_decoy_functions=False)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        sum_list = namespace["sum_list"]

        assert sum_list([1, 2, 3, 4, 5]) == 15
        assert sum_list([]) == 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_function(self):
        """Test function with only pass."""
        code = """
def empty():
    pass
"""
        tree = ast.parse(code)
        config = DCIConfig(min_statements=1, injection_ratio=1.0)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_only_docstring(self):
        """Test function with only docstring."""
        code = '''
def documented():
    """This function does nothing."""
    pass
'''
        tree = ast.parse(code)
        config = DCIConfig(min_statements=1, injection_ratio=1.0)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_lambda_unchanged(self):
        """Test that lambdas are not modified (they're expressions)."""
        code = """
add = lambda x, y: x + y
"""
        tree = ast.parse(code)
        config = DCIConfig(injection_ratio=1.0)
        injector = DeadCodeInjector(config, seed=42)
        result = injector.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        add = namespace["add"]

        assert add(2, 3) == 5


# Run pytest if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
