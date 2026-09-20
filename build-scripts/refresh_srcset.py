#!/usr/bin/env python3
"""Point every <img> at the current best WebP derivative.

Run this after build_images.py whenever images are added or re-sized: it
rewrites src/srcset/width/height in place and leaves alt, loading, class and
everything else alone. Idempotent.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from imgsrc import img_attrs, variants

# Which `sizes` an image gets, by the class on it or on its wrapper.
SIZES = [
    ("article-hero", "(min-width: 900px) 820px, calc(100vw - 60px)"),
    ("mech-feature-img", "(min-width: 700px) 230px, calc(100vw - 60px)"),
    ("mech-card-image", "(min-width: 700px) 230px, calc(100vw - 60px)"),
    ("article-card-image", "(min-width: 1180px) 420px, (min-width: 700px) 46vw, calc(100vw - 60px)"),
    ("mech-schematic", "(min-width: 900px) 560px, calc(100vw - 80px)"),
]
DEFAULT_SIZES = "(min-width: 900px) 800px, calc(100vw - 60px)"

IMG_RE = re.compile(r'<img\b[^>]*>', re.I)
SRC_RE = re.compile(r'\bsrc="([^"]+)"')


def strip(tag, attr):
    return re.sub(r'\s+%s="[^"]*"' % attr, "", tag)


def source_of(url):
    """Map a page-relative url (maybe already a derivative) back to a repo
    source path, plus the prefix the page uses."""
    prefix = ""
    path = url
    while path.startswith("../"):
        path = path[3:]
        prefix += "../"
    if path.startswith("/"):
        prefix = "/"
        path = path[1:]
    # if it already points at a derivative, go back to the original
    m = re.match(r'^(.*)-(\d+)\.webp$', path)
    if m:
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            cand = m.group(1) + ext
            if os.path.exists(cand):
                return prefix, cand
    return prefix, path


def sizes_for(tag, context):
    blob = tag + " " + context
    for cls, sizes in SIZES:
        if cls in blob:
            return sizes
    return DEFAULT_SIZES


def process(path, dry=False):
    src = original = open(path, encoding="utf-8").read()
    changed = []

    def sub(m):
        tag = m.group(0)
        sm = SRC_RE.search(tag)
        if not sm:
            return tag
        if "assets/images" not in sm.group(1):
            return tag
        prefix, repo = source_of(sm.group(1))
        if not os.path.exists(repo):
            changed.append("  MISSING " + repo)
            return tag
        vs, _w, _h = variants(repo)
        if not vs:
            return tag
        # 200 chars of surrounding markup, for the wrapper's class
        start = max(0, m.start() - 200)
        context = src[start:m.start()]
        attrs = img_attrs(repo, prefix, sizes_for(tag, context))

        out = tag
        for a in ("src", "srcset", "sizes", "width", "height"):
            out = strip(out, a)
        out = re.sub(r'^<img', "<img " + attrs, out, count=1)
        out = re.sub(r'\s+', " ", out).replace("< img", "<img")
        if out != tag:
            changed.append("  %s -> %s" % (os.path.basename(repo),
                                           os.path.basename(vs[-1][0])))
        return out

    src = IMG_RE.sub(sub, src)
    if src != original and not dry:
        open(path, "w", encoding="utf-8").write(src)
    return changed


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    total = 0
    for f in sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html")):
        ch = process(f, dry)
        if ch:
            print(f)
            for c in ch:
                print(c)
            total += len(ch)
    print("\n%d <img> tags refreshed" % total)
