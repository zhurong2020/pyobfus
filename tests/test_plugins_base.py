"""Tests for plugin base classes."""

import ast
import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.plugins.base import BasePlugin, ExampleProPlugin


class TestExampleProPlugin:
    def test_creation(self):
        config = ObfuscationConfig()
        plugin = ExampleProPlugin(config)
        assert plugin is not None

    def test_get_name(self):
        config = ObfuscationConfig()
        plugin = ExampleProPlugin(config)
        assert plugin.get_name() == "Example Pro Feature"

    def test_get_version(self):
        config = ObfuscationConfig()
        plugin = ExampleProPlugin(config)
        assert plugin.get_version() == "1.0.0"

    def test_is_pro_feature(self):
        config = ObfuscationConfig()
        plugin = ExampleProPlugin(config)
        assert plugin.is_pro_feature() is True

    def test_transform_returns_tree(self):
        config = ObfuscationConfig()
        plugin = ExampleProPlugin(config)
        tree = ast.parse("x = 1")
        result = plugin.transform(tree)
        assert result is tree

    def test_validate_license(self):
        config = ObfuscationConfig()
        plugin = ExampleProPlugin(config)
        assert plugin.validate_license() is True

    def test_get_description(self):
        config = ObfuscationConfig()
        plugin = ExampleProPlugin(config)
        desc = plugin.get_description()
        assert "Example Pro Feature" in desc
        assert "1.0.0" in desc


class TestBasePluginIsAbstract:
    def test_cannot_instantiate_base_plugin(self):
        with pytest.raises(TypeError):
            BasePlugin(ObfuscationConfig())
