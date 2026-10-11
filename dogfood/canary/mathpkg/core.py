"""Cross-file consumer of the leaf helpers."""

import mathpkg.helpers as helpers


def compute(x: int) -> int:
    result = helpers.scale(x)
    return result + 1
