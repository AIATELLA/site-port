# SEO Foundation & Missing Pages — Design

**Date:** 2026-07-30
**Status:** Awaiting review
**Scope:** Tier 1 (technical SEO) + Tier 2 (missing legal/security pages) of the wider site-port improvement programme

---

## 1. Context

`site-port` is a static export of the Framer-built aiatella.com. It is intended to **become production**, replacing the Framer-hosted site. A full audit (SEO, performance, messaging, usability, accessibility) produced a five-tier improvement programme; this spec covers tiers 1 and 2 only.

### The problem this solves

Seven of the eight pages carry `<meta name="robots" content="noindex">`, inherited from the live Framer site. Production confirms the consequence: `https://www.aiatella.com/sitemap.xml` contains only the homepage and 11 blog posts. The Approach, Solutions, Company, Contact and Waitlist pages cannot rank at all.

Compounding this:

- Titles are single words (`Products`, `Company`, `Approach`) with no brand or keywords
- Meta descriptions are internal notes (`"AIATELLA Details"`, `"AIATELLA contact page"`)
- `canonical` is a relative file path (`href="index.html"`) contradicting `og:url`
- No `og:image` anywhere, so every social share renders a blank card
- Zero structured data across the whole site
- No `robots.txt`, no `sitemap.xml`
- Five pages have no `<h1>`
- Four pages that exist or should exist are absent: security, terms, cookies, 404

### Goals

1. Make every page that should rank, rankable, with metadata targeting the keyword research
2. Give search engines and social platforms complete, correct signals
3. Close the legal/trust page gaps (security, cookies, terms, 404)
4. Change nothing about the visual design or copy on the page — beyond the two exceptions noted in §4.1

### Non-goals

Explicitly deferred to later passes:

- **Tier 3 — Performance.** 132 of 133 images have a fake `srcset` (every width points at the same original); 22.4 MB of unresized originals; a 9.9 MB / 8192×5464 JPEG on `approach.html`; 19 MB of committed sourcemaps; no lazy loading.
- **Tier 4 — Messaging.** Applying the comms strategy's own rewrites, the founding story, the *ajatella* brand narrative, the impact-led homepage layer.
- **Tier 5 — Consumer SEO pages.** Carotid / AAA / PAD / vascular health service pages.
- **Forms.** Both still POST to `api.framer.com/forms/v1/...`. Known, tracked separately, must be resolved before cutover.
- **Go-live mechanics.** DNS, redirects, hosting cutover.
- **Product analytics.** See §3.7. Site measurement *is* in scope (§3.5–3.6).

---

## 2. Key decisions

### 2.1 URL strategy — extensionless canonicals, `.html` internal links

Live URLs are extensionless (`/approach` → 200, `/approach.html` → 404). All existing ranking signals and backlinks are on the extensionless form. GitHub Pages serves `approach.html` at `/approach` automatically.

Therefore:

| Context | Form |
|---|---|
| Internal `href` | `approach.html` — unchanged, keeps localhost working |
| `canonical`, `og:url`, `sitemap.xml` | `https://www.aiatella.com/approach` — absolute, extensionless |

This preserves link equity on cutover without breaking local development.

### 2.2 Canonical host — `https://www.aiatella.com`

The live sitemap and all `og:url` values use `www`. The live `robots.txt` inconsistently points at the non-www sitemap. Standardise on `www` everywhere.

### 2.3 Indexing policy — selective, not blanket

Remove `noindex` from the six content pages that carry it (`approach`, `solutions`, `company`, `blog`, `contact`, `waitlist`). **Deliberately retain `noindex`** on `privacy` (which has it today) plus the new `terms`, `cookies` and `404`: boilerplate pages that dilute crawl budget on a small site and never usefully rank. `security.html` **is** indexable — researchers search for disclosure policies.

### 2.4 No regulatory claims

The comms strategy states approvals are *pending* in the US, UK and France. No metadata, schema or page copy produced by this work will imply FDA clearance, CE marking, or any approval not held. This constrains the `MedicalBusiness` / `SoftwareApplication` schema in particular.

### 2.5 Terms of Service is a reviewed draft, not final

A Terms of Service for a medical-imaging company touches regulated ground. This work will produce a defensible **general website** terms draft (site use, IP, disclaimers, limitation of liability, governing law: Finland). It will:

- carry a visible draft marker until legal sign-off
- **not** invent medical-device terms, clinical-service terms, or patient-facing contractual language

