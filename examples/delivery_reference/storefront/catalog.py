"""Catalog used by the reference order."""

UNIT_PRICES = {"widget": 12.5, "gadget": 40.0}


def lookup_unit_price(item):
    return UNIT_PRICES[item]
