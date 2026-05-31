#!/usr/bin/env python3
"""
Alex Savage — Patreon Tier Images
Generates landscape tier images for the Savagery & Co. Patreon, sized
1280×720 (16:9) — works well in BOTH Patreon display contexts:
  • Membership card preview (wide banner at top of each tier card)
  • Tier list thumbnail (small landscape thumb next to each tier name)

Both crops keep the character face visible because we build the image
with the face anchored in the upper-center area.

Each tier image is character art + subtle brand polish:
  • Crop source to 16:9 landscape, face-biased
  • Apply gentle brand-purple tint at the edges (atmospheric, doesn't
    obscure the character)
  • Add gold or coral vignette glow per tier
  • Tiny Savagery & Co. mark in the bottom-right corner

NO title text on the image — Patreon adds the tier name and price below.

Usage:
    python3 gen_tier_images.py [-o output_dir]

Edit the TIERS list at the bottom of this file to change source images,
accent colors, or tier names. Re-run to regenerate everything.
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Brand ────────────────────────────────────────────────────────────────
PRIMARY_DEEP = (22, 12, 36)
BRAND_GOLD   = (232, 183, 86)
BRAND_CORAL  = (255, 126, 148)
BRAND_CREAM  = (245, 239, 230)

# ─── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
BRAND_DIR   = SCRIPT_DIR.parent
ASSETS_DIR  = BRAND_DIR.parent / "assets"
FONT_DIR    = BRAND_DIR / "fonts"

FONT_IMPRINT = FONT_DIR / "Cinzel-VF.ttf"
FONT_BODY    = FONT_DIR / "Inter-VF.ttf"

# Source cards (paths to webp/jpg files in alex-savage-website root or anywhere)
WEBSITE_ROOT   = BRAND_DIR.parent.parent           # /alex-savage-website
SOURCE_VEXIA   = WEBSITE_ROOT / "6c2a640e59c04205888525f200a2c31f.jpg"   # dark purple-robe
SOURCE_REDHEAD = WEBSITE_ROOT / "96e859e8753047b493b7547aca2c19d1.webp"  # redhead library
SOURCE_CHEER   = WEBSITE_ROOT / "ffd92ff9a13b4c278fe92c71c98a43e1.webp"  # cheerleader
SOURCE_FORGE   = WEBSITE_ROOT / "83df2e561d054f7e895006b163bdd12f.webp"  # steampunk mage
SOURCE_BUBBLE  = WEBSITE_ROOT / "efebea30ffdb447a87d0571d64caadc4.webp"  # bubblegum
SOURCE_BLONDE  = WEBSITE_ROOT / "0193f898c1f346fd8b82539dac023927.webp"  # blonde nightgown

# ─── Output spec ──────────────────────────────────────────────────────────
TIER_SIZE = (1280, 720)  # 16:9 landscape — Patreon's safe upload size


# ─── Helpers ──────────────────────────────────────────────────────────────

def load_imprint(size: int, variant: str = "Bold"):
    f = ImageFont.truetype(str(FONT_IMPRINT), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def fit_landscape_face(src: Image.Image, target_w: int, target_h: int,
                       face_y_pct: float = 0.32) -> Image.Image:
    """Crop source to target landscape aspect with face in the upper area.

    face_y_pct: where the face is in the source vertically (0-1 from top).
                For most character art portraits, face sits at 0.25-0.40.

    Strategy:
      - If source is taller than target ratio, take a horizontal slice
        centered on the face. The face ends up at ~32% of the slice (upper
        third) so both the full banner crop AND the small thumbnail crop
        preserve it.
      - If source is wider, crop sides centered.
    """
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h  # 1.78 for 16:9

    if src_ratio < target_ratio:
        # Source is taller — take a horizontal slice
        new_h = int(src.width / target_ratio)
        face_px = int(src.height * face_y_pct)
        # Want face at 32% of the crop
        top = face_px - int(new_h * 0.32)
        top = max(0, min(top, src.height - new_h))
        cropped = src.crop((0, top, src.width, top + new_h))
    else:
        # Source is wider — center crop horizontally
        new_w = int(src.height * target_ratio)
        left = (src.width - new_w) // 2
        cropped = src.crop((left, 0, left + new_w, src.height))

    return cropped.resize((target_w, target_h), Image.LANCZOS)


def add_brand_vignette(img: Image.Image, accent: tuple, intensity: float = 0.55) -> Image.Image:
    """Add a soft vignette with brand accent at the edges. Subtle —
    enhances the character art without obscuring it."""
    w, h = img.size
    rgba = img.convert("RGBA")
    vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    vd = ImageDraw.Draw(vignette)

    # Dark edge vignette (brand primary-deep)
    edge = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    cx, cy = w // 2, int(h * 0.45)
    max_r = int(max(w, h) * 0.75)
    for r in range(max_r, 0, -8):
        ratio = r / max_r
        alpha = int(200 * (ratio ** 2.5) * intensity)
        ed.ellipse((cx - r, cy - r, cx + r, cy + r),
                   fill=PRIMARY_DEEP + (alpha,))
    edge = edge.filter(ImageFilter.GaussianBlur(40))

    # Subtle accent glow in upper-right corner
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gcx, gcy = int(w * 0.85), int(h * 0.15)
    g_max_r = int(max(w, h) * 0.45)
    for r in range(g_max_r, 0, -8):
        ratio = r / g_max_r
        alpha = int(50 * (1 - ratio) ** 1.5)
        gd.ellipse((gcx - r, gcy - r, gcx + r, gcy + r),
                   fill=accent + (alpha,))
    glow = glow.filter(ImageFilter.GaussianBlur(30))

    rgba.alpha_composite(edge)
    rgba.alpha_composite(glow)
    return rgba.convert("RGB")


def add_imprint_corner_mark(img: Image.Image) -> Image.Image:
    """Tiny SAVAGERY & CO. wordmark in the bottom-right corner — quiet brand
    signature without competing with the character art."""
    w, h = img.size
    rgba = img.convert("RGBA")
    draw = ImageDraw.Draw(rgba)

    main_font = load_imprint(int(h * 0.022), variant="Bold")
    sub_font  = load_imprint(int(h * 0.014), variant="Regular")

    main_text = "SAVAGERY"
    sub_text  = "& CO."

    main_spacing = int(h * 0.005)
    main_total = sum(text_size(draw, ch, main_font)[0] for ch in main_text) + \
                 main_spacing * (len(main_text) - 1)
    sub_spacing = int(h * 0.008)
    sub_total = sum(text_size(draw, ch, sub_font)[0] for ch in sub_text) + \
                sub_spacing * (len(sub_text) - 1)

    margin_x = int(w * 0.022)
    margin_y = int(h * 0.025)

    main_x = w - margin_x - main_total
    main_y = h - margin_y - int(h * 0.04)

    # Build a soft dark backplate so the mark is legible on bright character art
    plate_pad_x = int(h * 0.022)
    plate_pad_y = int(h * 0.015)
    plate = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plate)
    pd.rectangle(
        (main_x - plate_pad_x,
         main_y - plate_pad_y,
         w,
         h),
        fill=(10, 6, 18, 120),
    )
    plate = plate.filter(ImageFilter.GaussianBlur(8))
    rgba.alpha_composite(plate)
    draw = ImageDraw.Draw(rgba)

    # Render with per-char spacing
    cursor = main_x
    for ch in main_text:
        draw.text((cursor, main_y), ch, font=main_font,
                  fill=BRAND_CREAM + (220,))
        cursor += text_size(draw, ch, main_font)[0] + main_spacing

    sub_y = main_y + text_size(draw, main_text, main_font)[1] + int(h * 0.005)
    cursor = w - margin_x - sub_total
    for ch in sub_text:
        draw.text((cursor, sub_y), ch, font=sub_font,
                  fill=BRAND_GOLD + (220,))
        cursor += text_size(draw, ch, sub_font)[0] + sub_spacing

    return rgba.convert("RGB")


# ─── Tier rendering ───────────────────────────────────────────────────────

def render_tier(spec: dict) -> Image.Image:
    src_path = Path(spec["source"])
    if not src_path.exists():
        sys.exit(f"Error: source image not found: {src_path}")

    src = Image.open(src_path).convert("RGB")
    W, H = TIER_SIZE
    face_y = spec.get("face_y", 0.32)
    accent = spec.get("accent", BRAND_GOLD)
    intensity = spec.get("vignette_intensity", 0.55)

    # Crop to landscape, face-biased
    img = fit_landscape_face(src, W, H, face_y_pct=face_y)
    # Brand vignette + accent glow
    img = add_brand_vignette(img, accent, intensity=intensity)
    # Tiny Savagery & Co. corner mark
    img = add_imprint_corner_mark(img)

    return img


# ─── Tier configuration ───────────────────────────────────────────────────
# Edit source paths, accent colors, face_y per tier.
# face_y = where the face sits in the source (0=top, 1=bottom).
# Adjust this per source so the face lands at upper-third of the tier image.

TIERS = [
    {
        "name":   "initiate",
        "source": SOURCE_CHEER,
        "accent": BRAND_CORAL,
        "face_y": 0.30,
        "vignette_intensity": 0.45,
    },
    {
        "name":   "acolyte",
        "source": SOURCE_BUBBLE,
        "accent": BRAND_CORAL,
        "face_y": 0.20,
        "vignette_intensity": 0.45,
    },
    {
        "name":   "adept",
        "source": SOURCE_REDHEAD,
        "accent": BRAND_GOLD,
        "face_y": 0.18,
        "vignette_intensity": 0.55,
    },
    {
        "name":   "magus",
        "source": SOURCE_FORGE,
        "accent": BRAND_GOLD,
        "face_y": 0.30,
        "vignette_intensity": 0.55,
    },
    {
        "name":   "warlord",
        "source": SOURCE_VEXIA,
        "accent": BRAND_GOLD,
        "face_y": 0.32,
        "vignette_intensity": 0.60,
    },
]


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Patreon Tier Images",
    )
    parser.add_argument("-o", "--output", type=Path, default=ASSETS_DIR,
                        help="Output directory (default: assets/)")
    args = parser.parse_args()

    out = args.output / "patreon-tiers"
    out.mkdir(parents=True, exist_ok=True)

    print("Alex Savage — Patreon Tier Images")
    print(f"Generating {len(TIERS)} tier images at {TIER_SIZE[0]}×{TIER_SIZE[1]} → {out}/\n")

    for tier in TIERS:
        img = render_tier(tier)
        out_path = out / f"tier-{tier['name']}.jpg"
        img.save(out_path, "JPEG", quality=92,
                 optimize=True, progressive=True)
        print(f"  ✓ {tier['name']:10s} → {out_path.name}")

    print(f"\nDone. {len(TIERS)} tier images generated.")


if __name__ == "__main__":
    main()
