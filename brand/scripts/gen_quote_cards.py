#!/usr/bin/env python3
"""
Alex Savage — Quote Card Generator
Builds branded quote cards for social and inside-book teasers.

Usage:
    python3 gen_quote_cards.py \
        --quote "The wards didn't see him coming. Nothing does." \
        --book "Undercover Archmage" \
        --cover ~/Desktop/ua1.jpg \
        [-o ~/Desktop/quote-cards/]

Or via a YAML/JSON-ish config file (one line per arg):
    python3 gen_quote_cards.py --config quotes/ua1-snake.json

Outputs (in {output_dir}/{slug}/):
    ig-square.jpg       1080×1080   Instagram feed / Facebook square
    ig-story.jpg        1080×1920   Instagram / Facebook stories
    fb-landscape.jpg    1200×630    Facebook link preview / shareable
    teaser-2000.jpg     2000×2000   Inside-book back-matter, high quality

Requires: Pillow  (install: pip3 install Pillow --break-system-packages)
"""

import argparse
import json
import re
import sys
import textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Brand ────────────────────────────────────────────────────────────────
# Mirror of BRAND_FOUNDATION.md — keep in sync.
PRIMARY_DEEP = (22, 12, 36)      # #160C24
SURFACE_1    = (39, 24, 71)      # #271847
BRAND_GOLD   = (232, 183, 86)    # #E8B756
GOLD_SOFT    = (244, 210, 122)   # #F4D27A
BRAND_CORAL  = (255, 126, 148)   # #FF7E94
BRAND_CREAM  = (245, 239, 230)   # #F5EFE6
MUTED_LAV    = (177, 162, 204)   # #B1A2CC

# ─── Fonts ────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
FONT_DIR   = SCRIPT_DIR.parent / "fonts"

FONT_QUOTE   = FONT_DIR / "Fraunces-Italic-VF.ttf"   # italic display for the quote
FONT_DISPLAY = FONT_DIR / "Fraunces-VF.ttf"          # author lockup, headlines
FONT_BODY    = FONT_DIR / "Inter-VF.ttf"             # metadata, CTAs
FONT_ACCENT  = FONT_DIR / "Caveat-Regular.ttf"       # handwritten attribution

# ─── Defaults ─────────────────────────────────────────────────────────────
DEFAULT_AUTHOR = "Alex Savage"
DEFAULT_CTA    = "Available on Kindle Unlimited"

# ─── Output specs ─────────────────────────────────────────────────────────
VARIANTS = [
    {"name": "ig-square",     "size": (1080, 1080), "layout": "square",    "quality": 92},
    {"name": "ig-story",      "size": (1080, 1920), "layout": "portrait",  "quality": 92},
    {"name": "fb-landscape",  "size": (1200, 630),  "layout": "landscape", "quality": 92},
    {"name": "teaser-2000",   "size": (2000, 2000), "layout": "square",    "quality": 94},
]


# ─── Helpers ──────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    return s[:60].strip("-") or "quote"


def load_font(path: Path, size: int, variant: str = None):
    """Load a font. For variable fonts, pass variant name (e.g. 'Italic',
    'SemiBold', 'Regular') to pick a specific instance."""
    f = ImageFont.truetype(str(path), size)
    if variant:
        try:
            f.set_variation_by_name(variant.encode())
        except (OSError, AttributeError):
            pass  # Not a variable font, or variant unavailable — use default
    return f


def load_quote_font(size: int):
    """Quote display — regular italic weight, not the default Black."""
    return load_font(FONT_QUOTE, size, variant="Italic")


def load_display_font(size: int, weight: str = "SemiBold"):
    """Author wordmark, headlines. Default SemiBold matches website spec."""
    return load_font(FONT_DISPLAY, size, variant=weight)


