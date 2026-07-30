"""Rewrite <head> metadata from the manifest. Idempotent."""
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402
import htmlhead as H  # noqa: E402

OG_DIR = "assets/images/og"


def canonical(p):
    return pages.SITE + ("/" if p["path"] == "/" else p["path"])


def apply_one(p):
    path = p["file"]
    if not os.path.exists(path):
        return False
    t = H.read(path)
    title = html.escape(p["title"], quote=False)
    desc = html.escape(p["desc"], quote=True)
    can = canonical(p)
    img = "%s/%s/%s.png" % (pages.SITE, OG_DIR, p["og"])

    t = H.replace_title(t, title)
    t, _ = H.replace_tag(t, "meta", "name", "description",
                         '<meta name="description" content="%s">' % desc)
    t, _ = H.replace_tag(t, "meta", "name", "viewport",
                         '<meta name="viewport" content="width=device-width, initial-scale=1">')
    t, _ = H.replace_tag(t, "meta", "name", "robots",
                         '<meta name="robots" content="%s">' % p["robots"])
    t, _ = H.replace_tag(t, "link", "rel", "canonical",
                         '<link rel="canonical" href="%s">' % can)
    pairs = [
        ("property", "og:type", "article" if p["file"].startswith("blog-details/") else "website"),
        ("property", "og:site_name", "AIATELLA"),
        ("property", "og:locale", "en_GB"),
        ("property", "og:title", title),
        ("property", "og:description", desc),
        ("property", "og:url", can),
        ("property", "og:image", img),
        ("property", "og:image:width", "1200"),
        ("property", "og:image:height", "630"),
        ("property", "og:image:alt", "AIATELLA — %s" % title.split(" | ")[0]),
        ("name", "twitter:card", "summary_large_image"),
        ("name", "twitter:title", title),
        ("name", "twitter:description", desc),
        ("name", "twitter:image", img),
    ]
    for attr, key, val in pairs:
        tag = '<meta %s="%s" content="%s">' % (attr, key, val)
        t, _ = H.replace_tag(t, "meta", attr, key, tag)

    # Framer search index is not wired up in the port; remove the dead refs.
    for key in ("framer-search-index", "framer-search-index-fallback"):
        t = H.strip_tag(t, "meta", "name", key)

    H.write(path, t)
    return True


if __name__ == "__main__":
    n = sum(1 for p in pages.PAGES if apply_one(p))
    print("rewrote %d files" % n)
