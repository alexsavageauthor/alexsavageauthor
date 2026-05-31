#!/usr/bin/env python3
"""
CI validation gate for the Alex Savage static site.

Runs in GitHub Actions before every deploy. Fails the build (exit 1) on
high-confidence breakage so a bad commit never goes live:

  * a JSON-LD <script> block that doesn't parse
  * a malformed .xml file (e.g. sitemap.xml)
  * an .html file with no closing </html>

Local asset / link references that don't resolve are reported as warnings
(non-fatal) — they surface typos without blocking a deploy on a pre-existing
quirk. Run from anywhere; paths resolve relative to the repo root.
"""
import sys
import re
import json
import pathlib
import xml.dom.minidom as minidom

ROOT = pathlib.Path(__file__).resolve().parents[2]   # .github/scripts/ -> repo root

errors: list[str] = []
warnings: list[str] = []

SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "#", "data:", "//")

html_files = sorted(ROOT.glob("*.html"))

for f in html_files:
    html = f.read_text(encoding="utf-8")

    if "</html>" not in html.lower():
        errors.append(f"{f.name}: missing closing </html>")

    for i, block in enumerate(
        re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    ):
        try:
            json.loads(block)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{f.name}: invalid JSON-LD block #{i + 1}: {e}")

    # local href/src existence — warning only
    for ref in re.findall(r'(?:src|href)="([^"]+)"', html):
        if ref.startswith(SKIP_PREFIXES):
            continue
        clean = ref.split("#")[0].split("?")[0]
        if clean and not (ROOT / clean).exists():
            warnings.append(f"{f.name}: unresolved reference -> {ref}")

    # <source srcset="a.webp, b.webp 2x"> — warning only
    for srcset in re.findall(r'srcset="([^"]+)"', html):
        for part in srcset.split(","):
            part = part.strip()
            if not part:
                continue
            asset = part.split()[0].split("#")[0].split("?")[0]
            if asset.startswith(SKIP_PREFIXES):
                continue
            if asset and not (ROOT / asset).exists():
                warnings.append(f"{f.name}: unresolved srcset asset -> {asset}")

for f in sorted(ROOT.glob("*.xml")):
    try:
        minidom.parseString(f.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        errors.append(f"{f.name}: malformed XML: {e}")

if warnings:
    print(f"::group::{len(warnings)} warning(s) — non-blocking")
    for w in warnings:
        print(f"WARN  {w}")
    print("::endgroup::")

if errors:
    print(f"\n{len(errors)} error(s) — failing the build:")
    for e in errors:
        print(f"ERROR {e}")
    sys.exit(1)

print(
    f"Validation passed: {len(html_files)} HTML files checked, "
    f"all JSON-LD and XML parse"
    + (f" ({len(warnings)} warning(s))" if warnings else "")
    + "."
)
