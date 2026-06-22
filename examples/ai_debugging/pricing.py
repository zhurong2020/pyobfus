"""Tiny order-pricing module with a latent bug, for the reverse-mapping demo."""


def line_total(unit_price, quantity):
    return unit_price * quantity


def order_total(line_items):
    subtotal = 0
    for item in line_items:
        subtotal += line_total(item["price"], item["qty"])
    # BUG: assumes a "discount_rate" key that some items lack -> KeyError
    discount = subtotal * line_items[0]["discount_rate"]
    return subtotal - discount


if __name__ == "__main__":
    cart = [{"price": 10.0, "qty": 2}, {"price": 5.0, "qty": 4}]
    print(order_total(cart))
