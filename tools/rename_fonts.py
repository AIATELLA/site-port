"""Give the webfont files human-readable names derived from their @font-face rules.

The Framer export ships 40 woff2 files with opaque hash names
(5vvr9Vy74if2I6bQbJvbw7SY1pQ.woff2), which tells a reader nothing about
which family, weight, style or unicode subset they hold. Every one of them
is declared in exactly one place -- assets/css/fonts.css -- so the family,
weight, style and unicode-range needed to name them properly are already
sitting right next to the url().

Naming follows the Fontsource convention, which is what most tooling and
most developers will recognise:

    inter-latin-400-normal.woff2
    inter-cyrillic-ext-700-italic.woff2
    manrope-500-normal.woff2          (no unicode-range declared)

Renames are pure: no bytes change, only filenames and the url() strings in
fonts.css. Run with --check to report drift without writing.

Framer bundled two vintages of Inter, so two faces can share family, weight
and style while declaring slightly different "latin" ranges (one includes
the superscript/subscript block U+2070, U+2074-207E, U+2080-208E, the other
does not). They cannot share a filename. Where that happens the *last*
declaration wins at render time for every overlapping codepoint, so the
last one gets the plain name and the shadowed earlier ones are suffixed
-shadowed. Naming it the other way round would put the obvious name on the
file the browser never actually uses.
"""
import os
import re
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(ROOT, "assets", "css", "fonts.css")

FACE = re.compile(r"@font-face\s*\{[^}]*\}")
URL = re.compile(r'url\("([^"]+)"\)')
PROP = lambda name, block: (re.search(r"%s:\s*([^;}]+)" % name, block) or [None, ""])[1].strip()

# Most specific range first -- a subset's range often contains a broader one's.
SUBSETS = [
    ("cyrillic-ext", "U+0460-052F"),
    ("cyrillic", "U+0400-045F"),
    ("greek-ext", "U+1F00-1FFF"),
    ("greek", "U+0370-03FF"),
    ("vietnamese", "U+1EA0-1EF9"),
    ("latin-ext", "U+0100-024F"),
    ("latin", "U+0000-00FF"),
]


def subset_of(unicode_range):
    for name, probe in SUBSETS:
        if probe in unicode_range:
            return name
    return None


def slug(family):
    return re.sub(r"[^a-z0-9]+", "-", family.strip().strip('"').lower()).strip("-")


def plan():
    """Return (renames, css_text) where renames is [(old_abs, new_abs, old_url, new_url)]."""
    with open(CSS, encoding="utf-8", newline="") as fh:
        css = fh.read()

    # Pass 1: work out the ideal stem for every face, in declaration order.
    faces = []
    for block in FACE.findall(css):
        m = URL.search(block)
        if not m:
            continue                                  # local("Arial") placeholder faces
        url = m.group(1)
        old_abs = os.path.normpath(os.path.join(os.path.dirname(CSS), url))
        if not os.path.exists(old_abs):
            raise SystemExit("fonts.css references a missing file: %s" % url)

        family = slug(PROP("font-family", block))
        weight = PROP("font-weight", block) or "400"
        style = PROP("font-style", block) or "normal"
        sub = subset_of(PROP("unicode-range", block))
        stem = "-".join([family] + ([sub] if sub else []) + [weight, style])
        faces.append(dict(url=url, old=old_abs, stem=stem,
                          ext=os.path.splitext(old_abs)[1]))

    # Pass 2: resolve stem collisions. The last declaration wins at render
    # time, so it keeps the plain name; earlier ones are marked shadowed.
    by_stem = {}
    for f in faces:
        by_stem.setdefault(f["stem"], []).append(f)
    for stem, group in by_stem.items():
        if len(group) == 1:
            group[0]["name"] = stem + group[0]["ext"]
            continue
        group[-1]["name"] = stem + group[-1]["ext"]
        for i, f in enumerate(group[:-1]):
            tag = "-shadowed" if len(group) == 2 else "-shadowed-%d" % (i + 1)
            f["name"] = stem + tag + f["ext"]

    renames = []
    for f in faces:
        new_abs = os.path.join(os.path.dirname(f["old"]), f["name"])
        if f["old"] != new_abs:
            new_url = f["url"].rsplit("/", 1)[0] + "/" + f["name"]
            renames.append((f["old"], new_abs, f["url"], new_url))

    return renames, css


def main():
    check = "--check" in sys.argv
    renames, css = plan()

    if not renames:
        print("clean -- every webfont already has a readable name")
        return

    print("%d file(s) to rename:" % len(renames))
    for old, new, _ou, _nu in renames:
        print("  %-46s -> %s" % (os.path.basename(old), os.path.basename(new)))

    if check:
        print("\nSTALE -- run without --check to apply")
        raise SystemExit(1)

    # A batch can legitimately swap two names (the plain name moves to
    # -shadowed while another file takes the plain name), so go via temporary
    # names. A direct pass would trip the overwrite guard, or clobber a file.
    targets = {os.path.normcase(n) for _o, n, _ou, _nu in renames}
    sources = {os.path.normcase(o) for o, _n, _ou, _nu in renames}
    for _old, new, _ou, _nu in renames:
        if os.path.exists(new) and os.path.normcase(new) not in sources:
            raise SystemExit("refusing to overwrite existing file: %s" % new)

    staged = []
    for old, new, _ou, _nu in renames:
        tmp = old + ".renaming"
        shutil.move(old, tmp)
        staged.append((tmp, new))
    for tmp, new in staged:
        if os.path.exists(new):
            raise SystemExit("target appeared during rename: %s" % new)
        shutil.move(tmp, new)
    assert not targets - {os.path.normcase(n) for _t, n in staged}

    out = css
    for _old, _new, old_url, new_url in renames:
        assert out.count('url("%s")' % old_url) == 1, old_url
        out = out.replace('url("%s")' % old_url, 'url("%s")' % new_url)
    with open(CSS, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)

    print("\nrenamed %d file(s) and rewrote fonts.css" % len(renames))
    verify()


def verify():
    """Every url() in every CSS file must resolve, and no font may be orphaned."""
    css_dir = os.path.join(ROOT, "assets", "css")
    referenced = set()
    checked = 0
    for name in sorted(os.listdir(css_dir)):
        if not name.endswith(".css"):
            continue
        path = os.path.join(css_dir, name)
        text = open(path, encoding="utf-8", newline="").read()
        for m in URL.finditer(text):
            url = m.group(1)
            if url.startswith("data:"):
                continue
            target = os.path.normpath(os.path.join(os.path.dirname(path), url.split("?")[0]))
            checked += 1
            if not os.path.exists(target):
                raise SystemExit("BROKEN url() in %s -> %s" % (name, url))
            referenced.add(os.path.normcase(target))

    orphans = []
    for sub in ("fonts", "third-party-fonts"):
        d = os.path.join(ROOT, "assets", sub)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if os.path.isfile(p) and os.path.normcase(p) not in referenced:
                orphans.append(os.path.relpath(p, ROOT).replace("\\", "/"))

    print("verification: %d url() reference(s) all resolve" % checked)
    if orphans:
        print("WARNING: %d font file(s) not referenced by any CSS:" % len(orphans))
        for o in orphans:
            print("   ", o)
    else:
        print("verification: no orphaned font files")


if __name__ == "__main__":
    if "--verify-only" in sys.argv:
        verify()
    else:
        main()
