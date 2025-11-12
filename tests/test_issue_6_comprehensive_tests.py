"""
Test case for Issue #6: Comprehensive tests for method obfuscation and large files.

This test suite covers:
1. Additional method obfuscation patterns (decorators, properties, etc.)
2. Large file performance (3000+ lines)
3. Real-world code structures
"""

import ast
import time
import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.transformers.name_mangler import NameMangler


class TestMethodObfuscationPatterns:
    """Additional method obfuscation test patterns."""

    def test_decorator_method_obfuscation(self):
        """Test method obfuscation with decorators."""
        code = """
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class Service:
    @my_decorator
    def process(self, data):
        return data.upper()

svc = Service()
result = svc.process("hello")
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Decorator) ===")
        print(obfuscated_code)

        # Verify: method name should be obfuscated
        assert "process" not in obfuscated_code or obfuscated_code.count("process") == 0

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        result_values = [v for v in namespace.values() if isinstance(v, str) and v == "HELLO"]
        assert len(result_values) > 0

    def test_property_obfuscation(self):
        """Test obfuscation of property methods."""
        code = """
class Rectangle:
    def __init__(self, width, height):
        self._width = width
        self._height = height

    @property
    def area(self):
        return self._width * self._height

    @property
    def perimeter(self):
        return 2 * (self._width + self._height)

rect = Rectangle(5, 3)
a = rect.area
p = rect.perimeter
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Property) ===")
        print(obfuscated_code)

        # Note: Properties with @property decorator are tricky - the attribute access
        # looks different from method calls
        # This test documents current behavior

    def test_static_method_obfuscation(self):
        """Test static method obfuscation."""
        code = """
class MathUtils:
    @staticmethod
    def add(a, b):
        return a + b

    @staticmethod
    def multiply(a, b):
        return a * b

result1 = MathUtils.add(5, 3)
result2 = MathUtils.multiply(4, 2)
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Static Method) ===")
        print(obfuscated_code)

        # Verify: method names should be obfuscated
        assert "add" not in obfuscated_code
        assert "multiply" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        values = [v for v in namespace.values() if isinstance(v, int)]
        assert 8 in values  # result1
        assert 8 in values  # result2

    @pytest.mark.xfail(reason="Known limitation: class attributes accessed via cls.attribute not fully obfuscated")
    def test_class_method_obfuscation(self):
        """Test class method obfuscation."""
        # Note: This test demonstrates a current limitation - class attributes accessed
        # via cls.attribute are not yet fully obfuscated
        code = """
class Counter:
    value = 0

    @classmethod
    def increment(cls):
        cls.value += 1
        return cls.value

    @classmethod
    def get_value(cls):
        return cls.value

Counter.increment()
Counter.increment()
result = Counter.get_value()
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Class Method) ===")
        print(obfuscated_code)

        # Verify: method names should be obfuscated
        assert "increment" not in obfuscated_code
        assert "get_value" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        int_values = [v for v in namespace.values() if isinstance(v, int) and v == 2]
        assert len(int_values) > 0

    def test_private_method_obfuscation(self):
        """Test private method obfuscation."""
        code = """
class Database:
    def _connect(self):
        return "connected"

    def _execute(self, query):
        return f"Executed: {query}"

    def run_query(self, query):
        conn = self._connect()
        result = self._execute(query)
        return result

db = Database()
output = db.run_query("SELECT * FROM users")
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Private Methods) ===")
        print(obfuscated_code)

        # Verify: private method names should be obfuscated
        assert "_connect" not in obfuscated_code
        assert "_execute" not in obfuscated_code
        assert "run_query" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        expected = "Executed: SELECT * FROM users"
        string_values = [v for v in namespace.values() if isinstance(v, str) and v == expected]
        assert len(string_values) > 0

    @pytest.mark.xfail(reason="Known limitation: nested class access via Outer.Inner not fully obfuscated")
    def test_nested_class_methods(self):
        """Test obfuscation of nested class methods."""
        # Note: This test demonstrates a current limitation with nested class access
        code = """
class Outer:
    def outer_method(self):
        return "outer"

    class Inner:
        def inner_method(self):
            return "inner"

outer = Outer()
r1 = outer.outer_method()

# Access inner class directly (limitation: class attribute access not yet fully supported)
inner_class = Outer.__dict__['Inner']
inner = inner_class()
r2 = inner.inner_method()
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Nested Classes) ===")
        print(obfuscated_code)

        # Verify: method names should be obfuscated
        assert "outer_method" not in obfuscated_code
        assert "inner_method" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        assert any(v == "outer" for v in namespace.values() if isinstance(v, str))
        assert any(v == "inner" for v in namespace.values() if isinstance(v, str))


