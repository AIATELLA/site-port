"""Generate robots.txt and sitemap.xml from the manifest."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402

ROBOTS = """User-agent: *
Allow: /

Sitemap: {site}/sitemap.xml
""".format(site=pages.SITE)


def sitemap():
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages.INDEXABLE:
        loc = pages.SITE + ("/" if p["path"] == "/" else p["path"])
        out.append("  <url><loc>%s</loc></url>" % loc)
    out.append("</urlset>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    with open("robots.txt", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(ROBOTS)
    with open("sitemap.xml", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(sitemap())
    print("wrote robots.txt and sitemap.xml (%d URLs)" % len(pages.INDEXABLE))
