Discover Your Next Favorite Movie in Seconds!
AI-powered movie picks, recommended by real people, right on WhatsApp!

## Site rules and tools

- No viewer, vote, rating or review counts anywhere in site copy. Check with `python3 scripts/lint_counts.py` (exit code 1 if it finds one). This is a manual check only and is not part of the Netlify build, so it cannot fail a deploy.
- `python3 scripts/build_geo_pages.py` rebuilds `/best/` and `/data/` from the rating cards under `movie-ratings/`. Run it after adding or changing a card.
- Shared site styles (header, WhatsApp bar, score box, focus ring) live in `assets/mmj-ui.css`. The header and WhatsApp bar markup is repeated in each page.
- The `/movie-ratings/` index page is not produced by a script in this repo. After adding a rating card, add its row to that page by hand, or it will be missing from the index.
