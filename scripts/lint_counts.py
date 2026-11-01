#!/usr/bin/env python3
"""Fail if site copy shows viewer, vote, rating or review counts.

MyMovieJam never publishes audience counts (see /how-we-rate/). This lint scans
the site's content files for phrases such as "8,800 votes", "17k ratings" or
"24 people" and exits 1 if it finds any.

Usage (from repo root):  python3 scripts/lint_counts.py
Exit code: 0 = clean, 1 = matches found.

Standalone check only: it is NOT part of the Netlify build, so it can never fail a
deploy. Run it by hand or in a pre-commit hook. If a match is a false positive
(for example "5 people in the cast"), reword the line, or add the marker
`lint-counts-ignore` somewhere on that same line (an HTML comment is fine).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTS = {".html", ".md", ".txt", ".csv", ".json", ".xml"}
SKIP_DIRS = {".git", "node_modules", "scripts", "assets"}
NOUNS = r"(votes|reviews|ratings|viewers|people)"
# plain numbers ("8,800 votes") and k/M shorthand ("17k ratings", "2.1M viewers")
PATTERN = re.compile(
    r"\d[\d,]*\s*" + NOUNS + r"|\d[\d,.]*\s?[kKmM]\+?\s*" + NOUNS,
    re.IGNORECASE,
)
IGNORE = "lint-counts-ignore"


def main() -> int:
    hits = 0
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if not path.is_file() or path.suffix.lower() not in EXTS:
            continue
        if any(part in SKIP_DIRS for part in rel.parts[:-1]) or rel.name == "README.md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if IGNORE in line:
                continue
            for m in PATTERN.finditer(line):
                hits += 1
                start = max(0, m.start() - 40)
                print(f"{rel}:{n}: ...{line[start:m.end() + 30].strip()}...")
    if hits:
        print(f"\nlint_counts: {hits} count claim(s) found. Reword them (we do not publish counts).")
        return 1
    print("lint_counts: OK, no viewer/vote/review counts found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
