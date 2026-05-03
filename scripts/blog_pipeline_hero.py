#!/usr/bin/env python3
import argparse
import hashlib
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

SIZE = (1600, 900)
W, H = SIZE

FONT_CANDIDATES_BOLD = [
    "/System/Library/Fonts/SFNSRounded.ttf",
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


def fit_title_font(draw, text, max_width, max_lines, start_size=96, min_size=64):
    size = start_size
    while size >= min_size:
        font = load_font(FONT_CANDIDATES_BOLD, size)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4
    font = load_font(FONT_CANDIDATES_BOLD, min_size)
    return font, wrap_text(draw, text, font, max_width)[:max_lines]


def shorten_text(text, max_chars=110):
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    trimmed = text[: max_chars - 1].rsplit(" ", 1)[0].strip()
    return (trimmed or text[: max_chars - 1]).rstrip(" ,;:") + "…"


def parse_featured_titles(subtitle):
    subtitle = subtitle.strip()
    m = re.search(r"Featuring\s+(.+?)\s+—", subtitle, flags=re.IGNORECASE)
    if not m:
        return []
    chunk = m.group(1)
    chunk = re.sub(r"\band\b", ",", chunk, flags=re.IGNORECASE)
    titles = [part.strip(" .") for part in chunk.split(",") if part.strip()]
    return titles[:3]


def hash_palette(seed_text):
    h = hashlib.sha256(seed_text.encode()).digest()
    bg1 = (6 + h[0] % 10, 8 + h[1] % 12, 14 + h[2] % 18)
    bg2 = (34 + h[3] % 26, 10 + h[4] % 18, 14 + h[5] % 18)
    yellow = (255, 197 + h[6] % 24, 28)
    red = (188 + h[7] % 24, 32 + h[8] % 18, 34 + h[9] % 18)
    return bg1, bg2, yellow, red


def gradient_bg(c1, c2):
    img = Image.new("RGB", SIZE, c1)
    px = img.load()
    for y in range(H):
        for x in range(W):
            mix = (0.66 * (x / (W - 1))) + (0.34 * (y / (H - 1)))
            px[x, y] = tuple(int(c1[i] * (1 - mix) + c2[i] * mix) for i in range(3))
    return img.convert("RGBA")


def draw_pill(draw, x, y, text, font, fill, text_fill=(255, 255, 255), outline=None):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 34
    h = bbox[3] - bbox[1] + 18
    rect = (x, y, x + w, y + h)
    draw.rounded_rectangle(rect, radius=18, fill=fill, outline=outline, width=2 if outline else 0)
    draw.text((x + 17, y + 8), text, font=font, fill=text_fill)
    return rect


def build_poster_stack(featured_titles, accent, accent2):
    stack = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    card_w, card_h = 320, 430
    positions = [(1080, 104), (1180, 194), (960, 262)]
    title_font = load_font(FONT_CANDIDATES_BOLD, 38)
    meta_font = load_font(FONT_CANDIDATES_REGULAR, 18)

    titles = featured_titles or ["MovieJam", "Blog", "Pick better"]
    for idx, (x, y) in enumerate(positions[: len(titles)]):
        shadow = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow, "RGBA")
        sd.rounded_rectangle((14, 18, card_w - 2, card_h - 2), radius=30, fill=(0, 0, 0, 150))
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        stack.alpha_composite(shadow, (x - 10, y + 12))

        card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card, "RGBA")
        cd.rounded_rectangle((0, 0, card_w, card_h), radius=30, fill=(10, 12, 18, 245), outline=(255, 255, 255, 38), width=2)
        cd.rounded_rectangle((0, card_h - 74, card_w, card_h), radius=30, fill=accent2 + (255,))
        cd.rectangle((0, card_h - 74, card_w, card_h - 30), fill=accent2 + (255,))

        lines = wrap_text(cd, titles[idx].upper(), title_font, 246)[:3]
        yy = 112
        for line in lines:
            cd.text((34, yy), line, font=title_font, fill=(255, 255, 255))
            yy += title_font.size + 8

        cd.text((28, card_h - 62), "what to watch", font=meta_font, fill=(255, 255, 255))
        cd.text((28, card_h - 38), "without the scroll", font=meta_font, fill=(255, 244, 214))
        stack.alpha_composite(card, (x, y))
    return stack


