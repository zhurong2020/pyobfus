"""
Tests for String Encoding (Base64) feature - Community Edition.

Tests that string literals are encoded with Base64 and runtime decoding
infrastructure is properly injected.
"""

import ast
import base64
import pytest

from pyobfus.core.parser import ASTParser
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.config import ObfuscationConfig
from pyobfus.transformers.string_encoder import StringEncoder


class TestStringEncoding:
    """Test suite for string encoding feature."""

    def test_basic_string_encoding(self):
        """Test that string literals are encoded with Base64."""
        code = """
message = "Hello, World!"
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original string should not appear in plaintext
        assert "Hello, World!" not in obfuscated_code

        # Decoder function should be present
        assert "_decode_str" in obfuscated_code or encoder.decode_function_name in obfuscated_code

        # Code should be executable and produce correct result
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["message"] == "Hello, World!"

    def test_multiple_strings_encoded(self):
        """Test that multiple strings are all encoded."""
        code = """
greeting = "Hello"
name = "Alice"
farewell = "Goodbye"
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original strings should not appear
        assert "Hello" not in obfuscated_code
        assert "Alice" not in obfuscated_code
        assert "Goodbye" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["greeting"] == "Hello"
        assert namespace["name"] == "Alice"
        assert namespace["farewell"] == "Goodbye"

    def test_fstring_skipped(self):
        """Test that f-strings are not encoded (they contain runtime expressions)."""
        code = """
name = "Alice"
greeting = f"Hello, {name}!"
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # F-string should still be present (at least the static parts)
        # The "Alice" string should be encoded, but f-string parts should remain

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["greeting"] == "Hello, Alice!"

        # Statistics should show skipped f-strings
        stats = encoder.get_statistics()
        assert stats["skipped_fstrings"] >= 1

    def test_docstring_preservation(self):
        """Test that docstrings are preserved and not encoded."""
        code = '''
def greet(name):
    """Greet the user."""
    return "Hello"
'''
        config = ObfuscationConfig()
        config.string_encoding = True
        config.remove_docstrings = False  # Keep docstrings

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Docstring should be preserved
        assert "Greet the user." in obfuscated_code

        # But return string should be encoded
        # (We can't easily check the encoded form, but we can verify execution)
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["greet"]("Alice") == "Hello"

    def test_empty_string_encoding(self):
        """Test that empty strings are handled correctly."""
        code = """
empty = ""
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["empty"] == ""

    def test_string_in_function_call(self):
        """Test that strings in function calls are encoded."""
        code = """
result = len("Hello")
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original string should not appear
        assert "Hello" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["result"] == 5

    def test_string_in_return_statement(self):
        """Test that strings in return statements are encoded."""
        code = """
def get_message():
    return "Success"
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original string should not appear
        assert "Success" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["get_message"]() == "Success"

    def test_multiline_string_encoding(self):
        """Test that multiline strings are encoded correctly."""
        code = '''
text = """This is
a multiline
string"""
'''
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original multiline string should not appear
        assert "This is" not in obfuscated_code or "a multiline" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["text"] == "This is\na multiline\nstring"

    def test_unicode_string_encoding(self):
        """Test that Unicode strings are encoded correctly."""
        code = """
chinese = "你好世界"
emoji = "Hello 👋 World"
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original strings should not appear
        assert "你好世界" not in obfuscated_code
        assert "👋" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["chinese"] == "你好世界"
        assert namespace["emoji"] == "Hello 👋 World"

    def test_statistics_reporting(self):
        """Test that statistics are reported correctly."""
        code = """
str1 = "Hello"
str2 = "World"
fstring = f"Hello {str1}"
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        encoder.transform(tree)

        stats = encoder.get_statistics()
        assert stats["encoded_strings"] >= 2  # At least "Hello" and "World"
        assert stats["skipped_fstrings"] >= 1  # The f-string

    def test_string_concatenation(self):
        """Test that concatenated strings are encoded."""
        code = """
result = "Hello" + " " + "World"
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original strings should not appear
        assert "Hello" not in obfuscated_code
        assert "World" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["result"] == "Hello World"

    def test_string_in_list_dict(self):
        """Test that strings in collections are encoded."""
        code = """
my_list = ["apple", "banana", "cherry"]
my_dict = {"key1": "value1", "key2": "value2"}
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original strings should not appear
        assert "apple" not in obfuscated_code
        assert "banana" not in obfuscated_code
        assert "value1" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["my_list"] == ["apple", "banana", "cherry"]
        assert namespace["my_dict"] == {"key1": "value1", "key2": "value2"}

    def test_special_characters_encoding(self):
        """Test that strings with special characters are encoded correctly."""
        code = r"""
newline = "Hello\nWorld"
tab = "Hello\tWorld"
quote = "He said \"Hello\""
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["newline"] == "Hello\nWorld"
        assert namespace["tab"] == "Hello\tWorld"
        assert namespace["quote"] == 'He said "Hello"'

    def test_no_encoding_when_disabled(self):
        """Test that strings are not encoded when feature is disabled."""
        code = """
message = "Hello, World!"
"""
        config = ObfuscationConfig()
        config.string_encoding = False

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # String should remain in plaintext
        assert "Hello, World!" in obfuscated_code

        # No decoder function should be injected
        assert "_decode_str" not in obfuscated_code

    def test_decoder_function_injected_only_when_needed(self):
        """Test that decoder function is only injected when strings are encoded."""
        code = """
x = 42
"""
        config = ObfuscationConfig()
        config.string_encoding = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encoder = StringEncoder(config, analyzer)
        obfuscated_tree = encoder.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # No strings to encode, so no decoder function should be present
        assert "_decode_str" not in obfuscated_code

        stats = encoder.get_statistics()
        assert stats["encoded_strings"] == 0
