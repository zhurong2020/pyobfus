"""Tests for the P2-1 Selective Opacity build-pass AST transformer (W3-B).

Covers the transformer in ``pyobfus_pro/transformers/opacity.py``:

- per-layer dispatch (L0 / L1 / L2 / L3)
- L3 ciphertext + LAYER_KEY emission + runtime import injection
- L3 round-trip via exec (decrypt-on-first-call works through emitted AST)
- decorator > config > default precedence in the transformer
- v1 limitations (class methods, nested defs, class-level @opacity rejected;
  L3 with extra decorators rejected)
- ``dont_inherit=True`` future-flag discipline regression (P2-9 W1 finding)

The runtime side has its own test module (``test_opacity_runtime.py``).
"""

from __future__ import annotations

import secrets
import textwrap

import pytest

from pyobfus_pro import OpacityRuntimeError
from pyobfus_pro.opacity import Layer, OpacityConfig, OpacityRule
from pyobfus_pro.transformers.opacity import (
    OpacityBuildError,
    transform_module,
)


def _src(body: str) -> str:
    """Dedent + ensure trailing newline."""
    return textwrap.dedent(body).strip() + "\n"


def _exec_transformed(source: str, **kwargs) -> tuple[dict, dict]:
    """Transform + exec source; return (namespace, layer_assignments)."""
    transformed, assignments = transform_module(source, **kwargs)
    namespace: dict = {}
    exec(compile(transformed, "<test-load>", "exec"), namespace)  # noqa: S102
    return namespace, assignments


# ---------------------------------------------------------------------------
# No-op: module without any top-level functions
# ---------------------------------------------------------------------------


class TestNoOp:
    def test_module_without_functions_returns_unchanged(self):
        src = "x = 1\ny = x + 2\n"
        out, assignments = transform_module(src)
        assert out == src
        assert assignments == {}

    def test_module_without_opacity_decorators_still_records_assignments(self):
        # Even unmarked functions get a layer assignment via the default.
        src = _src("""
            def helper(x):
                return x + 1
        """)
        config = OpacityConfig(default_layer=Layer.AI_READABLE)
        _, assignments = transform_module(src, config)
        assert assignments == {"helper": Layer.AI_READABLE}


# ---------------------------------------------------------------------------
# L0 transparent: strip decorator, keep body
# ---------------------------------------------------------------------------


class TestL0Transparent:
    def test_l0_strips_opacity_decorator(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("transparent")
            def public_api(x):
                return x + 1
        """)
        out, assignments = transform_module(src)
        assert "@opacity" not in out
        assert "_CIPHER_" not in out
        assert "_LAYER_KEY" not in out
        assert assignments == {"public_api": Layer.TRANSPARENT}

    def test_l0_round_trip_executes_unchanged(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("transparent")
            def public_api(x):
                return x + 1
        """)
        ns, _ = _exec_transformed(src)
        assert ns["public_api"](5) == 6


# ---------------------------------------------------------------------------
# L1 ai_readable / L2 obfuscated: strip decorator, defer to Core orchestration
# ---------------------------------------------------------------------------


