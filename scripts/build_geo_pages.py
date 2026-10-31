#!/usr/bin/env python3
"""Build the /best/ answer pages and the /data/ open ratings dataset.

Source of truth: the rating cards under movie-ratings/<slug>/index.html (these
carry the exact score shown on the site, and blog-review scores where a blog
review exists). Nothing is invented: titles, scores, platforms, years, genres,
Watch if / Skip if lines are all read from those cards.

Usage (from repo root):  python3 scripts/build_geo_pages.py
Writes: best/**, data/index.html, data/mymoviejam-ratings.csv/.json
"""
from __future__ import annotations

import csv
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://mymoviejam.com"
UPDATED_ISO = "2026-10-31"
UPDATED_HUMAN = "Oct 31, 2026"
SHARE_IMG = f"{SITE}/blog/images/mymoviejam-share-2026-10-v2.jpg"
SHARE_ALT = ("MyMovieJam share card: Real opinions. Rated fast. Honest scores from people who actually "
             "watched, next to a Pluribus rating card scoring 8.8 Great with Watch if and Skip if lines.")
WA_NAV = "https://api.whatsapp.com/send?phone=6581615926&amp;text=Hi%20MovieJam,%20What%20should%20I%20watch%20tonight?"
WA_PICKS = "https://api.whatsapp.com/send?phone=6581615926&text=Hi%20MovieJam,%20give%20me%203%20movie%20or%20show%20picks"
WA_TONIGHT = "https://api.whatsapp.com/send?phone=6581615926&text=Hi%20MovieJam,%20What%20should%20I%20watch%20tonight?"
METHOD = ("Scores come from a panel of friends and family who watched each title, cross-checked against "
          "sentiment on X, with Milind Patil making the final call.")
BANDS_TXT = "8–10 Great, 7–7.9 Good, 5–6.9 Mixed, below 5 Skip"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def band(score: float) -> str:
    return "Great" if score >= 8 else "Good" if score >= 7 else "Mixed" if score >= 5 else "Skip"


# ---------------------------------------------------------------- catalog
def parse_catalog() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for d in sorted((ROOT / "movie-ratings").iterdir()):
        p = d / "index.html"
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")

        def g(rx: str):
            m = re.search(rx, t, re.S)
            return html.unescape(m.group(1).strip()) if m else None

        meta = g(r'<div class="meta">(.*?)</div>') or ""
        parts = [x.strip() for x in meta.split(" · ")]
        # "<type> · [platform ·] <genre> · [year ·] <editor/review credit>"
        platform = g(r"<li>Platform: (.*?)</li>") or ""
        year = g(r"<li>Year: (.*?)</li>") or ""
        mid = [x for x in parts[1:-1] if x != platform and not re.fullmatch(r"\d{4}", x)]
        genre = " · ".join(mid)
        score_s = g(r'<div class="rating">([\d.]+)')
        typ = g(r"<li>Type: (.*?)</li>") or parts[0]
        out[d.name] = dict(
            slug=d.name,
            title=g(r"<h1>(.*?)</h1>"),
            score_s=score_s,
            score=float(score_s),
            platform=platform,
            genre=genre,
            year=year,
            type="Film" if typ == "Movie" else typ,
            watch_if=g(r'<h3>Watch if</h3><p>(.*?)</p>'),
            skip_if=g(r'<h3>Skip if</h3><p>(.*?)</p>'),
            url=f"{SITE}/movie-ratings/{d.name}/",
        )
        out[d.name]["band"] = band(out[d.name]["score"])
    return out


# ---------------------------------------------------------------- dataset
FIELDS = ["title", "year", "type", "genre", "platform", "score", "band", "watch_if", "skip_if", "rating_page_url"]


def dataset_rows(cat):
    rows = []
    for r in sorted(cat.values(), key=lambda r: (-r["score"], r["title"].lower())):
        rows.append({
            "title": r["title"], "year": r["year"], "type": r["type"], "genre": r["genre"],
            "platform": r["platform"], "score": r["score_s"], "band": r["band"],
            "watch_if": r["watch_if"], "skip_if": r["skip_if"], "rating_page_url": r["url"],
        })
    return rows


