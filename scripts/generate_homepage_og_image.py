#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SIZE = (1200, 630)
W, H = SIZE
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "blog" / "images" / "mymoviejam-home-share.jpg"

FONT_BOLD_CANDIDATES = [
    "/System/Library/Fonts/SFNSRounded.ttf",
    "/System/Library/Fonts/HelveticaNeue.ttc",
    "/System/Library/Fonts/Avenir Next.ttc",
    "/System/Library/Fonts/Avenir.ttc",
]
FONT_REGULAR_CANDIDATES = [
    "/System/Library/Fonts/SFNS.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Avenir Next.ttc",
    "/System/Library/Fonts/Avenir.ttc",
]


def load_font(candidates: list[str], size: int, index: int = 0) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in candidates:
        path = Path(candidate)
        if not path.exists():
            continue
        try:
            return ImageFont.truetype(str(path), size=size, index=index)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_vertical_gradient() -> Image.Image:
    img = Image.new("RGB", SIZE)
    px = img.load()
    top = (12, 9, 18)
    bottom = (29, 14, 18)
    for y in range(H):
        mix = y / (H - 1)
        row = tuple(int(top[i] * (1 - mix) + bottom[i] * mix) for i in range(3))
        for x in range(W):
            px[x, y] = row
    return img


def add_glow(base: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> None:
    layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    x, y = center
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*color, alpha))
    blurred = layer.filter(ImageFilter.GaussianBlur(radius // 2))
    base.alpha_composite(blurred)


def rounded_panel(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: tuple[int, int, int, int], outline: tuple[int, int, int, int] | None = None) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=2 if outline else 0)


def wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
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


def fit_lines(draw: ImageDraw.ImageDraw, text: str, max_width: int, max_lines: int, start_size: int, min_size: int) -> tuple[ImageFont.ImageFont, list[str]]:
    for size in range(start_size, min_size - 1, -2):
        font = load_font(FONT_BOLD_CANDIDATES, size, index=1)
        lines = wrap(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
    font = load_font(FONT_BOLD_CANDIDATES, min_size, index=1)
    return font, wrap(draw, text, font, max_width)[:max_lines]


def make_logo(size: int = 76) -> Image.Image:
    logo = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(logo)
    for i in range(size):
        mix = i / max(1, size - 1)
        color = (
            int(255 * (1 - mix) + 255 * mix),
            int(87 * (1 - mix) + 138 * mix),
            int(87 * (1 - mix) + 61 * mix),
            255,
        )
        draw.ellipse((0, 0, size - 1, size - 1), outline=color)
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, size - 1, size - 1), fill=255)
    grad = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gp = grad.load()
    for y in range(size):
        for x in range(size):
            mix = ((x / max(1, size - 1)) + (y / max(1, size - 1))) / 2
            gp[x, y] = (
                int(255 * (1 - mix) + 255 * mix),
                int(87 * (1 - mix) + 138 * mix),
                int(87 * (1 - mix) + 61 * mix),
                255,
            )
    grad.putalpha(mask)
    logo.alpha_composite(grad)
    play = [
        (size * 0.42, size * 0.30),
        (size * 0.42, size * 0.70),
        (size * 0.73, size * 0.50),
    ]
    draw.polygon(play, fill=(255, 255, 255, 255))
    return logo


def main() -> None:
    base = draw_vertical_gradient().convert("RGBA")
    add_glow(base, (250, 130), 270, (255, 100, 100), 80)
    add_glow(base, (1020, 90), 300, (255, 162, 66), 78)
    add_glow(base, (1030, 500), 240, (255, 95, 80), 68)

    panel = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(panel)

    main_box = (44, 42, 880, 588)
    rounded_panel(draw, main_box, radius=34, fill=(9, 11, 18, 216), outline=(255, 255, 255, 20))

    accent_box = (912, 92, 1138, 516)
    rounded_panel(draw, accent_box, radius=30, fill=(11, 12, 20, 228), outline=(255, 255, 255, 24))
    panel = panel.filter(ImageFilter.GaussianBlur(0.2))
    base.alpha_composite(panel)

    draw = ImageDraw.Draw(base)
    logo = make_logo(72)
    base.alpha_composite(logo, (84, 84))

    brand_font = load_font(FONT_BOLD_CANDIDATES, 34, index=0)
    micro_font = load_font(FONT_REGULAR_CANDIDATES, 20, index=0)
    body_font = load_font(FONT_REGULAR_CANDIDATES, 22, index=0)
    chip_font = load_font(FONT_REGULAR_CANDIDATES, 17, index=0)

    draw.text((172, 96), "MyMovieJam", font=brand_font, fill=(255, 255, 255))
    draw.text((172, 140), "Built for people who are done doom-scrolling.", font=micro_font, fill=(255, 218, 169))

    title = "Stop scrolling. Start watching."
    title_font, lines = fit_lines(draw, title, 650, 3, start_size=72, min_size=56)
    y = 218
    for line in lines:
        draw.text((86, y), line, font=title_font, fill=(255, 255, 255))
        bbox = draw.textbbox((86, y), line, font=title_font)
        y = bbox[3] + 8

    draw.rounded_rectangle((88, y + 14, 292, y + 24), radius=6, fill=(255, 203, 54))
    draw.rounded_rectangle((304, y + 14, 498, y + 24), radius=6, fill=(248, 225, 187))

    body_lines = [
        "Audience-first movie picks, honest reviews, and",
        "what-to-watch-tonight help across Netflix, Prime Video, Disney+ and more.",
    ]
    by = y + 56
    for line in body_lines:
        draw.text((86, by), line, font=body_font, fill=(232, 235, 243))
        bbox = draw.textbbox((86, by), line, font=body_font)
        by = bbox[3] + 6

    chips = [
        "WhatsApp-first picks",
        "Honest reviews",
        "Movie night solved",
    ]
    cx = 86
    cy = by + 10
    for chip in chips:
        bbox = draw.textbbox((0, 0), chip, font=chip_font)
        width = (bbox[2] - bbox[0]) + 34
        draw.rounded_rectangle((cx, cy, cx + width, cy + 34), radius=17, fill=(20, 23, 33), outline=(255, 192, 62), width=2)
        draw.text((cx + 17, cy + 8), chip, font=chip_font, fill=(255, 245, 219))
        cx += width + 12

    draw.text((86, cy + 48), "mymoviejam.com", font=micro_font, fill=(255, 255, 255, 220))

    accent = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    ad = ImageDraw.Draw(accent)
    ad.rounded_rectangle((942, 128, 1108, 456), radius=28, fill=(16, 18, 28, 255))
    ad.rounded_rectangle((964, 152, 1086, 342), radius=18, fill=(255, 203, 54))
    ad.rounded_rectangle((964, 358, 1086, 432), radius=18, fill=(220, 45, 45))
    base.alpha_composite(accent.rotate(-9, resample=Image.Resampling.BICUBIC, center=(1025, 292)))

    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((900, 32, 1170, 302), fill=(255, 171, 54, 34))
    od.ellipse((956, 288, 1160, 492), fill=(255, 95, 80, 42))
    base.alpha_composite(overlay.filter(ImageFilter.GaussianBlur(18)))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(OUT, format="JPEG", quality=92, optimize=True, progressive=True)
    print(OUT)


if __name__ == "__main__":
    main()
