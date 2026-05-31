#!/usr/bin/env python3
"""
Alex Savage — Patreon Collection Tiles
Generates branded 1080×1080 collection tiles for the Savagery & Co. Patreon.

Each tile uses the same template — brand purple gradient background, a visual
motif in the upper area, the collection name in Fraunces SemiBold cream, a
gold or coral accent rule, and an Inter-italic descriptor below.

Edit the COLLECTIONS list at the bottom of this file to change names,
descriptors, accent colors, or motifs. Re-run to regenerate every tile in
one pass.

Usage:
    python3 gen_collection_tiles.py [-o output_dir]

Output: {output_dir}/patreon-collections/{slug}.jpg

Requires: Pillow  (install: pip3 install Pillow --break-system-packages)
"""

import argparse
import re
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Brand ────────────────────────────────────────────────────────────────
PRIMARY_DEEP = (22, 12, 36)
SURFACE_1    = (39, 24, 71)
BRAND_GOLD   = (232, 183, 86)
GOLD_SOFT    = (244, 210, 122)
BRAND_CORAL  = (255, 126, 148)
BRAND_CREAM  = (245, 239, 230)
MUTED_LAV    = (177, 162, 204)
COVER_BAND   = (26, 15, 44)

# ─── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR  = Path(__file__).resolve().parent
BRAND_DIR   = SCRIPT_DIR.parent
ASSETS_DIR  = BRAND_DIR.parent / "assets"
FONT_DIR    = BRAND_DIR / "fonts"

FONT_DISPLAY = FONT_DIR / "Fraunces-VF.ttf"
FONT_ITALIC  = FONT_DIR / "Fraunces-Italic-VF.ttf"
FONT_BODY    = FONT_DIR / "Inter-VF.ttf"
FONT_ACCENT  = FONT_DIR / "Caveat-Regular.ttf"
FONT_IMPRINT = FONT_DIR / "Cinzel-VF.ttf"   # Savagery & Co. wordmark face

PORTRAIT_PATH = ASSETS_DIR / "alex-savage-portrait.jpg"
COVERS_DIR    = ASSETS_DIR / "covers"
IMPRINT_SVG   = BRAND_DIR / "savagery-co-light.svg"  # for reference only

# Cover paths
COVER_UA1 = COVERS_DIR / "ua1_hi.jpg"
COVER_UA2 = COVERS_DIR / "ua2_hi.jpg"
COVER_UA3 = COVERS_DIR / "ua3_hi.jpg"
COVER_UA4 = COVERS_DIR / "ua4_hi.jpg"
COVER_WA1 = COVERS_DIR / "wa1_hi.jpg"
COVER_WA2 = COVERS_DIR / "wa2_hi.jpg"


# ─── Helpers ──────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s[:60].strip("-") or "tile"