def load_body_font(size: int, weight: str = "Regular"):
    return load_font(FONT_BODY, size, variant=weight)


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    """Return (width, height) of rendered text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_to_width(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wrap text so each line fits within max_width pixels at given font."""
    words = text.split()
    lines, current = [], []
    for word in words:
        trial = " ".join(current + [word])
        w, _ = text_size(draw, trial, font)
        if w <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def make_bg(width: int, height: int) -> Image.Image:
    """Brand-primary background with a subtle radial gold glow top-right."""
    bg = Image.new("RGB", (width, height), PRIMARY_DEEP)
    # Add a soft radial glow in gold
    glow = Image.new("RGB", (width, height), PRIMARY_DEEP)
    gd = ImageDraw.Draw(glow)
    cx, cy = int(width * 0.78), int(height * 0.18)
    max_r = int(max(width, height) * 0.7)
    for r in range(max_r, 0, -max(1, max_r // 60)):
        # Fade gold toward primary-deep
        ratio = r / max_r
        color = (
            int(PRIMARY_DEEP[0] + (BRAND_GOLD[0] - PRIMARY_DEEP[0]) * (1 - ratio) * 0.12),
            int(PRIMARY_DEEP[1] + (BRAND_GOLD[1] - PRIMARY_DEEP[1]) * (1 - ratio) * 0.12),
            int(PRIMARY_DEEP[2] + (BRAND_GOLD[2] - PRIMARY_DEEP[2]) * (1 - ratio) * 0.12),
        )
        gd.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)
    glow = glow.filter(ImageFilter.GaussianBlur(radius=80))
    return Image.blend(bg, glow, 0.45)


def fit_cover(cover_path: Path, target_w: int, target_h: int) -> Image.Image:
    """Load a cover and fit-to-cover-crop to target dimensions."""
    src = Image.open(cover_path).convert("RGB")
    src_ratio = src.width / src.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        # source wider — crop sides
        new_w = int(src.height * target_ratio)
        offset = (src.width - new_w) // 2
        src = src.crop((offset, 0, offset + new_w, src.height))
    else:
        new_h = int(src.width / target_ratio)
        offset = (src.height - new_h) // 4  # bias upward — keeps title visible
        src = src.crop((0, offset, src.width, offset + new_h))
    return src.resize((target_w, target_h), Image.LANCZOS)


def draw_underline(draw, x_center, y, width, color=BRAND_GOLD, thickness=2):
    draw.line(
        [(x_center - width // 2, y), (x_center + width // 2, y)],
        fill=color, width=thickness,
    )


# ─── Layouts ──────────────────────────────────────────────────────────────

def render_square(spec, quote, book, author, cta, cover_path):
    """Square layout — for IG square (1080) and teaser (2000)."""
    W, H = spec["size"]
    scale = W / 1080  # all dimensions scale from the 1080 reference
    img = make_bg(W, H)
    draw = ImageDraw.Draw(img)

    pad = int(80 * scale)
    quoted = f"“{quote}”"   # proper curly opening/closing quotes inline

    # — Author wordmark at top —
    author_font = load_display_font(int(36 * scale))
    aw, ah = text_size(draw, author, author_font)
    author_y = int(pad)
    draw.text(((W - aw) // 2, author_y), author, font=author_font, fill=BRAND_CREAM)
    draw_underline(draw, W // 2, author_y + ah + int(14 * scale),
                   int(aw * 0.55), color=BRAND_GOLD, thickness=max(1, int(2 * scale)))

    # — Cover thumbnail bottom-left —
    thumb_h = int(280 * scale)
    thumb_w = int(thumb_h / 1.6)
    thumb = fit_cover(cover_path, thumb_w, thumb_h)
    thumb_x = pad
    thumb_y = H - pad - thumb_h
    shadow = Image.new("RGBA", (thumb_w + 16, thumb_h + 16), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle((8, 8, thumb_w + 8, thumb_h + 8), fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8))
    img.paste(shadow, (thumb_x - 8, thumb_y - 4), shadow)
    img.paste(thumb, (thumb_x, thumb_y))

    # — CTA bottom-right —
    cta_x_start = thumb_x + thumb_w + int(40 * scale)
    cta_label_font = load_body_font(int(20 * scale), "Medium")
    cta_main_font  = load_display_font(int(34 * scale))

    draw.text(
        (cta_x_start, thumb_y + int(50 * scale)),
        "READ NOW",
        font=cta_label_font, fill=BRAND_GOLD,
    )
    cta_lines = wrap_to_width(cta, cta_main_font, W - cta_x_start - pad, draw)
    cy = thumb_y + int(90 * scale)
    for line in cta_lines:
        draw.text((cta_x_start, cy), line, font=cta_main_font, fill=BRAND_CREAM)
        cy += int(46 * scale)

    # — Quote area (between author at top and bottom strip) —
    quote_top = author_y + ah + int(60 * scale)
    quote_bottom = thumb_y - int(60 * scale)
    quote_max_w = W - 2 * pad

    # Find font size that fits the quote
    quote_size = int(60 * scale)
    while quote_size > int(28 * scale):
        qfont = load_quote_font(quote_size)
        lines = wrap_to_width(quoted, qfont, quote_max_w, draw)
        line_h = int(quote_size * 1.3)
        total_h = line_h * len(lines)
        book_font = load_font(FONT_ACCENT, max(int(40 * scale), int(quote_size * 0.7)))
        bw, bh = text_size(draw, f"— {book}", book_font)
        block_h = total_h + int(36 * scale) + bh
        if block_h <= (quote_bottom - quote_top):
            break
        quote_size -= 4

    qfont = load_quote_font(quote_size)
    lines = wrap_to_width(quoted, qfont, quote_max_w, draw)
    line_h = int(quote_size * 1.3)
    block_h = line_h * len(lines)
    book_font = load_font(FONT_ACCENT, max(int(40 * scale), int(quote_size * 0.7)))
    bw, bh = text_size(draw, f"— {book}", book_font)
    full_block_h = block_h + int(36 * scale) + bh

    start_y = quote_top + (quote_bottom - quote_top - full_block_h) // 2

    for i, line in enumerate(lines):
        lw, _ = text_size(draw, line, qfont)
        draw.text(((W - lw) // 2, start_y + i * line_h), line, font=qfont, fill=BRAND_CREAM)

    # Book attribution (handwritten, coral)
    attribution = f"— {book}"
    aw2, _ = text_size(draw, attribution, book_font)
    draw.text(((W - aw2) // 2, start_y + block_h + int(36 * scale)),
              attribution, font=book_font, fill=BRAND_CORAL)

    return img


def render_portrait(spec, quote, book, author, cta, cover_path):
    """Portrait/story layout — 1080×1920. More vertical breathing room."""
    W, H = spec["size"]
    img = make_bg(W, H)
    draw = ImageDraw.Draw(img)

    pad = 80
    quoted = f"“{quote}”"

    # — Author wordmark top —
    author_font = load_display_font(40)
    aw, ah = text_size(draw, author, author_font)
    author_y = pad + 60
    draw.text(((W - aw) // 2, author_y), author, font=author_font, fill=BRAND_CREAM)
    draw_underline(draw, W // 2, author_y + ah + 16, int(aw * 0.55), BRAND_GOLD, 2)

    # — Cover thumbnail center, generous size for stories —
    thumb_h = 540
    thumb_w = int(thumb_h / 1.6)
    thumb = fit_cover(cover_path, thumb_w, thumb_h)
    thumb_x = (W - thumb_w) // 2
    thumb_y = H - pad - 380 - thumb_h
    shadow = Image.new("RGBA", (thumb_w + 24, thumb_h + 24), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle((12, 12, thumb_w + 12, thumb_h + 12), fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    img.paste(shadow, (thumb_x - 12, thumb_y - 6), shadow)
    img.paste(thumb, (thumb_x, thumb_y))

    # — Book title beneath thumb —
    book_font = load_font(FONT_ACCENT, 64)
    bw, bh = text_size(draw, book, book_font)
    book_y = thumb_y + thumb_h + 40
    draw.text(((W - bw) // 2, book_y), book, font=book_font, fill=BRAND_CORAL)

    # — CTA below book title —
    cta_label_font = load_body_font(22, "Medium")
    cta_main_font  = load_display_font(40)

    cl_w, cl_h = text_size(draw, "READ NOW", cta_label_font)
    label_y = book_y + bh + 36
    draw.text(((W - cl_w) // 2, label_y), "READ NOW", font=cta_label_font, fill=BRAND_GOLD)

    cta_lines = wrap_to_width(cta, cta_main_font, W - 2 * pad, draw)
    cy = label_y + cl_h + 8
    for line in cta_lines:
        lw, lh = text_size(draw, line, cta_main_font)
        draw.text(((W - lw) // 2, cy), line, font=cta_main_font, fill=BRAND_CREAM)
        cy += int(40 * 1.2)

    # — Quote area in the top half —
    quote_top = author_y + ah + 80
    quote_bottom = thumb_y - 40
    quote_max_w = W - 2 * pad

    quote_size = 68
    while quote_size > 32:
        qfont = load_quote_font(quote_size)
        lines = wrap_to_width(quoted, qfont, quote_max_w, draw)
        line_h = int(quote_size * 1.3)
        if line_h * len(lines) <= (quote_bottom - quote_top):
            break
        quote_size -= 4

    qfont = load_quote_font(quote_size)
    lines = wrap_to_width(quoted, qfont, quote_max_w, draw)
    line_h = int(quote_size * 1.3)
    block_h = line_h * len(lines)
    start_y = quote_top + (quote_bottom - quote_top - block_h) // 2

    for i, line in enumerate(lines):
        lw, _ = text_size(draw, line, qfont)
        draw.text(((W - lw) // 2, start_y + i * line_h), line, font=qfont, fill=BRAND_CREAM)

    return img


def render_landscape(spec, quote, book, author, cta, cover_path):
    """Landscape layout — 1200×630. Cover on the left, text on the right."""
    W, H = spec["size"]
    img = make_bg(W, H)
    draw = ImageDraw.Draw(img)

    pad = 40
    quoted = f"“{quote}”"

    # — Cover thumbnail on left —
    thumb_h = H - 2 * pad
    thumb_w = int(thumb_h / 1.6)
    thumb = fit_cover(cover_path, thumb_w, thumb_h)
    thumb_x = pad
    thumb_y = pad
    shadow = Image.new("RGBA", (thumb_w + 20, thumb_h + 20), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle((10, 10, thumb_w + 10, thumb_h + 10), fill=(0, 0, 0, 160))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    img.paste(shadow, (thumb_x - 10, thumb_y - 4), shadow)
    img.paste(thumb, (thumb_x, thumb_y))

    # — Right side: text block —
    text_x = thumb_x + thumb_w + 50
    text_w = W - text_x - pad

    # Author wordmark at top right
    author_font = load_display_font(28)
    aw, ah = text_size(draw, author, author_font)
    draw.text((text_x, pad + 10), author, font=author_font, fill=BRAND_CREAM)
    draw_underline(draw, text_x + aw // 2, pad + 10 + ah + 10, int(aw * 0.7),
                   BRAND_GOLD, 2)

    # Quote in the middle
    quote_top = pad + 70
    quote_bottom = H - pad - 100

    quote_size = 38
    while quote_size > 20:
        qfont = load_quote_font(quote_size)
        lines = wrap_to_width(quoted, qfont, text_w, draw)
        line_h = int(quote_size * 1.3)
        if line_h * len(lines) <= (quote_bottom - quote_top):
            break
        quote_size -= 2

    qfont = load_quote_font(quote_size)
    lines = wrap_to_width(quoted, qfont, text_w, draw)
    line_h = int(quote_size * 1.3)
    block_h = line_h * len(lines)
    start_y = quote_top + (quote_bottom - quote_top - block_h) // 2

    for i, line in enumerate(lines):
        draw.text((text_x, start_y + i * line_h), line, font=qfont, fill=BRAND_CREAM)

    # Book attribution and CTA at bottom right
    book_font = load_font(FONT_ACCENT, 32)
    draw.text((text_x, H - pad - 70), f"— {book}", font=book_font, fill=BRAND_CORAL)
    cta_font = load_body_font(14, "Medium")
    draw.text((text_x, H - pad - 28), cta.upper(),
              font=cta_font, fill=BRAND_GOLD)

    return img


LAYOUTS = {
    "square":    render_square,
    "portrait":  render_portrait,
    "landscape": render_landscape,
}


def process(quote: str, book: str, cover_path: Path,
            author: str, cta: str, output_dir: Path) -> None:
    slug = slugify(book + "-" + quote.split()[0])
    out = output_dir / slug
    out.mkdir(parents=True, exist_ok=True)

    print(f"\n  Quote: {quote[:60]}{'...' if len(quote) > 60 else ''}")
    print(f"  Book:  {book}")
    print(f"  Cover: {cover_path.name}")
    print(f"  → {out}/")

    for variant in VARIANTS:
        layout_fn = LAYOUTS[variant["layout"]]
        img = layout_fn(variant, quote, book, author, cta, cover_path)
        out_path = out / f"{variant['name']}.jpg"
        img.save(out_path, "JPEG", quality=variant["quality"],
                 optimize=True, progressive=True)
        w, h = variant["size"]
        print(f"    ✓ {variant['name']:14s} {w}×{h}")


def main():
    parser = argparse.ArgumentParser(
        description="Alex Savage — Quote Card Generator",
    )
    parser.add_argument("--quote", help="The quote text")
    parser.add_argument("--book", help="Book title for attribution")
    parser.add_argument("--cover", type=Path, help="Path to cover image")
    parser.add_argument("--author", default=DEFAULT_AUTHOR, help="Author name")
    parser.add_argument("--cta", default=DEFAULT_CTA, help="Call to action text")
    parser.add_argument("--config", type=Path,
                        help="JSON config file (overrides individual flags)")
    parser.add_argument("-o", "--output", type=Path, default=Path("."),
                        help="Output directory (default: current dir)")
    args = parser.parse_args()

    # Load from config if provided
    if args.config:
        with args.config.open() as f:
            cfg = json.load(f)
        quote = cfg.get("quote") or args.quote
        book = cfg.get("book") or args.book
        cover = Path(cfg.get("cover")) if cfg.get("cover") else args.cover
        author = cfg.get("author", args.author)
        cta = cfg.get("cta", args.cta)
    else:
        quote = args.quote
        book = args.book
        cover = args.cover
        author = args.author
        cta = args.cta

    if not (quote and book and cover):
        sys.exit("Error: --quote, --book, and --cover are required "
                 "(or pass a --config file containing all three).")

    if not cover.exists():
        sys.exit(f"Error: cover '{cover}' not found")

    args.output.mkdir(parents=True, exist_ok=True)

    print("Alex Savage — Quote Card Generator")
    process(quote, book, cover, author, cta, args.output)
    print("\nDone.")


if __name__ == "__main__":
    main()
