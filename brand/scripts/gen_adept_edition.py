#!/usr/bin/env python3
"""
Alex Savage — Adept Edition Badge
Takes a cover image and stamps an "ADEPT EDITION" diagonal sash in the
upper-right corner, signalling the Patreon-tier extended/uncut version.

The sash is brand-gold (#E8B756), Fraunces SemiBold lettering, sits at
~30° rotation so it doesn't conflict with the existing title typography
along the bottom or the author wordmark along the top.

Usage:
    python3 gen_adept_edition.py <cover.jpg> [-o <output.jpg>] \
        [--sub "Extended cut · Patreon"]

Default output: ../../assets/adept-editions/{basename}-adept.jpg

Requires: Pillow.
"""

import argparse
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR  = Path(__file__).resolve().parent
BRAND_DIR   = SCRIPT_DIR.parent
ASSETS_DIR  = BRAND_DIR.parent / "assets"
FONT_DIR    = BRAND_DIR / "fonts"

FONT_DISPLAY = FONT_DIR / "Fraunces-VF.ttf"
FONT_BODY    = FONT_DIR / "Inter-VF.ttf"

# Brand
BRAND_GOLD       = (232, 183, 86)
BRAND_GOLD_LIGHT = (244, 210, 122)
BRAND_GOLD_DEEP  = (180, 138, 48)
BRAND_CREAM      = (245, 239, 230)
PRIMARY_DEEP     = (22, 12, 36)


