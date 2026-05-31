#!/usr/bin/env python3
"""
Alex Savage — Amazon A+ Content Generator
Builds A+ Content modules for the Amazon book product page. Each module
is rendered as a self-contained image baked with brand typography so it
displays consistently across desktop, tablet, and mobile.

Supported modules:
  • header        — Standard Image Header with Text (1940×600)
  • comparison    — Standard Comparison Chart (rendered as one image)
  • characters    — Multiple-Image Module / character intro trio
  • reviews       — Reader quote card

Amazon A+ rules baked in:
  • No time-sensitive language ("now", "new", "latest", "on sale")
  • No KU / external link mentions
  • RGB, JPEG, ≤ 3MB per image

Usage:
    python3 gen_aplus.py header --book wa1 \
        --headline "Magic. Apocalypse. School runs." \
        --sub "A Supremacy-grade mage. A daughter. A System apocalypse next door."

Output: assets/aplus/{book}/{module}.jpg

Requires: Pillow.
"""

import argparse
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SCRIPT_DIR  = Path(__file__).resolve().parent
BRAND_DIR   = SCRIPT_DIR.parent
ASSETS_DIR  = BRAND_DIR.parent / "assets"
FONT_DIR    = BRAND_DIR / "fonts"

FONT_DISPLAY = FONT_DIR / "Fraunces-VF.ttf"
FONT_ITALIC  = FONT_DIR / "Fraunces-Italic-VF.ttf"
FONT_BODY    = FONT_DIR / "Inter-VF.ttf"

# Brand palette
PRIMARY_DEEP = (22, 12, 36)        # #160C24
SURFACE_1    = (39, 24, 71)        # #271847
BRAND_GOLD   = (232, 183, 86)      # #E8B756
GOLD_SOFT    = (244, 210, 122)     # #F4D27A
BRAND_CORAL  = (255, 126, 148)     # #FF7E94
CORAL_SOFT   = (255, 177, 189)     # #FFB1BD
BRAND_CREAM  = (245, 239, 230)     # #F5EFE6
MUTED_LAV    = (177, 162, 204)     # #B1A2CC

# Module dimensions (Amazon A+ specs, high-res)
HEADER_SIZE     = (1940, 600)
COMPARISON_SIZE = (1464, 600)
CHARACTERS_SIZE = (1464, 600)
REVIEWS_SIZE    = (1464, 600)


# ─── Font helpers ─────────────────────────────────────────────────────────

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


def load_body(size: int, variant: str = "Regular"):
    f = ImageFont.truetype(str(FONT_BODY), size)
    try:
        f.set_variation_by_name(variant.encode())
    except (OSError, AttributeError):
        pass
    return f


def text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def draw_star(draw, cx, cy, outer_r, fill, inner_ratio=0.4):
    """Draw a 5-pointed star centered at (cx, cy)."""
    import math
    points = []
    for i in range(10):
        angle = math.pi / 2 - i * math.pi / 5    # start at top
        r = outer_r if i % 2 == 0 else outer_r * inner_ratio
        x = cx + r * math.cos(angle)
        y = cy - r * math.sin(angle)
        points.append((x, y))
    draw.polygon(points, fill=fill)


def draw_star_row(draw, x_left, y, count, star_size, gap, fill):
    """Draw `count` stars in a horizontal row starting at (x_left, y).
    Returns (total_width, height) of the row for layout."""
    total_w = count * star_size * 2 + (count - 1) * gap
    cx = x_left + star_size
    for _ in range(count):
        draw_star(draw, cx, y + star_size, star_size, fill)
        cx += star_size * 2 + gap
    return total_w, star_size * 2


# ─── Backgrounds ──────────────────────────────────────────────────────────

