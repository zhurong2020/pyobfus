"""Tests for the @seal_code build-pass AST transformer."""

import textwrap

import pytest

from pyobfus_pro import IntegrityError
from pyobfus_pro.transformers.seal import SealBuildError, transform_module


def _exec_transformed(source: str) -> dict:
    """Parse + transform + exec source; return the resulting namespace."""
    transformed = transform_module(source)
    namespace: dict = {}
    exec(compile(transformed, "<test-load>", "exec"), namespace)  # noqa: S102
    return namespace


def _src(body: str) -> str:
    """Dedent + ensure trailing newline."""
    return textwrap.dedent(body).strip() + "\n"


class TestNoOp:
    def test_module_without_seal_code_returns_unchanged(self):
        src = "def f(x):\n    return x + 1\n"
        assert transform_module(src) == src


class TestDecoratorRewrite:
    def test_seal_code_decorator_replaced_with_verify_seal(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        out = transform_module(src)
        assert "@seal_code" not in out
        assert "@_verify_seal(_SEAL_critical)" in out

    def test_seal_constant_emitted_before_function_def(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        out = transform_module(src)
        seal_pos = out.find("_SEAL_critical = ")
        def_pos = out.find("def critical(")
        assert 0 <= seal_pos < def_pos, (
            f"Expected _SEAL_critical before def critical, "
            f"got positions {seal_pos} and {def_pos}"
        )

    def test_runtime_import_added_when_absent(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        out = transform_module(src)
        assert "from pyobfus_pro.runtime import _verify_seal" in out

    def test_runtime_import_extended_when_partial(self):
        src = _src("""
            from pyobfus_pro import seal_code
            from pyobfus_pro.runtime import IntegrityError

            @seal_code
            def critical(x):
                return x * 2
        """)
        out = transform_module(src)
        assert "_verify_seal" in out
        assert "IntegrityError" in out


class TestEndToEndExecution:
    def test_round_trip_succeeds(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        ns = _exec_transformed(src)
        assert ns["critical"](5) == 10

    def test_tampered_code_raises_at_runtime(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        ns = _exec_transformed(src)
        critical = ns["critical"]

        # Tamper before first call: replace the underlying func's __code__
        # via the `__wrapped__` attribute set by functools.wraps.
        def evil(x):
            return x * 999

        critical.__wrapped__.__code__ = evil.__code__

        with pytest.raises(IntegrityError):
            critical(5)

    def test_call_after_successful_first_verify_does_not_re_check(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def critical(x):
                return x * 2
        """)
        ns = _exec_transformed(src)
        critical = ns["critical"]

        # First call locks the verified state
        assert critical(1) == 2

        # Tamper after first call: cached state should bypass re-check
        def evil(x):
            return x * 999

        critical.__wrapped__.__code__ = evil.__code__

        # The wrapper short-circuits, so we still get the (now) evil result
        # without an IntegrityError. This documents the cache semantics.
        assert critical(1) == 999


class TestMultipleFunctions:
    def test_multiple_sealed_functions_each_get_own_seal(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def alpha(x):
                return x + 1

            @seal_code
            def beta(x):
                return x - 1
        """)
        ns = _exec_transformed(src)
        assert ns["alpha"](10) == 11
        assert ns["beta"](10) == 9

    def test_unsealed_functions_unaffected(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def sealed_one(x):
                return x * 2

            def unsealed(x):
                return x * 3
        """)
        out = transform_module(src)
        assert "_SEAL_sealed_one" in out
        assert "_SEAL_unsealed" not in out
        ns = _exec_transformed(src)
        assert ns["sealed_one"](2) == 4
        assert ns["unsealed"](2) == 6


class TestAsyncFunction:
    def test_sealed_async_function_decoration_rewritten(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            async def critical(x):
                return x * 2
        """)
        out = transform_module(src)
        assert "@_verify_seal(_SEAL_critical)" in out
        assert "async def critical" in out


class TestDecoratorRecognition:
    def test_dotted_seal_code_decorator_recognized(self):
        src = _src("""
            import pyobfus_pro

            @pyobfus_pro.seal_code
            def critical(x):
                return x * 2
        """)
        out = transform_module(src)
        assert "_SEAL_critical" in out
        assert "@pyobfus_pro.seal_code" not in out


class TestFutureImportIndependence:
    """The build-time compile must use ``dont_inherit=True`` to avoid leaking
    future-flag bits from the obfuscator's own module into the user's
    compiled code. Without it, the build hash differs from the runtime hash
    by exactly the inherited future-flag bits (e.g. CO_FUTURE_ANNOTATIONS),
    producing false-positive IntegrityError at first call.

    Regression for the W1 finding (2026-05-09).
    """

    def test_source_without_future_imports_round_trips(self):
        src = _src("""
            from pyobfus_pro import seal_code

            @seal_code
            def f(x):
                return x * 2
        """)
        ns = _exec_transformed(src)
        assert ns["f"](5) == 10

    def test_source_with_future_annotations_round_trips(self):
        src = _src("""
            from __future__ import annotations
            from pyobfus_pro import seal_code

            @seal_code
            def f(x: int) -> int:
                return x * 2
        """)
        ns = _exec_transformed(src)
        assert ns["f"](5) == 10


class TestUnsupportedLocations:
    def test_seal_code_in_class_method_rejected(self):
        src = _src("""
            from pyobfus_pro import seal_code

            class Foo:
                @seal_code
                def method(self, x):
                    return x
        """)
        with pytest.raises(SealBuildError, match="not supported"):
            transform_module(src)

    def test_seal_code_in_nested_function_rejected(self):
        src = _src("""
            from pyobfus_pro import seal_code

            def outer():
                @seal_code
                def inner(x):
                    return x
                return inner
        """)
        with pytest.raises(SealBuildError, match="not supported"):
            transform_module(src)
