"""
Tests for AES-256 String Encryption feature - Pro Edition.

Tests that string literals are encrypted with AES-256 (Fernet) and runtime
decryption infrastructure is properly injected.
"""

import pytest
from typing import TYPE_CHECKING

from pyobfus.core.parser import ASTParser
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.config import ObfuscationConfig

# Pro features require pyobfus_pro to be installed
PRO_AVAILABLE = False
if TYPE_CHECKING:
    from pyobfus_pro.string_aes import StringAESEncryptor
else:
    try:
        from pyobfus_pro.string_aes import StringAESEncryptor

        PRO_AVAILABLE = True
    except ImportError:
        pass


@pytest.mark.skipif(not PRO_AVAILABLE, reason="Pro features not installed")
class TestStringAESEncryption:
    """Test suite for AES-256 string encryption feature."""

    def test_basic_string_encryption(self):
        """Test that string literals are encrypted with AES-256."""
        code = """
message = "Hello, World!"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Original string should not appear in plaintext
        assert "Hello, World!" not in obfuscated_code

        # Decryption function should be present
        assert (
            "_decrypt_str" in obfuscated_code or encryptor.decrypt_function_name in obfuscated_code
        )

        # Encryption key should be present
        assert (
            "_ENCRYPTION_KEY" in obfuscated_code or encryptor.key_variable_name in obfuscated_code
        )

        # Code should be executable and produce correct result
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["message"] == "Hello, World!"

    def test_multiple_strings_encrypted(self):
        """Test that multiple strings are all encrypted independently."""
        code = """
greeting = "Hello"
name = "Alice"
farewell = "Goodbye"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
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
        """Test that f-strings are not encrypted (they contain runtime expressions)."""
        code = """
name = "Bob"
message = f"Hello, {name}!"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Static string "Bob" should be encrypted
        assert "Bob" not in obfuscated_code

        # F-string should still work
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["name"] == "Bob"
        assert namespace["message"] == "Hello, Bob!"

        # Statistics should show skipped f-strings
        stats = encryptor.get_statistics()
        assert stats["skipped_fstrings"] >= 1

    def test_unicode_strings(self):
        """Test encryption of Unicode strings."""
        code = """
chinese = "你好世界"
emoji = "Hello 🌍"
german = "Guten Tag"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Unicode strings should not appear
        assert "你好世界" not in obfuscated_code
        assert "🌍" not in obfuscated_code
        assert "Guten Tag" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["chinese"] == "你好世界"
        assert namespace["emoji"] == "Hello 🌍"
        assert namespace["german"] == "Guten Tag"

    def test_long_strings(self):
        """Test encryption of long strings."""
        long_text = "Lorem ipsum dolor sit amet, " * 50  # ~1400 chars
        code = f"""
long_string = "{long_text}"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Long string should not appear in plaintext
        assert long_text not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["long_string"] == long_text

    def test_strings_in_function(self):
        """Test that strings inside functions are encrypted."""
        code = """
def greet():
    return "Hello from function"
result = greet()
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # String should not appear
        assert "Hello from function" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["result"] == "Hello from function"

    def test_strings_in_class(self):
        """Test that strings inside classes are encrypted."""
        code = """
class Greeter:
    message = "Class message"

    def greet(self):
        return "Instance method"

obj = Greeter()
class_msg = obj.message
method_msg = obj.greet()
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Strings should not appear
        assert "Class message" not in obfuscated_code
        assert "Instance method" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["class_msg"] == "Class message"
        assert namespace["method_msg"] == "Instance method"

    def test_docstring_preservation(self):
        """Test that docstrings are skipped when remove_docstrings=False."""
        code = '''
"""Module docstring"""

def func():
    """Function docstring"""
    return "Return value"

class MyClass:
    """Class docstring"""
    pass

result = func()
'''
        config = ObfuscationConfig()
        config.string_encryption = True
        config.remove_docstrings = False

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Docstrings should remain (not encrypted)
        assert "Module docstring" in obfuscated_code or "Module docstring" in str(obfuscated_tree)
        assert "Function docstring" in obfuscated_code or "Function docstring" in str(
            obfuscated_tree
        )
        assert "Class docstring" in obfuscated_code or "Class docstring" in str(obfuscated_tree)

        # Regular string should be encrypted
        assert "Return value" not in obfuscated_code

        # Code should execute
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["result"] == "Return value"

    def test_special_characters(self):
        """Test encryption of strings with special characters."""
        code = r"""
