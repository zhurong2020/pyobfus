"""
Community Edition obfuscation transformers.

This module contains the free, open-source obfuscation techniques:
- Name mangling (variable/function renaming)
- Comment and docstring removal
- Simple string encoding (Base64)
"""

from pyobfus.transformers.name_mangler import NameMangler
from pyobfus.transformers.string_encoder import StringEncoder

__all__ = [
    "NameMangler",
    "StringEncoder",
]
