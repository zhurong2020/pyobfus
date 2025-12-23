"""
Tests for configuration features (v0.2.1).

Tests for:
- Configuration templates (--init-config)
- Configuration validation (--validate-config)
- Auto-discovery of configuration files
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from pyobfus.config_templates import get_template, list_templates, TEMPLATES
from pyobfus.config_validator import (
    validate_config_file,
    find_config_file,
    ValidationResult,
)


class TestConfigTemplates:
    """Test suite for configuration templates."""

    def test_list_templates(self):
        """Test that all expected templates are available."""
        templates = list_templates()
        assert "django" in templates
        assert "flask" in templates
        assert "library" in templates
        assert "general" in templates
        assert len(templates) == 4

    def test_get_template_django(self):
        """Test Django template content."""
        template = get_template("django")
        assert "django" in template.lower()
        assert "migrations" in template
        assert "urlpatterns" in template
        assert "Meta" in template

    def test_get_template_flask(self):
        """Test Flask template content."""
        template = get_template("flask")
        assert "flask" in template.lower()
        assert "create_app" in template
        assert "blueprint" in template

    def test_get_template_library(self):
        """Test library template content."""
        template = get_template("library")
        assert "library" in template.lower()
        assert "__version__" in template
        assert "preserve_param_names" in template

    def test_get_template_general(self):
        """Test general template content."""
        template = get_template("general")
        assert "main" in template
        assert "logger" in template

    def test_get_template_invalid(self):
        """Test that invalid template name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_template("invalid_template")
        assert "Unknown template" in str(exc_info.value)
        assert "invalid_template" in str(exc_info.value)

    def test_templates_are_valid_yaml(self):
        """Test that all templates are valid YAML."""
        for name, content in TEMPLATES.items():
            try:
                config = yaml.safe_load(content)
                assert config is not None, f"Template {name} loaded as None"
                assert isinstance(config, dict), f"Template {name} is not a dict"
                assert "obfuscation" in config, f"Template {name} missing 'obfuscation'"
            except yaml.YAMLError as e:
                pytest.fail(f"Template {name} is not valid YAML: {e}")


class TestConfigValidator:
    """Test suite for configuration validator."""

    def test_validate_valid_config(self):
        """Test validation of a valid configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(
                """
obfuscation:
  level: community
  string_encoding: true
  exclude_names:
    - main
    - logger
"""
            )
            result = validate_config_file(config_path)
            assert result.is_valid
            assert len(result.errors) == 0

    def test_validate_invalid_level(self):
        """Test validation catches invalid obfuscation level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(
                """
obfuscation:
  level: ultra
"""
            )
            result = validate_config_file(config_path)
            assert not result.is_valid
            assert len(result.errors) == 1
            assert "level" in result.errors[0].lower()
            assert "ultra" in result.errors[0]

    def test_validate_typo_detection(self):
        """Test validation detects common typos."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(
                """
obfuscation:
  level: community
  exclude_pattern:
    - test.py
  string_encode: true
"""
            )
            result = validate_config_file(config_path)
            # Should have warnings for typos
            assert len(result.warnings) > 0
            # Should have suggestions
            assert len(result.suggestions) > 0
            # Check for typo suggestions
            all_output = " ".join(result.warnings + result.suggestions)
            assert "exclude_patterns" in all_output
            assert "string_encoding" in all_output

    def test_validate_pro_feature_warning(self):
        """Test validation warns about Pro features with community level."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text(
                """
obfuscation:
  level: community
  string_encryption: true
"""
            )
            result = validate_config_file(config_path)
            # Should have warning about Pro features
            assert len(result.warnings) > 0
            all_warnings = " ".join(result.warnings)
            assert "pro" in all_warnings.lower() or "string_encryption" in all_warnings

    def test_validate_nonexistent_file(self):
        """Test validation handles nonexistent file."""
        result = validate_config_file(Path("/nonexistent/path/config.yaml"))
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "not found" in result.errors[0].lower()

    def test_validate_invalid_yaml(self):
        """Test validation handles invalid YAML syntax."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("invalid: yaml: content: [")
            result = validate_config_file(config_path)
            assert not result.is_valid
            assert len(result.errors) == 1
            assert "yaml" in result.errors[0].lower()

    def test_validate_empty_file(self):
        """Test validation handles empty file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"
            config_path.write_text("")
            result = validate_config_file(config_path)
            assert not result.is_valid
            assert len(result.errors) == 1
            assert "empty" in result.errors[0].lower()


class TestConfigAutoDiscovery:
    """Test suite for configuration auto-discovery."""

    def test_find_config_yaml(self):
        """Test finding pyobfus.yaml file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyobfus.yaml"
            config_path.write_text("obfuscation:\n  level: community\n")

            found_path, config_type = find_config_file(Path(tmpdir))
            assert found_path == config_path
            assert config_type == "yaml"

    def test_find_config_yml(self):
        """Test finding pyobfus.yml file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "pyobfus.yml"
            config_path.write_text("obfuscation:\n  level: community\n")

            found_path, config_type = find_config_file(Path(tmpdir))
            assert found_path == config_path
            assert config_type == "yaml"

    def test_find_config_hidden(self):
        """Test finding .pyobfus.yaml hidden file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".pyobfus.yaml"
            config_path.write_text("obfuscation:\n  level: community\n")

            found_path, config_type = find_config_file(Path(tmpdir))
            assert found_path == config_path
            assert config_type == "yaml"

    def test_find_config_priority(self):
        """Test that pyobfus.yaml has priority over .pyobfus.yaml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create both files
            primary = Path(tmpdir) / "pyobfus.yaml"
            hidden = Path(tmpdir) / ".pyobfus.yaml"
            primary.write_text("obfuscation:\n  level: community\n")
            hidden.write_text("obfuscation:\n  level: pro\n")

            found_path, _ = find_config_file(Path(tmpdir))
            assert found_path == primary

    def test_find_config_not_found(self):
        """Test when no config file exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found_path, config_type = find_config_file(Path(tmpdir))
            assert found_path is None
            assert config_type is None


class TestValidationResult:
    """Test suite for ValidationResult class."""

    def test_empty_result_is_valid(self):
        """Test that empty result is valid."""
        result = ValidationResult()
        assert result.is_valid
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_result_with_error_is_invalid(self):
        """Test that result with error is invalid."""
        result = ValidationResult()
        result.add_error("Test error")
        assert not result.is_valid
        assert len(result.errors) == 1

    def test_result_with_warning_is_valid(self):
        """Test that result with only warnings is still valid."""
        result = ValidationResult()
        result.add_warning("Test warning")
        assert result.is_valid
        assert len(result.warnings) == 1

    def test_summary_valid(self):
        """Test summary for valid config."""
        result = ValidationResult()
        assert "valid" in result.get_summary().lower()

    def test_summary_valid_with_warnings(self):
        """Test summary for valid config with warnings."""
        result = ValidationResult()
        result.add_warning("Warning 1")
        result.add_warning("Warning 2")
        summary = result.get_summary()
        assert "valid" in summary.lower()
        assert "2" in summary

    def test_summary_invalid(self):
        """Test summary for invalid config."""
        result = ValidationResult()
        result.add_error("Error 1")
        summary = result.get_summary()
        assert "invalid" in summary.lower()
        assert "1" in summary
