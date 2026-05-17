#!/usr/bin/env python3
"""
Alex Savage — Series Cover Frame
Applies the locked brand frame to finished cover artwork.

What it adds (in order from top):
  • Series color anchor rule along the top edge (gold for UA, coral for WA)
  • Author wordmark "Alex Savage" in Fraunces, centered just below the rule
  • Savagery & Co. imprint mark in the bottom-right corner, subtle

What it does NOT do:
  • Render the book title — that's hand-tuned typographic work owned by
    your cover designer, not by a script. Deliver artwork with the title
    already painted in.

Usage:
    python3 gen_series_cover.py <cover.jpg> --series ua
    python3 gen_series_cover.py <cover.jpg> --series wa
    python3 gen_series_cover.py <cover.jpg> --series ua --variants    # also outputs store sizes

Requires: Pillow  (install: pip3 install Pillow --break-system-packages)
"""

import argparse
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Brand ────────────────────────────────────────────────────────────────
BRAND_GOLD   = (232, 183, 86)    # #E8B756
BRAND_CORAL  = (255, 126, 148)   # #FF7E94
BRAND_CREAM  = (245, 239, 230)   # #F5EFE6
COVER_BAND   = (26, 15, 44)      # #1A0F2C (overlay tone)

# ─── Series → anchor color ────────────────────────────────────────────────
SERIES_ANCHORS = {
    "ua": BRAND_GOLD,     # The Ravenwick Chronicle (Undercover Archmage)
    "wa": BRAND_CORAL,    # The WarMage of Arkley
    # Add more series here as the catalog grows.
}

# ─── Fonts ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FONT_DIR   = SCRIPT_DIR.parent / "fonts"
FONT_DISPLAY = FONT_DIR / "Fraunces-VF.ttf"

# ─── Imprint mark ─────────────────────────────────────────────────────────
IMPRINT_SVG = SCRIPT_DIR.parent / "alex-savage-mark-simple.svg"   # fallback
# Best path: use the savagery-co-light.svg, but that's SVG and Pillow can't
# rasterize it natively. So we use a tiny text mark in Cinzel-style fallback.


# ─── Helpers ──────────────────────────────────────────────────────────────

def load_display(size: int, variant: str = "SemiBold"):
    f = ImageFont.truetype(str(FONT_DISPLAY), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_underline(draw, x_center, y, width, color=BRAND_GOLD, thickness=2):
    draw.line(
        [(x_center - width // 2, y), (x_center + width // 2, y)],
        fill=color, width=thickness,
    )


def make_top_overlay(width: int, height: int, scale: float,
                     anchor_color, author_text: str) -> Image.Image:
    """Build the top brand frame as a transparent overlay.
       Returns RGBA image the same size as the cover."""
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # — Series color anchor rule (top edge) —
    rule_h = max(4, int(8 * scale))
    draw.rectangle((0, 0, width, rule_h), fill=anchor_color + (255,))

    # — Soft fade band so the author wordmark sits cleanly on dark covers —
    band_h = int(140 * scale)
    fade = Image.new("RGBA", (width, band_h), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fade)
    for y in range(band_h):
        alpha = int(220 * (1 - y / band_h) ** 1.6)  # smooth fade out
        fd.line([(0, y), (width, y)], fill=COVER_BAND + (alpha,))
    overlay.alpha_composite(fade, (0, rule_h))

    # — Author wordmark, Fraunces SemiBold, cream —
    font_size = int(72 * scale)
    afont = load_display(font_size)
    aw, ah = text_size(draw, author_text, afont)
    author_y = rule_h + int(34 * scale)
    draw.text(((width - aw) // 2, author_y),
              author_text, font=afont, fill=BRAND_CREAM + (255,))

    # — Thin gold underline rule beneath the wordmark —
    draw_underline(draw, width // 2, author_y + ah + int(10 * scale),
                   int(aw * 0.55), color=BRAND_GOLD, thickness=max(2, int(2 * scale)))

    return overlay


def make_imprint_mark(scale: float) -> Image.Image:
    """Small SAVAGERY & CO mark for bottom-right corner.
       Returns RGBA image sized to fit naturally on a cover."""
    mark_w = int(180 * scale)
    mark_h = int(36 * scale)
    img = Image.new("RGBA", (mark_w, mark_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    main_font = load_display(int(18 * scale), variant="SemiBold")
    sub_font  = load_display(int(10 * scale), variant="Regular")

    # Render at 70% opacity by drawing on a separate layer then blending
    text_color = BRAND_CREAM + (180,)
    accent     = BRAND_GOLD + (220,)

    main = "SAVAGERY"
    sub  = "& CO."
    mw, mh = text_size(d, main, main_font)
    sw, sh = text_size(d, sub, sub_font)

    d.text(((mark_w - mw) // 2, 0), main, font=main_font, fill=text_color)
    d.text(((mark_w - sw) // 2, mh + int(2 * scale)),
           sub, font=sub_font, fill=accent)

    return img


# ─── Main ─────────────────────────────────────────────────────────────────

def apply_frame(input_path: Path, series: str, output_path: Path,
                author: str = "Alex Savage") -> None:
    anchor_color = SERIES_ANCHORS.get(series.lower())
    if not anchor_color:
        sys.exit(f"Error: unknown series '{series}'. "
                 f"Known: {', '.join(SERIES_ANCHORS.keys())}")

    src = Image.open(input_path).convert("RGBA")
    width, height = src.size

    # Scale all dimensions from 1600px-wide reference cover
    scale = width / 1600.0

    # Build and composite the top overlay
    top_overlay = make_top_overlay(width, height, scale, anchor_color, author)
    src.alpha_composite(top_overlay)

    # Bottom-right imprint mark
    mark = make_imprint_mark(scale)
    margin = int(28 * scale)
    mark_x = width - mark.width - margin
    mark_y = height - mark.height - margin
    src.alpha_composite(mark, (mark_x, mark_y))

    # Save (convert to RGB to drop alpha for JPEG)
    out_img = src.convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out_img.save(output_path, "JPEG", quality=94, optimize=True, progressive=True)
    print(f"  ✓ {output_path}  ({width}×{height})")


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Series Cover Frame",
    )
    parser.add_argument("input", type=Path, help="Cover artwork image")
    parser.add_argument("--series", required=True, choices=list(SERIES_ANCHORS.keys()),
                        help=f"Which series ({'/'.join(SERIES_ANCHORS.keys())})")
    parser.add_argument("--author", default="Alex Savage", help="Author wordmark text")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output file (default: {input}-framed.jpg next to input)")
    parser.add_argument("--variants", action="store_true",
                        help="After framing, also run gen_covers.py to produce store sizes")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Error: {args.input} not found")

    output = args.output or args.input.parent / f"{args.input.stem}-framed.jpg"

    print(f"Alex Savage — Series Cover Frame")
    print(f"Series: {args.series.upper()}  ·  anchor: {SERIES_ANCHORS[args.series.lower()]}")
    print(f"Input:  {args.input}")

    apply_frame(args.input, args.series, output, args.author)

    if args.variants:
        print(f"\nRunning gen_covers.py on the framed output...")
        result = subprocess.run([
            sys.executable,
            str(SCRIPT_DIR / "gen_covers.py"),
            str(output),
        ])
        if result.returncode != 0:
            print("  ✗ Variant generation failed")
            sys.exit(1)

    print(f"\nDone.")


if __name__ == "__main__":
    main()
