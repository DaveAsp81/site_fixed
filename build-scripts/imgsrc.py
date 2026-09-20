"""Shared helper: build srcset/src attributes for a source image path."""
import glob
import os
import re
from PIL import Image

WIDTHS = [480, 800, 1280, 1600]
_cache = {}


def variants(repo_path):
    """Return (list_of_(url_suffix,width), intrinsic_w, intrinsic_h) for a source
    image given as a repo-root-relative path. Empty list if no derivatives."""
    if repo_path in _cache:
        return _cache[repo_path]
    stem, _ext = os.path.splitext(repo_path)
    # Discover by glob rather than by the fixed ladder: sources narrower than
    # the smallest target get a single derivative at their native width.
    out = []
    for cand in glob.glob(glob.escape(stem) + "-*.webp"):
        m = re.match(r'^' + re.escape(stem) + r'-(\d+)\.webp$',
                     cand.replace(os.sep, "/"))
        if m:
            out.append((cand.replace(os.sep, "/"), int(m.group(1))))
    out.sort(key=lambda x: x[1])
    dims = (None, None)
    if os.path.exists(repo_path):
        try:
            with Image.open(repo_path) as im:
                dims = (im.width, im.height)
        except Exception:
            pass
    _cache[repo_path] = (out, dims[0], dims[1])
    return _cache[repo_path]


def img_attrs(repo_path, prefix, sizes, preferred=800):
    """Build src/srcset/width/height attribute string.

    prefix is what the page needs in front of a repo-root path (e.g. '../').
    Falls back to the original file when no derivatives exist.
    """
    vs, iw, ih = variants(repo_path)
    if not vs:
        attrs = 'src="%s%s"' % (prefix, repo_path)
    else:
        # src = the derivative closest to `preferred` without exceeding it,
        # else the smallest available.
        under = [v for v in vs if v[1] <= preferred] or [vs[0]]
        src = under[-1]
        srcset = ", ".join("%s%s %dw" % (prefix, p, w) for p, w in vs)
        attrs = 'src="%s%s" srcset="%s" sizes="%s"' % (
            prefix, src[0], srcset, sizes)
    if iw and ih:
        attrs += ' width="%d" height="%d"' % (iw, ih)
    return attrs