This is flagged as a hard dependency on counsel before cutover.

### 2.6 Cookie policy reflects actual behaviour

Verified: no analytics or tracking of any kind is configured (no GA/GTM/Segment/Plausible/PostHog IDs present; the `Segment`/`GTag` strings in the bundle are a font name and Framer property-control enums). The only client-side storage is functional `localStorage` — locale preference and Framer's fetch cache.

The cookie policy will describe exactly that, plus the Cloudflare Web Analytics beacon added per §3.5 — which is itself cookieless and stores no client-side state.

**No consent banner is required**, since only strictly-necessary storage is in use. This holds *because* of the analytics choice in §3.5; adopting a cookie-based tool such as GA4 or PostHog later would require revisiting both this page and adding a consent mechanism.

---

## 3. Section A — Metadata

### 3.1 Titles and descriptions

Titles ≤60 chars, descriptions ≤160 chars, targeting the keyword research.

| Page | Title | Description |
|---|---|---|
| `index` | AI Cardiovascular Imaging & Screening \| AIATELLA | Explainable AI that automates cardiovascular measurements from MRI, CT and ultrasound — precise results in minutes, and earlier detection of disease. |
| `approach` | Our Approach: Explainable AI for Cardiac Imaging \| AIATELLA | How AIATELLA's Automated Imaging Measurement works — transparent AI that integrates with existing PACS and automates rule-based measurement tasks. |
| `solutions` | Aorta AIM — Automated Cardiovascular Analysis \| AIATELLA | Aorta AIM delivers instant, standardised aortic measurements from CT, MRI and ultrasound. Track and quantify aortic pathologies over time. |
| `company` | About AIATELLA — Our Story, Team & Mission | Founded in Helsinki in 2022 to give doctors more time with patients and people more time with their loved ones. Meet the team behind AIATELLA. |
| `blog` | News & Resources on AI Cardiovascular Imaging \| AIATELLA | Research, press coverage and clinical evidence on AI-powered cardiovascular imaging and preventative screening from the AIATELLA team. |
| `contact` | Contact AIATELLA — Talk to Our Team | Get in touch about AIATELLA's cardiovascular imaging AI, clinical partnerships, or preventative screening programmes. |
| `waitlist` | Join the Carotid Artery Screening Waitlist \| AIATELLA | Non-invasive carotid ultrasound screening, analysed by AI and reviewed by physicians. Join the waitlist for priority access and early-bird pricing. |
| `security` | Security & Vulnerability Disclosure \| AIATELLA | Report a security vulnerability to AIATELLA. Our disclosure policy, scope, researcher commitments and 90-day resolution timeline. |
| `privacy` | Privacy Policy \| AIATELLA | How AIATELLA collects, uses and protects your personal data, including your rights under GDPR and CCPA. |
| `terms` | Terms of Service \| AIATELLA | The terms governing use of the AIATELLA website and services. |
| `cookies` | Cookie Policy \| AIATELLA | Which cookies and local storage the AIATELLA website uses, why, and how to control them. |
| `404` | Page Not Found \| AIATELLA | — |

Keyword coverage: `AI cardiovascular imaging` (2,400/mo), `cardiac imaging AI` (3,200/mo), `carotid artery screening` (4,300/mo), `AI radiology cardiovascular` (1,900/mo), plus `explainable AI`, `PACS`, and modality terms.

The `solutions` description deliberately uses **"Track and quantify aortic pathologies over time"** — the exact replacement the comms strategy prescribes for the sentence currently on that page (see §4.1).

### 3.2 Per-page `<head>` changes

For each page:

- `<title>` and `<meta name="description">` per the table above
- `og:title` / `og:description` / `twitter:title` / `twitter:description` aligned to the same copy
- `og:url` and `<link rel="canonical">` → absolute extensionless production URL
- `og:image` / `twitter:image` → per §5, absolute URL, with `og:image:width`, `og:image:height`, `og:image:alt`
- `og:site_name` → `AIATELLA` (currently absent)
- `og:locale` → `en_GB`
- `robots` per §2.3
- `viewport` → `width=device-width, initial-scale=1` (currently omits `initial-scale`)

Remove the two `framer-search-index` meta tags — they reference a search feature not wired up in the port.

### 3.3 Missing `<h1>` elements

`approach`, `solutions`, `company`, `blog`, `contact` have no `<h1>`. Promote the existing lead `<h2>` to `<h1>` in each.

