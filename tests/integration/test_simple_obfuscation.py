"""
Integration test for basic obfuscation workflow.

Tests the complete pipeline: parse -> analyze -> transform -> generate
"""

import ast
import subprocess
import sys


from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.parser import ASTParser
from pyobfus.transformers.name_mangler import NameMangler


def test_simple_obfuscation():
    """Test obfuscating a simple Python script."""
    # Sample code
    source_code = """
def calculate_risk(age, calcium_score):
    risk_factor = 0.1
    if calcium_score > 100:
        risk_factor = 0.5
    return age * risk_factor

patient_age = 55
patient_calcium = 150
risk = calculate_risk(patient_age, patient_calcium)
print(f"Risk: {risk}")
"""

    # Parse
    tree = ASTParser.parse_string(source_code)
    assert isinstance(tree, ast.Module)

    # Analyze
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    # Should find obfuscatable names
    obfuscatable = analyzer.get_obfuscatable_names()
    assert len(obfuscatable) > 0
    assert "calculate_risk" in obfuscatable
    assert "age" in obfuscatable
    assert "calcium_score" in obfuscatable

    # Transform
    mangler = NameMangler(config, analyzer)
    transformed_tree = mangler.transform(tree)

    # Generate
    obfuscated_code = CodeGenerator.generate(transformed_tree)

    # Verify obfuscation
    assert "calculate_risk" not in obfuscated_code
    assert "patient_age" not in obfuscated_code
    assert "I0" in obfuscated_code or "I1" in obfuscated_code

    # Verify code still executes
    exec_globals = {}
    exec(obfuscated_code, exec_globals)


def test_obfuscated_code_executes(tmp_path):
    """Test that obfuscated code produces same output as original."""
    # Original code
    original_code = """
def add(x, y):
    return x + y

result = add(2, 3)
print(result)
"""

    # Parse and obfuscate
    tree = ASTParser.parse_string(original_code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)
    mangler = NameMangler(config, analyzer)
    transformed_tree = mangler.transform(tree)
    obfuscated_code = CodeGenerator.generate(transformed_tree)

    # Write original and obfuscated to temp files
    original_file = tmp_path / "original.py"
    obfuscated_file = tmp_path / "obfuscated.py"

    original_file.write_text(original_code)
    obfuscated_file.write_text(obfuscated_code)

    # Execute both and compare output
    original_output = subprocess.run(
        [sys.executable, str(original_file)], capture_output=True, text=True
    )
    obfuscated_output = subprocess.run(
        [sys.executable, str(obfuscated_file)], capture_output=True, text=True
    )

    assert original_output.stdout == obfuscated_output.stdout
    assert original_output.returncode == obfuscated_output.returncode == 0


def test_preserve_builtins():
    """Test that builtin names are not obfuscated."""
    source_code = """
result = len([1, 2, 3])
text = str(result)
print(text)
"""

    tree = ASTParser.parse_string(source_code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)
    mangler = NameMangler(config, analyzer)
    transformed_tree = mangler.transform(tree)
    obfuscated_code = CodeGenerator.generate(transformed_tree)

    # Builtins should be preserved
    assert "len" in obfuscated_code
    assert "str" in obfuscated_code
    assert "print" in obfuscated_code

    # User variables should be obfuscated
    assert "result" not in obfuscated_code or obfuscated_code.count("result") == 0
    assert "text" not in obfuscated_code or obfuscated_code.count("text") == 0


def test_preserve_magic_methods():
    """Test that magic methods are not obfuscated."""
    source_code = """
class MyClass:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

obj = MyClass(42)
print(obj)
"""

    tree = ASTParser.parse_string(source_code)
    config = ObfuscationConfig.community_edition()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)
    mangler = NameMangler(config, analyzer)
    transformed_tree = mangler.transform(tree)
    obfuscated_code = CodeGenerator.generate(transformed_tree)

    # Magic methods should be preserved
    assert "__init__" in obfuscated_code
    assert "__str__" in obfuscated_code
