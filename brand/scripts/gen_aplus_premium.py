#!/usr/bin/env python3
"""
Alex Savage — A+ premium design pass.

Applies senior-designer polish across the four module types:
    * Banner header (970x300)
    * Hero single image (970x600)
    * Polaroid character tile (300x300)
    * Review quote tile (300x300)

Moves added on top of the base layouts:
    * Paper-grain noise on dark backgrounds
    * Layered drop shadows (close-sharp + far-soft)
    * Washi tape strip on polaroid cards
    * Refined accent rule with dot ornament caps
    * Ghost-quotation glyph behind quote text
    * Edge vignette on hero modules
    * AS monogram watermark in hero negative space

Usage:
    python3 gen_aplus_premium.py --book wa1 \
        --headline "Magic. Apocalypse. School runs." \
        --sub "A Supremacy-grade mage. A daughter to raise. ..." \
        --char "src/teacher.png||His daughter's teacher.||Has questions." \
        --char "src/bear.png||A shapeshifting bear.||Knows what he is." \
        --char "src/babysitter.jpg||The babysitter.||Utterly lethal." \
        --review "Quote text||Reviewer Name" \
        --review "Quote text||Reviewer Name" \
        --review "Quote text||Reviewer Name" \
        --review "Quote text||Reviewer Name"

For now this script also exports specific functions used by the WA1/WA2
batch script — call render_hero(), render_banner_header(), render_polaroid_tile(),
render_quote_tile() directly.
"""

import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Paths ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
BRAND_DIR  = SCRIPT_DIR.parent
ASSETS_DIR = BRAND_DIR.parent / "assets"
FONT_DIR   = BRAND_DIR / "fonts"
FONT_DISPLAY = FONT_DIR / "Fraunces-VF.ttf"
FONT_BODY    = FONT_DIR / "Inter-VF.ttf"

# ─── Palette ──────────────────────────────────────────────────────────────
PRIMARY_DEEP     = (22, 12, 36)
PRIMARY_DEEPER   = (12, 6, 22)        # vignette corners
BRAND_GOLD       = (232, 183, 86)
BRAND_GOLD_GLINT = (244, 215, 142)
BRAND_CORAL      = (255, 126, 148)
BRAND_CORAL_DEEP = (210, 90, 110)
BRAND_CREAM      = (245, 239, 230)
BRAND_CREAM_DEEP = (220, 213, 199)
MUTED_LAV        = (180, 165, 200)
SHADOW_PURPLE    = (10, 4, 18)        # tinted shadow rather than pure black

# ─── Fonts ────────────────────────────────────────────────────────────────
def load_display(size, variant="SemiBold"):
    f = ImageFont.truetype(str(FONT_DISPLAY), size)
    try: f.set_variation_by_name(variant.encode())
    except Exception: pass
    return f

def load_italic(size, variant="Italic"):
    f = ImageFont.truetype(str(FONT_DISPLAY), size)
    try: f.set_variation_by_name(variant.encode())
    except Exception: pass
    return f

def load_body(size, variant="SemiBold"):
    f = ImageFont.truetype(str(FONT_BODY), size)
    try: f.set_variation_by_name(variant.encode())
    except Exception: pass
    return f

def text_w(draw, text, font):
    return draw.textbbox((0, 0), text, font=font)[2]

def text_size(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]

