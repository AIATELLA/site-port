"""Head-rewriting primitives. Parsing rules live here only, so every script
treats the markup identically."""
import re

ANCHOR = "<!-- End of headStart -->"


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def head_slice(text):
    m = re.search(r"<head[^>]*>", text)
    e = text.index("</head>", m.end())
    return m.end(), e


def replace_tag(text, kind, attr, value, new_tag):
    """Replace a <meta>/<link> in the head identified by attr="value".
    Returns (text, replaced). If absent, inserts before the headStart anchor."""
    s, e = head_slice(text)
    head = text[s:e]
    pat = re.compile(
        r"<%s\b[^>]*?\b%s=\"%s\"[^>]*?>" % (kind, attr, re.escape(value)), re.I)
    if pat.search(head):
        return text[:s] + pat.sub(lambda _: new_tag, head, count=1) + text[e:], True
    return upsert_block_raw(text, new_tag), False


def replace_title(text, new_title):
    s, e = head_slice(text)
    head = text[s:e]
    head2, n = re.subn(r"<title\b[^>]*>.*?</title>",
                       lambda _: "<title>%s</title>" % new_title, head,
                       count=1, flags=re.S)
    if not n:
        raise ValueError("no <title> in head")
    return text[:s] + head2 + text[e:]


def upsert_block_raw(text, block):
    """Insert raw markup immediately before the headStart anchor."""
    i = text.index(ANCHOR)
    return text[:i] + block + "\n    " + text[i:]


def upsert_block(text, marker, block):
    """Insert or replace a delimited managed block. Idempotent."""
    start, end = "<!-- seo:%s start -->" % marker, "<!-- seo:%s end -->" % marker
    payload = "%s\n%s\n%s" % (start, block, end)
    if start in text:
        a = text.index(start)
        b = text.index(end) + len(end)
        return text[:a] + payload + text[b:]
    return upsert_block_raw(text, payload)


def strip_tag(text, kind, attr, value):
    s, e = head_slice(text)
    head = text[s:e]
    pat = re.compile(
        r"\s*<%s\b[^>]*?\b%s=\"%s\"[^>]*?>" % (kind, attr, re.escape(value)), re.I)
    return text[:s] + pat.sub("", head) + text[e:]
