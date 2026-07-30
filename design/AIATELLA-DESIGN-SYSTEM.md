# AIATELLA Design System

This is the human-readable guide to AIATELLA's visual and brand language. It documents
`design/tokens.json` (the source of truth) and the generated `design/design.css` /
`design/tokens.ts` outputs, which any project can use directly.

**Status:** Phase A — the design layer described here is extracted from the live
`site-port` Framer export and is additive. It does not yet replace anything in this
repository; that migration is Phase B onward (see
`docs/superpowers/specs/2026-07-30-aiatella-design-system-design.md`).

**No file in this document was invented.** Every colour, size, weight and spacing
value below was measured from `assets/css/*.css` in this repository and independently
re-verified by script (see "Verification" at the end). If a number here looks wrong,
it was wrong in the source CSS, not added by this document.

---

## 1. Colour

AIATELLA's palette collapses to **16 semantic colours**, extracted from 17 Framer
UUID custom properties in `assets/css/shared.css` (two of the seventeen are an exact
duplicate `#fff` pair, collapsed to one `color.surface`).

| Token | Value | Role |
|---|---|---|
| `color.ink` | `#000000` | Primary text |
| `color.ink.muted` | `#000000b3` (70%) | Secondary text |
| `color.ink.overlay` | `#0000000d` (5%) | Hairline dividers / subtle scrims on light surfaces |
| `color.ink.warm` | `#1c1313` | Warm near-black, used as the text colour on several heading/body presets instead of pure black |
| `color.surface` | `#ffffff` | Primary background |
| `color.surface.muted` | `#ffffffb3` (70%) | Muted white |
| `color.surface.overlay` | `#ffffff1a` (10%) | White overlay |
| `color.surface.overlay.subtle` | `#ffffff14` (8%) | Subtler white overlay |
| `color.surface.overlay.strong` | `#ffffff66` (40%) | Strongest white overlay |
| `color.surface.subtle` | `#f7f7f7` | Off-white section background |
| `color.surface.subtle.muted` | `#f7f7f7b3` (70%) | Muted off-white |
| `color.surface.subtle.overlay` | `#f7f7f766` (40%) | Off-white overlay |
| `color.border` | `#dbdbdb` | Default hairline border |
| `color.border.strong` | `#b8b8b8` | Stronger, decorative-only border |
| `color.brand.red` | `#d10000` | Primary brand colour |
| `color.brand.red.deep` | `#8a0000` | Gradient partner to brand red |

### Contrast — recomputed, not transcribed

Ratios below were computed with the standard WCAG relative-luminance formula
(sRGB → linear, `(L1 + 0.05) / (L2 + 0.05)`), against a white (`#ffffff`) background,
by a script in this repository's verification run (see the bottom of this document).

| Colour | Ratio on white | WCAG AA (text, ≥4.5:1) |
|---|---|---|
| `color.brand.red` `#d10000` | **5.66:1** | **PASS** |
| `color.border.strong` `#b8b8b8` | **1.98:1** | **FAIL** |
| `#999` (`#999999`), used directly in `contact.css` and `waitlist.css` as `--framer-input-icon-color`, not a named token | **2.85:1** | **FAIL** |

**Read this plainly: `color.border.strong` and `#999` fail WCAG AA and must never be
used to render text.** They exist only as decorative borders / icon tints on a
non-text element. `color.brand.red` is the only one of these three that passes AA
and may carry text (e.g. links, labels) on a white background.

