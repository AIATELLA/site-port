"""Screenshot every page at desktop and mobile widths."""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pages  # noqa: E402

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BASE = "http://127.0.0.1:8000"
SIZES = {"desktop": "1440,2400", "mobile": "390,2400"}


def shoot(outdir):
    os.makedirs(outdir, exist_ok=True)
    # A fresh, throwaway profile per run. Without --user-data-dir, headless
    # Chrome uses the caller's default profile and its persistent disk cache;
    # a page fetched once under a given URL can then be served from cache on
    # every later run, silently hiding real content changes between "before"
    # and "after" captures taken minutes or days apart on the same server URL.
    profile_dir = tempfile.mkdtemp(prefix="shoot_profile_")
    try:
        for p in pages.PAGES:
            if not os.path.exists(p["file"]):
                continue
            slug = p["file"].replace("/", "_").replace("\\", "_")[:-5]
            for name, size in SIZES.items():
                dest = os.path.abspath(os.path.join(outdir, "%s.%s.png" % (slug, name)))
                subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                                "--force-device-scale-factor=1", "--window-size=" + size,
                                "--force-prefers-reduced-motion",
                                "--virtual-time-budget=20000",
                                "--user-data-dir=" + profile_dir,
                                "--disk-cache-dir=" + profile_dir + "\\cache",
                                "--screenshot=" + dest, "%s/%s" % (BASE, p["file"])],
                               check=False, capture_output=True, timeout=120)
            print("shot", slug)
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)


if __name__ == "__main__":
    shoot(sys.argv[1])
