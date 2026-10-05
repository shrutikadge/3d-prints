"""Build the static site (GitHub Pages) from prints/*/print.json + README.md.

    python build_site.py

Writes index.html (gallery) and prints/<slug>/index.html (one page per print).
To add a print: make prints/<slug>/ with README.md, print.json and a cover image,
then run this again and commit the generated HTML.
"""
import html
import json
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).parent
SITE = json.loads((ROOT / "site.json").read_text())
BASE = SITE.get("base_url", "").rstrip("/")
REPO = SITE.get("repo_url", "").rstrip("/")
e = html.escape


def head(title, desc, image, depth, url_path):
    rel = "../" * depth
    og_img = f"{BASE}/{image}" if BASE else f"{rel}{image}"
    og_url = f'<meta property="og:url" content="{BASE}/{url_path}">' if BASE else ""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{e(og_img)}">
{og_url}
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{rel}assets/style.css">
</head>
<body>
<header class="site"><a href="{rel}index.html" class="brand">{e(SITE["title"])}</a>
{f'<a class="gh" href="{e(REPO)}">GitHub</a>' if REPO else ''}</header>
"""


FOOT = """<footer class="site">{note}</footer>
</body>
</html>
"""


def chips(p):
    items = [p.get("material"), p.get("print_time"), p.get("parts")]
    return "".join(f'<span class="chip">{e(x)}</span>' for x in items if x)


def load_prints():
    out = []
    for pj in sorted((ROOT / "prints").glob("*/print.json")):
        meta = json.loads(pj.read_text())
        meta["slug"] = pj.parent.name
        meta["dir"] = pj.parent
        out.append(meta)
    return sorted(out, key=lambda m: m.get("date", ""), reverse=True)


def build_print(p):
    md = (p["dir"] / "README.md").read_text()
    md = re.sub(r"\A#\s+.*\n", "", md)                      # page title comes from print.json
    body = markdown.markdown(md, extensions=["tables", "fenced_code", "sane_lists"])
    body = body.replace("<blockquote>", '<blockquote class="note">')
    files = sorted(f.name for f in p["dir"].iterdir()
                   if f.suffix in (".py", ".txt") and f.is_file())
    src = f"{REPO}/tree/main/prints/{p['slug']}" if REPO else ""
    slug = p["slug"]
    href = (lambda f: f"{REPO}/blob/main/prints/{slug}/{f}") if REPO else (lambda f: f)
    links = "".join(f'<li><a href="{e(href(f))}"><code>{e(f)}</code></a></li>' for f in files)
    page = head(f'{p["title"]} · {SITE["title"]}', p["summary"], f'prints/{p["slug"]}/{p["cover"]}', 2,
                f'prints/{p["slug"]}/')
    page += f"""<main class="article">
<p class="crumb"><a href="../../index.html">← All prints</a></p>
<h1>{e(p["title"])}</h1>
<p class="lede">{e(p["summary"])}</p>
<p class="meta">{chips(p)}<span class="date">{e(p.get("date", ""))}</span></p>
{body}
<h2>Files</h2>
<ul class="files">{links}</ul>
{f'<p><a class="button" href="{e(src)}">View the source on GitHub</a></p>' if src else ''}
</main>
"""
    page += FOOT.format(note=e(SITE.get("footer", "")))
    (p["dir"] / "index.html").write_text(page)


def build_index(prints):
    cards = "".join(f"""
<a class="card" href="prints/{e(p['slug'])}/index.html">
  <img src="prints/{e(p['slug'])}/{e(p['cover'])}" alt="{e(p['title'])}" loading="lazy">
  <div class="card-body">
    <h2>{e(p['title'])}</h2>
    <p>{e(p['summary'])}</p>
    <p class="meta">{chips(p)}<span class="date">{e(p.get('date', ''))}</span></p>
  </div>
</a>""" for p in prints)
    cover = f"prints/{prints[0]['slug']}/{prints[0]['cover']}" if prints else ""
    page = head(SITE["title"], SITE["tagline"], cover, 0, "")
    page += f"""<main class="gallery">
<h1>{e(SITE["title"])}</h1>
<p class="lede">{e(SITE["tagline"])}</p>
<div class="grid">{cards}
</div>
</main>
"""
    page += FOOT.format(note=e(SITE.get("footer", "")))
    (ROOT / "index.html").write_text(page)


if __name__ == "__main__":
    prints = load_prints()
    for p in prints:
        build_print(p)
    build_index(prints)
    print(f"built index.html + {len(prints)} print page(s)")
