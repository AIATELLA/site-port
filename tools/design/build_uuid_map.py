"""Build the --token-<uuid> -> --aiatella-<semantic> mapping from tokens.json,
by walking $extensions.com.aiatella.framer.token(s) on every leaf. This is the
single source of truth for the Phase B rename; nothing here is hand-transcribed.

Stdlib only. Importable (returns the mapping) and runnable (prints it).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DIR = REPO_ROOT / "design"
TOKENS_JSON = DESIGN_DIR / "tokens.json"

sys.path.insert(0, str(DESIGN_DIR))
import importlib.util

_spec = importlib.util.spec_from_file_location("build_tokens", DESIGN_DIR / "build-tokens.py")
build_tokens = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_tokens)


def load_tokens() -> dict:
    with TOKENS_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def uuid_to_var_map() -> dict[str, str]:
    """--token-<uuid> (lowercase, no fallback) -> --aiatella-<semantic>."""
    tokens = load_tokens()
    leaves: list[tuple[tuple[str, ...], dict]] = []
    build_tokens.walk(tokens, [], leaves)

    mapping: dict[str, str] = {}
    for parts, token in leaves:
        ext = token.get("$extensions", {}).get("com.aiatella.framer", {})
        uuid_tokens = ext.get("tokens") or ([ext["token"]] if "token" in ext else [])
        if not uuid_tokens:
            continue
        var_name = build_tokens.css_var_name(parts)
        for uuid_token in uuid_tokens:
            mapping[uuid_token] = var_name
    return mapping


if __name__ == "__main__":
    m = uuid_to_var_map()
    print(f"{len(m)} UUID source tokens mapped")
    for k, v in m.items():
        print(f"  {k} -> {v}")
