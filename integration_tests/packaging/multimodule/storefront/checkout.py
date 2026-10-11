"""Combines the catalog and the discount rules."""

from .catalog import lookup_unit_price
from .rules.discounts import DiscountPolicy


def quote_order(lines, tier):
    policy = DiscountPolicy(tier)
    subtotal = sum(lookup_unit_price(item) * qty for item, qty in lines)
    return f"{tier}: {policy.apply_tier_discount(subtotal):.2f}"
