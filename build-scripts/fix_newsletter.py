#!/usr/bin/env python3
"""Make the 32 newsletter forms accessible and keep readers on the page.

Before: every form posted to Mailchimp with target="_blank", so subscribing
threw the reader into a new tab on a Mailchimp page. The name and email
fields had a placeholder and no label, which is the one thing a screen
reader cannot recover from.

After: labelled fields with autocomplete, and site.js submits through
Mailchimp's JSONP endpoint so the confirmation appears in place. With
JavaScript off the form still posts normally, just in the same tab.
"""
import glob
import re
import sys

FORM_RE = re.compile(r'<form\b[^>]*list-manage\.com[^>]*>', re.I)


def fix_form_tag(tag):
    if "data-mc-ajax" not in tag:
        tag = tag[:-1].rstrip() + " data-mc-ajax>"
    # the new tab is what site.js replaces
    tag = tag.replace(' target="_blank"', "").replace(" target='_blank'", "")
    return tag


def label_for(src, name, label_text, autocomplete, kind):
    """Give every <input name=NAME> an id, a visually hidden label and an
    autocomplete hint. Ids are made unique per page by index."""
    out = []
    pos = 0
    n = 0
    pattern = re.compile(r'<input\b[^>]*name="%s"[^>]*>' % re.escape(name), re.I)
    for m in pattern.finditer(src):
        tag = m.group(0)
        out.append(src[pos:m.start()])
        pos = m.end()
        n += 1
        ident = "nl-%s-%d" % (kind, n)
        if 'id="' not in tag:
            tag = tag[:-1].rstrip() + ' id="%s"' % ident + ">"
        else:
            ident = re.search(r'id="([^"]*)"', tag).group(1)
        if "autocomplete=" not in tag:
            tag = tag[:-1].rstrip() + ' autocomplete="%s"' % autocomplete + ">"
        # drop a redundant aria-label now that there is a real <label>
        tag = re.sub(r'\s*aria-label="[^"]*"', "", tag)
        out.append('<label class="sr-only" for="%s">%s</label>%s'
                   % (ident, label_text, tag))
    out.append(src[pos:])
    return "".join(out), n


def process(path, dry=False):
    src = original = open(path, encoding="utf-8").read()
    notes = []

    if not FORM_RE.search(src):
        return notes

    src = FORM_RE.sub(lambda m: fix_form_tag(m.group(0)), src)
    if src != original:
        notes.append("form-tag")

    before = src
    src, n = label_for(src, "EMAIL", "Email address", "email", "email")
    if n and src != before:
        notes.append("email-label x%d" % n)
    before = src
    src, n = label_for(src, "FNAME", "First name", "given-name", "fname")
    if n and src != before:
        notes.append("fname-label x%d" % n)

    # The Mailchimp legal line was #444 on near-black: 1.92:1.
    before = src
    src = src.replace('style="margin-top:14px; font-size:0.78rem; color:#444;"',
                      'class="form-legal" style="margin-top:14px; font-size:0.78rem;"')
    src = src.replace('<a href="https://mailchimp.com/legal/privacy/" target="_blank" style="color:#444;" rel="noopener">',
                      '<a href="https://mailchimp.com/legal/privacy/" target="_blank" rel="noopener">')
    if src != before:
        notes.append("legal-contrast")

    if src != original and not dry:
        open(path, "w", encoding="utf-8").write(src)
    return notes


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    total = 0
    for f in sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html")):
        n = process(f, dry)
        if n:
            print("%-44s %s" % (f, ", ".join(n)))
            total += 1
    print("\n%d files touched" % total)
