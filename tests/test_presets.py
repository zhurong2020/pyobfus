"""
Unit tests for Configuration Presets.

Tests the preset configuration system for different use cases.
"""

import pytest
from datetime import datetime

from pyobfus.config import ObfuscationConfig


class TestCommunityPresets:
    """Tests for Community Edition presets."""

    def test_preset_safe(self):
        """Test safe preset configuration."""
        config = ObfuscationConfig.preset_safe()

        # Should preserve docstrings
        assert config.remove_docstrings is False
        # Default level
        assert config.level == "community"

    def test_preset_balanced(self):
        """Test balanced preset (default) configuration."""
        config = ObfuscationConfig.preset_balanced()

        # Should remove docstrings
        assert config.remove_docstrings is True
        assert config.remove_comments is True
        assert config.level == "community"

    def test_preset_aggressive(self):
        """Test aggressive preset configuration."""
        config = ObfuscationConfig.preset_aggressive()

        # Should remove everything
        assert config.remove_docstrings is True
        assert config.remove_comments is True
        # Should have minimal exclusions
        assert "__init__" in config.exclude_names
        assert len(config.exclude_names) < 10


class TestProPresets:
    """Tests for Pro Edition presets."""

    def test_preset_trial(self):
        """Test trial preset configuration."""
        config = ObfuscationConfig.preset_trial()

        # Should be Pro level
        assert config.level == "pro"
        # Should have expiration
        assert config.license_expire is not None
        # Expiration should be ~30 days from now
        expire_date = datetime.strptime(config.license_expire, "%Y-%m-%d")
        days_until = (expire_date - datetime.now()).days
        assert 29 <= days_until <= 31  # Allow for timing differences
        # Should have all Pro features
        assert config.string_encryption is True
        assert config.anti_debug is True
        assert config.control_flow_flattening is True
        assert config.dead_code_injection is True

    def test_preset_trial_custom_days(self):
        """Test trial preset with custom expiration days."""
        config = ObfuscationConfig.preset_trial(expire_days=7)

        expire_date = datetime.strptime(config.license_expire, "%Y-%m-%d")
        days_until = (expire_date - datetime.now()).days
        assert 6 <= days_until <= 8  # Allow for timing differences

    def test_preset_commercial(self):
        """Test commercial preset configuration."""
        config = ObfuscationConfig.preset_commercial()

        # Should be Pro level
        assert config.level == "pro"
        # Should have machine binding
        assert config.license_bind_machine is True
        # Should have all Pro features
        assert config.string_encryption is True
        assert config.anti_debug is True
        assert config.control_flow_flattening is True
        assert config.dead_code_injection is True
        # Should NOT have expiration or run limits
        assert config.license_expire is None
        assert config.license_max_runs == 0

    def test_preset_library(self):
        """Test library preset configuration."""
        config = ObfuscationConfig.preset_library()

        # Should be Pro level
        assert config.level == "pro"
        # Should preserve docstrings and param names
        assert config.remove_docstrings is False
        assert config.preserve_param_names is True
        # Should have string encryption
        assert config.string_encryption is True
        # Should NOT have aggressive features
        assert config.license_bind_machine is False

    def test_preset_maximum(self):
        """Test maximum preset configuration."""
        config = ObfuscationConfig.preset_maximum()

        # Should be Pro level
        assert config.level == "pro"
        # Should have ALL protections
        assert config.string_encryption is True
        assert config.anti_debug is True
        assert config.control_flow_flattening is True
        assert config.dead_code_injection is True
        assert config.license_bind_machine is True
        assert config.license_max_runs == 1000


class TestGetPreset:
    """Tests for get_preset method."""

    def test_get_preset_by_name(self):
        """Test getting presets by name."""
        config = ObfuscationConfig.get_preset("trial")
        assert config.level == "pro"
        assert config.license_expire is not None

        config = ObfuscationConfig.get_preset("commercial")
        assert config.license_bind_machine is True

        config = ObfuscationConfig.get_preset("safe")
        assert config.remove_docstrings is False

    def test_get_preset_case_insensitive(self):
        """Test that get_preset is case-insensitive."""
        config1 = ObfuscationConfig.get_preset("trial")
        config2 = ObfuscationConfig.get_preset("TRIAL")
        config3 = ObfuscationConfig.get_preset("Trial")

        # All should return same preset type
        assert config1.level == config2.level == config3.level == "pro"

    def test_get_preset_unknown(self):
        """Test that unknown preset raises ValueError."""
        with pytest.raises(ValueError, match="Unknown preset"):
            ObfuscationConfig.get_preset("unknown_preset")

    def test_get_preset_error_message(self):
        """Test that error message lists available presets."""
        with pytest.raises(ValueError) as exc_info:
            ObfuscationConfig.get_preset("invalid")

        error_msg = str(exc_info.value)
        assert "trial" in error_msg
        assert "commercial" in error_msg
        assert "balanced" in error_msg


class TestListPresets:
    """Tests for list_presets method."""

    def test_list_presets(self):
        """Test listing all presets."""
        presets = ObfuscationConfig.list_presets()

        assert isinstance(presets, list)
        assert "trial" in presets
        assert "commercial" in presets
        assert "library" in presets
        assert "maximum" in presets
        assert "safe" in presets
        assert "balanced" in presets
        assert "aggressive" in presets
        assert len(presets) == 7


class TestPresetLimits:
    """Tests for preset limits and restrictions."""

    def test_pro_presets_have_unlimited_files(self):
        """Test that Pro presets have unlimited files."""
        pro_presets = ["trial", "commercial", "library", "maximum"]

        for preset_name in pro_presets:
            config = ObfuscationConfig.get_preset(preset_name)
            assert config.max_files is None, f"{preset_name} should have unlimited files"
            assert config.max_total_loc is None, f"{preset_name} should have unlimited LOC"

    def test_community_presets_have_default_limits(self):
        """Test that Community presets use default limits."""
        community_presets = ["safe", "balanced", "aggressive"]

        for preset_name in community_presets:
            config = ObfuscationConfig.get_preset(preset_name)
            assert config.level == "community", f"{preset_name} should be community level"


class TestPresetExcludeNames:
    """Tests for preset exclude_names configuration."""

    def test_safe_preset_excludes_defaults(self):
        """Test that safe preset uses default exclusions."""
        config = ObfuscationConfig.preset_safe()

        # Should include common exclusions
        assert "print" in config.exclude_names
        assert "__init__" in config.exclude_names

    def test_aggressive_preset_minimal_exclusions(self):
        """Test that aggressive preset has minimal exclusions."""
        config = ObfuscationConfig.preset_aggressive()

        # Should only have essential magic methods
        assert "__init__" in config.exclude_names
        assert "__main__" in config.exclude_names
        # Should NOT have common function names
        assert "print" not in config.exclude_names


# Run pytest if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
