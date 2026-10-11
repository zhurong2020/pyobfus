"""Discount rules; reaches back to the parent package with a relative import."""

from ..catalog import UNIT_PRICES

TIER_RATES = {"free": 0.0, "pro": 0.15, "enterprise": 0.30}


class DiscountPolicy:
    def __init__(self, tier):
        if tier not in TIER_RATES:
            raise ValueError(f"Unknown pricing tier: {tier}")
        self.rate = TIER_RATES[tier]

    def apply_tier_discount(self, amount):
        # Touch the parent-package import so it is exercised at runtime.
        assert UNIT_PRICES
        return amount * (1 - self.rate)
