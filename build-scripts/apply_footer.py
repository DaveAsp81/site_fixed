#!/usr/bin/env python3
"""Apply one consistent footer to every page.

Before this there were eight different footers and six pages with none at
all. The 25 article pages had a footer carrying four links — about, contact,
privacy and the affiliate disclosure — so from the bottom of a 3,500 word
guide there was no route to a tool, another guide, or search. The tool pages
had no footer, and so no way back into the site at all.

Links are root-relative, so the same markup works from / and from /articles/.
"""
import glob
import os
import re
import sys

FOOTER = """<footer>
    <div class="footer-content">
        <div class="footer-section">
            <h4>BattleTech HQ</h4>
            <p>Guides, tools and opinions for the modern MechWarrior, from the
            <a href="https://www.youtube.com/@DaveAsp81" target="_blank" rel="noopener" style="color:#ff8c00;">BattleTech Down Under</a>
            YouTube channel. Something wrong or missing?
            <a href="mailto:DaveAsp81@gmail.com" style="color:#ff8c00;">Tell me</a>.</p>
            <p style="margin-top:14px;"><a class="bmc-button" href="https://buymeacoffee.com/daveasp" target="_blank" rel="noopener">&#9749; Buy me a coffee</a></p>
        </div>
        <div class="footer-section">
            <h4>Tools</h4>
            <ul>
                <li><a href="/lance-builder">Lance Builder</a></li>
                <li><a href="/game-tracker">Game Tracker</a></li>
                <li><a href="/opfor-command">OpFor Command</a></li>
                <li><a href="/campaign">Campaign Tracker</a></li>
                <li><a href="/paint-tool">Paint Tool</a></li>
                <li><a href="/tools">All five, compared &rarr;</a></li>
            </ul>
        </div>
        <div class="footer-section">
            <h4>Reading</h4>
            <ul>
                <li><a href="/articles/battletech-beginner-guide">Start here</a></li>
                <li><a href="/mechs">Mech Guides</a></li>
                <li><a href="/guides">All guides &amp; articles</a></li>
                <li><a href="/rating-scale">How guides are rated</a></li>
                <li><a href="/search">Search the site</a></li>
            </ul>
        </div>
        <div class="footer-section">
            <h4>Elsewhere</h4>
            <ul>
                <li><a href="https://www.sarna.net" target="_blank" rel="noopener">Sarna.net &mdash; BattleTech Wiki</a></li>
                <li><a href="https://www.masterunitlist.info" target="_blank" rel="noopener">Master Unit List</a></li>
                <li><a href="https://megamek.org" target="_blank" rel="noopener">MegaMek &mdash; free digital BT</a></li>
                <li><a href="https://store.catalystgamelabs.com" target="_blank" rel="noopener">Catalyst Game Labs</a></li>
                <li><a href="https://battletech.com" target="_blank" rel="noopener">Official BattleTech</a></li>
            </ul>
        </div>
    </div>
    <div class="footer-bottom">
        <p><a href="/about">About</a> &middot; <a href="/contact">Contact</a> &middot;
           <a href="/privacy">Privacy</a> &middot;
           <a href="/affiliate-disclosure">Affiliate disclosure</a> &middot;
           <a href="/image-credits">Image credits</a></p>
        <p>&copy; 2026 BattleTech HQ. Unofficial fansite. BattleTech is a registered trademark of Topps Company, Inc.</p>
        <p class="affiliate-note">As an Amazon Associate I earn from qualifying purchases.</p>
    </div>
</footer>"""

# opfor-command.html has its own light theme and does not load the site
# stylesheet, so it gets a scoped strip of its own instead.
OPFOR_STRIP = """<nav class="bt-foot" aria-label="Site">
  <a href="/">BattleTech HQ</a>
  <a href="/tools">Tools</a>
  <a href="/lance-builder">Lance Builder</a>
  <a href="/game-tracker">Game Tracker</a>
  <a href="/mechs">Mech Guides</a>
  <a href="/guides">Articles</a>
  <a href="/search">Search</a>
  <a href="/about">About</a>
</nav>"""

OPFOR_CSS = """
  /* Site links, scoped: this page carries its own theme. */
  .bt-foot { max-width:1200px; margin:24px auto 40px; padding:16px 16px 0;
      border-top:1px solid var(--rule-2); display:flex; flex-wrap:wrap;
      gap:8px 18px; align-items:center; }
  .bt-foot a { color:var(--ink-2); text-decoration:none; font-size:0.82rem;
      font-family:'Saira Condensed',sans-serif; letter-spacing:0.05em;
      text-transform:uppercase; display:inline-block; padding:10px 0;
      min-height:40px; }
  .bt-foot a:hover, .bt-foot a:focus-visible { color:var(--stamp); }
"""

# offline.html must not link anywhere it cannot reach; it is hand-maintained.
EXCLUDE = {"offline.html", "opfor-command.html"}

FOOTER_RE = re.compile(r'<footer\b.*?</footer>', re.S | re.I)


def process(path, dry=False):
    src = original = open(path, encoding="utf-8").read()
    note = None

    if FOOTER_RE.search(src):
        if FOOTER_RE.search(src).group(0).strip() != FOOTER:
            src = FOOTER_RE.sub(lambda m: FOOTER, src, count=1)
            note = "replaced"
    else:
        # no footer at all: put one before the closing body tag
        end = src.rfind("</body>")
        if end == -1:
            return "NO </body>"
        src = src[:end] + "\n" + FOOTER + "\n\n" + src[end:]
        note = "added"

    if src != original and not dry:
        open(path, "w", encoding="utf-8").write(src)
    return note


def process_opfor(dry=False):
    path = "opfor-command.html"
    src = original = open(path, encoding="utf-8").read()
    notes = []

    if ".bt-foot" not in src:
        anchor = "  .bt-back { display:inline-block;"
        i = src.index(anchor)
        src = src[:i] + OPFOR_CSS.lstrip("\n") + src[i:]
        notes.append("css")

    if 'class="bt-foot"' not in src:
        end = src.rfind("</body>")
        src = src[:end] + OPFOR_STRIP + "\n\n" + src[end:]
        notes.append("strip")

    if src != original and not dry:
        open(path, "w", encoding="utf-8").write(src)
    return ", ".join(notes)


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    files = [f for f in sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html"))
             if os.path.basename(f) not in EXCLUDE]
    counts = {}
    for f in files:
        n = process(f, dry)
        if n:
            counts[n] = counts.get(n, 0) + 1
    o = process_opfor(dry)
    print("footers: " + ", ".join("%s %d" % (k, v) for k, v in counts.items()))
    print("opfor-command.html: " + (o or "unchanged"))
