# AIATELLA Design System — Design

**Date:** 2026-07-30
**Status:** Phase A approved, executing
**Scope:** A portable AIATELLA design system, plus readable and de-duplicated HTML/CSS across the site

---

## 1. Context

`site-port` is a Framer export destined to replace www.aiatella.com. Its design layer is machine-generated and unusable as a source of truth:

- **17 design tokens**, all opaque UUIDs — `--token-6fa10ce0-ad77-4ae2-9539-cc850356aaa1: #000`. Two are exact duplicates (both `#fff`).
- **2,932 token references**, of which **2,767 sit in HTML inline styles**, not CSS.
- **12 typography presets** hidden in hash-named `framer-styles-preset-*` classes. A coherent scale exists; it has no names.
- **90 identical selector+body CSS rules** duplicated across 2+ page files ≈ **44 KB** of pure duplication.
- **25 HTML files, 2,439 KB, but only 1,835 lines** — ~73 lines per 97 KB page.
- **561 `ssr-variant` blocks**: Framer emits every breakpoint variant into the DOM, so most markup exists three times.
- Font files are hash-named (`1K3W8DizY3v4emK8Mb08YHxTbs.woff2`). Inter has 37 faces, Manrope 3.

Nothing here is reusable outside this repo, and none of it is legible to a human.

### Goals

1. One portable, machine- and human-readable source of truth for AIATELLA's visual language **and** brand language.
2. Consumable by this site, a React/web app, and Figma.
3. Readable HTML and CSS with no duplicated declarations.
4. No visual regression at any step.

### Owner decisions (2026-07-30)

- **HTML depth:** go as far as collapsing the 3× breakpoint duplication — replace Framer's `ssr-variant` system with real media queries so each element exists once. Acknowledged as effectively rebuilding the responsive layer.
- **Consumers:** this site, a React/web app, and Figma/designers. Therefore W3C DTCG token format plus a CSS build plus a JS/TS export.

---

## 2. Phasing

Riskiest last. Each phase ends verified before the next begins.

| Phase | Deliverable | Risk |
|---|---|---|
| **A** | `tokens.json` (DTCG), generated `design.css`, `tokens.ts`, `AIATELLA-DESIGN-SYSTEM.md` | **Zero** — purely additive |
| **B** | Replace all 2,767 UUID references with semantic names wired to `design.css` | Low — mechanical, pixel-verifiable |
| **C** | Eliminate the 90 duplicate rules; layered stylesheets pulling from `design.css` | Low–medium |
| **D** | Prettify all 25 HTML files to readable indented markup | Medium — inline whitespace is significant |
| **E** | Collapse 561 variant blocks into media queries | **High** — the rebuild |

This spec covers **Phase A** in full and fixes the token/type/scale decisions that B–E depend on. B–E get their own plans.

---

## 3. Extracted design language

All values measured from the codebase, not invented.

### 3.1 Colour

The 17 UUID tokens map to 16 semantic names (two source tokens are both `#fff`).

| Semantic name | Value | Source token suffix | Notes |
|---|---|---|---|
| `color.ink` | `#000000` | `6fa10ce0` | primary text |
| `color.ink.muted` | `#000000b3` | `e27e3a45` | 70% |
| `color.ink.overlay` | `#0000000d` | `412cf3f5` | 5% |
| `color.ink.warm` | `#1c1313` | `137326a3` | |
| `color.surface` | `#ffffff` | `55a9b33d`, `6c9f0706` | **duplicate pair — collapse to one** |
| `color.surface.muted` | `#ffffffb3` | `90b2aadb` | 70% |
| `color.surface.overlay.strong` | `#ffffff66` | `892d3b4a` | 40% |
| `color.surface.overlay` | `#ffffff1a` | `07aaf817` | 10% |
| `color.surface.overlay.subtle` | `#ffffff14` | `b43a18e0` | 8% |
| `color.surface.subtle` | `#f7f7f7` | `4bed56f7` | |
| `color.surface.subtle.muted` | `#f7f7f7b3` | `75be653a` | 70% |
| `color.surface.subtle.overlay` | `#f7f7f766` | `4f6ed643` | 40% |
| `color.border` | `#dbdbdb` | `d55a03e9` | |
| `color.border.strong` | `#b8b8b8` | `f2a1dab5` | **2.0:1 on white — decorative only, never text** |
| `color.brand.red` | `#d10000` | `8f13e9a5` | **5.6:1 on white — passes AA for text** |
| `color.brand.red.deep` | `#8a0000` | `94818a51` | gradient partner |

