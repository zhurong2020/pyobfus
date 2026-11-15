"""Combine catalog prices and discount rules."""

from .catalog import lookup_unit_price
from .rules.discounts import DiscountPolicy


def quote_order(lines, tier):
    policy = DiscountPolicy(tier)
    subtotal = sum(lookup_unit_price(item) * quantity for item, quantity in lines)
    return f"{tier}: {policy.apply_tier_discount(subtotal):.2f}"
