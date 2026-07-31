/*
 * GENERATED FILE — do not hand-edit.
 * Source of truth: design/tokens.json. Regenerate with:
 *     python design/build-tokens.py
 */

export const tokens = {
  color: {
    ink: {
      DEFAULT: "#000000",
      muted: "#000000b3",
      overlay: "#0000000d",
      warm: "#1c1313",
    },
    surface: {
      DEFAULT: "#ffffff",
      muted: "#ffffffb3",
      overlay: {
        DEFAULT: "#ffffff1a",
        subtle: "#ffffff14",
        strong: "#ffffff66",
      },
      subtle: {
        DEFAULT: "#f7f7f7",
        muted: "#f7f7f7b3",
        overlay: "#f7f7f766",
      },
    },
    border: {
      DEFAULT: "#dbdbdb",
      strong: "#b8b8b8",
    },
    brand: {
      red: {
        DEFAULT: "#d10000",
        deep: "#8a0000",
      },
    },
    icon: {
      nav: "#1d1f13",
    },
  },
  fontFamily: {
    manrope: ["Manrope", "Manrope Placeholder", "sans-serif"],
    inter: ["Inter", "Inter Placeholder", "sans-serif"],
  },
  fontWeight: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  typography: {
    display: {
      xl: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "64px", lineHeight: "80px", fontWeight: 500, letterSpacing: "0px" },
      l: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "40px", lineHeight: "48px", fontWeight: 500, letterSpacing: "0px" },
    },
    heading: {
      l: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "28px", lineHeight: "36px", fontWeight: 500, letterSpacing: "0px" },
      m: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "22px", lineHeight: "28px", fontWeight: 500, letterSpacing: "0px" },
      s: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "20px", lineHeight: "28px", fontWeight: 500, letterSpacing: "0px" },
    },
    body: {
      l: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "18px", lineHeight: "26px", fontWeight: 500, letterSpacing: "0px" },
      m: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "16px", lineHeight: "22px", fontWeight: 500, letterSpacing: "0px" },
    },
    label: {
      m: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "16px", lineHeight: "16px", fontWeight: 500, letterSpacing: "0px" },
    },
    prose: {
      m: { fontFamily: ["Inter", "Inter Placeholder", "sans-serif"], fontSize: "16px", lineHeight: "20px", fontWeight: 400, letterSpacing: "-0.02em" },
    },
    caption: {
      m: { fontFamily: ["Manrope", "Manrope Placeholder", "sans-serif"], fontSize: "14px", lineHeight: "20px", fontWeight: 500, letterSpacing: "0px" },
      s: { fontFamily: ["Inter", "Inter Placeholder", "sans-serif"], fontSize: "12px", lineHeight: "16px", fontWeight: 400, letterSpacing: "-0.02em" },
    },
  },
  space: {
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "10": "40px",
    "16": "64px",
    "20": "80px",
    "32": "128px",
    legacy: {
      "10": "10px",
      "26": "104px",
    },
  },
  radius: {
    m: "20px",
    l: "40px",
    pill: "100px",
  },
  breakpoint: {
    tablet: "860px",
    desktop: "1200px",
  },
  motion: {
    easing: {
      standard: [0.44, 0, 0.56, 1],
    },
    duration: {
      fast: "150ms",
    },
  },
  focus: {
    ring: { color: "#d10000", offsetX: "0px", offsetY: "0px", blur: "0px", spread: "5px", inset: true },
  },
} as const;

export type AiatellaTokens = typeof tokens;

/** Maps each token's dotted path (matching tokens.json) to the CSS custom
 * property name it compiles to in design.css. */
export const cssVarNames = {
  "color.ink": "--aiatella-color-ink",
  "color.ink.muted": "--aiatella-color-ink-muted",
  "color.ink.overlay": "--aiatella-color-ink-overlay",
  "color.ink.warm": "--aiatella-color-ink-warm",
  "color.surface": "--aiatella-color-surface",
  "color.surface.muted": "--aiatella-color-surface-muted",
  "color.surface.overlay": "--aiatella-color-surface-overlay",
  "color.surface.overlay.subtle": "--aiatella-color-surface-overlay-subtle",
  "color.surface.overlay.strong": "--aiatella-color-surface-overlay-strong",
  "color.surface.subtle": "--aiatella-color-surface-subtle",
  "color.surface.subtle.muted": "--aiatella-color-surface-subtle-muted",
  "color.surface.subtle.overlay": "--aiatella-color-surface-subtle-overlay",
  "color.border": "--aiatella-color-border",
  "color.border.strong": "--aiatella-color-border-strong",
  "color.brand.red": "--aiatella-color-brand-red",
  "color.brand.red.deep": "--aiatella-color-brand-red-deep",
  "color.icon.nav": "--aiatella-color-icon-nav",
  "fontFamily.manrope": "--aiatella-font-family-manrope",
  "fontFamily.inter": "--aiatella-font-family-inter",
  "fontWeight.regular": "--aiatella-font-weight-regular",
  "fontWeight.medium": "--aiatella-font-weight-medium",
  "fontWeight.semibold": "--aiatella-font-weight-semibold",
  "fontWeight.bold": "--aiatella-font-weight-bold",
  "typography.display.xl": "--aiatella-typography-display-xl",
  "typography.display.l": "--aiatella-typography-display-l",
  "typography.heading.l": "--aiatella-typography-heading-l",
  "typography.heading.m": "--aiatella-typography-heading-m",
  "typography.heading.s": "--aiatella-typography-heading-s",
  "typography.body.l": "--aiatella-typography-body-l",
  "typography.body.m": "--aiatella-typography-body-m",
  "typography.label.m": "--aiatella-typography-label-m",
  "typography.prose.m": "--aiatella-typography-prose-m",
  "typography.caption.m": "--aiatella-typography-caption-m",
  "typography.caption.s": "--aiatella-typography-caption-s",
  "space.1": "--aiatella-space-1",
  "space.2": "--aiatella-space-2",
  "space.3": "--aiatella-space-3",
  "space.4": "--aiatella-space-4",
  "space.5": "--aiatella-space-5",
  "space.6": "--aiatella-space-6",
  "space.8": "--aiatella-space-8",
  "space.10": "--aiatella-space-10",
  "space.16": "--aiatella-space-16",
  "space.20": "--aiatella-space-20",
  "space.32": "--aiatella-space-32",
  "space.legacy.10": "--aiatella-space-legacy-10",
  "space.legacy.26": "--aiatella-space-legacy-26",
  "radius.m": "--aiatella-radius-m",
  "radius.l": "--aiatella-radius-l",
  "radius.pill": "--aiatella-radius-pill",
  "breakpoint.tablet": "--aiatella-breakpoint-tablet",
  "breakpoint.desktop": "--aiatella-breakpoint-desktop",
  "motion.easing.standard": "--aiatella-motion-easing-standard",
  "motion.duration.fast": "--aiatella-motion-duration-fast",
  "focus.ring": "--aiatella-focus-ring",
} as const;

export type AiatellaCssVarNames = typeof cssVarNames;
