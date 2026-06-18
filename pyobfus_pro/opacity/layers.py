"""Layer enum + frozen pass-selection matrix for P2-1 Selective Opacity.

The layer lattice is strictly nested: a symbol assigned to layer N receives
every pass that layer N-1 receives, plus more. This nesting property is what
the patent's main combination claim hangs on.

See docs/P2-1_DESIGN.md for the design rationale and PATENT_NOTES.md for the
inventive-step framing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum


class Layer(Enum):
    """Four protection layers, ordered weakest to strongest.

    Members:
        TRANSPARENT  -- no obfuscation; source as-is
        AI_READABLE  -- rename locals + private members only
        OBFUSCATED   -- L1 + Core full pipeline
        ENCRYPTED    -- L2 + per-function AES-256-GCM with lazy materialization
    """

    TRANSPARENT = "transparent"
    AI_READABLE = "ai_readable"
    OBFUSCATED = "obfuscated"
    ENCRYPTED = "encrypted"

    @classmethod
    def from_string(cls, name: str) -> Layer:
        """Parse a canonical layer name; raise OpacityConfigError on unknown.

        The error type is imported lazily to avoid a circular import between
        this module and ``opacity.config``.
        """
        for member in cls:
            if member.value == name:
                return member
        from pyobfus_pro.opacity.config import OpacityConfigError

        valid = sorted(m.value for m in cls)
        raise OpacityConfigError(f"Unknown layer: {name!r}. Valid: {valid}")

    def is_at_least(self, other: Layer) -> bool:
        """Return True if self is >= other in the layer ordering."""
        return _ORDER[self] >= _ORDER[other]

    @property
    def order(self) -> int:
        """Integer rank: TRANSPARENT=0 ... ENCRYPTED=3."""
        return _ORDER[self]


_ORDER: Mapping[Layer, int] = {
    Layer.TRANSPARENT: 0,
    Layer.AI_READABLE: 1,
    Layer.OBFUSCATED: 2,
    Layer.ENCRYPTED: 3,
}


@dataclass(frozen=True)
class LayerSpec:
    """Frozen description of which AST passes a layer applies.

    The fields are the inputs to the build-pass transformer's per-layer
    dispatch logic; the spec for a layer is the deterministic mapping element
    that the patent's main claim language refers to.

    Fields are intentionally additive across layers (each higher layer turns
    on at least every flag the previous one had), encoding the strict-subset
    nesting property of the lattice.
    """

    layer: Layer
    rename_locals: bool
    rename_publics: bool
    inject_dead_code: bool
    flatten_control_flow: bool
    encrypt_strings: bool
    marshal_encrypt_code: bool
    seal_target: str
    materialization: str

    def __post_init__(self) -> None:
        if self.seal_target not in ("plaintext", "ciphertext"):
            raise ValueError(
                f"seal_target must be 'plaintext' or 'ciphertext', got {self.seal_target!r}"
            )
        if self.materialization not in ("function_body", "constant"):
            raise ValueError(
                f"materialization must be 'function_body' or 'constant', "
                f"got {self.materialization!r}"
            )


LAYER_SPECS: Mapping[Layer, LayerSpec] = {
    Layer.TRANSPARENT: LayerSpec(
        layer=Layer.TRANSPARENT,
        rename_locals=False,
        rename_publics=False,
        inject_dead_code=False,
        flatten_control_flow=False,
        encrypt_strings=False,
        marshal_encrypt_code=False,
        seal_target="plaintext",
        materialization="function_body",
    ),
    Layer.AI_READABLE: LayerSpec(
        layer=Layer.AI_READABLE,
        rename_locals=True,
        rename_publics=False,
        inject_dead_code=False,
        flatten_control_flow=False,
        encrypt_strings=False,
        marshal_encrypt_code=False,
        seal_target="plaintext",
        materialization="function_body",
    ),
    Layer.OBFUSCATED: LayerSpec(
        layer=Layer.OBFUSCATED,
        rename_locals=True,
        rename_publics=True,
        inject_dead_code=True,
        flatten_control_flow=True,
        encrypt_strings=True,
        marshal_encrypt_code=False,
        seal_target="plaintext",
        materialization="function_body",
    ),
    Layer.ENCRYPTED: LayerSpec(
        layer=Layer.ENCRYPTED,
        rename_locals=True,
        rename_publics=True,
        inject_dead_code=True,
        flatten_control_flow=True,
        encrypt_strings=True,
        marshal_encrypt_code=True,
        seal_target="ciphertext",
        materialization="function_body",
    ),
}
