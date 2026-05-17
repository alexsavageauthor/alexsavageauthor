#!/usr/bin/env python3
"""
Alex Savage — Portrait Social Variants
Takes your author portrait and produces profile-photo sizes for every
platform you upload to. Profile pictures only — banners deliberately
omitted because tall portraits don't crop into wide banners well.

Usage:
    python3 gen_portrait_variants.py <portrait.jpg> [-o output_dir]

Outputs (in {basename}-social/):
    amazon-author.jpg      1500×1500   Amazon Author Central profile photo
    profile-2048.jpg      2048×2048   Max-resolution master (any future need)
    profile-1024.jpg      1024×1024   High-res universal
    profile-800.jpg         800×800   Universal social profile (FB/IG/Reddit)
    profile-400.jpg         400×400   Small avatar use, mobile-optimized
    profile-180.jpg         180×180   Favicon source / website nav mark

Crop strategy:
  All outputs are square, center-cropped with upper-third bias so the
  face stays visible regardless of source dimensions. Designed for
  portrait-orientation sources where the face is in the upper portion.

Requires: Pillow  (install: pip3 install Pillow --break-system-packages)
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

# ─── Brand ────────────────────────────────────────────────────────────────
PRIMARY_DEEP = (22, 12, 36)      # #160C24
SURFACE_1    = (39, 24, 71)      # #271847
BRAND_GOLD   = (232, 183, 86)    # #E8B756

# ─── Output specs ─────────────────────────────────────────────────────────
# Profile pictures only — all squares, all face-cropped.
# Banner formats are intentionally omitted; if you want them later, add
# wide_left or tall_fit entries (the rendering modes are still defined below).
VARIANTS = [
    {"name": "amazon-author",  "size": (1500, 1500), "mode": "square_face", "quality": 94},
    {"name": "profile-2048",   "size": (2048, 2048), "mode": "square_face", "quality": 94},
    {"name": "profile-1024",   "size": (1024, 1024), "mode": "square_face", "quality": 92},
    {"name": "profile-800",    "size": (800, 800),   "mode": "square_face", "quality": 92},
    {"name": "profile-400",    "size": (400, 400),   "mode": "square_face", "quality": 90},
    {"name": "profile-180",    "size": (180, 180),   "mode": "square_face", "quality": 90},
]


# ─── Helpers ──────────────────────────────────────────────────────────────

def brand_bg(width: int, height: int, with_glow: bool = True) -> Image.Image:
    """Brand primary-deep background with optional radial gold glow."""
    bg = Image.new("RGB", (width, height), PRIMARY_DEEP)
    if not with_glow:
        return bg

    glow = Image.new("RGB", (width, height), PRIMARY_DEEP)
    gd = ImageDraw.Draw(glow)
    cx, cy = int(width * 0.85), int(height * 0.2)
    max_r = int(max(width, height) * 0.7)
    for r in range(max_r, 0, -max(1, max_r // 60)):
        ratio = r / max_r
        color = tuple(
            int(PRIMARY_DEEP[i] + (BRAND_GOLD[i] - PRIMARY_DEEP[i]) * (1 - ratio) * 0.12)
            for i in range(3)
        )
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=80))
    return Image.blend(bg, glow, 0.4)


def crop_square_face(src: Image.Image, target: int,
                     face_x: float = 0.5, face_y: float = 0.4,
                     zoom: float = 1.0) -> Image.Image:
    """Crop a square centered on the face, then resize to target.

    face_x, face_y: where the face center sits in the source, as a fraction
                    from top-left (0..1). Defaults assume face is horizontally
                    centered and in the upper portion (typical headshot).
    zoom:           1.0 = use full available source dimension as square side.
                    >1.0 = tighter crop, bigger face. Higher values give a
                    closer headshot but increase upscaling on small sources.

    The face is placed at 50% horizontal, 40% vertical of the output square
    (slight upper bias is more flattering than dead-center for portraits).
    """
    w, h = src.size

    # Square side from the smaller source dimension divided by zoom
    side = int(min(w, h) / zoom)
    side = max(64, min(side, min(w, h)))  # clamp to sensible bounds

    # Face position in source pixels
    face_px = face_x * w
    face_py = face_y * h

    # Where we want the face within the output square (in square pixels)
    target_face_x = side * 0.5
    target_face_y = side * 0.4

    # Compute crop window position
    left = int(face_px - target_face_x)
    top  = int(face_py - target_face_y)

    # Clamp so crop stays inside source bounds
    left = max(0, min(left, w - side))
    top  = max(0, min(top,  h - side))

    cropped = src.crop((left, top, left + side, top + side))
    return cropped.resize((target, target), Image.LANCZOS)


def render_wide_left(src: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Portrait placed on the left of a wide banner, brand-gradient on the right.
       Leaves the right ~55% of the banner clear for overlay text."""
    canvas = brand_bg(target_w, target_h)

    # Determine how big to render the portrait
    # Use full target height; portrait width is whatever maintains its aspect ratio
    src_ratio = src.width / src.height
    portrait_h = target_h
    portrait_w = int(portrait_h * src_ratio)

    # If portrait_w would take more than 50% of the banner, cap it
    max_portrait_w = int(target_w * 0.45)
    if portrait_w > max_portrait_w:
        portrait_w = max_portrait_w
        portrait_h = int(portrait_w / src_ratio)

    portrait = src.resize((portrait_w, portrait_h), Image.LANCZOS)

    # Soft right-edge fade so the portrait blends into the brand gradient
    # rather than ending in a hard line
    portrait_rgba = portrait.convert("RGBA")
    mask = Image.new("L", (portrait_w, portrait_h), 255)
    md = ImageDraw.Draw(mask)
    fade_w = int(portrait_w * 0.25)
    for x in range(fade_w):
        alpha = int(255 * (1 - x / fade_w))
        md.line([(portrait_w - fade_w + x, 0), (portrait_w - fade_w + x, portrait_h)],
                fill=alpha)

    # Paste portrait on the left, vertically centered
    paste_x = 0
    paste_y = (target_h - portrait_h) // 2
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.paste(portrait_rgba, (paste_x, paste_y), mask)
    return canvas_rgba.convert("RGB")


