# Daily MyMovieJam Blog Publishing Prompt

You are publishing exactly **one** new MyMovieJam blog post from the CSV-driven pipeline.

## Goal

Create a daily post that is easy to find and feels like a real MyMovieJam article:
- strong viral hook
- opinionated audience-first voice
- honest recommendations only
- explicit fit for one of the four strategic search clusters
- clear WhatsApp CTA
- visual/theme consistency with existing MyMovieJam pages
- same vibe as the current MyMovieJam blog, not a new editorial voice

## Strategic lane priority

Default to topics that strengthen one of these MyMovieJam search clusters:
1. **Honest movie reviews** — “Should I watch X?”, “worth watching or skip?”, blunt verdict pages
2. **Decision-help queries** — “what to watch tonight”, platform-specific picks, mood-based lists
3. **Similarity / fit queries** — “movies like Interstellar”, “if I liked X what should I watch”
4. **Audience-first recommendation pages** — who should watch / who should skip, no fake positivity

If a brief does not clearly support one of these clusters, reshape the angle so it does. Prefer fit, honesty, and decision-help over generic entertainment blogging.

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
   - This is the **default blog image generator** now.
   - Keep using the latest dark, high-contrast MyMovieJam hook-style look from `scripts/blog_pipeline_hero.py`.
   - Do not revert to the older softer blog-card look unless Milind explicitly asks.
7. Update `blog/index.html` so the new post appears in the featured/latest area if appropriate and also inside the post grid.
8. Update `sitemap.xml` with the new URL and `lastmod` date.
9. Add 2-4 relevant internal links inside the article.
10. For timely movie-specific review pages, research current audience pulse with live web search before writing.
    - Use at least 1 official source (for example Netflix, Tudum, studio, or platform page)
    - Use at least 1 community signal source when available (for example Reddit, X/Twitter reactions, or a reputable article summarizing social chatter)
    - If the title has real chatter, add a short “what viewers are actually saying” / internet-pulse section instead of relying only on your own framing
11. Include:
   - title/meta description/keywords (see Required publishing rules #2)
   - OG + Twitter tags
   - Article schema with the Person author (rule #1)
   - FAQ schema
   - visible trust signal when relevant (for example: clear byline, rating logic, or link path to /editorial-policy/ or /how-we-rate/)
   - quick picks section
   - strong CTA card at the end
12. After files look correct, mark the brief as published:
   ```bash
   python3 scripts/blog_pipeline_selector.py publish --config automation/blog-pipeline/config.json --brief automation/blog-pipeline/next_brief.json
   ```
13. Commit and push:
   ```bash
   git add blog/index.html sitemap.xml blog/images blog/*/index.html automation/blog-pipeline/state.json automation/blog-pipeline/next_brief.json
   git commit -m "Add daily MyMovieJam blog: <slug>"
   git push origin main
   ```


## Required publishing rules (added 2026-10-01)

These are mandatory for every post. Check each one before committing.

1. **Author is always Milind Patil, as a Person.** In every Article, BlogPosting, Review and HowTo JSON-LD block, use exactly:
   `"author":{"@type":"Person","@id":"https://mymoviejam.com/about/#milind-patil","name":"Milind Patil","url":"https://mymoviejam.com/about/"}`
   - Show a visible byline: `By <a href="/about/">Milind Patil</a>`.
   - Never use "MovieJam Crew", "MyMovieJam" or any Organization as the author. The Organization stays only in `publisher`.
   - Set `<meta property="article:author" content="Milind Patil" />`.
2. **Real meta description.** 140–160 characters, a specific one-line pitch for the post. Never just "MyMovieJam" or the site name. `og:description` and `twitter:description` must match it.
   - Escape apostrophes and quotes properly (use `&#39;`/`’` or double-quoted attributes) so the content attribute is not cut off at the first apostrophe.
3. **Scores must match everywhere.** If the post gives a MyMovieJam score:
   - The JSON-LD `reviewRating.ratingValue` must equal the visible score (not IMDb, RT or any audience number shown on the page).
   - If `/movie-ratings/<slug>/` exists for the title, link to it from the post, and make sure the card score equals the blog score. If they differ, the blog score wins: update `data/movies_series_master.csv` / the card, and note it in the commit message.
   - Add the post to the card's "Full review" link (rating-card back-link) when a card exists.
4. **Correct item type.** `itemReviewed` must be `TVSeries` for series, miniseries and seasons, and `Movie` only for films. Check before writing.
5. **No SEO/strategy wording in reader-facing copy.** Do not write "SEO", "search intent", "query", "cluster", "layer", "strategy", "template", "answer engines" or "Google should see…" in visible text. The search clusters in this file are for planning only.
6. **Ping IndexNow after the push succeeds:**
   ```bash
   python3 scripts/indexnow_ping.py https://mymoviejam.com/blog/<slug>/ https://mymoviejam.com/blog/ https://mymoviejam.com/sitemap.xml
   ```
   Include any rating-card URL you changed. Report the HTTP status in your success note.

## Transparency rule

Where it fits naturally, reinforce the site’s trust layer:
- use clear bylines and honest caveat language
- prefer explicit uncertainty over fake precision
- support review/recommendation pages with links to `/editorial-policy/`, `/how-we-rate/`, or relevant hub pages when that improves reader trust

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
If everything succeeds, reply with a concise success note including the slug, commit hash and IndexNow HTTP status.
If anything fails, reply with the blocker only.