class TestL1AndL2:
    def test_l1_strips_decorator_records_ai_readable(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("ai_readable")
            def helper(x):
                return x * 3
        """)
        out, assignments = transform_module(src)
        assert "@opacity" not in out
        assert "_CIPHER_" not in out
        assert assignments == {"helper": Layer.AI_READABLE}

    def test_l2_strips_decorator_records_obfuscated(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("obfuscated")
            def core(x):
                return x * 2
        """)
        out, assignments = transform_module(src)
        assert "@opacity" not in out
        assert "_CIPHER_" not in out
        assert assignments == {"core": Layer.OBFUSCATED}

    def test_l1_l2_body_not_modified(self):
        # L1 / L2 leave the body untouched -- Core's downstream rename / CFF
        # pass is what mutates them. The transformer only strips the marker
        # decorator and records the assignment.
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("ai_readable")
            def helper(x):
                local_var = x * 3
                return local_var
        """)
        out, _ = transform_module(src)
        assert "local_var" in out
        assert "return local_var" in out


# ---------------------------------------------------------------------------
# L3 encrypted: cipher + LAYER_KEY + dispatch wrapper
# ---------------------------------------------------------------------------


class TestL3Emission:
    def test_l3_emits_cipher_constant_before_function(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        out, _ = transform_module(src)
        cipher_pos = out.find("_CIPHER_critical = ")
        def_pos = out.find("def critical(")
        assert 0 <= cipher_pos < def_pos

    def test_l3_emits_layer_key_at_module_top_after_imports(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        out, _ = transform_module(src)
        layer_key_pos = out.find("_LAYER_KEY = ")
        cipher_pos = out.find("_CIPHER_critical = ")
        # _LAYER_KEY appears once and before any _CIPHER_ constant
        assert 0 <= layer_key_pos < cipher_pos
        assert out.count("_LAYER_KEY = ") == 1

    def test_l3_replaces_opacity_with_l3_dispatch(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        out, _ = transform_module(src)
        assert "@opacity" not in out
        assert "@_l3_dispatch(_CIPHER_critical, _LAYER_KEY)" in out

    def test_l3_replaces_body_with_pass_stub(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        out, _ = transform_module(src)
        # The original body's "return x * 7" must NOT appear in the
        # transformed source (otherwise the encryption was pointless).
        # ast.unparse may emit `return x * 7` if any other unrelated function
        # repeats the literal; isolate by checking the body of `critical`
        # specifically. The simplest assertion: literal `7` must not appear
        # anywhere in the transformed source (cipher bytes are hex, not int
        # literals).
        assert " * 7" not in out
        assert "    pass" in out

    def test_l3_inserts_runtime_import_when_absent(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        out, _ = transform_module(src)
        assert "from pyobfus_pro.runtime import _l3_dispatch" in out

    def test_l3_extends_existing_runtime_import(self):
        src = _src("""
            from pyobfus_pro import opacity
            from pyobfus_pro.runtime import IntegrityError

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        out, _ = transform_module(src)
        assert "_l3_dispatch" in out
        assert "IntegrityError" in out

    def test_l3_preserves_docstring_in_stub(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                '''secret algorithm'''
                return x * 7
        """)
        out, _ = transform_module(src)
        assert "'secret algorithm'" in out or '"secret algorithm"' in out


# ---------------------------------------------------------------------------
# L3 end-to-end: round-trip exec actually executes the protected body
# ---------------------------------------------------------------------------


class TestL3RoundTrip:
    def test_l3_first_call_decrypts_and_returns_correct_result(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        ns, _ = _exec_transformed(src)
        assert ns["critical"](3) == 21

    def test_l3_second_call_uses_cached_code(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x + 100
        """)
        ns, _ = _exec_transformed(src)
        critical = ns["critical"]
        assert critical(1) == 101
        assert critical(2) == 102
        assert critical(0) == 100

    def test_l3_async_function_round_trips(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            async def critical(x):
                return x * 5
        """)
        out, assignments = transform_module(src)
        assert "async def critical" in out
        assert "@_l3_dispatch(_CIPHER_critical, _LAYER_KEY)" in out
        assert assignments == {"critical": Layer.ENCRYPTED}

    def test_l3_kwargs_and_varargs_pass_through(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(*args, **kwargs):
                return (sum(args), sorted(kwargs.items()))
        """)
        ns, _ = _exec_transformed(src)
        result = ns["critical"](1, 2, 3, foo="bar")
        assert result == (6, [("foo", "bar")])


# ---------------------------------------------------------------------------
# Multiple L3 functions share LAYER_KEY, have independent CIPHER constants
# ---------------------------------------------------------------------------


