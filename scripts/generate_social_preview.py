#!/usr/bin/env python3
"""Compose the GitHub social preview card at docs/assets/social-preview.png.

GitHub shows this image whenever the repository is linked from Slack, Discord,
X or anywhere else that reads Open Graph tags. Without one, every shared link
renders a generic auto-generated card, which is the difference between looking
like a product and looking like a scratch repository.

Why this is a script rather than an image-model prompt: the payload of a social
card *is* its text, and image models still garble text. Composing it here gives
exact glyphs, exact brand colours, and a rebuild whenever the tagline changes.
The existing logo is reused rather than redrawn so the card cannot drift away
from the mark used everywhere else.

    python scripts/generate_social_preview.py

Then upload the result at Settings -> General -> Social preview -> Edit.
GitHub wants 1280x640 and under 1 MB; this produces roughly 110 KB.
"""

from __future__ import annotations

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "docs" / "assets" / "logo.jpeg"
DEST = ROOT / "docs" / "assets" / "social-preview.png"

WIDTH, HEIGHT = 1280, 640
# Several platforms crop the edges of a preview card, so nothing goes here.
MARGIN = 88

NAVY = (26, 42, 94)
CYAN = (34, 199, 232)
INK = (28, 33, 48)
MUTED = (98, 110, 132)

BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

TITLE = "pyobfus"
TAGLINES = [
    "Obfuscate Python before you ship it.",
    "Reverse-map the tracebacks you get back.",
]
BADGE = "Apache-2.0 core  ·  PyPI  ·  MCP  ·  VS Code"


def main() -> None:
    logo = Image.open(LOGO).convert("RGB")
    # Paint the canvas in the logo's own ground colour so the pasted mark has
    # no visible edge.
    canvas = Image.new("RGB", (WIDTH, HEIGHT), logo.getpixel((2, 2)))
    draw = ImageDraw.Draw(canvas)

    for x in range(WIDTH):
        t = x / WIDTH
        draw.line(
            [(x, 0), (x, 10)],
            fill=tuple(int(NAVY[i] + (CYAN[i] - NAVY[i]) * t) for i in range(3)),
        )

    logo_height = 268
    width, height = logo.size
    logo = logo.resize((int(width * logo_height / height), logo_height), Image.LANCZOS)
    text_x = MARGIN + logo.size[0] + 44

    title_font = ImageFont.truetype(BOLD, 96)
    tag_font = ImageFont.truetype(REGULAR, 33)
    badge_font = ImageFont.truetype(BOLD, 23)

    # Fail loudly rather than ship a card with a sentence running off the edge.
    limit = WIDTH - MARGIN
    checks = [(TITLE, title_font), (BADGE, badge_font)]
    checks += [(line, tag_font) for line in TAGLINES]
    for text, font in checks:
        overflow = text_x + draw.textlength(text, font=font) - limit
        if overflow > 0:
            raise SystemExit(f"{text!r} overflows the safe area by {overflow:.0f}px")

    block_height = 96 + 20 + 44 + 44 + 24 + 23
    y = (HEIGHT - block_height) // 2 + 6
    canvas.paste(logo, (MARGIN, (HEIGHT - logo_height) // 2 + 5))

    draw.text((text_x, y), TITLE, font=title_font, fill=INK)
    y += 96 + 20
    draw.text((text_x + 4, y), TAGLINES[0], font=tag_font, fill=INK)
    y += 44
    draw.text((text_x + 4, y), TAGLINES[1], font=tag_font, fill=MUTED)
    y += 44 + 24
    draw.text((text_x + 4, y), BADGE, font=badge_font, fill=CYAN)

    canvas.save(DEST, "PNG", optimize=True)
    size_kb = os.path.getsize(DEST) / 1024
    if size_kb > 1024:
        raise SystemExit(f"{DEST} is {size_kb:.0f} KB; GitHub's limit is 1 MB")
    print(f"{DEST} — {WIDTH}x{HEIGHT}, {size_kb:.0f} KB")


if __name__ == "__main__":
    main()
