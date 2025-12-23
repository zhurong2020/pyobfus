"""
Dead Code Injection module for pyobfus Pro.

This module provides dead code injection to increase code complexity
and hinder reverse engineering attempts.
"""

from .injector import DeadCodeInjector, DCIConfig

__all__ = ["DeadCodeInjector", "DCIConfig"]
