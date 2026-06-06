"""
Tests for the Community numeric / constant obfuscation transformer.

The non-negotiable property is value-preserving round-trip: obfuscated numeric
literals must evaluate to *exactly* the original value. Tests compile and exec
the transformed AST directly (no unparse step), so they run identically on
Python 3.8-3.14.
"""

import ast
import math
import sys

import pytest

from pyobfus.config import ObfuscationConfig
from pyobfus.transformers.numeric_obfuscator import NumericObfuscator


def _obfuscate(source: str, enabled: bool = True):
    """Transform source, return (namespace_after_exec, transformer)."""
    config = ObfuscationConfig.community_edition()
    config.numeric_obfuscation = enabled
    tree = ast.parse(source)
    transformer = NumericObfuscator(config)
    new_tree = transformer.transform(tree)
    code = compile(new_tree, "<obf>", "exec")
    namespace: dict = {}
    exec(code, namespace)  # noqa: S102 - executing our own transformed AST in tests
    return namespace, transformer


# --------------------------------------------------------------------------- #
# Integer round-trip
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "value",
    [0, 1, -1, 42, -42, 255, 1000000, -1000000, 2**63, -(2**63), 2**100, 7, 13],
)
def test_int_round_trip(value):
    """Every integer literal must evaluate back to itself exactly."""
    ns, _ = _obfuscate(f"x = {value}")
    assert ns["x"] == value
    assert type(ns["x"]) is int


def test_int_literal_is_replaced_by_expression():
    """The standalone int Constant should become a compound expression."""
    config = ObfuscationConfig.community_edition()
    config.numeric_obfuscation = True
    tree = ast.parse("x = 42")
    NumericObfuscator(config).transform(tree)
    assign = tree.body[0]
    assert isinstance(assign, ast.Assign)
    # No longer a bare literal
    assert not isinstance(assign.value, ast.Constant)
    assert isinstance(assign.value, (ast.BinOp, ast.Call))


def test_many_int_strategies_all_correct():
    """Run enough literals that all three strategies (xor/add/sub) get exercised."""
    source = "\n".join(f"v{i} = {i * 37 - 500}" for i in range(60))
    ns, transformer = _obfuscate(source)
    for i in range(60):
        assert ns[f"v{i}"] == i * 37 - 500
    assert transformer.get_statistics()["numbers_obfuscated"] == 60


# --------------------------------------------------------------------------- #
# Float round-trip (exactness matters: 0.1 + 0.2 != 0.3)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "value",
    [3.14, 0.1, 0.2, 0.3, -2.5, 0.0, 1e10, 1e-10, 2.0, -0.5, 123456.789],
)
def test_float_round_trip_exact(value):
    """Floats must round-trip with bit-for-bit exactness."""
    ns, _ = _obfuscate(f"x = {value!r}")
    assert ns["x"] == value
    assert type(ns["x"]) is float


def test_float_infinity_round_trip():
    """A literal that overflows to inf must stay inf."""
    ns, _ = _obfuscate("x = 1e400")
    assert ns["x"] == math.inf


def test_negative_zero_sign_preserved():
    """-0.0 must keep its sign bit (float.fromhex preserves it)."""
    ns, _ = _obfuscate("x = -0.0")
    assert math.copysign(1.0, ns["x"]) == -1.0


# --------------------------------------------------------------------------- #
# Things that must be left alone
# --------------------------------------------------------------------------- #


def test_booleans_not_obfuscated():
    """True/False are int subclasses but must remain literal."""
    ns, transformer = _obfuscate("a = True\nb = False")
    assert ns["a"] is True
    assert ns["b"] is False
    assert transformer.get_statistics()["numbers_obfuscated"] == 0


def test_none_and_strings_untouched():
    ns, transformer = _obfuscate("a = None\nb = 'hello'\nc = b'bytes'")
    assert ns["a"] is None
    assert ns["b"] == "hello"
    assert ns["c"] == b"bytes"
    assert transformer.get_statistics()["numbers_obfuscated"] == 0


def test_complex_numbers_untouched():
    """Complex literals are out of scope for v1; must pass through unchanged."""
    ns, transformer = _obfuscate("x = 1j\ny = 2 + 3j")
    assert ns["x"] == 1j
    # the real/imag integer parts in `2 + 3j` ARE obfuscated; the result holds
    assert ns["y"] == 2 + 3j


def test_disabled_by_default_is_noop():
    """With the flag off, the AST must be untouched."""
    ns, transformer = _obfuscate("x = 42\ny = 3.14", enabled=False)
    assert ns["x"] == 42
    assert ns["y"] == 3.14
    assert transformer.get_statistics()["numbers_obfuscated"] == 0


# --------------------------------------------------------------------------- #
# Semantic preservation in real-ish code
# --------------------------------------------------------------------------- #


def test_arithmetic_expression_preserved():
    ns, _ = _obfuscate(
        "def calc():\n"
        "    total = 0\n"
        "    for i in range(10):\n"
        "        total += i * 2 + 1\n"
        "    return total\n"
        "result = calc()"
    )
    assert ns["result"] == sum(i * 2 + 1 for i in range(10))


def test_subscript_and_slice_preserved():
    ns, _ = _obfuscate("data = [10, 20, 30, 40, 50]\npart = data[1:4]\nitem = data[2]")
    assert ns["part"] == [20, 30, 40]
    assert ns["item"] == 30


def test_default_argument_values_preserved():
    ns, _ = _obfuscate("def f(a, b=5, c=2.5):\n    return a + b + c\nout = f(1)")
    assert ns["out"] == 1 + 5 + 2.5


# --------------------------------------------------------------------------- #
# match/case patterns must NOT be turned into expressions (3.10+)
# --------------------------------------------------------------------------- #


@pytest.mark.skipif(sys.version_info < (3, 10), reason="match/case is Python 3.10+")
def test_match_case_pattern_literal_preserved():
    source = (
        "def classify(n):\n"
        "    match n:\n"
        "        case 0:\n"
        "            return 'zero'\n"
        "        case 42:\n"
        "            return 'answer'\n"
        "        case _:\n"
        "            return 'other'\n"
        "r0 = classify(0)\n"
        "r42 = classify(42)\n"
        "rx = classify(7)\n"
    )
    ns, _ = _obfuscate(source)
    assert ns["r0"] == "zero"
    assert ns["r42"] == "answer"
    assert ns["rx"] == "other"


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def test_statistics_shape():
    _, transformer = _obfuscate("x = 1\ny = 2\nz = 3.0")
    stats = transformer.get_statistics()
    assert stats["numbers_obfuscated"] == 3
    assert stats["transformations"] == 3
    assert "skipped" in stats
