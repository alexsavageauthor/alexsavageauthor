#!/usr/bin/env python3
"""
Alex Savage — Catalog Showcase Banners
Builds Facebook cover and Reddit banner combining your portrait + book covers
+ brand wordmark in a cinematic cascade layout.

Usage:
    python3 gen_banners.py \
        --portrait <portrait.jpg> \
        --covers <covers_folder_or_files...> \
        [--output <dir>]

Examples:
    # Auto-grab all covers from the assets folder, glob style
    python3 gen_banners.py \
        --portrait ../../assets/alex-savage-portrait.jpg \
        --covers ../../assets/covers/ua1.jpg \
                 ../../assets/covers/ua2.jpg \
                 ../../assets/covers/ua3.jpg \
                 ../../assets/covers/ua4.jpg \
                 ../../assets/covers/wa1.jpg \
                 ../../assets/covers/wa2.jpg \
        -o ../../assets/

    # Or pass a directory and it grabs all .jpgs sorted alphabetically
    python3 gen_banners.py \
        --portrait ../../assets/alex-savage-portrait.jpg \
        --covers-dir ../../assets/covers/ \
        -o ../../assets/

Outputs (in alex-savage-banners/):
    fb-cover.jpg          1640×624   Facebook cover photo
    reddit-banner.jpg     1280×384   Reddit profile banner

Requires: Pillow  (install: pip3 install Pillow --break-system-packages)
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Brand ────────────────────────────────────────────────────────────────
PRIMARY_DEEP = (22, 12, 36)
SURFACE_1    = (39, 24, 71)
BRAND_GOLD   = (232, 183, 86)
BRAND_CORAL  = (255, 126, 148)
BRAND_CREAM  = (245, 239, 230)

# ─── Fonts ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FONT_DIR   = SCRIPT_DIR.parent / "fonts"
FONT_DISPLAY = FONT_DIR / "Fraunces-VF.ttf"
FONT_BODY    = FONT_DIR / "Inter-VF.ttf"

# ─── Output specs ─────────────────────────────────────────────────────────
BANNERS = [
    {"name": "fb-cover",      "size": (1640, 624), "portrait_w_pct": 0.28},
    {"name": "reddit-banner", "size": (1280, 384), "portrait_w_pct": 0.22},
    {"name": "patreon-cover", "size": (2500, 1000), "portrait_w_pct": 0.25},
]


# ─── Helpers ──────────────────────────────────────────────────────────────

def load_display(size: int, variant: str = "SemiBold"):
    f = ImageFont.truetype(str(FONT_DISPLAY), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def load_body(size: int, variant: str = "Medium"):
    f = ImageFont.truetype(str(FONT_BODY), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def brand_bg(width: int, height: int) -> Image.Image:
    """Deep purple gradient with subtle radial gold glow in upper-right."""
    bg = Image.new("RGB", (width, height), PRIMARY_DEEP)
    glow = Image.new("RGB", (width, height), PRIMARY_DEEP)
    gd = ImageDraw.Draw(glow)
    cx, cy = int(width * 0.78), int(height * 0.15)
    max_r = int(max(width, height) * 0.9)
    for r in range(max_r, 0, -max(1, max_r // 80)):
        ratio = r / max_r
        color = tuple(
            int(PRIMARY_DEEP[i] + (BRAND_GOLD[i] - PRIMARY_DEEP[i]) * (1 - ratio) * 0.16)
            for i in range(3)
        )
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=80))
    bg = Image.blend(bg, glow, 0.45)

    # Add a darker vignette at the bottom-left for portrait area depth
    vignette = Image.new("RGB", (width, height), (10, 6, 18))
    mask = Image.new("L", (width, height), 0)
    md = ImageDraw.Draw(mask)
    cx2, cy2 = int(width * 0.1), int(height * 0.7)
    max_r2 = int(max(width, height) * 0.5)
    for r in range(max_r2, 0, -max(1, max_r2 // 40)):
        ratio = r / max_r2
        alpha = int(120 * (1 - ratio) ** 1.5)
        md.ellipse((cx2 - r, cy2 - r, cx2 + r, cy2 + r), fill=alpha)
    return Image.composite(vignette, bg, mask)


def fit_portrait(src: Image.Image, target_w: int, target_h: int,
                 face_x: float = 0.62, face_y: float = 0.38) -> Image.Image:
    """Crop portrait to target dimensions, biasing toward the face."""
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        # Source wider — crop sides, keep face centered horizontally
        new_w = int(src.height * target_ratio)
        left = int(src.width * face_x - new_w / 2)
        left = max(0, min(left, src.width - new_w))
        src = src.crop((left, 0, left + new_w, src.height))
    else:
        # Source taller — crop top/bottom, keep face in upper portion
        new_h = int(src.width / target_ratio)
        top = int(src.height * face_y - new_h * 0.4)
        top = max(0, min(top, src.height - new_h))
        src = src.crop((0, top, src.width, top + new_h))
    return src.resize((target_w, target_h), Image.LANCZOS)


def apply_right_fade(img: Image.Image, fade_pct: float = 0.45) -> Image.Image:
    """Apply a transparency fade on the right edge of an image."""
    w, h = img.size
    rgba = img.convert("RGBA")
    mask = Image.new("L", (w, h), 255)
    md = ImageDraw.Draw(mask)
    fade_start = int(w * (1 - fade_pct))
    fade_w = w - fade_start
    for x in range(fade_w):
        alpha = int(255 * (1 - x / fade_w) ** 1.3)
        md.line([(fade_start + x, 0), (fade_start + x, h)], fill=alpha)
    rgba.putalpha(mask)
    return rgba


def make_cover_with_shadow(cover_path: Path, target_h: int,
                           tilt_angle: float = 0.0) -> Image.Image:
    """Load a cover, resize to height, add drop shadow, optional tilt."""
    cover = Image.open(cover_path).convert("RGB")
    cover_ratio = cover.width / cover.height
    target_w = int(target_h * cover_ratio)
    cover = cover.resize((target_w, target_h), Image.LANCZOS)

    # Subtle border (cream, 1px) so it pops against dark background
    bordered = Image.new("RGB",
                         (cover.width + 2, cover.height + 2),
                         (245, 239, 230))
    bordered.paste(cover, (1, 1))

    cover_rgba = bordered.convert("RGBA")

    # Drop shadow
    shadow_pad = 24
    shadow = Image.new("RGBA",
                       (cover_rgba.width + shadow_pad * 2,
                        cover_rgba.height + shadow_pad * 2),
                       (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle(
        (shadow_pad, shadow_pad + 8,
         shadow_pad + cover_rgba.width, shadow_pad + cover_rgba.height + 8),
        fill=(0, 0, 0, 180),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))

    # Composite cover onto shadow
    composed = shadow.copy()
    composed.alpha_composite(cover_rgba, (shadow_pad, shadow_pad))

    # Tilt if requested
    if abs(tilt_angle) > 0.01:
        composed = composed.rotate(tilt_angle, resample=Image.BICUBIC,
                                   expand=True)
    return composed


def scatter_embers(img: Image.Image, count: int = 14) -> Image.Image:
    """Scatter a few soft gold sparks across the upper portion of the image."""
    import random
    random.seed(42)  # deterministic
    w, h = img.size
    out = img.convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for _ in range(count):
        x = random.randint(int(w * 0.15), int(w * 0.95))
        y = random.randint(int(h * 0.05), int(h * 0.55))
        r = random.choice([2, 3, 3, 4, 5])
        opacity = random.randint(140, 220)
        ld.ellipse((x - r, y - r, x + r, y + r),
                   fill=BRAND_GOLD + (opacity,))
        # Soft glow
        ld.ellipse((x - r * 3, y - r * 3, x + r * 3, y + r * 3),
                   fill=BRAND_GOLD + (opacity // 6,))
    layer = layer.filter(ImageFilter.GaussianBlur(1.5))
    out.alpha_composite(layer)
    return out.convert("RGB")


def render_banner(spec, portrait_path: Path, cover_paths: list[Path]) -> Image.Image:
    W, H = spec["size"]
    bg = brand_bg(W, H).convert("RGBA")

    # — Portrait on left, full-height, fading to the right —
    portrait_w = int(W * spec["portrait_w_pct"])
    portrait_h = H
    portrait_src = Image.open(portrait_path).convert("RGB")
    portrait = fit_portrait(portrait_src, portrait_w, portrait_h)
    portrait_faded = apply_right_fade(portrait, fade_pct=0.45)
    bg.alpha_composite(portrait_faded, (0, 0))

    # — Covers cascading on the right —
    n_covers = len(cover_paths)
    if n_covers == 0:
        # No covers, leave space empty
        pass
    else:
        # Reserve right margin for wordmark space so covers don't crowd it
        wordmark_reserve = int(W * 0.10)  # ~10% of width kept clear top-right

        cover_area_left  = int(portrait_w * 0.9)
        cover_area_right = W - wordmark_reserve
        cover_area_w = cover_area_right - cover_area_left

        # Cover height: 78% of banner height (room for shadow + tilt expansion)
        cover_h = int(H * 0.78)
        cover_w_approx = int(cover_h / 1.6)

        # Account for tilt expansion — tilted covers are wider than upright ones
        max_tilt = 3  # degrees
        import math
        tilt_expansion = int(cover_h * math.sin(math.radians(max_tilt)))
        effective_cover_w = cover_w_approx + tilt_expansion

        # Step (distance between cover left edges) — overlap so all fit
        if n_covers > 1:
            # Last cover's left edge = cover_area_left + (n-1)*step
            # Last cover's right edge = that + effective_cover_w
            # Constraint: last right edge ≤ cover_area_right
            max_last_left = cover_area_right - effective_cover_w
            step = (max_last_left - cover_area_left) // (n_covers - 1)
            step = max(step, int(cover_w_approx * 0.45))  # min 45% non-overlap
        else:
            step = 0

        # Alternating gentle tilts
        tilts = [-3, 2, -2, 3, -3, 2, -2, 3][:n_covers]

        cover_y_center = H // 2

        for i, cover_path in enumerate(cover_paths):
            tilted = make_cover_with_shadow(cover_path, cover_h,
                                            tilt_angle=tilts[i])
            x = cover_area_left + i * step
            y = cover_y_center - tilted.height // 2
            bg.alpha_composite(tilted, (x, y))

    bg_rgb = bg.convert("RGB")

    # — Gold embers across upper area —
    bg_rgb = scatter_embers(bg_rgb, count=int(W * H / 70000))

    # — Wordmark + tagline in top-LEFT, over the dark purple sky portion
    #   of the portrait. No cover ever reaches this area, so we get
    #   guaranteed legibility without needing backplates or fades.
    draw = ImageDraw.Draw(bg_rgb)
    scale = H / 624.0

    author_size = max(30, int(40 * scale))
    tag_size    = max(16, int(18 * scale))

    author_font = load_display(author_size, variant="SemiBold")
    tag_font    = load_body(tag_size, variant="SemiBold")

    author_text = "Alex Savage"
    tag_text    = "ACTION  HAREMLIT"

    aw, ah = text_size(draw, author_text, author_font)
    tw, th = text_size(draw, tag_text, tag_font)

    left_margin = max(28, int(36 * scale))
    top_margin  = max(20, int(28 * scale))

    # — Author wordmark, left-aligned —
    author_x = left_margin
    author_y = top_margin
    draw.text((author_x, author_y), author_text,
              font=author_font, fill=BRAND_CREAM)

    # — Gold underline rule, left-aligned beneath wordmark —
    rule_y = author_y + ah + int(author_size * 0.22)
    rule_w = int(aw * 0.55)
    draw.line(
        [(author_x, rule_y), (author_x + rule_w, rule_y)],
        fill=BRAND_GOLD, width=max(2, int(2 * scale)),
    )

    # — Tagline below rule, left-aligned —
    tag_y = rule_y + int(tag_size * 0.9)
    draw.text((author_x, tag_y), tag_text,
              font=tag_font, fill=BRAND_GOLD)

    return bg_rgb


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Catalog Showcase Banners",
    )
    parser.add_argument("--portrait", type=Path, required=True,
                        help="Author portrait image")
    parser.add_argument("--covers", type=Path, nargs="*", default=[],
                        help="Specific cover image paths in display order")
    parser.add_argument("--covers-dir", type=Path, default=None,
                        help="Directory of cover images (sorted alphabetically)")
    parser.add_argument("-o", "--output", type=Path, default=Path("."),
                        help="Output directory (will create alex-savage-banners/ inside)")
    args = parser.parse_args()

    if not args.portrait.exists():
        sys.exit(f"Error: portrait '{args.portrait}' not found")

    # Resolve cover list
    covers = list(args.covers)
    if args.covers_dir:
        if not args.covers_dir.is_dir():
            sys.exit(f"Error: --covers-dir '{args.covers_dir}' is not a directory")
        covers += sorted(p for p in args.covers_dir.iterdir()
                         if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
                         and "_hi" not in p.stem
                         and "-" not in p.stem.split("_")[0]  # skip thumbnails like ua1-400
                         )

    # Dedupe while preserving order
    seen = set()
    covers = [p for p in covers if not (p in seen or seen.add(p))]

    if not covers:
        print("Warning: no covers provided. Banner will show portrait + wordmark only.")

    out = args.output / "alex-savage-banners"
    out.mkdir(parents=True, exist_ok=True)

    print(f"Alex Savage — Catalog Showcase Banners")
    print(f"Portrait: {args.portrait}")
    print(f"Covers ({len(covers)}):")
    for c in covers:
        print(f"  · {c.name}")
    print()

    for spec in BANNERS:
        img = render_banner(spec, args.portrait, covers)
        out_path = out / f"{spec['name']}.jpg"
        img.save(out_path, "JPEG", quality=92,
                 optimize=True, progressive=True)
        w, h = spec["size"]
        print(f"  ✓ {spec['name']:18s} {w}×{h}  →  {out_path}")

    print(f"\nDone.")


if __name__ == "__main__":
    main()
