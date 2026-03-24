"""Tests for BaseTransformer and CompositeTransformer."""

import ast
import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.core.transformer import BaseTransformer, CompositeTransformer
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.exceptions import TransformError


class ConcreteTransformer(BaseTransformer):
    """Minimal concrete implementation for testing."""

    def transform(self, tree: ast.Module) -> ast.Module:
        self._increment_transform_count()
        return tree


class FailingTransformer(BaseTransformer):
    """Transformer that raises an error."""

    def transform(self, tree: ast.Module) -> ast.Module:
        raise ValueError("intentional failure")


class TestBaseTransformer:
    def test_initialization(self):
        config = ObfuscationConfig()
        t = ConcreteTransformer(config)
        assert t.config is config
        assert t.analyzer is None
        assert t.get_transformation_count() == 0

    def test_initialization_with_analyzer(self):
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        t = ConcreteTransformer(config, analyzer)
        assert t.analyzer is analyzer

    def test_transform_increments_count(self):
        config = ObfuscationConfig()
        t = ConcreteTransformer(config)
        tree = ast.parse("x = 1")
        t.transform(tree)
        assert t.get_transformation_count() == 1
        t.transform(tree)
        assert t.get_transformation_count() == 2

    def test_should_transform_name_excluded(self):
        config = ObfuscationConfig()
        t = ConcreteTransformer(config)
        # Magic methods should be excluded
        assert t._should_transform_name("__init__") is False
        # Builtins should be excluded
        assert t._should_transform_name("print") is False

    def test_should_transform_name_normal(self):
        config = ObfuscationConfig()
        t = ConcreteTransformer(config)
        assert t._should_transform_name("my_variable") is True

    def test_should_transform_name_with_analyzer(self):
        config = ObfuscationConfig()
        analyzer = SymbolAnalyzer(config)
        tree = ast.parse("def my_func():\n    pass\n")
        analyzer.analyze(tree)
        t = ConcreteTransformer(config, analyzer)
        assert t._should_transform_name("my_func") is True

    def test_validate_tree_valid(self):
        config = ObfuscationConfig()
        t = ConcreteTransformer(config)
        tree = ast.parse("x = 1")
        ast.fix_missing_locations(tree)
        t._validate_tree(tree)  # should not raise

    def test_validate_tree_invalid(self):
        config = ObfuscationConfig()
        t = ConcreteTransformer(config)
        # Create an invalid AST by setting bad fields
        tree = ast.Module(body=[ast.Expr(value=None)], type_ignores=[])
        with pytest.raises(TransformError):
            t._validate_tree(tree)


class TestCompositeTransformer:
    def test_empty_pipeline(self):
        config = ObfuscationConfig()
        ct = CompositeTransformer(config, [])
        tree = ast.parse("x = 1")
        result = ct.transform(tree)
        assert result is not None

    def test_single_transformer(self):
        config = ObfuscationConfig()
        t1 = ConcreteTransformer(config)
        ct = CompositeTransformer(config, [t1])
        tree = ast.parse("x = 1")
        ct.transform(tree)
        assert ct.get_transformation_count() == 1

    def test_multiple_transformers(self):
        config = ObfuscationConfig()
        t1 = ConcreteTransformer(config)
        t2 = ConcreteTransformer(config)
        ct = CompositeTransformer(config, [t1, t2])
        tree = ast.parse("x = 1")
        ct.transform(tree)
        assert ct.get_transformation_count() == 2

    def test_failing_transformer_raises_transform_error(self):
        config = ObfuscationConfig()
        ft = FailingTransformer(config)
        ct = CompositeTransformer(config, [ft])
        tree = ast.parse("x = 1")
        with pytest.raises(TransformError, match="failed"):
            ct.transform(tree)
