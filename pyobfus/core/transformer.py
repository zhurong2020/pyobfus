"""
Base transformer class for AST transformations.

Provides the foundation for all obfuscation transformers.
"""

import ast
from abc import ABC, abstractmethod
from typing import List, Optional

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.exceptions import TransformError


class BaseTransformer(ast.NodeTransformer, ABC):
    """
    Abstract base class for all AST transformers.

    Subclasses implement specific obfuscation techniques
    (name mangling, string encoding, etc.).
    """

    def __init__(self, config: ObfuscationConfig, analyzer: Optional[SymbolAnalyzer] = None):
        """
        Initialize transformer.

        Args:
            config: Obfuscation configuration
            analyzer: Optional symbol analyzer (pre-analyzed symbols)
        """
        self.config = config
        self.analyzer = analyzer
        self._transformation_count = 0

    @abstractmethod
    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform an AST module.

        Args:
            tree: AST module to transform

        Returns:
            ast.Module: Transformed AST

        Raises:
            TransformError: If transformation fails
        """
        pass

    def get_transformation_count(self) -> int:
        """
        Get the number of transformations applied.

        Returns:
            int: Number of nodes transformed
        """
        return self._transformation_count

    def _increment_transform_count(self) -> None:
        """Increment transformation counter."""
        self._transformation_count += 1

    def _should_transform_name(self, name: str) -> bool:
        """
        Check if a name should be transformed.

        Args:
            name: Name to check

        Returns:
            bool: True if name should be transformed
        """
        # Check config exclusions
        if self.config.should_exclude_name(name):
            return False

        # Check analyzer if available
        if self.analyzer:
            return name in self.analyzer.obfuscatable_names

        # Default: transform if not excluded
        return True

    def _validate_tree(self, tree: ast.Module) -> None:
        """
        Validate transformed AST.

        Args:
            tree: AST to validate

        Raises:
            TransformError: If AST is invalid
        """
        try:
            # Try to compile to verify validity
            compile(tree, "<ast>", "exec")
        except Exception as e:
            raise TransformError(f"Transformed AST is invalid: {e}") from e


class CompositeTransformer(BaseTransformer):
    """
    Combines multiple transformers into a pipeline.

    Applies transformers sequentially to an AST.
    """

    def __init__(
        self,
        config: ObfuscationConfig,
        transformers: List[BaseTransformer],
        analyzer: Optional[SymbolAnalyzer] = None,
    ):
        """
        Initialize composite transformer.

        Args:
            config: Obfuscation configuration
            transformers: List of transformers to apply
            analyzer: Optional symbol analyzer
        """
        super().__init__(config, analyzer)
        self.transformers = transformers

    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Apply all transformers sequentially.

        Args:
            tree: AST module to transform

        Returns:
            ast.Module: Transformed AST
        """
        current_tree = tree

        for transformer in self.transformers:
            try:
                current_tree = transformer.transform(current_tree)
                self._transformation_count += transformer.get_transformation_count()
            except TransformError:
                raise
            except Exception as e:
                raise TransformError(
                    f"Transformer {transformer.__class__.__name__} failed: {e}"
                ) from e

        # Fix missing locations after transformations
        ast.fix_missing_locations(current_tree)

        return current_tree
