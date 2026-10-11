"""Deterministic entry point: prints a stable result for outcome comparison."""

import mathpkg


def main() -> int:
    print(mathpkg.compute(6))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