# ─── Helpers: paper grain, vignette, layered shadow, refined rule ─────────
def add_paper_grain(im: Image.Image, intensity: int = 8,
                    seed: int = 42) -> Image.Image:
    """Overlay subtle noise. Intensity ~6-12 reads as film grain."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(im.convert("RGB"), dtype=np.int16)
    noise = rng.integers(-intensity, intensity + 1, arr.shape, dtype=np.int16)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(arr)


def add_edge_vignette(im: Image.Image, strength: float = 0.55) -> Image.Image:
    """Darken corners gently for cinematic depth."""
    w, h = im.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = w / 2, h / 2
    max_d = math.hypot(cx, cy)
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    yy, xx = np.indices((h, w))
    d = np.hypot(xx - cx, yy - cy) / max_d
    alpha = np.clip((d - 0.45) / (1.0 - 0.45), 0, 1) ** 1.6 * (255 * strength)
    arr[..., 3] = alpha.astype(np.uint8)
    overlay = Image.fromarray(arr, mode="RGBA")
    base = im.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def layered_shadow_mask(width: int, height: int,
                        passes=((4, 6, 8, 90), (10, 14, 20, 140))):
    """Build a stacked drop-shadow image from a rectangle mask.
       passes: list of (offset_x, offset_y, blur, alpha)."""
    pad = max(p[0] + p[2] + 6 for p in passes), max(p[1] + p[2] + 6 for p in passes)
    canvas_w = width + pad[0] * 2
    canvas_h = height + pad[1] * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    for ox, oy, blur, alpha in passes:
        layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rectangle((pad[0] + ox, pad[1] + oy,
                     pad[0] + ox + width, pad[1] + oy + height),
                    fill=SHADOW_PURPLE + (alpha,))
        layer = layer.filter(ImageFilter.GaussianBlur(blur))
        canvas.alpha_composite(layer)
    return canvas, pad


def draw_refined_rule(draw, x, y, length, color, cap_color=None, thickness=2):
    """Hairline with a small dot ornament at the right end."""
    if cap_color is None:
        cap_color = color
    draw.line([(x, y), (x + length, y)], fill=color, width=thickness)
    r = max(2, thickness + 1)
    draw.ellipse((x + length - r, y - r, x + length + r, y + r), fill=cap_color)


def draw_star(d, cx, cy, r, fill, inner_ratio=0.4):
    inner = r * inner_ratio
    pts = []
    for i in range(10):
        ang = math.pi / 2 - i * math.pi / 5
        rad = r if i % 2 == 0 else inner
        pts.append((cx + rad * math.cos(ang), cy - rad * math.sin(ang)))
    d.polygon(pts, fill=fill)


def add_washi_tape(card_img: Image.Image, tape_color: tuple[int, int, int],
                   length_pct: float = 0.30, height_px: int = 18,
                   x_center_pct: float = 0.50, alpha: int = 160) -> Image.Image:
    """Add a translucent washi tape strip across the TOP edge of a card.
       Subtle, no rotation — the tape signals 'pinned photo' without shouting."""
    w, h = card_img.size
    tape_w = int(w * length_pct)
    tape_h = height_px
    tape_x = int(w * x_center_pct - tape_w / 2)
    tape_y = -4  # extend just past top edge

    overlay = Image.new("RGBA", card_img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # Main tape body
    d.rectangle((tape_x, tape_y, tape_x + tape_w, tape_y + tape_h),
                fill=tape_color + (alpha,))
    # Inner highlight line (paper crepe-tape feel)
    d.line([(tape_x + 4, tape_y + tape_h // 2),
            (tape_x + tape_w - 4, tape_y + tape_h // 2)],
           fill=tape_color + (max(0, alpha - 60),), width=1)
    # Add very subtle frayed edges via short alpha ramps
    base = card_img.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


def smooth_ai_photo(im: Image.Image,
                    blur_radius: float = 0.6,
                    saturation: float = 0.92,
                    grain_intensity: int = 6,
                    vignette: float = 0.25,
                    warm_shift: tuple = (4, 0, -4)) -> Image.Image:
    """Take the edge off a raw AI-generated portrait.
       Subtle soften + slight desaturation + warm grade + film grain + vignette.
       Keeps the face readable while making the image feel less synthetic."""
    from PIL import ImageEnhance
    out = im.convert("RGB")
    # Micro-blur to soften linework
    if blur_radius > 0:
        out = out.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    # Desaturate slightly — AI generations tend to be over-saturated
    if saturation != 1.0:
        out = ImageEnhance.Color(out).enhance(saturation)
    # Warm shift in RGB
    if any(v != 0 for v in warm_shift):
        arr = np.asarray(out, dtype=np.int16)
        arr[..., 0] = np.clip(arr[..., 0] + warm_shift[0], 0, 255)
        arr[..., 1] = np.clip(arr[..., 1] + warm_shift[1], 0, 255)
        arr[..., 2] = np.clip(arr[..., 2] + warm_shift[2], 0, 255)
        out = Image.fromarray(arr.astype(np.uint8))
    # Film grain
    if grain_intensity > 0:
        out = add_paper_grain(out, intensity=grain_intensity, seed=77)
    # Subtle vignette
    if vignette > 0:
        out = add_edge_vignette(out, strength=vignette)
    return out


def crop_for_face(im: Image.Image, eye_x_pct: float, eye_y_pct: float,
                  head_height_pct: float,
                  target_head_pct_of_crop: float = 0.78,
                  eye_y_pct_of_crop: float = 0.40) -> Image.Image:
    w, h = im.size
    head_h_px = h * head_height_pct
    eye_x_abs = w * eye_x_pct
    eye_y_abs = h * eye_y_pct
    side = int(head_h_px / target_head_pct_of_crop)
    side = min(side, w, h)
    crop_left = int(eye_x_abs - side / 2)
    crop_left = max(0, min(crop_left, w - side))
    crop_top  = int(eye_y_abs - side * eye_y_pct_of_crop)
    crop_top  = max(0, min(crop_top, h - side))
    return im.crop((crop_left, crop_top, crop_left + side, crop_top + side))


def make_grain_bg(W: int, H: int, base_color=PRIMARY_DEEP,
                  glow_color=BRAND_CORAL, glow_anchor=(0.78, 0.18),
                  glow_strength=0.16, grain=8, seed=42) -> Image.Image:
    """Deep-purple background with off-center radial brand glow and paper grain."""
    img = Image.new("RGB", (W, H), base_color)
    cx, cy = W * glow_anchor[0], H * glow_anchor[1]
    max_d = math.hypot(W, H) * 0.6
    yy, xx = np.indices((H, W))
    d = np.hypot(xx - cx, yy - cy) / max_d
    ratio = np.clip(1 - d, 0, 1) ** 2.4 * glow_strength
    base = np.full((H, W, 3), base_color, dtype=np.float32)
    glow = np.full((H, W, 3), glow_color, dtype=np.float32)
    blended = base + (glow - base) * ratio[..., None]
    img = Image.fromarray(np.clip(blended, 0, 255).astype(np.uint8))
    if grain:
        img = add_paper_grain(img, intensity=grain, seed=seed)
    return img


def draw_monogram(draw: ImageDraw.ImageDraw, cx: int, cy: int,
                  size: int = 70, color=BRAND_CREAM, alpha=18):
    """Faint A·S monogram for hero watermark. Drawn with alpha by using a layer."""
    return None  # left to caller — needs its own RGBA layer


# ─── Cover with layered shadow ────────────────────────────────────────────
def make_cover_with_layered_shadow(cover_path: Path, target_h: int,
                                   tilt: float = -2.0) -> Image.Image:
    cover = Image.open(cover_path).convert("RGB")
    ratio = target_h / cover.height
    target_w = int(cover.width * ratio)
    cover = cover.resize((target_w, target_h), Image.LANCZOS)
    # Border (cream micro-edge — signals print page)
    bordered = Image.new("RGB", (target_w + 4, target_h + 4), BRAND_CREAM)
    bordered.paste(cover, (2, 2))
    cv = bordered.convert("RGBA")
    if abs(tilt) > 0.01:
        cv = cv.rotate(tilt, resample=Image.BICUBIC, expand=True)
    # Layered shadow
    shadow_img, pad = layered_shadow_mask(cv.width, cv.height,
        passes=((3, 6, 4, 100), (10, 18, 22, 140)))
    canvas = Image.new("RGBA",
                       (cv.width + pad[0] * 2, cv.height + pad[1] * 2),
                       (0, 0, 0, 0))
    canvas.alpha_composite(shadow_img)
    canvas.alpha_composite(cv, (pad[0], pad[1]))
    return canvas


# ─── Module 1 — Banner header (970x300) ───────────────────────────────────
def render_banner_header(cover_path: Path, headline: str, sub_text: str,
                         tonal_lean: str = "slice_of_life") -> Image.Image:
    """3-zone layout: cover | headline column | brand block on the right.
    Each headline beat gets its own line so 'Bigger apocalypse' can't bleed off."""
    W, H = 970, 300
    accent = BRAND_CORAL if tonal_lean == "slice_of_life" else BRAND_GOLD
    bg = make_grain_bg(W, H, glow_color=accent,
                       glow_anchor=(0.92, 0.12), glow_strength=0.16,
                       grain=5, seed=11)
    canvas = bg.convert("RGBA")

    # Cover with layered shadow. text_x is computed from cover_pkg.width (which
    # already includes the shadow blur padding) so text can never overlap the
    # shadow trail.
    cover_target_h = int(H * 0.84)
    cover_pkg = make_cover_with_layered_shadow(cover_path, cover_target_h, tilt=-2)
    cover_x = 18
    cover_y = (H - cover_pkg.height) // 2
    canvas.alpha_composite(cover_pkg, (cover_x, cover_y))

    # Three-zone layout maths — gap is past the entire cover package
    text_x = cover_x + cover_pkg.width + 14
    BRAND_BLOCK_W = 150       # right-side anchor block
    text_w_avail = W - text_x - BRAND_BLOCK_W - 28

    draw = ImageDraw.Draw(canvas)

    # ── Headline first (each beat on its own line, so nothing bleeds) ─────
    parts = [p.strip() for p in headline.split(".") if p.strip()]
    if not parts:
        parts = [headline]

    # Auto-size so the longest line fits the column
    h_size = 38
    while h_size > 20:
        f = load_display(h_size, variant="SemiBold")
        max_w = max(text_size(draw, p + ".", f)[0] for p in parts)
        if max_w <= text_w_avail:
            break
        h_size -= 2
    f = load_display(h_size, variant="SemiBold")
    line_h = int(h_size * 1.02)

    # Vertically center the headline block in the canvas
    block_h = line_h * len(parts)
    headline_y = (H - block_h) // 2 - 6

    for i, line in enumerate(parts):
        is_last = (i == len(parts) - 1)
        fill = accent if is_last and len(parts) > 1 else BRAND_CREAM
        draw.text((text_x, headline_y + i * line_h), line + ".",
                  font=f, fill=fill, anchor="lt")

    # Sub-text below — Inter Medium for crisp small-text rendering.
    # (Italic Fraunces at 13pt on grain reads fuzzy at this scale; Inter is
    # designed for screen legibility and renders sharp under JPEG.)
    sub_y = headline_y + block_h + 12
    sub_font = load_body(13, variant="Medium")
    sw = text_size(draw, sub_text, sub_font)[0]
    if sw <= text_w_avail:
        draw.text((text_x, sub_y), sub_text, font=sub_font, fill=BRAND_CREAM_DEEP,
                  anchor="lt")
    else:
        words = sub_text.split()
        lines, cur = [], []
        for word in words:
            trial = " ".join(cur + [word])
            if text_size(draw, trial, sub_font)[0] <= text_w_avail:
                cur.append(word)
            else:
                if cur: lines.append(" ".join(cur))
                cur = [word]
        if cur: lines.append(" ".join(cur))
        for i, ln in enumerate(lines[:2]):
            draw.text((text_x, sub_y + i * 18), ln, font=sub_font,
                      fill=BRAND_CREAM_DEEP, anchor="lt")

    # ── Right-side brand block fills the negative space ──────────────────
    # Vertical hairline divider with dot caps top and bottom
    brand_x = W - BRAND_BLOCK_W + 4
    div_x = brand_x
    div_top = 50
    div_bot = H - 50
    draw.line([(div_x, div_top), (div_x, div_bot)], fill=accent, width=1)
    r = 3
    draw.ellipse((div_x - r, div_top - r, div_x + r, div_top + r),
                 fill=BRAND_GOLD_GLINT)
    draw.ellipse((div_x - r, div_bot - r, div_x + r, div_bot + r),
                 fill=BRAND_GOLD_GLINT)

    # Wordmark stacked + kicker, vertically centered in the brand block
    block_inner_x = brand_x + 22
    wm_font = load_display(22, variant="SemiBold")
    wm_text = "Alex"
    wm2_text = "Savage"
    wm_h_each = text_size(draw, wm_text, wm_font)[1]
    kicker_line_a = "ACTION HAREMLIT"
    kicker_line_b = "SLICE-OF-LIFE LITRPG"
    kicker_font = load_body(9, variant="SemiBold")
    kh = text_size(draw, kicker_line_a, kicker_font)[1]
    # Total stack: wm + wm + gap + rule + gap + 2 kicker lines
    stack_h = wm_h_each * 2 + 10 + 14 + (kh + 4) * 2
    stack_top = (H - stack_h) // 2

    draw.text((block_inner_x, stack_top), wm_text, font=wm_font,
              fill=BRAND_CREAM, anchor="lt")
    draw.text((block_inner_x, stack_top + wm_h_each + 4), wm2_text,
              font=wm_font, fill=BRAND_CREAM, anchor="lt")
    rule_y2 = stack_top + wm_h_each * 2 + 14
    draw_refined_rule(draw, block_inner_x, rule_y2, 44, accent,
                      cap_color=BRAND_GOLD_GLINT, thickness=2)
    kicker_y = rule_y2 + 10
    for i, ln in enumerate([kicker_line_a, kicker_line_b]):
        draw.text((block_inner_x, kicker_y + i * (kh + 4)), ln,
                  font=kicker_font, fill=accent, anchor="lt")

    return canvas.convert("RGB")


