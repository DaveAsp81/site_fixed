#!/usr/bin/env python3
"""Apply one consistent, accessible page chrome to every HTML file.

Before this the site had two different navs across 49 pages (the 42 article
and tool pages could not reach Paint Tool or Articles at all), no <main>, no
skip link, a nav toggle with no aria-expanded, three pages whose <header> was
never closed, and the same inline nav script pasted into 40 files.

The script is idempotent: running it twice changes nothing the second time.
"""
import glob
import os
import re
import sys

# ── the one nav ──────────────────────────────────────────────────────
# Five destinations plus search. Game Tracker, Campaign Tracker, OpFor and
# Paint Tool live behind /tools rather than a JS dropdown, so they are
# linkable, indexable and work without JavaScript.
NAV = [
    ("/lance-builder", "Lance Builder", {"lance-builder.html"}),
    ("/tools", "Tools", {"tools.html", "game-tracker.html", "opfor-command.html",
                         "campaign.html", "paint-tool.html"}),
    ("/mechs", "Mech Guides", {"mechs.html", "locust.html", "atlas.html",
                               "marauder.html", "warhammer.html",
                               "highlander.html", "rating-scale.html"}),
    ("/guides", "Articles", {"guides.html"}),
    ("/about", "About", {"about.html", "contact.html"}),
]

SKIP_LINK = '<a class="skip-link" href="#main">Skip to main content</a>'

HEADER_TMPL = """<header{cls}>
    <div class="header-content">
        <a href="/" class="logo">BattleTech HQ</a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav">
            <span aria-hidden="true">&#9776;</span> Menu
        </button>
        <nav id="site-nav" aria-label="Main">
            <ul>
{items}
                <li><a class="nav-search" href="/search"{search_cur}><span aria-hidden="true">&#9906;</span> Search</a></li>
            </ul>
        </nav>
    </div>
</header>"""

# Fonts were pulled in with @import inside style.css, which serialises the
# requests: HTML -> style.css -> Google CSS -> woff2. A preconnect plus a
# direct <link> lets the font CSS start immediately, in parallel with ours.
HEAD_BLOCK = """    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700;900&family=Rajdhani:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap">
"""

MANIFEST_LINK = '    <link rel="manifest" href="/site.webmanifest">\n'
SITE_JS = '    <script defer src="/assets/js/site.js"></script>\n'

# The inline nav-toggle snippet that was duplicated across 40 pages.
INLINE_NAV_RE = re.compile(
    r'\n?<script>\s*document\.addEventListener\(\s*[\'"]DOMContentLoaded[\'"].*?'
    r'nav-toggle.*?</script>\s*', re.S)

SITE_HEADER_RE = re.compile(r'<header\b[^>]*>', re.I)


def nav_items(page):
    out = []
    for href, label, owners in NAV:
        cur = ' aria-current="page"' if page in owners else ''
        out.append('                <li><a href="%s"%s>%s</a></li>' % (href, cur, label))
    return "\n".join(out)


def build_header(page, cls=""):
    # opfor-command.html styles its own header via .bt-nav and does not load
    # the site stylesheet, so keep whatever class the page already had.
    return HEADER_TMPL.format(
        cls=' class="%s"' % cls if cls else "",
        items=nav_items(page),
        search_cur=' aria-current="page"' if page == "search.html" else "")


def find_site_header(src):
    """Return (start, end, class_attr) of the site header block, or None.

    The site header is the one containing header-content; opfor-command.html
    has a second <header class="mast"> that must be left alone. Three pages
    never closed their <header>, so fall back to the end of the nav.
    """
    for m in SITE_HEADER_RE.finditer(src):
        window = src[m.start():m.start() + 400]
        if "header-content" not in window:
            continue
        cls_m = re.search(r'class="([^"]*)"', m.group(0))
        cls = cls_m.group(1) if cls_m else ""
        close = src.find("</header>", m.end())
        nav_close = src.find("</nav>", m.end())
        if close != -1 and (nav_close == -1 or close < nav_close + 600):
            return m.start(), close + len("</header>"), cls
        if nav_close != -1:
            # unclosed <header>: stop after the </div> that ends header-content
            div_close = src.find("</div>", nav_close)
            if div_close != -1:
                return m.start(), div_close + len("</div>"), cls
            return m.start(), nav_close + len("</nav>"), cls
    return None