newline = "Line1\nLine2"
tab = "Col1\tCol2"
quote = "He said \"Hello\""
backslash = "Path\\to\\file"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["newline"] == "Line1\nLine2"
        assert namespace["tab"] == "Col1\tCol2"
        assert namespace["quote"] == 'He said "Hello"'
        assert namespace["backslash"] == "Path\\to\\file"

    def test_empty_string(self):
        """Test that empty strings are not encrypted, but other strings are."""
        code = """
empty = ""
short = "test_xyz"
normal = "Hello"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Empty string should remain (not worth encrypting)
        # All non-empty strings should be encrypted
        assert '"test_xyz"' not in obfuscated_code
        assert "Hello" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["empty"] == ""
        assert namespace["short"] == "test_xyz"
        assert namespace["normal"] == "Hello"

    def test_statistics(self):
        """Test that encryption statistics are correctly reported."""
        code = """
string1 = "First"
string2 = "Second"
fstring = f"Dynamic {string1}"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        _obfuscated_tree = encryptor.transform(tree)  # noqa: F841

        stats = encryptor.get_statistics()
        assert "encrypted_strings" in stats
        assert "skipped_fstrings" in stats
        assert stats["encrypted_strings"] >= 2  # At least "First" and "Second"
        assert stats["skipped_fstrings"] >= 1  # The f-string

    def test_different_string_types(self):
        """Test encryption of different types of string constants."""
        code = """
single = 'Single quotes'
double = "Double quotes"
triple_single = '''Triple single'''
triple_double = \"\"\"Triple double\"\"\"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # None should appear in plaintext
        assert "Single quotes" not in obfuscated_code
        assert "Double quotes" not in obfuscated_code
        assert "Triple single" not in obfuscated_code
        assert "Triple double" not in obfuscated_code

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["single"] == "Single quotes"
        assert namespace["double"] == "Double quotes"
        assert namespace["triple_single"] == "Triple single"
        assert namespace["triple_double"] == "Triple double"

    def test_fstring_with_function_call(self):
        """Test f-strings with function calls inside (Issue #10 related)."""
        code = """
def get_name():
    return "Alice"

greeting = f"Hello, {get_name()}!"
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # F-string should work correctly (this was Issue #10)
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["greeting"] == "Hello, Alice!"

    def test_nested_structures(self):
        """Test encryption in nested data structures."""
        code = """
data = {
    "key1": "value1",
    "key2": ["item1", "item2"],
    "key3": {"nested": "value"}
}
"""
        config = ObfuscationConfig()
        config.string_encryption = True

        tree = ASTParser.parse_string(code)
        analyzer = SymbolAnalyzer(config)
        analyzer.analyze(tree)

        encryptor = StringAESEncryptor(config, analyzer)
        obfuscated_tree = encryptor.transform(tree)
        obfuscated_code = CodeGenerator.generate(obfuscated_tree)

        # Strings should not appear
        assert "value1" not in obfuscated_code
        assert "item1" not in obfuscated_code
        assert "item2" not in obfuscated_code
        assert (
            "value" not in obfuscated_code or obfuscated_code.count("value") <= 1
        )  # May appear once in key

        # Code should execute correctly
        namespace = {}
        exec(obfuscated_code, namespace)
        assert namespace["data"]["key1"] == "value1"
        assert namespace["data"]["key2"] == ["item1", "item2"]
        assert namespace["data"]["key3"]["nested"] == "value"
