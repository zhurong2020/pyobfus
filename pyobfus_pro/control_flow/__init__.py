"""
Control Flow Flattening module for pyobfus Pro.

This module provides control flow obfuscation by transforming structured
control flow (if/else, loops) into state machine representations.
"""

from .flattener import ControlFlowFlattener
from .state_machine import StateMachine, State

__all__ = ["ControlFlowFlattener", "StateMachine", "State"]
