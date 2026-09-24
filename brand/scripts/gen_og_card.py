#!/usr/bin/env python3
"""
Generic Open Graph card (1200x630) in the gen_chirurgeon_og.py house style:
cover left with layered shadow, "Alex Savage" wordmark, kicker, two-beat hook
(last beat in the series colour), italic tagline.

Add or edit a card in CARDS, then run:
    python3 brand/scripts/gen_og_card.py            # all cards
    python3 brand/scripts/gen_og_card.py chir2 mgs  # just these
"""
import sys
from pathlib import Path
from PIL import ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from gen_aplus_premium import (  # noqa: E402
    make_grain_bg, make_cover_with_layered_shadow, draw_refined_rule,
    add_edge_vignette, load_display, load_italic, load_body,
    text_size, BRAND_CREAM, MUTED_LAV,
)

ASSETS = SCRIPT_DIR.parent.parent / "assets"
COVERS, OG = ASSETS / "covers", ASSETS / "og"

GARNET = ((139, 46, 60), (196, 78, 96), (224, 122, 138))
EMBER = ((168, 64, 26), (224, 103, 43), (240, 150, 100))
BOURBON = ((184, 116, 31), (224, 154, 60), (243, 199, 126))

CARDS = {
    "og-series-chirurgeon": dict(
        cover="chir.jpg", pal=GARNET, kicker="PROGRESSION FANTASY   ·   ISEKAI  ·  HAREMLIT",
        hook="Another world. Same bad shift.",
        tagline=("A Pittsburgh ER nurse, yanked into a dying world mid-trauma, with a "
                 "system bracer on his wrist, a free company at his back, and three "
                 "women who each decide he's theirs to keep alive.")),
    "og-chirurgeon-2": dict(
        cover="chir2.jpg", pal=GARNET, kicker="CHIRURGEON 2   ·   PROGRESSION FANTASY",
        hook="He says who burns. No pressure.",
        tagline=("Forty thousand people behind a quarantine wall. Creatures wearing them "
                 "like coats. And a Witch Hunter whose only cure for all this is fire.")),
    "og-series-monster-girl-sheriff": dict(
        cover="mgs.jpg", pal=EMBER, kicker="SMALL TOWN   ·   MONSTER GIRL  ·  HAREM LITRPG",
        hook="Seven sheriffs. Six in the ground.",
        tagline=("A repo man takes the badge of a town built round a hellmouth, three "
                 "days before the Tallyman comes to collect what the town owes.")),
    "og-accidental-succubus-wrangler-2": dict(
        cover="asw2.jpg", pal=BOURBON, kicker="MONSTER GIRL   ·   HAREM COMEDY FOR MEN",
        hook="Sixteen days. Four succubi.",
        tagline=("Three succubi now with his surname, a warrant nailed to his bar's door, "
                 "and Hell's most implacable Hunter lodging up the street.")),
}


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


def render(cover, pal, kicker, hook, tagline):
    base, bright, glint = pal
    W, H = 1200, 630
    canvas = make_grain_bg(W, H, glow_color=base, glow_anchor=(0.82, 0.18),
                           glow_strength=0.20, grain=8, seed=23)
    canvas = add_edge_vignette(canvas, strength=0.42).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    pkg = make_cover_with_layered_shadow(COVERS / cover, int(H * 0.82), tilt=-2)
    canvas.alpha_composite(pkg, (48, (H - pkg.height) // 2))
    text_x = 48 + pkg.width + 40
    avail = W - text_x - 60

    wm_font = load_display(36, variant="SemiBold")
    wm_y = int(H * 0.16)
    draw.text((text_x, wm_y), "Alex Savage", font=wm_font, fill=BRAND_CREAM)
    wmw, wmh = text_size(draw, "Alex Savage", wm_font)
    draw.ellipse((text_x - 16, wm_y + wmh // 2 - 4, text_x - 8, wm_y + wmh // 2 + 4), fill=bright)
    ruley = wm_y + wmh + 10
    draw_refined_rule(draw, text_x, ruley, int(wmw * 0.6), base, cap_color=glint, thickness=2)
    draw.text((text_x, ruley + 14), kicker, font=load_body(13, variant="SemiBold"), fill=bright)

    parts = [p.strip() for p in hook.split(".") if p.strip()]
    hs = 78
    while hs > 36:
        f = load_display(hs, variant="SemiBold")
        if max(text_size(draw, p + ".", f)[0] for p in parts) <= avail:
            break
        hs -= 3
    f = load_display(hs, variant="SemiBold")
    line_h = int(hs * 1.04)
    hy = ruley + 54
    for i, ln in enumerate(parts):
        draw.text((text_x, hy + i * line_h), ln + ".", font=f,
                  fill=bright if (i == len(parts) - 1 and len(parts) > 1) else BRAND_CREAM)

    sf = load_italic(20, variant="Italic")
    sub_y = hy + line_h * len(parts) + 20
    for i, ln in enumerate(_wrap(draw, tagline, sf, avail)[:5]):
        draw.text((text_x, sub_y + i * 28), ln, font=sf, fill=MUTED_LAV)
    return canvas.convert("RGB")


if __name__ == "__main__":
    for name in (sys.argv[1:] or CARDS):
        img = render(**CARDS[name])
        img.save(OG / f"{name}.jpg", "JPEG", quality=88, optimize=True)
        img.save(OG / f"{name}.webp", "WEBP", quality=82, method=6)
        print("wrote", name)
