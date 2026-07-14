def caesar(text, shift):
    """Caesar-cipher `text` by `shift`, preserving case and passing non-letters."""
    out = []
    for ch in text:
        if "a" <= ch <= "z":
            base = ord("a")
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        elif "A" <= ch <= "Z":
            base = ord("A")
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)
