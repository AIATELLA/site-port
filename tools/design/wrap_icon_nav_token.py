"""Fix round 1: --token-34f2fca6-59e0-489a-9f06-3c3a8bbd36c7 (the mobile-nav
hamburger-icon bars) is now a real semantic token, color.icon.nav, added to
design/tokens.json and regenerated into design/design.css as
--aiatella-color-icon-nav (#1d1f13 == rgb(29, 31, 19)).

migrate_tokens.py (Phase B) had already de-tokenized this orphan UUID down to
its bare literal fallback, since at that time no semantic name existed for
it. Now that one exists, this script does the second half of the job: wrap
every bare `rgb(29, 31, 19)` literal back into
`var(--aiatella-color-icon-nav, rgb(29, 31, 19))` -- same pattern as every
other colour reference on the site, fallback preserved exactly.

Idempotent: if a literal is already inside that var() wrapper, it is left
alone (the search string is the bare literal not already preceded by the var
wrapper's opening).

Stdlib only. UTF-8 I/O, newline='' throughout.
"""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

LITERAL = "rgb(29, 31, 19)"
WRAPPED = "var(--aiatella-color-icon-nav, rgb(29, 31, 19))"
ALREADY_WRAPPED = "var(--aiatella-color-icon-nav, " + LITERAL + ")"


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
    report = {"per_file": {}, "total_replacements": 0, "files_changed": 0}
    for path in target_files():
        text = _read(path)
        original = text
        # Count bare literals that are NOT already inside the var() wrapper.
        already = text.count(ALREADY_WRAPPED)
        total_literal = text.count(LITERAL)
        bare = total_literal - already
        if bare <= 0:
            continue
        # Replacing the wrapper-form first would double-wrap it; instead,
        # temporarily protect already-wrapped occurrences, replace the rest,
        # then restore.
        placeholder = "\x00ICON_NAV_ALREADY_WRAPPED\x00"
        text = text.replace(ALREADY_WRAPPED, placeholder)
        n = text.count(LITERAL)
        text = text.replace(LITERAL, WRAPPED)
        text = text.replace(placeholder, ALREADY_WRAPPED)
        if text != original:
            _write(path, text)
            report["files_changed"] += 1
            rel = str(path.relative_to(REPO_ROOT)).replace("\\", "/")
            report["per_file"][rel] = n
            report["total_replacements"] += n
    return report


if __name__ == "__main__":
    r = migrate()
    print(f"files changed: {r['files_changed']}")
    print(f"total bare rgb(29, 31, 19) literals wrapped: {r['total_replacements']}")
    for f, n in sorted(r["per_file"].items()):
        print(f"  {f}: {n}")
