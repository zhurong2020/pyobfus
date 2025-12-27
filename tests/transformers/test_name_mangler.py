"""
Unit tests for name mangling transformer.
"""

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.parser import ASTParser
from pyobfus.transformers.name_mangler import NameMangler


def test_mangle_simple_names():
    """Test basic name mangling."""
    code = """
x = 1
y = 2
z = x + y
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    mangler = NameMangler(config, analyzer)
    transformed = mangler.transform(tree)
    result = CodeGenerator.generate(transformed)

    # Original names should be replaced
    assert "x" not in result or result.count("x") == 0
    assert "y" not in result or result.count("y") == 0
    assert "z" not in result or result.count("z") == 0

    # Mangled names should be present
    assert "I0" in result or "I1" in result or "I2" in result


def test_mangle_function_names():
    """Test function name mangling."""
    code = """
def calculate(value):
    return value * 2

result = calculate(21)
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    mangler = NameMangler(config, analyzer)
    transformed = mangler.transform(tree)
    result = CodeGenerator.generate(transformed)

    # Function name should be mangled
    assert "calculate" not in result
    assert "I0" in result


def test_preserve_name_prefix():
    """Test custom name prefix."""
    code = """
x = 1
y = 2
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    config.name_prefix = "VAR"
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    mangler = NameMangler(config, analyzer)
    transformed = mangler.transform(tree)
    result = CodeGenerator.generate(transformed)

    # Should use custom prefix
    assert "VAR0" in result or "VAR1" in result


def test_remove_docstrings():
    """Test docstring removal."""
    code = '''
def func(x):
    """This is a docstring."""
    return x * 2
'''
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    config.remove_docstrings = True
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    mangler = NameMangler(config, analyzer)
    transformed = mangler.transform(tree)
    result = CodeGenerator.generate(transformed)

    # Docstring should be removed
    assert "This is a docstring" not in result


def test_name_mapping():
    """Test that name mapping is consistent."""
    code = """
def func(x):
    return x + x

a = func(1)
b = func(2)
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    mangler = NameMangler(config, analyzer)
    mangler.transform(tree)

    # Get name mapping
    name_map = mangler.get_name_mapping()

    # Check that mapping is consistent
    assert len(name_map) > 0
    for original, mangled in name_map.items():
        assert mangled.startswith(config.name_prefix)


def test_transformation_count():
    """Test transformation counter."""
    code = """
x = 1
y = 2
z = x + y
"""
    tree = ASTParser.parse_string(code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    mangler = NameMangler(config, analyzer)
    mangler.transform(tree)

    # Should have transformed some names
    assert mangler.get_transformation_count() > 0
