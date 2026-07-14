def to_roman(n):
    """Convert an integer in 1..3999 to its Roman-numeral string."""
    table = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    out = []
    for value, symbol in table:
        while n >= value:
            out.append(symbol)
            n = n - value
    return "".join(out)