def brand_bg_slice_of_life(width: int, height: int) -> Image.Image:
    """Warmer composition — coral radial glow primary, gold secondary."""
    bg = Image.new("RGB", (width, height), PRIMARY_DEEP)
    glow = Image.new("RGB", (width, height), PRIMARY_DEEP)
    gd = ImageDraw.Draw(glow)

    # Coral glow upper-right (warm/intimate)
    cx, cy = int(width * 0.85), int(height * 0.30)
    max_r = int(max(width, height) * 0.8)
    for r in range(max_r, 0, -max(1, max_r // 80)):
        ratio = r / max_r
        color = tuple(
            int(PRIMARY_DEEP[i] + (BRAND_CORAL[i] - PRIMARY_DEEP[i]) * (1 - ratio) * 0.16)
            for i in range(3)
        )
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=100))
    bg = Image.blend(bg, glow, 0.45)

    # Subtle gold accent lower-left for texture
    gold = Image.new("RGB", (width, height), PRIMARY_DEEP)
    gd2 = ImageDraw.Draw(gold)
    cx2, cy2 = int(width * 0.1), int(height * 0.85)
    max_r2 = int(max(width, height) * 0.4)
    for r in range(max_r2, 0, -max(1, max_r2 // 60)):
        ratio = r / max_r2
        color = tuple(
            int(PRIMARY_DEEP[i] + (BRAND_GOLD[i] - PRIMARY_DEEP[i]) * (1 - ratio) * 0.08)
            for i in range(3)
        )
        gd2.ellipse((cx2 - r, cy2 - r, cx2 + r, cy2 + r), fill=color)
    gold = gold.filter(ImageFilter.GaussianBlur(radius=80))
    bg = Image.blend(bg, gold, 0.35)
    return bg


def brand_bg_action(width: int, height: int) -> Image.Image:
    """Cooler composition — gold dominant, LitRPG-mechanics register."""
    bg = Image.new("RGB", (width, height), PRIMARY_DEEP)
    glow = Image.new("RGB", (width, height), PRIMARY_DEEP)
    gd = ImageDraw.Draw(glow)
    cx, cy = int(width * 0.80), int(height * 0.20)
    max_r = int(max(width, height) * 0.85)
    for r in range(max_r, 0, -max(1, max_r // 80)):
        ratio = r / max_r
        color = tuple(
            int(PRIMARY_DEEP[i] + (BRAND_GOLD[i] - PRIMARY_DEEP[i]) * (1 - ratio) * 0.16)
            for i in range(3)
        )
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=80))
    return Image.blend(bg, glow, 0.45)


# ─── Cover handling ───────────────────────────────────────────────────────

def make_cover_with_shadow(cover_path: Path, target_h: int,
                           tilt: float = 0.0) -> Image.Image:
    """Cover at target height with cream border + drop shadow + optional tilt."""
    cover = Image.open(cover_path).convert("RGB")
    ratio = cover.width / cover.height
    target_w = int(target_h * ratio)
    cover = cover.resize((target_w, target_h), Image.LANCZOS)

    bordered = Image.new("RGB",
                         (cover.width + 3, cover.height + 3),
                         BRAND_CREAM)
    bordered.paste(cover, (1, 1))
    rgba = bordered.convert("RGBA")

    pad = 30
    shadow = Image.new("RGBA",
                       (rgba.width + pad * 2, rgba.height + pad * 2),
                       (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle((pad, pad + 10, pad + rgba.width, pad + rgba.height + 10),
                 fill=(0, 0, 0, 200))
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))
    composed = shadow.copy()
    composed.alpha_composite(rgba, (pad, pad))

    if abs(tilt) > 0.01:
        composed = composed.rotate(tilt, resample=Image.BICUBIC, expand=True)
    return composed


# ─── Module 1: Image Header with Text ─────────────────────────────────────

def _render_header_compact(W: int, H: int, cover_path: Path,
                           headline: str, sub_text: str,
                           tonal_lean: str) -> Image.Image:
    """Compact layout for 970×300-style headers.
    Headline collapses to 2 lines: setup + punchline."""
    bg = (brand_bg_slice_of_life(W, H) if tonal_lean == "slice_of_life"
          else brand_bg_action(W, H))
    canvas = bg.convert("RGBA")
    accent = BRAND_CORAL if tonal_lean == "slice_of_life" else BRAND_GOLD

    # Cover on the left — taller relative to a short canvas
    cover_h = int(H * 0.88)
    cover = make_cover_with_shadow(cover_path, cover_h, tilt=-2)
    cover_x = int(W * 0.025)
    cover_y = (H - cover.height) // 2
    canvas.alpha_composite(cover, (cover_x, cover_y))

    text_x = cover_x + cover.width + int(W * 0.025)
    text_w_available = W - text_x - int(W * 0.035)

    draw = ImageDraw.Draw(canvas)

    # Wordmark + kicker on a single tight row up top
    wm_font = load_display(20, variant="SemiBold")
    wm_text = "Alex Savage"
    wm_y = int(H * 0.10)
    draw.text((text_x, wm_y), wm_text, font=wm_font, fill=BRAND_CREAM)
    wm_w, wm_h = text_size(draw, wm_text, wm_font)

    # Kicker to the right of wordmark — separator dot in accent
    kicker_font = load_body(10, variant="SemiBold")
    sep = "  ·  "
    kicker_text = "ACTION HAREMLIT" + sep + "SLICE-OF-LIFE LITRPG"
    draw.text((text_x + wm_w + 14, wm_y + wm_h - 14),
              kicker_text, font=kicker_font, fill=accent)

    # Coral rule under wordmark
    rule_y = wm_y + wm_h + 6
    draw.line([(text_x, rule_y), (text_x + int(wm_w * 0.65), rule_y)],
              fill=accent, width=2)

    # Headline: collapse parts into setup + punchline.
    headline_parts = [p.strip() for p in headline.split(".") if p.strip()]
    if len(headline_parts) >= 3:
        setup    = ". ".join(headline_parts[:-1]) + "."
        punchline = headline_parts[-1] + "."
    elif len(headline_parts) == 2:
        setup    = headline_parts[0] + "."
        punchline = headline_parts[1] + "."
    else:
        setup, punchline = (headline_parts[0] if headline_parts else headline), ""

    # Auto-shrink so both lines fit width
    h_size = 40
    while h_size > 22:
        f_setup = load_display(h_size, variant="SemiBold")
        f_punch = load_display(h_size, variant="SemiBold")
        setup_w = text_size(draw, setup, f_setup)[0]
        punch_w = text_size(draw, punchline, f_punch)[0] if punchline else 0
        if max(setup_w, punch_w) <= text_w_available:
            break
        h_size -= 2

    line_h = int(h_size * 1.05)
    headline_y = rule_y + 14
    draw.text((text_x, headline_y), setup,
              font=load_display(h_size, variant="SemiBold"), fill=BRAND_CREAM)
    if punchline:
        draw.text((text_x, headline_y + line_h), punchline,
                  font=load_display(h_size, variant="SemiBold"), fill=accent)

    # Sub-text — small italic, single-line if possible
    sub_y = headline_y + line_h * (2 if punchline else 1) + 8
    sub_size = 14
    sub_font = load_italic(sub_size, variant="Italic")
    # Truncate / wrap to one line
    sub_w = text_size(draw, sub_text, sub_font)[0]
    if sub_w <= text_w_available:
        draw.text((text_x, sub_y), sub_text, font=sub_font, fill=MUTED_LAV)
    else:
        # Wrap to 2 lines max
        words = sub_text.split()
        lines, current = [], []
        for word in words:
            trial = " ".join(current + [word])
            if text_size(draw, trial, sub_font)[0] <= text_w_available:
                current.append(word)
            else:
                if current: lines.append(" ".join(current))
                current = [word]
        if current: lines.append(" ".join(current))
        for i, ln in enumerate(lines[:2]):
            draw.text((text_x, sub_y + i * int(sub_size * 1.3)),
                      ln, font=sub_font, fill=MUTED_LAV)

    return canvas.convert("RGB")


def render_header(book_key: str, cover_path: Path,
                  headline: str, sub_text: str,
                  tonal_lean: str = "slice_of_life",
                  size: tuple[int, int] | None = None) -> Image.Image:
    """Image Header with Text. Defaults to 1940×600 (Premium A+).
    Pass size=(970, 300) for Standard A+ module (uses compact layout).
    Left: cover. Right: wordmark + headline + sub + accent rule."""
    W, H = size if size else HEADER_SIZE
    if H < 400:
        return _render_header_compact(W, H, cover_path, headline, sub_text,
                                       tonal_lean)

    bg = (brand_bg_slice_of_life(W, H) if tonal_lean == "slice_of_life"
          else brand_bg_action(W, H))
    canvas = bg.convert("RGBA")

    # Cover on the left
    cover_h = int(H * 0.82)
    cover_tilt = -3
    cover = make_cover_with_shadow(cover_path, cover_h, tilt=cover_tilt)
    cover_x = int(W * 0.03)
    cover_y = (H - cover.height) // 2
    canvas.alpha_composite(cover, (cover_x, cover_y))

    # Text area starts to the right of the cover
    text_x = cover_x + cover.width + int(W * 0.02)
    text_w_available = W - text_x - int(W * 0.04)

    draw = ImageDraw.Draw(canvas)

    # Author wordmark (top of text area)
    wm_size = 36
    wm_font = load_display(wm_size, variant="SemiBold")
    wm_text = "Alex Savage"
    draw.text((text_x, int(H * 0.10)), wm_text, font=wm_font, fill=BRAND_CREAM)

    # Coral underline rule beneath wordmark
    wm_w, wm_h = text_size(draw, wm_text, wm_font)
    rule_y = int(H * 0.10) + wm_h + 10
    accent = BRAND_CORAL if tonal_lean == "slice_of_life" else BRAND_GOLD
    draw.line([(text_x, rule_y), (text_x + int(wm_w * 0.55), rule_y)],
              fill=accent, width=2)

    # Tiny kicker — "ACTION HAREMLIT"
    kicker_font = load_body(14, variant="SemiBold")
    kicker_text = "ACTION  HAREMLIT  ·  SLICE-OF-LIFE  LITRPG"
    draw.text((text_x, rule_y + 14), kicker_text, font=kicker_font, fill=accent)

    # Headline — three-line stacked for "Magic. Apocalypse. School runs."
    headline_parts = [p.strip() for p in headline.split(".") if p.strip()]
    if len(headline_parts) <= 1:
        headline_parts = [headline]

    headline_size = 110 if len(headline_parts) <= 3 else 80
    headline_font = load_display(headline_size, variant="SemiBold")
    line_h = int(headline_size * 1.05)

    # Auto-shrink if any line wider than available width
    while headline_size > 38:
        headline_font = load_display(headline_size, variant="SemiBold")
        # Include trailing period in the width check since render adds one
        max_line_w = max(text_size(draw, p + ".", headline_font)[0]
                         for p in headline_parts)
        if max_line_w <= text_w_available:
            break
        headline_size -= 3
    line_h = int(headline_size * 1.05)

    block_h = line_h * len(headline_parts)
    headline_y = int(H * 0.32)

    for i, line in enumerate(headline_parts):
        # Last line gets the accent colour (the slice-of-life "punchline")
        is_last = (i == len(headline_parts) - 1)
        fill = accent if is_last and len(headline_parts) > 1 else BRAND_CREAM
        draw.text((text_x, headline_y + i * line_h), line + ".",
                  font=headline_font, fill=fill)

    # Sub-text below headline
    sub_y = headline_y + block_h + int(H * 0.03)
    sub_size = 30
    sub_font = load_italic(sub_size, variant="Italic")
    # Word-wrap sub-text manually
    words = sub_text.split()
    lines = []
    current = []
    for word in words:
        trial = " ".join(current + [word])
        if text_size(draw, trial, sub_font)[0] <= text_w_available:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))

    for i, ln in enumerate(lines):
        draw.text((text_x, sub_y + i * int(sub_size * 1.3)),
                  ln, font=sub_font, fill=MUTED_LAV)

    return canvas.convert("RGB")


