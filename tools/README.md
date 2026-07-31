# Regenerating the site

The 25 HTML files are machine-generated/managed in layers. To regenerate
from scratch (or after editing a partial, a page's own content, or the
page metadata in `tools/seo/pages.py`), run these in order:

```
python tools/prettify_html.py <files>          # 1. reformat to readable, indented markup
python tools/build-partials.py                 # 2. render partials/nav.html + partials/footer.html into every page
python tools/seo/apply_meta.py                  # 3. title/description/canonical/OG/Twitter meta
python tools/seo/build_jsonld.py                #    JSON-LD structured data
python tools/seo/build_crawl.py                 #    robots.txt + sitemap.xml
python tools/seo/apply_analytics.py             #    Cloudflare Web Analytics beacon
python tools/prettify_html.py <files>           # 4. re-run once more (see note below)
```

`<files>` is every root HTML file plus `blog-details/*.html`, e.g.:

```
python tools/prettify_html.py 404.html approach.html blog.html company.html \
  contact.html contact-thanks.html cookies.html index.html privacy.html \
  security.html solutions.html terms.html waitlist.html waitlist-thanks.html \
  blog-details/*.html
```

## Why the formatter runs twice

Step 3's generators (`tools/seo/htmlhead.py`'s `upsert_block`) always
flatten their own managed blocks (`<!-- seo:jsonld -->`,
`<!-- seo:analytics -->`) back to column 0 when they rewrite them. This is
pre-existing, harmless, documented behavior (see phase-d and phase-e
reports) -- it doesn't touch anything outside those two blocks. Re-running
`prettify_html.py` after step 3 restores full indentation for the
committed state. Verify with `--check`: it should report
`would change 0/25 files` after the second formatter pass.

## Why `build-partials.py` runs before the SEO generators, not after

`build-partials.py` only touches the `<nav>`/`<footer>` subtrees (between
`<!-- partial:nav:BREAKPOINT -->` / `<!-- partial:footer:BREAKPOINT -->`
markers); the SEO generators only touch `<head>` and two of their own
managed blocks. The two don't overlap, so the order between them doesn't
affect correctness -- but partials go first here so that a fresh export
(no markers yet) gets its nav/footer migrated to managed blocks before
anything else touches the file.

## Verifying everything stayed idempotent

```
python tools/prettify_html.py --check <files>     # would change 0/25 files
python tools/build-partials.py                    # run twice; git status must be clean between runs
python tools/seo/verify.py                        # FAIL (25) is expected -- all findings are
                                                    # check [11], the placeholder Cloudflare token;
                                                    # do not replace it here (see tools/seo/pages.py)
python design/build-tokens.py --check              # OK: design.css and tokens.ts match tokens.json
```

## Editing the nav or footer

Edit `partials/nav.html` or `partials/footer.html` (see the header
comment in each for the `{{DEPTH}}` / `{{CUR:slug}}` placeholder
contract), then re-run `tools/build-partials.py` -- it finds the existing
`<!-- partial:... -->` markers in every page and refreshes their content
in place. Never hand-edit the markup between a page's own
`<!-- partial:... start/end -->` markers; it will be overwritten on the
next run.
