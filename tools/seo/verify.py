"""Verification suite for the SEO foundation work. Spec §7.
Run from the repo root. Exit 0 = all checks pass."""
import html as _html
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402
from htmlhead import read  # noqa: E402

FAILS = []
BASE = "http://127.0.0.1:8000"


def fail(check, msg):
    FAILS.append("[%s] %s" % (check, msg))


def head_of(text):
    m = re.search(r"<head[^>]*>(.*?)</head>", text, re.S)
    return m.group(1) if m else ""


def meta(head, attr, value):
    m = re.search(r"<meta\b[^>]*?\b%s=\"%s\"[^>]*?content=\"([^\"]*)\"" % (attr, re.escape(value)),
                  head, re.I)
    if m:
        return m.group(1)
    m = re.search(r"<meta\b[^>]*?content=\"([^\"]*)\"[^>]*?\b%s=\"%s\"" % (attr, re.escape(value)),
                  head, re.I)
    return m.group(1) if m else None


def existing(p):
    return os.path.exists(p["file"])


# 1 indexability
def check_1():
    for p in pages.PAGES:
        if not existing(p):
            fail(1, "missing file %s" % p["file"]); continue
        got = meta(head_of(read(p["file"])), "name", "robots")
        if got != p["robots"]:
            fail(1, "%s robots=%r expected %r" % (p["file"], got, p["robots"]))


# 2 metadata completeness
def check_2():
    for p in pages.PAGES:
        if not existing(p):
            continue
        t = read(p["file"]); h = head_of(t)
        m = re.search(r"<title\b[^>]*>(.*?)</title>", t, re.S)
        # The writer HTML-escapes (& -> &amp;, ' -> &#x27;), which is correct in
        # markup. Unescape before comparing, and so the length limits measure the
        # rendered string -- which is what Google counts.
        title = _html.unescape(m.group(1).strip()) if m else ""
        if title != p["title"]:
            fail(2, "%s title=%r expected %r" % (p["file"], title, p["title"]))
        if len(title) > 60:
            fail(2, "%s title %d chars > 60" % (p["file"], len(title)))
        d = _html.unescape(meta(h, "name", "description") or "")
        if d != p["desc"]:
            fail(2, "%s description=%r expected %r" % (p["file"], d[:70], p["desc"][:70]))
        if len(d) > 160:
            fail(2, "%s description %d chars > 160" % (p["file"], len(d)))
        for prop in ("og:title", "og:description", "og:url", "og:image",
                     "og:site_name", "og:type", "og:locale"):
            if not meta(h, "property", prop):
                fail(2, "%s missing %s" % (p["file"], prop))
        for nm in ("twitter:card", "twitter:title", "twitter:description", "twitter:image"):
            if not meta(h, "name", nm):
                fail(2, "%s missing %s" % (p["file"], nm))
        if "framer-search-index" in h:
            fail(2, "%s still has framer-search-index" % p["file"])
        vp = meta(h, "name", "viewport") or ""
        if "initial-scale=1" not in vp:
            fail(2, "%s viewport lacks initial-scale=1" % p["file"])


# 3 canonical correctness
def check_3():
    for p in pages.PAGES:
        if not existing(p):
            continue
        t = read(p["file"]); h = head_of(t)
        want = pages.SITE + ("" if p["path"] == "/" else p["path"]) + ("/" if p["path"] == "/" else "")
        m = re.search(r"<link\b[^>]*?rel=\"canonical\"[^>]*?href=\"([^\"]*)\"", h, re.I)
        can = m.group(1) if m else None
        if can != want:
            fail(3, "%s canonical=%r expected %r" % (p["file"], can, want))
        if meta(h, "property", "og:url") != want:
            fail(3, "%s og:url != canonical" % p["file"])
        if can and (".html" in can or "//www." not in can or not can.startswith("https://")):
            fail(3, "%s canonical not https/www/extensionless" % p["file"])


