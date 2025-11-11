"""
Base plugin interface for extending pyobfus with Pro features.

Defines the interface that all Pro plugins must implement.
"""

import ast
from abc import ABC, abstractmethod

from pyobfus.config import ObfuscationConfig
from pyobfus.core.transformer import BaseTransformer


class BasePlugin(BaseTransformer, ABC):
    """
    Abstract base class for pyobfus plugins.

    Pro features should extend this class and implement
    the required methods.
    """

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the plugin name.

        Returns:
            str: Plugin name (e.g., "AES String Encryption")
        """
        pass

    @abstractmethod
    def get_version(self) -> str:
        """
        Get the plugin version.

        Returns:
            str: Version string (e.g., "1.0.0")
        """
        pass

    @abstractmethod
    def is_pro_feature(self) -> bool:
        """
        Check if this is a Pro-only feature.

        Returns:
            bool: True if Pro feature, False if Community
        """
        pass

    @abstractmethod
    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform the AST with the plugin's functionality.

        Args:
            tree: AST module to transform

        Returns:
            ast.Module: Transformed AST
        """
        pass

    def validate_license(self) -> bool:
        """
        Validate Pro license.

        Returns:
            bool: True if license is valid (override in Pro plugins)
        """
        # Community edition always returns True
        # Pro plugins should override this
        return True

    def get_description(self) -> str:
        """
        Get plugin description.

        Returns:
            str: Human-readable description
        """
        return f"{self.get_name()} v{self.get_version()}"


# Example plugin structure (not implemented, just for documentation)
class ExampleProPlugin(BasePlugin):
    """
    Example Pro plugin structure.

    This is NOT implemented - just shows the interface.
    """

    def __init__(self, config: ObfuscationConfig):
        super().__init__(config)

    def get_name(self) -> str:
        return "Example Pro Feature"

    def get_version(self) -> str:
        return "1.0.0"

    def is_pro_feature(self) -> bool:
        return True

    def transform(self, tree: ast.Module) -> ast.Module:
        # Pro transformation logic here
        return tree
