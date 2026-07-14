def luhn_valid(number):
    """Return True if the digit string passes the Luhn checksum."""
    digits = [int(c) for c in str(number) if c.isdigit()]
    total = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d = d * 2
            if d > 9:
                d = d - 9
        total = total + d
    return total % 10 == 0
