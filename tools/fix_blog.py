#!/usr/bin/env python3
"""Fix blog page: add filter functionality, add missing resource cards."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOG = ROOT / "blog.html"

# Category mappings by card title substring
CATEGORY_MAP = {
    "Mtv3": "article",
    "MTV3": "article",
    "€2M": "press-release",
    "2M": "press-release",
    "Instrumentarium": "press-release",
    "AI Visionaries": "article",
    "Womens Health": "article",
    "HelsinkiSmart": "article",
    "revolutionize": "article",
    "Hoiva": "article",
    "Slush": "press-release",
    "HI NENC": "article",
    "NENC": "article",
    "BBC": "article",
    "Cureus": "paper",
    "Pubmed": "paper",
    "Novel AI Tool": "paper",
}

# New cards to add. Each has: title, source, date, href, target, category
NEW_CARDS = [
    {
        "title": "AI already examines cancers and may soon detect heart diseases from ultrasound images",
        "source": "Helsingin Sanomat",
        "date": "Aug 2026",
        "href": "https://www.hs.fi/tiede/art-2000012095538.html",
        "target": "_blank",
        "category": "article",
    },
    {
        "title": "From Mandate to Mechanism: Closing the Delivery Gap in Cardiovascular Screening",
        "source": "AIATELLA",
        "date": "Jun 2026",
        "href": "/blog-details/from-mandate-to-mechanism-closing-the-delivery-gap-in-cardiovascular-screening",
        "target": None,
        "category": "blog",
    },
    {
        "title": "Evaluating a Novel AI Tool for Automated Measurement of the Aortic Root and Valve",
        "source": "AIATELLA",
        "date": "May 2026",
        "href": "/blog-details/valve-trial",
        "target": None,
        "category": "paper",
    },
]


def categorize_card(card_html):
    """Determine category from card content."""
    for keyword, cat in CATEGORY_MAP.items():
        if keyword in card_html:
            return cat
    return "article"  # default


def add_data_category(card_html, category):
    """Add data-category attribute to the outermost <a> tag of a card."""
    return card_html.replace(
        'class="framer-1dmiu0e framer-1wqqh7k"',
        f'class="framer-1dmiu0e framer-1wqqh7k" data-category="{category}"',
        1,
    )


def make_card_desktop(card):
    """Generate a desktop-variant news card."""
    target_attr = f' target="{card["target"]}" rel="noopener"' if card["target"] else ""
    return (
        f'<!--$--><a class="framer-1dmiu0e framer-1wqqh7k" data-category="{card["category"]}" '
        f'href="{card["href"]}"{target_attr} '
        f'style="border-bottom-left-radius:20px;border-bottom-right-radius:20px;border-top-left-radius:20px;border-top-right-radius:20px">'
        f'<div class="framer-1pqpjhk-container">'
        f'<div class="news-card footer__scope-1 footer__scope-3 btn__base footer__scope-4 news-card__root news-card--desktop" '
        f'data-border="true" tabindex="0" '
        f'style="--border-bottom-width:1px;--border-color:var(--aiatella-color-border, rgb(225, 225, 225));--border-left-width:1px;--border-right-width:1px;--border-style:solid;--border-top-width:1px;background-color:var(--aiatella-color-surface-subtle, rgb(247, 247, 247));width:100%;border-bottom-left-radius:20px;border-bottom-right-radius:20px;border-top-left-radius:20px;border-top-right-radius:20px">'
        f'<div class="news-card__content">'
        f'<div class="news-card__title" style="--extracted-a0htzi:var(--aiatella-color-ink-warm, rgb(28, 19, 19));--framer-link-text-color:rgb(0, 153, 255);--framer-link-text-decoration:underline;transform:none">'
        f'<h3 class="framer-text" style="--font-selector:RlM7TWFucm9wZS1tZWRpdW0=;--framer-font-family:&quot;Manrope&quot;, &quot;Manrope Placeholder&quot;, sans-serif;--framer-font-size:24px;--framer-font-weight:500;--framer-letter-spacing:-0.2px;--framer-line-height:32px;--framer-text-alignment:left;--framer-text-color:var(--extracted-a0htzi, var(--aiatella-color-ink-warm, rgb(28, 19, 19)))">{card["title"]}</h3>'
        f'</div>'
        f'<div class="news-card__meta">'
        f'<div class="news-card__source" style="--framer-link-text-color:rgb(0, 153, 255);--framer-link-text-decoration:underline;transform:none">'
        f'<h4 class="framer-text framer-styles-preset-r0omsg" data-styles-preset="hlt44p_OT">{card["source"]}</h4>'
        f'</div>'
        f'<div class="news-card__date" style="--extracted-r6o4lv:rgba(0, 0, 0, 0.4);--framer-link-text-color:rgb(0, 153, 255);--framer-link-text-decoration:underline;transform:none">'
        f'<p class="framer-text framer-styles-preset-99gjg" data-styles-preset="yZyeiMEPd" style="--framer-text-color:var(--extracted-r6o4lv, rgba(0, 0, 0, 0.4))">{card["date"]}</p>'
        f'</div></div></div>'
        f'<div class="news-card__image" style="background-color:var(--aiatella-color-brand-red, rgb(209, 0, 0));transform:rotate(14deg)"></div>'
        f'</div></div></a><!--/$-->'
    )


def make_card_hover(card):
    """Generate a tablet/mobile-variant news card (hover variant)."""
    target_attr = f' target="{card["target"]}" rel="noopener"' if card["target"] else ""
    # Tablet uses smaller font sizes and news-card--hover class
    return (
        f'<!--$--><a class="framer-1dmiu0e framer-1wqqh7k" data-category="{card["category"]}" '
        f'href="{card["href"]}"{target_attr} '
        f'style="border-bottom-left-radius:20px;border-bottom-right-radius:20px;border-top-left-radius:20px;border-top-right-radius:20px">'
        f'<div class="framer-1pqpjhk-container">'
        f'<div class="news-card footer__scope-1 footer__scope-3 btn__base footer__scope-4 news-card__root news-card--hover" '
        f'data-border="true" tabindex="0" '
        f'style="--border-bottom-width:1px;--border-color:var(--aiatella-color-border, rgb(225, 225, 225));--border-left-width:1px;--border-right-width:1px;--border-style:solid;--border-top-width:1px;background-color:var(--aiatella-color-surface-subtle, rgb(247, 247, 247));width:100%;border-bottom-left-radius:20px;border-bottom-right-radius:20px;border-top-left-radius:20px;border-top-right-radius:20px">'
        f'<div class="news-card__content">'
        f'<div class="news-card__title" style="--extracted-a0htzi:var(--aiatella-color-ink-warm, rgb(28, 19, 19));--framer-link-text-color:rgb(0, 153, 255);--framer-link-text-decoration:underline;transform:none">'
        f'<h3 class="framer-text" style="--font-selector:RlM7TWFucm9wZS1tZWRpdW0=;--framer-font-family:&quot;Manrope&quot;, &quot;Manrope Placeholder&quot;, sans-serif;--framer-font-size:20px;--framer-font-weight:500;--framer-letter-spacing:-0.2px;--framer-line-height:26px;--framer-text-alignment:left;--framer-text-color:var(--extracted-a0htzi, var(--aiatella-color-ink-warm, rgb(28, 19, 19)))">{card["title"]}</h3>'
        f'</div>'
        f'<div class="news-card__meta">'
        f'<div class="news-card__source" style="--framer-link-text-color:rgb(0, 153, 255);--framer-link-text-decoration:underline;transform:none">'
        f'<h4 class="framer-text framer-styles-preset-19iuj27" data-styles-preset="C1zhxrynF">{card["source"]}</h4>'
        f'</div>'
        f'<div class="news-card__date" style="--extracted-r6o4lv:rgba(0, 0, 0, 0.4);--framer-link-text-color:rgb(0, 153, 255);--framer-link-text-decoration:underline;transform:none">'
        f'<p class="framer-text framer-styles-preset-10g3946" data-styles-preset="BF4w3L9Bq" style="--framer-text-color:var(--extracted-r6o4lv, rgba(0, 0, 0, 0.4))">{card["date"]}</p>'
        f'</div></div></div>'
        f'<div class="news__variant-inner" style="background-color:var(--aiatella-color-brand-red, rgb(209, 0, 0));transform:rotate(13deg)"></div>'
        f'</div></div></a><!--/$-->'
    )


def process_card_container(container_html, variant):
    """Add data-category to existing cards and append new cards."""
    # Split into individual cards by the <!--/$--><!--$--> separator
    # Each card starts with <!--$--><a and ends with </a><!--/$-->
    card_pattern = r'(<!--\$--><a class="framer-1dmiu0e.*?</a><!--/\$-->)'
    cards = re.findall(card_pattern, container_html)

    result = container_html
    for card in cards:
        category = categorize_card(card)
        updated = add_data_category(card, category)
        result = result.replace(card, updated, 1)

    # Append new cards before the closing <!--/$--></div>
    new_cards_html = ""
    for c in NEW_CARDS:
        if variant == "desktop":
            new_cards_html += make_card_desktop(c)
        else:
            new_cards_html += make_card_hover(c)

    # Insert before the final <!--/$--></div>
    result = result.replace("<!--/$--></div>", f"{new_cards_html}<!--/$--></div>", 1)

    return result


def main():
    html = BLOG.read_text(encoding="utf-8")

    # Find all card containers (class="framer-o35a9e")
    # There are 3: desktop (line ~297), tablet (line ~339), mobile (line ~381)
    container_pattern = r'(<div class="framer-o35a9e">.*?<!--/\$--></div>)'
    containers = list(re.finditer(container_pattern, html))

    print(f"Found {len(containers)} card containers")

    for i, match in enumerate(reversed(containers)):
        # Process in reverse to preserve positions
        variant = "desktop" if i == len(containers) - 1 else "hover"
        old = match.group(0)
        new = process_card_container(old, variant)
        html = html[:match.start()] + new + html[match.end():]
        print(f"  Container {len(containers) - i}: {variant} variant updated")

    # Add blog-filter.js script tag before </body>
    filter_script = '    <script src="/assets/js/blog-filter.js"></script>\n'
    html = html.replace("</body>", f"{filter_script}</body>")

    BLOG.write_text(html, encoding="utf-8")
    print("\nblog.html updated successfully")


if __name__ == "__main__":
    main()