> Note on the `#999` count: the design spec that commissioned this system states
> `#999` appears "16 times" in the source CSS. Directly measuring `assets/css/*.css`
> finds the literal string `#999` on 5 lines (2 in `contact.css`, 3 in `waitlist.css`),
> covering 12 comma-separated CSS selectors between them (`--framer-input-icon-color`
> on Framer's generated input-icon classes). The 2.85:1 ratio itself is confirmed
> exactly. The occurrence count could not be reconciled to 16 and is flagged here
> rather than silently repeated.

**Known likely AA failure, flagged for Phase C:** the footer's legal links render as
low-contrast grey text on a dark red background. This was not exhaustively measured
here (it requires the actual grey and red values as rendered, including any
opacity), but it is called out because it is the kind of failure this system exists
to prevent going forward.

---

## 2. Typography

Two families carry the entire site:

- **Manrope** — display and UI: headings, body copy, labels, captions. Weights
  available in this codebase: **500 (medium), 600 (semibold), 700 (bold)**.
- **Inter** — long-form prose and the smallest captions. Weights available: **400
  (regular), 500 (medium), 700 (bold)**.

Both are referenced by name in `design.css` with generic fallbacks
(`"Manrope", "Manrope Placeholder", sans-serif` / `"Inter", "Inter Placeholder", sans-serif`).
Phase A does not ship font files or `@font-face` rules — that's Phase C. Without
loading Manrope/Inter yourself, text renders in the fallback sans-serif.

### The 11-step scale

Extracted from 11 distinct `framer-styles-preset-*` hash classes across
`assets/css/*.css`. Class names below are what `design.css` generates
(`.aiatella-<step>`).

| Step | Class | Family | Size / line-height | Weight | Use |
|---|---|---|---|---|---|
| `display.xl` | `.aiatella-display-xl` | Manrope | 64 / 80 | 500 | Largest hero headline |
| `display.l` | `.aiatella-display-l` | Manrope | 40 / 48 | 500 | Secondary hero headline |
| `heading.l` | `.aiatella-heading-l` | Manrope | 28 / 36 | 500 | Section heading |
| `heading.m` | `.aiatella-heading-m` | Manrope | 22 / 28 | 500 | Sub-section heading |
| `heading.s` | `.aiatella-heading-s` | Manrope | 20 / 28 | 500 | Card / component heading |
| `body.l` | `.aiatella-body-l` | Manrope | 18 / 26 | 500 | Lead paragraph |
| `body.m` | `.aiatella-body-m` | Manrope | 16 / 22 | 500 | Standard body copy |
| `label.m` | `.aiatella-label-m` | Manrope | 16 / 16 | 500 | Tight single-line labels (buttons, form labels) |
| `prose.m` | `.aiatella-prose-m` | Inter | 16 / 20 | 400 | Long-form reading copy (blog body) |
| `caption.m` | `.aiatella-caption-m` | Manrope | 14 / 20 | 500 | Small UI caption |
| `caption.s` | `.aiatella-caption-s` | Inter | 12 / 16 | 400 | Smallest caption / metadata |

**A twelfth preset, `7964ex`, is not on this list on purpose.** It's the class Framer
applies to footer links. It declares no font-family, size, line-height or weight at
all — it is purely `text-decoration: none`, inheriting every type property from its
context. It is recorded in `tokens.json` under `typography.link` for audit
completeness (so anyone diffing "12 presets in the source" against "11 steps in the
system" can see where the twelfth went), but it is not part of the type scale and has
no utility class.

---

## 3. Spacing

A 4px-based scale, chosen to cover every spacing value actually observed in the
source CSS (8, 10, 16, 20, 24, 32, 40, 64, 80, 104, 128px) so that migrating existing
code to these tokens is a pure rename, not a value change.

| Token | Value |
|---|---|
| `space.1` | 4px |
| `space.2` | 8px |
| `space.3` | 12px |
| `space.4` | 16px |
| `space.5` | 20px |
| `space.6` | 24px |
| `space.8` | 32px |
| `space.10` | 40px |
| `space.16` | 64px |
| `space.20` | 80px |
| `space.32` | 128px |

Two values don't land on the 4px grid and are kept as explicitly-named outliers
rather than silently rounded:

| Token | Value | Note |
|---|---|---|
| `space.legacy.10` | 10px | Off-grid (would need to be 2.5 units) |
| `space.legacy.26` | 104px | Off-grid (104 = 26 × 4, sits between `space.20`=80 and `space.32`=128) |

Both are flagged for reconciliation in a later phase — use them where the source
uses 10px/104px today; don't round them to a neighbouring on-grid value without a
deliberate design decision.

## 4. Radii

| Token | Value | Note |
|---|---|---|
| `radius.m` | 20px | Dominant radius — 20 uses in the source CSS |
| `radius.l` | 40px | |
| `radius.pill` | 100px | Fully rounded / pill shape |

## 5. Breakpoints

Framer emits three layout variants per element: desktop, tablet, mobile. The
boundaries are almost consistent:

- **Desktop:** `min-width: 1200px` — consistent everywhere.
- **Tablet:** `min-width: 860px` — consistent everywhere **except `company.css`,
  which uses `810px`.**
- **Mobile:** below the tablet breakpoint.

This system **normalises on 860px** (`breakpoint.tablet`). `company.css`'s 810px is
the sole outlier in the entire codebase; adopting 860px there shifts that one page's
tablet threshold by 50px. This is deliberately deferred — Phase C must pixel-verify
`company.html` specifically in the 810–860px window before this normalisation lands
in that file.

| Token | Value |
|---|---|
| `breakpoint.tablet` | 860px |
| `breakpoint.desktop` | 1200px |

## 6. Motion

The entire source CSS uses exactly **one** easing curve and **one** duration:

| Token | Value |
|---|---|
| `motion.easing.standard` | `cubic-bezier(0.44, 0, 0.56, 1)` |
| `motion.duration.fast` | `150ms` |

## 7. Focus ring

The source site has **no global `:focus-visible` styling at all** — keyboard focus
is invisible on most interactive elements today. This system reuses the one
meaningful shadow value found in the CSS — the brand's checked/selected indicator,
`inset 0 0 0 5px #d10000` — as `focus.ring`, and `design.css` wires it up globally:

```css
:focus-visible {
  outline: none;
  box-shadow: var(--aiatella-focus-ring);
}
```

This is a genuine accessibility improvement over the current site, not a value
that already existed as a focus style — it's a deliberate reuse of an existing
brand-red visual language for a purpose the site doesn't yet serve.

---

## 8. The logo

The AIATELLA mark is an ECG-waveform line drawing at
`assets/images/sIjcnF79hqocNDHvZGTIrQXQo0k.svg` (viewBox `0 0 1078.99 944.21`). It is
built from exactly two `<path>` elements:

1. The waveform stroke: `fill:none; stroke:#231f20; stroke-width:27px`.
2. A small filled accent shape: `fill:#231f20`.

**One colour, one stroke, one fill.** Recolouring the entire logo — for a dark
background, an inverted variant, whatever — is a single find-and-replace of
`#231f20` in that SVG. There is no gradient, no second colour, no embedded raster
asset to worry about.

---

## 9. Brand language

Design is not only colour and type. This section is verbatim from the
Communications Strategy (San Francisco Oy, 7 July 2025) as summarised in the design
spec — nothing here is invented, and nothing beyond what's below should be assumed
without going back to that source document.

**Vision:** "To give people more time."

**Mission:** "To give doctors more time with their patients and people more time
with their loved ones."

**WHY:** "Every person deserves control over their own health, so they can have
every minute they want with those they love."

**Name origin:** AIATELLA comes from the Finnish *ajatella*, "to think" — the
company's self-description is AI that protects the radiologist's ability to think,
rather than replacing it. Any copy or design that frames the product as a
replacement for clinical judgement is off-brand at the root, not just off-tone.

**Tonal blend:** clear, factual, trustworthy; humane and relatable; uses precise
medical terminology without drowning the reader in jargon; passionate, and at times
provocative, but always grounded in facts and empathy. Never hype-driven, never cold.

**Prescribed rewrites ("Instead of / Say," p.24 of the strategy doc):** the strategy
document includes a table of banned phrasings and their replacements. Two of these
were still being violated on the live site before the SEO pass that preceded this
work — treat "Instead of / Say" as binding copy guidance, not a suggestion; consult
the source strategy document for the full table before writing new copy.

**Three audiences, three distinct emotional targets:**

| Audience | Positioning | Emotion to land |
|---|---|---|
| General population | Relief | "This protects the people I love." |
| Clinicians | Confidence | "This makes me better at my job, not obsolete." |
| Investors | Excitement | "This is a category-defining opportunity." |

Design and copy aimed at one audience should not default to another's tone — a
clinician-facing page that reads like an investor deck (or vice versa) is a
positioning failure even if every individual sentence is accurate.

### No regulatory claims

**AIATELLA's regulatory approvals are pending in the US, UK and France.** No design
or copy work — anywhere, including this design system's own future extensions — may
imply FDA clearance, CE marking, or ISO certification that has not actually been
granted. This is a hard constraint, not a style preference, and it binds every phase
of work that follows this one.

---

## 10. How to use this in a new project

1. **Copy one file:** `design/design.css`. It is fully standalone — every
   `var(--aiatella-*)` it uses is defined in that same file. Drop it into any HTML
   page, React app, or design tool that accepts a CSS file, with zero other
   dependencies.
2. **Load Manrope and Inter yourself** (Google Fonts, self-hosted, whatever the
   target project already uses for fonts) if you want the real typefaces rather
   than the fallback sans-serif — `design.css` deliberately ships no `@font-face`
   rules.
3. **Reach for these class names** for text: `.aiatella-display-xl`,
   `.aiatella-display-l`, `.aiatella-heading-l`, `.aiatella-heading-m`,
   `.aiatella-heading-s`, `.aiatella-body-l`, `.aiatella-body-m`,
   `.aiatella-label-m`, `.aiatella-prose-m`, `.aiatella-caption-m`,
   `.aiatella-caption-s`. Each one sets font-family, size, line-height and weight
   together — never mix-and-match a class with a manual `font-size` override.
4. **Reach for these custom properties** for everything else: colours
   (`var(--aiatella-color-brand-red)`, `var(--aiatella-color-ink)`, …), spacing
   (`var(--aiatella-space-4)`, …), radii (`var(--aiatella-radius-m)`, …), and motion
   (`var(--aiatella-motion-easing-standard)`, `var(--aiatella-motion-duration-fast)`).
5. **In a React/TypeScript codebase**, import `design/tokens.ts` instead of parsing
   CSS: `import { tokens, cssVarNames } from "./tokens"`. `tokens` is a fully
   resolved, typed, nested `const` object (`tokens.color.brand.red.DEFAULT`,
   `tokens.space["4"]`, `tokens.typography.heading.l`, …); `cssVarNames` maps each
   token's dotted path to the exact custom property name it compiles to in
   `design.css`, so JS and CSS never drift apart.
6. **In Figma**, `design/tokens.json` is W3C DTCG format — importable directly by
   Figma variables (and by Style Dictionary, if a build pipeline is preferred over
   a manual import) without any bespoke conversion step.
7. **Never hand-edit `design.css` or `tokens.ts`.** Both are generated from
   `tokens.json` by `design/build-tokens.py`. Change the JSON, then run
   `python design/build-tokens.py` to regenerate both. Run
   `python design/build-tokens.py --check` in CI to fail the build if the committed
   generated files have drifted from the JSON.
8. **Respect the two `color.border.strong` / `#999` failures and the no-regulatory-
   claims constraint above** in whatever you build next — they are recorded here
   specifically so future work doesn't have to rediscover them the hard way.

---

## Verification

This document's numeric claims were checked by script, not eyeballed:

- **DTCG validity:** every one of the 54 leaf tokens in `tokens.json` has both
  `$type` and `$value`. Counts by type: `color` 16, `dimension` 18, `fontFamily` 2,
  `fontWeight` 4, `typography` 11, `cubicBezier` 1, `duration` 1, `shadow` 1.
- **Colour fidelity:** all 17 source `--token-<uuid>` custom properties in
  `assets/css/shared.css` map to exactly one of the 16 semantic colours above, and
  every value matches byte-for-byte (case-insensitive hex).
- **Typography fidelity:** all 12 `framer-styles-preset-*` classes (11 scale steps
  + `7964ex`) were located in `assets/css/*.css` and their family/size/line-height/
  weight match this document and `tokens.json` exactly.
- **Contrast:** the three ratios in section 1 were recomputed from the WCAG formula
  independently of this document's prose and matched exactly (5.66:1, 1.98:1,
  2.85:1) with the stated AA verdicts.
- **Self-containment:** every `var(--aiatella-*)` referenced anywhere in
  `design.css` is defined as a custom property in that same file (0 orphans).
- **Determinism:** running `python design/build-tokens.py` twice in a row produces
  byte-identical `design.css` and `tokens.ts`; `python design/build-tokens.py
  --check` exits 0 against the committed files.