# 4 document structure
def check_4():
    for p in pages.PAGES:
        if not existing(p):
            continue
        t = read(p["file"])
        h1s = re.findall(r"<h1\b[^>]*>(.*?)</h1>", t, re.S)
        texts = {re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", x)).strip() for x in h1s}
        texts = {x for x in texts if x}
        if len(texts) != 1:
            fail(4, "%s has %d distinct h1 texts (want 1): %s"
                 % (p["file"], len(texts), sorted(texts)[:3]))
        if "<footer" not in t:
            fail(4, "%s has no <footer> landmark" % p["file"])


# 5 sitemap integrity
def check_5():
    if not os.path.exists("sitemap.xml"):
        fail(5, "sitemap.xml missing"); return
    locs = re.findall(r"<loc>([^<]+)</loc>", read("sitemap.xml"))
    want = {pages.SITE + ("/" if p["path"] == "/" else p["path"]) for p in pages.INDEXABLE}
    if len(locs) != len(set(locs)):
        fail(5, "sitemap has duplicates")
    if set(locs) != want:
        for x in sorted(want - set(locs)):
            fail(5, "sitemap missing %s" % x)
        for x in sorted(set(locs) - want):
            fail(5, "sitemap has unexpected %s" % x)
    noidx = {pages.SITE + p["path"] for p in pages.PAGES if "noindex" in p["robots"]}
    for x in sorted(noidx & set(locs)):
        fail(5, "sitemap lists noindex page %s" % x)
    if not os.path.exists("robots.txt"):
        fail(5, "robots.txt missing")
    else:
        r = read("robots.txt")
        if "Sitemap: %s/sitemap.xml" % pages.SITE not in r:
            fail(5, "robots.txt sitemap line wrong (must be www)")


# 6 JSON-LD validity
def check_6():
    for p in pages.PAGES:
        if not existing(p) or not p["schema"]:
            continue
        blocks = re.findall(
            r"<script[^>]*application/ld\+json[^>]*>(.*?)</script>", read(p["file"]), re.S)
        if not blocks:
            fail(6, "%s expected schema %s, found none" % (p["file"], p["schema"]))
            continue
        types = set()
        for b in blocks:
            try:
                data = json.loads(b)
            except Exception as exc:
                fail(6, "%s invalid JSON-LD: %s" % (p["file"], exc)); continue
            for node in (data if isinstance(data, list) else [data]):
                if "@context" not in node:
                    fail(6, "%s JSON-LD missing @context" % p["file"])
                types.add(node.get("@type"))
        for want in p["schema"]:
            if want not in types:
                fail(6, "%s missing @type %s (got %s)" % (p["file"], want, sorted(types)))
        raw = read(p["file"])
        for banned in ("FDA", "CE mark", "CE-mark", "FDA-approved", "FDA cleared"):
            for b in blocks:
                if banned.lower() in b.lower():
                    fail(6, "%s schema contains regulatory claim %r" % (p["file"], banned))


# 7 og:image resolves at 1200x630
def png_size(path):
    with open(path, "rb") as fh:
        d = fh.read(33)
    if d[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")


def check_7():
    for p in pages.PAGES:
        if not existing(p):
            continue
        url = meta(head_of(read(p["file"])), "property", "og:image")
        if not url:
            continue
        if not url.startswith(pages.SITE + "/"):
            fail(7, "%s og:image not absolute: %s" % (p["file"], url)); continue
        rel = url[len(pages.SITE) + 1:]
        if not os.path.exists(rel):
            fail(7, "%s og:image file missing: %s" % (p["file"], rel)); continue
        size = png_size(rel)
        if size != (1200, 630):
            fail(7, "%s og:image is %s, want (1200, 630)" % (rel, size))


# 9 link integrity (8 and 12 are manual/scripted separately)
def check_9():
    for p in pages.PAGES:
        if not existing(p):
            continue
        d = os.path.dirname(p["file"])
        for href in set(re.findall(r'href="([^"#?][^"]*)"', read(p["file"]))):
            if re.match(r"^(https?:|mailto:|tel:|//|#)", href):
                continue
            target = os.path.normpath(os.path.join(d, href.split("#")[0].split("?")[0]))
            if not os.path.exists(target):
                fail(9, "%s -> broken link %s" % (p["file"], href))


# 11 analytics beacon present exactly once
def check_11():
    for p in pages.PAGES:
        if not existing(p):
            continue
        t = read(p["file"])
        n = t.count("static.cloudflareinsights.com/beacon.min.js")
        if n != 1:
            fail(11, "%s has %d Cloudflare beacon tags (want 1)" % (p["file"], n))
        if "TODO-CF-TOKEN" in t:
            fail(11, "%s still has placeholder Cloudflare token" % p["file"])


# 5b served URLs resolve (requires local server)
def check_serve():
    try:
        urllib.request.urlopen(BASE + "/index.html", timeout=3).read(1)
    except Exception:
        print("  (skipped served-URL check: no server on %s)" % BASE)
        return
    for p in pages.INDEXABLE:
        try:
            code = urllib.request.urlopen(BASE + "/" + p["file"], timeout=5).getcode()
        except Exception as exc:
            fail("serve", "%s not served: %s" % (p["file"], exc)); continue
        if code != 200:
            fail("serve", "%s -> HTTP %s" % (p["file"], code))


CHECKS = {1: check_1, 2: check_2, 3: check_3, 4: check_4, 5: check_5,
          6: check_6, 7: check_7, 9: check_9, 11: check_11}

if __name__ == "__main__":
    only = None
    if "--only" in sys.argv:
        only = int(sys.argv[sys.argv.index("--only") + 1])
    for num, fn in sorted(CHECKS.items()):
        if only and num != only:
            continue
        fn()
    if not only:
        check_serve()
    if FAILS:
        print("FAIL (%d)" % len(FAILS))
        for f in FAILS[:60]:
            print("  " + f)
        if len(FAILS) > 60:
            print("  ... and %d more" % (len(FAILS) - 60))
        sys.exit(1)
    print("PASS — all checks green")
