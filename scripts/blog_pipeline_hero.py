#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SIZE = (1600, 900)
W, H = SIZE
USER_AGENT = "Mozilla/5.0 (compatible; MyMovieJamHero/1.0)"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
CACHE_DIR = Path(__file__).resolve().parents[1] / "cache" / "blog_hero_posters"

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


def normalize(text):
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def strip_year_suffix(title):
    return re.sub(r"\s*\((?:19|20)\d{2}[^)]*\)$", "", title).strip()


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"&", " and ", text)
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


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


def fit_title_font(draw, text, max_width, max_lines, start_size=100, min_size=58):
    size = start_size
    while size >= min_size:
        font = load_font(FONT_CANDIDATES_BOLD, size)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return font, lines
        size -= 4
    font = load_font(FONT_CANDIDATES_BOLD, min_size)
    return font, wrap_text(draw, text, font, max_width)[:max_lines]


def shorten_text(text, max_chars=120):
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


def infer_review_target(title):
    cleaned = re.sub(r"\b(review|ending explained|is it worth it|worth it|moviejam|series review|movie review)\b", "", title, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bon\s+(netflix|amazon prime|prime video|disney\+?|hulu|max|apple tv\+?)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(netflix|amazon prime|prime video|disney\+?|hulu|max|apple tv\+?)\b", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.split(r"[:\-–|]", cleaned)[0].strip(" ?!.:")
    cleaned = re.sub(r"\b(on|at|for|from|with)\b\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return strip_year_suffix(cleaned)


def infer_queries(title, subtitle):
    featured = parse_featured_titles(subtitle)
    if featured:
        return featured
    target = infer_review_target(title)
    return [target] if target else []


def hash_palette(seed_text):
    h = hashlib.sha256(seed_text.encode()).digest()
    bg1 = (6 + h[0] % 12, 8 + h[1] % 14, 16 + h[2] % 18)
    bg2 = (42 + h[3] % 28, 10 + h[4] % 18, 20 + h[5] % 22)
    yellow = (255, 200 + h[6] % 20, 34)
    red = (190 + h[7] % 24, 34 + h[8] % 18, 36 + h[9] % 18)
    blue = (82 + h[10] % 30, 150 + h[11] % 40, 255)
    return bg1, bg2, yellow, red, blue


def gradient_bg(c1, c2):
    img = Image.new("RGB", SIZE, c1)
    px = img.load()
    for y in range(H):
        for x in range(W):
            mix = (0.62 * (x / (W - 1))) + (0.38 * (y / (H - 1)))
            px[x, y] = tuple(int(c1[i] * (1 - mix) + c2[i] * mix) for i in range(3))
    return img.convert("RGBA")


def wiki_api_json(params):
    url = WIKIPEDIA_API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def wiki_search_titles(query):
    data = wiki_api_json({"action": "query", "format": "json", "list": "search", "srsearch": query, "srlimit": "5"})
    return [item["title"] for item in data.get("query", {}).get("search", [])]


def wiki_page_images(page_title):
    data = wiki_api_json({"action": "query", "format": "json", "prop": "images", "titles": page_title})
    pages = data.get("query", {}).get("pages", {})
    images = []
    for page in pages.values():
        for item in page.get("images", []):
            images.append(item["title"])
    return images


def wiki_image_url(file_title):
    data = wiki_api_json({"action": "query", "format": "json", "titles": file_title, "prop": "imageinfo", "iiprop": "url"})
    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        infos = page.get("imageinfo") or []
        if infos:
            return infos[0].get("url")
    return None


def choose_poster_file(image_titles):
    preferred = []
    fallback = []
    for title in image_titles:
        t = title.lower()
        if not t.startswith("file:"):
            continue
        if any(skip in t for skip in ["logo", "icon", "svg", "wordmark", "edit-clear"]):
            continue
        if any(key in t for key in ["poster", "promotional", "title card", "cover"]):
            preferred.append(title)
        elif any(ext in t for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            fallback.append(title)
    return (preferred or fallback or [None])[0]


def fetch_wikipedia_poster(query):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(query)
    for ext in ["jpg", "jpeg", "png", "webp"]:
        cached = CACHE_DIR / f"{slug}.{ext}"
        if cached.exists():
            return cached

    candidates = [query, f"{query} (film)", f"{query} (TV series)", f'"{query}" film', f'"{query}" TV series']
    page_titles = []
    seen = set()
    for item in candidates:
        key = normalize(item)
        if key not in seen:
            page_titles.append(item)
            seen.add(key)
        try:
            for result in wiki_search_titles(item):
                n = normalize(result)
                if n not in seen:
                    page_titles.append(result)
                    seen.add(n)
        except Exception:
            continue

    for page_title in page_titles[:20]:
        try:
            images = wiki_page_images(page_title)
            file_title = choose_poster_file(images)
            if not file_title:
                continue
            img_url = wiki_image_url(file_title)
            if not img_url:
                continue
            ext = Path(urllib.parse.urlparse(img_url).path).suffix or ".jpg"
            dest = CACHE_DIR / f"{slug}{ext}"
            req = urllib.request.Request(img_url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as r:
                dest.write_bytes(r.read())
            return dest
        except Exception:
            continue
    return None


def fit_image_card(img, box, radius=42):
    fitted = ImageOps.cover(img.convert("RGB"), box, method=Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", box, (0, 0, 0, 0))
    canvas.paste(fitted.convert("RGBA"), (0, 0))
    mask = Image.new("L", box, 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, box[0], box[1]), radius=radius, fill=255)
    canvas.putalpha(mask)
    return canvas


def draw_pill(draw, x, y, text, font, fill, text_fill=(255, 255, 255), outline=None):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0] + 34
    h = bbox[3] - bbox[1] + 18
    rect = (x, y, x + w, y + h)
    draw.rounded_rectangle(rect, radius=18, fill=fill, outline=outline, width=2 if outline else 0)
    draw.text((x + 17, y + 8), text, font=font, fill=text_fill)
    return rect


def poster_stack_with_art(featured_titles, accent, blue):
    stack = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    positions = [
        {"xy": (1040, 92), "box": (390, 560), "angle": -6, "shadow": 26},
        {"xy": (1214, 238), "box": (248, 360), "angle": 8, "shadow": 18},
        {"xy": (920, 340), "box": (230, 330), "angle": -10, "shadow": 16},
    ]

    title_font = load_font(FONT_CANDIDATES_BOLD, 26)
    meta_font = load_font(FONT_CANDIDATES_REGULAR, 16)
    fallback_bg = (12, 14, 22, 245)

    titles = featured_titles[:3] or ["MovieJam Pick"]
    posters = [fetch_wikipedia_poster(title) for title in titles]

    if posters and posters[0]:
        try:
            poster = Image.open(posters[0]).convert("RGB")
            bg = ImageOps.fit(poster, SIZE, method=Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28)).convert("RGBA")
            overlay = Image.new("RGBA", SIZE, (4, 6, 12, 166))
            left_vignette = Image.new("RGBA", SIZE, (0, 0, 0, 0))
            vg = ImageDraw.Draw(left_vignette, "RGBA")
            vg.rectangle((0, 0, 1040, H), fill=(6, 8, 14, 210))
            vg.rectangle((860, 0, W, H), fill=(0, 0, 0, 20))
            bg = Image.alpha_composite(bg, overlay)
            bg = Image.alpha_composite(bg, left_vignette)
            stack = Image.alpha_composite(stack, bg)
        except Exception:
            pass

    for idx, title in enumerate(titles):
        cfg = positions[idx]
        x, y = cfg["xy"]
        box_w, box_h = cfg["box"]
        poster_path = posters[idx] if idx < len(posters) else None

        shadow = Image.new("RGBA", (box_w + 50, box_h + 50), (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow, "RGBA")
        sd.rounded_rectangle((22, 22, box_w + 22, box_h + 22), radius=42, fill=(0, 0, 0, 170))
        shadow = shadow.filter(ImageFilter.GaussianBlur(cfg["shadow"]))
        stack.alpha_composite(shadow, (x - 20, y + 18))

        card = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card, "RGBA")
        cd.rounded_rectangle((0, 0, box_w, box_h), radius=42, fill=fallback_bg, outline=(255, 255, 255, 36), width=2)
        if poster_path and Path(poster_path).exists():
            try:
                poster = Image.open(poster_path)
                art = fit_image_card(poster, (box_w, box_h), radius=42)
                card.alpha_composite(art, (0, 0))
                shade = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
                sh = ImageDraw.Draw(shade, "RGBA")
                sh.rectangle((0, int(box_h * 0.54), box_w, box_h), fill=(6, 8, 14, 188))
                card.alpha_composite(shade, (0, 0))
            except Exception:
                pass
        else:
            cd.rounded_rectangle((0, box_h - 96, box_w, box_h), radius=42, fill=accent + (255,))
            cd.rectangle((0, box_h - 96, box_w, box_h - 36), fill=accent + (255,))

        label_rect = (18, 18, 168, 58)
        cd.rounded_rectangle(label_rect, radius=16, fill=(8, 12, 20, 210), outline=blue + (180,), width=2)
        cd.text((34, 28), "MYMOVIEJAM", font=meta_font, fill=(255, 255, 255))

        lines = wrap_text(cd, title.upper(), title_font, box_w - 44)[:3]
        yy = box_h - 112 - (len(lines) - 1) * (title_font.size + 4)
        for line in lines:
            cd.text((22, yy), line, font=title_font, fill=(255, 255, 255))
            yy += title_font.size + 4

        badge_font = load_font(FONT_CANDIDATES_BOLD, 18)
        badge_y = box_h - 52
        cd.rounded_rectangle((22, badge_y, 150, badge_y + 34), radius=14, fill=accent + (255,))
        cd.text((38, badge_y + 7), "TOP PICK", font=badge_font, fill=(18, 18, 22))

        rotated = card.rotate(cfg["angle"], resample=Image.Resampling.BICUBIC, expand=True)
        stack.alpha_composite(rotated, (x, y))
    return stack


def add_noise(img, opacity=20):
    noise = Image.effect_noise(SIZE, 8).convert("L")
    noise = ImageOps.colorize(noise, black=(0, 0, 0), white=(255, 255, 255)).convert("RGBA")
    alpha = Image.new("L", SIZE, opacity)
    noise.putalpha(alpha)
    return Image.alpha_composite(img, noise)


def main():
    parser = argparse.ArgumentParser(description="Generate a minimal MyMovieJam blog hero image.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--eyebrow", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGBA", SIZE, (8, 8, 10, 255))

    bg = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    bp = bg.load()
    for y in range(H):
        mix = y / (H - 1)
        top = (7, 7, 9)
        bottom = (18, 18, 22)
        row = tuple(int(top[i] * (1 - mix) + bottom[i] * mix) for i in range(3))
        for x in range(W):
            bp[x, y] = row + (255,)
    img = Image.alpha_composite(img, bg)

    glow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    g = ImageDraw.Draw(glow, "RGBA")
    g.ellipse((-180, -120, 520, 420), fill=(48, 72, 128, 48))
    g.ellipse((1080, 500, 1710, 1120), fill=(88, 88, 120, 34))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.alpha_composite(img, glow)
    img = add_noise(img, opacity=6)

    draw = ImageDraw.Draw(img)
    eyebrow_text = f"{args.eyebrow.upper()} • MYMOVIEJAM"
    eyebrow_font = load_font(FONT_CANDIDATES_REGULAR, 26)
    title_font, title_lines = fit_title_font(draw, args.title, 1120, 4, start_size=96, min_size=52)
    footer_font = load_font(FONT_CANDIDATES_REGULAR, 20)

    eyebrow_bbox = draw.textbbox((0, 0), eyebrow_text, font=eyebrow_font)
    eyebrow_w = eyebrow_bbox[2] - eyebrow_bbox[0]
    draw.text(((W - eyebrow_w) / 2, 164), eyebrow_text, font=eyebrow_font, fill=(176, 176, 184))

    y = 318
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_w = bbox[2] - bbox[0]
        x = (W - line_w) / 2
        draw.text((x, y), line, font=title_font, fill=(245, 245, 247))
        y += title_font.size + 10

    rule_y = y + 28
    rule_w = 180
    draw.rounded_rectangle(((W - rule_w) / 2, rule_y, (W + rule_w) / 2, rule_y + 6), radius=3, fill=(92, 92, 102))

    footer = "mymoviejam.com"
    footer_bbox = draw.textbbox((0, 0), footer, font=footer_font)
    footer_w = footer_bbox[2] - footer_bbox[0]
    draw.text(((W - footer_w) / 2, H - 96), footer, font=footer_font, fill=(124, 124, 132))

    img.convert("RGB").save(out_path, quality=94)
    print(out_path)


if __name__ == "__main__":
    main()
