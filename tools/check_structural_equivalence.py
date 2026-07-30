"""Structural-equivalence check for Phase D. Parses two HTML documents with
Python's stdlib html.parser and asserts they produce the same sequence of
tags/attributes/text (whitespace-normalized in text nodes), independent of
any rendering engine. This is a sanity check that the prettifier only moved
whitespace around -- not a substitute for the pixel diff, but a fast,
render-independent gate.

Usage: python tools/check_structural_equivalence.py FILE_BEFORE FILE_AFTER
"""
import re
import sys
from html.parser import HTMLParser


class TreeBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.events = []

    def handle_starttag(self, tag, attrs):
        self.events.append(("start", tag, tuple(sorted(attrs))))

    def handle_startendtag(self, tag, attrs):
        self.events.append(("startend", tag, tuple(sorted(attrs))))

    def handle_endtag(self, tag):
        self.events.append(("end", tag))

    def handle_data(self, data):
        norm = re.sub(r"\s+", " ", data)
        if norm.strip() == "":
            return  # whitespace-only text is exactly what we're allowed to change
        self.events.append(("text", norm))

    def handle_comment(self, data):
        self.events.append(("comment", data))


def build(path):
    with open(path, encoding="utf-8", newline="") as fh:
        text = fh.read()
    p = TreeBuilder()
    p.feed(text)
    p.close()
    return p.events


def compare(before_path, after_path):
    before = build(before_path)
    after = build(after_path)
    if before == after:
        return True, None
    # Find first divergence for a useful error message.
    for i, (b, a) in enumerate(zip(before, after)):
        if b != a:
            return False, "first divergence at event %d:\n  before: %r\n  after:  %r" % (i, b, a)
    return False, "length mismatch: before has %d events, after has %d" % (len(before), len(after))


if __name__ == "__main__":
    ok, msg = compare(sys.argv[1], sys.argv[2])
    if ok:
        print("EQUIVALENT %s == %s" % (sys.argv[1], sys.argv[2]))
        sys.exit(0)
    print("DIVERGENT %s != %s" % (sys.argv[1], sys.argv[2]))
    print(msg)
    sys.exit(1)