Because Framer emits every breakpoint variant into the DOM (`ssr-variant` blocks), each logical heading appears 2–3 times. **All variants of the lead heading must be promoted together**, or different viewports will expose different heading structures.

CSS impact: heading styles are driven by Framer's `--framer-font-size` custom properties on the element, not by tag selector, so promoting `h2`→`h1` is visually inert. To be verified per page (§7).

### 3.4 Blog post metadata

11 posts (10 present + 1 to port, see §4.2). Each gets a keyword-aware title, a real description drawn from its own opening paragraph, canonical, `og:*`, and `Article` schema (§4.3).

### 3.5 Measurement — Search Console + Cloudflare Web Analytics

Without this there is no way to know whether any of the work in this spec succeeded. Decided approach:

| Tool | Role | Cost |
|---|---|---|
| **Google Search Console** | The instrument that matters. Queries, impressions, average position, and **indexing status** — i.e. the direct confirmation that removing `noindex` worked | Free |
| **Cloudflare Web Analytics** | Traffic volume, referrers, per-page views, Core Web Vitals. Cookieless, so no consent banner (§2.6). JS beacon works on any host — no DNS change or Cloudflare proxying needed | Free |
| **Bing Webmaster Tools** | Bing's index feeds ChatGPT and Copilot, so this is the entry point for being cited by AI assistants | Free |

GA4 was considered and rejected. Two reasons: a visitor on `/waitlist` is expressing interest in cardiovascular screening, which makes that pageview an inference about their health — GDPR Article 9 territory, and precisely the pattern US regulators pursued hospitals over. And practically, GA4 needs a consent banner in the EU, which both loses a large share of the data to refusals and costs conversions on the pages that matter most. The cookieless choice measures more, not less.

*(GA4 is lawful in the EU today under the 2023 EU–US Data Privacy Framework; the 2022 adverse rulings concerned Universal Analytics. The objection here is the health-data sensitivity and the consent-banner cost, not illegality.)*

**Implementation scope:** add the Cloudflare beacon script to all pages. Account creation for all three tools requires Onni's login and is an owner action (§8).

### 3.6 Conversion tracking — thank-you pages

Cloudflare Web Analytics measures pageviews only; it has no custom events or goals. Rather than buy a heavier tool, conversions are modelled as pageviews of dedicated confirmation URLs:

| Form | Redirects to on success |
|---|---|
| Waitlist | `/waitlist-thanks` |
| Contact | `/contact-thanks` |

A pageview of those URLs *is* the conversion. This is tool-agnostic — it works identically with Cloudflare, Plausible or GA4 — so the measurement approach survives any later change of analytics vendor. It is also better UX than an inline success message: a real confirmation page can set expectations about what happens next.

Both pages are `noindex`. This is not just crawl hygiene: an indexed thank-you page would collect organic landings and inflate the conversion count.

**Dependency:** the redirect can only be wired when the forms are rebuilt (both currently POST to `api.framer.com`). This spec therefore *creates the pages* and leaves the redirect wiring to the forms work. Flat-file pages are used rather than `/waitlist/thanks` to avoid a `waitlist.html` file and `waitlist/` directory coexisting, which some static hosts resolve inconsistently.

### 3.7 Product analytics — deliberately out of scope

PostHog, Mixpanel and Amplitude track individual behaviour across sessions inside an application — funnels, retention cohorts, feature adoption. That is genuinely valuable, but it is the wrong instrument for a public marketing site: it needs accounts and repeat visits to be meaningful, it requires cookies (hence a consent banner), and on a health site it reintroduces the Article 9 exposure argued against in §3.5.

The right time is when there is an authenticated product — the screening service or a clinician-facing tool. Do it there, inside the app, with proper consent, where events describe product usage and a user has a real identity. On this site the only meaningful events are "read a page" and "submitted a form", both already covered by §3.5 and §3.6.

**Upgrade path if pageview-level conversions prove too coarse** (e.g. wanting per-source conversion rates or form-abandonment funnels): Plausible's paid tier adds goals and custom events, EU-hosted and still cookieless, for $9/month. Because the thank-you pages already exist, switching is a one-line script change. Starting free costs nothing later.

---

## 4. Section B — Crawl infrastructure

### 4.1 The two copy exceptions

This pass changes on-page copy in exactly two places, both because the comms strategy explicitly prescribes the replacement:

