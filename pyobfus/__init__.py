"""
pyobfus - Modern Python Code Obfuscator

Enterprise-Grade Python Code Protection at 50% Lower Cost

Born from Medical AI Research, pyobfus provides robust, transparent,
and community-driven code obfuscation for Python 3.8+.
"""

__version__ = "0.1.3"
__author__ = "Rong Zhu"
__license__ = "Apache-2.0"

from pyobfus.core.parser import ASTParser
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.generator import CodeGenerator
from pyobfus.transformers.name_mangler import NameMangler

__all__ = [
    "ASTParser",
    "SymbolAnalyzer",
    "CodeGenerator",
    "NameMangler",
    "__version__",
]
