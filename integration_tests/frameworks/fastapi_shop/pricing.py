"""Pricing rules: the part a vendor would want to keep private."""

from models import OrderQuote, OrderRequest

TIER_DISCOUNTS = {"standard": 0.0, "partner": 0.08, "enterprise": 0.15}
VOLUME_THRESHOLD = 1000.0
VOLUME_BONUS = 0.02


def discount_rate(tier: str, subtotal: float) -> float:
    rate = TIER_DISCOUNTS[tier]
    if subtotal >= VOLUME_THRESHOLD:
        rate += VOLUME_BONUS
    return rate


def quote_order(order: OrderRequest) -> OrderQuote:
    subtotal = sum(line.quantity * line.unit_price for line in order.lines)
    discount = round(subtotal * discount_rate(order.customer_tier, subtotal), 2)
    return OrderQuote(
        subtotal=round(subtotal, 2),
        discount=discount,
        total=round(subtotal - discount, 2),
        line_count=len(order.lines),
    )


def margin_ratio(revenue: float, cost: float) -> float:
    # No guard for revenue == 0: the integration test uses this as the
    # deliberate production failure whose traceback gets unmapped.
    return round((revenue - cost) / revenue, 4)
