"""
Unit tests for License Embedding.

Tests the embedding of license restrictions (expiration, machine binding, run limits)
into obfuscated code.
"""

import ast
import os
import sys
import tempfile
from datetime import datetime, timedelta

import pytest

# Add pyobfus_pro to path for testing
sys.path.insert(0, str(__file__).replace("tests/test_license_embed.py", ""))

from pyobfus_pro.license_embed import LicenseEmbedder, LicenseEmbedConfig, embed_license_checks


class TestLicenseEmbedConfig:
    """Tests for LicenseEmbedConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LicenseEmbedConfig()
        assert config.enabled is True
        assert config.expire_date is None
        assert config.bind_machine is False
        assert config.max_runs == 0
        assert config.var_prefix == "_lic_"

    def test_expiration_config(self):
        """Test expiration date configuration."""
        config = LicenseEmbedConfig(expire_date="2025-12-31")
        assert config.expire_date == "2025-12-31"

    def test_machine_binding_config(self):
        """Test machine binding configuration."""
        config = LicenseEmbedConfig(bind_machine=True)
        assert config.bind_machine is True

    def test_max_runs_config(self):
        """Test max runs configuration."""
        config = LicenseEmbedConfig(max_runs=100)
        assert config.max_runs == 100

    def test_custom_messages(self):
        """Test custom error messages."""
        config = LicenseEmbedConfig(
            expire_message="License expired!",
            machine_message="Wrong machine!",
            runs_message="Too many runs!",
        )
        assert config.expire_message == "License expired!"
        assert config.machine_message == "Wrong machine!"
        assert config.runs_message == "Too many runs!"


class TestLicenseEmbedder:
    """Tests for LicenseEmbedder class."""

    def test_disabled_embedder(self):
        """Test that disabled embedder doesn't modify code."""
        code = """
def hello():
    print("Hello")
"""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(enabled=False, expire_date="2025-12-31")
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        # Should be unchanged
        assert len(result.body) == 1
        assert isinstance(result.body[0], ast.FunctionDef)

    def test_expiration_embedding(self):
        """Test expiration date embedding."""
        code = """
def hello():
    print("Hello")
"""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(expire_date="2025-12-31")
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        # Should have import + if statement before function
        assert len(result.body) > 1
        assert isinstance(result.body[0], ast.Import)  # import datetime
        assert isinstance(result.body[1], ast.If)  # if now > expire

        # Verify code compiles
        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_expiration_check_works(self):
        """Test that expiration check actually works at runtime."""
        code = """
result = "success"
"""
        # Use a future date - should not raise
        tree = ast.parse(code)
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        config = LicenseEmbedConfig(expire_date=future_date)
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        namespace = {}
        exec(compiled, namespace)
        assert namespace["result"] == "success"

    def test_expiration_raises_on_past_date(self):
        """Test that expired code raises RuntimeError."""
        code = """
result = "success"
"""
        # Use a past date - should raise
        tree = ast.parse(code)
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        config = LicenseEmbedConfig(expire_date=past_date)
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        with pytest.raises(RuntimeError, match="expired"):
            exec(compiled, {})

    def test_invalid_date_format(self):
        """Test that invalid date format raises ValueError."""
        code = "x = 1"
        tree = ast.parse(code)
        config = LicenseEmbedConfig(expire_date="invalid-date")
        embedder = LicenseEmbedder(config)

        with pytest.raises(ValueError, match="Invalid expire date format"):
            embedder.visit(tree)

    def test_machine_binding_embedding(self):
        """Test machine binding embedding."""
        code = """
def hello():
    print("Hello")
"""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(bind_machine=True)
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        # Should have imports + assignment + if statement
        assert len(result.body) > 1

        # Verify code compiles
        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_machine_binding_works_on_current_machine(self):
        """Test that machine binding works on the current machine."""
        code = """
result = "success"
"""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(bind_machine=True)
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        # Should work on current machine
        namespace = {}
        exec(compiled, namespace)
        assert namespace["result"] == "success"

    def test_machine_binding_fails_on_wrong_fingerprint(self):
        """Test that wrong machine fingerprint raises RuntimeError."""
        code = """
result = "success"
"""
        tree = ast.parse(code)
        # Use a specific fingerprint that won't match
        config = LicenseEmbedConfig(
            bind_machine=True,
            machine_fingerprint="0000000000000000",  # Wrong fingerprint
        )
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        with pytest.raises(RuntimeError, match="not licensed"):
            exec(compiled, {})

    def test_run_count_embedding(self):
        """Test run count limit embedding."""
        code = """
def hello():
    print("Hello")
"""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(max_runs=10)
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        # Should have import + path + count + try + augassign + write + if
        assert len(result.body) > 1

        # Verify code compiles
        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_run_count_works(self):
        """Test that run count tracking works."""
        code = """
result = "success"
"""
        # Use a unique counter file for this test
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pyobfus_test") as f:
            counter_file = os.path.basename(f.name)

        try:
            tree = ast.parse(code)
            config = LicenseEmbedConfig(max_runs=5, run_counter_filename=counter_file)
            embedder = LicenseEmbedder(config)
            result = embedder.visit(tree)

            ast.fix_missing_locations(result)
            compiled = compile(result, "<test>", "exec")

            # Should work for first 5 runs
            for i in range(5):
                namespace = {}
                exec(compiled, namespace)
                assert namespace["result"] == "success"

            # 6th run should fail
            with pytest.raises(RuntimeError, match="run limit"):
                exec(compiled, {})

        finally:
            # Cleanup
            counter_path = os.path.join(os.path.expanduser("~"), counter_file)
            if os.path.exists(counter_path):
                os.remove(counter_path)

    def test_get_current_fingerprint(self):
        """Test getting current machine fingerprint."""
        embedder = LicenseEmbedder()
        fp = embedder.get_current_fingerprint()

        assert isinstance(fp, str)
        assert len(fp) == 16  # 16 hex characters
        assert all(c in "0123456789abcdef" for c in fp)

    def test_combined_restrictions(self):
        """Test combining multiple restrictions."""
        code = """
result = "success"
"""
        future_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")

        tree = ast.parse(code)
        config = LicenseEmbedConfig(
            expire_date=future_date,
            bind_machine=True,
            max_runs=1000,
        )
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        # Should have all three checks
        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        # Should work on current machine with valid date
        namespace = {}
        exec(compiled, namespace)
        assert namespace["result"] == "success"


