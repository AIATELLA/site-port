"""Render share cards to 1200x630 PNGs with headless Chrome."""
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TEMPLATE = "tools/og-cards/card.html"
LOGO = "assets/images/sIjcnF79hqocNDHvZGTIrQXQo0k.svg"
OUT = "assets/images/og"

# slug -> (eyebrow, headline)
CARDS = {
    "home":      ("Cardiovascular AI", "Radiology. Redefined."),
    "approach":  ("Our Approach", "Explainable AI that automates the measuring."),
    "solutions": ("Aorta AIM", "Track and quantify aortic pathologies over time."),
    "company":   ("Our Company", "Giving doctors and patients more time."),
    "blog":      ("News & Resources", "Evidence, press and research."),
    "contact":   ("Contact", "Talk to our team."),
    "waitlist":  ("Screening Waitlist", "Know your cardiovascular risk."),
    "security":  ("Security", "Responsible vulnerability disclosure."),
    "default":   ("Cardiovascular AI", "AIATELLA"),
}


def logo_data_uri():
    with open(LOGO, encoding="utf-8") as fh:
        svg = fh.read()
    svg = svg.replace("#231f20", "#ffffff")
    import base64
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def render(slug, eyebrow, headline, uri):
    with open(TEMPLATE, encoding="utf-8") as fh:
        html = fh.read()
    html = html.replace('id="eyebrow">Cardiovascular AI',
                        'id="eyebrow">%s' % eyebrow)
    html = html.replace('id="headline">Radiology. Redefined.',
                        'id="headline">%s' % headline)
    html = html.replace('id="mark" src=""', 'id="mark" src="%s"' % uri)
    tmp = os.path.join(tempfile.gettempdir(), "og-%s.html" % slug)
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(html)
    dest = os.path.join(OUT, slug + ".png")
    if os.path.exists(dest):
        os.remove(dest)
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", "--window-size=1200,630",
                    "--screenshot=" + os.path.abspath(dest),
                    "file:///" + tmp.replace("\\", "/")],
                   check=True, capture_output=True, timeout=90)
    if not os.path.exists(dest) or os.path.getsize(dest) < 5000:
        raise SystemExit("failed to render %s: file missing or blank (%d bytes)"
                         % (slug, os.path.getsize(dest) if os.path.exists(dest) else 0))
    return dest


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    uri = logo_data_uri()
    need = {p["og"] for p in pages.PAGES}
    missing = need - set(CARDS)
    if missing:
        raise SystemExit("manifest needs cards with no definition: %s" % sorted(missing))
    for slug in sorted(need):
        d = render(slug, *CARDS[slug], uri=uri)
        print("wrote", d, os.path.getsize(d), "bytes")