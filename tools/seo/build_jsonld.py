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


def organization():
    return {
        "@context": "https://schema.org", "@type": "Organization", "@id": ORG_ID,
        "name": "AIATELLA", "legalName": "AIATELLA Oy", "url": pages.SITE + "/",
        "logo": LOGO, "foundingDate": "2022",
        "email": "contact@aiatella.com",
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
            "medicalSpecialty": "Vascular",
            "address": dict({"@type": "PostalAddress"}, **pages.ORG_ADDRESS),
            "parentOrganization": {"@id": ORG_ID},
            "availableService": [{
                "@type": "MedicalProcedure", "name": "Carotid Artery Ultrasound Screening",
                "procedureType": "https://schema.org/NoninvasiveProcedure",
                "howPerformed": ("Non-invasive carotid ultrasound, analysed by AI and "
                                 "reviewed by a physician."),
            }]}


def article(p):
    title = p["title"].split(" | ")[0]
    return {"@context": "https://schema.org", "@type": "Article",
            "headline": title, "description": p["desc"],
            "mainEntityOfPage": pages.SITE + p["path"],
            "image": "%s/assets/images/og/%s.png" % (pages.SITE, p["og"]),
            "author": {"@id": ORG_ID}, "publisher": {"@id": ORG_ID},
            "inLanguage": "en-GB"}


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
            "MedicalBusiness": lambda p: medical_business(), "Article": article}


def apply_one(p):
    if not os.path.exists(p["file"]) or not p["schema"]:
        return False
    nodes = [BUILDERS[name](p) for name in p["schema"]]
    if "Article" in p["schema"]:
        nodes.append(breadcrumbs(p))
    block = "\n".join(
        '<script type="application/ld+json">%s</script>'
        % json.dumps(n, ensure_ascii=False, separators=(",", ":")) for n in nodes)
    t = H.upsert_block(H.read(p["file"]), "jsonld", block)
    H.write(p["file"], t)
    return True


if __name__ == "__main__":
    banned = re.compile(r"\bFDA\b|\bCE[ -]mark|\bcleared\b|\bcertified\b|DiagnosticProcedure|\bdiagnos(is|tic)\b", re.I)
    n = 0
    for p in pages.PAGES:
        if apply_one(p):
            n += 1
    for p in pages.PAGES:
        if os.path.exists(p["file"]):
            for b in re.findall(r"application/ld\+json[^>]*>(.*?)</script>",
                                H.read(p["file"]), re.S):
                if banned.search(b):
                    raise SystemExit("REGULATORY CLAIM in %s" % p["file"])
    print("injected JSON-LD into %d files" % n)