def main():
    parser = argparse.ArgumentParser(description="Generate a MyMovieJam-style hero image.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--eyebrow", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    bg1, bg2, accent, accent2 = hash_palette(args.title + "|" + args.eyebrow)
    img = gradient_bg(bg1, bg2)

    glow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow, "RGBA")
    g.ellipse((1020, -80, 1710, 520), fill=accent2 + (120,))
    g.ellipse((830, 120, 1480, 820), fill=accent + (52,))
    g.ellipse((-180, 500, 520, 1180), fill=(80, 18, 22, 86))
    glow = glow.filter(ImageFilter.GaussianBlur(78))
    img = Image.alpha_composite(img, glow)

    frame = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    fd = ImageDraw.Draw(frame, "RGBA")
    fd.rounded_rectangle((26, 26, W - 26, H - 26), radius=42, fill=(5, 6, 10, 48), outline=(255, 255, 255, 28), width=2)
    fd.rounded_rectangle((60, 58, 934, H - 60), radius=36, fill=(5, 6, 10, 126), outline=(255, 255, 255, 18), width=2)
    fd.rounded_rectangle((60, H - 160, 430, H - 114), radius=18, fill=accent2 + (255,))
    img = Image.alpha_composite(img, frame)

    featured_titles = parse_featured_titles(args.subtitle)
    poster_stack = build_poster_stack(featured_titles, accent, accent2)
    img = Image.alpha_composite(img, poster_stack)

    draw = ImageDraw.Draw(img)
    eyebrow_font = load_font(FONT_CANDIDATES_BOLD, 26)
    subtitle_font = load_font(FONT_CANDIDATES_REGULAR, 27)
    footer_font = load_font(FONT_CANDIDATES_BOLD, 24)
    cta_font = load_font(FONT_CANDIDATES_BOLD, 28)
    micro_font = load_font(FONT_CANDIDATES_BOLD, 22)
    title_font, title_lines = fit_title_font(draw, args.title, 748, 4, start_size=94, min_size=56)

    draw.text((86, 104), "HOOK-STYLE BLOG IMAGE", font=micro_font, fill=(255, 245, 220))
    draw_pill(draw, 86, 150, args.eyebrow.upper()[:34], eyebrow_font, fill=accent + (255,), text_fill=(18, 18, 22))
    draw_pill(draw, 350, 150, "MYMOVIEJAM", eyebrow_font, fill=(255, 255, 255, 28), text_fill=(255, 255, 255), outline=(255, 255, 255, 50))

    y = 246
    for line in title_lines:
        draw.text((89, y + 3), line, font=title_font, fill=(0, 0, 0, 110))
        draw.text((86, y), line, font=title_font, fill=(255, 255, 255))
        y += title_font.size + 6

    underline_y = y + 10
    draw.rounded_rectangle((88, underline_y, 404, underline_y + 8), radius=4, fill=accent)
    draw.rounded_rectangle((410, underline_y + 2, 540, underline_y + 10), radius=4, fill=(255, 244, 214))

    subtitle = shorten_text(args.subtitle, max_chars=112)
    subtitle_lines = wrap_text(draw, subtitle, subtitle_font, 720)[:2]
    y = underline_y + 38
    for idx, line in enumerate(subtitle_lines):
        color = (232, 236, 244) if idx < len(subtitle_lines) - 1 else (255, 224, 146)
        draw.text((90, y), line, font=subtitle_font, fill=color)
        y += subtitle_font.size + 10

    draw.rounded_rectangle((86, 720, 446, 782), radius=26, fill=accent2, outline=accent, width=3)
    draw.text((120, 739), "Get picks on WhatsApp →", font=cta_font, fill=(255, 255, 255))
    draw.text((86, 804), "MYMOVIEJAM BLOG", font=footer_font, fill=(255, 255, 255))
    draw.text((330, 804), "what to watch without the scroll", font=footer_font, fill=(230, 232, 236))

    img.convert("RGB").save(out_path, quality=92)
    print(out_path)


if __name__ == "__main__":
    main()
