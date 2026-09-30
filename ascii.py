"""Turns a photo into ascii.txt for the profile card.

    python ascii.py path/to/photo.jpg            # portrait
    python ascii.py --initials SS                # fallback monogram

Crop the photo to a roughly square head-and-shoulders shot first; a plain
background gives the cleanest result; paint the background black.
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

COLS, ROWS = 36, 21  # fits the 375px-wide left column at 16px Consolas, same height as the info rows
RAMP = " .'`^\",:;Il!i~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"


def to_ascii(img):
    img = ImageOps.autocontrast(img.convert("L"))
    img = img.resize((COLS, ROWS))
    px = img.load()
    rows = []
    for y in range(ROWS):
        row = ""
        for x in range(COLS):
            # bright pixels -> dense glyphs, so the portrait reads as lit on the dark card
            row += RAMP[int(px[x, y] / 256 * len(RAMP))]
        rows.append(row.rstrip())
    return "\n".join(rows)


def initials_image(text):
    img = Image.new("L", (COLS * 10, ROWS * 18), 0)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arialbd.ttf", 300)
    except OSError:
        font = ImageFont.load_default()
    box = draw.textbbox((0, 0), text, font=font)
    w, h = box[2] - box[0], box[3] - box[1]
    draw.text(((img.width - w) / 2 - box[0], (img.height - h) / 2 - box[1]), text, font=font, fill=255)
    return img


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--initials":
        img = initials_image(sys.argv[2])
    elif len(sys.argv) == 2:
        img = Image.open(sys.argv[1])
    else:
        sys.exit(__doc__)
    out = Path(__file__).with_name("ascii.txt")
    out.write_text(to_ascii(img) + "\n", encoding="utf-8")
    print(out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
