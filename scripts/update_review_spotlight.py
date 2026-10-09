#!/usr/bin/env python3

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BLOG_DIR = ROOT / "blog"
HOMEPAGE = ROOT / "index.html"
MAX_CARDS = 20


@dataclass(order=True)
class ReviewCard:
    published: date
    href: str
    title: str
    rating: str
    summary: str


def strip_tags(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", value)
    return html.unescape(re.sub(r"\s+", " ", without_tags)).strip()


def extract(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


def extract_title(text: str) -> str | None:
    raw_title = extract(r"<title>(.*?)</title>", text)
    if not raw_title:
        return None

    cleaned = html.unescape(raw_title)
    cleaned = re.sub(r"\s*\|\s*MyMovieJam\s*$", "", cleaned)
    cleaned = re.split(r"\s+[–—-]\s+", cleaned, maxsplit=1)[0].strip()
    return cleaned


def extract_rating(text: str) -> str | None:
    rating = extract(r'<div class="rating-card">\s*<strong>(.*?)</strong>', text)
    if not rating:
        return None
    return strip_tags(rating)


def extract_summary(text: str) -> str:
    quick_take = extract(r'<div class="quick-take">\s*<p>(.*?)</p>', text)
    if quick_take:
        summary = strip_tags(quick_take)
        summary = re.sub(r"^MyMovieJam verdict:\s*", "", summary, flags=re.IGNORECASE)
        return summary

    meta_description = extract(r'<meta\s+name="description"\s+content="(.*?)"\s*/?>', text)
    return html.unescape(meta_description or "Blunt verdicts, audience-first fit guidance, and a visible rating before you commit.")


def extract_date(text: str) -> date | None:
    raw_date = extract(r'<meta\s+property="article:published_time"\s+content="([0-9]{4}-[0-9]{2}-[0-9]{2})"', text)
    if not raw_date:
        raw_date = extract(r'"datePublished"\s*:\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"', text)
    return date.fromisoformat(raw_date) if raw_date else None


def is_review_post(text: str) -> bool:
    return bool(re.search(r'"@type"\s*:\s*"Review"|"@type":"Review"', text))


def build_card(review: ReviewCard) -> str:
    title = html.escape(review.title)
    rating = html.escape(review.rating)
    summary = html.escape(review.summary)
    return (
        f'                <a class="review-spotlight-card" href="{review.href}">\n'
        f'                    <strong>{title}</strong>\n'
        f'                    <div class="review-spotlight-rating">Rating: {rating}</div>\n'
        f'                    <p>{summary}</p>\n'
        f'                    <span>Read the review →</span>\n'
        f'                </a>'
    )


def load_reviews() -> list[ReviewCard]:
    reviews: list[ReviewCard] = []
    for article_path in sorted(BLOG_DIR.glob("*/index.html")):
        text = article_path.read_text(encoding="utf-8")
        if not is_review_post(text):
            continue

        published = extract_date(text)
        title = extract_title(text)
        rating = extract_rating(text)
        if not (published and title and rating):
            continue

        href = "/" + article_path.parent.relative_to(ROOT).as_posix() + "/"
        summary = extract_summary(text)
        reviews.append(
            ReviewCard(
                published=published,
                href=href,
                title=title,
                rating=rating,
                summary=summary,
            )
        )

    reviews.sort(key=lambda review: (review.published, review.href), reverse=True)
    return reviews[:MAX_CARDS]


def update_homepage(cards_markup: str) -> None:
    homepage = HOMEPAGE.read_text(encoding="utf-8")
    pattern = re.compile(
        r'(<section class="section-block review-spotlight".*?<div class="review-spotlight-grid">\n)(.*?)(\n\s*</div>\n\s*</section>)',
        re.DOTALL,
    )

    updated, count = pattern.subn(rf'\1{cards_markup}\3', homepage, count=1)
    if count != 1:
        raise RuntimeError("Could not find the review spotlight grid in index.html")

    HOMEPAGE.write_text(updated, encoding="utf-8")


def main() -> None:
    reviews = load_reviews()
    if not reviews:
        raise RuntimeError("No review posts found to populate the homepage spotlight")

    cards_markup = "\n".join(build_card(review) for review in reviews)
    update_homepage(cards_markup)


if __name__ == "__main__":
    main()