def write_dataset(cat):
    rows = dataset_rows(cat)
    d = ROOT / "data"
    d.mkdir(exist_ok=True)
    with open(d / "mymoviejam-ratings.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    jrows = []
    for r in rows:
        j = dict(r)
        j["score"] = float(r["score"])
        j["year"] = int(r["year"]) if str(r["year"]).isdigit() else (r["year"] or None)
        jrows.append(j)
    doc = {
        "dataset": "MyMovieJam Ratings Dataset",
        "publisher": "MyMovieJam (mymoviejam.com)",
        "url": f"{SITE}/data/",
        "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": "MyMovieJam (mymoviejam.com)",
        "updated": UPDATED_ISO,
        "method": METHOD + " Bands: " + BANDS_TXT + ". See " + SITE + "/how-we-rate/",
        "fields": FIELDS,
        "ratings": jrows,
    }
    (d / "mymoviejam-ratings.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return rows


# ---------------------------------------------------------------- html shell
def css() -> str:
    ref = (ROOT / "movie-ratings/operation-safed-sagar/index.html").read_text(encoding="utf-8")
    base = re.search(r"<style>\n(.*?)</style>", ref, re.S).group(1)
    extra = """
.answer{font-size:20px;line-height:1.45;font-weight:500;letter-spacing:-.015em;margin:8px 0 14px}
.updated{font-size:14px;color:var(--secondary);margin-bottom:28px}
.picks{list-style:none;padding:0;margin:0 0 28px}
.pick{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:14px}
.pick-head{display:flex;gap:14px;align-items:center}
.rank{width:36px;height:36px;border-radius:50%;background:var(--text);color:#fff;font-weight:700;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.pick-title{flex:1;min-width:0}
.pick-title h2{font-size:20px;letter-spacing:-.02em;line-height:1.2}
.pick-title h2 a{text-decoration:none}
.pick-title h2 a:hover{text-decoration:underline}
.pick .meta{margin-top:4px;font-size:14px}
.pick .rating{font-size:22px;padding:8px 14px}
.band{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:4px 10px;border-radius:980px}
.band-great{background:rgba(37,211,102,.14);color:var(--wa-dark)}
.band-good{background:rgba(0,122,255,.1);color:#0a5bc4}
.band-mixed{background:rgba(255,159,10,.16);color:#9a5b00}
.pick .split{margin:16px 0 10px}
.pick-link{font-size:14px;font-weight:600;color:var(--secondary);text-decoration:none}
.pick-link:hover{color:var(--text)}
.faq h3{font-size:16px;margin:16px 0 6px}
.faq h3:first-of-type{margin-top:0}
.note{font-size:14px;line-height:1.55;color:var(--secondary);margin:0 0 20px}
.note a{color:inherit;text-decoration:underline}
table.fields{width:100%;border-collapse:collapse;font-size:14px;margin-top:8px}
table.fields th,table.fields td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--border);vertical-align:top}
table.fields th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--secondary)}
pre.sample{background:#f5f5f7;border:1px solid var(--border);border-radius:12px;padding:14px;overflow-x:auto;font-size:13px;line-height:1.5}
.panel p+p{margin-top:10px}
@media(max-width:640px){.pick-head{flex-wrap:wrap}.pick .rating-wrap{align-items:flex-start;width:100%}}
"""
    return base + extra


def jsonld(obj) -> str:
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>"


ORG = {"@type": "Organization", "@id": f"{SITE}/#organization", "name": "MyMovieJam", "url": f"{SITE}/"}
EDITOR = {"@type": "Person", "@id": f"{SITE}/about/#milind-patil", "name": "Milind Patil", "url": f"{SITE}/about/"}


def shell(*, path: str, title: str, desc: str, kicker: str, h1: str, body: str, ld: list, og_type="article") -> str:
    url = f"{SITE}{path}"
    graph = {"@context": "https://schema.org", "@graph": ld}
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}" />
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1" />
<meta name="author" content="Milind Patil" />
<link rel="canonical" href="{url}" />
<meta property="og:type" content="{og_type}" />
<meta property="og:site_name" content="MyMovieJam" />
<meta property="og:title" content="{esc(title)}" />
<meta property="og:description" content="{esc(desc)}" />
<meta property="og:url" content="{url}" />
<meta property="og:image" content="{SHARE_IMG}" />
<meta property="og:image:width" content="1200" />
<meta property="og:image:height" content="630" />
<meta property="og:image:alt" content="{esc(SHARE_ALT)}" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="{esc(title)}" />
<meta name="twitter:description" content="{esc(desc)}" />
<meta name="twitter:image" content="{SHARE_IMG}" />
<meta name="twitter:image:alt" content="{esc(SHARE_ALT)}" />
{jsonld(graph)}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
{css()}</style>
<script async src="https://plausible.io/js/pa--oC4nGgp0K7LQGFneiNaZ.js"></script>
<script>window.plausible=window.plausible||function(){{(plausible.q=plausible.q||[]).push(arguments)}},plausible.init=plausible.init||function(opts){{plausible.o=opts||{{}}}};plausible.init();</script>
</head>
<body>
<header class="site-header"><div class="header-inner">
<a class="logo" href="/"><div class="logo-icon"><svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg></div><span>MyMovieJam</span></a>
<nav><a href="/" class="">Home</a><a href="/movie-reviews/" class="">Reviews</a><a href="/movie-ratings/" class="">Ratings</a><a href="/best/" class="{'active' if path.startswith('/best') else ''}">Best picks</a><a href="/blog/" class="">Blog</a><a href="/pricing.html" class="">Pricing</a><a href="{WA_NAV}" class="wa" target="_blank" rel="noopener">Chat on WhatsApp</a></nav></div></header>
<main class="page">
{body}
  <div class="actions">
    <a class="btn btn-primary" href="{WA_PICKS}" target="_blank" rel="noopener">Get 3 picks on WhatsApp</a>
    <a class="btn btn-secondary" href="/movie-ratings/">Browse all ratings</a>
  </div>
  <div class="cta" style="margin-top:36px">
    <strong style="font-size:20px;letter-spacing:-.02em">Need a tonight shortlist?</strong>
    <p>Mood + platform + who you’re with — three picks on WhatsApp.</p>
    <a href="{WA_TONIGHT}" target="_blank" rel="noopener">Chat on WhatsApp</a>
  </div>
</main>
<footer class="site-foot"><p>© MyMovieJam · MyMovieJam scores, edited by Milind Patil · <a href="/how-we-rate/">How we rate</a> · <a href="/editorial-policy/">Editorial policy</a> · <a href="/data/">Ratings data</a></p></footer>
</body></html>
"""


# ---------------------------------------------------------------- /best pages
def sc(r):  # score as displayed on the rating card
    return r["score_s"]


def pick_html(i: int, r: dict) -> str:
    plat = esc(r["platform"])
    meta = f"{plat} · {esc(r['year'])} · {esc(r['genre'])}"
    return f"""    <li class="pick">
      <div class="pick-head">
        <span class="rank" aria-label="Rank {i}">{i}</span>
        <div class="pick-title"><h2><a href="/movie-ratings/{r['slug']}/">{esc(r['title'])}</a></h2><div class="meta">{meta}</div></div>
        <div class="rating-wrap"><span class="rating-label">MyMovieJam score</span><div class="rating">{sc(r)} <small>/10</small></div><span class="band band-{r['band'].lower()}">{r['band']}</span></div>
      </div>
      <div class="split">
        <div class="pill"><h3>Watch if</h3><p>{esc(r['watch_if'])}</p></div>
        <div class="pill"><h3>Skip if</h3><p>{esc(r['skip_if'])}</p></div>
      </div>
      <a class="pick-link" href="/movie-ratings/{r['slug']}/">Full rating card for {esc(r['title'])} →</a>
    </li>"""


PAGES = [
    dict(
        slug="netflix-thrillers",
        h1="Which Netflix thrillers are actually worth watching?",
        kicker="Netflix · Thrillers · Ranked by MyMovieJam score",
        title="Which Netflix Thrillers Are Worth Watching? Ranked Picks | MyMovieJam",
        desc="The best Netflix thrillers ranked by MyMovieJam score, with Watch if / Skip if for each. Scores from a panel of friends and family who watched, cross-checked against X.",
        slugs=["something-bad-is-going-to-happen", "maharaja", "i-will-find-you", "skyscraper-live", "you",
               "kohra-2", "the-conjuring", "zero-dark-thirty"],
        crumb="Netflix thrillers",
        related=[("/netflix-movie-recommendations/", "Netflix movie recommendations"), ("/what-to-watch-tonight/", "What to watch tonight")],
    ),
    dict(
        slug="prime-video-hidden-gems",
        h1="What are the best hidden gems on Prime Video?",
        kicker="Prime Video · Hidden gems · Ranked by MyMovieJam score",
        title="Best Hidden Gems on Prime Video: Honest Ratings, No Hype | MyMovieJam",
        desc="Prime Video hidden gems ranked by MyMovieJam score, each with an honest Watch if / Skip if. Scores from a panel of friends and family who watched, cross-checked against X.",
        slugs=["made-in-india-a-titan-story", "bandish-bandit", "the-pyramid-scheme", "major", "dupahiya-season-2",
               "young-sherlock", "the-impossible", "dupahiya"],
        crumb="Prime Video hidden gems",
        related=[("/amazon-prime-movie-recommendations/", "Amazon Prime movie recommendations"), ("/what-to-watch-tonight/", "What to watch tonight")],
    ),
    dict(
        slug="great-rated-picks-tonight",
        h1="What should I watch tonight?",
        kicker="Great-rated picks (8+) · Netflix, Prime Video, Apple TV+ and Disney+",
        title="What Should I Watch Tonight? Great-Rated Picks on Netflix, Prime, Apple TV+ | MyMovieJam",
        desc="What to watch tonight: Great-rated (8+) picks across Netflix, Prime Video and Apple TV+, each with Watch if / Skip if. Scores from a panel of friends and family, cross-checked against X.",
        slugs=["the-crash", "made-in-india-a-titan-story", "the-sheep-detectives", "rafa", "pluribus", "small-prophets",
               "margo-s-got-money-troubles", "operation-safed-sagar", "spider-noir"],
        crumb="What to watch tonight",
        related=[("/what-to-watch-tonight/", "More ways to decide tonight"), ("/netflix-movie-recommendations/", "Netflix movie recommendations"),
                 ("/amazon-prime-movie-recommendations/", "Amazon Prime movie recommendations")],
    ),
]


def money(cat, slugs):
    rows = [cat[s] for s in slugs]
    rows.sort(key=lambda r: -r["score"])  # stable: curated order breaks ties
    return rows


def answers(cat, page, rows):
    n = lambda s: cat[s]["title"]
    v = lambda s: cat[s]["score_s"]
    slug = page["slug"]
    if slug == "netflix-thrillers":
        assert all(r["platform"] == "Netflix" for r in rows)
        great = [r for r in rows if r["band"] == "Great"]
        good = [r for r in rows if r["band"] == "Good"]
        lo, hi = min(r["score"] for r in good), max(r["score"] for r in good)
        fmt = lambda x: f"{x:g}"
        return (f"The highest-rated thriller on Netflix in our catalog is {n('something-bad-is-going-to-happen')} at "
                f"{v('something-bad-is-going-to-happen')}/10 (Great), followed by {n('maharaja')} ({v('maharaja')}) and "
                f"{n('i-will-find-you')} ({v('i-will-find-you')}), the {len(great)} Great-rated Netflix thrillers. "
                f"The other {len(good)} score Good ({fmt(lo)}–{fmt(hi)}) and suit specific tastes, so check each Watch if / Skip if line. "
                f"Scores come from a panel of friends and family who watched each title, cross-checked against X sentiment.")
    if slug == "prime-video-hidden-gems":
        assert all(r["platform"] == "Prime Video" for r in rows)
        lo = min(r["score"] for r in rows)
        return (f"Our top Prime Video hidden gem is {n('made-in-india-a-titan-story')} at {v('made-in-india-a-titan-story')}/10 (Great), "
                f"with {n('bandish-bandit')} ({v('bandish-bandit')}) and {n('the-pyramid-scheme')} ({v('the-pyramid-scheme')}) close behind. "
                f"By “hidden gem” we mean a Prime Video title that scores Good or Great with our panel but is not one of the household-name "
                f"headliners; that is an editorial call, not a popularity statistic. Every title below scores {lo:g} or higher.")
    if slug == "great-rated-picks-tonight":
        assert all(r["score"] >= 8 for r in rows)
        return (f"The highest-scoring pick tonight is {n('the-crash')} on Netflix ({v('the-crash')}/10), a true-crime documentary. "
                f"If you want something gentler, try {n('the-sheep-detectives')} on Prime Video ({v('the-sheep-detectives')}/10) or "
                f"{n('small-prophets')} on Apple TV+ ({v('small-prophets')}/10). "
                f"Every pick below is Great (8–10) with our panel of friends and family, and no Disney+ title in our catalog reaches Great, so none is listed.")
    raise KeyError(slug)


def build_best(cat):
    results = []
    for page in PAGES:
        rows = money(cat, page["slugs"])
        ans = answers(cat, page, rows)
        path = f"/best/{page['slug']}/"
        url = f"{SITE}{path}"
        faq = [
            (page["h1"], ans),
            ("How are these scores decided?",
             METHOD + " We do not publish viewer or review counts. Details are on our How We Rate page."),
            ("What do the score bands mean?", BANDS_TXT + "."),
        ]
        if page["slug"] == "great-rated-picks-tonight":
            dis = max((r for r in cat.values() if r["platform"] == "Disney+"), key=lambda r: r["score"])
            faq.append(("Is there a Great-rated Disney+ pick?",
                        f"Not right now. The highest-rated Disney+ title in our catalog is {dis['title']} at {dis['score_s']}/10 ({dis['band']}), "
                        f"so none is listed here."))
        items = "\n".join(pick_html(i, r) for i, r in enumerate(rows, 1))
        faq_html = "\n".join(f"    <h3>{esc(q)}</h3>\n    <p>{esc(a)}</p>" for q, a in faq)
        rel = " · ".join(f'<a href="{u}">{esc(t)}</a>' for u, t in page["related"])
        body = f"""  <a class="back" href="/best/">← All best picks</a>
  <div class="kicker">{esc(page['kicker'])}</div>
  <h1>{esc(page['h1'])}</h1>
  <p class="answer">{esc(ans)}</p>
  <p class="updated">Updated <time datetime="{UPDATED_ISO}">{UPDATED_HUMAN}</time> · Edited by Milind Patil</p>
  <ol class="picks">
{items}
  </ol>
  <div class="panel">
    <h2>How we rate</h2>
    <p>{esc(METHOD)} Bands: {esc(BANDS_TXT)}. Rankings follow the MyMovieJam score shown on each rating card; where Milind has written a blog review, the score in that review is the one used. <a href="/how-we-rate/#mymoviejam-score">How the MyMovieJam score works</a> · <a href="/data/">Download the ratings data</a>.</p>
  </div>
  <div class="panel faq">
    <h2>Quick answers</h2>
{faq_html}
  </div>
  <p class="note">More: {rel}</p>"""
        ld = [
            {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": page["h1"], "description": page["desc"],
             "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO, "inLanguage": "en",
             "isPartOf": {"@type": "WebSite", "name": "MyMovieJam", "url": f"{SITE}/"},
             "author": ORG, "publisher": ORG, "editor": EDITOR,
             "breadcrumb": {"@id": url + "#breadcrumb"}, "mainEntity": {"@id": url + "#list"}},
            {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
                {"@type": "ListItem", "position": 2, "name": "Best picks", "item": f"{SITE}/best/"},
                {"@type": "ListItem", "position": 3, "name": page["crumb"], "item": url}]},
            {"@type": "ItemList", "@id": url + "#list", "name": page["h1"], "itemListOrder": "https://schema.org/ItemListOrderDescending",
             "numberOfItems": len(rows),
             "itemListElement": [{"@type": "ListItem", "position": i, "name": r["title"], "url": r["url"]} for i, r in enumerate(rows, 1)]},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
        ]
        html_out = shell(path=path, title=page["title"], desc=page["desc"], kicker=page["kicker"], h1=page["h1"], body=body, ld=ld)
        d = ROOT / "best" / page["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(html_out, encoding="utf-8")
        results.append((page, rows, ans))
    return results


def build_hub(results):
    path = "/best/"
    url = SITE + path
    cards = "\n".join(
        f"""    <a class="row" href="/best/{p['slug']}/"><div class="score-wrap"><span class="score-label">Top pick</span><div class="score">{sc_}</div></div><div><div class="t">{esc(p['h1'])}</div><div class="s">{esc(p['kicker'])}</div></div><div class="open">Open →</div></a>"""
        for p, rows, _ in results for sc_ in [rows[0]["score_s"]])
    body = f"""  <div class="kicker">Best picks · Answer-first guides</div>
  <h1>What should I watch? Straight answers, ranked.</h1>
  <p class="answer">Each guide answers one question, then ranks titles from our ratings catalog by MyMovieJam score, with a Watch if / Skip if line for every pick. Scores come from a panel of friends and family who watched each title, cross-checked against X sentiment.</p>
  <p class="updated">Updated <time datetime="{UPDATED_ISO}">{UPDATED_HUMAN}</time> · Edited by Milind Patil</p>
  <div id="list">
{cards}
  </div>
  <div class="panel">
    <h2>How we rate</h2>
    <p>{esc(METHOD)} Bands: {esc(BANDS_TXT)}. <a href="/how-we-rate/#mymoviejam-score">How the MyMovieJam score works</a>. Prefer the raw numbers? <a href="/data/">Download the open ratings dataset</a> (CC BY 4.0) or <a href="/movie-ratings/">browse every rating card</a>.</p>
  </div>"""
    title = "Best Movies & Shows to Watch: Ranked Answers | MyMovieJam"
    desc = "Answer-first guides to what to watch on Netflix, Prime Video, Apple TV+ and Disney+, ranked by MyMovieJam score with Watch if / Skip if."
    ld = [
        {"@type": "CollectionPage", "@id": url + "#webpage", "url": url, "name": "Best movies and shows to watch", "description": desc,
         "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO, "inLanguage": "en",
         "isPartOf": {"@type": "WebSite", "name": "MyMovieJam", "url": f"{SITE}/"}, "publisher": ORG, "editor": EDITOR,
         "mainEntity": {"@id": url + "#list"}},
        {"@type": "ItemList", "@id": url + "#list", "name": "MyMovieJam best-picks guides", "numberOfItems": len(results),
         "itemListElement": [{"@type": "ListItem", "position": i, "name": p["h1"], "url": f"{SITE}/best/{p['slug']}/"} for i, (p, _, _) in enumerate(results, 1)]},
    ]
    (ROOT / "best").mkdir(exist_ok=True)
    (ROOT / "best/index.html").write_text(shell(path=path, title=title, desc=desc, kicker="", h1="", body=body, ld=ld, og_type="website"), encoding="utf-8")


# ---------------------------------------------------------------- /data page
def build_data_page(rows):
    path = "/data/"
    url = SITE + path
    csv_url = f"{SITE}/data/mymoviejam-ratings.csv"
    json_url = f"{SITE}/data/mymoviejam-ratings.json"
    sample = next(r for r in rows if r["title"] == "Operation Safed Sagar")
    sample_j = dict(sample)
    sample_j["score"] = float(sample["score"])
    sample_j["year"] = int(sample["year"])
    desc_f = {
        "title": "Title as shown on its rating page.",
        "year": "Release year as shown on the rating page.",
        "type": "Film, Series, Film/Series or as shown on the rating page.",
        "genre": "Genre as shown on the rating page.",
        "platform": "Streaming platform (Netflix, Prime Video, Apple TV+, Disney+, Theatrical). Left blank where we do not track one.",
        "score": "MyMovieJam score out of 10, identical to the score on the rating page (or in the blog review where one exists).",
        "band": "Great (8–10), Good (7–7.9), Mixed (5–6.9) or Skip (below 5).",
        "watch_if": "One-line “Watch if” from the rating page.",
        "skip_if": "One-line “Skip if” from the rating page.",
        "rating_page_url": "Canonical URL of the title’s MyMovieJam rating page.",
    }
    trs = "\n".join(f"        <tr><td><code>{k}</code></td><td>{esc(v)}</td></tr>" for k, v in desc_f.items())
    body = f"""  <div class="kicker">Open data · CC BY 4.0</div>
  <h1>MyMovieJam ratings dataset</h1>
  <p class="answer">Every score on the MyMovieJam ratings index, as free, reusable data: title, year, type, genre, platform, score, band, Watch if and Skip if, and the link to the rating page. It is available as CSV and JSON under a CC BY 4.0 license.</p>
  <p class="updated">Updated <time datetime="{UPDATED_ISO}">{UPDATED_HUMAN}</time> · Edited by Milind Patil</p>
  <div class="actions">
    <a class="btn btn-secondary" href="/data/mymoviejam-ratings.csv" download>Download CSV</a>
    <a class="btn btn-secondary" href="/data/mymoviejam-ratings.json" download>Download JSON</a>
  </div>
  <div class="panel">
    <h2>Fields</h2>
    <table class="fields">
      <thead><tr><th>Field</th><th>Description</th></tr></thead>
      <tbody>
{trs}
      </tbody>
    </table>
    <p style="margin-top:12px">The files carry no viewer counts or review counts; we do not track a panel size per title.</p>
  </div>
  <div class="panel">
    <h2>Example record (JSON)</h2>
    <pre class="sample">{esc(json.dumps(sample_j, ensure_ascii=False, indent=2))}</pre>
  </div>
  <div class="panel">
    <h2>Method</h2>
    <p>{esc(METHOD)} Scores are out of 10. Bands: {esc(BANDS_TXT)}. Where a MyMovieJam blog review exists for a title, the score in that review is the source and the rating page shows the same number. Full explanation: <a href="/how-we-rate/#mymoviejam-score">How we rate</a>.</p>
  </div>
  <div class="panel">
    <h2>License and attribution</h2>
    <p>Licensed under <a href="https://creativecommons.org/licenses/by/4.0/" rel="license noopener">Creative Commons Attribution 4.0 (CC BY 4.0)</a>. You may copy, redistribute, adapt and use it commercially, as long as you give credit.</p>
    <p>Suggested attribution: “Ratings data from MyMovieJam (mymoviejam.com), CC BY 4.0”, with a link to <a href="{url}">{url}</a>.</p>
  </div>
  <div class="panel">
    <h2>Update date</h2>
    <p>Last updated <time datetime="{UPDATED_ISO}">{UPDATED_HUMAN}</time>. Browse the same scores on the <a href="/movie-ratings/">ratings index</a> or in our <a href="/best/">best-picks guides</a>.</p>
  </div>"""
    title = "MyMovieJam Ratings Dataset (CSV & JSON, CC BY 4.0) | MyMovieJam"
    desc = "Open dataset of MyMovieJam movie and series scores: title, year, genre, platform, score, band, Watch if and Skip if. CSV and JSON, CC BY 4.0."
    ld = [
        {"@type": "WebPage", "@id": url + "#webpage", "url": url, "name": "MyMovieJam ratings dataset", "description": desc,
         "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO, "inLanguage": "en", "publisher": ORG, "editor": EDITOR,
         "mainEntity": {"@id": url + "#dataset"}},
        {"@type": "Dataset", "@id": url + "#dataset", "name": "MyMovieJam Ratings Dataset",
         "description": ("MyMovieJam scores for movies and series: title, year, type, genre, platform, score out of 10, band "
                         "(Great, Good, Mixed, Skip), Watch if, Skip if and rating page URL. Scores come from a panel of friends and "
                         "family who watched each title, cross-checked against sentiment on X."),
         "url": url, "sameAs": f"{SITE}/movie-ratings/", "license": "https://creativecommons.org/licenses/by/4.0/",
         "creditText": "MyMovieJam (mymoviejam.com)", "isAccessibleForFree": True, "inLanguage": "en",
         "datePublished": UPDATED_ISO, "dateModified": UPDATED_ISO,
         "keywords": ["movie ratings", "TV series ratings", "streaming", "Netflix", "Prime Video", "Apple TV+", "Disney+", "watch or skip"],
         "creator": ORG, "publisher": ORG,
         "measurementTechnique": METHOD,
         "variableMeasured": [{"@type": "PropertyValue", "name": k, "description": v} for k, v in desc_f.items()],
         "distribution": [
             {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": csv_url, "name": "mymoviejam-ratings.csv"},
             {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": json_url, "name": "mymoviejam-ratings.json"}]},
    ]
    d = ROOT / "data"
    d.mkdir(exist_ok=True)
    (d / "index.html").write_text(shell(path=path, title=title, desc=desc, kicker="", h1="", body=body, ld=ld, og_type="website"), encoding="utf-8")


def main():
    cat = parse_catalog()
    rows = write_dataset(cat)
    results = build_best(cat)
    build_hub(results)
    build_data_page(rows)
    print(f"catalog={len(cat)} dataset_rows={len(rows)}")
    for page, rs, _ in results:
        print(page["slug"], [(r["title"], r["score_s"], r["band"], r["platform"]) for r in rs])


if __name__ == "__main__":
    main()
