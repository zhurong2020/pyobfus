"""Deterministic entry point: prints a stable result for outcome comparison."""

from mathpkg import compute


def main() -> int:
    print(compute(6))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
