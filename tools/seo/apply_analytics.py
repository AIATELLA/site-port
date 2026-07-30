"""Upsert the Cloudflare Web Analytics beacon into every page's managed
`seo:analytics` head block. Idempotent -- safe to re-run.

Nothing else in tools/seo/ reproduces this beacon, so a fresh-tree rebuild
was silently missing it; this generator closes that gap (Fix 8). The token
is a placeholder (pages.CF_BEACON_TOKEN) on purpose -- verify.py check 11 is
meant to keep failing until the real Cloudflare token is set at cutover.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402
import htmlhead as H  # noqa: E402

BEACON = (
    '<script defer src="https://static.cloudflareinsights.com/beacon.min.js" '
    'data-cf-beacon=\'{"token": "%s"}\'></script>' % pages.CF_BEACON_TOKEN
)


def apply_one(p):
    path = p["file"]
    if not os.path.exists(path):
        return False
    t = H.upsert_block(H.read(path), "analytics", BEACON)
    H.write(path, t)
    return True


if __name__ == "__main__":
    n = sum(1 for p in pages.PAGES if apply_one(p))
    print("upserted analytics beacon into %d files" % n)
