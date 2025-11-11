"""
Unit tests for symbol analyzer.
"""

import ast

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.parser import ASTParser


def test_analyze_simple_function():
    """Test analyzing a simple function."""
    code = """
def calculate(x, y):
    result = x + y
    return result
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    obfuscatable = analyzer.get_obfuscatable_names()

    assert "calculate" in obfuscatable
    assert "x" in obfuscatable
    assert "y" in obfuscatable
    assert "result" in obfuscatable


def test_exclude_builtins():
    """Test that builtins are excluded."""
    code = """
x = len([1, 2, 3])
y = print(x)
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    obfuscatable = analyzer.get_obfuscatable_names()

    # User variables should be obfuscatable
    assert "x" in obfuscatable
    assert "y" in obfuscatable

    # Builtins should not be
    assert "len" not in obfuscatable
    assert "print" not in obfuscatable


def test_exclude_imports():
    """Test that imported names are excluded."""
    code = """
import os
from pathlib import Path

x = os.path.join("a", "b")
y = Path("/tmp")
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    obfuscatable = analyzer.get_obfuscatable_names()

    # User variables should be obfuscatable
    assert "x" in obfuscatable
    assert "y" in obfuscatable

    # Imported names should not be
    assert "os" not in obfuscatable
    assert "Path" not in obfuscatable


def test_exclude_magic_methods():
    """Test that magic methods are excluded."""
    code = """
class MyClass:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

    def custom_method(self):
        return self.value * 2
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    obfuscatable = analyzer.get_obfuscatable_names()

    # Regular methods should be obfuscatable
    assert "MyClass" in obfuscatable
    assert "custom_method" in obfuscatable

    # Magic methods should not be
    assert "__init__" not in obfuscatable
    assert "__str__" not in obfuscatable


def test_statistics():
    """Test statistics generation."""
    code = """
def func(x, y):
    result = x + y
    return result

a = 1
b = 2
c = func(a, b)
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    stats = analyzer.get_statistics()

    assert stats["total_names"] > 0
    assert stats["obfuscatable_names"] > 0
    assert stats["obfuscatable_names"] <= stats["total_names"]
