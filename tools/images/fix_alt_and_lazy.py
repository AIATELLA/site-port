"""Phase G Step 3: correct alt text and add loading="lazy" to below-the-
fold images. Spec: .superpowers/sdd/phase-g-images/task-1-brief.md Step 3.

3a (the logo) is handled by hand-editing partials/nav.html and
partials/footer.html directly (alt="" + aria-label="AIATELLA -- home" on
the nav link), then tools/build-partials.py -- not by this script. This
script additionally normalises the ONE extra hardcoded logo instance
that lives outside the partial system: company.html has a page-specific
".company__nav-logo-2" hero decoration (same 5a4Cx6...png file) that
build-partials.py never touches because it isn't part of <nav>/<footer>.
Its wrapping div already carries aria-label="Logo" (it is not a link, so
no "home" language applies there); this script gives its <img> alt=""
for the same reason as every other logo copy. That decorative logo
occurrence is also the answer to the brief's predicted "one straggler"
on company.html (19 <img> tags = 7 logo copies -- 6 from the partials +
this one -- + 12 people, not 6 + 12; an audit of all 25 pages found zero
truly unclassified images).

3b replaces the 14 copy-pasted-wrong alts and fills in the alt for every
other content photo, keyed by filename (ALT_TABLE below, transcribed
verbatim from the brief). An <img> whose file is neither the logo nor in
ALT_TABLE is left completely untouched and printed as an unresolved
straggler -- inventing alt text is worse than missing it.

3c adds loading="lazy" to every <img> except the 3 nav logo copies
(identified by the <!-- partial:nav:* start/end --> markers Phase F
left in place -- they render above the fold on every page) and the
first non-nav <img> in document order on each page (the LCP candidate).
Footer logo copies are below the fold and DO get lazy. An <img> that
already carries loading="lazy" (9 on company.html) is left alone rather
than duplicating the attribute.

Idempotent: alt values are exact-match fixed points and the lazy check
looks for the attribute before adding it, so a second run changes
nothing.
"""
import os
import re
import sys

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "seo"))
import pages  # noqa: E402

IMG_RE = re.compile(r"<img\b[^>]*?>", re.I)
SRC_RE = re.compile(r'\bsrc="([^"]*)"')
ALT_RE = re.compile(r'\balt(?:="[^"]*")?')
NAV_SPAN_RE = re.compile(r"<!-- partial:nav:\w+ start -->.*?<!-- partial:nav:\w+ end -->", re.S)

LOGO = "5a4Cx6gEHpj0e7cfQX0qezC0eI.png"

