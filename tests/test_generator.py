"""
Tests for the code generator module.

Focuses on f-string quote handling and validation to prevent syntax errors
in generated code.
"""

import ast

from pyobfus.core.generator import CodeGenerator


class TestFStringQuoteFix:
    """Test f-string quote conflict detection and fixing."""

    def test_valid_code_unchanged(self):
        """Valid code should pass through without modification."""
        valid_code = """print(f"Value: {data['key']}")"""
        result = CodeGenerator._fix_fstring_quotes(valid_code)
        assert result == valid_code

    def test_single_quote_fstring_with_single_quote_subscript(self):
        """f'...' with ['key'] should be fixed to ["key"]."""
        invalid_code = """print(f'Value: {data['key']}')"""
        result = CodeGenerator._fix_fstring_quotes(invalid_code)
        assert result == """print(f'Value: {data["key"]}')"""
        # Verify it compiles
        compile(result, "<test>", "exec")

    def test_multiple_subscripts_in_single_fstring(self):
        """Multiple subscripts in one f-string should all be fixed."""
        invalid_code = """print(f'A: {d['a']}, B: {d['b']}')"""
        result = CodeGenerator._fix_fstring_quotes(invalid_code)
        assert result == """print(f'A: {d["a"]}, B: {d["b"]}')"""
        compile(result, "<test>", "exec")

    def test_nested_dict_access(self):
        """Nested dictionary access should be handled."""
        invalid_code = """print(f'{d['a']['b']}')"""
        result = CodeGenerator._fix_fstring_quotes(invalid_code)
        assert result == """print(f'{d["a"]["b"]}')"""
        compile(result, "<test>", "exec")

    def test_mixed_content_fstring(self):
        """f-string with mixed content (vars and subscripts)."""
        invalid_code = """x = f'Name: {name}, Key: {d['key']}'"""
        result = CodeGenerator._fix_fstring_quotes(invalid_code)
        assert result == """x = f'Name: {name}, Key: {d["key"]}'"""
        compile(result, "<test>", "exec")

    def test_double_quote_fstring_unchanged(self):
        """f-string with double quotes and single-quote subscripts is valid."""
        valid_code = """print(f"Value: {data['key']}")"""
        result = CodeGenerator._fix_fstring_quotes(valid_code)
        assert result == valid_code
        compile(result, "<test>", "exec")

    def test_multiple_fstrings_in_code(self):
        """Multiple f-strings in the same code block."""
        invalid_code = """
x = f'First: {d['a']}'
y = f'Second: {d['b']}'
"""
        result = CodeGenerator._fix_fstring_quotes(invalid_code)
        assert """f'First: {d["a"]}'""" in result
        assert """f'Second: {d["b"]}'""" in result
        compile(result, "<test>", "exec")

    def test_fstring_with_function_call(self):
        """f-string containing function call with subscript."""
        invalid_code = """print(f'{str(d['key'])}')"""
        result = CodeGenerator._fix_fstring_quotes(invalid_code)
        assert result == """print(f'{str(d["key"])}')"""
        compile(result, "<test>", "exec")

    def test_fstring_with_method_call(self):
        """f-string containing method call on subscripted value."""
        invalid_code = """print(f'{d['key'].upper()}')"""
        result = CodeGenerator._fix_fstring_quotes(invalid_code)
        assert result == """print(f'{d["key"].upper()}')"""
        compile(result, "<test>", "exec")

    def test_empty_fstring(self):
        """Empty f-string should be unchanged."""
        valid_code = """x = f''"""
        result = CodeGenerator._fix_fstring_quotes(valid_code)
        assert result == valid_code

    def test_fstring_without_expressions(self):
        """f-string without expressions should be unchanged."""
        valid_code = """x = f'Hello, World!'"""
        result = CodeGenerator._fix_fstring_quotes(valid_code)
        assert result == valid_code

    def test_regular_string_unchanged(self):
        """Regular strings (not f-strings) should be unchanged."""
        valid_code = """x = 'Hello'
y = "World"
z = data['key']"""
        result = CodeGenerator._fix_fstring_quotes(valid_code)
        assert result == valid_code

    def test_fstring_with_numeric_index(self):
        """f-string with numeric index should be unchanged (no quotes)."""
        valid_code = """print(f'{lst[0]}')"""
        result = CodeGenerator._fix_fstring_quotes(valid_code)
        assert result == valid_code
        compile(result, "<test>", "exec")

    def test_fstring_with_variable_index(self):
        """f-string with variable index should be unchanged."""
        valid_code = """print(f'{d[key]}')"""
        result = CodeGenerator._fix_fstring_quotes(valid_code)
        assert result == valid_code
        compile(result, "<test>", "exec")


