"""Single source of truth for AIATELLA page metadata. Data only, no logic."""

SITE = "https://www.aiatella.com"
ORG_ADDRESS = {
    "streetAddress": "Lapinlahdenkatu 16",
    "postalCode": "00180",
    "addressLocality": "Helsinki",
    "addressCountry": "FI",
}
IDX = "index,follow,max-image-preview:large"
NO = "noindex,follow"

# Cloudflare Web Analytics beacon token. Left as a placeholder deliberately --
# verify.py check 11 must keep failing until the real token is set at
# cutover; do not replace this with a real value here.
CF_BEACON_TOKEN = "TODO-CF-TOKEN"

# Top-level pages. `og` is the share-card slug; `schema` selects JSON-LD blocks.
TOP = [
    dict(file="index.html", path="/", og="home", schema=["Organization", "WebSite"],
         robots=IDX,
         title="AI Cardiovascular Imaging & Screening | AIATELLA",
         desc="Explainable AI that automates cardiovascular measurements from MRI, CT and ultrasound — precise results in minutes, and earlier detection of disease."),
    dict(file="approach.html", path="/approach", og="approach", schema=["Organization"],
         robots=IDX,
         title="Our Approach: Explainable AI for Cardiac Imaging | AIATELLA",
         desc="How AIATELLA's Automated Imaging Measurement works — transparent AI that integrates with existing PACS and automates rule-based measurement tasks."),
    dict(file="solutions.html", path="/solutions", og="solutions",
         schema=["Organization", "SoftwareApplication"], robots=IDX,
         title="Aorta AIM — Automated Cardiovascular Analysis | AIATELLA",
         desc="Aorta AIM delivers instant, standardised aortic measurements from CT, MRI and ultrasound. Track and quantify aortic pathologies over time."),
    dict(file="company.html", path="/company", og="company", schema=["Organization"],
         robots=IDX,
         title="About AIATELLA — Our Story, Team & Mission",
         desc="Founded in Helsinki in 2022 to give doctors more time with patients and people more time with their loved ones. Meet the team behind AIATELLA."),
    dict(file="blog.html", path="/blog", og="blog", schema=["Organization"], robots=IDX,
         title="News & Resources on AI Cardiovascular Imaging | AIATELLA",
         desc="Research, press coverage and clinical evidence on AI-powered cardiovascular imaging and preventative screening from the AIATELLA team."),
    dict(file="contact.html", path="/contact", og="contact", schema=["Organization"],
         robots=IDX,
         title="Contact AIATELLA — Talk to Our Team",
         desc="Get in touch about AIATELLA's cardiovascular imaging AI, clinical partnerships, or preventative screening programmes."),
    dict(file="waitlist.html", path="/waitlist", og="waitlist",
         schema=["Organization", "MedicalBusiness"], robots=IDX,
         title="Join the Carotid Artery Screening Waitlist | AIATELLA",
         desc="Non-invasive carotid ultrasound screening, analysed by AI and reviewed by physicians. Join the waitlist for priority access and early-bird pricing."),
    dict(file="security.html", path="/security", og="security", schema=["Organization"],
         robots=IDX,
         title="Security & Vulnerability Disclosure | AIATELLA",
         desc="Report a security vulnerability to AIATELLA. Our disclosure policy, scope, researcher commitments and 90-day resolution timeline."),
    # Intentionally noindex (spec §2.3): boilerplate that would dilute crawl budget.
    dict(file="privacy.html", path="/privacy", og="default", schema=[], robots=NO,
         title="Privacy Policy | AIATELLA",
         desc="How AIATELLA collects, uses and protects your personal data, including your rights under GDPR and CCPA."),
    dict(file="terms.html", path="/terms", og="default", schema=[], robots=NO,
         title="Terms of Service | AIATELLA",
         desc="The terms governing use of the AIATELLA website and services."),
    dict(file="cookies.html", path="/cookies", og="default", schema=[], robots=NO,
         title="Cookie Policy | AIATELLA",
         desc="Which cookies and local storage the AIATELLA website uses, why, and how to control them."),
    dict(file="404.html", path="/404", og="default", schema=[], robots=NO,
         title="Page Not Found | AIATELLA",
         desc="That page could not be found. Browse AIATELLA's approach, solutions and resources instead."),
    dict(file="waitlist-thanks.html", path="/waitlist-thanks", og="default", schema=[],
         robots=NO,
         title="You're on the Waitlist | AIATELLA",
         desc="Thank you for joining the AIATELLA screening waitlist. Here is what happens next."),
    dict(file="contact-thanks.html", path="/contact-thanks", og="default", schema=[],
         robots=NO,
         title="Message Received | AIATELLA",
         desc="Thank you for contacting AIATELLA. Here is what happens next."),
]

