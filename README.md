# 3D Prints

Things I've designed and printed. Each print is a parametric Python model: change a number, re-run, get a new part.

**Site:** https://shrutikadge.github.io/3d-prints/

| Print | What it is |
|---|---|
| [Pantry flip-bar lock](prints/pantry-flip-lock/) | Toddler lock that ties two pantry doors together, plus a printed drilling template |

## Layout

```
prints/<slug>/
  README.md     write-up (also becomes the site page)
  print.json    title, summary, cover, material, print time
  docs/         images
  *.py          the model; outputs go to stl/ (not committed)
build_site.py   makes index.html + prints/<slug>/index.html for GitHub Pages
site.json       site title, base URL, repo URL
assets/         site stylesheet
```

## Adding a print

1. Make `prints/<slug>/` with `README.md`, `print.json` and `docs/cover.jpg`.
2. `pip install markdown && python build_site.py`
3. Commit everything, including the generated `index.html` files.

These are hobby prints, not certified products. Use them at your own risk.
