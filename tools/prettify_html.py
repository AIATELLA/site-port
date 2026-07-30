"""Phase D: reformat the 25 machine-generated HTML files into readable,
indented markup without changing anything a browser would render.

The hazard: whitespace between inline-level elements is significant in
HTML. Framer's export glues <span>/<a>/<p>/etc. together with zero
whitespace on purpose; inserting a newline+indent between two such
elements inserts a rendered space that was not there before.

Strategy: parse the document into a tree (custom, stdlib-only, no HTML
interpretation beyond what's needed to find tag/comment/text boundaries).
Then re-serialize. For each element we decide, conservatively, whether it
is safe to "expand" -- i.e. place its children on separate indented
lines -- or whether it must be reproduced byte-for-byte from the original
source with no whitespace changes at all ("opaque").

An element is opaque if any of:
  - its tag is one Framer/HTML commonly uses for inline or mixed
    text+inline content (span, a, p, h1-h6, em, strong, code, button,
    label, li) -- always opaque, regardless of actual content;
  - its tag is a raw-text element (script, style, textarea) -- content
    is not markup and must never be touched;
  - its tag is not on the small, explicit whitelist of container tags we
    know are safe to expand (div, section, nav, footer, header, main,
    ul, ol, form, fieldset, table*, picture, figure, article, aside,
    details, dl, html, head, body) -- anything else defaults to opaque;
  - it has a direct, non-whitespace text child (mixed text+element
    content) -- the general form of the rule above;
  - it has 2+ non-trivial children, is not itself flagged
    display:flex/grid/none, and two of its direct element children,
    with only comments/whitespace between them, are both tags that
    default to inline (or inline-block) rendering -- inserting
    whitespace there could produce a visible gap that was not there in
    the unformatted source.

When an element is opaque, its entire subtree -- open tag, children,
close tag -- is reproduced exactly as it appeared in the source: same
bytes, no exceptions. When it is not opaque ("expandable"), its
whitespace-only text children are dropped and replaced with the
formatter's own newline+indent, and each remaining child is placed on
its own line, recursing with the same rules.

Void elements (meta, link, img, br, ...) and self-closing tags have no
children and are reproduced as a single atomic token either way.

Usage:
    python tools/prettify_html.py FILE [FILE ...]
    python tools/prettify_html.py --check FILE [FILE ...]   (dry run, exit 1 on would-be change)

Idempotent: running it twice produces byte-identical output.
"""
import re
import sys

INDENT = "  "

VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
}

# Raw-text elements: content is never parsed as markup, and is never
# reformatted -- reproduced byte-exact always.
RAWTEXT_TAGS = {"script", "style", "textarea"}

# Tags we never expand into, regardless of what they contain. Matches the
# explicit list in the phase spec plus the raw-text elements above.
ALWAYS_OPAQUE_TAGS = {
    "span", "a", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "em", "strong", "code", "button", "label", "li",
} | RAWTEXT_TAGS

# Whitelist of container tags safe to expand (place children on separate
# lines) when the other opaqueness checks don't trip. Deliberately small;
# anything not listed here defaults to opaque -- "when in doubt, leave
# unformatted" per spec.
SAFE_CONTAINER_TAGS = {
    "html", "head", "body", "div", "section", "nav", "footer", "header",
    "main", "ul", "ol", "form", "fieldset", "table", "thead", "tbody",
    "tfoot", "tr", "colgroup", "picture", "figure", "article", "aside",
    "details", "dl",
}

# Tags that generate no visible box at all (UA stylesheet display:none,
# or not rendered full stop). Whitespace adjacent to these is exactly as
# harmless as whitespace adjacent to a comment -- skip them like comments
# when scanning for risky inline/inline adjacency.
NEVER_RENDERED_TAGS = {"script", "style", "link", "meta", "title", "base"}

# Tags that default to inline (or inline-block) rendering. Two of these
# sitting directly adjacent (nothing but comments/never-rendered
# tags/whitespace between) in a non-flex/grid/none parent would render a
# visible gap if we inserted whitespace between them, so such a parent is
# not expanded. Deliberately excludes p/h1-h6/li (ALWAYS_OPAQUE but
# default block-level -- adjacency between them is always whitespace-safe)
# and script/style/etc. (NEVER_RENDERED_TAGS, handled separately).
INLINE_RISK_TAGS = {
    "span", "a", "em", "strong", "code", "button", "label",
    "svg", "img", "input", "select", "textarea", "output", "small", "b",
    "i", "u", "sup", "sub", "mark", "time", "abbr", "cite", "q", "kbd",
    "samp", "var", "ins", "del", "s", "bdo", "bdi", "data", "dfn", "ruby",
    "rt", "rp", "audio", "video", "canvas", "iframe", "object", "embed",
}

