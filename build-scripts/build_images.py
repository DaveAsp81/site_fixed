#!/usr/bin/env python3
"""Generate responsive WebP derivatives for every source image under assets/images.

For each source, writes <name>-<width>.webp for each target width that is not an
upscale, plus one at the source width if it is smaller than the smallest target.
Re-run it after adding images; it skips derivatives that are already up to date.
"""
import os
import re
import sys
from PIL import Image

SRC_ROOT = "assets/images"
WIDTHS = [480, 800, 1280, 1600]
QUALITY = 78
# Any "<name>-<width>.webp" is one of our own derivatives, not a source.
DERIVATIVE_RE = re.compile(r"-\d+\.webp$", re.I)
SOURCE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


# Sources below this are already small enough to serve as they are.
MIN_WIDTH = 600
MIN_BYTES = 40 * 1024


def targets_for(width):
    """Widths to emit for a source of the given width (never upscale).

    A source narrower than the smallest target still gets one derivative at
    its native width, so even the small schematics are served as WebP.
    """
    out = [w for w in WIDTHS if w <= width]
    return out or [width]


def build(force=False):
    made = saved = 0
    for root, _dirs, files in os.walk(SRC_ROOT):
        for name in sorted(files):
            stem, ext = os.path.splitext(name)
            if ext.lower() not in SOURCE_EXTS:
                continue
            if DERIVATIVE_RE.search(name):
                continue
            src = os.path.join(root, name)
            try:
                im = Image.open(src)
            except Exception as exc:  # not an image we can read
                print("  skip %s (%s)" % (src, exc))
                continue
            with im:
                if im.width < MIN_WIDTH and os.path.getsize(src) < MIN_BYTES:
                    continue
                im = im.convert("RGBA") if im.mode in ("P", "LA", "RGBA") else im.convert("RGB")
                src_mtime = os.path.getmtime(src)
                for w in targets_for(im.width):
                    dst = os.path.join(root, "%s-%d.webp" % (stem, w))
                    if (not force and os.path.exists(dst)
                            and os.path.getmtime(dst) >= src_mtime):
                        continue
                    h = max(1, round(im.height * w / im.width))
                    im.resize((w, h), Image.LANCZOS).save(
                        dst, "WEBP", quality=QUALITY, method=6)
                    made += 1
                    saved += os.path.getsize(src) - os.path.getsize(dst)
                    print("  %-58s %5.0f KB" % (dst, os.path.getsize(dst) / 1024))
    print("\n%d derivatives written" % made)


# One-offs: images referenced from CSS, where there is no <img> to carry a
# srcset. These keep their plain .webp name because style.css points at it.
CSS_BACKGROUNDS = [
    ("assets/images/hero-madcat.jpg", "assets/images/hero-madcat.webp"),
]


def build_css_backgrounds():
    for src, dst in CSS_BACKGROUNDS:
        if not os.path.exists(src):
            continue
        if (os.path.exists(dst)
                and os.path.getmtime(dst) >= os.path.getmtime(src)):
            continue
        with Image.open(src) as im:
            im.convert("RGB").save(dst, "WEBP", quality=80, method=6)
        print("  %-58s %5.0f KB (css background)"
              % (dst, os.path.getsize(dst) / 1024))


if __name__ == "__main__":
    build(force="--force" in sys.argv)
    build_css_backgrounds()