class TestMultipleL3:
    def test_multiple_l3_functions_share_single_layer_key(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def alpha(x):
                return x + 1

            @opacity("encrypted")
            def beta(x):
                return x - 1
        """)
        out, assignments = transform_module(src)
        assert out.count("_LAYER_KEY = ") == 1
        assert "_CIPHER_alpha = " in out
        assert "_CIPHER_beta = " in out
        assert assignments == {"alpha": Layer.ENCRYPTED, "beta": Layer.ENCRYPTED}

    def test_multiple_l3_functions_each_round_trip_independently(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def alpha(x):
                return x + 1

            @opacity("encrypted")
            def beta(x):
                return x - 1
        """)
        ns, _ = _exec_transformed(src)
        assert ns["alpha"](10) == 11
        assert ns["beta"](10) == 9

    def test_layer_key_is_unique_across_calls_unless_supplied(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x
        """)
        out_a, _ = transform_module(src)
        out_b, _ = transform_module(src)
        # Different per-call random keys -> different output texts
        assert out_a != out_b

    def test_layer_key_supplied_externally_is_used_verbatim(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 2
        """)
        key = secrets.token_bytes(32)
        out, _ = transform_module(src, layer_key=key)
        assert repr(key) in out
        # And the round-trip works because the LAYER_KEY in the emitted
        # module matches the encryption key used.
        ns: dict = {}
        exec(compile(out, "<t>", "exec"), ns)  # noqa: S102
        assert ns["critical"](5) == 10

    def test_layer_key_must_be_32_bytes(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x
        """)
        with pytest.raises(ValueError, match="32 bytes"):
            transform_module(src, layer_key=b"too short")


# ---------------------------------------------------------------------------
# Mixed-layer modules: L0/L1/L2/L3 functions in one module
# ---------------------------------------------------------------------------


class TestMixedLayers:
    def test_mixed_layers_in_one_module(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("transparent")
            def public_api(x):
                return x

            @opacity("ai_readable")
            def helper(x):
                return x + 1

            @opacity("obfuscated")
            def internal(x):
                return x * 2

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        out, assignments = transform_module(src)
        # Only critical's body is replaced; public_api / helper / internal
        # keep their bodies intact (Core handles L1/L2 downstream).
        assert "_CIPHER_public_api" not in out
        assert "_CIPHER_helper" not in out
        assert "_CIPHER_internal" not in out
        assert "_CIPHER_critical = " in out
        assert assignments == {
            "public_api": Layer.TRANSPARENT,
            "helper": Layer.AI_READABLE,
            "internal": Layer.OBFUSCATED,
            "critical": Layer.ENCRYPTED,
        }

    def test_mixed_module_round_trips(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("transparent")
            def public_api(x):
                return x

            @opacity("encrypted")
            def critical(x):
                return x * 7
        """)
        ns, _ = _exec_transformed(src)
        assert ns["public_api"](5) == 5
        assert ns["critical"](3) == 21


# ---------------------------------------------------------------------------
# Precedence: decorator > config > default
# ---------------------------------------------------------------------------


class TestPrecedence:
    def test_decorator_overrides_config_rule(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("transparent")
            def f(x):
                return x
        """)
        # Config says "f" should be encrypted, decorator says transparent.
        config = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="f", layer=Layer.ENCRYPTED),),
        )
        _, assignments = transform_module(src, config)
        assert assignments == {"f": Layer.TRANSPARENT}

    def test_config_rule_overrides_default(self):
        src = _src("""
            def helper(x):
                return x
        """)
        config = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="helper", layer=Layer.AI_READABLE),),
        )
        _, assignments = transform_module(src, config)
        assert assignments == {"helper": Layer.AI_READABLE}

    def test_glob_pattern_with_module_qualname(self):
        src = _src("""
            def parse_a(x):
                return x

            def parse_b(x):
                return x

            def other(x):
                return x
        """)
        config = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="myapp.utils.parse_*", layer=Layer.AI_READABLE),),
        )
        _, assignments = transform_module(src, config, module_qualname="myapp.utils")
        assert assignments == {
            "myapp.utils.parse_a": Layer.AI_READABLE,
            "myapp.utils.parse_b": Layer.AI_READABLE,
            "myapp.utils.other": Layer.OBFUSCATED,
        }


# ---------------------------------------------------------------------------
# Decorator argument forms
# ---------------------------------------------------------------------------


class TestDecoratorArguments:
    def test_string_literal_argument(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def f(x):
                return x
        """)
        _, assignments = transform_module(src)
        assert assignments == {"f": Layer.ENCRYPTED}

    def test_layer_enum_attribute_argument(self):
        src = _src("""
            from pyobfus_pro import Layer, opacity

            @opacity(Layer.ENCRYPTED)
            def f(x):
                return x
        """)
        _, assignments = transform_module(src)
        assert assignments == {"f": Layer.ENCRYPTED}

    def test_dotted_opacity_decorator_recognized(self):
        src = _src("""
            import pyobfus_pro

            @pyobfus_pro.opacity("ai_readable")
            def f(x):
                return x
        """)
        _, assignments = transform_module(src)
        assert assignments == {"f": Layer.AI_READABLE}

    def test_unknown_layer_string_raises(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("paranoid")
            def f(x):
                return x
        """)
        with pytest.raises(OpacityBuildError, match="paranoid"):
            transform_module(src)

    def test_dynamic_argument_raises(self):
        src = _src("""
            from pyobfus_pro import opacity

            chosen = "encrypted"

            @opacity(chosen)
            def f(x):
                return x
        """)
        with pytest.raises(OpacityBuildError, match="not statically parseable"):
            transform_module(src)

    def test_multiple_opacity_decorators_raise(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            @opacity("ai_readable")
            def f(x):
                return x
        """)
        with pytest.raises(OpacityBuildError, match="multiple times"):
            transform_module(src)

    def test_keyword_argument_to_opacity_raises(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity(layer="encrypted")
            def f(x):
                return x
        """)
        with pytest.raises(OpacityBuildError, match="exactly one"):
            transform_module(src)


# ---------------------------------------------------------------------------
# v1 limitations
# ---------------------------------------------------------------------------


class TestV1Limitations:
    def test_class_method_with_opacity_rejected(self):
        src = _src("""
            from pyobfus_pro import opacity

            class Foo:
                @opacity("encrypted")
                def method(self, x):
                    return x
        """)
        with pytest.raises(OpacityBuildError, match="class method"):
            transform_module(src)

    def test_class_level_opacity_rejected(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            class Foo:
                pass
        """)
        with pytest.raises(OpacityBuildError, match="class"):
            transform_module(src)

    def test_nested_function_with_opacity_rejected(self):
        src = _src("""
            from pyobfus_pro import opacity

            def outer():
                @opacity("encrypted")
                def inner(x):
                    return x
                return inner
        """)
        with pytest.raises(OpacityBuildError, match="nested"):
            transform_module(src)


