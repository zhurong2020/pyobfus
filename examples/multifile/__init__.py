"""
Multi-file example package for pyobfus demonstration.

This package shows how pyobfus handles:
- Multiple Python files
- Import statements
- Cross-file references
"""

from .calculator import Calculator
from .utils import format_result

__version__ = "1.0.0"
__all__ = ["Calculator", "format_result"]
