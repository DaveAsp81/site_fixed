#!/usr/bin/env python3
"""Syntax-check every inline <script> and external JS file with node.

The tool pages carry tens of kilobytes of inline JavaScript each, so a bad
edit is easy to make and invisible until someone opens the page.
"""
import glob
import os
import re
import subprocess
import sys
import tempfile

SCRIPT_RE = re.compile(
    r'<script(?![^>]*\bsrc=)([^>]*)>(.*?)</script>', re.S | re.I)


def check_source(src, label, module=False):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(src)
        tmp = fh.name
    try:
        res = subprocess.run(["node", "--check", tmp],
                             capture_output=True, text=True)
        if res.returncode != 0:
            print("FAIL %s" % label)
            for line in res.stderr.strip().splitlines()[:6]:
                print("     " + line)
            return False
        return True
    finally:
        os.unlink(tmp)


def main():
    files = sorted(glob.glob("*.html")) + sorted(glob.glob("articles/*.html"))
    checked = failed = 0
    for path in files:
        src = open(path, encoding="utf-8").read()
        for i, m in enumerate(SCRIPT_RE.finditer(src), 1):
            attrs, body = m.group(1), m.group(2)
            if "application/ld+json" in attrs or "application/json" in attrs:
                continue
            if not body.strip():
                continue
            checked += 1
            if not check_source(body, "%s script #%d" % (path, i)):
                failed += 1

    for path in sorted(glob.glob("assets/js/*.js")) + ["sw.js"]:
        if not os.path.exists(path):
            continue
        checked += 1
        if not check_source(open(path, encoding="utf-8").read(), path):
            failed += 1

    # JSON-LD and data files have to parse too.
    import json
    for path in files:
        src = open(path, encoding="utf-8").read()
        for i, m in enumerate(re.finditer(
                r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>',
                src, re.S | re.I), 1):
            checked += 1
            try:
                json.loads(m.group(1))
            except Exception as exc:
                failed += 1
                print("FAIL %s JSON-LD #%d: %s" % (path, i, exc))
    for path in ["site.webmanifest", "force-packs.json",
                 "assets/data/paints.json", "assets/data/paint-schemes.json"]:
        if os.path.exists(path):
            checked += 1
            try:
                json.load(open(path, encoding="utf-8"))
            except Exception as exc:
                failed += 1
                print("FAIL %s: %s" % (path, exc))

    print("\n%d scripts/JSON checked, %d failed" % (checked, failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
