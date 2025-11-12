"""
Tests for Issue #8: Keyword Argument Support

Tests that --preserve-param-names flag preserves parameter names
to allow keyword arguments after obfuscation.
"""

import ast
import pytest

from pyobfus.core.parser import ASTParser
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.config import ObfuscationConfig
from pyobfus.transformers.name_mangler import NameMangler


class TestKeywordArgumentSupport:
    """Test suite for keyword argument support (Issue #8)."""

    def test_preserve_param_names_flag(self):
        """Test that preserve_param_names preserves parameter names."""
        code = """
def calculate_total(price, quantity):
    return price * quantity
"""
        # Parse and obfuscate with flag
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)

        # Check that parameter names are preserved
        func_def = obfuscated_tree.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        assert func_def.args.args[0].arg == "price"
        assert func_def.args.args[1].arg == "quantity"

    def test_keyword_args_work_after_obfuscation(self):
        """Test that keyword arguments work in obfuscated code."""
        code = """
def calculate_total(price, quantity):
    result = price * quantity
    return result

final = calculate_total(price=100, quantity=2)
"""
        # Obfuscate with flag
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Execute obfuscated code - it should work without errors
        # The variable names are obfuscated, but parameter names are preserved
        namespace = {}
        try:
            exec(obfuscated_code, namespace)
            # If we get here, keyword arguments worked correctly
            assert True
        except TypeError as e:
            # If we get "unexpected keyword argument", the feature doesn't work
            if "unexpected keyword argument" in str(e):
                pytest.fail(f"Keyword arguments failed: {e}")
            else:
                raise

    def test_without_flag_parameters_are_renamed(self):
        """Test that without flag, parameters are still renamed."""
        code = """
def calculate_total(price, quantity):
    return price * quantity
"""
        config = ObfuscationConfig()
        config.preserve_param_names = False

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)

        func_def = obfuscated_tree.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        # Parameters should be renamed to I-prefixed names
        assert func_def.args.args[0].arg != "price"
        assert func_def.args.args[1].arg != "quantity"
        assert func_def.args.args[0].arg.startswith("I")
        assert func_def.args.args[1].arg.startswith("I")

    def test_kwonly_args_preserved(self):
        """Test that keyword-only arguments are preserved."""
        code = """
def func(a, b, *, kwonly1, kwonly2):
    return a + b + kwonly1 + kwonly2
"""
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)

        func_def = obfuscated_tree.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        assert func_def.args.args[0].arg == "a"
        assert func_def.args.args[1].arg == "b"
        assert func_def.args.kwonlyargs[0].arg == "kwonly1"
        assert func_def.args.kwonlyargs[1].arg == "kwonly2"

    def test_vararg_and_kwarg_preserved(self):
        """Test that *args and **kwargs are preserved."""
        code = """
def func(a, *args, **kwargs):
    pass
"""
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)

        func_def = obfuscated_tree.body[0]
        assert isinstance(func_def, ast.FunctionDef)
        assert func_def.args.args[0].arg == "a"
        assert func_def.args.vararg is not None
        assert func_def.args.vararg.arg == "args"
        assert func_def.args.kwarg is not None
        assert func_def.args.kwarg.arg == "kwargs"

    def test_local_variables_still_obfuscated(self):
        """Test that local variables are still obfuscated."""
        code = """
def calculate(price, quantity):
    tax_rate = 0.1
    subtotal = price * quantity
    return subtotal * (1 + tax_rate)
"""
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Parameters should be preserved
        assert "price" in obfuscated_code
        assert "quantity" in obfuscated_code

        # Local variables should be obfuscated
        assert "tax_rate" not in obfuscated_code
        assert "subtotal" not in obfuscated_code

    def test_async_function_params_preserved(self):
        """Test that async function parameters are preserved."""
        code = """
async def fetch_data(url, timeout):
    return url, timeout
"""
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)

        func_def = obfuscated_tree.body[0]
        assert isinstance(func_def, ast.AsyncFunctionDef)
        assert func_def.args.args[0].arg == "url"
        assert func_def.args.args[1].arg == "timeout"

    def test_preserve_patterns_combined_with_param_names(self):
        """Test that exclude_names still works with preserve_param_names."""
        code = """
def __init__(self, data_path):
    pass
"""
        config = ObfuscationConfig()
        config.preserve_param_names = True
        config.add_exclude_name("__init__")

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        assert "__init__" in obfuscated_code
        assert "data_path" in obfuscated_code

    def test_multiple_functions_with_same_param_names(self):
        """Test that multiple functions with same parameter names work correctly."""
        code = """
def add(x, y):
    return x + y

def multiply(x, y):
    return x * y

result1 = add(x=5, y=3)
result2 = multiply(x=5, y=3)
"""
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Execute obfuscated code - should work without keyword argument errors
        namespace = {}
        try:
            exec(obfuscated_code, namespace)
            assert True  # If we got here, keyword arguments worked
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                pytest.fail(f"Keyword arguments failed: {e}")
            else:
                raise

        # Both functions should preserve x, y parameters
        assert obfuscated_code.count("def ") == 2
        assert "x" in obfuscated_code
        assert "y" in obfuscated_code

    def test_default_argument_values_preserved(self):
        """Test that default argument values work with preserved parameter names."""
        code = """
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

result1 = greet(name="Alice")
result2 = greet(name="Bob", greeting="Hi")
"""
        config = ObfuscationConfig()
        config.preserve_param_names = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        obfuscated_tree = mangler.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Execute obfuscated code - should work without keyword argument errors
        namespace = {}
        try:
            exec(obfuscated_code, namespace)
            assert True  # If we got here, keyword arguments worked
        except TypeError as e:
            if "unexpected keyword argument" in str(e):
                pytest.fail(f"Keyword arguments failed: {e}")
            else:
                raise
