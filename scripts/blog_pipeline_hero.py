#!/usr/bin/env python3
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SIZE = (1600, 900)

FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
]
FONT_CANDIDATES_REGULAR = [
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
]


def load_font(candidates, size):
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def main():
    parser = argparse.ArgumentParser(description="Generate a MyMovieJam-style hero image.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--eyebrow", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", SIZE, "#0a0d16")
    draw = ImageDraw.Draw(img)

    for y in range(SIZE[1]):
        t = y / SIZE[1]
        r = int(8 + (42 - 8) * t)
        g = int(13 + (18 - 13) * t)
        b = int(22 + (71 - 22) * t)
        draw.line((0, y, SIZE[0], y), fill=(r, g, b))

    glow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse((1020, -120, 1620, 480), fill=(37, 211, 102, 110))
    gdraw.ellipse((-100, 420, 540, 1120), fill=(255, 68, 68, 90))
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    img = Image.alpha_composite(img.convert("RGBA"), glow)

    panel = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    pdraw = ImageDraw.Draw(panel)
    pdraw.rounded_rectangle((78, 72, 1522, 828), radius=42, fill=(255, 255, 255, 20), outline=(255, 255, 255, 42), width=2)
    img = Image.alpha_composite(img, panel)

    draw = ImageDraw.Draw(img)
    eyebrow_font = load_font(FONT_CANDIDATES_BOLD, 34)
    title_font = load_font(FONT_CANDIDATES_BOLD, 82)
    subtitle_font = load_font(FONT_CANDIDATES_REGULAR, 34)
    badge_font = load_font(FONT_CANDIDATES_BOLD, 28)

    draw.rounded_rectangle((110, 120, 430, 176), radius=28, fill=(37, 211, 102, 230))
    draw.text((138, 131), args.eyebrow.upper()[:28], font=badge_font, fill=(255, 255, 255))

    title_lines = wrap_text(draw, args.title, title_font, 1120)
    y = 230
    for line in title_lines[:4]:
        draw.text((118, y), line, font=title_font, fill=(255, 255, 255))
        bbox = draw.textbbox((118, y), line, font=title_font)
        y = bbox[3] + 10

    subtitle_lines = wrap_text(draw, args.subtitle, subtitle_font, 980)
    y += 34
    for line in subtitle_lines[:3]:
        draw.text((122, y), line, font=subtitle_font, fill=(228, 232, 240))
        bbox = draw.textbbox((122, y), line, font=subtitle_font)
        y = bbox[3] + 10

    draw.rounded_rectangle((118, 700, 540, 772), radius=34, fill=(255, 255, 255, 240))
    draw.text((152, 720), "Get picks on WhatsApp →", font=badge_font, fill=(18, 140, 126))
    draw.text((118, 796), "mymoviejam.com", font=subtitle_font, fill=(220, 226, 236))

    img.convert("RGB").save(out_path, quality=92)
    print(out_path)


if __name__ == "__main__":
    main()
