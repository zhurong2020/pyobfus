"""TOML config parser for P2-1 Selective Opacity.

Parses opacity.toml of the form::

    default_layer = "obfuscated"

    [[rules]]
    pattern = "myapp.api.*"
    layer   = "transparent"

    [[rules]]
    pattern = "myapp.crypto.*"
    layer   = "encrypted"

Validation:

- ``default_layer`` (optional, defaults to ``"obfuscated"``) must be one of the
  4 canonical layer names.
- ``rules`` (optional) is a list of ``{pattern, layer}`` records; each ``layer``
  must be canonical; ``pattern`` is a non-empty string (Unix-style glob).
- ``OpacityConfig.assignment_hash(qualnames)`` produces a deterministic
  ``sha256`` digest of the ``(qualname, layer)`` set, used by P2-7 to seed the
  forensic-watermark RNG without divergence.

Module deliberately does NOT depend on the build-pass transformer or the
runtime; can be imported and tested standalone.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # type: ignore[import-not-found,unused-ignore]
except ModuleNotFoundError:  # pragma: no cover -- only on py3.9 / py3.10
    import tomli as tomllib  # type: ignore[import-not-found,no-redef,unused-ignore]

from pyobfus_pro.opacity.layers import Layer


class OpacityConfigError(ValueError):
    """Raised on malformed opacity.toml or conflicting layer assignment."""


@dataclass(frozen=True)
class OpacityRule:
    pattern: str
    layer: Layer


@dataclass(frozen=True)
class OpacityConfig:
    """Parsed opacity.toml.

    ``default_layer`` is the floor for symbols neither decorated nor matched
    by a rule. ``rules`` are evaluated in declaration order, first-match wins.
    """

    default_layer: Layer = Layer.OBFUSCATED
    rules: tuple[OpacityRule, ...] = field(default_factory=tuple)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> OpacityConfig:
        if not isinstance(data, Mapping):
            raise OpacityConfigError(
                f"opacity config must be a TOML table, got {type(data).__name__}"
            )

        default_value = data.get("default_layer", "obfuscated")
        if not isinstance(default_value, str):
            raise OpacityConfigError(
                f"default_layer must be a string, got {type(default_value).__name__}"
            )
        default_layer = Layer.from_string(default_value)

        raw_rules = data.get("rules", [])
        if not isinstance(raw_rules, Sequence) or isinstance(raw_rules, (str, bytes)):
            raise OpacityConfigError(
                f"rules must be a list of tables, got {type(raw_rules).__name__}"
            )

        parsed_rules = []
        for index, entry in enumerate(raw_rules):
            if not isinstance(entry, Mapping):
                raise OpacityConfigError(
                    f"rules[{index}] must be a TOML table, got {type(entry).__name__}"
                )
            pattern = entry.get("pattern")
            layer_name = entry.get("layer")
            if not isinstance(pattern, str) or not pattern:
                raise OpacityConfigError(f"rules[{index}].pattern must be a non-empty string")
            if not isinstance(layer_name, str):
                raise OpacityConfigError(
                    f"rules[{index}].layer must be a string, got {type(layer_name).__name__}"
                )
            parsed_rules.append(OpacityRule(pattern=pattern, layer=Layer.from_string(layer_name)))

        return cls(default_layer=default_layer, rules=tuple(parsed_rules))

    @classmethod
    def from_toml(cls, source: str | Path | bytes) -> OpacityConfig:
        """Parse from a TOML file path or raw TOML bytes/string.

        ``source`` may be ``str`` / ``Path`` (filesystem path) or ``bytes``
        (raw TOML content). Strings that look like TOML content (containing
        ``=`` or ``[``) are parsed as content, not paths -- this keeps tests
        ergonomic without a tmp_path round-trip.
        """
        if isinstance(source, (bytes, bytearray)):
            data = tomllib.loads(source.decode("utf-8"))
        elif isinstance(source, Path):
            data = tomllib.loads(source.read_text(encoding="utf-8"))
        elif isinstance(source, str):
            looks_like_content = "=" in source or "[" in source or "\n" in source
            if looks_like_content:
                data = tomllib.loads(source)
            else:
                data = tomllib.loads(Path(source).read_text(encoding="utf-8"))
        else:
            raise TypeError(
                f"from_toml source must be str, Path, or bytes; got {type(source).__name__}"
            )

        try:
            return cls.from_dict(data)
        except OpacityConfigError:
            raise
        except Exception as exc:  # pragma: no cover -- defensive
            raise OpacityConfigError(f"Invalid opacity config: {exc}") from exc

    def assignment_hash(self, qualnames: Iterable[str]) -> bytes:
        """Deterministic sha256 over the (qualname, resolved layer) set.

        Used by P2-7 to seed the forensic-watermark RNG. The hash is stable
        across builds with identical config + symbol set, which is the
        property the patent main claim's "deterministic mapping" leans on.

        The resolver is constructed inline (no decorator overrides at this
        boundary -- decorator info lives on AST nodes, not in the config
        object). For runtime hashing including decorator overrides, callers
        should construct ``Resolver`` directly and pass its results in.
        """
        from pyobfus_pro.opacity.patterns import Resolver

        resolver = Resolver(self)
        sorted_qualnames = sorted(qualnames)
        digest = hashlib.sha256()
        for qualname in sorted_qualnames:
            layer = resolver.resolve(qualname, decorator_layer=None)
            digest.update(qualname.encode("utf-8"))
            digest.update(b"\x00")
            digest.update(layer.value.encode("utf-8"))
            digest.update(b"\x00")
        return digest.digest()