def load_display(size: int, variant: str = "Bold"):
    f = ImageFont.truetype(str(FONT_DISPLAY), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def load_body(size: int, variant: str = "SemiBold"):
    f = ImageFont.truetype(str(FONT_BODY), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def render_diagonal_sash(cover_w: int, cover_h: int,
                         main_text: str = "ADEPT EDITION",
                         sub_text: str = "EXTENDED CUT · PATREON",
                         angle_deg: float = -30.0) -> Image.Image:
    """Build a transparent overlay the size of the cover with a diagonal
    gold sash in the upper-right corner carrying ADEPT EDITION text."""
    # Sash dimensions sized relative to cover width
    sash_length = int(cover_w * 1.1)   # extends past the corner so it bleeds
    sash_thickness = int(cover_w * 0.13)
    # Font sizes scale with sash thickness
    main_size = int(sash_thickness * 0.42)
    sub_size  = int(sash_thickness * 0.18)

    # 1. Build the sash horizontally first (text upright), then rotate it.
    sash_w = sash_length
    sash_h = sash_thickness
    sash = Image.new("RGBA", (sash_w, sash_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sash)

    # Vertical gradient fill (light at top, deeper at bottom)
    for y in range(sash_h):
        ratio = y / sash_h
        # interpolate light → gold → deep
        if ratio < 0.5:
            t = ratio / 0.5
            color = tuple(
                int(BRAND_GOLD_LIGHT[i] + (BRAND_GOLD[i] - BRAND_GOLD_LIGHT[i]) * t)
                for i in range(3)
            )
        else:
            t = (ratio - 0.5) / 0.5
            color = tuple(
                int(BRAND_GOLD[i] + (BRAND_GOLD_DEEP[i] - BRAND_GOLD[i]) * t)
                for i in range(3)
            )
        sd.line([(0, y), (sash_w, y)], fill=color + (255,))

    # Inner rule lines (cream hairlines) — top and bottom edges of sash
    rule_inset = int(sash_h * 0.10)
    rule_thickness = max(1, int(sash_h * 0.018))
    sd.rectangle((0, rule_inset, sash_w, rule_inset + rule_thickness),
                 fill=BRAND_CREAM + (180,))
    sd.rectangle((0, sash_h - rule_inset - rule_thickness, sash_w, sash_h - rule_inset),
                 fill=BRAND_CREAM + (180,))

    # Main text — centered
    main_font = load_display(main_size, variant="Bold")
    main_spacing = int(main_size * 0.20)
    main_total_w = sum(text_size(sd, ch, main_font)[0] for ch in main_text) + \
                   main_spacing * (len(main_text) - 1)
    main_h = text_size(sd, main_text, main_font)[1]
    cursor = (sash_w - main_total_w) // 2
    main_y = int(sash_h * 0.32) - main_h // 2 + int(sash_h * 0.18)
    # Slight dark shadow for legibility
    shadow_offset = max(1, int(sash_h * 0.012))
    for ch in main_text:
        sd.text((cursor + shadow_offset, main_y + shadow_offset), ch,
                font=main_font, fill=(80, 50, 10, 180))
        sd.text((cursor, main_y), ch, font=main_font,
                fill=PRIMARY_DEEP + (255,))
        cursor += text_size(sd, ch, main_font)[0] + main_spacing

    # Sub-text — smaller, beneath main
    if sub_text:
        sub_font = load_body(sub_size, variant="SemiBold")
        sub_spacing = int(sub_size * 0.32)
        sub_total_w = sum(text_size(sd, ch, sub_font)[0] for ch in sub_text) + \
                      sub_spacing * (len(sub_text) - 1)
        sub_h = text_size(sd, sub_text, sub_font)[1]
        cursor = (sash_w - sub_total_w) // 2
        sub_y = main_y + main_h + int(sash_h * 0.08)
        for ch in sub_text:
            sd.text((cursor, sub_y), ch, font=sub_font,
                    fill=PRIMARY_DEEP + (220,))
            cursor += text_size(sd, ch, sub_font)[0] + sub_spacing

    # 2. Rotate the sash
    rotated = sash.rotate(angle_deg, resample=Image.BICUBIC, expand=True)

    # 3. Drop shadow under the sash
    shadow = Image.new("RGBA", rotated.size, (0, 0, 0, 0))
    sd2 = ImageDraw.Draw(shadow)
    # Build shadow from rotated alpha
    mask = rotated.split()[3]
    shadow.paste((0, 0, 0, 160), (0, 0), mask)
    shadow = shadow.filter(ImageFilter.GaussianBlur(int(sash_h * 0.10)))

    # 4. Build full-cover overlay and paste the rotated sash near the
    #    upper-right corner.
    overlay = Image.new("RGBA", (cover_w, cover_h), (0, 0, 0, 0))
    # The center of the sash sits about 14% of cover width from the right
    # edge and ~14% from the top
    sash_center_x = int(cover_w * 0.74)
    sash_center_y = int(cover_h * 0.10)
    paste_x = sash_center_x - rotated.width // 2
    paste_y = sash_center_y - rotated.height // 2
    shadow_offset_x = int(cover_w * 0.006)
    shadow_offset_y = int(cover_w * 0.008)
    overlay.alpha_composite(shadow, (paste_x + shadow_offset_x,
                                      paste_y + shadow_offset_y))
    overlay.alpha_composite(rotated, (paste_x, paste_y))
    return overlay


def process(cover_path: Path, output_path: Path, sub_text: str) -> None:
    cover = Image.open(cover_path).convert("RGB")
    print(f"  Source: {cover_path.name} ({cover.width}×{cover.height})")
    overlay = render_diagonal_sash(cover.width, cover.height,
                                   sub_text=sub_text)
    base = cover.convert("RGBA")
    base.alpha_composite(overlay)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(output_path, "JPEG", quality=94,
                             optimize=True, progressive=True)
    print(f"  ✓ {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Adept Edition badge",
    )
    parser.add_argument("input", type=Path, help="Source cover image")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output path (default: adept-editions/{basename}-adept.jpg)")
    parser.add_argument("--sub", default="EXTENDED CUT · PATREON",
                        help="Sub-text on the sash (set to '' to omit)")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Error: {args.input} not found")

    if args.output is None:
        out_dir = ASSETS_DIR / "adept-editions"
        args.output = out_dir / f"{args.input.stem}-adept.jpg"

    print("Alex Savage — Adept Edition Badge")
    process(args.input, args.output, args.sub)
    print("\nDone.")


if __name__ == "__main__":
    main()
