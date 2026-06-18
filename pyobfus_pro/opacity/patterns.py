"""Per-symbol layer resolver: decorator > config-rule > default precedence.

The resolution function is byte-deterministic for a given config and qualname
set, which the patent main claim hangs on. Its only non-determinism source is
the decorator-layer parameter, which is itself a property of the AST node
under transformation -- so for any (config, AST) pair, layer assignment is a
pure function.
"""

from __future__ import annotations

from fnmatch import fnmatchcase

from pyobfus_pro.opacity.config import OpacityConfig
from pyobfus_pro.opacity.layers import Layer


class Resolver:
    """Resolves a symbol's qualified name to its protection layer.

    Precedence (highest first):
        1. ``decorator_layer`` argument (set when the AST node carries
           ``@opacity("...")``)
        2. First matching rule in ``config.rules`` (declaration order)
        3. ``config.default_layer``

    The resolver does not raise on unmatched symbols -- the default layer is
    the configured floor. Conflicting overlapping rules are detected via
    ``check_for_conflicts()`` rather than at resolve time, so resolution
    itself stays branch-light for the build pass.
    """

    def __init__(self, config: OpacityConfig) -> None:
        self.config = config

    def resolve(self, qualname: str, decorator_layer: Layer | None = None) -> Layer:
        if decorator_layer is not None:
            return decorator_layer
        for rule in self.config.rules:
            if fnmatchcase(qualname, rule.pattern):
                return rule.layer
        return self.config.default_layer

    def check_for_conflicts(self, qualnames):
        """Return list of (qualname, [matching_rules]) where >1 rule matches.

        Multiple matching rules aren't an error per se (first-match-wins), but
        the build pass surfaces them as a warning so users can clean up
        ambiguous configs. The actual hard-error case (same qualname assigned
        different layers via decorator AND a conflicting decorator on a
        wrapper) is handled in the build pass, not here.
        """
        conflicts = []
        for qualname in qualnames:
            matching = [rule for rule in self.config.rules if fnmatchcase(qualname, rule.pattern)]
            if len(matching) > 1:
                conflicts.append((qualname, matching))
        return conflicts
