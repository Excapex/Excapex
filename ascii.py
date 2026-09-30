"""Turns a portrait into ascii.txt for the profile card.

    python ascii.py portrait.png             # dark lines on a white background (recommended)
    python ascii.py portrait.png --invert    # light subject on a black background
    python ascii.py --initials SS            # fallback monogram

Works best with a high-contrast, head-and-shoulders illustration on a plain
white background (see PORTRAIT_PROMPT.md). Photos with busy backgrounds turn
into noise at this size.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

COLS, ROWS = 60, 30  # rendered in a smaller font than the info column, see today.py
RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def to_ascii(img, invert=False):
    img = ImageOps.autocontrast(img.convert("L"), cutoff=1)
    img = img.resize((COLS, ROWS), Image.LANCZOS)
    px = img.load()
    rows = []
    for y in range(ROWS):
        row = ""
        for x in range(COLS):
            v = px[x, y] if invert else 255 - px[x, y]  # denser glyph = more "ink"
            row += RAMP[int(v / 256 * len(RAMP))]
        rows.append(row.rstrip())
    return "\n".join(rows)


def initials_image(text):
    img = Image.new("L", (COLS * 10, ROWS * 18), 255)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arialbd.ttf", 300)
    except OSError:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(((img.width - w) / 2 - box[0], (img.height - h) / 2 - box[1]), text, font=font, fill=0)
    return img


def main():
    args = [a for a in sys.argv[1:] if a != "--invert"]
    invert = "--invert" in sys.argv
    if len(args) == 2 and args[0] == "--initials":
        img = initials_image(args[1])
    elif len(args) == 1:
        img = Image.open(args[0])
    else:
        sys.exit(__doc__)
    out = Path(__file__).with_name("ascii.txt")
    out.write_text(to_ascii(img, invert) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
