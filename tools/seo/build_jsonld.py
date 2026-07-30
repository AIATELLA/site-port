"""Inject JSON-LD from the manifest into a managed head block. Idempotent."""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402
import htmlhead as H  # noqa: E402

ORG_ID = pages.SITE + "/#organization"
LOGO = pages.SITE + "/assets/images/sIjcnF79hqocNDHvZGTIrQXQo0k.svg"

# Regulatory-overclaim guard. Targets actual overclaiming -- a regulator word
# next to a clearance/approval verb, the invalid DiagnosticProcedure type, and
# verbs asserting the product diagnoses -- while permitting legitimate medtech
# copy such as "diagnostic imaging" or "ISO 13485 certified quality system".
# This is the single source of truth for the pattern; verify.py's check_6
# imports it so the gate that actually runs in CI enforces the same rule.
BANNED = re.compile(
    r"\b(FDA|CE)\b[^.]{0,30}\b(cleared|approved|certified|marked)\b"
    r"|DiagnosticProcedure"
    r"|\bdiagnos(e|es|ing)\b", re.I)


def organization():
    return {
        "@context": "https://schema.org", "@type": "Organization", "@id": ORG_ID,
        "name": "AIATELLA", "legalName": "AIATELLA Oy", "url": pages.SITE + "/",
        "logo": LOGO, "foundingDate": "2022",
        "email": "contact@aiatella.com",
        "sameAs": ["https://www.linkedin.com/company/aiatella/"],
        "address": dict({"@type": "PostalAddress"}, **pages.ORG_ADDRESS),
        "description": ("AIATELLA builds explainable AI that automates cardiovascular "
                        "image measurement from MRI, CT and ultrasound."),
    }


def website():
    return {"@context": "https://schema.org", "@type": "WebSite",
            "@id": pages.SITE + "/#website", "url": pages.SITE + "/",
            "name": "AIATELLA", "inLanguage": "en-GB",
            "publisher": {"@id": ORG_ID}}


def software_application():
    return {"@context": "https://schema.org", "@type": "SoftwareApplication",
            "name": "Aorta AIM", "applicationCategory": "HealthApplication",
            "operatingSystem": "Web-based, integrates with PACS",
            "publisher": {"@id": ORG_ID},
            "description": ("Automated Image Measurement for the aorta. Delivers instant, "
                            "standardised aortic measurements from CT, MRI and ultrasound, "
                            "and tracks change over time.")}


def medical_business():
    return {"@context": "https://schema.org", "@type": "MedicalBusiness",
            "name": "AIATELLA Vascular Screening", "url": pages.SITE + "/waitlist",
            "medicalSpecialty": "Cardiovascular",
            "address": dict({"@type": "PostalAddress"}, **pages.ORG_ADDRESS),
            "parentOrganization": {"@id": ORG_ID},
            "availableService": [{
                "@type": "MedicalProcedure", "name": "Carotid Artery Ultrasound Screening",
                "procedureType": "https://schema.org/NoninvasiveProcedure",
                "howPerformed": ("Non-invasive carotid ultrasound, analysed by AI and "
                                 "reviewed by a physician."),
                # Pre-launch: the screening has not launched and regulatory
                # approvals are pending. An unqualified offered-service
                # declaration would overstate reality, so the offer is
                # explicitly marked PreOrder rather than left implying the
                # service is available today.
                "offers": {"@type": "Offer", "availability": "https://schema.org/PreOrder"},
            }]}


def article(p):
    title = p["title"].split(" | ")[0]
    node = {"@context": "https://schema.org", "@type": "Article",
            "headline": title, "description": p["desc"],
            "mainEntityOfPage": pages.SITE + p["path"],
            "image": "%s/assets/images/og/%s.png" % (pages.SITE, p["og"]),
            "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
            "inLanguage": "en-GB"}
    if p.get("date"):
        node["datePublished"] = p["date"]
    return node


def webpage(p):
    # Pointer/press-mention posts: title, date, source and prev/next links,
    # but no article body on the page. Article schema would describe content
    # that is not there, so these get WebPage instead (spec/Fix 6).
    title = p["title"].split(" | ")[0]
    node = {"@context": "https://schema.org", "@type": "WebPage",
            "name": title, "description": p["desc"],
            "url": pages.SITE + p["path"],
            "primaryImageOfPage": "%s/assets/images/og/%s.png" % (pages.SITE, p["og"]),
            "isPartOf": {"@id": pages.SITE + "/#website"},
            "inLanguage": "en-GB"}
    if p.get("date"):
        node["datePublished"] = p["date"]
    return node


def breadcrumbs(p):
    title = p["title"].split(" | ")[0]
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": pages.SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Resources",
                 "item": pages.SITE + "/blog"},
                {"@type": "ListItem", "position": 3, "name": title,
                 "item": pages.SITE + p["path"]},
            ]}


BUILDERS = {"Organization": lambda p: organization(), "WebSite": lambda p: website(),
            "SoftwareApplication": lambda p: software_application(),
            "MedicalBusiness": lambda p: medical_business(), "Article": article,
            "WebPage": webpage}


def build_nodes(p):
    nodes = [BUILDERS[name](p) for name in p["schema"]]
    if p["file"].startswith("blog-details/"):
        nodes.append(breadcrumbs(p))
    return nodes


def validate(p, nodes):
    """Raise before anything touches disk if a node is invalid or trips the
    regulatory-overclaim guard. Called pre-write so a violation never lands
    on disk (Fix 4)."""
    for node in nodes:
        blob = json.dumps(node, ensure_ascii=False)
        if BANNED.search(blob):
            raise SystemExit("REGULATORY CLAIM in %s: %r" % (p["file"], blob))


def apply_one(p):
    if not os.path.exists(p["file"]) or not p["schema"]:
        return False
    nodes = build_nodes(p)
    validate(p, nodes)
    block = "\n".join(
        '<script type="application/ld+json">%s</script>'
        % json.dumps(n, ensure_ascii=False, separators=(",", ":")) for n in nodes)
    t = H.upsert_block(H.read(p["file"]), "jsonld", block)
    H.write(p["file"], t)
    return True


if __name__ == "__main__":
    n = 0
    for p in pages.PAGES:
        if apply_one(p):
            n += 1
    print("injected JSON-LD into %d files" % n)