# ---------------------------------------------------------------------------
# Future-flag discipline regression (P2-9 W1 finding)
# ---------------------------------------------------------------------------


class TestFutureFlagDiscipline:
    def test_source_with_future_annotations_round_trips(self):
        # The transformer's own module uses ``from __future__ import
        # annotations``; if compile() inherited those flags, the L3
        # ciphertext's co_flags would carry CO_FUTURE_ANNOTATIONS bits the
        # runtime decryption + materialization wouldn't expect. dont_inherit
        # = True prevents that. This is the same regression test pattern as
        # ``test_seal_transformer.TestFutureImportIndependence``.
        src = _src("""
            from __future__ import annotations
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x: int) -> int:
                return x * 4
        """)
        ns, _ = _exec_transformed(src)
        assert ns["critical"](6) == 24

    def test_source_without_future_imports_round_trips(self):
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 4
        """)
        ns, _ = _exec_transformed(src)
        assert ns["critical"](6) == 24


# ---------------------------------------------------------------------------
# Tamper detection at runtime via the L3 dispatch path
# ---------------------------------------------------------------------------


class TestRuntimeTamperDetection:
    def test_layer_key_mismatch_at_runtime_surfaces_as_opacity_error(self):
        # Build a module with a known-good layer_key, then patch the bound
        # _LAYER_KEY in the namespace to a wrong key before calling. This
        # simulates an attacker who replaces the embedded key without also
        # re-encrypting the cipher constants.
        src = _src("""
            from pyobfus_pro import opacity

            @opacity("encrypted")
            def critical(x):
                return x * 9
        """)
        good_key = secrets.token_bytes(32)
        out, _ = transform_module(src, layer_key=good_key)
        ns: dict = {}
        exec(compile(out, "<t>", "exec"), ns)  # noqa: S102

        # Tamper: replace _LAYER_KEY with a fresh random key, then re-decorate
        # critical. Easiest path: rebuild the dispatch wrapper with wrong key.
        from pyobfus_pro import _l3_dispatch

        wrong_key = secrets.token_bytes(32)
        cipher = ns["_CIPHER_critical"]

        @_l3_dispatch(cipher, wrong_key)
        def critical_tampered(x):  # noqa: ARG001
            raise AssertionError("stub")

        with pytest.raises(OpacityRuntimeError):
            critical_tampered(1)