# ─── Module 4: Reader Reviews quote card ──────────────────────────────────

def render_reviews(book_title: str, reviews: list[dict],
                   tonal_lean: str = "slice_of_life") -> Image.Image:
    """Module 4 — Image with text overlay carrying 3 Amazon reader quotes.
    Each review is {quote, name}. Stars are always 5 (or pass rating)."""
    W, H = REVIEWS_SIZE
    bg = (brand_bg_slice_of_life(W, H) if tonal_lean == "slice_of_life"
          else brand_bg_action(W, H))
    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    accent = BRAND_CORAL if tonal_lean == "slice_of_life" else BRAND_GOLD

    # — Title bar at top —
    kicker_font = load_body(16, variant="SemiBold")
    title_font = load_display(46, variant="SemiBold")

    kicker_text = "FROM AMAZON READERS · VERIFIED REVIEWS"
    title_text = f"Praise for {book_title}"

    kicker_w, kicker_h = text_size(draw, kicker_text, kicker_font)
    title_w, title_h = text_size(draw, title_text, title_font)

    top_y = int(H * 0.10)
    draw.text(((W - kicker_w) // 2, top_y),
              kicker_text, font=kicker_font, fill=accent)
    draw.text(((W - title_w) // 2, top_y + kicker_h + 12),
              title_text, font=title_font, fill=BRAND_CREAM)

    # Accent rule under title
    rule_y = top_y + kicker_h + 12 + title_h + 18
    rule_w = 120
    draw.line(
        [((W - rule_w) // 2, rule_y), ((W + rule_w) // 2, rule_y)],
        fill=accent, width=2,
    )

    # — Three review columns —
    n = len(reviews)
    if n == 0:
        return canvas.convert("RGB")

    col_top = rule_y + 50
    col_bottom = H - int(H * 0.08)
    col_h_available = col_bottom - col_top

    side_margin = int(W * 0.05)
    gap_between = int(W * 0.025)
    col_w = (W - 2 * side_margin - (n - 1) * gap_between) // n

    quote_font = load_italic(22, variant="Italic")
    name_font = load_body(16, variant="SemiBold")
    tag_font = load_body(11, variant="SemiBold")

    star_size = 12   # outer radius
    star_gap = 8

    for i, review in enumerate(reviews):
        col_x = side_margin + i * (col_w + gap_between)

        # Stars (5 gold stars, drawn as polygons — Fraunces has no ★ glyph)
        row_w = 5 * star_size * 2 + 4 * star_gap
        star_x_left = col_x + (col_w - row_w) // 2
        draw_star_row(draw, star_x_left, col_top, count=5,
                      star_size=star_size, gap=star_gap, fill=BRAND_GOLD)
        sh = star_size * 2

        # Wrap quote text
        quote_text = f"“{review['quote']}”"
        words = quote_text.split()
        lines = []
        current = []
        for word in words:
            trial = " ".join(current + [word])
            if text_size(draw, trial, quote_font)[0] <= col_w - 10:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))

        # Render quote lines, centered in column
        line_h = int(22 * 1.5)
        block_h = line_h * len(lines)
        quote_top = col_top + sh + 24

        for j, line in enumerate(lines):
            lw, _ = text_size(draw, line, quote_font)
            draw.text((col_x + (col_w - lw) // 2, quote_top + j * line_h),
                      line, font=quote_font, fill=BRAND_CREAM)

        # Reviewer name + tag at bottom of column
        name_text = review["name"]
        tag_text = "AMAZON · 5★ VERIFIED"
        nw, nh = text_size(draw, name_text, name_font)
        tw, th = text_size(draw, tag_text, tag_font)

        name_y = quote_top + block_h + 28
        draw.text((col_x + (col_w - nw) // 2, name_y),
                  name_text, font=name_font, fill=accent)
        draw.text((col_x + (col_w - tw) // 2, name_y + nh + 6),
                  tag_text, font=tag_font, fill=MUTED_LAV)

    return canvas.convert("RGB")


# ─── Module 2: Character intro trio ───────────────────────────────────────

def crop_to_portrait(src: Image.Image, target_w: int, target_h: int,
                     face_y_pct: float = 0.30) -> Image.Image:
    """Crop source to target aspect with face in the upper third."""
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h

    if src_ratio < target_ratio:
        # Source taller than target — slice horizontally
        new_h = int(src.width / target_ratio)
        face_px = int(src.height * face_y_pct)
        top = face_px - int(new_h * 0.32)
        top = max(0, min(top, src.height - new_h))
        cropped = src.crop((0, top, src.width, top + new_h))
    else:
        # Source wider — slice sides
        new_w = int(src.height * target_ratio)
        left = (src.width - new_w) // 2
        cropped = src.crop((left, 0, left + new_w, src.height))
    return cropped.resize((target_w, target_h), Image.LANCZOS)


def render_characters(book_key: str, characters: list[dict],
                      title_text: str = "Three women. None of them what they seem.",
                      kicker_text: str = "MEET THE NEIGHBOURS",
                      tonal_lean: str = "slice_of_life") -> Image.Image:
    """Module 2 — three-column character intro trio.
    characters = [{image: Path, descriptor: str, punchline: str}, ...]"""
    W, H = CHARACTERS_SIZE
    bg = (brand_bg_slice_of_life(W, H) if tonal_lean == "slice_of_life"
          else brand_bg_action(W, H))
    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    accent = BRAND_CORAL if tonal_lean == "slice_of_life" else BRAND_GOLD

    # — Title section at top —
    kicker_font = load_body(15, variant="SemiBold")
    title_font = load_display(38, variant="SemiBold")
    kicker_w, kicker_h = text_size(draw, kicker_text, kicker_font)
    title_w, title_h = text_size(draw, title_text, title_font)

    top_y = int(H * 0.06)
    draw.text(((W - kicker_w) // 2, top_y),
              kicker_text, font=kicker_font, fill=accent)
    draw.text(((W - title_w) // 2, top_y + kicker_h + 10),
              title_text, font=title_font, fill=BRAND_CREAM)
    rule_y = top_y + kicker_h + 10 + title_h + 14
    rule_w = 80
    draw.line([((W - rule_w) // 2, rule_y), ((W + rule_w) // 2, rule_y)],
              fill=accent, width=2)

    # — Three character columns —
    n = len(characters)
    side_margin = int(W * 0.04)
    gap = int(W * 0.025)
    col_w = (W - 2 * side_margin - (n - 1) * gap) // n

    # Image area dimensions — 4:5 portrait, sized to fit
    img_h = int(H * 0.50)        # 300px
    img_w = int(img_h * 0.80)    # 240px (4:5)
    # If column is narrower than image_w, scale down
    if img_w > col_w - 20:
        img_w = col_w - 20
        img_h = int(img_w / 0.80)

    desc_font = load_display(20, variant="SemiBold")
    punch_font = load_italic(20, variant="Italic")

    col_top = rule_y + 30

    for i, char in enumerate(characters):
        col_x = side_margin + i * (col_w + gap)
        col_center = col_x + col_w // 2

        # Load and crop character image
        src = Image.open(char["image"]).convert("RGB")
        face_y = char.get("face_y", 0.30)
        portrait = crop_to_portrait(src, img_w, img_h, face_y_pct=face_y)

        # Round-corner mask + cream border + drop shadow
        bordered = Image.new("RGB",
                             (portrait.width + 4, portrait.height + 4),
                             BRAND_CREAM)
        bordered.paste(portrait, (2, 2))
        rgba = bordered.convert("RGBA")

        pad = 16
        shadow = Image.new("RGBA",
                           (rgba.width + pad * 2, rgba.height + pad * 2),
                           (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rectangle((pad, pad + 6, pad + rgba.width, pad + rgba.height + 6),
                     fill=(0, 0, 0, 200))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        composed = shadow.copy()
        composed.alpha_composite(rgba, (pad, pad))

        paste_x = col_center - composed.width // 2
        paste_y = col_top
        canvas.alpha_composite(composed, (paste_x, paste_y))

        # Captions beneath
        descriptor = char["descriptor"]
        punchline = char["punchline"]
        dw, dh = text_size(draw, descriptor, desc_font)
        pw, ph = text_size(draw, punchline, punch_font)

        cap_y = paste_y + composed.height - pad + 4
        draw.text((col_center - dw // 2, cap_y),
                  descriptor, font=desc_font, fill=BRAND_CREAM)
        draw.text((col_center - pw // 2, cap_y + dh + 6),
                  punchline, font=punch_font, fill=accent)

    return canvas.convert("RGB")


# ─── Module 3: Catalog Comparison ─────────────────────────────────────────

def render_comparison(book_key: str, books: list[dict],
                      title_text: str = "More from Alex Savage",
                      kicker_text: str = "WHERE TO READ NEXT",
                      tonal_lean: str = "slice_of_life") -> Image.Image:
    """Module 3 — comparison chart cross-promoting other books in the catalog.
    books = [{cover: Path, title: str, series: str, hook: str, tag: str}, ...]
    Up to 5 columns supported."""
    W, H = COMPARISON_SIZE
    bg = (brand_bg_slice_of_life(W, H) if tonal_lean == "slice_of_life"
          else brand_bg_action(W, H))
    canvas = bg.convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    accent = BRAND_CORAL if tonal_lean == "slice_of_life" else BRAND_GOLD

    # — Title section —
    kicker_font = load_body(15, variant="SemiBold")
    title_font = load_display(38, variant="SemiBold")
    kicker_w, kicker_h = text_size(draw, kicker_text, kicker_font)
    title_w, title_h = text_size(draw, title_text, title_font)

    top_y = int(H * 0.06)
    draw.text(((W - kicker_w) // 2, top_y),
              kicker_text, font=kicker_font, fill=accent)
    draw.text(((W - title_w) // 2, top_y + kicker_h + 10),
              title_text, font=title_font, fill=BRAND_CREAM)
    rule_y = top_y + kicker_h + 10 + title_h + 14
    draw.line([((W - 80) // 2, rule_y), ((W + 80) // 2, rule_y)],
              fill=accent, width=2)

    # — Book columns —
    n = len(books)
    side_margin = int(W * 0.04)
    gap = int(W * 0.018)
    col_w = (W - 2 * side_margin - (n - 1) * gap) // n

    cover_h = int(H * 0.45)
    cover_w = int(cover_h / 1.6)
    # Ensure cover fits in column
    if cover_w > col_w - 30:
        cover_w = col_w - 30
        cover_h = int(cover_w * 1.6)

    title_card_font = load_display(20, variant="SemiBold")
    series_font = load_body(11, variant="SemiBold")
    hook_font = load_italic(15, variant="Italic")
    tag_font = load_body(11, variant="SemiBold")

    col_top = rule_y + 24

    for i, book in enumerate(books):
        col_x = side_margin + i * (col_w + gap)
        col_center = col_x + col_w // 2

        # Cover
        try:
            cover = Image.open(book["cover"]).convert("RGB")
        except Exception:
            continue
        cover = cover.resize((cover_w, cover_h), Image.LANCZOS)
        bordered = Image.new("RGB", (cover_w + 3, cover_h + 3), BRAND_CREAM)
        bordered.paste(cover, (1, 1))
        cv = bordered.convert("RGBA")

        # Shadow
        pad = 14
        shadow = Image.new("RGBA", (cv.width + pad * 2, cv.height + pad * 2),
                           (0, 0, 0, 0))
        sd = ImageDraw.Draw(shadow)
        sd.rectangle((pad, pad + 6, pad + cv.width, pad + cv.height + 6),
                     fill=(0, 0, 0, 180))
        shadow = shadow.filter(ImageFilter.GaussianBlur(8))
        composed = shadow.copy()
        composed.alpha_composite(cv, (pad, pad))

        paste_x = col_center - composed.width // 2
        paste_y = col_top
        canvas.alpha_composite(composed, (paste_x, paste_y))

        # Series kicker
        series_text = book.get("series", "").upper()
        sw, sh = text_size(draw, series_text, series_font)
        cap_y = paste_y + composed.height - pad + 6
        draw.text((col_center - sw // 2, cap_y),
                  series_text, font=series_font, fill=accent)

        # Book title
        title_text_b = book.get("title", "")
        tw, th = text_size(draw, title_text_b, title_card_font)
        title_y = cap_y + sh + 6
        # Auto-shrink if too wide
        font_size = 20
        while font_size > 14:
            f = load_display(font_size, variant="SemiBold")
            tw_check = text_size(draw, title_text_b, f)[0]
            if tw_check <= col_w - 10:
                title_card_font = f
                tw = tw_check
                th = text_size(draw, title_text_b, f)[1]
                break
            font_size -= 1
        draw.text((col_center - tw // 2, title_y),
                  title_text_b, font=title_card_font, fill=BRAND_CREAM)

        # Hook (italic, one or two lines)
        hook = book.get("hook", "")
        hook_y = title_y + th + 6
        # Wrap the hook
        words = hook.split()
        lines = []
        current = []
        for word in words:
            trial = " ".join(current + [word])
            if text_size(draw, trial, hook_font)[0] <= col_w - 10:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]
        if current:
            lines.append(" ".join(current))
        for j, line in enumerate(lines[:2]):
            lw, _ = text_size(draw, line, hook_font)
            draw.text((col_center - lw // 2, hook_y + j * 18),
                      line, font=hook_font, fill=MUTED_LAV)

    return canvas.convert("RGB")


# ─── CLI ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Amazon A+ Content Generator",
    )
    sub = parser.add_subparsers(dest="module", required=True)

    p_comp = sub.add_parser("comparison", help="Catalog comparison chart")
    p_comp.add_argument("--book", required=True)
    p_comp.add_argument("--title", default="More from Alex Savage")
    p_comp.add_argument("--kicker", default="WHERE TO READ NEXT")
    p_comp.add_argument("--tone", choices=["slice_of_life", "action"],
                         default="slice_of_life")
    p_comp.add_argument("-o", "--output", type=Path, default=None)
    p_comp.add_argument("--entry", action="append", default=[],
                         help="Format: 'cover_path||SERIES||Title||Hook' (repeat per book)")

    p_chars = sub.add_parser("characters", help="Character intro trio")
    p_chars.add_argument("--book", required=True)
    p_chars.add_argument("--title", default="Three women. None of them what they seem.")
    p_chars.add_argument("--kicker", default="MEET THE NEIGHBOURS")
    p_chars.add_argument("--tone", choices=["slice_of_life", "action"],
                          default="slice_of_life")
    p_chars.add_argument("-o", "--output", type=Path, default=None)
    # Characters supplied as: --char "path||Descriptor||Punchline" repeatable
    p_chars.add_argument("--char", action="append", default=[],
                          help="Format: 'image_path||Descriptor||Punchline' (repeat 3x)")

    p_reviews = sub.add_parser("reviews", help="Reader Reviews quote card")
    p_reviews.add_argument("--book", required=True)
    p_reviews.add_argument("--title", required=True,
                           help="Book title for the heading, e.g. 'The WarMage of Arkley'")
    p_reviews.add_argument("--tone", choices=["slice_of_life", "action"],
                           default="slice_of_life")
    p_reviews.add_argument("-o", "--output", type=Path, default=None)
    # Reviews supplied as repeated --review "Quote text||Reviewer Name"
    p_reviews.add_argument("--review", action="append", default=[],
                           help="Format: 'Quote text||Reviewer Name' (repeat per review)")

    p_header = sub.add_parser("header", help="Image Header with Text")
    p_header.add_argument("--book", required=True,
                          help="Book key, e.g. wa1, ua1")
    p_header.add_argument("--cover", type=Path, default=None,
                          help="Cover image path (defaults to assets/covers/{book}_hi.jpg)")
    p_header.add_argument("--headline", required=True,
                          help="Headline text (use periods to split into stacked lines)")
    p_header.add_argument("--sub", default="",
                          help="Sub-headline below the main headline")
    p_header.add_argument("--tone", choices=["slice_of_life", "action"],
                          default="slice_of_life",
                          help="Tonal lean (coral-warm vs gold-cool)")
    p_header.add_argument("--variant", choices=["premium", "standard", "tall"],
                          default="premium",
                          help="Amazon A+ module size: premium=1940x600, standard=970x300, tall=970x600")
    p_header.add_argument("-o", "--output", type=Path, default=None)

    args = parser.parse_args()

    if args.module == "comparison":
        entries = []
        for e in args.entry:
            parts = e.split("||")
            if len(parts) < 4:
                sys.exit(f"Bad entry format: {e}")
            entries.append({
                "cover": Path(parts[0].strip()),
                "series": parts[1].strip(),
                "title": parts[2].strip(),
                "hook": parts[3].strip(),
            })
        if not entries:
            sys.exit("Need at least one --entry")
        for e in entries:
            if not e["cover"].exists():
                sys.exit(f"Cover not found: {e['cover']}")

        out = args.output or (ASSETS_DIR / "aplus" / args.book / "03-comparison.jpg")
        out.parent.mkdir(parents=True, exist_ok=True)

        print(f"Alex Savage — A+ Comparison for {args.book}")
        for e in entries:
            print(f"  · {e['title']} ({e['series']})")

        img = render_comparison(args.book, entries,
                                 title_text=args.title,
                                 kicker_text=args.kicker,
                                 tonal_lean=args.tone)
        img.save(out, "JPEG", quality=92, optimize=True, progressive=True)
        print(f"\n  ✓ {out}")
        return

    if args.module == "characters":
        characters = []
        for c in args.char:
            parts = c.split("||")
            if len(parts) < 3:
                sys.exit(f"Bad character format (need 'path||desc||punch'): {c}")
            characters.append({
                "image": Path(parts[0].strip()),
                "descriptor": parts[1].strip(),
                "punchline": parts[2].strip(),
            })
        if not characters:
            sys.exit("Need at least one --char")
        for ch in characters:
            if not ch["image"].exists():
                sys.exit(f"Image not found: {ch['image']}")

        out = args.output or (ASSETS_DIR / "aplus" / args.book / "02-characters.jpg")
        out.parent.mkdir(parents=True, exist_ok=True)

        print(f"Alex Savage — A+ Characters for {args.book}")
        for ch in characters:
            print(f"  · {ch['descriptor']} / {ch['punchline']}")

        img = render_characters(args.book, characters,
                                 title_text=args.title,
                                 kicker_text=args.kicker,
                                 tonal_lean=args.tone)
        img.save(out, "JPEG", quality=92, optimize=True, progressive=True)
        print(f"\n  ✓ {out}")
        return

    if args.module == "reviews":
        reviews = []
        for r in args.review:
            if "||" not in r:
                sys.exit(f"Bad review format (need 'Quote||Name'): {r}")
            quote, name = r.split("||", 1)
            reviews.append({"quote": quote.strip(), "name": name.strip()})
        if not reviews:
            sys.exit("Need at least one --review")

        out = args.output or (ASSETS_DIR / "aplus" / args.book / "04-reviews.jpg")
        out.parent.mkdir(parents=True, exist_ok=True)

        print(f"Alex Savage — A+ Reviews for {args.book}")
        for r in reviews:
            print(f"  · {r['name']}: “{r['quote'][:60]}{'...' if len(r['quote'])>60 else ''}”")

        img = render_reviews(args.title, reviews, tonal_lean=args.tone)
        img.save(out, "JPEG", quality=92, optimize=True, progressive=True)
        print(f"\n  ✓ {out}")
        return

    if args.module == "header":
        cover_path = args.cover or (ASSETS_DIR / "covers" / f"{args.book}_hi.jpg")
        if not cover_path.exists():
            sys.exit(f"Error: cover not found: {cover_path}")

        if args.variant == "standard":
            size = (970, 300)
        elif args.variant == "tall":
            size = (970, 600)
        else:
            size = (1940, 600)
        default_name = ("01-header-standard.jpg" if args.variant == "standard"
                        else "01-header-tall.jpg" if args.variant == "tall"
                        else "01-header.jpg")
        out = args.output or (ASSETS_DIR / "aplus" / args.book / default_name)
        out.parent.mkdir(parents=True, exist_ok=True)

        print(f"Alex Savage — A+ Header for {args.book}")
        print(f"  Cover:    {cover_path.name}")
        print(f"  Headline: {args.headline}")
        print(f"  Sub:      {args.sub}")
        print(f"  Tone:     {args.tone}")
        print(f"  Variant:  {args.variant} ({size[0]}x{size[1]})")

        img = render_header(args.book, cover_path, args.headline,
                            args.sub, tonal_lean=args.tone, size=size)
        img.save(out, "JPEG", quality=92, optimize=True, progressive=True)
        print(f"\n  ✓ {out}")


if __name__ == "__main__":
    main()
