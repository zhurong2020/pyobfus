"""
Community Edition obfuscation transformers.

This module contains the free, open-source obfuscation techniques:
- Name mangling (variable/function renaming)
- Comment and docstring removal
- Simple string encoding
"""

from pyobfus.transformers.name_mangler import NameMangler

__all__ = [
    "NameMangler",
]
