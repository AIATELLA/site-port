"""Phase F: render the nav and footer partials into every page.

The problem this fixes: <nav> and <footer> markup was copy-pasted across
all 25 pages -- 75 <nav> instances (only 25 distinct), 75 <footer>
instances (only 33 distinct), together about 60% of the site's HTML
bytes. Both are now defined exactly once, in partials/nav.html and
partials/footer.html, and this script renders them into every page
between managed HTML-comment markers, the same way tools/seo/*.py manage
their own blocks.

Why one marker pair *per breakpoint* rather than one `partial:nav` block
per component (as a first cut might assume): a <nav>/<footer>'s three
breakpoint variants (desktop/tablet/mobile for nav; desktop/tablet/phone
for footer) are genuinely different markup, not a restyle (see
phase-e-report.md), and Framer interleaves each variant's <nav>/<footer>
with a page-specific wrapper div (a per-page container class plus
`ssr-variant hidden-<hash>` classes that the page's OWN stylesheet
defines for breakpoint visibility -- confirmed by grepping e.g.
`.hidden-70vk7t{display:none!important}` in privacy.css). That wrapper
chrome is real per-page infrastructure, not reusable content, so it is
left untouched, outside the managed blocks; only the <nav>/<footer>
element itself is templated. Because the three variants are not always
in the same document order on every page (some pages emit
desktop/tablet/mobile, others desktop/mobile/tablet), a single
"partial:nav start/end" span can't unambiguously address one variant --
hence one clearly-named marker per breakpoint:

    <!-- partial:nav:desktop start -->  ... <!-- partial:nav:desktop end -->
    <!-- partial:nav:tablet start -->   ... <!-- partial:nav:tablet end -->
    <!-- partial:nav:mobile start -->   ... <!-- partial:nav:mobile end -->
    <!-- partial:footer:desktop start --> ... end
    <!-- partial:footer:tablet start -->  ... end
    <!-- partial:footer:phone start -->   ... end

What varies per page, and nothing else (verified by reconstructing all
25 pages x 6 instances = 150 nav/footer instances byte-for-byte from the
template before this script was written):

  - `{{DEPTH}}` -- "" for root-level pages, "../" for blog-details/*.
  - `{{CUR:slug}}` -- expands to ' data-framer-page-link-current="true"'
    when `slug` names the page currently being marked "current" in the
    nav/footer link list, else "". EFFECTIVE_CURRENT below is NOT simply
    "the page's own filename": five pages already carry Framer's own
    pre-existing bug where the footer's "current" link points at
    privacy.html instead of the viewed page (contact-thanks, cookies,
    terms, waitlist-thanks all do this; security.html is the one
    "utility" page that computes it correctly). This script preserves
    that exactly rather than silently "fixing" it, per the pure-refactor
    constraint.

Two more per-page differences were found and judged incidental (normalized
away, not parameterized) because they never change what a browser
renders -- both are documented at length in phase-f-report.md:
  - the logo <img>'s `sizes` attribute appeared in three textually
    different but behaviourally identical forms (reversed clause order;
    a stale pre-Phase-C 810px boundary on company.html; and a `.98`
    sub-pixel suffix on index.html/company.html) -- all three ways refer
    to the exact same srcset candidate, so one canonical form is used
    everywhere.
  - 404.html alone used site-root-absolute paths ("/index.html",
    "/assets/...") instead of the plain-relative convention every other
    root page uses; both resolve identically once served from the site's
    own domain root, so 404.html now gets the same relative form as
    everyone else.

Idempotent: running this twice produces byte-identical output (second
run finds the markers already in place and only refreshes their inner
content, which renders the same). Run order: prettify_html.py, then this
script, then the tools/seo/*.py generators -- see tools/README.md.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTIALS_DIR = os.path.join(ROOT, "partials")

# Framer's own per-breakpoint data-framer-name values, keyed by our
# lower-case breakpoint id.
NAV_BREAKPOINTS = [("desktop", "Desktop"), ("tablet", "Tablet"), ("mobile", "Mobile / Closed")]
FOOTER_BREAKPOINTS = [("desktop", "Desktop"), ("tablet", "Tablet"), ("phone", "Phone")]

# Per-page "current nav/footer link" identity. Preserves a pre-existing
# quirk in the ported site rather than correcting it: contact-thanks,
# cookies, terms and waitlist-thanks already mark "privacy.html" current
# in their footer (not their own page); security.html is the one utility
# page that gets it right. 404.html and every blog-details/* page mark
# nothing at all (their own page is never a nav/footer link target).
EFFECTIVE_CURRENT = {
    "404.html": None,
    "approach.html": "approach",
    "blog.html": "blog",
    "company.html": "company",
    "contact.html": "contact",
    "contact-thanks.html": "privacy",
    "cookies.html": "privacy",
    "index.html": "index",
    "privacy.html": "privacy",
    "security.html": "security",
    "solutions.html": "solutions",
    "terms.html": "privacy",
    "waitlist.html": "waitlist",
    "waitlist-thanks.html": "privacy",
}

ROOT_FILES = sorted(EFFECTIVE_CURRENT.keys())
BLOG_DETAILS = sorted(
    p.replace(ROOT + os.sep, "").replace("\\", "/")
    for p in glob.glob(os.path.join(ROOT, "blog-details", "*.html"))
)
ALL_FILES = ROOT_FILES + BLOG_DETAILS


def effective_current(fname):
    fname = fname.replace("\\", "/")
    if fname.startswith("blog-details/"):
        return None
    return EFFECTIVE_CURRENT[fname]


def depth_for(fname):
    fname = fname.replace("\\", "/")
    return "../" if fname.startswith("blog-details/") else ""


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def load_partial_sections(path, ids):
    """Split a partials/*.html file into {breakpoint_id: raw_template_text}
    using the <!-- breakpoint: id --> / <!-- /breakpoint: id --> markers."""
    text = read(path)
    out = {}
    for bp_id, _ in ids:
        m = re.search(
            r"<!-- breakpoint: %s -->\n(.*?)\n<!-- /breakpoint: %s -->" % (bp_id, bp_id),
            text, re.S)
        if not m:
            raise ValueError("breakpoint %r not found in %s" % (bp_id, path))
        out[bp_id] = m.group(1)
    return out


CUR_RE = re.compile(r"\{\{CUR:([\w-]+)\}\}")


def render(template, depth, current_slug):
    text = template.replace("{{DEPTH}}", depth)
    text = CUR_RE.sub(
        lambda m: ' data-framer-page-link-current="true"' if m.group(1) == current_slug else "",
        text)
    return text


def reindent(text, indent):
    """Add `indent` spaces to every line (partials/*.html store content
    dedented to a zero baseline; this re-establishes the absolute column
    the tag needs to sit at in a given page, preserving the relative
    nesting already present in the template)."""
    lines = text.split("\n")
    return "\n".join((" " * indent + l if l else l) for l in lines)


def build_payload(indent, start_marker, body, end_marker):
    return "%s%s\n%s\n%s%s" % (
        " " * indent, start_marker, reindent(body, indent), " " * indent, end_marker)


def find_balanced_tag(text, tag, name, start=0):
    """Locate a <tag ... data-framer-name="name" ...>...</tag> block
    (balanced against nested same-name tags) starting the search at
    `start`. Returns (block_start, block_end, line_indent) or None."""
    open_re = re.compile(r'<%s\b[^>]*>' % tag)
    tag_re = re.compile(r'<(/?)%s\b[^>]*>' % tag)
    pos = start
    while True:
        m = open_re.search(text, pos)
        if not m:
            return None
        if ('data-framer-name="%s"' % name) not in m.group(0):
            pos = m.end()
            continue
        block_start = m.start()
        depth = 1
        scan = m.end()
        while depth > 0:
            m2 = tag_re.search(text, scan)
            if m2 is None:
                raise ValueError("unbalanced <%s> in document" % tag)
            depth += -1 if m2.group(1) == "/" else 1
            scan = m2.end()
        block_end = scan
        line_start = text.rfind("\n", 0, block_start) + 1
        indent = block_start - line_start
        # only a genuine indent (nothing but spaces before the tag)
        if text[line_start:block_start].strip() == "":
            return block_start, block_end, indent, line_start
        pos = m.end()
    return None


def upsert_component(text, component, bp_id, framer_name, tag, rendered_body):
    start_marker = "<!-- partial:%s:%s start -->" % (component, bp_id)
    end_marker = "<!-- partial:%s:%s end -->" % (component, bp_id)

    existing = re.search(re.escape(start_marker), text)
    if existing:
        a = existing.start()
        line_start = text.rfind("\n", 0, a) + 1
        indent = a - line_start
        b = text.index(end_marker) + len(end_marker)
        payload = build_payload(indent, start_marker, rendered_body, end_marker)
        return text[:line_start] + payload + text[b:], True

    found = find_balanced_tag(text, tag, framer_name)
    if not found:
        return text, False
    block_start, block_end, indent, line_start = found
    payload = build_payload(indent, start_marker, rendered_body, end_marker)
    return text[:line_start] + payload + text[block_end:], True


def process_file(fname, nav_tpl, foot_tpl):
    path = os.path.join(ROOT, fname)
    text = read(path)
    depth = depth_for(fname)
    current = effective_current(fname)
    changed_any = False

    for bp_id, framer_name in NAV_BREAKPOINTS:
        rendered = render(nav_tpl[bp_id], depth, current)
        text, touched = upsert_component(text, "nav", bp_id, framer_name, "nav", rendered)
        changed_any = changed_any or touched

    for bp_id, framer_name in FOOTER_BREAKPOINTS:
        rendered = render(foot_tpl[bp_id], depth, current)
        text, touched = upsert_component(text, "footer", bp_id, framer_name, "footer", rendered)
        changed_any = changed_any or touched

    write(path, text)
    return changed_any


def main():
    nav_tpl = load_partial_sections(os.path.join(PARTIALS_DIR, "nav.html"), NAV_BREAKPOINTS)
    foot_tpl = load_partial_sections(os.path.join(PARTIALS_DIR, "footer.html"), FOOTER_BREAKPOINTS)

    n = 0
    for fname in ALL_FILES:
        if process_file(fname, nav_tpl, foot_tpl):
            n += 1
    print("rendered nav+footer partials into %d/%d files" % (n, len(ALL_FILES)))


if __name__ == "__main__":
    sys.exit(main())