class TestCodeGeneratorGenerate:
    """Test the main generate method."""

    def test_generate_simple_code(self):
        """Generate simple Python code from AST."""
        code = "x = 1"
        tree = ast.parse(code)
        result = CodeGenerator.generate(tree)
        assert "x" in result
        assert "1" in result

    def test_generate_with_fstring(self):
        """Generate code containing f-strings."""
        code = """data = {'key': 'value'}
print(f"Value: {data['key']}")"""
        tree = ast.parse(code)
        result = CodeGenerator.generate(tree)
        # Should compile without errors
        compile(result, "<test>", "exec")

    def test_generate_validates_output(self):
        """Generated code should always be valid Python."""
        # Complex code with potential edge cases
        code = """
def process(data):
    result = {}
    for key in data:
        result[key] = data[key] * 2
    return f"Processed {len(result)} items"
"""
        tree = ast.parse(code)
        result = CodeGenerator.generate(tree)
        compile(result, "<test>", "exec")


class TestPython36Compatibility:
    """Test that generated code is compatible with Python 3.6-3.11."""

    def test_fstring_quotes_always_normalized(self):
        """f-string quotes should ALWAYS be normalized for backward compatibility.

        Python 3.12+ (PEP 701) allows f'text {d['key']}' but Python 3.6-3.11 don't.
        PyObfus must generate code compatible with ALL supported Python versions.
        """
        # Even if this code would compile on Python 3.12+, we need to normalize it
        # Input simulates what ast.unparse might produce on Python 3.12+
        code_with_same_quotes = """print(f'Value: {data['key']}')"""

        result = CodeGenerator._fix_fstring_quotes(code_with_same_quotes)

        # Should use different quotes for subscript
        assert '["key"]' in result or "['key']" not in result.replace("f'", "")
        # Must compile on all Python versions
        compile(result, "<test>", "exec")

    def test_double_quote_fstring_normalized(self):
        """Double-quote f-strings with double-quote subscripts should be fixed."""
        code = """print(f"Value: {data["key"]}")"""
        result = CodeGenerator._fix_fstring_quotes(code)

        # Should use single quotes for subscript inside double-quoted f-string
        assert "['key']" in result
        compile(result, "<test>", "exec")

    def test_already_compatible_code_unchanged(self):
        """Code already using different quotes should remain valid."""
        # This is already compatible with all Python versions
        compatible_code = """print(f"Value: {data['key']}")"""
        result = CodeGenerator._fix_fstring_quotes(compatible_code)

        # Should remain unchanged (or equivalent)
        compile(result, "<test>", "exec")
        assert "['key']" in result  # Still uses single quotes for subscript


class TestIntegrationWithObfuscation:
    """Test f-string handling with actual obfuscation pipeline."""

    def test_obfuscated_code_with_fstring_subscript(self):
        """Obfuscated code with f-string subscripts should be valid."""
        from pyobfus.core.parser import ASTParser
        from pyobfus.core.analyzer import SymbolAnalyzer
        from pyobfus.transformers.name_mangler import NameMangler
        from pyobfus.transformers.string_encoder import StringEncoder
        from pyobfus.config import ObfuscationConfig

        code = """data = {'license_code': 'ABC123'}
print(f"License: {data['license_code']}")
"""
        tree = ASTParser.parse_string(code)
        config = ObfuscationConfig(string_encoding=True)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        # Apply transformations
        mangler = NameMangler(config, analyzer)
        tree = mangler.transform(tree)

        encoder = StringEncoder(config, analyzer)
        tree = encoder.transform(tree)

        # Generate code
        result = CodeGenerator.generate(tree)

        # Should compile and execute
        compile(result, "<test>", "exec")

        # Execute to verify behavior
        namespace = {}
        exec(result, namespace)
        # If we got here without error, the test passes

    def test_multiple_fstring_subscripts_after_obfuscation(self):
        """Multiple f-string subscripts should work after obfuscation."""
        from pyobfus.core.parser import ASTParser
        from pyobfus.core.analyzer import SymbolAnalyzer
        from pyobfus.transformers.name_mangler import NameMangler
        from pyobfus.config import ObfuscationConfig

        code = """data = {'key1': 'value1', 'key2': 'value2'}
result = f"K1: {data['key1']}, K2: {data['key2']}"
"""
        tree = ASTParser.parse_string(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        tree = mangler.transform(tree)

        result = CodeGenerator.generate(tree)
        compile(result, "<test>", "exec")

        namespace = {}
        exec(result, namespace)
        # Find the string result variable (not the dict)
        obfuscated_vars = [k for k in namespace.keys() if k.startswith("I")]
        # One of them should be the f-string result
        found_expected = False
        for var in obfuscated_vars:
            if namespace[var] == "K1: value1, K2: value2":
                found_expected = True
                break
        assert (
            found_expected
        ), f"Expected 'K1: value1, K2: value2' in namespace values: {[namespace[v] for v in obfuscated_vars]}"
