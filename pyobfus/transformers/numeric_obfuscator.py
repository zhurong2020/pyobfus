"""
Numeric / Constant Obfuscation Transformer (Community Edition)

Replaces numeric literals with value-preserving opaque expressions so the
original constants are not visible in the shipped source.

Examples:
    Original: timeout = 42
    Obfuscated: timeout = (1719105443 ^ 1719105417)   # both eval to 42

    Original: ratio = 3.14
    Obfuscated: ratio = float.fromhex('0x1.91eb851eb851fp+1')   # exact 3.14

Correctness guarantees:
- Integers use XOR / add / sub identities, which are exact in Python's
  arbitrary-precision integer arithmetic (including negatives and zero).
- Floats use ``float.fromhex(float.hex(x))``, which round-trips every finite
  float and the infinities exactly (no decimal-rounding drift).

Deliberately skipped (returned unchanged):
- Booleans (``True`` / ``False`` are ``int`` subclasses but must stay literal)
- ``None``, strings, bytes, complex numbers
- Any numeric literal inside a ``match`` / ``case`` *pattern*, where Python
  requires a literal and rejects a computed expression.

Masks are drawn from ``secrets`` (CSPRNG) rather than ``random`` to stay
consistent with the project's security-tool baseline.
"""

import ast
import secrets
from typing import Dict, Optional, Set, cast

from pyobfus.config import ObfuscationConfig
from pyobfus.core.analyzer import SymbolAnalyzer
from pyobfus.core.transformer import BaseTransformer

# Mask magnitude for integer obfuscation. 32-bit keeps the emitted constants
# opaque without exploding source size on large modules.
_MASK_BITS = 32
_MASK_RANGE = 1 << _MASK_BITS


class NumericObfuscator(BaseTransformer):
    """
    Obfuscates integer and float literals into equivalent opaque expressions.

    Features:
    - Integer literals -> random XOR / add / sub identity (exact)
    - Float literals -> ``float.fromhex(...)`` (exact round-trip)
    - Skips booleans, None, strings, bytes, complex
    - Skips literals inside match/case patterns (must remain literal)
    - No external dependencies; emitted code uses only builtins
    """

    def __init__(self, config: ObfuscationConfig, analyzer: Optional[SymbolAnalyzer] = None):
        """
        Initialize numeric obfuscator.

        Args:
            config: Obfuscation configuration
            analyzer: Symbol analyzer (optional, unused — kept for interface parity)
        """
        super().__init__(config, analyzer)
        self._numbers_obfuscated = 0
        self._skipped = 0
        # ids of Constant nodes inside match/case patterns (must stay literal)
        self._pattern_const_ids: Set[int] = set()

    def transform(self, tree: ast.Module) -> ast.Module:
        """
        Transform AST by obfuscating numeric literals.

        Args:
            tree: Input AST

        Returns:
            ast.Module: Transformed AST with obfuscated numbers
        """
        if not self.config.numeric_obfuscation:
            return tree

        self._identify_pattern_constants(tree)
        transformed = cast(ast.Module, self.visit(tree))
        ast.fix_missing_locations(transformed)
        return transformed

    def _identify_pattern_constants(self, tree: ast.Module) -> None:
        """
        Record numeric Constants that live inside a match/case pattern.

        ``case 42:`` requires the literal ``42`` to stay a literal — replacing
        it with ``(a ^ b)`` is a syntax error. We collect those node ids up
        front and skip them in :meth:`visit_Constant`. No-op before Python 3.10
        where ``ast.match_case`` does not exist.

        Args:
            tree: AST tree to scan
        """
        match_case_cls = getattr(ast, "match_case", None)
        if match_case_cls is None:
            return

        for node in ast.walk(tree):
            if isinstance(node, match_case_cls):
                for sub in ast.walk(node.pattern):
                    if isinstance(sub, ast.Constant):
                        self._pattern_const_ids.add(id(sub))

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        """
        Visit a Constant node and obfuscate int/float literals.

        Args:
            node: Constant node

        Returns:
            ast.AST: Original node, or an equivalent opaque expression
        """
        value = node.value

        # bool is a subclass of int — must stay literal (True/False)
        if isinstance(value, bool) or value is None:
            return node

        # Inside a match/case pattern: literal required, leave alone
        if id(node) in self._pattern_const_ids:
            if isinstance(value, (int, float)):
                self._skipped += 1
            return node

        if isinstance(value, int):
            return self._obfuscate_int(value)

        if isinstance(value, float):
            return self._obfuscate_float(value)

        # str, bytes, complex, etc. — not our concern
        return node

    def _obfuscate_int(self, value: int) -> ast.expr:
        """
        Build an opaque expression that evaluates exactly to ``value``.

        Picks one of three integer identities at random per literal:
        - XOR:  (value ^ k) ^ k
        - ADD:  a + (value - a)
        - SUB:  (value + b) - b

        All are exact for Python's arbitrary-precision ints, for any sign.

        Args:
            value: Integer literal value

        Returns:
            ast.expr: BinOp expression equal to ``value``
        """
        strategy = secrets.randbelow(3)

        if strategy == 0:  # XOR
            k = secrets.randbelow(_MASK_RANGE) + 1
            new_node: ast.expr = ast.BinOp(
                left=ast.Constant(value=value ^ k),
                op=ast.BitXor(),
                right=ast.Constant(value=k),
            )
        elif strategy == 1:  # ADD (offset may be negative)
            a = secrets.randbelow(_MASK_RANGE) - (_MASK_RANGE >> 1)
            new_node = ast.BinOp(
                left=ast.Constant(value=a),
                op=ast.Add(),
                right=ast.Constant(value=value - a),
            )
        else:  # SUB
            b = secrets.randbelow(_MASK_RANGE) + 1
            new_node = ast.BinOp(
                left=ast.Constant(value=value + b),
                op=ast.Sub(),
                right=ast.Constant(value=b),
            )

        self._increment_transform_count()
        self._numbers_obfuscated += 1
        return new_node

    def _obfuscate_float(self, value: float) -> ast.expr:
        """
        Build ``float.fromhex('<hex>')`` that reconstructs ``value`` exactly.

        ``float.hex`` / ``float.fromhex`` round-trip every finite float and the
        infinities without decimal-rounding drift, so this is value-preserving
        where a naive ``a + b`` split would not be.

        Args:
            value: Float literal value

        Returns:
            ast.expr: Call expression equal to ``value``
        """
        hex_repr = float.hex(value)
        new_node = ast.Call(
            func=ast.Attribute(
                value=ast.Name(id="float", ctx=ast.Load()),
                attr="fromhex",
                ctx=ast.Load(),
            ),
            args=[ast.Constant(value=hex_repr)],
            keywords=[],
        )
        self._increment_transform_count()
        self._numbers_obfuscated += 1
        return new_node

    def get_statistics(self) -> Dict[str, int]:
        """
        Get obfuscation statistics.

        Returns:
            dict: Statistics about the numeric obfuscation process
        """
        return {
            "numbers_obfuscated": self._numbers_obfuscated,
            "skipped": self._skipped,
            "transformations": self._transformation_count,
        }
