# TRIAD Index — Book Site

A GitBook-style documentation site (sidebar table of contents, chapter pages, code
blocks) built from your methodology paper and your Python scoring engine — plus a
real download of the desktop GUI tool.

## Structure

```
index.html          Ch.00 Overview
background.html      Ch.01 Background & Objectives
methodology.html      Ch.02 The Scoring Methodology (with real code)
case-studies.html      Ch.03 Case Studies
calculator.html         Ch.04 Live in-browser calculator
tool.html                Ch.05 Desktop GUI — download page
appendix.html              Ch.06 Full TRL/MRL/CRL level definitions + references
advisory.html                 Ch.07 Advisory services & contact

assets/book.css       Shared stylesheet (light, GitBook-style theme)
assets/site.js         Sidebar toggle (mobile menu)
assets/data.js           Scoring engine — categories, gate rules, case study data
assets/app.js              Calculator + case-study interactivity
assets/chart.umd.min.js      Chart.js, bundled locally (no external CDN needed)

downloads/trl_readiness_gui.py   Your desktop GUI tool, offered as a direct download
downloads/trl-readiness-gui.zip    Same tool + README, zipped
downloads/README.txt                 Run instructions bundled into the zip

build.py    The generator script that produces all *.html chapter pages from one
            template — edit content here, not the HTML files directly (see below).
```

## Before you publish

1. **Personalize contact info.** In `build.py`, find `[Your Name]`, `[you@example.com]`,
   and `[linkedin.com/in/you]` in the `advisory` chapter and replace them, then
   re-run `python3 build.py` to regenerate `advisory.html`.
2. **Rename the tool if you like.** "TRIAD Index" appears in `build.py` (page titles,
   sidebar brand) — a find-and-replace there, then rebuild, covers it.
3. Case study scores are illustrative, not audited — swap in real numbers by
   editing `CASE_STUDIES` in `assets/data.js` (no rebuild needed for this file).

## Editing content

**Don't hand-edit the `.html` files** — they're generated. Edit the chapter content
inside `build.py` (each chapter is a Python string passed to `render(...)`), then run:

```bash
python3 build.py
```

This regenerates all eight pages with consistent sidebar navigation and
previous/next links, so chapters never drift out of sync with each other.

The scoring logic itself (categories, gate rules) lives in `assets/data.js` and is
shared by both the web calculator and referenced in the methodology chapter's code
samples — update it there if the underlying framework changes.

## Publish to GitHub Pages

```bash
git init
git add .
git commit -m "Initial TRIAD Index book site"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Then in the repo: **Settings → Pages → Build and deployment → Source** →
**Deploy from a branch**, branch `main`, folder `/ (root)` → **Save**.

Your site will be live at `https://<your-username>.github.io/<your-repo>/` within
a minute or two.
