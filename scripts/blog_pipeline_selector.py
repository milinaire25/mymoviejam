#!/usr/bin/env python3
import argparse
import csv
import json
import math
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def primary_genre(raw: str) -> str:
    if not raw:
        return "Unknown"
    first = re.split(r"[/,]", raw)[0].strip()
    return first or "Unknown"


def parse_platforms(raw: str):
    if not raw:
        return []
    return [p.strip() for p in raw.split(",") if p.strip()]


def parse_year(raw: str):
    try:
        return int(raw)
    except Exception:
        return None


def load_rows(csv_path: Path):
    rows = []
    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            title = (row.get("title") or "").strip()
            if not title:
                continue
            genre = (row.get("genre") or "").strip()
            ott = (row.get("ott_platform") or "").strip()
            year = parse_year((row.get("year_of_release") or "").strip())
            description = (row.get("description") or "").strip()
            rows.append({
                "id": (row.get("id") or "").strip(),
                "title": title,
                "genre": genre,
                "primary_genre": primary_genre(genre),
                "ott_platform": ott,
                "platforms": parse_platforms(ott),
                "year_of_release": year,
                "description": description,
            })
    return rows


def get_existing_slugs(repo_root: Path):
    blog_dir = repo_root / "blog"
    if not blog_dir.exists():
        return set()
    return {p.name for p in blog_dir.iterdir() if p.is_dir() and p.name != "images"}


def score_recent_year(year, preferred_years):
    if year is None:
        return -2
    if year in preferred_years:
        return len(preferred_years) - preferred_years.index(year)
    return 1 if year >= 2020 else 0


def choose_titles(candidates, target_titles):
    def sort_key(r):
        return (
            -(r["year_of_release"] or 0),
            -len(r.get("platforms", [])),
            r["title"].lower(),
        )
    ordered = sorted(candidates, key=sort_key)
    return ordered[:target_titles]


def build_groups(rows, state, config):
    published_titles = {t.lower() for t in state.get("published_titles", [])}
    eligible = [r for r in rows if r["title"].lower() not in published_titles and r["primary_genre"] not in set(config.get("genre_blacklist", []))]
    min_titles = config.get("min_titles_per_post", 5)
    target_titles = config.get("target_titles_per_post", 7)
    preferred_years = config.get("preferred_years", [])

    groups = defaultdict(list)

    for row in eligible:
        genre = row["primary_genre"]
        year = row["year_of_release"]
        platforms = row["platforms"] or [""]
        if year:
            groups[("year_genre", genre, year)].append(row)
        for platform in platforms:
            if platform:
                groups[("platform_genre", genre, platform)].append(row)
            if platform and year:
                groups[("year_platform_genre", genre, year, platform)].append(row)
        groups[("evergreen_genre", genre)].append(row)

    candidates = []
    for key, items in groups.items():
        family = key[0]
        if len(items) < min_titles:
            continue
        year = None
        platform = None
        genre = None
        if family == "year_genre":
            _, genre, year = key
        elif family == "platform_genre":
            _, genre, platform = key
        elif family == "year_platform_genre":
            _, genre, year, platform = key
        elif family == "evergreen_genre":
            _, genre = key

        chosen = choose_titles(items, target_titles)
        count = len(items)
        year_score = score_recent_year(year, preferred_years)
        platform_bonus = 1 if platform else 0
        score = count * 4 + year_score * 3 + platform_bonus
        candidates.append({
            "family": family,
            "genre": genre,
            "year": year,
            "platform": platform,
            "count": count,
            "score": score,
            "selected_titles": chosen,
        })
    return sorted(candidates, key=lambda c: (-c["score"], -c["count"], c["genre"], str(c.get("year") or ""), c.get("platform") or ""))


def headline_for(candidate):
    genre = candidate["genre"]
    year = candidate.get("year")
    platform = candidate.get("platform")
    count = len(candidate["selected_titles"])
    if candidate["family"] == "year_genre":
        return f"Best {genre.lower()} picks from {year}: {count} titles actually worth your time"
    if candidate["family"] == "platform_genre":
        return f"Best {genre.lower()} picks on {platform} right now: {count} titles worth starting first"
    if candidate["family"] == "year_platform_genre":
        return f"Best {platform} {genre.lower()} picks from {year}: {count} titles to queue first"
    return f"Best {genre.lower()} picks to stream when you want something better than another lazy scroll"


