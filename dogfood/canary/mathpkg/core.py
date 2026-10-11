"""Cross-file consumer of the leaf helpers."""

from .helpers import scale


def compute(x: int) -> int:
    result = scale(x)
    return result + 1