# Blog posts. Titles are the real on-page headings; the `| AIATELLA` suffix is
# appended by _blog() only when it fits inside 60 characters.
#
# `date` is the publication month visible on the page itself (e.g. "June
# 2025"), recorded as an ISO year-month -- never a fabricated day. `None`
# means no date could be sourced from the page, and datePublished is omitted
# for that post.
#
# Only aiatella-2m-seed carries real article prose; every other post is a
# pointer/press-mention page (title, date, source, prev/next links), so it
# gets `WebPage` schema instead of `Article` (see FULL_ARTICLES below).
_POSTS = [
    ("aiatella-2m-seed",
     "AIATELLA raises €2M for cardiovascular imaging AI",
     "Finnish medtech AIATELLA secures €2M led by Nordic Science Investments to fund clinical trials and launch ultrasound-based preventative carotid screening.",
     "2025-06"),
    ("mtv3-features-aiatella",
     "MTV3: Finnish invention detects dangerous stenosis",
     "Finland's MTV3 covers AIATELLA's AI screening, which detects and quantifies dangerous carotid artery narrowing in minutes rather than hours.",
     "2025-07"),
    ("aiatella-instrumentarium",
     "AIATELLA receives Instrumentarium science grant",
     "AIATELLA receives a grant from the Instrumentarium Science Foundation to advance its automated cardiovascular image measurement technology.",
     "2025-02"),
    ("aiatella-ceo-featured-in-2025-ai-visionaries-womens-health",
     "AIATELLA CEO named a 2025 AI Visionary",
     "AIATELLA's CEO is featured in the 2025 AI Visionaries list for women's health, highlighting AI's role in closing the cardiovascular gender health gap.",
     "2025-01"),
    ("helsinkismart-aiatella",
     "How AIATELLA uses AI to transform radiology",
     "Helsinki Smart profiles how AIATELLA's explainable AI automates radiology measurement work, freeing clinicians for interpretation and patient care.",
     "2025-01"),
    ("hoiva",
     "AIATELLA featured in Hoiva & Terveys",
     "Finnish healthcare publication Hoiva & Terveys features AIATELLA's AI-powered approach to faster, more accessible cardiovascular imaging.",
     "2025-01"),
    ("slush2024-showcase",
     "AIATELLA demonstrates screening at Slush 2024",
     "AIATELLA demonstrated its AI-powered preventative cardiovascular screening at Slush 2024 in Helsinki.",
     "2024-11"),
    ("hi-nenc-report",
     "HI NENC report: early detection of CVD",
     "Health Innovation North East and North Cumbria reports on using AIATELLA's AI to increase early detection of cardiovascular disease.",
     "2024-10"),
    ("bbc-feature",
     "BBC: closing the gender gap in heart disease",
     "The BBC covers how AIATELLA's AI, trained on diverse populations, can help close the gender health gap in cardiovascular disease detection.",
     "2024-10"),
    ("valve-trial",
     "Evaluating AI aortic root and valve measurement",
     "Research evaluating AIATELLA's AI tool for automated measurement of the aortic root and valve in cardiac magnetic resonance imaging.",
     None),  # page shows only "May 4" with no year -- not sourceable
    ("from-mandate-to-mechanism-closing-the-delivery-gap-in-cardiovascular-screening",
     "Closing the cardiovascular screening delivery gap",
     "Why cardiovascular screening mandates stall at delivery, and the mechanisms needed to turn policy into population-level screening.",
     "2026-06"),
]

# Posts with real article prose on the page (not just title/date/source/nav).
# Everything else in _POSTS is a pointer/press-mention page and gets WebPage
# schema instead of Article.
FULL_ARTICLES = {"aiatella-2m-seed"}


def _blog(slug, title, desc, date=None):
    suffixed = f"{title} | AIATELLA"
    article_type = "Article" if slug in FULL_ARTICLES else "WebPage"
    return dict(
        file=f"blog-details/{slug}.html",
        path=f"/blog-details/{slug}",
        title=suffixed if len(suffixed) <= 60 else title,
        desc=desc, robots=IDX, og="blog", schema=["Organization", article_type],
        slug=slug, date=date,
    )


BLOG = [_blog(*p) for p in _POSTS]
PAGES = TOP + BLOG
INDEXABLE = [p for p in PAGES if "noindex" not in p["robots"]]


def by_file(name):
    name = name.replace("\\", "/")
    for p in PAGES:
        if p["file"] == name:
            return p
    raise KeyError(name)