def render_tall_fit(src: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Fit source to target width, pad top/bottom with brand-gradient if needed."""
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h

    if src_ratio >= target_ratio:
        # Source wider than target ratio — fit to width, will be shorter
        new_w = target_w
        new_h = int(target_w / src_ratio)
    else:
        # Source taller than target ratio — fit to height, crop sides
        new_h = target_h
        new_w = int(target_h * src_ratio)

    resized = src.resize((new_w, new_h), Image.LANCZOS)

    if new_w == target_w and new_h == target_h:
        return resized

    canvas = brand_bg(target_w, target_h)
    # If source is wider than target, we need to crop. If taller, center horizontally.
    if new_w > target_w:
        left = (new_w - target_w) // 2
        resized = resized.crop((left, 0, left + target_w, new_h))
        new_w = target_w
        paste_x = 0
    else:
        paste_x = (target_w - new_w) // 2

    # Vertically center with slight upward bias (face visible)
    if new_h < target_h:
        # Bias upward: place at 35% from top instead of 50%
        paste_y = int((target_h - new_h) * 0.35)
    else:
        paste_y = 0
        # Need to crop the height
        top = int((new_h - target_h) * 0.2)
        resized = resized.crop((0, top, new_w, top + target_h))

    canvas.paste(resized, (paste_x, paste_y))
    return canvas


def process(input_path: Path, output_dir: Path,
            face_x: float, face_y: float, zoom: float) -> None:
    base = input_path.stem
    out = output_dir / f"{base}-social"
    out.mkdir(parents=True, exist_ok=True)

    print(f"\n  {input_path.name}")
    src = Image.open(input_path).convert("RGB")
    print(f"    source: {src.width}×{src.height}")
    print(f"    face position: ({face_x:.2f}, {face_y:.2f})   zoom: {zoom}")

    for v in VARIANTS:
        w, h = v["size"]
        mode = v["mode"]
        if mode == "square_face":
            img = crop_square_face(src, w, face_x=face_x, face_y=face_y, zoom=zoom)
        elif mode == "wide_left":
            img = render_wide_left(src, w, h)
        elif mode == "tall_fit":
            img = render_tall_fit(src, w, h)
        else:
            print(f"    ✗ unknown mode '{mode}', skipping {v['name']}")
            continue

        out_path = out / f"{v['name']}.jpg"
        img.save(out_path, "JPEG", quality=v["quality"],
                 optimize=True, progressive=True)
        print(f"    ✓ {v['name']:18s} {w}×{h}")

    print(f"    → {out}/")


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Portrait Social Variants",
    )
    parser.add_argument("input", type=Path, help="Author portrait image")
    parser.add_argument("-o", "--output", type=Path, default=None,
                        help="Output directory (default: same as input)")
    parser.add_argument("--face-x", type=float, default=0.5,
                        help="Face center horizontal position in source (0-1, default 0.5)")
    parser.add_argument("--face-y", type=float, default=0.4,
                        help="Face center vertical position in source (0-1, default 0.4)")
    parser.add_argument("--zoom", type=float, default=1.0,
                        help="Crop tightness (1.0=full source dimension, >1.0=tighter, default 1.0)")
    args = parser.parse_args()

    if not args.input.exists():
        sys.exit(f"Error: {args.input} not found")

    output_dir = args.output or args.input.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Alex Savage — Portrait Social Variants")
    process(args.input, output_dir, args.face_x, args.face_y, args.zoom)
    print(f"\nDone.")


if __name__ == "__main__":
    main()
