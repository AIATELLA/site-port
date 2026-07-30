#!/usr/bin/env python3
"""Generate design.css and tokens.ts from tokens.json.

Usage:
    python build-tokens.py            # write design.css and tokens.ts next to tokens.json
    python build-tokens.py --check    # regenerate in memory, exit 1 if committed files differ

Standard library only. Deterministic: given the same tokens.json, running this
twice produces byte-identical output (dict iteration order in tokens.json is
preserved by json.load, so output order only ever depends on tokens.json itself).

design.css and tokens.ts are GENERATED. Never hand-edit them — edit tokens.json
and regenerate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DESIGN_DIR = Path(__file__).resolve().parent
TOKENS_JSON = DESIGN_DIR / "tokens.json"
DESIGN_CSS = DESIGN_DIR / "design.css"
TOKENS_TS = DESIGN_DIR / "tokens.ts"

GENERIC_FONT_KEYWORDS = {
    "serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui",
}

GENERATED_NOTICE = (
    "GENERATED FILE — do not hand-edit.\n"
    "Source of truth: design/tokens.json. Regenerate with:\n"
    "    python design/build-tokens.py"
)


# ---------------------------------------------------------------------------
# Tree walking
# ---------------------------------------------------------------------------

def is_leaf(node: Any) -> bool:
    return isinstance(node, dict) and "$value" in node and "$type" in node


def walk(node: Any, path_parts: list[str], out: list[tuple[tuple[str, ...], dict]]) -> None:
    """Depth-first walk collecting every ($type, $value) leaf token.

    Preserves tokens.json's own key order (json.load / dict is order-preserving),
    so this is deterministic across runs for a fixed tokens.json.
    """
    if not isinstance(node, dict):
        return
    if is_leaf(node):
        out.append((tuple(path_parts), node))
        return
    for key, value in node.items():
        if key.startswith("$"):
            continue
        walk(value, path_parts + [key], out)


def display_parts(path_parts: tuple[str, ...]) -> tuple[str, ...]:
    """Drop the synthetic 'DEFAULT' path segment used when a group also has
    its own base value (e.g. color.surface.DEFAULT -> color.surface)."""
    return tuple(p for p in path_parts if p != "DEFAULT")


def dotted(path_parts: tuple[str, ...]) -> str:
    """Dotted alias-lookup path, exactly matching tokens.json key casing
    (e.g. 'fontFamily.manrope') so it matches '{...}' alias references."""
    return ".".join(display_parts(path_parts))


def kebab_segment(segment: str) -> str:
    """camelCase -> kebab-case for a single path segment, e.g. fontFamily -> font-family."""
    out = []
    for ch in segment:
        if ch.isupper() and out:
            out.append("-")
        out.append(ch.lower())
    return "".join(out)


def dashed(path_parts: tuple[str, ...]) -> str:
    """Dashed path for generated identifiers (CSS custom properties, class
    names). Unlike dotted(), camelCase segments are kebab-cased so generated
    names read as e.g. --aiatella-font-family-manrope, not -fontFamily-."""
    return "-".join(kebab_segment(p) for p in display_parts(path_parts))


def css_var_name(path_parts: tuple[str, ...]) -> str:
    return f"--aiatella-{dashed(path_parts)}"


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------

def is_alias(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("{") and value.endswith("}")


def alias_path(value: str) -> str:
    return value[1:-1]


def build_raw_map(leaves: list[tuple[tuple[str, ...], dict]]) -> dict[str, dict]:
    """Map dotted alias-lookup path -> raw token dict, for every leaf."""
    return {dotted(parts): token for parts, token in leaves}


def build_var_map(leaves: list[tuple[tuple[str, ...], dict]]) -> dict[str, str]:
    """Map dotted alias-lookup path -> its CSS custom property name."""
    return {dotted(parts): css_var_name(parts) for parts, token in leaves}


# ---------------------------------------------------------------------------
# CSS value formatting
# ---------------------------------------------------------------------------

def format_font_family_css(names: list[str]) -> str:
    parts = []
    for name in names:
        if name in GENERIC_FONT_KEYWORDS:
            parts.append(name)
        else:
            parts.append(f'"{name}"')
    return ", ".join(parts)


def format_cubic_bezier_css(nums: list[float]) -> str:
    return "cubic-bezier(" + ", ".join(str(n) for n in nums) + ")"


def format_font_weight_css(value: Any) -> str:
    return str(int(value))


def scalar_css_value(token_type: str, value: Any) -> str:
    if token_type == "color":
        return value
    if token_type == "dimension":
        return value
    if token_type == "duration":
        return value
    if token_type == "fontFamily":
        return format_font_family_css(value)
    if token_type == "fontWeight":
        return format_font_weight_css(value)
    if token_type == "cubicBezier":
        return format_cubic_bezier_css(value)
    raise ValueError(f"no scalar CSS formatting for $type {token_type!r}")


def shadow_css_value(value: dict, var_map: dict[str, str]) -> str:
    color = value["color"]
    if is_alias(color):
        color_css = f"var({var_map[alias_path(color)]})"
    else:
        color_css = color
    segments = [value["offsetX"], value["offsetY"], value["blur"], value["spread"], color_css]
    prefix = "inset " if value.get("inset") else ""
    return prefix + " ".join(segments)


def typography_css_refs(value: dict, var_map: dict[str, str]) -> dict[str, str]:
    """Return the CSS value (var() ref or literal) for each typography field."""
    out = {}
    for field in ("fontFamily", "fontSize", "lineHeight", "fontWeight"):
        v = value[field]
        if is_alias(v):
            out[field] = f"var({var_map[alias_path(v)]})"
        else:
            out[field] = v
    return out


# ---------------------------------------------------------------------------
# design.css generation
# ---------------------------------------------------------------------------

CSS_PROP_NAMES = {
    "fontFamily": "font-family",
    "fontSize": "font-size",
    "lineHeight": "line-height",
    "fontWeight": "font-weight",
}


def generate_css(tokens: dict) -> str:
    leaves: list[tuple[tuple[str, ...], dict]] = []
    walk(tokens, [], leaves)
    var_map = build_var_map(leaves)

    root_lines: list[str] = []
    typography_leaves: list[tuple[tuple[str, ...], dict]] = []

    for parts, token in leaves:
        t = token["$type"]
        var_name = css_var_name(parts)
        if t == "typography":
            refs = typography_css_refs(token["$value"], var_map)
            for field in ("fontFamily", "fontSize", "lineHeight", "fontWeight"):
                sub_var = f"{var_name}-{CSS_PROP_NAMES[field]}"
                root_lines.append(f"  {sub_var}: {refs[field]};")
            typography_leaves.append((parts, token))
        elif t == "shadow":
            root_lines.append(f"  {var_name}: {shadow_css_value(token['$value'], var_map)};")
        else:
            root_lines.append(f"  {var_name}: {scalar_css_value(t, token['$value'])};")

    class_blocks: list[str] = []
    for parts, token in typography_leaves:
        disp = display_parts(parts)
        assert disp[0] == "typography"
        class_name = "aiatella-" + "-".join(disp[1:])
        var_name = css_var_name(parts)
        lines = [f".{class_name} {{"]
        for field in ("fontFamily", "fontSize", "lineHeight", "fontWeight"):
            prop = CSS_PROP_NAMES[field]
            lines.append(f"  {prop}: var({var_name}-{prop});")
        lines.append("}")
        class_blocks.append("\n".join(lines))

    focus_ring_var = css_var_name(("focus", "ring"))

    out: list[str] = []
    out.append("/*")
    for line in GENERATED_NOTICE.splitlines():
        out.append(f" * {line}" if line else " *")
    out.append(" *")
    out.append(" * AIATELLA design system — standalone stylesheet.")
    out.append(" * Drop this single file into any project to get AIATELLA's colour")
    out.append(" * palette, type scale, spacing, radii, motion and focus ring. Every")
    out.append(" * var(--aiatella-*) referenced below is defined in this same file.")
    out.append(" *")
    out.append(" * Font families are referenced by name (Manrope, Inter) with system")
    out.append(" * fallbacks. No @font-face rules are declared here — load the actual")
    out.append(" * font files yourself, or the fallback stack renders instead.")
    out.append(" */")
    out.append("")
    out.append(":root {")
    out.extend(root_lines)
    out.append("}")
    out.append("")
    out.append("/* Type-scale utility classes: family, size, line-height and weight together. */")
    for block in class_blocks:
        out.append(block)
        out.append("")
    out.append("/* Focus ring. The source site has no global focus styling at all; this is new. */")
    out.append(":focus-visible {")
    out.append("  outline: none;")
    out.append(f"  box-shadow: var({focus_ring_var});")
    out.append("}")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# tokens.ts generation
# ---------------------------------------------------------------------------

def ts_string(s: str) -> str:
    return json.dumps(s)


def ts_literal(token_type: str, value: Any, raw_map: dict[str, dict]) -> str:
    if token_type in ("color", "dimension", "duration"):
        return ts_string(value)
    if token_type == "fontFamily":
        return "[" + ", ".join(ts_string(n) for n in value) + "]"
    if token_type == "fontWeight":
        return str(int(value))
    if token_type == "cubicBezier":
        return "[" + ", ".join(str(n) for n in value) + "]"
    raise ValueError(f"no TS literal formatting for $type {token_type!r}")


def resolve_alias_value(value: Any, raw_map: dict[str, dict]) -> Any:
    if is_alias(value):
        target = raw_map[alias_path(value)]
        return target["$type"], target["$value"]
    return None


def typography_ts_object(value: dict, raw_map: dict[str, dict]) -> str:
    parts = []
    for field in ("fontFamily", "fontSize", "lineHeight", "fontWeight"):
        v = value[field]
        resolved = resolve_alias_value(v, raw_map)
        if resolved is not None:
            rtype, rvalue = resolved
            literal = ts_literal(rtype, rvalue, raw_map)
        else:
            literal = ts_string(v)
        parts.append(f"{field}: {literal}")
    return "{ " + ", ".join(parts) + " }"


def shadow_ts_object(value: dict, raw_map: dict[str, dict]) -> str:
    color = value["color"]
    resolved = resolve_alias_value(color, raw_map)
    color_literal = ts_string(resolved[1]) if resolved is not None else ts_string(color)
    parts = [
        f"color: {color_literal}",
        f"offsetX: {ts_string(value['offsetX'])}",
        f"offsetY: {ts_string(value['offsetY'])}",
        f"blur: {ts_string(value['blur'])}",
        f"spread: {ts_string(value['spread'])}",
        f"inset: {'true' if value.get('inset') else 'false'}",
    ]
    return "{ " + ", ".join(parts) + " }"


def nest_ts(leaves: list[tuple[tuple[str, ...], dict]], raw_map: dict[str, dict]) -> dict:
    """Build a nested plain-dict tree (using JS-safe leaf markers) mirroring
    tokens.json's structure, with DEFAULT segments preserved as literal keys
    (valid in a TS object: `DEFAULT: "#fff"`)."""
    root: dict[str, Any] = {}
    for parts, token in leaves:
        cur = root
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = ("__LEAF__", token)
    return root


def render_ts_tree(node: dict, raw_map: dict[str, dict], indent: int) -> str:
    pad = "  " * indent
    inner_pad = "  " * (indent + 1)
    lines = ["{"]
    for key, value in node.items():
        key_str = key if key.isidentifier() else ts_string(key)
        if isinstance(value, tuple) and value and value[0] == "__LEAF__":
            token = value[1]
            t = token["$type"]
            v = token["$value"]
            if t == "typography":
                literal = typography_ts_object(v, raw_map)
            elif t == "shadow":
                literal = shadow_ts_object(v, raw_map)
            else:
                literal = ts_literal(t, v, raw_map)
            lines.append(f"{inner_pad}{key_str}: {literal},")
        else:
            nested = render_ts_tree(value, raw_map, indent + 1)
            lines.append(f"{inner_pad}{key_str}: {nested},")
    lines.append(f"{pad}}}")
    return "\n".join(lines)


def generate_ts(tokens: dict) -> str:
    leaves: list[tuple[tuple[str, ...], dict]] = []
    walk(tokens, [], leaves)
    raw_map = build_raw_map(leaves)
    var_map = build_var_map(leaves)
    tree = nest_ts(leaves, raw_map)
    body = render_ts_tree(tree, raw_map, 0)

    css_var_entries = []
    for parts, _token in leaves:
        key = dotted(parts)
        css_var_entries.append(f'  {ts_string(key)}: {ts_string(var_map[key])},')

    out: list[str] = []
    out.append("/*")
    for line in GENERATED_NOTICE.splitlines():
        out.append(f" * {line}" if line else " *")
    out.append(" */")
    out.append("")
    out.append("export const tokens = " + body + " as const;")
    out.append("")
    out.append("export type AiatellaTokens = typeof tokens;")
    out.append("")
    out.append(
        "/** Maps each token's dotted path (matching tokens.json) to the CSS custom\n"
        " * property name it compiles to in design.css. */"
    )
    out.append("export const cssVarNames = {")
    out.extend(css_var_entries)
    out.append("} as const;")
    out.append("")
    out.append("export type AiatellaCssVarNames = typeof cssVarNames;")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def load_tokens() -> dict:
    with TOKENS_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="regenerate in memory and exit non-zero if committed files differ",
    )
    args = parser.parse_args(argv)

    tokens = load_tokens()
    css = generate_css(tokens)
    ts = generate_ts(tokens)

    if args.check:
        ok = True
        for path, content in ((DESIGN_CSS, css), (TOKENS_TS, ts)):
            existing = path.read_text(encoding="utf-8") if path.exists() else None
            if existing != content:
                ok = False
                print(f"DRIFT: {path.name} does not match a fresh build of tokens.json", file=sys.stderr)
        if ok:
            print("OK: design.css and tokens.ts match tokens.json")
            return 0
        return 1

    DESIGN_CSS.write_text(css, encoding="utf-8", newline="\n")
    TOKENS_TS.write_text(ts, encoding="utf-8", newline="\n")
    print(f"wrote {DESIGN_CSS}")
    print(f"wrote {TOKENS_TS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
