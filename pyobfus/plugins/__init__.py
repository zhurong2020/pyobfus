"""
Plugin system for Pro features.

This module defines the base plugin interface for extending pyobfus
with proprietary obfuscation techniques (Pro Edition).

Pro plugins are NOT included in the open-source repository.
"""

from pyobfus.plugins.base import BasePlugin

__all__ = [
    "BasePlugin",
]