class TestLargeFilePerformance:
    """Test obfuscation performance on large files."""

    def test_large_file_3000_lines(self):
        """Test obfuscation of a large file (3000+ lines)."""
        # Generate a large synthetic code file
        classes = []
        for class_idx in range(50):
            methods = []
            for method_idx in range(20):
                method_code = f"""
    def method_{class_idx}_{method_idx}(self, x, y):
        # Some computation
        result = x + y
        result = result * 2
        result = result - 1
        result = result / 2
        return result
"""
                methods.append(method_code)

            class_code = f"""
class TestClass{class_idx}:
    def __init__(self):
        self.value = {class_idx}
{''.join(methods)}
"""
            classes.append(class_code)

        # Add functions
        functions = []
        for func_idx in range(100):
            func_code = f"""
def test_function_{func_idx}(a, b, c):
    temp1 = a + b
    temp2 = b + c
    temp3 = temp1 * temp2
    return temp3
"""
            functions.append(func_code)

        # Combine into one large file
        large_code = "\n".join(classes) + "\n".join(functions)

        # Count lines
        line_count = large_code.count("\n")
        print(f"\nGenerated code with {line_count} lines")
        assert line_count > 3000, "Test file should be at least 3000 lines"

        # Parse
        tree = ast.parse(large_code)

        # Analyze
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        start_time = time.time()
        analyzer.analyze(tree)
        analyze_time = time.time() - start_time

        # Transform
        mangler = NameMangler(config, analyzer)
        start_time = time.time()
        transformed = mangler.transform(tree)
        transform_time = time.time() - start_time

        # Generate
        generator = CodeGenerator()
        start_time = time.time()
        obfuscated_code = generator.generate(transformed)
        generate_time = time.time() - start_time

        total_time = analyze_time + transform_time + generate_time

        print(f"Analyze time: {analyze_time:.2f}s")
        print(f"Transform time: {transform_time:.2f}s")
        print(f"Generate time: {generate_time:.2f}s")
        print(f"Total time: {total_time:.2f}s")

        # Performance requirement: should complete in under 10 seconds
        assert total_time < 10.0, f"Performance requirement not met: {total_time:.2f}s > 10s"

        # Verify obfuscation worked
        assert "method_0_0" not in obfuscated_code
        assert "test_function_0" not in obfuscated_code
        assert "TestClass0" not in obfuscated_code

        # Verify code is valid
        compile(obfuscated_code, "<string>", "exec")


class TestRealWorldPatterns:
    """Test obfuscation on real-world code patterns."""

    def test_context_manager_methods(self):
        """Test obfuscation of context manager methods."""
        code = """
class FileManager:
    def __enter__(self):
        self.file = "opened"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file = "closed"
        return False

    def read_data(self):
        return self.file

with FileManager() as fm:
    data = fm.read_data()
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Context Manager) ===")
        print(obfuscated_code)

        # __enter__ and __exit__ should NOT be obfuscated (magic methods)
        assert "__enter__" in obfuscated_code
        assert "__exit__" in obfuscated_code

        # But read_data should be obfuscated
        assert "read_data" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)

    def test_method_chaining(self):
        """Test obfuscation with method chaining."""
        code = """
class Builder:
    def __init__(self):
        self.value = 0

    def add(self, x):
        self.value += x
        return self

    def multiply(self, x):
        self.value *= x
        return self

    def get_result(self):
        return self.value

result = Builder().add(5).multiply(3).add(2).get_result()
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Method Chaining) ===")
        print(obfuscated_code)

        # Verify: method names should be obfuscated
        assert "add" not in obfuscated_code
        assert "multiply" not in obfuscated_code
        assert "get_result" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        int_values = [v for v in namespace.values() if isinstance(v, int) and v == 17]
        assert len(int_values) > 0  # (5 + 2) would be 7, but (5 * 3) + 2 = 17

    def test_lambda_with_methods(self):
        """Test obfuscation when lambdas call methods."""
        code = """
class Processor:
    def process(self, x):
        return x * 2

p = Processor()
func = lambda x: p.process(x) + 10
result = func(5)
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Lambda with Methods) ===")
        print(obfuscated_code)

        # Verify: method name should be obfuscated
        assert "process" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        int_values = [v for v in namespace.values() if isinstance(v, int) and v == 20]
        assert len(int_values) > 0