def load_display(size: int, variant: str = "SemiBold"):
    f = ImageFont.truetype(str(FONT_DISPLAY), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def load_italic(size: int, variant: str = "Italic"):
    f = ImageFont.truetype(str(FONT_ITALIC), size)
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


def load_imprint(size: int, variant: str = "Bold"):
    """Cinzel — Savagery & Co. imprint face. Classical caps serif."""
    f = ImageFont.truetype(str(FONT_IMPRINT), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def brand_bg(width: int, height: int) -> Image.Image:
    """Deep purple background with radial gold glow upper-right."""
    bg = Image.new("RGB", (width, height), PRIMARY_DEEP)
    glow = Image.new("RGB", (width, height), PRIMARY_DEEP)
    gd = ImageDraw.Draw(glow)
    cx, cy = int(width * 0.85), int(height * 0.15)
    max_r = int(max(width, height) * 0.85)
    for r in range(max_r, 0, -max(1, max_r // 80)):
        ratio = r / max_r
        color = tuple(
            int(PRIMARY_DEEP[i] + (BRAND_GOLD[i] - PRIMARY_DEEP[i]) * (1 - ratio) * 0.14)
            for i in range(3)
        )
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=80))
    return Image.blend(bg, glow, 0.4)


def apply_bottom_fade(img: Image.Image, fade_h_pct: float = 0.4) -> Image.Image:
    """Darken the bottom portion of an image with a vertical gradient so
    text overlay reads cleanly. Returns RGB."""
    w, h = img.size
    rgba = img.convert("RGBA")
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    fade_start_y = int(h * (1 - fade_h_pct))
    fade_h = h - fade_start_y
    for y in range(fade_h):
        alpha = int(220 * (y / fade_h) ** 1.4)
        od.line([(0, fade_start_y + y), (w, fade_start_y + y)],
                fill=COVER_BAND + (alpha,))
    rgba.alpha_composite(overlay)
    return rgba.convert("RGB")


# ─── Motif renderers ──────────────────────────────────────────────────────

def motif_brand_only(canvas: Image.Image, motif_data) -> Image.Image:
    """Typographic motif using the Cinzel imprint wordmark + decorative rule.
    Used for collections without a natural image, like character card sets."""
    w, h = canvas.size
    rgba = canvas.convert("RGBA")
    draw = ImageDraw.Draw(rgba)

    # SAVAGERY in Cinzel, large, brand-cream, centered upper
    sav_size = int(h * 0.075)
    sav_font = load_imprint(sav_size, variant="Bold")
    sav_text = motif_data.get("upper_text", "SAVAGERY")
    sw, sh = text_size(draw, sav_text, sav_font)
    sx = (w - sw) // 2
    sy = int(h * 0.18)
    # Add letter-spacing by drawing each character individually
    spacing = int(sav_size * 0.18)
    total_w = sum(text_size(draw, ch, sav_font)[0] for ch in sav_text) + \
              spacing * (len(sav_text) - 1)
    cursor = (w - total_w) // 2
    for ch in sav_text:
        draw.text((cursor, sy), ch, font=sav_font, fill=BRAND_CREAM)
        cursor += text_size(draw, ch, sav_font)[0] + spacing

    # Decorative center ornament (dot-rule-dot-rule-dot) in gold
    orn_y = sy + sh + int(h * 0.025)
    rule_w = int(w * 0.20)
    rule_thickness = max(2, int(h * 0.003))
    cx = w // 2
    # Center dot
    draw.ellipse((cx - 4, orn_y - 4, cx + 4, orn_y + 4), fill=BRAND_GOLD)
    # Left rule + dot
    draw.line([(cx - 16, orn_y), (cx - 16 - rule_w, orn_y)],
              fill=BRAND_GOLD, width=rule_thickness)
    draw.ellipse((cx - 16 - rule_w - 4, orn_y - 4,
                  cx - 16 - rule_w + 4, orn_y + 4), fill=BRAND_GOLD)
    # Right rule + dot
    draw.line([(cx + 16, orn_y), (cx + 16 + rule_w, orn_y)],
              fill=BRAND_GOLD, width=rule_thickness)
    draw.ellipse((cx + 16 + rule_w - 4, orn_y - 4,
                  cx + 16 + rule_w + 4, orn_y + 4), fill=BRAND_GOLD)

    # "& CO." or sub-text below ornament
    sub_size = int(h * 0.035)
    sub_font = load_imprint(sub_size, variant="Regular")
    sub_text = motif_data.get("lower_text", "& CO.")
    sub_spacing = int(sub_size * 0.42)
    sub_total = sum(text_size(draw, ch, sub_font)[0] for ch in sub_text) + \
                sub_spacing * (len(sub_text) - 1)
    sub_cursor = (w - sub_total) // 2
    sub_y = orn_y + int(h * 0.018)
    for ch in sub_text:
        draw.text((sub_cursor, sub_y), ch, font=sub_font, fill=BRAND_GOLD)
        sub_cursor += text_size(draw, ch, sub_font)[0] + sub_spacing

    return rgba.convert("RGB")


def motif_portrait(canvas: Image.Image, motif_data) -> Image.Image:
    """Hooded portrait, full bleed across upper area with bottom fade.
    Preserves the source aspect ratio — crops to the target aspect first,
    keeping the face in the upper-third visual sweet spot."""
    w, h = canvas.size
    portrait = Image.open(PORTRAIT_PATH).convert("RGB")
    pw, ph = portrait.size

    # Upper area dimensions on the tile
    target_w = w
    target_h = int(h * 0.65)
    target_ratio = target_w / target_h

    # Face position in source (calibrated for this specific portrait)
    face_x_pct = motif_data.get("face_x", 0.62)
    face_y_pct = motif_data.get("face_y", 0.38)

    # Crop source to target aspect ratio
    src_ratio = pw / ph
    if src_ratio > target_ratio:
        # Source is wider — crop sides, centering on face_x
        new_w = int(ph * target_ratio)
        left = int(pw * face_x_pct - new_w / 2)
        left = max(0, min(left, pw - new_w))
        cropped = portrait.crop((left, 0, left + new_w, ph))
    else:
        # Source is taller (our case) — crop top/bottom, positioning face
        # in the upper-third of the crop
        new_h = int(pw / target_ratio)
        # Want face_y position in source to land at ~40% of the cropped region
        top = int(ph * face_y_pct - new_h * 0.4)
        top = max(0, min(top, ph - new_h))
        cropped = portrait.crop((0, top, pw, top + new_h))

    # Now scale to target dimensions (proper aspect, no stretching)
    portrait = cropped.resize((target_w, target_h), Image.LANCZOS)
    rgba = canvas.convert("RGBA")
    rgba.paste(portrait.convert("RGBA"), (0, 0))
    rgba_rgb = rgba.convert("RGB")
    return apply_bottom_fade(rgba_rgb, fade_h_pct=0.5)


def motif_single_cover(canvas: Image.Image, motif_data) -> Image.Image:
    """Single book cover, centered upper, with shadow + tilt."""
    w, h = canvas.size
    cover_path = motif_data.get("cover")
    if not cover_path or not Path(cover_path).exists():
        return motif_brand_only(canvas, motif_data)

    cover = Image.open(cover_path).convert("RGB")
    cover_h = int(h * 0.55)
    cover_w = int(cover_h / 1.6)
    cover = cover.resize((cover_w, cover_h), Image.LANCZOS)
    # Border
    bordered = Image.new("RGB", (cover_w + 2, cover_h + 2), BRAND_CREAM)
    bordered.paste(cover, (1, 1))
    cover_rgba = bordered.convert("RGBA")

    # Shadow
    pad = 30
    shadow = Image.new("RGBA",
                       (cover_rgba.width + pad * 2, cover_rgba.height + pad * 2),
                       (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle((pad, pad + 8,
                  pad + cover_rgba.width, pad + cover_rgba.height + 8),
                 fill=(0, 0, 0, 180))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    composed = shadow.copy()
    composed.alpha_composite(cover_rgba, (pad, pad))

    tilt = motif_data.get("tilt", -3)
    if abs(tilt) > 0.01:
        composed = composed.rotate(tilt, resample=Image.BICUBIC, expand=True)

    rgba = canvas.convert("RGBA")
    paste_x = (w - composed.width) // 2
    paste_y = int(h * 0.08)
    rgba.alpha_composite(composed, (paste_x, paste_y))
    return rgba.convert("RGB")


def motif_cover_stack(canvas: Image.Image, motif_data) -> Image.Image:
    """Multiple book covers in a tight fan, centered upper area.
    motif_data['orientation'] = 'horizontal' (default) or 'vertical'."""
    w, h = canvas.size
    cover_paths = motif_data.get("covers", [])
    cover_paths = [p for p in cover_paths if Path(p).exists()]
    if not cover_paths:
        return motif_brand_only(canvas, motif_data)

    orientation = motif_data.get("orientation", "horizontal")
    rgba = canvas.convert("RGBA")
    n = len(cover_paths)

    if orientation == "vertical":
        # Cards stacked vertically with horizontal offsets — premium feel
        cover_h = int(h * 0.32)
        cw = int(cover_h / 1.6)
        # Alternating horizontal offsets for natural cascade
        x_offsets = [-30, 20, -20, 30, -30, 20][:n]

        # Vertical stacking with overlap
        vstep = int(cover_h * 0.42)
        total_h = (n - 1) * vstep + cover_h
        start_y = int(h * 0.06)
        center_x = w // 2

        for i, path in enumerate(cover_paths):
            cover = Image.open(path).convert("RGB")
            cover = cover.resize((cw, cover_h), Image.LANCZOS)
            bordered = Image.new("RGB", (cw + 2, cover_h + 2), BRAND_CREAM)
            bordered.paste(cover, (1, 1))
            cv = bordered.convert("RGBA")
            # Shadow
            pad = 18
            shadow = Image.new("RGBA",
                               (cv.width + pad * 2, cv.height + pad * 2),
                               (0, 0, 0, 0))
            sd = ImageDraw.Draw(shadow)
            sd.rectangle((pad, pad + 6, pad + cv.width, pad + cv.height + 6),
                         fill=(0, 0, 0, 180))
            shadow = shadow.filter(ImageFilter.GaussianBlur(10))
            composed = shadow.copy()
            composed.alpha_composite(cv, (pad, pad))
            px = center_x + x_offsets[i] - composed.width // 2
            py = start_y + i * vstep
            rgba.alpha_composite(composed, (px, py))
        return rgba.convert("RGB")

    # Horizontal fan (default)
    cover_h = int(h * 0.50)
    if n == 1:
        angles = [0]
    elif n == 2:
        angles = [-4, 4]
    elif n == 3:
        angles = [-6, 0, 6]
    else:
        spread = 14
        angles = [(-spread / 2) + (spread * i / (n - 1)) for i in range(n)]

    rendered = []
    for path, angle in zip(cover_paths, angles):
        cover = Image.open(path).convert("RGB")
        cw = int(cover_h / 1.6)
        cover = cover.resize((cw, cover_h), Image.LANCZOS)
        bordered = Image.new("RGB", (cw + 2, cover_h + 2), BRAND_CREAM)
        bordered.paste(cover, (1, 1))
        cv = bordered.convert("RGBA")
        pad = 22
        shadow = Image.new("RGBA",
                           (cv.width + pad * 2, cv.height + pad * 2),
                           (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rectangle((pad, pad + 6, pad + cv.width, pad + cv.height + 6),
                     fill=(0, 0, 0, 170))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        composed = shadow.copy()
        composed.alpha_composite(cv, (pad, pad))
        composed = composed.rotate(angle, resample=Image.BICUBIC, expand=True)
        rendered.append(composed)

    center_x = w // 2
    center_y = int(h * 0.32)
    step = int(cover_h * 0.42 / 1.6)
    total_w = (n - 1) * step
    start_x = center_x - total_w // 2

    for i, img in enumerate(rendered):
        px = start_x + i * step - img.width // 2
        py = center_y - img.height // 2
        rgba.alpha_composite(img, (px, py))

    return rgba.convert("RGB")


def motif_parchment_desk(canvas: Image.Image, motif_data) -> Image.Image:
    """Aged parchment on dark wood, with handwritten text, wax seal,
    and atmospheric candlelight. For 'author updates' / personal tiles."""
    import math
    w, h = canvas.size
    rgba = canvas.convert("RGBA")
    draw = ImageDraw.Draw(rgba)

    # Subtle dark wood-grain wash on the existing brand background
    grain = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grain)
    import random
    random.seed(7)
    for y in range(0, int(h * 0.70), 3):
        opacity = random.randint(20, 50)
        gd.line([(0, y), (w, y)], fill=(10, 6, 18, opacity))
    rgba.alpha_composite(grain.filter(ImageFilter.GaussianBlur(1.2)))

    # Parchment rectangle — cream, slightly rotated, drop shadow
    parch_w = int(w * 0.62)
    parch_h = int(h * 0.42)
    parch_cx = int(w * 0.50)
    parch_cy = int(h * 0.30)
    tilt = -3.5  # gentle natural rotation

    # Build parchment with rough/torn edges
    parch = Image.new("RGBA", (parch_w + 80, parch_h + 80), (0, 0, 0, 0))
    pd = ImageDraw.Draw(parch)
    # Main paper body
    paper_color = (245, 235, 215, 255)  # slightly warmer than brand-cream
    pd.rounded_rectangle((40, 40, 40 + parch_w, 40 + parch_h),
                         radius=4, fill=paper_color)
    # Aged staining: a few coffee-ring-style dabs at random
    stain = Image.new("RGBA", (parch_w + 80, parch_h + 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(stain)
    random.seed(13)
    for _ in range(6):
        sx = random.randint(80, parch_w - 30)
        sy = random.randint(80, parch_h - 30)
        sr = random.randint(40, 90)
        sd.ellipse((sx - sr, sy - sr, sx + sr, sy + sr),
                   fill=(180, 140, 80, random.randint(18, 35)))
    stain = stain.filter(ImageFilter.GaussianBlur(18))
    parch.alpha_composite(stain)

    # Handwritten phrase on the parchment
    phrase = motif_data.get("phrase", "from the desk")
    phrase_font = ImageFont.truetype(str(FONT_ACCENT), int(parch_h * 0.30))
    bbox = pd.textbbox((0, 0), phrase, font=phrase_font)
    pw_text = bbox[2] - bbox[0]
    ph_text = bbox[3] - bbox[1]
    tx = (parch_w + 80 - pw_text) // 2
    ty = 40 + (parch_h - ph_text) // 2 - int(parch_h * 0.08)
    # Slight ink-bleed shadow
    pd.text((tx + 1, ty + 1), phrase, font=phrase_font,
            fill=(60, 25, 15, 80))
    pd.text((tx, ty), phrase, font=phrase_font,
            fill=(60, 30, 50, 230))  # dark plum-ink

    # Underline rule
    rule_x1 = tx + int(pw_text * 0.18)
    rule_x2 = tx + int(pw_text * 0.82)
    rule_y = ty + ph_text + int(parch_h * 0.05)
    pd.line([(rule_x1, rule_y), (rule_x2, rule_y)],
            fill=(80, 40, 60, 180), width=2)

    # Wax seal — small coral disc bottom-right of parchment
    seal_r = int(parch_h * 0.10)
    seal_cx = parch_w + 40 - int(seal_r * 1.4)
    seal_cy = parch_h + 40 - int(seal_r * 1.4)
    pd.ellipse((seal_cx - seal_r, seal_cy - seal_r,
                seal_cx + seal_r, seal_cy + seal_r),
               fill=(190, 50, 70, 240))
    pd.ellipse((seal_cx - seal_r + 4, seal_cy - seal_r + 4,
                seal_cx + seal_r - 4, seal_cy + seal_r - 4),
               outline=(140, 30, 50, 200), width=2)
    # Tiny "S" mark in seal
    sf = ImageFont.truetype(str(FONT_IMPRINT), int(seal_r * 1.2))
    sbox = pd.textbbox((0, 0), "S", font=sf)
    sw, sh = sbox[2] - sbox[0], sbox[3] - sbox[1]
    pd.text((seal_cx - sw // 2, seal_cy - sh // 2 - 2),
            "S", font=sf, fill=(245, 220, 180, 220))

    # Drop shadow for parchment
    shadow = Image.new("RGBA", (parch_w + 120, parch_h + 120), (0, 0, 0, 0))
    shd = ImageDraw.Draw(shadow)
    shd.rounded_rectangle((40 + 8, 40 + 12,
                           40 + parch_w + 8, 40 + parch_h + 12),
                          radius=4, fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))

    # Rotate both
    parch = parch.rotate(tilt, resample=Image.BICUBIC, expand=True)
    shadow = shadow.rotate(tilt, resample=Image.BICUBIC, expand=True)

    # Composite shadow first then parchment
    paste_x = parch_cx - parch.width // 2
    paste_y = parch_cy - parch.height // 2
    rgba.alpha_composite(shadow, (paste_x - 10, paste_y + 8))
    rgba.alpha_composite(parch, (paste_x, paste_y))

    # Candlelight glow upper-left
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gld = ImageDraw.Draw(glow)
    glow_cx, glow_cy = int(w * 0.15), int(h * 0.12)
    for r in range(int(h * 0.4), 0, -8):
        ratio = r / (h * 0.4)
        alpha = int(70 * (1 - ratio) ** 1.5)
        gld.ellipse((glow_cx - r, glow_cy - r, glow_cx + r, glow_cy + r),
                    fill=BRAND_GOLD + (alpha,))
    glow = glow.filter(ImageFilter.GaussianBlur(30))
    rgba.alpha_composite(glow)

    return rgba.convert("RGB")


def motif_arcane_sigil(canvas: Image.Image, motif_data) -> Image.Image:
    """Magical circle / sigil composition — concentric rings, runes,
    geometric pattern. Lore/grimoire feel for worldbuilding tiles."""
    import math
    w, h = canvas.size
    rgba = canvas.convert("RGBA")
    draw = ImageDraw.Draw(rgba)

    cx = w // 2
    cy = int(h * 0.30)
    base_r = int(h * 0.22)

    # Outer ring (thin gold)
    r_outer = base_r + int(h * 0.04)
    draw.ellipse((cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer),
                 outline=BRAND_GOLD, width=3)
    # Inner thinner ring
    r_outer2 = r_outer - 14
    draw.ellipse((cx - r_outer2, cy - r_outer2, cx + r_outer2, cy + r_outer2),
                 outline=BRAND_GOLD, width=1)

    # Mid ring
    r_mid = int(base_r * 0.78)
    draw.ellipse((cx - r_mid, cy - r_mid, cx + r_mid, cy + r_mid),
                 outline=BRAND_GOLD, width=2)

    # Runes around outer ring — 12 small geometric marks drawn directly
    # (Unicode rune chars don't render in Cinzel — use vector primitives)
    rune_r = (r_outer + r_outer2) // 2
    rune_size = int(h * 0.018)
    for i in range(12):
        angle = (i / 12) * 2 * math.pi - math.pi / 2  # start at top
        rx = cx + int(rune_r * math.cos(angle))
        ry = cy + int(rune_r * math.sin(angle))
        kind = i % 4
        if kind == 0:
            # Vertical bar
            draw.line([(rx, ry - rune_size), (rx, ry + rune_size)],
                      fill=BRAND_GOLD, width=2)
        elif kind == 1:
            # Diamond
            draw.polygon([(rx, ry - rune_size), (rx + rune_size, ry),
                          (rx, ry + rune_size), (rx - rune_size, ry)],
                         outline=BRAND_GOLD, width=2)
        elif kind == 2:
            # Cross
            draw.line([(rx - rune_size, ry), (rx + rune_size, ry)],
                      fill=BRAND_GOLD, width=2)
            draw.line([(rx, ry - rune_size), (rx, ry + rune_size)],
                      fill=BRAND_GOLD, width=2)
        else:
            # Small circle
            draw.ellipse((rx - rune_size, ry - rune_size,
                          rx + rune_size, ry + rune_size),
                         outline=BRAND_GOLD, width=2)

    # Inner geometric pattern — six-pointed star (two overlapping triangles)
    def triangle_at(angle_offset_deg, color):
        pts = []
        for k in range(3):
            ang = math.radians(angle_offset_deg + k * 120 - 90)
            px = cx + int(r_mid * 0.85 * math.cos(ang))
            py = cy + int(r_mid * 0.85 * math.sin(ang))
            pts.append((px, py))
        draw.line([pts[0], pts[1]], fill=color, width=2)
        draw.line([pts[1], pts[2]], fill=color, width=2)
        draw.line([pts[2], pts[0]], fill=color, width=2)
    triangle_at(0, BRAND_GOLD)
    triangle_at(180, BRAND_GOLD)

    # Center dot
    draw.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=BRAND_GOLD)

    # Soft glow behind the sigil
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(r_outer + int(h * 0.12), 0, -6):
        ratio = r / (r_outer + h * 0.12)
        alpha = int(40 * (1 - ratio) ** 1.4)
        gd.ellipse((cx - r, cy - r, cx + r, cy + r),
                   fill=BRAND_GOLD + (alpha,))
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    out = rgba.convert("RGBA")
    blended = Image.alpha_composite(glow, out)
    return blended.convert("RGB")


def motif_imprint_mark(canvas: Image.Image, motif_data) -> Image.Image:
    """Full Savagery & Co. imprint mark — Cinzel wordmark + arrow-piercing-book
    glyph, sized to read clearly at tile dimensions."""
    w, h = canvas.size
    rgba = canvas.convert("RGBA")
    draw = ImageDraw.Draw(rgba)

    # — Arrow-piercing-book glyph (cleaner version) —
    cx = w // 2
    book_cy = int(h * 0.20)
    book_half = int(h * 0.085)  # half-width of book base
    book_top  = book_cy - int(book_half * 0.85)
    book_base = book_cy + int(book_half * 0.85)

    # Open book: two pages meeting at top center, opening down
    left_page  = [(cx - book_half, book_base), (cx, book_top), (cx, book_base)]
    right_page = [(cx, book_top), (cx + book_half, book_base), (cx, book_base)]
    draw.polygon(left_page,  fill=BRAND_CREAM)
    draw.polygon(right_page, fill=BRAND_CREAM)
    # Base spine
    draw.rectangle(
        (cx - book_half - 4, book_base, cx + book_half + 4, book_base + 6),
        fill=BRAND_CREAM,
    )
    # Page detail lines (thin gold rays from spine outward)
    for offset in [0.35, 0.55, 0.75]:
        x_left  = cx - int(book_half * offset)
        x_right = cx + int(book_half * offset)
        y_pos   = book_base - int(book_half * (1 - offset) * 0.4)
        draw.line([(x_left, book_base - 4), (cx - 2, book_top + 20)],
                  fill=BRAND_GOLD, width=2)
        draw.line([(x_right, book_base - 4), (cx + 2, book_top + 20)],
                  fill=BRAND_GOLD, width=2)

    # Arrow shaft running vertically through the book, in gold
    arrow_x = cx
    arrow_top    = int(h * 0.025)
    arrow_bottom = book_base + int(h * 0.05)
    draw.rectangle(
        (arrow_x - 4, arrow_top, arrow_x + 4, arrow_bottom),
        fill=BRAND_GOLD,
    )
    # Arrowhead
    head_w = int(h * 0.028)
    head_h = int(h * 0.032)
    draw.polygon(
        [(arrow_x - head_w, arrow_bottom - 4),
         (arrow_x, arrow_bottom + head_h),
         (arrow_x + head_w, arrow_bottom - 4),
         (arrow_x, arrow_bottom + 6)],
        fill=BRAND_GOLD,
    )
    # Fletching (jagged feather at top)
    flet_y = arrow_top
    flet_w = int(h * 0.022)
    draw.polygon(
        [(arrow_x, flet_y - int(h * 0.025)),
         (arrow_x + flet_w, flet_y),
         (arrow_x + flet_w // 2, flet_y + int(h * 0.008)),
         (arrow_x, flet_y - int(h * 0.005)),
         (arrow_x - flet_w // 2, flet_y + int(h * 0.008)),
         (arrow_x - flet_w, flet_y)],
        fill=BRAND_GOLD,
    )

    # — Cinzel SAVAGERY & CO. wordmark below the glyph —
    word_y = book_base + int(h * 0.10)

    main_size = int(h * 0.06)
    main_font = load_imprint(main_size, variant="Bold")
    main_text = "SAVAGERY"
    main_spacing = int(main_size * 0.16)
    main_total = sum(text_size(draw, ch, main_font)[0] for ch in main_text) + \
                 main_spacing * (len(main_text) - 1)
    cursor = (w - main_total) // 2
    for ch in main_text:
        draw.text((cursor, word_y), ch, font=main_font, fill=BRAND_CREAM)
        cursor += text_size(draw, ch, main_font)[0] + main_spacing

    sub_size = int(h * 0.026)
    sub_font = load_imprint(sub_size, variant="Regular")
    sub_text = "& CO."
    sub_spacing = int(sub_size * 0.42)
    sub_total = sum(text_size(draw, ch, sub_font)[0] for ch in sub_text) + \
                sub_spacing * (len(sub_text) - 1)
    sub_cursor = (w - sub_total) // 2
    sub_y = word_y + main_size + int(h * 0.012)
    for ch in sub_text:
        draw.text((sub_cursor, sub_y), ch, font=sub_font, fill=BRAND_GOLD)
        sub_cursor += text_size(draw, ch, sub_font)[0] + sub_spacing

    return rgba.convert("RGB")


def motif_caveat_flourish(canvas: Image.Image, motif_data) -> Image.Image:
    """Handwritten Caveat flourish — for personal/journal collections."""
    w, h = canvas.size
    rgba = canvas.convert("RGBA")
    draw = ImageDraw.Draw(rgba)
    # Big Caveat-style symbol or a brief handwritten phrase
    font = ImageFont.truetype(str(FONT_ACCENT), int(h * 0.18))
    phrase = motif_data.get("phrase", "— a note —")
    pw, ph = text_size(draw, phrase, font)
    px = (w - pw) // 2
    py = int(h * 0.22)
    # Drop shadow
    draw.text((px + 2, py + 2), phrase, font=font, fill=(0, 0, 0, 120))
    draw.text((px, py), phrase, font=font, fill=BRAND_CORAL + (235,))
    return rgba.convert("RGB")


def motif_custom_image(canvas: Image.Image, motif_data) -> Image.Image:
    """Full-bleed custom image across upper portion with bottom fade.
    Use motif_data['image'] = path to any image. Use 'fit' = 'fill' (default,
    crops to fit) or 'contain' (letterboxes with brand bg)."""
    w, h = canvas.size
    image_path = motif_data.get("image")
    if not image_path or not Path(image_path).exists():
        return motif_brand_only(canvas, motif_data)

    src = Image.open(image_path).convert("RGB")
    target_w = w
    target_h = int(h * motif_data.get("upper_height_pct", 0.70))

    fit = motif_data.get("fit", "fill")
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h

    if fit == "fill":
        # Crop source to target aspect, biased to top-center for portraits
        if src_ratio > target_ratio:
            new_w = int(src.height * target_ratio)
            left = (src.width - new_w) // 2
            src = src.crop((left, 0, left + new_w, src.height))
        else:
            new_h = int(src.width / target_ratio)
            top_bias = motif_data.get("top_bias", 0.0)  # 0 = top, 0.5 = center
            top = int((src.height - new_h) * top_bias)
            src = src.crop((0, top, src.width, top + new_h))
        src = src.resize((target_w, target_h), Image.LANCZOS)
    else:  # contain
        src.thumbnail((target_w, target_h), Image.LANCZOS)

    rgba = canvas.convert("RGBA")
    if fit == "fill":
        rgba.paste(src.convert("RGBA"), (0, 0))
    else:
        px = (target_w - src.width) // 2
        py = (target_h - src.height) // 2
        rgba.paste(src.convert("RGBA"), (px, py))

    rgba_rgb = rgba.convert("RGB")
    return apply_bottom_fade(rgba_rgb, fade_h_pct=0.45)


MOTIFS = {
    "brand_only":       motif_brand_only,
    "portrait":         motif_portrait,
    "single_cover":     motif_single_cover,
    "cover_stack":      motif_cover_stack,
    "imprint_mark":     motif_imprint_mark,
    "caveat_flourish":  motif_caveat_flourish,
    "custom_image":     motif_custom_image,
    "parchment_desk":   motif_parchment_desk,
    "arcane_sigil":     motif_arcane_sigil,
}


# ─── Tile composition ─────────────────────────────────────────────────────

def render_tile(spec: dict) -> Image.Image:
    W = spec.get("width", 1080)
    H = spec.get("height", 1080)
    name        = spec["name"]
    descriptor  = spec.get("descriptor", "")
    accent      = spec.get("accent", BRAND_GOLD)
    motif       = spec.get("motif", "brand_only")
    motif_data  = spec.get("motif_data", {})

    # Background
    img = brand_bg(W, H)

    # Motif
    img = MOTIFS[motif](img, motif_data)

    # Bottom dark band so text sits cleanly
    img = apply_bottom_fade(img, fade_h_pct=0.40)

    draw = ImageDraw.Draw(img)

    # — Title in Fraunces SemiBold, auto-sized and wrapped to fit —
    max_w = int(W * 0.88)
    title_size = int(H * 0.10)
    min_size   = int(H * 0.058)
    title_font = load_display(title_size, variant="SemiBold")
    title_lines = [name]

    # First try to shrink the single-line title until it fits
    while title_size > min_size:
        title_font = load_display(title_size, variant="SemiBold")
        if text_size(draw, name, title_font)[0] <= max_w:
            break
        title_size -= 4

    # If still too wide, wrap to two lines with balanced widths
    if text_size(draw, name, title_font)[0] > max_w:
        words = name.split()
        if len(words) >= 2:
            # Find the split that gives the most balanced line widths
            best_split = 1
            best_diff = float("inf")
            for i in range(1, len(words)):
                w1 = text_size(draw, " ".join(words[:i]),  title_font)[0]
                w2 = text_size(draw, " ".join(words[i:]),  title_font)[0]
                if w1 <= max_w and w2 <= max_w and abs(w1 - w2) < best_diff:
                    best_diff = abs(w1 - w2)
                    best_split = i
            title_lines = [
                " ".join(words[:best_split]),
                " ".join(words[best_split:]),
            ]
            # Reset to default size for the wrapped version (often fits)
            title_size = int(H * 0.095)
            title_font = load_display(title_size, variant="SemiBold")
            # If wrapped lines still don't fit, shrink further
            while title_size > min_size:
                title_font = load_display(title_size, variant="SemiBold")
                if all(text_size(draw, ln, title_font)[0] <= max_w for ln in title_lines):
                    break
                title_size -= 4

    line_h = int(title_size * 1.15)
    block_h = line_h * len(title_lines)
    title_y_start = int(H * 0.66) - block_h // 2

    for i, line in enumerate(title_lines):
        lw, _ = text_size(draw, line, title_font)
        draw.text(((W - lw) // 2, title_y_start + i * line_h),
                  line, font=title_font, fill=BRAND_CREAM)

    # — Accent rule —
    rule_y = title_y_start + block_h + int(title_size * 0.18)
    rule_w = int(W * 0.22)
    draw.line(
        [((W - rule_w) // 2, rule_y), ((W + rule_w) // 2, rule_y)],
        fill=accent, width=max(3, int(H * 0.005)),
    )

    # — Descriptor below rule, Inter italic-ish (regular for now) —
    if descriptor:
        desc_size = int(H * 0.028)
        desc_font = load_italic(desc_size, variant="Italic")
        dw, dh = text_size(draw, descriptor, desc_font)
        desc_y = rule_y + int(H * 0.022)
        draw.text(((W - dw) // 2, desc_y),
                  descriptor, font=desc_font, fill=MUTED_LAV)

    # — Small "ALEX SAVAGE · SAVAGERY & CO." footer —
    footer_font = load_body(int(H * 0.018), variant="SemiBold")
    footer_text = "ALEX  SAVAGE  ·  SAVAGERY  &  CO."
    fw, fh = text_size(draw, footer_text, footer_font)
    draw.text(((W - fw) // 2, int(H * 0.94)),
              footer_text, font=footer_font, fill=BRAND_GOLD)

    return img


# ─── Collections config ───────────────────────────────────────────────────
# Edit names, descriptors, accent colors, motifs here. Re-run script to apply.

COLLECTIONS = [
    {
        "name":       "Undercover Archmage",
        "descriptor": "Magic-academy action haremlit · The Ravenwick Chronicle",
        "accent":     BRAND_GOLD,
        "motif":      "single_cover",
        "motif_data": {"cover": COVER_UA1, "tilt": -3},
    },
    {
        "name":       "WarMage of Arkley",
        "descriptor": "Slice-of-life LitRPG · Single-dad apocalypse",
        "accent":     BRAND_CORAL,
        "motif":      "single_cover",
        "motif_data": {"cover": COVER_WA1, "tilt": 3},
    },
    {
        "name":       "Welcome & Information",
        "descriptor": "Start here · About the imprint · Patreon perks",
        "accent":     BRAND_GOLD,
        "motif":      "portrait",
        "motif_data": {},
    },
    {
        "name":       "State of the Desk",
        "descriptor": "Author updates · Voice memos · Plotting in real time",
        "accent":     BRAND_CORAL,
        "motif":      "parchment_desk",
        "motif_data": {"phrase": "from the desk"},
    },
    {
        "name":       "Free Sample Chapters",
        "descriptor": "First-look chapters · Open to all tiers",
        "accent":     BRAND_GOLD,
        "motif":      "cover_stack",
        "motif_data": {"covers": [COVER_UA1, COVER_WA1, COVER_UA4]},
    },
    {
        "name":       "Bonus Shorts",
        "descriptor": "Side stories · Between-book scenes",
        "accent":     BRAND_CORAL,
        "motif":      "custom_image",
        "motif_data": {
            "image": str(ASSETS_DIR / "patreon-collections/source/bonus-shorts-bubble-gum.webp"),
            "top_bias": 0.0,
        },
    },
    {
        "name":       "World Bible",
        "descriptor": "Lore · Continuity · Worldbuilding reference",
        "accent":     BRAND_GOLD,
        "motif":      "arcane_sigil",
        "motif_data": {},
    },
    {
        "name":       "Adept Editions",
        "descriptor": "Adept tier · Premium bonus material",
        "accent":     BRAND_GOLD,
        "motif":      "cover_stack",
        "motif_data": {
            "covers": [COVER_UA1, COVER_UA2, COVER_UA3, COVER_UA4],
            "orientation": "vertical",
        },
    },
    {
        "name":       "Waifu Cards",
        "descriptor": "Character portrait collection · Premium tier",
        "accent":     BRAND_CORAL,
        "motif":      "custom_image",
        "motif_data": {
            "image": str(ASSETS_DIR / "patreon-collections/source/waifu-card-premium-redhead-library.webp"),
            "top_bias": 0.05,
        },
    },
    {
        "name":       "Initiate Waifu Cards",
        "descriptor": "Character cards · Free tier introduction",
        "accent":     BRAND_CORAL,
        "motif":      "custom_image",
        "motif_data": {
            "image": str(ASSETS_DIR / "patreon-collections/source/waifu-card-free-cheerleader.jpg"),
            "top_bias": 0.0,
        },
    },
]


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Patreon Collection Tiles",
    )
    parser.add_argument("-o", "--output", type=Path, default=ASSETS_DIR,
                        help="Output directory (default: assets/)")
    args = parser.parse_args()

    out = args.output / "patreon-collections"
    out.mkdir(parents=True, exist_ok=True)

    print("Alex Savage — Patreon Collection Tiles")
    print(f"Generating {len(COLLECTIONS)} tiles → {out}/\n")

    for spec in COLLECTIONS:
        # Add default dimensions
        spec.setdefault("width", 1080)
        spec.setdefault("height", 1080)
        img = render_tile(spec)
        slug = slugify(spec["name"])
        out_path = out / f"{slug}.jpg"
        img.save(out_path, "JPEG", quality=92,
                 optimize=True, progressive=True)
        print(f"  ✓ {spec['name']:30s}  →  {out_path.name}")

    print(f"\nDone. {len(COLLECTIONS)} tiles generated.")


if __name__ == "__main__":
    main()
