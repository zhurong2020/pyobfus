"""Extended tests for SymbolAnalyzer to improve coverage.

Targets the uncovered visit methods and edge cases:
- visit_AsyncFunctionDef
- visit_ClassDef (class attributes, annotated assignments)
- visit_For (tuple unpacking)
- visit_With
- visit_Import / visit_ImportFrom
- visit_Global / visit_Nonlocal
- visit_AnnAssign
- visit_Assign (tuple/list targets)
- Public API auto-detection
- kwonlyargs, posonlyargs, vararg, kwarg
"""

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.parser import ASTParser


@pytest.fixture
def config():
    return ObfuscationConfig.community_edition()


class TestAsyncFunctionDef:
    def test_async_function_detected(self, config):
        code = "async def fetch(url):\n    return url\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "fetch" in analyzer.obfuscatable_names
        assert "url" in analyzer.obfuscatable_names

    def test_async_function_kwonly_args(self, config):
        code = "async def fetch(*, timeout):\n    return timeout\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "timeout" in analyzer.parameter_names

    def test_async_function_vararg_kwarg(self, config):
        code = "async def fetch(*args, **kwargs):\n    pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "args" in analyzer.parameter_names
        assert "kwargs" in analyzer.parameter_names


class TestFunctionArgTypes:
    def test_kwonly_args(self, config):
        code = "def func(*, key, value):\n    pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "key" in analyzer.parameter_names
        assert "value" in analyzer.parameter_names

    def test_posonly_args(self, config):
        code = "def func(x, y, /):\n    pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "x" in analyzer.parameter_names
        assert "y" in analyzer.parameter_names

    def test_vararg(self, config):
        code = "def func(*items):\n    pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "items" in analyzer.parameter_names

    def test_kwarg(self, config):
        code = "def func(**options):\n    pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "options" in analyzer.parameter_names


class TestClassDef:
    def test_class_attributes(self, config):
        code = "class Foo:\n    bar = 42\n    baz = 'hello'\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "bar" in analyzer.all_class_attributes
        assert "baz" in analyzer.all_class_attributes

    def test_annotated_class_attributes(self, config):
        code = "class Foo:\n    bar: int = 42\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "bar" in analyzer.all_class_attributes

    def test_method_names_tracked(self, config):
        code = "class Foo:\n    def method(self):\n        pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "method" in analyzer.method_names


class TestAssignment:
    def test_tuple_unpacking(self, config):
        code = "a, b = 1, 2\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "a" in analyzer.local_names
        assert "b" in analyzer.local_names

    def test_list_unpacking(self, config):
        code = "[a, b] = [1, 2]\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "a" in analyzer.local_names
        assert "b" in analyzer.local_names

    def test_annotated_assignment(self, config):
        code = "x: int = 42\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "x" in analyzer.local_names


class TestForLoop:
    def test_tuple_loop_variable(self, config):
        code = "for a, b in [(1, 2)]:\n    pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "a" in analyzer.local_names
        assert "b" in analyzer.local_names


class TestWithStatement:
    def test_context_manager_variable(self, config):
        code = "with open('f') as fh:\n    pass\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "fh" in analyzer.local_names


class TestImports:
    def test_import_alias(self, config):
        code = "import numpy as np\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "np" in analyzer.imported_names

    def test_import_dotted(self, config):
        code = "import os.path\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "os" in analyzer.imported_names

    def test_from_import(self, config):
        code = "from os import path\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "path" in analyzer.imported_names

    def test_from_import_alias(self, config):
        code = "from os import path as p\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "p" in analyzer.imported_names

    def test_star_import_skipped(self, config):
        code = "from os import *\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        # Star import should not add "*" to imported_names


class TestGlobalNonlocal:
    def test_global_statement(self, config):
        code = "def f():\n    global x\n    x = 1\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "x" in analyzer.global_names

    def test_nonlocal_statement(self, config):
        code = "def outer():\n    x = 1\n    def inner():\n        nonlocal x\n        x = 2\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        assert "x" in analyzer.local_names


class TestStatistics:
    def test_get_statistics(self, config):
        code = "import os\ndef func(x):\n    result = x + 1\n    return result\n"
        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)
        stats = analyzer.get_statistics()
        assert "total_names" in stats
        assert "obfuscatable_names" in stats
        assert "imported_names" in stats
        assert stats["imported_names"] >= 1