def patch_head(src, page):
    """Add font preconnect/link, manifest and site.js exactly once."""
    if "fonts.googleapis.com/css2" not in src:
        # put the font links immediately before the site stylesheet
        m = re.search(r'[ \t]*<link rel="stylesheet" href="[^"]*assets/css/style\.css">\n', src)
        if m:
            src = src[:m.start()] + HEAD_BLOCK + m.group(0) + src[m.end():]
        else:
            src = src.replace("</head>", HEAD_BLOCK + "</head>", 1)
    if 'rel="manifest"' not in src:
        src = src.replace("</head>", MANIFEST_LINK + "</head>", 1)
    if "assets/js/site.js" not in src:
        src = src.replace("</head>", SITE_JS + "</head>", 1)
    return src


def patch_main(src):
    """Wrap the page body in <main id="main">.

    Skipped where a <main> already exists (one article does) - that one just
    gains the id.
    """
    if re.search(r'<main\b', src, re.I):
        if 'id="main"' not in src:
            src = re.sub(r'<main\b', '<main id="main"', src, count=1)
        return src

    close = src.find("</header>")
    if close == -1:
        return src
    open_at = close + len("</header>")
    src = src[:open_at] + '\n<main id="main">' + src[open_at:]

    # Close before the footer if there is one, else at the end of the body.
    foot = src.find("<footer")
    if foot != -1:
        return src[:foot] + "</main>\n\n" + src[foot:]
    body_end = src.rfind("</body>")
    if body_end != -1:
        return src[:body_end] + "</main>\n" + src[body_end:]
    return src + "\n</main>\n"


def patch_rels(src):
    """Add rel="noopener" to every target="_blank", and mark affiliate links.

    Amazon Associates requires sponsored/nofollow on affiliate links; 12 links
    across the site opened new tabs with no noopener at all.
    """
    def fix(m):
        tag = m.group(0)
        if 'target="_blank"' not in tag and "target='_blank'" not in tag:
            return tag
        affiliate = bool(re.search(r'href="[^"]*(amzn\.to|amazon\.[a-z.]+/)', tag))
        want = ["sponsored", "nofollow", "noopener"] if affiliate else ["noopener"]
        rel_m = re.search(r'rel="([^"]*)"', tag)
        have = rel_m.group(1).split() if rel_m else []
        merged = have + [w for w in want if w not in have]
        if rel_m:
            if merged == have:
                return tag
            return tag[:rel_m.start()] + 'rel="%s"' % " ".join(merged) + tag[rel_m.end():]
        return tag[:-1].rstrip() + ' rel="%s"' % " ".join(merged) + ">"

    return re.sub(r'<a\b[^>]*>', fix, src)


def process(path, dry=False):
    page = os.path.basename(path)
    src = original = open(path, encoding="utf-8").read()
    notes = []

    span = find_site_header(src)
    if span:
        new = build_header(page, span[2])
        if src[span[0]:span[1]] != new:
            src = src[:span[0]] + new + src[span[1]:]
            notes.append("header")
    else:
        notes.append("NO HEADER FOUND")

    if SKIP_LINK not in src:
        src = re.sub(r'(<body\b[^>]*>)', r'\1\n' + SKIP_LINK, src, count=1)
        notes.append("skip-link")

    before = src
    src = INLINE_NAV_RE.sub("\n", src)
    if src != before:
        notes.append("-inline-nav-js")

    before = src
    src = patch_head(src, page)
    if src != before:
        notes.append("head")

    before = src
    src = patch_main(src)
    if src != before:
        notes.append("main")

    before = src
    src = patch_rels(src)
    if src != before:
        notes.append("rel")

    if src != original and not dry:
        open(path, "w", encoding="utf-8").write(src)
    return notes


# offline.html is shown when there is no network at all, so it must not
# reference a webfont, a service worker or anything else off-origin. It is
# hand-maintained and deliberately skipped here.
EXCLUDE = {"offline.html"}


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    files = [f for f in sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html"))
             if os.path.basename(f) not in EXCLUDE]
    for f in files:
        n = process(f, dry)
        if n:
            print("%-44s %s" % (f, ", ".join(n)))
    print("\n%d files considered" % len(files))
