"""Phase G: generate real responsive image variants and shrink oversized
originals. Spec: .superpowers/sdd/phase-g-images/task-1-brief.md Step 1.

Background: Framer's srcset ladders (512/1024/2048/4096/intrinsic) all
pointed at the same original file -- the intent (a real doubling ladder)
was honest, only the URLs were fake, so browsers downloaded up to an
8192px original to fill a ~1049 CSS px slot. This script makes the ladder
real: it resizes each distinct image referenced by an <img> tag (across
all 25 pages) down to a capped set of widths and re-encodes the base
file itself at the cap, which is what actually shrinks the worst
offenders (a 9.9 MB / 8192x5464 JPEG among them).

Ladder policy (uniform, no per-file tuning) -- see brief for rationale:
    candidates = [c for c in (512, 1024, 2048) if c < W]
    cap        = min(W, 2048)
    widths     = sorted(set(candidates) | {cap})
If W <= 512, there is nothing to gain: no variants, base left untouched.

Why there is a manifest (tools/images/manifest.json), committed alongside
the images: once this script overwrites a base file at its cap, the true
original pixels are gone -- there is nothing left on disk to re-derive
from. Empirically, re-decoding an already-processed JPEG/WebP and
re-encoding it at the same quality is NOT perfectly byte-stable across
generations (small quantization drift each pass), so a naive "recompute
from whatever is currently on disk" --check would flag its own prior
output as stale forever and slowly degrade quality on every run. The
manifest instead records the sha256 this script itself produced for each
base and variant file; a matching hash means "already done, don't
re-touch it", so the fixed point is genuinely stable. A file with no
manifest entry (new image, or a manifest miss because someone replaced
the source under the same name) is (re)processed from whatever bytes are
currently on disk -- which is the true original in that case.

Encoding:
    JPEG: quality=82, optimize=True, progressive=True, RGB, no EXIF
          (Pillow only writes EXIF if you hand it back explicitly). Any
          EXIF rotation is baked into the pixels first -- see plan_file.
    PNG:  optimize=True. RGBA preserved where the source has genuine
          partial transparency, else RGB. Never resized directly in P
          (palette) mode -- LANCZOS on a palette needs a full-colour
          image first or it bands.
    WebP: quality=84, method=6. Same alpha handling as PNG.
A variant that would land on disk larger than the file it was resized
from is dropped and logged instead of written (never a net loss).
"""
import hashlib
import io
import json
import os
import re
import sys

from PIL import Image, ImageOps

TOOLS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS_DIR)
sys.path.insert(0, os.path.join(TOOLS_DIR, "seo"))
import pages  # noqa: E402

IMAGES_DIR = os.path.join(ROOT, "assets", "images")
OG_DIR = os.path.join(IMAGES_DIR, "og")  # must never be touched (fixed 1200x630 cards)
MANIFEST_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manifest.json")

IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
SRC_RE = re.compile(r'\bsrc="([^"]*)"')

CANDIDATES = (512, 1024, 2048)

FORMATS_BY_EXT = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}


def discover_files():
    """Distinct basenames referenced by <img src="..."> across all 25 pages."""
    names = set()
    for p in pages.PAGES:
        path = os.path.join(ROOT, p["file"])
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            text = fh.read()
        for m in IMG_RE.finditer(text):
            sm = SRC_RE.search(m.group(0))
            if sm:
                names.add(os.path.basename(sm.group(1)))
    return sorted(names)


