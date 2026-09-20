#!/usr/bin/env python3
"""Verify every local href, src and srcset candidate resolves to a real file.

Clean URLs make this easy to get wrong: /mechs has to find mechs.html, and a
srcset entry that 404s shows nothing with no error anywhere.
"""
import glob
import html
import os
import re
import sys

ATTR_RE = re.compile(r'\b(href|src)="([^"]+)"', re.I)
SRCSET_RE = re.compile(r'\bsrcset="([^"]+)"', re.I)
CSS_URL_RE = re.compile(r'url\(\s*[\'"]?([^\'")]+)[\'"]?\s*\)')

SKIP = re.compile(r'^(https?:|mailto:|tel:|data:|javascript:|#)')
# References built inside JS strings (`${...}`, ' + x + ') are code.
TEMPLATE = re.compile(r"""\$\{|\+\s|\s\+|^\s*['"]""")


def resolve(ref, page):
    """Return the file a reference points at, or None if it cannot be found."""
    ref = html.unescape(ref).split("#")[0].split("?")[0]
    if not ref:
        return "OK"
    if ref.startswith("/"):
        base = "."
        rel = ref.lstrip("/")
    else:
        base = os.path.dirname(page) or "."
        rel = ref
    target = os.path.normpath(os.path.join(base, rel))
    if os.path.exists(target):
        return "OK"
    # clean URL: /mechs -> mechs.html, /articles/foo -> articles/foo.html
    if os.path.exists(target + ".html"):
        return "OK"
    if os.path.isdir(target) and os.path.exists(os.path.join(target, "index.html")):
        return "OK"
    return None


def main():
    pages = sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html"))
    bad = 0
    checked = 0
    for page in pages:
        src = open(page, encoding="utf-8").read()
        refs = []
        for m in ATTR_RE.finditer(src):
            refs.append(m.group(2))
        for m in SRCSET_RE.finditer(src):
            for cand in m.group(1).split(","):
                url = cand.strip().split()[0] if cand.strip() else ""
                if url:
                    refs.append(url)
        for m in CSS_URL_RE.finditer(src):
            refs.append(m.group(1))
        for ref in refs:
            if SKIP.match(ref) or TEMPLATE.search(ref):
                continue
            checked += 1
            if resolve(ref, page) is None:
                print("BROKEN  %-44s -> %s" % (page, ref))
                bad += 1

    # the stylesheet's own url() references resolve against the css file
    css = "assets/css/style.css"
    if os.path.exists(css):
        text = open(css, encoding="utf-8").read()
        for m in CSS_URL_RE.finditer(text):
            ref = m.group(1)
            if SKIP.match(ref) or TEMPLATE.search(ref):
                continue
            checked += 1
            target = os.path.normpath(os.path.join(os.path.dirname(css), ref))
            if not os.path.exists(target):
                print("BROKEN  %-44s -> %s" % (css, ref))
                bad += 1

    print("\n%d local references checked, %d broken" % (checked, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
