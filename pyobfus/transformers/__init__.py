"""
Community Edition obfuscation transformers.

This module contains the free, open-source obfuscation techniques:
- Name mangling (variable/function renaming)
- Comment and docstring removal
- Simple string encoding (Base64)
- Numeric / constant obfuscation (opaque arithmetic)
- AI artifact stripping (provenance-marker removal)
"""

from pyobfus.transformers.ai_artifact_stripper import AIArtifactStripper
from pyobfus.transformers.name_mangler import NameMangler
from pyobfus.transformers.numeric_obfuscator import NumericObfuscator
from pyobfus.transformers.string_encoder import StringEncoder

__all__ = [
    "AIArtifactStripper",
    "NameMangler",
    "NumericObfuscator",
    "StringEncoder",
]
