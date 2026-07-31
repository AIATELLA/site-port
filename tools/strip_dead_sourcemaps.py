"""Remove sourceMappingURL comments that point at files which do not exist.

The Framer export's bundles end with a `//# sourceMappingURL=...` comment
pointing into a `sourcemaps/` directory that was dropped from this repo (it
was 19 MB of build artefacts nobody here can use). The comment is only
fetched when devtools is open, so this is cosmetic -- but it produces a 404
per bundle for anyone who inspects the site, which looks like a broken
deploy.

Only comments whose target is genuinely missing are removed: a bundle that
still ships a real map keeps its comment. Run with --check to report
without writing (non-zero exit if anything is stale).
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = [os.path.join(ROOT, "assets", "js"), os.path.join(ROOT, "assets", "css")]
EXTS = (".js", ".mjs", ".css")
# Trailing comment, optionally preceded by whitespace/newlines, at EOF or not.
PATTERN = re.compile(r"[ \t]*(?://|/\*)[#@]\s*sourceMappingURL=(\S+?)(?:\s*\*/)?[ \t]*(\r?\n|$)")


def targets(path, text):
    """Yield (match, resolved_target, exists) for every sourcemap comment."""
    for m in PATTERN.finditer(text):
        url = m.group(1)
        if url.startswith("data:"):
            yield m, url, True          # inline map, nothing to fetch
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(path), url.split("?")[0]))
        yield m, target, os.path.exists(target)


def main():
    check = "--check" in sys.argv
    stale_files = 0
    stale_refs = 0
    kept = 0
    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for name in sorted(os.listdir(d)):
            if not name.lower().endswith(EXTS):
                continue
            path = os.path.join(d, name)
            with open(path, encoding="utf-8", newline="") as fh:
                text = fh.read()
            found = list(targets(path, text))
            if not found:
                continue
            dead = [m for m, _t, ok in found if not ok]
            kept += len(found) - len(dead)
            if not dead:
                continue
            stale_files += 1
            stale_refs += len(dead)
            print("  %s -- %d dead map ref(s)" % (
                os.path.relpath(path, ROOT).replace("\\", "/"), len(dead)))
            if check:
                continue
            # Rebuild without the dead comments, last-first so offsets hold.
            out = text
            for m in reversed(dead):
                out = out[:m.start()] + m.group(2) + out[m.end():]
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(out)

    print("\nfiles with dead sourcemap refs: %d (%d refs)" % (stale_files, stale_refs))
    print("live/inline refs left alone   : %d" % kept)
    if check:
        if stale_files:
            print("STALE -- run without --check to strip them")
            raise SystemExit(1)
        print("clean -- no dead sourcemap refs")
    else:
        print("stripped %d ref(s) from %d file(s)" % (stale_refs, stale_files))


if __name__ == "__main__":
    main()
