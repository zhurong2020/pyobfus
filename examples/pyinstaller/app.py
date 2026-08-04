"""
Standalone CLI app for the "obfuscate, then bundle to a single exe" cookbook.

Deliberately stdlib-only (no third-party imports) so the PyInstaller build
step in the accompanying README has nothing else to go wrong — the point of
this example is the obfuscate -> bundle -> run pipeline itself, not
PyInstaller's dependency-discovery machinery.
"""

import sys


def apply_discount(price, tier):
    """Return the discounted price for a pricing tier ('free', 'pro', 'enterprise')."""
    discounts = {"free": 0.0, "pro": 0.15, "enterprise": 0.30}
    if tier not in discounts:
        raise ValueError(f"Unknown pricing tier: {tier}")
    return round(price * (1 - discounts[tier]), 2)


def main():
    price = 100.0
    tier = sys.argv[1] if len(sys.argv) > 1 else "pro"
    final_price = apply_discount(price, tier)
    print(f"List price: ${price:.2f}")
    print(f"Tier: {tier}")
    print(f"Final price: ${final_price:.2f}")


if __name__ == "__main__":
    main()
