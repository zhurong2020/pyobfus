"""Unit prices, looked up by the checkout module."""

UNIT_PRICES = {"widget": 12.5, "gadget": 40.0}


def lookup_unit_price(item):
    return UNIT_PRICES[item]