# ─── Module 1b — Hero (970x600) ───────────────────────────────────────────
def render_hero(cover_path: Path, headline: str, sub_text: str,
                tonal_lean: str = "slice_of_life") -> Image.Image:
    W, H = 970, 600
    accent = BRAND_CORAL if tonal_lean == "slice_of_life" else BRAND_GOLD
    bg = make_grain_bg(W, H, glow_color=accent,
                       glow_anchor=(0.82, 0.20), glow_strength=0.18,
                       grain=8, seed=23)
    bg = add_edge_vignette(bg, strength=0.40)
    canvas = bg.convert("RGBA")

    # Monogram watermark — tucked tight into bottom-right, very subtle
    mono_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mono_layer)
    mono_font = load_display(150, variant="Bold")
    mono_text = "AS"
    mw, mh = text_size(md, mono_text, mono_font)
    md.text((W - mw - 24, H - mh - 8), mono_text, font=mono_font,
            fill=BRAND_GOLD_GLINT + (6,))
    canvas.alpha_composite(mono_layer)

    # Cover with layered shadow — compute text_x from the actual package width
    # so the shadow blur trail can't extend into the text column.
    cover_target_h = int(H * 0.82)
    cover_pkg = make_cover_with_layered_shadow(cover_path, cover_target_h, tilt=-2)
    cover_x = 24
    cover_y = (H - cover_pkg.height) // 2
    canvas.alpha_composite(cover_pkg, (cover_x, cover_y))

    # Text starts past the full cover_pkg (cover + shadow padding) + a clean gap
    text_x = cover_x + cover_pkg.width + 18
    text_w_avail = W - text_x - int(W * 0.04)

    draw = ImageDraw.Draw(canvas)

    # Wordmark with monogram dot
    wm_font = load_display(36, variant="SemiBold")
    wm_text = "Alex Savage"
    wm_y = int(H * 0.13)
    draw.text((text_x, wm_y), wm_text, font=wm_font, fill=BRAND_CREAM)
    wm_w, wm_h = text_size(draw, wm_text, wm_font)

    # Tiny accent dot to the left of wordmark (ornament mark)
    dot_r = 4
    draw.ellipse((text_x - 16, wm_y + wm_h // 2 - dot_r,
                  text_x - 16 + dot_r * 2, wm_y + wm_h // 2 + dot_r),
                 fill=accent)

    # Refined rule under wordmark
    rule_y = wm_y + wm_h + 10
    draw_refined_rule(draw, text_x, rule_y, int(wm_w * 0.65), accent,
                      cap_color=BRAND_GOLD_GLINT, thickness=2)

    # Kicker
    kicker_font = load_body(13, variant="SemiBold")
    kicker_text = "ACTION HAREMLIT   ·   SLICE-OF-LIFE LITRPG"
    draw.text((text_x, rule_y + 16), kicker_text, font=kicker_font, fill=accent)

    # Headline — stacked 3-line if 3 parts, last line in accent
    parts = [p.strip() for p in headline.split(".") if p.strip()]
    if not parts:
        parts = [headline]
    h_size = 88
    while h_size > 38:
        f = load_display(h_size, variant="SemiBold")
        max_w = max(text_size(draw, p + ".", f)[0] for p in parts)
        if max_w <= text_w_avail:
            break
        h_size -= 3
    f = load_display(h_size, variant="SemiBold")
    line_h = int(h_size * 1.02)
    headline_y = rule_y + 56
    for i, line in enumerate(parts):
        is_last = (i == len(parts) - 1)
        fill = accent if is_last and len(parts) > 1 else BRAND_CREAM
        draw.text((text_x, headline_y + i * line_h), line + ".",
                  font=f, fill=fill)

    # Sub-text
    sub_y = headline_y + line_h * len(parts) + 14
    sub_size = 22
    sub_font = load_italic(sub_size, variant="Italic")
    words = sub_text.split()
    lines, cur = [], []
    for word in words:
        trial = " ".join(cur + [word])
        if text_size(draw, trial, sub_font)[0] <= text_w_avail:
            cur.append(word)
        else:
            if cur: lines.append(" ".join(cur))
            cur = [word]
    if cur: lines.append(" ".join(cur))
    for i, ln in enumerate(lines[:3]):
        draw.text((text_x, sub_y + i * int(sub_size * 1.35)),
                  ln, font=sub_font, fill=MUTED_LAV)

    return canvas.convert("RGB")


# ─── Module 2 — Polaroid character tile (300x300) ─────────────────────────
def render_polaroid_tile(photo_im: Image.Image, rotation_deg: float = 0.0,
                         tape_color: tuple[int, int, int] = BRAND_GOLD
                         ) -> Image.Image:
    """Polaroid card on deep-purple grain background with washi tape & layered shadow."""
    TILE = 300
    CARD_W, CARD_H = 252, 290
    PAD_T, PAD_S, PAD_B = 12, 12, 48
    PHOTO_W = CARD_W - PAD_S * 2          # 228
    PHOTO_H = CARD_H - PAD_T - PAD_B      # 230

    # Photo
    photo = photo_im.resize((PHOTO_W, PHOTO_H), Image.LANCZOS)

    # Cream card with paper grain
    card = Image.new("RGB", (CARD_W, CARD_H), BRAND_CREAM)
    card = add_paper_grain(card, intensity=4, seed=51)
    card.paste(photo, (PAD_S, PAD_T))

    # Subtle inner bevel under the photo
    cd = ImageDraw.Draw(card)
    bevel_y = PAD_T + PHOTO_H + 1
    cd.line([(PAD_S, bevel_y), (CARD_W - PAD_S, bevel_y)],
            fill=(200, 192, 178), width=1)

    # Tiny dot ornament in the bottom margin of the polaroid (subtle brand mark)
    cd.ellipse((CARD_W // 2 - 2, PAD_T + PHOTO_H + (PAD_B - 4) // 2,
                CARD_W // 2 + 2, PAD_T + PHOTO_H + (PAD_B - 4) // 2 + 4),
               fill=tape_color)

    # Washi tape strip at top
    card = add_washi_tape(card, tape_color, length_pct=0.32, height_px=16,
                          x_center_pct=0.50, alpha=170)

    # Rotate
    card_rgba = card.convert("RGBA")
    rotated = card_rgba.rotate(rotation_deg, resample=Image.BICUBIC, expand=True)

    # Background canvas with grain
    bg = make_grain_bg(TILE, TILE, glow_anchor=(0.75, 0.15),
                       glow_strength=0.10, grain=6, seed=33)
    canvas = bg.convert("RGBA")

    # Layered shadow under card
    shadow_img, pad = layered_shadow_mask(rotated.width, rotated.height,
        passes=((2, 4, 3, 90), (8, 12, 16, 140)))
    paste_x = (TILE - rotated.width) // 2
    paste_y = (TILE - rotated.height) // 2
    canvas.alpha_composite(shadow_img,
                           (paste_x - pad[0], paste_y - pad[1]))
    canvas.alpha_composite(rotated, (paste_x, paste_y))

    return canvas.convert("RGB")


# ─── Module 4 — Premium review quote tile (300x300) ───────────────────────
def render_quote_tile_premium(quote: str, name: str) -> Image.Image:
    TILE = 300
    # Lower grain — small italic text reads fuzzy against high-noise bg
    canvas = make_grain_bg(TILE, TILE, glow_anchor=(0.75, 0.18),
                           glow_strength=0.14, grain=3, seed=hash(name) & 0xFF)
    canvas = canvas.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Ghost quotation glyph (large opening quote, low alpha)
    ghost = Image.new("RGBA", (TILE, TILE), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost)
    glyph_font = load_display(200, variant="Bold")
    glyph = "“"  # left double quotation mark
    gd.text((-10, -50), glyph, font=glyph_font, fill=BRAND_CREAM + (24,))
    canvas.alpha_composite(ghost)

    # Five mini stars (tighter & more refined)
    star_r = 8
    gap = 4
    stars_total_w = 5 * (star_r * 2) + 4 * gap
    sx = (TILE - stars_total_w) // 2 + star_r
    sy = int(TILE * 0.16)
    for i in range(5):
        draw_star(draw, sx + i * (star_r * 2 + gap), sy, star_r,
                  BRAND_GOLD_GLINT, inner_ratio=0.42)

    # Hairline rule between stars and quote
    rule_y = sy + star_r + 10
    draw_refined_rule(draw, TILE // 2 - 28, rule_y, 56,
                      BRAND_CORAL, cap_color=BRAND_GOLD_GLINT, thickness=1)

    # Quote text — auto-size, wrap, max 5 lines, italic Fraunces.
    # Higher starting size keeps text crisp; SemiBoldItalic stroke is more
    # legible than thin Italic on a textured background.
    margin_x = 22
    max_w = TILE - 2 * margin_x
    chosen = None
    for fs in (18, 17, 16, 15, 14, 13):
        f = load_italic(fs, variant="SemiBoldItalic")
        # Wrap
        words = quote.split()
        lines, cur = [], []
        for w in words:
            trial = " ".join(cur + [w])
            if text_w(draw, trial, f) <= max_w:
                cur.append(w)
            else:
                if cur: lines.append(" ".join(cur))
                cur = [w]
        if cur: lines.append(" ".join(cur))
        line_h = int(fs * 1.32)
        if len(lines) <= 5 and len(lines) * line_h <= int(TILE * 0.48):
            chosen = (f, lines, line_h, fs)
            break
    if chosen is None:
        f = load_italic(13, variant="SemiBoldItalic")
        words = quote.split()
        lines = []
        cur = []
        for w in words:
            trial = " ".join(cur + [w])
            if text_w(draw, trial, f) <= max_w:
                cur.append(w)
            else:
                if cur: lines.append(" ".join(cur))
                cur = [w]
        if cur: lines.append(" ".join(cur))
        chosen = (f, lines[:5], 17, 13)
    qf, qlines, qline_h, qfs = chosen
    quote_y = rule_y + 18
    for i, ln in enumerate(qlines):
        lw = text_w(draw, ln, qf)
        draw.text(((TILE - lw) // 2, quote_y + i * qline_h),
                  ln, font=qf, fill=BRAND_CREAM)

    # Attribution at bottom — name + small tag, refined hairline above name
    name_font = load_body(12, variant="SemiBold")
    tag_font  = load_body(8, variant="SemiBold")

    # Hairline rule above attribution
    attr_rule_y = TILE - 64
    draw_refined_rule(draw, TILE // 2 - 22, attr_rule_y, 44,
                      BRAND_CORAL, cap_color=BRAND_GOLD_GLINT, thickness=1)

    name_y = TILE - 48
    nw = text_w(draw, name, name_font)
    draw.text(((TILE - nw) // 2, name_y), name, font=name_font, fill=BRAND_CORAL)

    tag = "AMAZON  ·  5★ VERIFIED"
    tw = text_w(draw, tag, tag_font)
    draw.text(((TILE - tw) // 2, name_y + 18), tag, font=tag_font, fill=MUTED_LAV)

    return canvas.convert("RGB")


# ─── Module 4d — Premium praise/credibility tile (300x300) ────────────────
def render_praise_tile_premium(title_a: str, title_b: str) -> Image.Image:
    TILE = 300
    canvas = make_grain_bg(TILE, TILE, glow_anchor=(0.50, 0.20),
                           glow_strength=0.18, grain=6, seed=99)
    canvas = canvas.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    # Larger stars
    star_r = 11
    gap = 6
    stars_total_w = 5 * (star_r * 2) + 4 * gap
    sx = (TILE - stars_total_w) // 2 + star_r
    sy = int(TILE * 0.18)
    for i in range(5):
        draw_star(draw, sx + i * (star_r * 2 + gap), sy, star_r,
                  BRAND_GOLD_GLINT, inner_ratio=0.42)

    # Kicker
    f_kicker = load_body(10, variant="SemiBold")
    kicker = "PRAISE FOR"
    kw = text_w(draw, kicker, f_kicker)
    draw.text(((TILE - kw) // 2, int(TILE * 0.36)), kicker,
              font=f_kicker, fill=BRAND_CORAL)

    # Title
    f_title = load_display(25, variant="SemiBold")
    aw = text_w(draw, title_a, f_title)
    draw.text(((TILE - aw) // 2, int(TILE * 0.44)),
              title_a, font=f_title, fill=BRAND_CREAM)
    bw = text_w(draw, title_b, f_title)
    draw.text(((TILE - bw) // 2, int(TILE * 0.58)),
              title_b, font=f_title, fill=BRAND_CREAM)

    # Refined rule
    rule_y = int(TILE * 0.78)
    draw_refined_rule(draw, TILE // 2 - 30, rule_y, 60,
                      BRAND_CORAL, cap_color=BRAND_GOLD_GLINT, thickness=2)

    # Sub
    f_sub = load_body(9, variant="Medium")
    sub = "READ THE REST ON AMAZON"
    sw = text_w(draw, sub, f_sub)
    draw.text(((TILE - sw) // 2, rule_y + 11), sub, font=f_sub, fill=MUTED_LAV)

    return canvas.convert("RGB")