class TestConvenienceFunction:
    """Tests for embed_license_checks convenience function."""

    def test_embed_license_checks(self):
        """Test the convenience function."""
        code = """
def hello():
    print("Hello")
"""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(expire_date="2030-12-31")
        result = embed_license_checks(tree, config)

        # Should have expiration check
        assert len(result.body) > 1
        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_embed_without_config(self):
        """Test embedding without config (should do nothing)."""
        code = """
def hello():
    print("Hello")
"""
        tree = ast.parse(code)
        result = embed_license_checks(tree)  # No config = no restrictions

        # Should be unchanged
        assert len(result.body) == 1


class TestDocstringPreservation:
    """Tests for preserving module docstrings."""

    def test_preserves_module_docstring(self):
        """Test that module docstring is preserved."""
        code = '''"""This is a module docstring."""

def hello():
    print("Hello")
'''
        tree = ast.parse(code)
        config = LicenseEmbedConfig(expire_date="2030-12-31")
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        # First statement should still be the docstring
        assert isinstance(result.body[0], ast.Expr)
        assert isinstance(result.body[0].value, ast.Constant)
        assert "module docstring" in result.body[0].value.value

    def test_preserves_future_imports(self):
        """Test that __future__ imports are preserved at the top."""
        code = """from __future__ import annotations

def hello() -> str:
    return "Hello"
"""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(expire_date="2030-12-31")
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        # First statement should still be __future__ import
        assert isinstance(result.body[0], ast.ImportFrom)
        assert result.body[0].module == "__future__"


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_module(self):
        """Test embedding in empty module."""
        code = ""
        tree = ast.parse(code)
        config = LicenseEmbedConfig(expire_date="2030-12-31")
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_only_pass(self):
        """Test embedding in module with only pass."""
        code = "pass"
        tree = ast.parse(code)
        config = LicenseEmbedConfig(expire_date="2030-12-31")
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        ast.fix_missing_locations(result)
        compile(result, "<test>", "exec")

    def test_complex_module(self):
        """Test embedding in complex module."""
        code = '''"""Module docstring."""
from __future__ import annotations
import os
import sys

class MyClass:
    def __init__(self):
        self.value = 42

def main():
    obj = MyClass()
    return obj.value

if __name__ == "__main__":
    main()
'''
        tree = ast.parse(code)
        config = LicenseEmbedConfig(
            expire_date="2030-12-31",
            bind_machine=True,
        )
        embedder = LicenseEmbedder(config)
        result = embedder.visit(tree)

        ast.fix_missing_locations(result)
        compiled = compile(result, "<test>", "exec")

        # Execute and verify it works
        namespace = {}
        exec(compiled, namespace)
        assert namespace["MyClass"]().value == 42


# Run pytest if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
