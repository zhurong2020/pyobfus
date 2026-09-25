"""Leaf helpers imported across files."""


def scale(value: int) -> int:
    factor = 4  # local name that must survive mangling within its scope
    return value * factor
