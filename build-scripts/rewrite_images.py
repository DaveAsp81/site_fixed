#!/usr/bin/env python3
"""Replace CSS background-image divs with real <img> elements.

Background images cannot lazy-load, cannot carry alt text and cannot offer a
srcset, so every card thumbnail on the site was downloading at full desktop
size before it scrolled into view. This converts them to <img> inside the same
wrapper div, so the existing ::after gradient overlays still apply.

It also repairs the 25 article heroes whose inline url() was never closed.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imgsrc import img_attrs

CARD_SIZES = "(min-width: 1180px) 420px, (min-width: 700px) 46vw, calc(100vw - 60px)"
HERO_SIZES = "(min-width: 900px) 820px, calc(100vw - 60px)"
FEATURE_SIZES = "(min-width: 700px) 230px, calc(100vw - 60px)"

# kind -> (sizes, loading, extra attrs), most specific first
KINDS = [
    ("article-hero", (HERO_SIZES, "eager", ' fetchpriority="high"')),
    ("mech-feature-img", (FEATURE_SIZES, "lazy", "")),
    ("mech-card-image", (FEATURE_SIZES, "lazy", "")),
    ("article-card-image", (CARD_SIZES, "lazy", "")),
]

# Matches the wrapper div plus its inline background-image, tolerating the
# unterminated url( that 25 article pages shipped with.
DIV_RE = re.compile(
    r'<div class="(?P<cls>[^"]*?(?:article-card-image|article-hero|mech-feature-img|mech-card-image)[^"]*?)"'
    r'(?P<mid>[^>]*?)'
    r'''style="\s*background-image:\s*url\(\s*['"]?(?P<url>[^'")>]+?)['"]?\s*\)?\s*;?\s*"'''
    r'\s*>\s*</div>',
    re.I)


def rewrite(path, dry=False):
    src = open(path, encoding="utf-8").read()
    changed = []

    def sub(m):
        classes = m.group("cls").split()
        url = m.group("url").strip()
        mid = m.group("mid").rstrip()
        kind = next((k for k, _ in KINDS if k in classes), None)
        if kind is None:
            return m.group(0)
        sizes, loading, extra = dict(KINDS)[kind]
        # resolve the page-relative url back to a repo-root path
        prefix = ""
        repo_path = url
        while repo_path.startswith("../"):
            repo_path = repo_path[3:]
            prefix += "../"
        if repo_path.startswith("/"):
            prefix = "/"
            repo_path = repo_path[1:]
        if not os.path.exists(repo_path):
            changed.append("  MISSING SOURCE: " + url)
            return m.group(0)
        attrs = img_attrs(repo_path, prefix, sizes)
        changed.append("  %-18s -> %s" % (kind, os.path.basename(repo_path)))
        return ('<div class="%s"%s><img %s alt="" loading="%s" '
                'decoding="async"%s></div>'
                % (m.group("cls"), mid, attrs, loading, extra))

    out = DIV_RE.sub(sub, src)
    if out != src and not dry:
        open(path, "w", encoding="utf-8").write(out)
    return changed


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    total = 0
    for f in sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html")):
        ch = rewrite(f, dry)
        if ch:
            print(f)
            for c in ch:
                print(c)
            total += len(ch)
    print("\n%d image elements rewritten" % total)