def keyword_for(candidate):
    genre = candidate["genre"].lower()
    year = candidate.get("year")
    platform = candidate.get("platform")
    if candidate["family"] == "year_genre":
        return f"best {genre} movies and shows in {year}"
    if candidate["family"] == "platform_genre":
        return f"best {genre} picks on {platform.lower()}"
    if candidate["family"] == "year_platform_genre":
        return f"best {genre} picks on {platform.lower()} in {year}"
    return f"best {genre} picks to stream"


def subtitle_for(candidate):
    titles = [r["title"] for r in candidate["selected_titles"][:3]]
    genre = candidate["genre"]
    if len(titles) >= 3:
        return f"Featuring {titles[0]}, {titles[1]}, and {titles[2]} — plus more {genre.lower()} picks that deserve real attention."
    return f"A sharper, audience-first MyMovieJam guide to {genre.lower()} picks that are actually worth queuing."


def description_for(candidate):
    genre = candidate["genre"].lower()
    year = candidate.get("year")
    platform = candidate.get("platform")
    if candidate["family"] == "year_genre":
        return f"Looking for the best {genre} picks from {year}? Here are the titles that actually deserve your time, with clear audience-first takes and quick watch-fit guidance."
    if candidate["family"] == "platform_genre":
        return f"Need the best {genre} picks on {platform}? These are the titles worth starting first if you want something better than random browsing."
    if candidate["family"] == "year_platform_genre":
        return f"Looking for the best {genre} picks on {platform} from {year}? Here are the strongest titles to queue first, with honest MyMovieJam-style guidance."
    return f"Need better {genre} picks for tonight? Here are the titles actually worth starting first, without the usual generic streaming-list fluff."


def tags_for(candidate):
    parts = []
    if candidate.get("platform"):
        parts.append(candidate["platform"])
    parts.append(candidate["genre"])
    if candidate.get("year"):
        parts.append(str(candidate["year"]))
    parts.append("Curated list")
    return parts


def build_brief(repo_root: Path, config, state, candidate, existing_slugs):
    headline = headline_for(candidate)
    keyword = keyword_for(candidate)
    slug_base = slugify(keyword)
    slug = slug_base
    suffix = 2
    while slug in existing_slugs or slug in {p.get('slug') for p in state.get('published_posts', [])}:
        slug = f"{slug_base}-{suffix}"
        suffix += 1

    today = datetime.now().strftime("%Y-%m-%d")
    readable_date = datetime.now().strftime("%B %-d, %Y") if hasattr(datetime.now(), 'strftime') else today
    image_file = f"{slug}.jpg"
    brief = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "date": today,
        "readable_date": readable_date,
        "family": candidate["family"],
        "headline": headline,
        "slug": slug,
        "primary_keyword": keyword,
        "meta_description": description_for(candidate),
        "eyebrow": f"Curated List · {readable_date}",
        "subtitle": subtitle_for(candidate),
        "tags": tags_for(candidate),
        "genre": candidate["genre"],
        "platform": candidate.get("platform"),
        "year": candidate.get("year"),
        "hero_image": {
            "file": image_file,
            "path": f"blog/images/{image_file}",
            "web_path": f"/blog/images/{image_file}",
            "eyebrow": candidate["genre"] + (f" · {candidate['platform']}" if candidate.get("platform") else ""),
            "title": headline,
            "subtitle": subtitle_for(candidate),
        },
        "selected_titles": candidate["selected_titles"],
        "cta": config.get("cta", {}),
        "internal_link_defaults": config.get("internal_link_defaults", []),
        "style_rules": config.get("style_rules", []),
        "notes_for_writer": [
            "Tell the truth if the list mixes films and series.",
            "Write as a sharp viewer with taste, not a neutral database.",
            "Pick clear winners, easy starters, and mood-based recommendations.",
            "Use a clear WhatsApp CTA at the end."
        ]
    }
    return brief


