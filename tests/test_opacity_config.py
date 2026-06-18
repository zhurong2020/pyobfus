"""Tests for P2-1 Selective Opacity config + matcher + resolver.

Build-pass transformer and L3 runtime materialization land in W3-W4; their
tests are in ``test_opacity_transformer.py`` / ``test_opacity_runtime.py``
which don't exist yet. This file covers only the declarative-config + glob
+ precedence-resolver surface.
"""

from __future__ import annotations

import pytest

from pyobfus_pro import (
    LAYER_SPECS,
    Layer,
    OpacityConfig,
    OpacityConfigError,
    OpacityRule,
    Resolver,
    opacity,
)

# ---------------------------------------------------------------------------
# Layer enum
# ---------------------------------------------------------------------------


class TestLayerEnum:
    def test_layer_from_string_canonical_names(self):
        assert Layer.from_string("transparent") is Layer.TRANSPARENT
        assert Layer.from_string("ai_readable") is Layer.AI_READABLE
        assert Layer.from_string("obfuscated") is Layer.OBFUSCATED
        assert Layer.from_string("encrypted") is Layer.ENCRYPTED

    def test_layer_from_string_rejects_unknown(self):
        with pytest.raises(OpacityConfigError) as excinfo:
            Layer.from_string("ultra_secret")
        assert "ultra_secret" in str(excinfo.value)
        assert "transparent" in str(excinfo.value)

    def test_layer_ordering_reflects_strength(self):
        assert Layer.TRANSPARENT.order == 0
        assert Layer.ENCRYPTED.order == 3
        assert Layer.ENCRYPTED.is_at_least(Layer.OBFUSCATED)
        assert Layer.OBFUSCATED.is_at_least(Layer.AI_READABLE)
        assert not Layer.AI_READABLE.is_at_least(Layer.OBFUSCATED)


# ---------------------------------------------------------------------------
# Layer pass-selection matrix
# ---------------------------------------------------------------------------


class TestLayerSpecs:
    def test_each_layer_has_a_spec(self):
        for layer in Layer:
            assert layer in LAYER_SPECS
            assert LAYER_SPECS[layer].layer is layer

    def test_passes_are_strictly_additive_across_lattice(self):
        """Each higher layer turns on at least every flag the lower had.

        This is the lattice nesting property the patent main claim relies on.
        """
        flags = (
            "rename_locals",
            "rename_publics",
            "inject_dead_code",
            "flatten_control_flow",
            "encrypt_strings",
            "marshal_encrypt_code",
        )
        ordered = [
            Layer.TRANSPARENT,
            Layer.AI_READABLE,
            Layer.OBFUSCATED,
            Layer.ENCRYPTED,
        ]
        for prev, nxt in zip(ordered, ordered[1:]):
            for flag in flags:
                lower = getattr(LAYER_SPECS[prev], flag)
                higher = getattr(LAYER_SPECS[nxt], flag)
                assert higher >= lower, (
                    f"Layer {nxt.value}.{flag}={higher} must be >= "
                    f"{prev.value}.{flag}={lower} (lattice nesting)"
                )

    def test_l3_seals_against_ciphertext(self):
        assert LAYER_SPECS[Layer.ENCRYPTED].seal_target == "ciphertext"
        assert LAYER_SPECS[Layer.OBFUSCATED].seal_target == "plaintext"

    def test_layer_spec_rejects_invalid_seal_target(self):
        from pyobfus_pro.opacity.layers import LayerSpec

        with pytest.raises(ValueError, match="seal_target"):
            LayerSpec(
                layer=Layer.OBFUSCATED,
                rename_locals=False,
                rename_publics=False,
                inject_dead_code=False,
                flatten_control_flow=False,
                encrypt_strings=False,
                marshal_encrypt_code=False,
                seal_target="signed",
                materialization="function_body",
            )


# ---------------------------------------------------------------------------
# Config parsing
# ---------------------------------------------------------------------------


class TestConfigParsing:
    def test_minimal_config_uses_default(self):
        cfg = OpacityConfig.from_toml(b"")
        assert cfg.default_layer is Layer.OBFUSCATED
        assert cfg.rules == ()

    def test_default_layer_only(self):
        cfg = OpacityConfig.from_toml(b'default_layer = "ai_readable"\n')
        assert cfg.default_layer is Layer.AI_READABLE
        assert cfg.rules == ()

    def test_config_with_rules_parses(self):
        toml_src = b"""
default_layer = "obfuscated"

[[rules]]
pattern = "myapp.api.*"
layer = "transparent"

[[rules]]
pattern = "myapp.crypto.*"
layer = "encrypted"
"""
        cfg = OpacityConfig.from_toml(toml_src)
        assert cfg.default_layer is Layer.OBFUSCATED
        assert len(cfg.rules) == 2
        assert cfg.rules[0] == OpacityRule(pattern="myapp.api.*", layer=Layer.TRANSPARENT)
        assert cfg.rules[1] == OpacityRule(pattern="myapp.crypto.*", layer=Layer.ENCRYPTED)

    def test_invalid_default_layer_raises(self):
        with pytest.raises(OpacityConfigError, match="ultra_secret"):
            OpacityConfig.from_toml(b'default_layer = "ultra_secret"\n')

    def test_invalid_rule_layer_raises(self):
        toml_src = b"""
[[rules]]
pattern = "x.*"
layer = "transmogrified"
"""
        with pytest.raises(OpacityConfigError, match="transmogrified"):
            OpacityConfig.from_toml(toml_src)

    def test_empty_pattern_raises(self):
        toml_src = b"""
[[rules]]
pattern = ""
layer = "transparent"
"""
        with pytest.raises(OpacityConfigError, match="non-empty"):
            OpacityConfig.from_toml(toml_src)

    def test_malformed_toml_raises(self):
        # tomllib (3.11+) or tomli (3.9 / 3.10 fallback) raises its own error
        # on syntax; we don't promise to wrap it, only to propagate something
        # the caller can react to. Mirror the production fallback chain in
        # opacity/config.py so the test runs on both 3.10 and 3.11+.
        try:
            import tomllib  # type: ignore[import-not-found,unused-ignore]
        except ModuleNotFoundError:  # pragma: no cover -- py3.10 fallback
            import tomli as tomllib  # type: ignore[import-not-found,no-redef,unused-ignore]

        with pytest.raises((OpacityConfigError, tomllib.TOMLDecodeError)):
            OpacityConfig.from_toml(b"this is = not [valid toml")

    def test_config_is_frozen(self):
        cfg = OpacityConfig()
        with pytest.raises(Exception):  # FrozenInstanceError
            cfg.default_layer = Layer.TRANSPARENT  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Pattern matching + resolver precedence
