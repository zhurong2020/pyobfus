"""Runtime-side tests for @seal_code.

Exercises the _verify_seal decorator independent of the build-time obfuscator
pass. Build-pass tests will be added once the AST transformer lands (W1).
"""

import pytest

from pyobfus_pro import IntegrityError, seal_code
from pyobfus_pro.runtime.seal import _compute_seal, _verify_seal


class TestSealMarker:
    """The `@seal_code` source-level marker is a no-op outside the build pass."""

    def test_seal_code_is_identity_outside_build(self):
        @seal_code
        def f(x):
            return x * 2

        assert f(3) == 6
        assert f.__name__ == "f"


class TestVerifySealHappyPath:
    def test_correct_hash_passes(self):
        def target(x):
            return x + 1

        expected = _compute_seal(target)
        wrapped = _verify_seal(expected)(target)

        assert wrapped(10) == 11

    def test_multiple_calls_succeed(self):
        def target(x):
            return x * 2

        expected = _compute_seal(target)
        wrapped = _verify_seal(expected)(target)

        results = [wrapped(i) for i in range(5)]
        assert results == [0, 2, 4, 6, 8]


class TestVerifySealCaching:
    """After the first successful verify, subsequent calls do not re-hash."""

    def test_compute_seal_called_only_once_across_many_invocations(self, monkeypatch):
        import pyobfus_pro.runtime.seal as seal_mod

        call_count = {"n": 0}
        original = seal_mod._compute_seal

        def counting(func):
            call_count["n"] += 1
            return original(func)

        def target(x):
            return x

        # Compute expected with the original (uncounted) so the prep step
        # doesn't pollute the count.
        expected = original(target)

        monkeypatch.setattr(seal_mod, "_compute_seal", counting)
        wrapped = seal_mod._verify_seal(expected)(target)

        wrapped(1)
        wrapped(2)
        wrapped(3)

        assert call_count["n"] == 1, (
            f"Expected exactly 1 hash computation across 3 calls, " f"got {call_count['n']}"
        )


class TestVerifySealTamperDetection:
    def test_wrong_hash_raises(self):
        def target(x):
            return x * 3

        wrong_hash = b"\x00" * 32
        wrapped = _verify_seal(wrong_hash)(target)

        with pytest.raises(IntegrityError, match="Integrity check failed"):
            wrapped(5)

    def test_error_includes_function_qualname(self):
        def my_protected_func(x):
            return x

        wrong_hash = b"\x00" * 32
        wrapped = _verify_seal(wrong_hash)(my_protected_func)

        with pytest.raises(IntegrityError, match="my_protected_func"):
            wrapped(0)


class TestAttributeTamperResistance:
    """Pre-setting any attribute on the target should NOT bypass verification.

    State lives in a closure cell, not as an attribute on the wrapped or
    wrapper functions, so attribute-tamper attacks have no surface to grip.
    """

    def test_setting_arbitrary_attrs_on_target_does_not_bypass(self):
        def target(x):
            return x

        # Attacker pre-sets attributes on the function they control, guessing
        # at common cache-flag names:
        for name in [
            "_verified",
            "_seal_verified",
            "_pyobfus_pro_seal_verified",
            "_integrity_ok",
            "__cached__",
        ]:
            target.__dict__[name] = True

        wrong_hash = b"\x00" * 32
        wrapped = _verify_seal(wrong_hash)(target)

        with pytest.raises(IntegrityError):
            wrapped(0)


class TestFunctoolsWraps:
    def test_wrapped_preserves_metadata(self):
        def my_function(x):
            """Docstring for my_function."""
            return x

        expected = _compute_seal(my_function)
        wrapped = _verify_seal(expected)(my_function)

        assert wrapped.__name__ == "my_function"
        assert wrapped.__doc__ == "Docstring for my_function."


class TestMarshalBasedHashing:
    """The seal must catch tampering that only swaps constants.

    Two functions like ``return x * 2`` and ``return x * 999`` share the
    SAME ``co_code`` bytecode (constants are stored in ``co_consts`` and
    referenced by index). A seal that hashes only ``co_code`` would miss
    this kind of tampering. The marshal-based hash captures co_consts and
    every other behaviorally-significant field, so swap-only tampering is
    detected.
    """

    def test_constant_only_tampering_is_detected(self):
        def target(x):
            return x * 2

        def evil(x):
            return x * 999  # same shape, only constant differs

        expected = _compute_seal(target)
        target.__code__ = evil.__code__  # tamper before wrapping
        wrapped = _verify_seal(expected)(target)

        with pytest.raises(IntegrityError):
            wrapped(5)

    def test_co_code_alone_would_have_missed_this(self):
        """Sanity check: this documents WHY the seal is marshal-based.

        Both functions have identical ``co_code``; a co_code-only hash would
        falsely match. We assert the bytecode equality here so future readers
        can see the failure mode this design resists.

        Cross-Python-version note: CPython 3.14 introduced an opcode that
        inlines small ints (<= 255) directly into bytecode operands via
        LOAD_SMALL_INT, bypassing co_consts. Two small-int constants like
        ``2`` and ``999`` therefore produce DIFFERENT co_code on 3.14
        (``LOAD_SMALL_INT 2`` vs ``LOAD_CONST 0`` indexing co_consts[0]=999),
        so the original 3.10-3.13 motivating example no longer demonstrates
        the issue on 3.14. Using large ints (> 255) keeps both sides on the
        LOAD_CONST path across all versions, restoring the intended
        demonstration. The seal claim is unaffected -- it always covers BOTH
        cases via the normalized projection.
        """
        big_a = 2**32
        big_b = 2**33

        def f(x):
            return x * big_a

        def g(x):
            return x * big_b

        # Same co_code (LOAD_CONST + the same operand byte index) on every
        # CPython 3.10-3.14 surveyed; only the values stored in co_consts
        # differ. A co_code-only hash would fail to detect this swap.
        assert f.__code__.co_code == g.__code__.co_code
        # But the marshal-based seals differ:
        assert _compute_seal(f) != _compute_seal(g)