ALT_TABLE = {
    "zmSHY0fyBbl0hEXJfK1Gmaj3bt8.jpg":
        "Jack Parker, AIATELLA co-founder and CEO, speaking at a healthcare conference",
    "xLmROilZT4Qqvv7Dpl3dRJrwXM.jpeg":
        "Onni Eriksson, AIATELLA co-founder and CTO, presenting at a startup event",
    "9XUaoqS8rNc7BpxyKVnFusVkonI.jpg":
        "Jari Salo, AIATELLA Chief Information Officer",
    "31uJ2vAdIqQ0T4hiXe3RHH0Pnr8.webp":
        "Scott Flamm, AIATELLA medical advisor",
    "vunTJuLw55lTk72g86Fr9AyqtF4.jpg":
        "Franz Wiesbauer, AIATELLA medical advisor",
    "W2m1ZFRTnhFp4rueu0PEdYorpM.jpg":
        "Anand Prabhakar, AIATELLA medical advisor",
    "hLe4mIiCogAFXw15gaXlsx5NmkE.jpeg":
        "Molly O'Neil, AIATELLA advisor",
    "NAAuU9yLGNwIdBrnccDx03yg.webp":
        "Heikki Väänänen, AIATELLA advisor",
    "h0wXKbPcbAV1jwCi9ZgRa3Zps.webp":
        "Helen Chamberlain, AIATELLA advisor",
    "4hB3Gti272qT0aRT7ygcZK80M.webp":
        "Iain Taylor, AIATELLA advisor",
    "KJZYXY8TXeioldOxNIGc34zNXdY.jpeg":
        "Daniel Young, AIATELLA advisor",
    "mB3RdUqmGKRGHvtX5aB6RvotY.webp":
        "Risto Ilmoniemi, AIATELLA advisor",
    "E4n1OoSskKL9XeqtpPfz9ABTko.jpg":
        "Anatomical model of a human heart",
    "UdbgU2ccMT1MpldZdVEZ5Ba5gfA.jpg":
        "Radiographer preparing a patient for a CT scan",
    "NvfA30fvPewdSQKgXn74a1DoWQ0.jpeg":
        "Physician reassuring an older patient during a consultation",
    "CwKkH5OlZgLkquYgdev37jLaJ3c.jpg":
        "AIATELLA team demonstrating its imaging software at a startup event",
    "eLmqBaPRGyTXvJQkoeThpTiIEE.jpg":
        "Attendees at the HI NENC event on early detection of cardiovascular disease",
    "0kP6qzWo4fzbbACe9pMK27rpAs.webp":
        "Ultrasound scan being performed on a patient, with the live scan shown on screen",
    "aRh6PSUc4BxCb2TaZxcBTDEnQU.png":
        "Illustration of a red blood cell",
    "KnKZtlCMEsJFAnG2t8Pz0vuPP5U.jpg":
        "Cardiac MRI scan showing the heart in cross-section",
    "tuUiD2TDJeSvoPx25ATV1nHTGkY.png":
        "Three-dimensional segmentation of an aorta rendered in red",
    "N5cEbxRpVeEN8zxWBa27KYWw5I.png":
        "Automated Imaging Measurement report on screen, showing aorta measurements",
    "TiIgVJqdfp7Xe2j41XUsLQsUHQ.jpg":
        "Axial MRI slice with the aorta highlighted in red",
    "7EsS146cgyzhvtXBgrqf6T3Daxw.jpg":
        "Clinician in scrubs reviewing imaging results on a tablet",
    "tg3eFSW6QoGtQMIxR22Av9D1978.jpg":
        "Sonographer operating the control panel of an ultrasound machine",
}


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def set_alt(tag, value):
    escaped = value  # no '&' or '"' in any table value; apostrophes are literal
    new_attr = 'alt="%s"' % escaped
    if ALT_RE.search(tag):
        return ALT_RE.sub(new_attr, tag, count=1)
    return tag  # unreachable in practice -- every <img> here carries alt/alt=""


def add_lazy(tag):
    if re.search(r'\bloading="', tag):
        return tag  # already present (e.g. 9 pre-existing on company.html) -- don't duplicate
    return tag.replace('decoding="async"', 'decoding="async" loading="lazy"', 1)


def process(text, page_label, stragglers):
    nav_spans = [(m.start(), m.end()) for m in NAV_SPAN_RE.finditer(text)]

    def in_nav(pos):
        return any(s <= pos < e for s, e in nav_spans)

    out = []
    last = 0
    seen_first_content = False
    for m in IMG_RE.finditer(text):
        tag = m.group(0)
        out.append(text[last:m.start()])

        sm = SRC_RE.search(tag)
        base = os.path.basename(sm.group(1)) if sm else None
        nav = in_nav(m.start())

        if base == LOGO:
            tag = set_alt(tag, "")
        elif base in ALT_TABLE:
            tag = set_alt(tag, ALT_TABLE[base])
        elif base is not None:
            stragglers.append((page_label, base, tag[:200]))

        if not nav:
            if not seen_first_content:
                seen_first_content = True  # LCP candidate: no lazy
            else:
                tag = add_lazy(tag)

        out.append(tag)
        last = m.end()
    out.append(text[last:])
    return "".join(out)


def main():
    check = "--check" in sys.argv
    changed_files = []
    stragglers = []
    for p in pages.PAGES:
        path = os.path.join(ROOT, p["file"])
        if not os.path.exists(path):
            continue
        text = read(path)
        new_text = process(text, p["file"], stragglers)
        if new_text != text:
            changed_files.append(p["file"])
            if not check:
                write(path, new_text)

    if stragglers:
        print("Unresolved images (neither logo nor in ALT_TABLE) -- left untouched:")
        for page_label, base, snippet in stragglers:
            print("  %s: %s\n    %s" % (page_label, base, snippet))

    if check:
        if changed_files:
            print("STALE -- %d file(s) need rewriting:" % len(changed_files))
            for f in changed_files:
                print("  " + f)
            return 1
        print("clean -- no changes needed")
        return 0

    print("rewrote alt/lazy in %d file(s):" % len(changed_files))
    for f in changed_files:
        print("  " + f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
