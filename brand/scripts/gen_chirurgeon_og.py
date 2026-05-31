#!/usr/bin/env python3
"""
Chirurgeon — Open Graph / social-preview image (1200x630), parity with
assets/og/og-series-warmage.jpg. Cover-led, garnet anchor. Reuses the same
gen_aplus_premium helpers as the A+ set so type/grain/shadow match.

Outputs:
    assets/og/og-series-chirurgeon.jpg
    assets/og/og-series-chirurgeon.webp
    assets/covers/chir_hi.webp           (cover parity with wa1_hi.webp)
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from gen_aplus_premium import (            # noqa: E402
    make_grain_bg, make_cover_with_layered_shadow, draw_refined_rule,
    add_edge_vignette, load_display, load_italic, load_body,
    text_size, BRAND_CREAM, BRAND_CREAM_DEEP, MUTED_LAV,
)

ASSETS = SCRIPT_DIR.parent.parent / "assets"
COVERS = ASSETS / "covers"
OG     = ASSETS / "og"
OG.mkdir(parents=True, exist_ok=True)

CHIR_COVER = COVERS / "chir.jpg"

GARNET        = (139, 46, 60)     # #8B2E3C
GARNET_BRIGHT = (196, 78, 96)     # #C44E60
GARNET_GLINT  = (224, 122, 138)   # #E07A8A

KICKER_A = "PROGRESSION FANTASY"
KICKER_B = "ISEKAI  ·  HAREMLIT"
HOOK     = "Another world. Same bad shift."
TAGLINE  = ("A Pittsburgh ER nurse, yanked into a dying world mid-trauma — a "
            "system bracer on his wrist, a free company at his back, and three "
            "women who each decide he's theirs to keep alive.")


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], []
    for w in words:
        if text_size(draw, " ".join(cur + [w]), font)[0] <= max_w:
            cur.append(w)
        else:
            lines.append(" ".join(cur)); cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _headline_beats(draw, text_x, top, parts, font, line_h):
    for i, ln in enumerate(parts):
        fill = GARNET_BRIGHT if (i == len(parts) - 1 and len(parts) > 1) else BRAND_CREAM
        draw.text((text_x, top + i * line_h), ln + ".", font=font, fill=fill)


def render_og():
    W, H = 1200, 630
    canvas = make_grain_bg(W, H, glow_color=GARNET, glow_anchor=(0.82, 0.18),
                           glow_strength=0.20, grain=8, seed=23)
    canvas = add_edge_vignette(canvas, strength=0.42).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    cover_pkg = make_cover_with_layered_shadow(CHIR_COVER, int(H * 0.82), tilt=-2)
    cover_x = 48
    canvas.alpha_composite(cover_pkg, (cover_x, (H - cover_pkg.height) // 2))

    text_x = cover_x + cover_pkg.width + 40
    avail = W - text_x - 60

    wm_font = load_display(36, variant="SemiBold")
    wm_y = int(H * 0.16)
    draw.text((text_x, wm_y), "Alex Savage", font=wm_font, fill=BRAND_CREAM)
    wmw, wmh = text_size(draw, "Alex Savage", wm_font)
    draw.ellipse((text_x - 16, wm_y + wmh // 2 - 4, text_x - 8, wm_y + wmh // 2 + 4),
                 fill=GARNET_BRIGHT)
    ruley = wm_y + wmh + 10
    draw_refined_rule(draw, text_x, ruley, int(wmw * 0.6), GARNET,
                      cap_color=GARNET_GLINT, thickness=2)
    draw.text((text_x, ruley + 14), f"{KICKER_A}   ·   {KICKER_B}",
              font=load_body(13, variant="SemiBold"), fill=GARNET_BRIGHT)

    parts = [p.strip() for p in HOOK.split(".") if p.strip()]
    hs = 78
    while hs > 36:
        f = load_display(hs, variant="SemiBold")
        if max(text_size(draw, p + ".", f)[0] for p in parts) <= avail:
            break
        hs -= 3
    f = load_display(hs, variant="SemiBold")
    line_h = int(hs * 1.04)
    hy = ruley + 54
    _headline_beats(draw, text_x, hy, parts, f, line_h)

    sf = load_italic(20, variant="Italic")
    sub_y = hy + line_h * len(parts) + 20
    for i, ln in enumerate(_wrap(draw, TAGLINE, sf, avail)[:5]):
        draw.text((text_x, sub_y + i * int(20 * 1.4)), ln, font=sf, fill=MUTED_LAV)
    return canvas.convert("RGB")


if __name__ == "__main__":
    og = render_og()
    jpg = OG / "og-series-chirurgeon.jpg"
    webp = OG / "og-series-chirurgeon.webp"
    og.save(jpg, "JPEG", quality=88, optimize=True)
    og.save(webp, "WEBP", quality=82, method=6)
    print("wrote", jpg.name, og.size)
    print("wrote", webp.name)

    # cover parity: chir_hi.webp from the hi-res jpg
    hi = COVERS / "chir_hi.jpg"
    if hi.exists():
        im = Image.open(hi).convert("RGB")
        im.thumbnail((1600, 2400), Image.LANCZOS)
        im.save(COVERS / "chir_hi.webp", "WEBP", quality=82, method=6)
        print("wrote chir_hi.webp", im.size)
