# build-scripts

Maintenance scripts for the site. Nothing here is served: `robots.txt`
disallows the directory, and no page links to it. They are all plain Python 3
with [Pillow](https://pypi.org/project/pillow/) the only dependency, and every
one is safe to re-run — they either skip work that is already done or produce
the same result twice.

Run them from the repository root, not from this directory.

## Watch out for this first

**`build_mech_index.py` is not in this repo** — it lives in a local folder and
reads `index.html` from an *uploads* directory rather than from the repository.
If you run it before repointing it at the repo, it will overwrite the home page
and undo:

- the featured-guide shuffle block, which now swaps a real `<img>` `src` and
  `srcset` rather than a CSS background,
- the section jump strip,
- the position of the about strip, which sits below the tools now.

Point it at the repo copy, or run it and then re-apply those three by hand.

## Images

    python build-scripts/build_images.py          # generate WebP derivatives
    python build-scripts/refresh_srcset.py        # point every <img> at them

`build_images.py` walks `assets/images`, and for every source over 600px wide
or 40 KB writes `<name>-480.webp`, `-800.webp`, `-1280.webp` and `-1600.webp`,
skipping any width that would be an upscale. A source narrower than 480px gets
one derivative at its native width so it is still WebP. Pass `--force` to
regenerate everything.

It also handles the one image referenced from CSS rather than markup
(`hero-madcat.webp`), which has no `<img>` to carry a srcset.

`refresh_srcset.py` rewrites `src`, `srcset`, `sizes`, `width` and `height` on
every `<img>` that points into `assets/images`, leaving `alt`, `loading` and
`class` alone. Run it after `build_images.py`.

**Adding an image:** drop the original into `assets/images/`, run both scripts,
reference it from a page, then run `check_links.py`. The originals stay in the
repo as the masters and are never served.

    python build-scripts/build_icons.py           # PWA icon set from the touch icon

## Page chrome

    python build-scripts/apply_chrome.py          # one header, nav, <main>, skip link
    python build-scripts/apply_footer.py          # one footer
    python build-scripts/enhance_articles.py      # contents list, byline, related guides
    python build-scripts/fix_newsletter.py        # labels and in-page submit

`apply_chrome.py` holds the canonical nav in one place: edit the `NAV` list and
re-run to update all 52 pages. It skips `offline.html`, which must not
reference a webfont or anything else off-origin.

`apply_footer.py` holds the canonical footer the same way. It gives
`opfor-command.html` a scoped link strip instead, because that page carries its
own light theme and does not load the site stylesheet.

`enhance_articles.py` takes its related-guides groupings from `guides.html`, so
it never invents a relationship the site does not already claim. An article
absent from that index gets no related block — which is how the four orphaned
articles were found.

Each of these is idempotent: running it twice changes nothing the second time.

## Checks

    python build-scripts/audit.py                 # structure and accessibility
    python build-scripts/check_scripts.py         # every inline script and JSON block
    python build-scripts/check_links.py           # every local href, src and srcset

Run all three before committing. They print only what is wrong and exit
non-zero on a finding, so they work in a hook or CI as-is.

`audit.py` is the one to extend. Each check is a small function with a
`@check("description")` decorator; add one and it runs across every page.

## Data files these scripts do not touch

Edited by hand, no build step:

| File | What it holds |
| --- | --- |
| `assets/data/paint-schemes.json` | The paint schemes, each with a `sourced` flag and a citation |
| `assets/data/paints.json` | Citadel, Vallejo Model Color and Army Painter, with approximate swatch hexes |
| `mechs.json`, `vehicles.json` | The unit catalogue the tools load |
| `sitemap.xml` | Add a row when you add a page |
| `_headers` | Cache and security headers, applied by Netlify |

## The one versioned file

`assets/js/opfor-command.v1.js` is the OpFor Command application, extracted
from the page it used to sit inline in. Its filename carries a version because
`_headers` caches it for a year as `immutable`. Editing it in place without
renaming means returning visitors keep the old copy for up to a year, so:

1. rename to `opfor-command.v2.js`
2. update the `<script src>` in `opfor-command.html`
3. update the path in `_headers`

Nothing else in `assets/js/` is versioned; the rest gets a one-hour cache and
can be edited in place.