_OPEN_TAG_RE = re.compile(
    r'<([a-zA-Z][a-zA-Z0-9:_-]*)'
    r'((?:"[^"]*"|\'[^\']*\'|/(?!>)|[^">/])*)'
    r'(/?)>', re.S)
_CLOSE_TAG_RE = re.compile(r'</\s*([a-zA-Z][a-zA-Z0-9:_-]*)\s*>')
_DISPLAY_RE = re.compile(r'display\s*:\s*(flex|grid|none)', re.I)


class ParseError(Exception):
    pass


# --- Parsing -----------------------------------------------------------
# A node is one of:
#   ("text", raw)
#   ("comment", raw)              raw includes "<!--" and "-->"
#   ("doctype", raw)
#   ("element", tag, open_raw, children, close_raw, void)
#       void=True  -> no children, close_raw is None, open_raw is the
#                     entire tag (self-closing or a known void element)

def parse(text):
    pos = 0
    n = len(text)
    root = []
    stack = []  # list of [tag, children, open_raw]

    def children():
        return stack[-1][1] if stack else root

    while pos < n:
        ch = text[pos]
        if text.startswith("<!--", pos):
            end = text.find("-->", pos + 4)
            if end == -1:
                raise ParseError("unterminated comment at %d" % pos)
            end += 3
            children().append(("comment", text[pos:end]))
            pos = end
            continue

        if text[pos:pos + 2] == "<!" and text[pos:pos + 9].lower() == "<!doctype":
            end = text.find(">", pos)
            if end == -1:
                raise ParseError("unterminated doctype at %d" % pos)
            end += 1
            children().append(("doctype", text[pos:end]))
            pos = end
            continue

        if ch == "<" and pos + 1 < n and text[pos + 1] == "/":
            m = _CLOSE_TAG_RE.match(text, pos)
            if not m:
                raise ParseError("malformed close tag at %d: %r" % (pos, text[pos:pos + 20]))
            tag = m.group(1)
            end = m.end()
            if not stack:
                raise ParseError("close tag %r with empty stack at %d" % (tag, pos))
            if stack[-1][0].lower() != tag.lower():
                raise ParseError(
                    "mismatched close tag: expected </%s>, got </%s> at %d"
                    % (stack[-1][0], tag, pos))
            open_tag, kids, open_raw = stack.pop()
            children_target = stack[-1][1] if stack else root
            children_target.append(("element", open_tag, open_raw, kids, text[pos:end], False))
            pos = end
            continue

        if ch == "<" and pos + 1 < n and (text[pos + 1].isalpha()):
            m = _OPEN_TAG_RE.match(text, pos)
            if not m:
                # Not a real tag start (e.g. a bare '<' in malformed markup).
                # Treat as a literal character to stay conservative.
                children().append(("text", "<"))
                pos += 1
                continue
            tag = m.group(1)
            end = m.end()
            open_raw = text[pos:end]
            self_close = m.group(3) == "/"
            tl = tag.lower()

            if tl in RAWTEXT_TAGS and not self_close:
                close_pat = re.compile(r"</\s*%s\s*>" % re.escape(tag), re.I)
                cm = close_pat.search(text, end)
                if not cm:
                    raise ParseError("unterminated <%s> at %d" % (tag, pos))
                raw_content = text[end:cm.start()]
                close_raw = text[cm.start():cm.end()]
                children().append(("element", tag, open_raw,
                                    [("text", raw_content)], close_raw, False))
                pos = cm.end()
                continue

            if tl in VOID_TAGS or self_close:
                children().append(("element", tag, open_raw, [], None, True))
                pos = end
                continue

            stack.append([tag, [], open_raw])
            pos = end
            continue

        # Plain text run up to the next '<'.
        nxt = text.find("<", pos + 1)
        if nxt == -1:
            children().append(("text", text[pos:]))
            pos = n
        else:
            children().append(("text", text[pos:nxt]))
            pos = nxt

    if stack:
        raise ParseError("unclosed tags at EOF: %s" % [s[0] for s in stack])
    return root


# --- Raw (byte-exact) reproduction -------------------------------------

