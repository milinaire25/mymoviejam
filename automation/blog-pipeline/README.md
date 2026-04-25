# MyMovieJam Daily Blog Pipeline

This pipeline turns `data/blog_mymoviejam_enriched.csv` into one publishable MyMovieJam article per day.

## What it does

1. Picks the next unused cluster of titles from the CSV.
2. Rotates themes automatically:
   - best `{genre}` picks from `{year}`
   - best `{genre}` picks on `{platform}`
   - best `{platform}` `{genre}` picks from `{year}`
   - evergreen `{genre}` picks
3. Writes a brief to `automation/blog-pipeline/next_brief.json`.
4. A daily agent reads that brief, writes the actual SEO article in the MyMovieJam site theme, creates a hero image, updates `blog/index.html` + `sitemap.xml`, commits, pushes, and then marks the titles as used.

## Files

- `config.json` — pipeline settings
- `state.json` — published slugs, used titles, rotation pointer
- `DAILY_AGENT_PROMPT.md` — publishing instructions for the daily agent
- `next_brief.json` — the current dry-run / next post brief
- `../../scripts/blog_pipeline_selector.py` — selects the next topic cluster
- `../../scripts/blog_pipeline_hero.py` — creates a branded local hero image

## Manual dry run

```bash
python3 scripts/blog_pipeline_selector.py next \
  --config automation/blog-pipeline/config.json \
  --out automation/blog-pipeline/next_brief.json
```

## Mark a post as published

```bash
python3 scripts/blog_pipeline_selector.py publish \
  --config automation/blog-pipeline/config.json \
  --brief automation/blog-pipeline/next_brief.json
```

## Notes

- The selector avoids reusing titles already marked in `state.json`.
- It prefers recent years (2026, 2025, 2024, 2023) when possible.
- It does **not** force the article to call everything a movie; the writing agent should tell the truth if a list mixes films and series.
- If a post fails before push, do not mark it as published.
