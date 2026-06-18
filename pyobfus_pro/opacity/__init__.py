"""Selective Opacity (P2-1) -- main claim core.

Public API:

- ``opacity(layer)`` -- source-side decorator. No-op outside the build pass.
- ``Layer`` -- enum of the 4 layers (transparent / ai_readable / obfuscated / encrypted).
- ``OpacityConfig`` -- parsed opacity.toml + default-layer carrier.
- ``OpacityConfigError`` -- raised on unknown layer / malformed TOML / conflicting rules.
- ``Resolver`` -- decorator > config > default precedence resolver.
- ``LAYER_SPECS`` -- frozen mapping from Layer to its pass-selection LayerSpec.

Build-pass transformer and L3 runtime materialization are deferred to W3-W4.
See ../../docs/P2-1_DESIGN.md.
"""

from pyobfus_pro.opacity.config import (
    OpacityConfig,
    OpacityConfigError,
    OpacityRule,
)
from pyobfus_pro.opacity.layers import LAYER_SPECS, Layer, LayerSpec
from pyobfus_pro.opacity.patterns import Resolver

_VALID_LAYER_VALUES = frozenset(layer.value for layer in Layer)


def opacity(layer):
    """Marker decorator declaring the protection layer of a function or class.

    Accepts either a ``Layer`` enum member or its string name (``"transparent"``,
    ``"ai_readable"``, ``"obfuscated"``, ``"encrypted"``).

    Outside the build pass this returns the target unchanged so dev/test against
    unobfuscated source is unaffected. The build pass strips the decorator and
    routes the target through the assigned layer's pass subset.

    Patent-gated. See PATENT_NOTES.md and docs/P2-1_DESIGN.md.
    """
    if isinstance(layer, Layer):
        layer_value = layer.value
    elif isinstance(layer, str):
        if layer not in _VALID_LAYER_VALUES:
            raise OpacityConfigError(
                f"Unknown layer: {layer!r}. Valid: {sorted(_VALID_LAYER_VALUES)}"
            )
        layer_value = layer
    else:
        raise TypeError(f"opacity() layer must be Layer or str, got {type(layer).__name__}")

    def _wrap(target):
        target.__pyobfus_opacity_layer__ = layer_value
        return target

    return _wrap


__all__ = [
    "LAYER_SPECS",
    "Layer",
    "LayerSpec",
    "OpacityConfig",
    "OpacityConfigError",
    "OpacityRule",
    "Resolver",
    "opacity",
]
