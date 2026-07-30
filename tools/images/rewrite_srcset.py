"""Phase G: point every srcset entry at a real file of that width.
Spec: .superpowers/sdd/phase-g-images/task-1-brief.md Step 2.

Before this script, 174 of 182 <img> tags had a srcset whose every entry
pointed at the SAME original file -- Framer's real doubling ladder
(512/1024/2048/4096/intrinsic descriptors), but every "w" URL was
identical, so the descriptor was a lie and browsers always fetched the
largest rung. tools/images/build_variants.py (Step 1) made the files on
disk real; this script makes the markup that references them honest,
rewriting each srcset entry to the actual "<stem>-<w>w<ext> <w>w" variant
file, or the base filename itself for the top (cap) rung.

The relative path prefix ("assets/images/" on root pages, "../assets/
images/" under blog-details/, "{{DEPTH}}assets/images/" -- literally,
unresolved -- inside the two partials) is derived from each tag's own
existing src, never hardcoded, because getting it wrong silently breaks
every blog post page.

partials/nav.html and partials/footer.html are the source of truth for
the (identical, 151-copy) logo <img>; they are edited here directly and
tools/build-partials.py is invoked afterwards to propagate into all 25
pages -- editing the expanded copies inside page files directly would be
overwritten by the next partial regeneration.

Verification gate (run against the real, expanded 25 pages after
writing): every src/srcset URL resolves on disk relative to its page;
no two entries in one srcset repeat a URL (the original bug); every "w"
descriptor matches the real pixel width of the file it names.

--check reports which files' <img> markup would change, writes nothing,
and skips the write-only build-partials propagation and post-write
verification gate (there is nothing on disk yet to verify in check mode).
"""
import os
import re
import subprocess
import sys

from PIL import Image

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "seo"))
import pages  # noqa: E402

IMAGES_DIR = os.path.join(ROOT, "assets", "images")

IMG_RE = re.compile(r"<img\b[^>]*?>", re.I)
SRC_RE = re.compile(r'\bsrc="([^"]*)"')
SRCSET_RE = re.compile(r'\s*srcset="[^"]*"')

CANDIDATES = (512, 1024, 2048)

_width_cache = {}


def real_width(basename):
    if basename not in _width_cache:
        with Image.open(os.path.join(IMAGES_DIR, basename)) as im:
            _width_cache[basename] = im.size[0]
    return _width_cache[basename]


def ladder(w):
    cap = min(w, 2048)
    widths = sorted({c for c in CANDIDATES if c < w} | {cap})
    return widths, cap


def variant_name(basename, width, cap):
    if width == cap:
        return basename
    stem, ext = os.path.splitext(basename)
    return "%s-%dw%s" % (stem, width, ext)


def rewrite_tag(tag):
    sm = SRC_RE.search(tag)
    if not sm:
        return tag
    src = sm.group(1)
    if "/" in src:
        prefix, basename = src.rsplit("/", 1)
        prefix += "/"
    else:
        prefix, basename = "", src

    if not SRCSET_RE.search(tag):
        return tag  # nothing to do -- was already a bare src (W <= 512 originally)

    w = real_width(basename)
    if w <= 512:
        return SRCSET_RE.sub("", tag, count=1)

    widths, cap = ladder(w)
    # A rung is only real if build_variants.py actually wrote that file --
    # its not-smaller-than-source guard can (and does, for a handful of
    # already-efficient PNGs) legitimately skip one. Never fabricate an
    # entry pointing at a file that doesn't exist.
    widths = [width for width in widths
              if width == cap or os.path.exists(
                  os.path.join(IMAGES_DIR, variant_name(basename, width, cap)))]
    entries = ["%s%s %dw" % (prefix, variant_name(basename, width, cap), width)
               for width in widths]
    new_attr = ' srcset="%s"' % ",".join(entries)
    return SRCSET_RE.sub(new_attr, tag, count=1)


def rewrite_text(text):
    out = []
    last = 0
    changed = False
    for m in IMG_RE.finditer(text):
        out.append(text[last:m.start()])
        new_tag = rewrite_tag(m.group(0))
        if new_tag != m.group(0):
            changed = True
        out.append(new_tag)
        last = m.end()
    out.append(text[last:])
    return "".join(out), changed


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


PARTIALS = [os.path.join(ROOT, "partials", "nav.html"), os.path.join(ROOT, "partials", "footer.html")]


def targets():
    files = [os.path.join(ROOT, p["file"]) for p in pages.PAGES if os.path.exists(os.path.join(ROOT, p["file"]))]
    return files + PARTIALS


def run_build_partials():
    subprocess.run([sys.executable, os.path.join(TOOLS_DIR, "build-partials.py")],
                    check=True, cwd=ROOT)


# ---------------------------------------------------------------------------
# Verification gate
# ---------------------------------------------------------------------------

def verify():
    checked = 0
    failures = []
    for p in pages.PAGES:
        path = os.path.join(ROOT, p["file"])
        if not os.path.exists(path):
            continue
        page_dir = os.path.dirname(path)
        text = read(path)
        for m in IMG_RE.finditer(text):
            tag = m.group(0)
            sm = SRC_RE.search(tag)
            if sm:
                checked += 1
                resolved = os.path.normpath(os.path.join(page_dir, sm.group(1)))
                if not os.path.exists(resolved):
                    failures.append("%s: missing src %s" % (p["file"], sm.group(1)))
            ssm = re.search(r'\bsrcset="([^"]*)"', tag)
            if not ssm:
                continue
            urls_seen = set()
            for entry in ssm.group(1).split(","):
                entry = entry.strip()
                if not entry:
                    continue
                url, _, wdesc = entry.rpartition(" ")
                checked += 1
                if url in urls_seen:
                    failures.append("%s: duplicate srcset URL %s" % (p["file"], url))
                urls_seen.add(url)
                resolved = os.path.normpath(os.path.join(page_dir, url))
                if not os.path.exists(resolved):
                    failures.append("%s: missing srcset entry %s" % (p["file"], url))
                    continue
                want_w = int(wdesc.rstrip("w"))
                with Image.open(resolved) as im:
                    got_w = im.size[0]
                if got_w != want_w:
                    failures.append("%s: %s is %dpx wide, srcset says %dw"
                                    % (p["file"], url, got_w, want_w))
    return checked, failures


def main():
    check = "--check" in sys.argv
    changed_files = []
    for path in targets():
        text = read(path)
        new_text, changed = rewrite_text(text)
        if changed:
            changed_files.append(os.path.relpath(path, ROOT).replace("\\", "/"))
            if not check:
                write(path, new_text)

    if check:
        if changed_files:
            print("STALE -- %d file(s) need rewriting:" % len(changed_files))
            for f in changed_files:
                print("  " + f)
            return 1
        print("clean -- no changes needed")
        return 0

    print("rewrote srcset in %d file(s):" % len(changed_files))
    for f in changed_files:
        print("  " + f)

    run_build_partials()

    checked, failures = verify()
    print("\nverification: checked %d URL(s)" % checked)
    if failures:
        print("FAIL (%d)" % len(failures))
        for f in failures[:60]:
            print("  " + f)
        return 1
    print("PASS -- every src/srcset URL resolves, no duplicate entries, "
          "every w descriptor matches the real file width")
    return 0


if __name__ == "__main__":
    sys.exit(main())
