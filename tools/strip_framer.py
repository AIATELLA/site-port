#!/usr/bin/env python3
"""Strip all Framer artifacts from HTML files and normalize paths."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# All HTML files except partials and tool templates
HTML_FILES = sorted(
    [p for p in ROOT.rglob("*.html")
     if "partials" not in p.parts
     and "tools" not in p.parts
     and ".git" not in p.parts]
)

THANK_YOU_PAGES = {"contact-thanks.html", "waitlist-thanks.html"}


def strip_framer(html: str, filepath: Path) -> str:
    # 1. Remove <!-- Made in Framer ... --> comment (line 2 typically)
    html = re.sub(r'\s*<!--\s*Made in Framer\b[^>]*-->\s*\n?', '\n', html)

    # 2. Remove <meta name="generator" content="Framer ...">
    html = re.sub(
        r'\s*<meta\s+name="generator"\s+content="Framer[^"]*"\s*/?\s*>\s*\n?',
        '\n', html
    )

    # 3. Remove all <link rel="modulepreload" ...> tags
    html = re.sub(
        r'\s*<link\s+rel="modulepreload"[^>]*>\s*\n?',
        '', html
    )

    # 4. Remove <script type="framer/appear"> ... </script> blocks
    html = re.sub(
        r'\s*<script\s+type="framer/appear"[^>]*>.*?</script>\s*\n?',
        '', html, flags=re.DOTALL
    )

    # 5. Remove the appear-animation inline script
    #    It contains "animateAppearEffects" — unique identifier
    html = re.sub(
        r'\s*<script>\s*document\.addEventListener\("DOMContentLoaded"[^<]*animateAppearEffects[^<]*</script>\s*\n?',
        '', html, flags=re.DOTALL
    )


    # 5b. Remove the Framer variant URL-param propagation script
    #     Identified by: var w="framer_variant"
    html = re.sub(
        r"\s*<script>[^<]*var w=.framer_variant.[^<]*</script>\s*\n?",
        "", html, flags=re.DOTALL
    )

    # 5c. Remove the Framer animator runtime script
    #     Identified by: var animator=(()=>{ ... })()
    html = re.sub(
        r"\s*<script>var animator=\(\(\)=>\{.*?\}\)\(\)</script>\s*\n?",
        "", html, flags=re.DOTALL
    )

    # 5d. Remove the Framer appear-effects invocation script
    #     Identified by: framer-appear-start / animateAppearEffects
    html = re.sub(
        r"\s*<script>\(\(\)=>\{function c\(.*?animator\.animateAppearEffects.*?</script>\s*\n?",
        "", html, flags=re.DOTALL
    )


    # 5b. Remove the Framer variant URL-param propagation script
    #     Identified by: var w="framer_variant"
    html = re.sub(
        r'\s*<script>[^<]*var w="framer_variant"[^<]*</script>\s*\n?',
        '', html, flags=re.DOTALL
    )

    # 5c. Remove the Framer animator runtime script
    #     Identified by: var animator=(()=>{
    html = re.sub(
        r'\s*<script>var animator=\(\(\)=>\{.*?\}\)\(\)</script>\s*\n?',
        '', html, flags=re.DOTALL
    )

    # 5d. Remove the Framer appear-effects invocation script
    #     Identified by: function c(i,o,s){...animator.animateAppearEffects...
    html = re.sub(
        r'\s*<script>\(\(\)=>\{function c\(.*?</script>\s*\n?',
        '', html, flags=re.DOTALL
    )

    # 6. Remove data-framer-* attributes (but keep data-form, data-field, etc.)
    html = re.sub(r'\s+data-framer-[\w-]+="[^"]*"', '', html)
    # Also handle boolean data-framer attributes (no value)
    html = re.sub(r'\s+data-framer-[\w-]+(?=[>\s/])', '', html)

    # 7. Remove data-redirect-timezone="1" from <html> tag
    html = re.sub(r'\s+data-redirect-timezone="[^"]*"', '', html)

    # 8. Replace Cloudflare analytics with Clarity
    html = re.sub(
        r'\s*<script\s+defer\s+src="https://static\.cloudflareinsights\.com/beacon\.min\.js"[^>]*>\s*</script>\s*\n?',
        r"""
    <script>
      (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
      })(window,document,"clarity","script","TODO-CLARITY-ID");
    </script>
""",
        html
    )

    return html


def normalize_urls(html: str, filepath: Path) -> str:
    """Normalize internal href to clean URLs and CSS/JS paths to absolute."""
    depth = len(filepath.relative_to(ROOT).parts) - 1  # 0 for root, 1 for blog-details/

    # Normalize internal page links: href="approach.html" -> href="/approach"
    # Also href="../approach.html" -> href="/approach"
    def fix_page_link(m):
        prefix = m.group(1)  # href=" or href='
        path = m.group(2)    # the URL
        suffix = m.group(3)  # closing quote

        # Skip external URLs, anchors, mailto, tel, javascript
        if path.startswith(('http', '#', 'mailto:', 'tel:', 'javascript:')):
            return m.group(0)
        # Skip /api/ paths
        if path.startswith('/api/'):
            return m.group(0)

        # Strip ../ prefix
        clean = re.sub(r'^(\.\./)+', '', path)
        # Strip .html extension
        clean = re.sub(r'\.html$', '', clean)
        # Handle index -> /
        if clean == 'index' or clean == '':
            clean = '/'
        elif not clean.startswith('/'):
            clean = '/' + clean

        return f'{prefix}{clean}{suffix}'

    html = re.sub(
        r'(href=["\'])([^"\']*)(["\']\s*)',
        fix_page_link, html
    )

    # Normalize asset paths to absolute
    # href="assets/..." -> href="/assets/..."
    html = re.sub(r'((?:href|src)=["\'])(?:\.\./)*assets/', r'\1/assets/', html)
    # href="design/..." -> href="/design/..."
    html = re.sub(r'((?:href|src)=["\'])(?:\.\./)*design/', r'\1/design/', html)

    return html


def add_noindex(html: str, filepath: Path) -> str:
    """Add noindex to thank-you pages."""
    if filepath.name in THANK_YOU_PAGES:
        if 'name="robots"' not in html:
            html = html.replace(
                '</head>',
                '    <meta name="robots" content="noindex, nofollow">\n  </head>'
            )
    return html


def main():
    changed = 0
    for fp in HTML_FILES:
        original = fp.read_text(encoding="utf-8")
        result = original
        result = strip_framer(result, fp)
        result = normalize_urls(result, fp)
        result = add_noindex(result, fp)

        # Clean up multiple blank lines left by removals
        result = re.sub(r'\n{3,}', '\n\n', result)

        if result != original:
            fp.write_text(result, encoding="utf-8")
            print(f"  updated: {fp.relative_to(ROOT)}")
            changed += 1
        else:
            print(f"  skipped: {fp.relative_to(ROOT)} (no changes)")

    print(f"\n{changed}/{len(HTML_FILES)} files updated")


if __name__ == "__main__":
    main()