1. `solutions.html` — "Quantified, longitudinal assessment of aortic pathologies" → **"Track and quantify aortic pathologies over time"** (comms strategy p.24, verbatim prescription)
2. `privacy.html` — a heading rendering as literal markdown, `**Effective Date:** November 13, 2024` → properly rendered, with the date refreshed

The homepage's rejected sentence ("Our AI technology transforms cardiovascular workflows…", also named on p.24) is left for Tier 4, since its replacement is a longer rewrite needing voice sign-off.

### 4.2 `robots.txt`

```
User-agent: *
Allow: /

Sitemap: https://www.aiatella.com/sitemap.xml
```

### 4.3 `sitemap.xml`

19 URLs, all absolute and extensionless:

- 7 content pages: `/`, `/approach`, `/solutions`, `/company`, `/blog`, `/contact`, `/waitlist`
- 1 trust page: `/security`
- 11 blog posts

Present in the port (10): `aiatella-2m-seed`, `aiatella-ceo-featured-in-2025-ai-visionaries-womens-health`, `aiatella-instrumentarium`, `bbc-feature`, `helsinkismart-aiatella`, `hi-nenc-report`, `hoiva`, `mtv3-features-aiatella`, `slush2024-showcase`, `valve-trial`

**Missing from the port, present in the live sitemap (1):** `from-mandate-to-mechanism-closing-the-delivery-gap-in-cardiovascular-screening` — must be ported across, or cutover drops a live indexed URL.

Excluded per §2.3: privacy, terms, cookies, 404.

### 4.4 Structured data (JSON-LD)

| Schema | Where | Notes |
|---|---|---|
| `Organization` | All pages | Name, URL, logo, Helsinki address, `sameAs` → LinkedIn, `foundingDate` 2022 |
| `WebSite` | `index` | With `publisher` → Organization |
| `MedicalBusiness` + `MedicalProcedure` | `waitlist` | Carotid ultrasound screening. Constrained by §2.4 |
| `SoftwareApplication` | `solutions` | Aorta AIM. No approval claims (§2.4) |
| `Article` | Each of 11 blog posts | `headline`, `datePublished`, `author`, `image`, `publisher` |
| `BreadcrumbList` | Blog details | Home → Resources → post |

Deliberately **not** used: `MedicalDevice` (implies a regulatory status not held), `Review`/`AggregateRating` (no legitimate review data).

**Address:** `Lapinlahdenkatu 16, 00180 Helsinki, Finland`, taken from the live `/security` footer. The comms PDF's `Eerikinkatu 28` appears to be the agency's own address. **Open item — confirm before implementation** (§8).

---

## 5. Section C — `og:image`

### Design

A generated 1200×630 branded card. Available assets: the AIATELLA waveform logo (SVG, `#231f20`), Inter and Manrope in woff2, and the brand palette (`#000`, `#fff`, `#d10000` red — verified at 5.6:1 on white, passes WCAG AA — plus `#f7f7f7`).

- One sitewide default card
- Per-page variants for the seven content pages, differing only in the headline line
- Composition: logo, page-level headline in Manrope, wordmark, on a brand background with the waveform motif

### Rendering approach

Author each card as a small self-contained HTML file, rasterise to PNG with headless Chrome (confirmed present at `/c/Program Files/Google/Chrome/Application/chrome.exe`) at a 1200×630 viewport. Output to `assets/images/og/`.

This is deterministic, needs no new native dependencies, and keeps the card sources editable in the repo.

### Wiring

`og:image` and `twitter:image` must be **absolute** URLs (`https://www.aiatella.com/assets/images/og/<name>.png`) — relative paths are not resolved by most social scrapers. `twitter:card` stays `summary_large_image`, which is now truthful.

---

## 6. Section D — New and fixed pages

All six new pages reuse the existing nav, footer and CSS conventions so they are visually indistinguishable from the rest of the site.

| Page | Indexed | Content |
|---|---|---|
| `security.html` | yes | Ported verbatim from live: vulnerability reporting, `security@aiatella.com`, researcher commitments (no legal action in good faith, regular communication, PII protection), in/out of scope, 90-day critical resolution. Fixes the live bug where this page's `<title>` reads "Privacy" and its description reads "AIATELLA Privacy Page" |
| `cookies.html` | no | Written from verified behaviour (§2.6): functional `localStorage` plus the cookieless Cloudflare beacon, no tracking cookies, no third-party trackers. Sections: what we use, why, how to clear it, what would change if we adopted a cookie-based tool |
| `terms.html` | no | Draft per §2.5 — site use, IP, disclaimers, limitation of liability, governing law (Finland), changes to terms, contact. Visibly marked as awaiting legal review |
| `404.html` | no | Branded, nav + footer, links to the main sections |
| `waitlist-thanks.html` | no | Waitlist confirmation per §3.6. Sets expectations on what happens next. Redirect wiring deferred to the forms work |
| `contact-thanks.html` | no | Contact confirmation per §3.6. Same deferral |

