"""
Core obfuscation engine components.

This module contains the fundamental components for parsing,
analyzing, transforming, and generating obfuscated Python code.
"""

from pyobfus.core.parser import ASTParser
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.core.transformer import BaseTransformer

__all__ = [
    "ASTParser",
    "SymbolAnalyzer",
    "CodeGenerator",
    "BaseTransformer",
]