def select_next(repo_root: Path, config, state):
    rows = load_rows(repo_root / config["csv_path"])
    existing_slugs = get_existing_slugs(repo_root)
    candidates = build_groups(rows, state, config)
    rotation = config.get("theme_rotation", []) or ["year_genre", "platform_genre", "year_platform_genre", "evergreen_genre"]
    start_idx = state.get("next_theme_index", 0) % len(rotation)

    for offset in range(len(rotation)):
        family = rotation[(start_idx + offset) % len(rotation)]
        filtered = [c for c in candidates if c["family"] == family]
        if filtered:
            return build_brief(repo_root, config, state, filtered[0], existing_slugs), (start_idx + offset) % len(rotation)

    if candidates:
        return build_brief(repo_root, config, state, candidates[0], existing_slugs), 0
    raise SystemExit("No eligible candidate groups left. Either lower min_titles_per_post or allow title reuse.")


def cmd_next(args):
    repo_root = Path(args.repo).resolve()
    config = load_json(repo_root / args.config, {})
    state = load_json(repo_root / config["state_path"], {
        "published_posts": [],
        "published_titles": [],
        "theme_history": [],
        "next_theme_index": 0,
        "last_generated_at": None,
    })
    brief, theme_idx = select_next(repo_root, config, state)
    state["last_generated_at"] = brief["generated_at"]
    state["last_generated_slug"] = brief["slug"]
    state["last_generated_family"] = brief["family"]
    state["last_theme_index_used"] = theme_idx
    save_json(repo_root / config["state_path"], state)
    out_path = repo_root / (args.out or config["brief_output_path"])
    save_json(out_path, brief)
    print(json.dumps({
        "slug": brief["slug"],
        "headline": brief["headline"],
        "family": brief["family"],
        "title_count": len(brief["selected_titles"]),
        "out": str(out_path)
    }, indent=2))


def cmd_publish(args):
    repo_root = Path(args.repo).resolve()
    config = load_json(repo_root / args.config, {})
    state_path = repo_root / config["state_path"]
    state = load_json(state_path, {
        "published_posts": [],
        "published_titles": [],
        "theme_history": [],
        "next_theme_index": 0,
        "last_generated_at": None,
    })
    brief = load_json(repo_root / args.brief, None)
    if not brief:
        raise SystemExit("Brief file missing or empty.")

    slug = brief["slug"]
    if slug not in {p.get("slug") for p in state.get("published_posts", [])}:
        state.setdefault("published_posts", []).append({
            "slug": slug,
            "headline": brief.get("headline"),
            "family": brief.get("family"),
            "published_at": datetime.now().isoformat(timespec="seconds"),
        })
    used = {t.lower() for t in state.get("published_titles", [])}
    for row in brief.get("selected_titles", []):
        title = row["title"]
        if title.lower() not in used:
            state.setdefault("published_titles", []).append(title)
            used.add(title.lower())
    family = brief.get("family")
    state.setdefault("theme_history", []).append({
        "family": family,
        "slug": slug,
        "published_at": datetime.now().isoformat(timespec="seconds"),
    })
    rotation = config.get("theme_rotation", []) or ["year_genre", "platform_genre", "year_platform_genre", "evergreen_genre"]
    if family in rotation:
        state["next_theme_index"] = (rotation.index(family) + 1) % len(rotation)
    save_json(state_path, state)
    print(json.dumps({
        "published_slug": slug,
        "titles_marked": len(brief.get("selected_titles", [])),
        "next_theme_index": state.get("next_theme_index", 0)
    }, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Select and track MyMovieJam daily blog topics.")
    parser.add_argument("command", choices=["next", "publish"])
    parser.add_argument("--repo", default=".")
    parser.add_argument("--config", default="automation/blog-pipeline/config.json")
    parser.add_argument("--out")
    parser.add_argument("--brief", default="automation/blog-pipeline/next_brief.json")
    args = parser.parse_args()

    if args.command == "next":
        cmd_next(args)
    else:
        cmd_publish(args)


if __name__ == "__main__":
    main()
