#!/usr/bin/env python3
"""
Alex Savage — Cover Variant Generator
Generates store-ready cover variants from a master cover image.

Usage:
    python3 gen_covers.py <input.jpg>                 # single file
    python3 gen_covers.py <folder/>                   # all images in folder
    python3 gen_covers.py <input.jpg> -o <out_dir>    # custom output location

Outputs (one folder per input, named {basename}-variants/):
    ebook.jpg       1600×2560   Amazon / Kobo standard
    apple.jpg       1400×2100   Apple Books
    audible.jpg     2400×2400   Audible (cover padded on brand primary-deep)
    thumb-1200.jpg  1200×1800   Web hero / og card source
    thumb-600.jpg     600×900   Web medium / blog
    thumb-300.jpg     300×450   Web thumbnail / store grid

Requires: Pillow  (install: pip install Pillow --break-system-packages)
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

# ─── Brand ────────────────────────────────────────────────────────────────
# Single source of truth for colors used by this script. Mirror of
# BRAND_FOUNDATION.md — update both together if anything changes.
BRAND_PRIMARY_DEEP = (22, 12, 36)   # #160C24

# ─── Output specs ─────────────────────────────────────────────────────────
# Each variant: name, target dimensions, fit mode, JPEG quality.
#   "resize" = direct resize (preserves aspect ratio matching input)
#   "pad"    = fit inside target, pad rest with BRAND_PRIMARY_DEEP
#
# Add/remove variants here. Names become filenames.
VARIANTS = [
    {"name": "ebook",      "size": (1600, 2560), "mode": "resize", "quality": 92},
    {"name": "apple",      "size": (1400, 2100), "mode": "resize", "quality": 92},
    {"name": "audible",    "size": (2400, 2400), "mode": "pad",    "quality": 92},
    {"name": "thumb-1200", "size": (1200, 1800), "mode": "resize", "quality": 90},
    {"name": "thumb-600",  "size": (600, 900),   "mode": "resize", "quality": 88},
    {"name": "thumb-300",  "size": (300, 450),   "mode": "resize", "quality": 85},
]

VALID_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def resize_to(src: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """High-quality resize. Stretches if aspect ratios don't match — fine
    when source is already at the cover ratio (1:1.6)."""
    return src.resize((target_w, target_h), Image.LANCZOS)


def pad_to(src: Image.Image, target_w: int, target_h: int, bg=(0, 0, 0)) -> Image.Image:
    """Fit src inside target preserving aspect ratio, pad with bg."""
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_w = target_w
        new_h = round(target_w / src_ratio)
    else:
        new_h = target_h
        new_w = round(target_h * src_ratio)

    resized = src.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGB", (target_w, target_h), bg)
    canvas.paste(resized, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return canvas


def process_file(input_path: Path, output_dir: Path) -> int:
    """Generate all variants for one cover file. Returns count generated."""
    base = input_path.stem
    out = output_dir / f"{base}-variants"
    out.mkdir(parents=True, exist_ok=True)

    print(f"\n  {input_path.name}")

    try:
        src = Image.open(input_path).convert("RGB")
    except Exception as e:
        print(f"    ✗ Skipped (could not open): {e}")
        return 0

    print(f"    source: {src.width}×{src.height}")

    count = 0
    for v in VARIANTS:
        w, h = v["size"]
        if v["mode"] == "resize":
            img = resize_to(src, w, h)
        elif v["mode"] == "pad":
            img = pad_to(src, w, h, BRAND_PRIMARY_DEEP)
        else:
            print(f"    ✗ Unknown mode '{v['mode']}' — skipping {v['name']}")
            continue

        out_path = out / f"{v['name']}.jpg"
        img.save(out_path, "JPEG", quality=v["quality"], optimize=True, progressive=True)
        print(f"    ✓ {v['name']:12s} {w}×{h}")
        count += 1

    print(f"    → {out}/")
    return count


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Cover Variant Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Edit VARIANTS list at the top of this file to add/remove sizes.",
    )
    parser.add_argument("input", type=Path,
                        help="Cover image file, or folder of cover images")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output directory (default: same dir as input)")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Error: '{args.input}' does not exist")

    if args.input.is_file():
        files = [args.input]
        default_out = args.input.parent
    else:
        files = sorted(p for p in args.input.iterdir()
                       if p.is_file() and p.suffix.lower() in VALID_EXTS)
        default_out = args.input

    output_dir = args.output or default_out
    output_dir.mkdir(parents=True, exist_ok=True)

    if not files:
        sys.exit(f"Error: no image files found in '{args.input}'")

    print(f"Alex Savage — Cover Variant Generator")
    print(f"Processing {len(files)} file(s) → {output_dir}")

    total = 0
    for f in files:
        total += process_file(f, output_dir)

    print(f"\nDone. {total} variants generated from {len(files)} cover(s).")


if __name__ == "__main__":
    main()