def raw_serialize(node):
    kind = node[0]
    if kind in ("text", "comment", "doctype"):
        return node[1]
    # element
    _, tag, open_raw, kids, close_raw, void = node
    if void:
        return open_raw
    return open_raw + "".join(raw_serialize(c) for c in kids) + close_raw


def raw_serialize_all(nodes):
    return "".join(raw_serialize(n) for n in nodes)


# --- Opaqueness decision -------------------------------------------------

def _is_whitespace_text(node):
    return node[0] == "text" and node[1].strip() == ""


def _has_nonws_text_child(kids):
    return any(k[0] == "text" and k[1].strip() != "" for k in kids)


def _is_flex_like(open_raw):
    return bool(_DISPLAY_RE.search(open_raw))


def _has_risky_adjacency(kids, open_raw):
    if _is_flex_like(open_raw):
        return False
    prev_tag = None
    for k in kids:
        if k[0] == "text":
            if k[1].strip() != "":
                return True  # shouldn't reach here; caller already checked
            continue
        if k[0] == "comment":
            continue
        if k[0] == "element":
            t = k[1].lower()
            if t in NEVER_RENDERED_TAGS:
                continue
            if prev_tag is not None and prev_tag in INLINE_RISK_TAGS and t in INLINE_RISK_TAGS:
                return True
            prev_tag = t
    return False


def is_opaque(node):
    if node[0] != "element":
        return True
    _, tag, open_raw, kids, close_raw, void = node
    if void:
        return True
    tl = tag.lower()
    if tl in ALWAYS_OPAQUE_TAGS:
        return True
    if tl not in SAFE_CONTAINER_TAGS:
        return True
    if _has_nonws_text_child(kids):
        return True
    nontrivial = [k for k in kids if not _is_whitespace_text(k)]
    if len(nontrivial) >= 2 and _has_risky_adjacency(kids, open_raw):
        return True
    return False


# --- Pretty serialization -------------------------------------------------

def pretty_serialize_node(node, depth, out):
    if node[0] in ("text", "comment", "doctype"):
        out.append(raw_serialize(node))
        return
    _, tag, open_raw, kids, close_raw, void = node
    if void:
        out.append(open_raw)
        return
    if is_opaque(node):
        out.append(raw_serialize(node))
        return
    out.append(open_raw)
    nontrivial = [k for k in kids if not _is_whitespace_text(k)]
    if not nontrivial:
        out.append(close_raw)
        return
    pad = INDENT * (depth + 1)
    for k in nontrivial:
        out.append("\n" + pad)
        pretty_serialize_node(k, depth + 1, out)
    out.append("\n" + INDENT * depth)
    out.append(close_raw)


def pretty_serialize(nodes):
    """Top-level (document root) nodes: doctype, comments, <html>. Root
    sequencing is always safe to reformat -- these are document-structural
    nodes with no rendering ambiguity."""
    out = []
    nontrivial = [n for n in nodes if not _is_whitespace_text(n)]
    for i, n in enumerate(nontrivial):
        if i:
            out.append("\n")
        pretty_serialize_node(n, 0, out)
    out.append("\n")
    return "".join(out)


# --- Driver ----------------------------------------------------------------

def format_text(text):
    nodes = parse(text)
    # Self-check: raw reconstruction from the parse tree must equal the
    # original byte-for-byte. If it doesn't, the parser misunderstood the
    # markup and we must not proceed to reformat it.
    reconstructed = raw_serialize_all(nodes)
    if reconstructed != text:
        raise ParseError("raw round-trip mismatch -- refusing to format "
                          "(parser bug or unsupported markup)")
    return pretty_serialize(nodes)


def process_file(path, check=False):
    with open(path, encoding="utf-8", newline="") as fh:
        original = fh.read()
    formatted = format_text(original)
    if formatted == original:
        return False
    if not check:
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(formatted)
    return True


def main(argv):
    check = "--check" in argv
    files = [a for a in argv if a != "--check"]
    if not files:
        print("usage: prettify_html.py [--check] FILE [FILE ...]")
        return 2
    changed = []
    for f in files:
        try:
            did_change = process_file(f, check=check)
        except ParseError as exc:
            print("PARSE ERROR %s: %s" % (f, exc))
            return 1
        if did_change:
            changed.append(f)
    verb = "would change" if check else "changed"
    print("%s %d/%d files" % (verb, len(changed), len(files)))
    for f in changed:
        print("  " + f)
    if check and changed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
