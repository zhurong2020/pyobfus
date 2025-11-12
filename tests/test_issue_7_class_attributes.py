"""
Test for Issue #7: Class attribute renaming inconsistency.

Tests that class attributes are renamed consistently across:
- Class attribute declarations
- Direct class attribute access (ClassName.attr)
- Class method access (cls.attr)
- Instance access to class attributes (self.__class__.attr)
"""

import ast
import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.transformers.name_mangler import NameMangler


def run_obfuscated_code(code: str) -> dict:
    """Helper to obfuscate and execute code."""
    tree = ast.parse(code)
    config = ObfuscationConfig()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    mangler = NameMangler(config, analyzer)
    transformed = mangler.transform(tree)

    # Get obfuscated code for debugging
    obfuscated_code = ast.unparse(transformed)

    # Compile and execute
    try:
        compiled = compile(transformed, '<test>', 'exec')
        namespace = {}
        exec(compiled, namespace)
        return namespace
    except AttributeError as e:
        pytest.fail(f"AttributeError raised: {e}\nObfuscated code:\n{obfuscated_code}")
    except Exception as e:
        pytest.fail(f"Unexpected error: {type(e).__name__}: {e}\nObfuscated code:\n{obfuscated_code}")


def test_class_attribute_direct_access():
    """Test that ClassName.attribute references are updated."""
    code = """
class Counter:
    _count = 0

    def __init__(self):
        Counter._count += 1

    @classmethod
    def get_count(cls):
        return Counter._count

# Test execution
c1 = Counter()
c2 = Counter()
result = Counter.get_count()
"""
    # Should execute without AttributeError
    run_obfuscated_code(code)


def test_class_attribute_cls_access():
    """Test that cls.attribute references are updated in classmethods."""
    code = """
class MyClass:
    _count = 0

    @classmethod
    def increment(cls):
        cls._count += 1
        return cls._count

    @classmethod
    def get_count(cls):
        return cls._count

result = MyClass.increment()
"""
    # Should execute without AttributeError
    run_obfuscated_code(code)


def test_class_attribute_instance_access():
    """Test that instance access to class attributes works."""
    code = """
class Registry:
    _registry = {}

    def __init__(self, name):
        self.name = name
        Registry._registry[name] = self

    @classmethod
    def get_all(cls):
        return cls._registry

r1 = Registry("first")
r2 = Registry("second")
all_items = Registry.get_all()
"""
    # Should execute without AttributeError
    run_obfuscated_code(code)


def test_multiple_class_attributes():
    """Test multiple class attributes in the same class."""
    code = """
class DataProcessor:
    _instance_count = 0
    _registry = {}
    _config = {"debug": False}

    def __init__(self, name: str):
        DataProcessor._instance_count += 1
        DataProcessor._registry[name] = self

    @classmethod
    def get_count(cls):
        return cls._instance_count

    @classmethod
    def get_config(cls):
        return cls._config

p1 = DataProcessor("first")
p2 = DataProcessor("second")
count = DataProcessor.get_count()
config = DataProcessor.get_config()
"""
    # Should execute without AttributeError
    run_obfuscated_code(code)


def test_class_attribute_with_self_class():
    """Test self.__class__.attribute pattern."""
    code = """
class SharedState:
    _shared = {}

    def __init__(self):
        self.__class__._shared['initialized'] = True

    def get_shared(self):
        return self.__class__._shared

obj = SharedState()
result = obj.get_shared()
"""
    # Should execute without AttributeError
    run_obfuscated_code(code)


def test_class_attribute_analyzer_tracking():
    """Test that analyzer correctly tracks class attributes."""
    code = """
class MyClass:
    class_var1 = 10
    class_var2 = 20

    def method(self):
        return MyClass.class_var1
"""

    tree = ast.parse(code)
    config = ObfuscationConfig()
    analyzer = SymbolAnalyzer(config)
    analyzer.analyze(tree)

    # Verify that class attributes are tracked
    assert 'MyClass' in analyzer.class_attributes
    assert 'class_var1' in analyzer.class_attributes['MyClass']
    assert 'class_var2' in analyzer.class_attributes['MyClass']
    assert 'class_var1' in analyzer.all_class_attributes
    assert 'class_var2' in analyzer.all_class_attributes


def test_class_attribute_vs_method():
    """Test that both class attributes and methods are renamed correctly."""
    code = """
class MixedClass:
    _count = 0

    def increment(self):
        MixedClass._count += 1

    @classmethod
    def get_count(cls):
        return cls._count

obj = MixedClass()
obj.increment()
result = MixedClass.get_count()
"""
    # Should execute without AttributeError
    run_obfuscated_code(code)


def test_issue_7_exact_reproduction():
    """Exact test case from Issue #7."""
    code = """
class DataProcessor:
    _instance_count = 0

    def __init__(self, name: str):
        DataProcessor._instance_count += 1

    @classmethod
    def get_count(cls):
        return cls._instance_count

# Create instances
p1 = DataProcessor("first")
p2 = DataProcessor("second")
count = DataProcessor.get_count()
"""
    # Should execute without AttributeError
    run_obfuscated_code(code)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
