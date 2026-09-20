#!/usr/bin/env python3
"""Add a contents list, a visible byline and related guides to every article.

Three things were missing from every long-form page:

  * No table of contents. The Locust guide is 3,554 words and 25.7 phone
    screens with 12 h2 headings and no way to jump to any of them.
  * No visible date. Every page already carried datePublished and
    dateModified in its JSON-LD, so a reader had no way to tell whether a
    guide was current even though the site knew.
  * Nothing linked onward. The bottom of an article was a dead end.

Related guides come from guides.html, which is the site's own grouping, so
this never invents a relationship the site does not already claim.
"""
import glob
import html
import json
import os
import re
import sys

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]

TOC = ('<nav class="guide-toc" data-toc data-toc-scope="article" hidden '
       'aria-labelledby="toc-title"></nav>')


def pretty_date(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return None
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= mo <= 12:
        return None
    return "%d %s %d" % (d, MONTHS[mo - 1], y)


def categories():
    """category name -> [(url, title)] from the site's own guides index."""
    src = open("guides.html", encoding="utf-8").read()
    out = {}
    parts = re.split(r'<div class="section-divider"[^>]*>\s*<h2>(.*?)</h2>', src)
    for i in range(1, len(parts), 2):
        name = html.unescape(re.sub(r"<[^>]+>", "", parts[i])).strip()
        body = parts[i + 1]
        cards = re.findall(
            r'<h3>(.*?)</h3>.*?<a href="(/articles/[^"]+)"', body, re.S)
        out[name] = [(url, html.unescape(re.sub(r"\s+", " ",
                      re.sub(r"<[^>]+>", "", title)).strip()))
                     for title, url in cards]
    return out


def slug_of(path):
    return "/articles/" + os.path.splitext(os.path.basename(path))[0]


def build_related(path, cats):
    me = slug_of(path)
    for name, items in cats.items():
        urls = [u for u, _t in items]
        if me not in urls:
            continue
        siblings = [(u, t) for u, t in items if u != me][:3]
        if not siblings:
            return None
        rows = "\n".join(
            '            <li><a href="%s">%s</a></li>' % (u, html.escape(t))
            for u, t in siblings)
        return ('\n<div class="related-guides">\n'
                '    <h2>More in %s</h2>\n'
                '    <ul>\n%s\n    </ul>\n'
                '    <p style="margin:14px 0 0;"><a class="read-more" href="/guides">'
                'All guides and articles &rarr;</a></p>\n'
                '</div>\n' % (html.escape(name), rows))
    return None


def meta_block(src):
    """Surface the dates the page already declares in its JSON-LD."""
    m = re.search(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                  src, re.S | re.I)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except Exception:
        return None
    if isinstance(data, list):
        data = next((d for d in data if isinstance(d, dict)), {})
    pub = pretty_date(data.get("datePublished"))
    mod = pretty_date(data.get("dateModified"))
    author = (data.get("author") or {}).get("name") if isinstance(
        data.get("author"), dict) else None

    bits = []
    if author:
        bits.append('<span>By %s</span>' % html.escape(author))
    if mod and mod != pub:
        bits.append('<span class="meta-updated">Updated %s</span>' % mod)
        if pub:
            bits.append('<span>First published %s</span>' % pub)
    elif pub:
        bits.append('<span class="meta-updated">Published %s</span>' % pub)
    if not bits:
        return None
    return '<p class="article-meta">%s</p>' % "".join(bits)


def process(path, cats, dry=False):
    src = original = open(path, encoding="utf-8").read()
    notes = []

    h1 = re.search(r'</h1>', src)
    if not h1:
        return ["NO H1"]

    # Byline and contents both go directly under the title.
    insert = []
    if 'class="article-meta"' not in src:
        mb = meta_block(src)
        if mb:
            insert.append(mb)
            notes.append("byline")
    if "data-toc" not in src:
        h2s = len(re.findall(r"<h2[ >]", src))
        if h2s >= 4:
            insert.append(TOC)
            notes.append("toc(%d)" % h2s)
    if insert:
        at = h1.end()
        src = src[:at] + "\n" + "\n".join(insert) + "\n" + src[at:]

    # Related guides go at the end of the article body.
    if 'class="related-guides"' not in src:
        rel = build_related(path, cats)
        if rel:
            close = src.rfind("</article>")
            if close != -1:
                src = src[:close] + rel + src[close:]
                notes.append("related")

    if src != original and not dry:
        open(path, "w", encoding="utf-8").write(src)
    return notes


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    cats = categories()
    print("categories: " + ", ".join(
        "%s (%d)" % (k, len(v)) for k, v in cats.items()) + "\n")
    for f in sorted(glob.glob("articles/*.html")):
        n = process(f, cats, dry)
        print("%-46s %s" % (f, ", ".join(n) if n else "-"))
