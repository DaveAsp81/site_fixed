#!/usr/bin/env python3
"""Structural audit across every page. Prints only what is wrong."""
import glob
import os
import re
import sys

CHECKS = []


def check(name):
    def deco(fn):
        CHECKS.append((name, fn))
        return fn
    return deco


@check("no <main id=main>")
def c_main(s, f):
    return '<main id="main"' not in s


@check("no skip link")
def c_skip(s, f):
    return 'class="skip-link"' not in s


@check("nav-toggle missing aria-expanded")
def c_toggle(s, f):
    m = re.search(r'<button class="nav-toggle"[^>]*>', s)
    return bool(m) and 'aria-expanded' not in m.group(0)


@check("nav not labelled / wrong id")
def c_nav(s, f):
    return 'id="site-nav"' not in s


@check("old nav item present")
def c_oldnav(s, f):
    nav = re.search(r'<nav id="site-nav".*?</nav>', s, re.S)
    if not nav:
        return False
    return ('/#getting-started' in nav.group(0)
            or '/#lore' in nav.group(0)
            or '/opfor-command' in nav.group(0))


@check("site.js not included")
def c_js(s, f):
    return 'assets/js/site.js' not in s


@check("no manifest link")
def c_manifest(s, f):
    return 'rel="manifest"' not in s


@check("font @import still used")
def c_import(s, f):
    return '@import' in s and 'fonts.googleapis' in s


@check("fonts not preconnected")
def c_preconnect(s, f):
    return 'fonts.googleapis.com/css2' in s and 'rel="preconnect"' not in s


@check("target=_blank without noopener")
def c_noopener(s, f):
    for m in re.finditer(r'<a\b[^>]*target="_blank"[^>]*>', s):
        if 'noopener' not in m.group(0):
            return True
    return False


@check("affiliate link without sponsored/nofollow")
def c_aff(s, f):
    for m in re.finditer(r'<a\b[^>]*(amzn\.to|amazon\.[a-z.]+/)[^>]*>', s):
        if 'sponsored' not in m.group(0):
            return True
    return False


@check("unclosed <header>")
def c_header(s, f):
    return s.count("<header") != s.count("</header>")


@check("unclosed <main>")
def c_mainclose(s, f):
    return s.count("<main") != s.count("</main>")


@check("low-contrast grey (#444/#555/#666) text")
def c_grey(s, f):
    # `color:` only, not border-color / background-color / outline-color.
    # A dim border is fine; dim body text is not.
    return bool(re.search(r'(?<![-\w])color:\s*#(444|555|666)\b', s, re.I))


@check("background-image on a content thumbnail")
def c_bg(s, f):
    return bool(re.search(r'class="[^"]*(article-card-image|article-hero|mech-'
                          r'feature-img|mech-card-image)[^"]*"[^>]*background-image', s))


@check("img without alt")
def c_alt(s, f):
    # Only real elements: an <img> with no src at all is prose or a comment.
    for m in re.finditer(r'<img\b[^>]*>', s):
        tag = m.group(0)
        if 'src=' not in tag and 'srcset=' not in tag:
            continue
        if 'alt=' not in tag:
            return True
    return False


@check("newsletter form still target=_blank")
def c_mc(s, f):
    for m in re.finditer(r'<form\b[^>]*list-manage[^>]*>', s):
        if 'target="_blank"' in m.group(0):
            return True
    return False


@check("EMAIL input without a label")
def c_label(s, f):
    if 'name="EMAIL"' not in s:
        return False
    return 'class="sr-only" for="nl-email' not in s


@check("dead YouTube handle")
def c_yt(s, f):
    return 'youtube.com/@BattleTechDownUnder' in s


def main():
    files = sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html"))
    # pages that legitimately opt out of parts of the chrome
    exempt = {
        "offline.html": {"no <main id=main>", "no skip link",
                         "nav-toggle missing aria-expanded",
                         "nav not labelled / wrong id", "site.js not included",
                         "fonts not preconnected"},
    }
    total = 0
    for f in files:
        base = os.path.basename(f)
        s = open(f, encoding="utf-8").read()
        hits = [n for n, fn in CHECKS
                if n not in exempt.get(base, set()) and fn(s, f)]
        if hits:
            print("%-46s %s" % (f, "; ".join(hits)))
            total += len(hits)
    print("\n%d pages audited, %d findings" % (len(files), total))
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