**Accessibility, recorded in the system itself:** `#d10000` passes WCAG AA on white at 5.66:1. `#b8b8b8` (1.98:1) and the `#999` used **21 times** elsewhere in the CSS — 5 as `#999`, 16 as `rgb(153, 153, 153)` — (2.85:1) **fail AA** and must not carry text. The footer legal links are low-contrast grey on dark red and are a likely AA failure — flagged for Phase C.

### 3.2 Typography

Two families: **Manrope** for display and UI, **Inter** for long-form and captions.

| Name | Family | Size / line-height | Weight | Source preset |
|---|---|---|---|---|
| `display.xl` | Manrope | 64 / 80 | 500 | `1wnnaf1` |
| `display.l` | Manrope | 40 / 48 | 500 | `zgnytv` |
| `heading.l` | Manrope | 28 / 36 | 500 | `1gy43jf` |
| `heading.m` | Manrope | 22 / 28 | 500 | `18cqnal` |
| `heading.s` | Manrope | 20 / 28 | 500 | `k90szl` |
| `body.l` | Manrope | 18 / 26 | 500 | `r0omsg` |
| `body.m` | Manrope | 16 / 22 | 500 | `1rlbg1z` |
| `label.m` | Manrope | 16 / 16 | 500 | `1h599co` |
| `prose.m` | Inter | 16 / 20 | 400 | `99gjg` |
| `caption.m` | Manrope | 14 / 20 | 500 | `19iuj27` |
| `caption.s` | Inter | 12 / 16 | 400 | `10g3946` |

Available weights: Manrope 500/600/700; Inter 400/500/700. Preset `7964ex` (used by footer links) declares no type properties and is inherit-only — record it as a link style, not a scale step.

**Letter-spacing is part of a type step.** Measured: exactly the two Inter presets carry `letter-spacing: -.02em` (`99gjg` → `prose.m`, `10g3946` → `caption.s`); all nine Manrope steps are explicitly `0px`. Since those two are the body and caption styles — most of the running text on the site — a type step that omitted tracking would render incorrectly and force Phase C to special-case it outside the system. So a type step is family, size, line-height, weight **and letter-spacing**. Nothing else in the source varies, so nothing else is included.

### 3.3 Spacing

Observed: 8, 10, 16, 20, 24, 32, 40, 64, 80, 104, 128 px. Normalise to a 4px-based scale, keeping every value the site actually uses so Phase B is a pure rename:

`space.1`=4, `space.2`=8, `space.3`=12, `space.4`=16, `space.5`=20, `space.6`=24, `space.8`=32, `space.10`=40, `space.16`=64, `space.20`=80, `space.32`=128.

`10px` and `104px` are off-scale outliers. Record them as `space.legacy.10` and `space.legacy.26` so Phase B can rename without changing rendering; flag both for later reconciliation rather than silently rounding.

### 3.4 Radius

`radius.m`=20px (dominant, 20 uses), `radius.l`=40px, `radius.pill`=100px.

### 3.5 Breakpoints

Framer emits three variants. The boundaries are inconsistent:

- desktop `min-width: 1200px`
- tablet `min-width: 860px` — **except `company.css`, which uses `810px`**
- mobile below that

**Normalise on 860px.** `company.css` is the sole outlier; changing it alters that page's tablet threshold between 810 and 860px, so Phase C must pixel-verify `company.html` in that window specifically.

Tokens: `breakpoint.tablet`=860px, `breakpoint.desktop`=1200px.

### 3.6 Motion and focus

Only one easing curve and one duration exist: `cubic-bezier(0.44, 0, 0.56, 1)` and `150ms`. Record as `motion.easing.standard` and `motion.duration.fast`.

The only meaningful shadow is `inset 0 0 0 5px #d10000` — the brand focus/checked indicator. Record as `focus.ring`. This matters: the audit found **no global focus styles**, so having the ring named makes Phase C's accessibility fix straightforward.

