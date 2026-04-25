# Daily MyMovieJam Blog Publishing Prompt

You are publishing exactly **one** new MyMovieJam blog post from the CSV-driven pipeline.

## Goal

Create a daily SEO-optimized post that feels like a real MyMovieJam article:
- strong viral hook
- opinionated audience-first voice
- honest recommendations only
- clear WhatsApp CTA
- visual/theme consistency with existing MyMovieJam pages
- same vibe as the current MyMovieJam blog, not a new editorial voice

## Inputs

- pipeline config: `automation/blog-pipeline/config.json`
- pipeline state: `automation/blog-pipeline/state.json`
- source CSV: `data/blog_mymoviejam_enriched.csv`
- next brief: `automation/blog-pipeline/next_brief.json`
- reference pages:
  - `blog/index.html`
  - `blog/best-animated-netflix-shows-for-stranger-things-fans/index.html`
  - `blog/stranger-things-tales-from-85-review/index.html`
  - `blog/how-to-get-custom-movie-recs-on-whatsapp/index.html`

## Required workflow

1. Generate the next brief fresh:
   ```bash
   python3 scripts/blog_pipeline_selector.py next --config automation/blog-pipeline/config.json --out automation/blog-pipeline/next_brief.json
   ```
2. Read the brief and the reference pages.
3. Write a **real HTML article** under `blog/<slug>/index.html` using the MyMovieJam blog theme.
4. Use the selected titles from the brief. Do not pretend to have seen things you clearly have not. You can still sound opinionated by being specific about the audience fit, energy, binge-worthiness, and likely experience.
5. If the selected list mixes films and series, say so. Do **not** mislabel all of them as movies.
6. Create a matching hero image locally with:
   ```bash
   '/Users/milinaire/.openclaw/venvs/tweetx/bin/python' scripts/blog_pipeline_hero.py --title "<headline>" --eyebrow "<eyebrow>" --subtitle "<subtitle>" --out "blog/images/<image-file>.jpg"
   ```
7. Update `blog/index.html` so the new post appears in the featured/latest area if appropriate and also inside the post grid.
8. Update `sitemap.xml` with the new URL and `lastmod` date.
9. Add 2-4 relevant internal links inside the article.
10. Include:
   - title/meta description/keywords
   - OG + Twitter tags
   - Article schema
   - FAQ schema
   - quick picks section
   - strong CTA card at the end
11. After files look correct, mark the brief as published:
   ```bash
   python3 scripts/blog_pipeline_selector.py publish --config automation/blog-pipeline/config.json --brief automation/blog-pipeline/next_brief.json
   ```
12. Commit and push:
   ```bash
   git add blog/index.html sitemap.xml blog/images blog/*/index.html automation/blog-pipeline/state.json automation/blog-pipeline/next_brief.json
   git commit -m "Add daily MyMovieJam blog: <slug>"
   git push origin main
   ```

## Voice rules

- Match the current MyMovieJam blog voice: sharp, warm, audience-first, scannable, and a little opinionated.
- Sound like a smart viewer with taste.
- Be honest, not fake-hyped.
- Prefer lines like “this is the one to start with”, “this one is messy but fun”, “this one is better than its marketing”, “this one only works if you want pure comfort”.
- Keep the writing punchy and scannable.
- Avoid generic AI phrasing and plot-summary sludge.
- Do not suddenly become more aggressive, slangy, or sensational than the existing published MyMovieJam posts.

## Safety rules

- Do not invent streaming availability beyond the CSV.
- Do not invent cast, director, awards, or critic scores.
- If unsure, make the recommendation narrower instead of making up facts.
- If publish steps fail, do not mark the brief as published.

## Success condition

At the end, the post is live in the repo, pushed to `main`, and the state file reflects the used titles.
If everything succeeds, reply with a concise success note including the slug and commit hash.
If anything fails, reply with the blocker only.