# ---------------------------------------------------------------------------


class TestResolver:
    def test_default_when_no_rules(self):
        cfg = OpacityConfig(default_layer=Layer.AI_READABLE)
        resolver = Resolver(cfg)
        assert resolver.resolve("any.qualname") is Layer.AI_READABLE

    def test_exact_match(self):
        cfg = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="pkg.mod.func", layer=Layer.ENCRYPTED),),
        )
        resolver = Resolver(cfg)
        assert resolver.resolve("pkg.mod.func") is Layer.ENCRYPTED
        assert resolver.resolve("pkg.mod.other") is Layer.OBFUSCATED

    def test_glob_prefix_match(self):
        cfg = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="pkg.crypto.*", layer=Layer.ENCRYPTED),),
        )
        resolver = Resolver(cfg)
        assert resolver.resolve("pkg.crypto.aes_helper") is Layer.ENCRYPTED
        assert resolver.resolve("pkg.crypto.kdf") is Layer.ENCRYPTED
        assert resolver.resolve("pkg.api.login") is Layer.OBFUSCATED

    def test_first_match_wins(self):
        # Two overlapping rules, declaration order determines which wins.
        cfg = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(
                OpacityRule(pattern="pkg.*", layer=Layer.AI_READABLE),
                OpacityRule(pattern="pkg.crypto.*", layer=Layer.ENCRYPTED),
            ),
        )
        resolver = Resolver(cfg)
        # First rule "pkg.*" matches everything, so even pkg.crypto.aes goes
        # to AI_READABLE despite the more-specific later rule. Users avoid
        # this by ordering specific-first.
        assert resolver.resolve("pkg.crypto.aes") is Layer.AI_READABLE

    def test_decorator_overrides_config(self):
        cfg = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="pkg.*", layer=Layer.AI_READABLE),),
        )
        resolver = Resolver(cfg)
        assert resolver.resolve("pkg.x", decorator_layer=Layer.ENCRYPTED) is Layer.ENCRYPTED

    def test_check_for_conflicts_reports_overlap(self):
        cfg = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(
                OpacityRule(pattern="pkg.*", layer=Layer.AI_READABLE),
                OpacityRule(pattern="pkg.crypto.*", layer=Layer.ENCRYPTED),
            ),
        )
        resolver = Resolver(cfg)
        conflicts = resolver.check_for_conflicts(["pkg.api.x", "pkg.crypto.aes", "pkg.utils.parse"])
        # pkg.crypto.aes matches both rules; pkg.api.x and pkg.utils.parse
        # only match the first.
        assert len(conflicts) == 1
        qualname, matching = conflicts[0]
        assert qualname == "pkg.crypto.aes"
        assert len(matching) == 2


# ---------------------------------------------------------------------------
# Assignment hash determinism (P2-7 watermark seed contract)
# ---------------------------------------------------------------------------


class TestAssignmentHash:
    def test_assignment_hash_is_deterministic(self):
        cfg = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(
                OpacityRule(pattern="pkg.crypto.*", layer=Layer.ENCRYPTED),
                OpacityRule(pattern="pkg.api.*", layer=Layer.TRANSPARENT),
            ),
        )
        names = ["pkg.api.login", "pkg.crypto.aes", "pkg.helpers.x"]
        h1 = cfg.assignment_hash(names)
        h2 = cfg.assignment_hash(reversed(names))
        assert h1 == h2
        assert len(h1) == 32  # sha256 digest size

    def test_assignment_hash_changes_with_layer_assignment(self):
        cfg_a = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="pkg.x", layer=Layer.ENCRYPTED),),
        )
        cfg_b = OpacityConfig(
            default_layer=Layer.OBFUSCATED,
            rules=(OpacityRule(pattern="pkg.x", layer=Layer.AI_READABLE),),
        )
        assert cfg_a.assignment_hash(["pkg.x"]) != cfg_b.assignment_hash(["pkg.x"])


# ---------------------------------------------------------------------------
# Decorator surface (identity outside build pass)
# ---------------------------------------------------------------------------


class TestOpacityDecorator:
    def test_decorator_returns_callable_intact(self):
        @opacity("encrypted")
        def fn(x):
            return x + 1

        assert fn(2) == 3
        assert fn.__pyobfus_opacity_layer__ == "encrypted"

    def test_decorator_accepts_layer_enum(self):
        @opacity(Layer.AI_READABLE)
        def fn():
            return 42

        assert fn() == 42
        assert fn.__pyobfus_opacity_layer__ == "ai_readable"

    def test_decorator_rejects_unknown_layer_string(self):
        with pytest.raises(OpacityConfigError, match="ultra_secret"):
            opacity("ultra_secret")

    def test_decorator_rejects_non_string_non_enum(self):
        with pytest.raises(TypeError, match="Layer or str"):
            opacity(3)