### 3.7 Brand language

The system document carries voice as well as visuals, drawn from the Communications Strategy (San Francisco Oy, 7 July 2025) — because "the AIATELLA look" is not only colours:

- **Vision:** "To give people more time."
- **Mission:** "To give doctors more time with their patients and people more time with their loved ones."
- **WHY:** "Every person deserves control over their own health, so they can have every minute they want with those they love."
- **Name:** from Finnish *ajatella*, "to think" — AI that protects the radiologist's ability to think rather than replacing it.
- **Tonal blend:** clear, factual, trustworthy; humane and relatable; precise medical terms without drowning in jargon; passionate, sometimes provocative, always grounded in facts and empathy.
- **The prescribed rewrites** (p.24 "Instead of / Say"), including the two the site still violated before the SEO pass.
- **Three audiences** with distinct positioning: general population → relief; clinicians → confidence; investors → excitement.
- **No regulatory claims.** Approvals are pending in the US, UK and France. This constraint belongs in the design system so it binds future work.

---

## 4. Phase A architecture

Four artifacts, one source of truth.

```
design/
  tokens.json          <- SOURCE OF TRUTH. W3C DTCG format.
  build-tokens.py      <- generates the two files below. Never hand-edit them.
  design.css           <- GENERATED. CSS custom properties + type utility classes.
  tokens.ts            <- GENERATED. Typed export for React.
  AIATELLA-DESIGN-SYSTEM.md  <- the human document
```

**Why DTCG:** it is the W3C Design Tokens Community Group format, which Figma variables and Style Dictionary both import. That satisfies the Figma and React consumers without bespoke glue.

**Why generated CSS/TS:** a hand-maintained CSS copy drifts from the JSON. Generating both from `tokens.json` makes drift structurally impossible, and a verification step asserts the committed outputs match a fresh build.

`design.css` exposes:
- one custom property per token, named `--aiatella-<path>` (e.g. `--aiatella-color-brand-red`)
- one utility class per type step (e.g. `.aiatella-heading-l`) setting family/size/line-height/weight together
- a `:focus-visible` rule using `focus.ring`, which the site currently lacks entirely

It must be usable standalone: dropping `design.css` into an unrelated project gives that project the AIATELLA palette, type scale, spacing, radii and motion with no other dependency.

### Non-goals for Phase A

Phase A touches **no existing file**. It does not migrate tokens (B), consolidate CSS (C), prettify HTML (D), or collapse breakpoints (E). It also does not rename the hash-named font files — that is Phase C, since `fonts.css` references them.

---

## 5. Verification

Phase A is additive, so verification is about internal correctness, not regression:

1. `tokens.json` parses and validates as DTCG — every leaf has `$type` and `$value`.
2. Every one of the 17 source UUID tokens maps to exactly one semantic token, and every colour value in the table above appears in `tokens.json` byte-identically. A script asserts this against `assets/css/shared.css` so the mapping cannot drift from reality.
3. All 12 typography presets are represented; sizes, line-heights, weights and families match the CSS.
4. `design.css` and `tokens.ts` regenerate byte-identically from `tokens.json` (build twice, diff).
5. Every documented contrast ratio is recomputed by script, not transcribed — including the AA pass/fail verdicts.
6. `design.css` parses as valid CSS and every `var(--aiatella-*)` it references is defined within itself.
7. A standalone smoke page rendered with only `design.css` shows the full palette and type scale, screenshotted, confirming it works with no other stylesheet.

---

## 6. Risks

| Risk | Mitigation |
|---|---|
| Semantic names bake in wrong intent, forcing churn in Phase B | Names derive from observed usage; the two duplicate `#fff` tokens are collapsed deliberately and recorded |
| The 810px/860px normalisation shifts `company.html`'s tablet layout | Deferred to Phase C with a targeted pixel diff in the 810–860px window |
| Off-scale 10px/104px values get silently rounded | Preserved as `space.legacy.*`; Phase B stays a pure rename |
| Generated CSS drifts from JSON | Both generated; verification rebuilds and diffs |
| `#b8b8b8` / `#999` reused as text by future work | Recorded in the system as decorative-only with measured ratios |
