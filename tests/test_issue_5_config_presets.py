"""
Test case for Issue #5: Configuration presets and auto-detection.

This test suite covers:
1. Configuration presets (Safe, Balanced, Aggressive)
2. Auto-detection of public APIs
3. Preservation of documented methods
"""

import ast

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.transformers.name_mangler import NameMangler


class TestConfigurationPresets:
    """Test configuration preset functionality."""

    def test_preset_safe(self):
        """Test Safe preset configuration."""
        config = ObfuscationConfig.preset_safe()

        assert config.remove_docstrings is False
        # Safe preset should keep docstrings

    def test_preset_balanced(self):
        """Test Balanced preset configuration (default)."""
        config = ObfuscationConfig.preset_balanced()

        assert config.remove_docstrings is True
        assert isinstance(config.exclude_names, set)
        # Balanced is default configuration

    def test_preset_aggressive(self):
        """Test Aggressive preset configuration."""
        config = ObfuscationConfig.preset_aggressive()

        assert config.remove_docstrings is True
        assert config.remove_comments is True
        # Aggressive has minimal exclusions
        assert len(config.exclude_names) < 10

    def test_preset_comparison(self):
        """Compare exclusion sizes across presets."""
        ObfuscationConfig.preset_safe()
        balanced = ObfuscationConfig.preset_balanced()
        aggressive = ObfuscationConfig.preset_aggressive()

        # Aggressive should have fewest exclusions
        assert len(aggressive.exclude_names) < len(balanced.exclude_names)


class TestAutoDetection:
    """Test automatic public API detection."""

    def test_detect_public_methods_with_docstrings(self):
        """Test detection of public methods with docstrings."""
        code = """
class Calculator:
    def add(self, a, b):
        \"\"\"Add two numbers.\"\"\"
        return a + b

    def _internal_compute(self, x):
        # Private method
        return x * 2

calc = Calculator()
result = calc.add(5, 3)
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.enable_auto_detection(True)
        analyzer.analyze(tree)

        # With auto-detection, public methods with docstrings should be detected
        assert "add" in analyzer.public_api_names
        assert "add" in analyzer.names_with_docstrings

        # Private methods should not be in public API
        assert "_internal_compute" not in analyzer.public_api_names

    def test_detect_public_by_naming_convention(self):
        """Test detection of public methods by naming convention."""
        code = """
class Service:
    def process_data(self, data):
        return self._clean(data)

    def _clean(self, data):
        return data.strip()

    def validate(self, data):
        return len(data) > 0
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.enable_auto_detection(True)
        analyzer.analyze(tree)

        # Public methods (no leading underscore)
        assert "process_data" in analyzer.public_api_names
        assert "validate" in analyzer.public_api_names

        # Private method (leading underscore)
        assert "_clean" not in analyzer.public_api_names

    def test_auto_detection_preserves_public_apis(self):
        """Test that auto-detection prevents obfuscation of public APIs."""
        code = """
class Library:
    def public_method(self):
        \"\"\"This is a public API.\"\"\"
        return self._private_helper()

    def _private_helper(self):
        return "helper"

lib = Library()
result = lib.public_method()
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        analyzer.enable_auto_detection(True)
        analyzer.analyze(tree)

        # public_method should NOT be obfuscatable (it's public)
        assert "public_method" not in analyzer.obfuscatable_names

        # _private_helper SHOULD be obfuscatable
        assert "_private_helper" in analyzer.obfuscatable_names

        # Transform with auto-detection
        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Auto-Detection) ===")
        print(obfuscated_code)

        # Public method should be preserved
        assert "public_method" in obfuscated_code

        # Private helper should be obfuscated
        assert "_private_helper" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        string_values = [v for v in namespace.values() if isinstance(v, str) and v == "helper"]
        assert len(string_values) > 0

    def test_auto_detection_disabled_by_default(self):
        """Test that auto-detection is disabled by default."""
        code = """
class Example:
    def public_method(self):
        \"\"\"Public API.\"\"\"
        return 42
"""
        tree = ast.parse(code)
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        # Don't enable auto-detection
        analyzer.analyze(tree)

        # With auto-detection disabled, even public methods are obfuscatable
        assert "public_method" in analyzer.obfuscatable_names


class TestSafePresetBehavior:
    """Test Safe preset with auto-detection."""

    def test_safe_preset_preserves_docstrings(self):
        """Test that Safe preset preserves docstrings."""
        code = """
def calculate_risk(age, health_score):
    \"\"\"
    Calculate patient risk score.

    Args:
        age: Patient age
        health_score: Health assessment score

    Returns:
        float: Risk score between 0 and 1
    \"\"\"
    return age * 0.01 + health_score * 0.5
"""
        tree = ast.parse(code)
        config = ObfuscationConfig.preset_safe()
        analyzer = SymbolAnalyzer(config)
        analyzer.enable_auto_detection(True)
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Safe Preset) ===")
        print(obfuscated_code)

        # Docstring should be preserved (Safe preset)
        assert "Calculate patient risk score" in obfuscated_code

        # Public function with docstring should be preserved
        assert "calculate_risk" in obfuscated_code


class TestAggressivePresetBehavior:
    """Test Aggressive preset behavior."""

    def test_aggressive_preset_obfuscates_everything(self):
        """Test that Aggressive preset obfuscates maximum names."""
        code = """
def helper_function(x):
    return x * 2

def process_data(data):
    \"\"\"Process the data.\"\"\"
    return helper_function(data)

result = process_data(5)
"""
        tree = ast.parse(code)
        config = ObfuscationConfig.preset_aggressive()
        analyzer = SymbolAnalyzer(config)
        # Note: Aggressive doesn't use auto-detection by default
        analyzer.analyze(tree)

        mangler = NameMangler(config, analyzer)
        transformed = mangler.transform(tree)

        generator = CodeGenerator()
        obfuscated_code = generator.generate(transformed)

        print("\n=== Obfuscated Code (Aggressive Preset) ===")
        print(obfuscated_code)

        # Aggressive removes docstrings
        assert "Process the data" not in obfuscated_code

        # Both functions should be obfuscated
        assert "helper_function" not in obfuscated_code
        assert "process_data" not in obfuscated_code

        # Execute to verify correctness
        namespace = {}
        exec(obfuscated_code, namespace)
        int_values = [v for v in namespace.values() if isinstance(v, int) and v == 10]
        assert len(int_values) > 0