### Fixes to existing pages

- `privacy.html` — repair the literal `**Effective Date:**` markdown leaking through as a heading; refresh the stale November 2024 date
- **Footer** — three fixes, applied across all pages including blog details:
  - currently links only Privacy → add Security, Terms and Cookies
  - visible copyright reads `Copyright © 2025. All rights reserved to AIATELLA.` → bump to 2026. (A `data-framer-name="Copyright © 2023…"` attribute also carries a stale year, but it is a Framer design-layer label that never renders — leave it alone, or strip it as harmless noise. It is **not** the user-visible string.)
  - there is no `<footer>` element anywhere on the site → wrap the existing footer markup in one, which also serves the landmark requirement in §7.4

---

## 7. Verification

No claim of completion without a passing check. Per-page, scripted:

1. **Indexability** — assert exactly the intended `robots` value on all 14 top-level pages
2. **Metadata completeness** — every page has non-empty title ≤60, description ≤160, canonical, `og:url`, `og:image`, `og:site_name`
3. **Canonical correctness** — every canonical is absolute, `www`, extensionless, and matches its own page
4. **Document structure** — exactly one logical `<h1>` per page; no heading level skipped; a `<footer>` landmark present on every page
5. **Sitemap integrity** — 19 URLs; every one returns 200 on the local server (via its `.html` equivalent); every indexable page appears exactly once; no `noindex` page appears
6. **JSON-LD validity** — every block parses as JSON and carries `@context` + `@type`
7. **og:image resolves** — each referenced PNG exists on disk at 1200×630
8. **Visual regression** — screenshot each page before and after via headless Chrome at desktop + mobile widths; confirm the `h2`→`h1` promotions and metadata edits are visually inert
9. **Link integrity** — no internal `href` 404s, including the new footer links, across all 25 pages (14 top-level + 11 blog details)
10. **Live parity** — the ported security page and blog post match their live text
11. **Analytics beacon** — the Cloudflare script is present exactly once per page and sets no cookie (assert `document.cookie` stays empty on load, via headless Chrome)

Results reported with actual command output, including anything that fails.

---

## 8. Open items

| Item | Needs |
|---|---|
| Registered address | Confirm `Lapinlahdenkatu 16, 00180 Helsinki` is correct for `Organization` schema and page footers (§4.4) |
| Terms of Service | Legal review before cutover (§2.5) |
| Analytics accounts | **Owner action.** Google Search Console, Cloudflare Web Analytics and Bing Webmaster Tools all need Onni's login. Cloudflare issues a site token that must be pasted into the beacon script before it reports anything (§3.5) |
| Search Console verification | Requires either a DNS record or an uploaded verification file — depends on go-live hosting, so likely after cutover |
| Forms | Framer API dependency must be resolved before cutover. Also blocks the thank-you redirect wiring (§3.6) — tracked outside this spec |

## 9. Risks

| Risk | Mitigation |
|---|---|
| Removing `noindex` exposes weak pages to indexing before Tier 4 messaging lands | Acceptable — indexed-and-imperfect beats invisible. Tier 4 follows |
| `h2`→`h1` promotion changes rendering | Framer sizes headings via custom properties, not tag selectors. Verified by screenshot diff (§7.8) |
| Missing `ssr-variant` duplicates when promoting headings | Promote all variants together; assert one logical `h1` at every breakpoint (§7.4) |
| Extensionless canonicals break if hosting isn't GitHub Pages | Documented dependency. Any host must serve `.html` at extensionless paths, or add redirects |
| Terms draft treated as final | Visible draft marker + open item (§8) |
| Cloudflare beacon ships with a placeholder token and silently reports nothing | Verification step §7.11 asserts the script is present; a `TODO` marker in the token position plus the §8 owner action make the gap visible rather than silent |
| Thank-you pages exist but nothing redirects to them, so conversions read as zero | Documented dependency on the forms work (§3.6). The pages are inert-but-correct until then, not broken |
