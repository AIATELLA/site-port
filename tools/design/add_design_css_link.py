"""Phase B: add design/design.css as the first stylesheet on every page.

Inserts:
    <link rel="stylesheet" href="/design/design.css">
immediately before each page's existing fonts.css <link>, using a
root-relative href. Root-relative matters: blog-details/ pages sit one
directory down and 404.html is served from arbitrary paths, so a relative
href would break; the local server's (and the eventual production site's)
root is the repo root, so /design/design.css resolves correctly everywhere.

Idempotent: if a page already has a stylesheet link whose href resolves to
design/design.css (leading slash or not), it is left untouched -- re-running
never duplicates the tag.

Reuses tools/seo/pages.py (the existing page-manifest machinery) and
tools/seo/htmlhead.py (read/write helpers) rather than re-deriving the page
list or hand-rolling file I/O.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "seo"))
import pages  # noqa: E402
import htmlhead as H  # noqa: E402

DESIGN_LINK = '<link rel="stylesheet" href="/design/design.css">'
ALREADY_RE = re.compile(r'<link\b[^>]*\bhref="[^"]*design/design\.css"[^>]*>')
FONTS_LINK_RE = re.compile(r'<link\b[^>]*\bhref="[^"]*assets/css/fonts\.css"[^>]*>')


def apply_one(p):
    path = p["file"]
    if not os.path.exists(path):
        return None
    t = H.read(path)
    if ALREADY_RE.search(t):
        return "already-present"
    m = FONTS_LINK_RE.search(t)
    if not m:
        return "no-fonts-link-found"
    t2 = t[:m.start()] + DESIGN_LINK + "\n" + t[m.start():]
    H.write(path, t2)
    return "inserted"


if __name__ == "__main__":
    counts = {}
    for p in pages.PAGES:
        result = apply_one(p)
        counts[result] = counts.get(result, 0) + 1
        print("%-70s %s" % (p["file"], result))
    print(counts)