def ladder(w):
    cap = min(w, 2048)
    widths = sorted({c for c in CANDIDATES if c < w} | {cap})
    return widths, cap


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def save_manifest(manifest):
    with open(MANIFEST_PATH, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")


def has_real_alpha(im):
    """True if `im` carries genuine (non-fully-opaque) transparency."""
    if im.mode == "RGBA":
        return im.getchannel("A").getextrema() != (255, 255)
    if im.mode == "P" and "transparency" in im.info:
        return im.convert("RGBA").getchannel("A").getextrema() != (255, 255)
    return False


def prep_for_resize(im):
    """Return an image in a mode LANCZOS resamples cleanly (no palette)."""
    if im.mode == "P":
        return im.convert("RGBA") if has_real_alpha(im) else im.convert("RGB")
    if im.mode not in ("RGB", "RGBA", "L"):
        return im.convert("RGBA") if "A" in im.mode else im.convert("RGB")
    return im


def encode(im, fmt):
    buf = io.BytesIO()
    if fmt == "JPEG":
        im.convert("RGB").save(buf, format="JPEG", quality=82, optimize=True, progressive=True)
    elif fmt == "PNG":
        out = im.convert("RGBA") if has_real_alpha(im) else im.convert("RGB")
        out.save(buf, format="PNG", optimize=True)
    elif fmt == "WEBP":
        out = im.convert("RGBA") if has_real_alpha(im) else im.convert("RGB")
        out.save(buf, format="WEBP", quality=84, method=6)
    else:
        raise ValueError("unsupported format %r" % fmt)
    return buf.getvalue()


def resized_bytes(im, fmt, target_w, source_h, source_w):
    if target_w == source_w:
        work = im
    else:
        target_h = round(source_h * target_w / source_w)
        work = im.resize((target_w, target_h), Image.LANCZOS)
    return encode(work, fmt)


def variant_path(base_path, width):
    stem, ext = os.path.splitext(base_path)
    return "%s-%dw%s" % (stem, width, ext)


def variant_looks_correct(vpath, width):
    if not os.path.exists(vpath):
        return False
    try:
        with Image.open(vpath) as vim:
            return vim.size[0] == width
    except Exception:
        return False


def plan_file(fname, manifest):
    """Compute the on-disk action needed for one image. Never writes.
    Returns a dict consumed by apply_plan()."""
    path = os.path.join(IMAGES_DIR, fname)
    ext = os.path.splitext(fname)[1].lower()
    fmt = FORMATS_BY_EXT[ext]
    current_bytes = open(path, "rb").read()
    current_hash = sha256(current_bytes)
    im = Image.open(io.BytesIO(current_bytes))
    im.load()
    # Bake in EXIF orientation BEFORE measuring or resizing. Browsers honour
    # the EXIF Orientation tag (image-orientation: from-image is the CSS
    # default), but Pillow hands back the raw, unrotated pixel grid. So an
    # image tagged Orientation=6 displays rotated 90 degrees in Chrome while
    # measuring as landscape here. Re-encoding drops EXIF, and if we had not
    # rotated the pixels first the image would silently render in a different
    # orientation than it did before -- which is exactly what happened to
    # assets/images/TiIgVJqdfp7Xe2j41XUsLQsUHQ.jpg on the first run of this
    # tool. Transposing makes the pixels match what the browser used to show,
    # so dropping the tag afterwards is a no-op visually. It also means W/H
    # below are the *displayed* dimensions, which is what the ladder and the
    # srcset w-descriptors must be based on.
    im = ImageOps.exif_transpose(im)
    W, H = im.size

    result = dict(file=fname, path=path, intrinsic=(W, H), before=len(current_bytes),
                  after=len(current_bytes), status=None, variants_to_write=[],
                  base_new_bytes=None, skipped=[], manifest_entry=None)

    if W <= 512:
        result["status"] = "small"  # nothing to gain, base stays byte-identical, ever
        return result

    widths, cap = ladder(W)
    expected_variant_widths = [w for w in widths if w != cap]

    entry = manifest.get(fname)
    if entry and entry.get("base_sha256") == current_hash:
        result["status"] = "up-to-date"
        # Repair any variant that has gone missing/wrong-width since the
        # manifest was written -- resized from the current (already
        # capped) base, which is always >= every rung, so never an upscale.
        # Only repair rungs the manifest actually recorded as written: a
        # rung absent from entry["variants"] was deliberately dropped by
        # the not-smaller-than-source guard, not "missing".
        recorded_widths = {int(w) for w in entry.get("variants", {})}
        work_im = None
        for w in expected_variant_widths:
            if w not in recorded_widths:
                continue
            vpath = variant_path(path, w)
            if variant_looks_correct(vpath, w):
                continue
            if work_im is None:
                work_im = prep_for_resize(im)
            data = resized_bytes(work_im, fmt, w, H, W)
            if len(data) >= result["before"]:
                continue  # guard still holds; not actually a repair
            result["variants_to_write"].append((w, vpath, data))
        return result

    if not entry:
        # No manifest record. Distinguish "this was already correctly
        # produced before the manifest existed" (every expected variant
        # is already present at the right width, and the base is already
        # within cap) from "genuinely new/changed source" -- only the
        # latter needs the lossy pipeline; the former is reconciled by
        # simply recording hashes of what's already on disk.
        all_present = W <= 2048 and all(
            variant_looks_correct(variant_path(path, w), w) for w in expected_variant_widths)
        if all_present:
            result["status"] = "reconcile"
            return result

    # Genuinely stale: (re)run the real pipeline from whatever bytes are
    # currently on disk (the true original, in the normal case).
    result["status"] = "process"
    work_im = prep_for_resize(im)
    for w in expected_variant_widths:
        vpath = variant_path(path, w)
        data = resized_bytes(work_im, fmt, w, H, W)
        if len(data) >= result["before"]:
            result["skipped"].append((w, len(data)))
            continue
        result["variants_to_write"].append((w, vpath, data))

    base_data = resized_bytes(work_im, fmt, cap, H, W)
    if len(base_data) < result["before"]:
        result["base_new_bytes"] = base_data
        result["after"] = len(base_data)
    # else: recompressing at the cap didn't help -- leave the base as-is.
    return result


def apply_plan(result, manifest, write):
    """Returns the list of (kind, path, size) changes made (or, in --check
    mode, that would be made)."""
    changes = []
    fname = result["file"]
    path = result["path"]

    if result["status"] == "small":
        return changes

    for w, vpath, data in result["variants_to_write"]:
        existing = open(vpath, "rb").read() if os.path.exists(vpath) else None
        if existing != data:
            changes.append(("variant", vpath, len(data)))
            if write:
                with open(vpath, "wb") as fh:
                    fh.write(data)

    if result["status"] == "process" and result["base_new_bytes"] is not None:
        existing = open(path, "rb").read()
        if existing != result["base_new_bytes"]:
            changes.append(("base", path, len(result["base_new_bytes"])))
            if write:
                with open(path, "wb") as fh:
                    fh.write(result["base_new_bytes"])

    if write and result["status"] in ("process", "reconcile", "up-to-date"):
        # Record/refresh the manifest entry against whatever is now on
        # disk (post-write), so the next run's hash check matches.
        base_bytes = result["base_new_bytes"] if result["base_new_bytes"] is not None \
            else open(path, "rb").read()
        variants_meta = {}
        widths, cap = ladder(Image.open(io.BytesIO(base_bytes)).size[0]
                              if result["status"] != "up-to-date" else result["intrinsic"][0])
        for w in [w for w in widths if w != cap]:
            vpath = variant_path(path, w)
            if os.path.exists(vpath):
                with open(vpath, "rb") as fh:
                    variants_meta[str(w)] = dict(
                        path=os.path.basename(vpath), sha256=sha256(fh.read()))
        manifest[fname] = dict(base_sha256=sha256(base_bytes), variants=variants_meta)

    return changes


def main():
    check = "--check" in sys.argv
    files = discover_files()
    manifest = load_manifest()
    total_before = total_after = 0
    all_changes = []
    rows = []
    for fname in files:
        result = plan_file(fname, manifest)
        changes = apply_plan(result, manifest, write=not check)
        all_changes.extend(changes)
        total_before += result["before"]
        total_after += result["after"]
        rows.append((fname, result["intrinsic"], result["before"], result["after"],
                     len(result["variants_to_write"]), result["status"]))
        for w, size in result["skipped"]:
            print("  skip rung %dw for %s: variant (%d bytes) not smaller than source"
                  % (w, fname, size))

    print("%-45s %12s %14s %14s %10s  %s" % ("file", "intrinsic", "before", "after", "variants", "status"))
    for fname, (w, h), before, after, nvar, status in rows:
        print("%-45s %5dx%-6d %14s %14s %10d  %s" % (fname, w, h, before, after, nvar, status))
    saving = total_before - total_after
    print("\nTOTAL before=%s after=%s saving=%s bytes (%.1f%%)"
          % (total_before, total_after, saving,
             100.0 * saving / total_before if total_before else 0))

    if not check:
        save_manifest(manifest)

    if check:
        if all_changes:
            print("\nSTALE -- %d change(s) needed:" % len(all_changes))
            for kind, cpath, size in all_changes:
                print("  [%s] %s (%d bytes)" % (kind, cpath, size))
            return 1
        print("\nclean -- no changes needed")
        return 0

    print("\nwrote %d file(s)" % len(all_changes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
