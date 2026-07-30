"""Phase B: rename every opaque --token-<uuid> reference to its semantic
--aiatella-<name> equivalent, everywhere it appears (HTML inline styles and
assets/css/*.css). Pure rename -- no fallback value is touched, no colour
changes.

The mapping comes from build_uuid_map.uuid_to_var_map(), which reads
design/tokens.json programmatically. Nothing here is hand-transcribed.

Additionally tidies assets/css/shared.css: after the rename, its single
`body{...}` rule declares the (now-renamed) --aiatella-* custom properties
directly, duplicating what design/design.css already declares on :root with
byte-identical values. Since every page now loads design.css first, those
declarations are redundant; this script strips them (declaration-form only --
`name:value;` -- never touching `var(--aiatella-*, ...)` usages) and keeps the
one unrelated declaration in that rule (--framer-will-change-override).

Idempotent: safe to re-run. If no --token- references remain, it's a no-op
(the shared.css strip step is also idempotent -- once the declarations are
gone, the strip regex matches nothing further).

Stdlib only. UTF-8 I/O, newline='' throughout.
"""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_uuid_map import uuid_to_var_map  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_CSS = REPO_ROOT / "assets" / "css" / "shared.css"

# Declaration-form only: name immediately followed by ':' and a value up to
# the next ';'. This never matches a var(--aiatella-name, ...) usage, because
# there the character after the name is ',' or ')', not ':'.
DECL_RE = re.compile(r"--aiatella-[a-z0-9-]+:[^;{}]+;")

# --- Phase A gap, discovered during this migration -------------------------
# tokens.json documents 17 source UUID tokens. The live site actually
# references an 18th: --token-34f2fca6-59e0-489a-9f06-3c3a8bbd36c7, used only
# as the background-color of the two mobile-nav hamburger-icon bars
# (.nav__hamburger-top / .nav__hamburger-bot), 2 occurrences x 25 pages = 50.
# It is never declared anywhere in the codebase (checked shared.css, every
# assets/css/*.css, mapping.json) -- there is no --token-34f2fca6...: value
# set on any selector, so the var() always falls through to its fallback,
# rgb(29, 31, 19), on every page, in every browser. Confirmed byte-identical
# across all 50 occurrences.
#
# Since Phase A never captured this colour, there is no --aiatella-* name in
# design.css to rename it to (inventing one would fail Phase B's own gate
# that every semantic name used must be defined in design.css). But leaving
# it un-migrated would fail the zero-UUID-references gate. Since the fallback
# was already the only value that ever rendered, de-tokenizing to the literal
# is a zero-risk, zero-pixel-change resolution -- not a colour change, just
# dropping a custom-property indirection that pointed at nothing. Reported in
# the Phase B report as a genuine Phase A inventory gap, not silently folded
# into the 17-token narrative.
ORPHAN_UUID = "--token-34f2fca6-59e0-489a-9f06-3c3a8bbd36c7"
ORPHAN_FULL_EXPR = f"var({ORPHAN_UUID}, rgb(29, 31, 19))"
ORPHAN_LITERAL = "rgb(29, 31, 19)"


def _read(path: Path) -> str:
    with open(path, encoding="utf-8", newline="") as fh:
        return fh.read()


def _write(path: Path, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def target_files() -> list[Path]:
    files = []
    for pattern in ("*.html", "blog-details/*.html", "assets/css/*.css"):
        files.extend(REPO_ROOT.glob(pattern))
    return sorted(set(files))


def migrate() -> dict:
    mapping = uuid_to_var_map()
    report = {"per_file": {}, "total_replacements": 0, "files_changed": 0}

    for path in target_files():
        text = _read(path)
        original = text
        file_count = 0
        for uuid_token, var_name in mapping.items():
            n = text.count(uuid_token)
            if n:
                text = text.replace(uuid_token, var_name)
                file_count += n
        orphan_n = text.count(ORPHAN_FULL_EXPR)
        if orphan_n:
            text = text.replace(ORPHAN_FULL_EXPR, ORPHAN_LITERAL)
            file_count += orphan_n
            report["orphan_replacements"] = report.get("orphan_replacements", 0) + orphan_n
        if text != original:
            _write(path, text)
            report["files_changed"] += 1
        if file_count:
            rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
            report["per_file"][rel] = file_count
            report["total_replacements"] += file_count

    # Tidy shared.css: strip the now-redundant --aiatella-* declarations from
    # its body{} rule (design.css's :root already provides them, identically).
    if SHARED_CSS.exists():
        text = _read(SHARED_CSS)
        stripped, n = DECL_RE.subn("", text)
        if n:
            _write(SHARED_CSS, stripped)
        report["shared_css_declarations_stripped"] = n

    return report


if __name__ == "__main__":
    r = migrate()
    print(f"files changed: {r['files_changed']}")
    print(f"total --token- references replaced: {r['total_replacements']}")
    print(f"shared.css redundant declarations stripped: {r.get('shared_css_declarations_stripped', 0)}")
    for f, n in sorted(r["per_file"].items()):
        print(f"  {f}: {n}")
