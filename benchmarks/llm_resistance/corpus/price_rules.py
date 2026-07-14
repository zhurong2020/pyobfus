def final_price(quantity, unit_price, coupon):
    """Compute an order total from tiered volume discounts plus an optional coupon.

    Volume tiers: >=100 units 20% off, >=50 units 12% off, >=10 units 5% off.
    Coupon "SAVE10" takes a further 10% off the post-tier subtotal; "FREESHIP"
    subtracts a flat 7.50 but never below zero. Result is rounded to 2 places.
    """
    subtotal = quantity * unit_price
    if quantity >= 100:
        subtotal = subtotal * 0.80
    elif quantity >= 50:
        subtotal = subtotal * 0.88
    elif quantity >= 10:
        subtotal = subtotal * 0.95
    if coupon == "SAVE10":
        subtotal = subtotal * 0.90
    elif coupon == "FREESHIP":
        subtotal = subtotal - 7.50
        if subtotal < 0:
            subtotal = 0.0
    return round(subtotal, 2)
