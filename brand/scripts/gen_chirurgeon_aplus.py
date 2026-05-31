#!/usr/bin/env python3
"""
Chirurgeon — A+ / banner pass (Alex Savage house style), modeled on the
WarMage (wa1) and Undercover Archmage (ua1) A+ sets.

Cover-led now that the cover exists (assets/covers/chir.jpg). Series anchor:
GARNET / blood-red #8B2E3C (logged in BRAND_FOUNDATION.md).

Modules:
    01-header        970x300   cover-led header  (like wa1/01-header)
    01-hero          970x600   cover-led hero
    02-characters    970x600   character trio    (drop 3 profiles in source/)
    02-whats-inside  970x600   trope grid (used until reviews exist)
    03-more-from     970x600   "More from Alex Savage" — real UA/WA covers
    social-reddit    1280x384  social banner

Reuses gen_aplus_premium helpers verbatim so grain/shadow/type all match.
Three profile images go in: assets/aplus/chir/source/  named li1.* li2.* li3.*
(any of .png .jpg .jpeg .webp). Re-run and the characters module builds.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from gen_aplus_premium import (            # noqa: E402
    make_grain_bg, make_cover_with_layered_shadow, layered_shadow_mask,
    draw_refined_rule, add_edge_vignette, load_display, load_italic, load_body,
    text_size, text_w, BRAND_CREAM, BRAND_CREAM_DEEP, MUTED_LAV, SHADOW_PURPLE,
)

ASSETS = SCRIPT_DIR.parent.parent / "assets"
COVERS = ASSETS / "covers"
OUT    = ASSETS / "aplus" / "chir"
SRC    = OUT / "source"
OUT.mkdir(parents=True, exist_ok=True)
SRC.mkdir(parents=True, exist_ok=True)

CHIR_COVER = COVERS / "chir.jpg"

# ─── Chirurgeon series anchor — GARNET ───────────────────────────────────────
GARNET        = (139, 46, 60)     # #8B2E3C  anchor: rules, strips
GARNET_BRIGHT = (196, 78, 96)     # #C44E60  lifted accent text
GARNET_GLINT  = (224, 122, 138)   # ornament caps

KICKER_A = "PROGRESSION FANTASY"
KICKER_B = "ISEKAI  ·  HAREMLIT"
HOOK     = "Another world. Same bad shift."
TAGLINE  = ("A Pittsburgh ER nurse, yanked into a dying world mid-trauma — a "
           "system bracer on his wrist, a free company at his back, and three "
           "women who each decide he's theirs to keep alive.")
TAGLINE_SHORT = ("A combat medic in the wrong world, a system bracer, and three "
                "women who won't share him.")


def _wordmark_block(canvas, draw, x, y_center):
    wm_font = load_display(22, variant="SemiBold")
    wmh = text_size(draw, "Savage", wm_font)[1]
    kfont = load_body(9, variant="SemiBold")
    kh = text_size(draw, KICKER_A, kfont)[1]
    stack_h = wmh * 2 + 6 + 14 + 12 + (kh + 4) * 2
    top = y_center - stack_h // 2
    yy = top
    for ln in ("Alex", "Savage"):
        draw.text((x, yy), ln, font=wm_font, fill=BRAND_CREAM, anchor="lt"); yy += wmh + 6
    yy += 6
    draw_refined_rule(draw, x, yy, 46, GARNET, cap_color=GARNET_GLINT, thickness=2)
    yy += 12
    for ln in (KICKER_A, KICKER_B):
        draw.text((x, yy), ln, font=kfont, fill=GARNET_BRIGHT, anchor="lt"); yy += kh + 4


def _headline_beats(draw, text_x, top, parts, font, line_h):
    for i, ln in enumerate(parts):
        fill = GARNET_BRIGHT if (i == len(parts) - 1 and len(parts) > 1) else BRAND_CREAM
        draw.text((text_x, top + i * line_h), ln + ".", font=font, fill=fill)


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


# ─── 01 — Header 970x300 (cover-led) ─────────────────────────────────────────
def render_header():
    W, H = 970, 300
    canvas = make_grain_bg(W, H, glow_color=GARNET, glow_anchor=(0.90, 0.12),
                           glow_strength=0.18, grain=5, seed=11).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    cover_pkg = make_cover_with_layered_shadow(CHIR_COVER, int(H * 0.84), tilt=-2)
    cover_x = 16
    canvas.alpha_composite(cover_pkg, (cover_x, (H - cover_pkg.height) // 2))

    BRAND_W = 168
    brand_x = W - BRAND_W + 8
    draw.line([(brand_x, 48), (brand_x, H - 48)], fill=GARNET, width=1)
    for yy in (48, H - 48):
        draw.ellipse((brand_x - 3, yy - 3, brand_x + 3, yy + 3), fill=GARNET_GLINT)
    _wordmark_block(canvas, draw, brand_x + 22, H // 2)

    text_x = cover_x + cover_pkg.width + 14
    avail = brand_x - text_x - 20
    parts = [p.strip() for p in HOOK.split(".") if p.strip()]
    hs = 42
    while hs > 22:
        f = load_display(hs, variant="SemiBold")
        if max(text_size(draw, p + ".", f)[0] for p in parts) <= avail:
            break
        hs -= 2
    f = load_display(hs, variant="SemiBold")
    line_h = int(hs * 1.05)
    block_h = line_h * len(parts)
    hy = (H - block_h) // 2 - 18
    _headline_beats(draw, text_x, hy, parts, f, line_h)

    sf = load_body(12, variant="Medium")
    for i, ln in enumerate(_wrap(draw, TAGLINE_SHORT, sf, avail)[:2]):
        draw.text((text_x, hy + block_h + 12 + i * 17), ln, font=sf,
                  fill=BRAND_CREAM_DEEP, anchor="lt")
    return canvas.convert("RGB")


# ─── 01b — Hero 970x600 (cover-led) ──────────────────────────────────────────
def render_hero():
    W, H = 970, 600
    canvas = make_grain_bg(W, H, glow_color=GARNET, glow_anchor=(0.82, 0.18),
                           glow_strength=0.20, grain=8, seed=23)
    canvas = add_edge_vignette(canvas, strength=0.42).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    cover_pkg = make_cover_with_layered_shadow(CHIR_COVER, int(H * 0.82), tilt=-2)
    cover_x = 30
    canvas.alpha_composite(cover_pkg, (cover_x, (H - cover_pkg.height) // 2))

    text_x = cover_x + cover_pkg.width + 26
    avail = W - text_x - 50

    wm_font = load_display(34, variant="SemiBold")
    wm_y = int(H * 0.15)
    draw.text((text_x, wm_y), "Alex Savage", font=wm_font, fill=BRAND_CREAM)
    wmw, wmh = text_size(draw, "Alex Savage", wm_font)
    draw.ellipse((text_x - 16, wm_y + wmh // 2 - 4, text_x - 8, wm_y + wmh // 2 + 4),
                 fill=GARNET_BRIGHT)
    ruley = wm_y + wmh + 10
    draw_refined_rule(draw, text_x, ruley, int(wmw * 0.6), GARNET,
                      cap_color=GARNET_GLINT, thickness=2)
    draw.text((text_x, ruley + 14), f"{KICKER_A}   ·   {KICKER_B}",
              font=load_body(12, variant="SemiBold"), fill=GARNET_BRIGHT)

    parts = [p.strip() for p in HOOK.split(".") if p.strip()]
    hs = 72
    while hs > 34:
        f = load_display(hs, variant="SemiBold")
        if max(text_size(draw, p + ".", f)[0] for p in parts) <= avail:
            break
        hs -= 3
    f = load_display(hs, variant="SemiBold")
    line_h = int(hs * 1.04)
    hy = ruley + 50
    _headline_beats(draw, text_x, hy, parts, f, line_h)

    sf = load_italic(19, variant="Italic")
    sub_y = hy + line_h * len(parts) + 18
    for i, ln in enumerate(_wrap(draw, TAGLINE, sf, avail)[:5]):
        draw.text((text_x, sub_y + i * int(19 * 1.4)), ln, font=sf, fill=MUTED_LAV)
    return canvas.convert("RGB")


# ─── 02 — Character trio 970x600 (modeled on wa1/02-characters) ───────────────
CHARS = [
    ("The Front-Rank.",  "Goes through the door first."),
    ("The reader.",      "Knows what you are."),
    ("The scout.",       "You never hear her coming."),
]

def _find_profile(stem):
    for ext in (".png", ".jpg", ".jpeg", ".webp"):
        p = SRC / f"{stem}{ext}"
        if p.exists():
            return p
    return None

def render_characters():
    profiles = [_find_profile(s) for s in ("li1", "li2", "li3")]
    if not all(profiles):
        print("  · characters: drop li1/li2/li3 images in", SRC, "— skipped")
        return None
    W, H = 970, 600
    canvas = make_grain_bg(W, H, glow_color=GARNET, glow_anchor=(0.5, 0.10),
                           glow_strength=0.16, grain=6, seed=44).convert("RGBA")
    draw = ImageDraw.Draw(canvas)

    kf = load_body(15, variant="SemiBold")
    k = "THE THREE WHO KEEP HIM"
    kw = text_size(draw, k, kf)[0]
    ky = int(H * 0.06)
    draw.text(((W - kw) // 2, ky), k, font=kf, fill=GARNET_BRIGHT)
    tf = load_display(38, variant="SemiBold")
    tt = "Three women. None of them sharing."
    tw, th = text_size(draw, tt, tf)
    ty = ky + text_size(draw, "X", kf)[1] + 10
    draw.text(((W - tw) // 2, ty), tt, font=tf, fill=BRAND_CREAM)
    ruley = ty + th + 14
    draw.line([((W - 80) // 2, ruley), ((W + 80) // 2, ruley)], fill=GARNET, width=2)

    n = 3
    side, gap = int(W * 0.06), int(W * 0.04)
    col_w = (W - 2 * side - (n - 1) * gap) // n
    photo_w = col_w
    photo_h = int(photo_w * 1.18)
    top = ruley + 34
    name_font = load_display(20, variant="SemiBold")
    sub_font = load_italic(15, variant="Italic")
    for i, (path, (name, sub)) in enumerate(zip(profiles, CHARS)):
        cx = side + i * (col_w + gap)
        ccx = cx + col_w // 2
        photo = Image.open(path).convert("RGB")
        # cover-crop to portrait
        r = max(photo_w / photo.width, photo_h / photo.height)
        photo = photo.resize((int(photo.width * r), int(photo.height * r)), Image.LANCZOS)
        L = (photo.width - photo_w) // 2
        T = int((photo.height - photo_h) * 0.18)
        photo = photo.crop((L, T, L + photo_w, T + photo_h))
        bordered = Image.new("RGB", (photo_w + 4, photo_h + 4), BRAND_CREAM)
        bordered.paste(photo, (2, 2))
        bv = bordered.convert("RGBA")
        sh, pad = layered_shadow_mask(bv.width, bv.height, passes=((2, 4, 4, 90), (8, 12, 16, 130)))
        canvas.alpha_composite(sh, (cx - pad[0], top - pad[1]))
        canvas.alpha_composite(bv, (cx, top))
        cap_y = top + photo_h + 12
        nw = text_size(draw, name, name_font)[0]
        draw.text((ccx - nw // 2, cap_y), name, font=name_font, fill=BRAND_CREAM)
        sw = text_size(draw, sub, sub_font)[0]
        draw.text((ccx - sw // 2, cap_y + 26), sub, font=sub_font, fill=GARNET_BRIGHT)
    return canvas.convert("RGB")


# ─── 02 (fallback) — What's inside / trope grid ──────────────────────────────
TROPES = [
    ("ISEKAI", "Pulled through mid-shift, hands already in the wound."),
    ("COMBAT-MEDIC MC", "He doesn't out-fight them. He out-works them."),
    ("SYSTEM BRACER", "A progression that levels by saving lives."),
    ("THREE LOVE INTERESTS", "A warrior, a reader, a scout. None of them share."),
    ("GRIMDARK STAKES", "A wound in the world, and a clock counting down to fire."),
    ("SLOW BURN, THEN FAST", "Earned chemistry, then it lands all at once."),
]

def render_whats_inside():
    W, H = 970, 600
    canvas = make_grain_bg(W, H, glow_color=GARNET, glow_anchor=(0.5, 0.12),
                           glow_strength=0.16, grain=6, seed=41).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    kf = load_body(15, variant="SemiBold")
    kw = text_size(draw, "WHAT YOU'RE GETTING", kf)[0]
    draw.text(((W - kw) // 2, int(H * 0.06)), "WHAT YOU'RE GETTING", font=kf, fill=GARNET_BRIGHT)
    tf = load_display(40, variant="SemiBold")
    tt = "Competence, chemistry, and a body count."
    tw, th = text_size(draw, tt, tf)
    ty = int(H * 0.06) + text_size(draw, "X", kf)[1] + 10
    draw.text(((W - tw) // 2, ty), tt, font=tf, fill=BRAND_CREAM)
    ruley = ty + th + 16
    draw.line([((W - 90) // 2, ruley), ((W + 90) // 2, ruley)], fill=GARNET, width=2)
    cols, rows = 2, 3
    mx, gx, gy = 70, 40, 26
    top = ruley + 40
    cw = (W - 2 * mx - (cols - 1) * gx) // cols
    ch = (H - top - 50 - (rows - 1) * gy) // rows
    lab = load_display(23, variant="SemiBold")
    bod = load_body(14, variant="Regular")
    for i, (label, body) in enumerate(TROPES):
        cx = mx + (i % cols) * (cw + gx)
        cy = top + (i // cols) * (ch + gy)
        draw.rectangle((cx, cy + 4, cx + 4, cy + 26), fill=GARNET)
        draw.text((cx + 16, cy), label, font=lab, fill=BRAND_CREAM, anchor="lt")
        lh = text_size(draw, label, lab)[1]
        for j, ln in enumerate(_wrap(draw, body, bod, cw - 16)[:2]):
            draw.text((cx + 16, cy + lh + 8 + j * 19), ln, font=bod, fill=MUTED_LAV, anchor="lt")
    return canvas.convert("RGB")


# ─── 03 — More from Alex Savage (real covers) ────────────────────────────────
MORE = [
    ("ua1_hi.jpg", "UNDERCOVER ARCHMAGE · BK 1", "Undercover Archmage",
     "A Supremacy-grade mage walks into a magic academy. Nobody knows what he is."),
    ("ua2_hi.jpg", "UNDERCOVER ARCHMAGE · BK 2", "Undercover Archmage 2",
     "The cover holds. The body count doesn't."),
    ("wa1_hi.jpg", "THE WARMAGE OF ARKLEY · BK 1", "The WarMage of Arkley",
     "A supremacy-grade mage. A daughter to raise. An apocalypse next door."),
    ("ua3_hi.jpg", "UNDERCOVER ARCHMAGE · BK 3", "Undercover Archmage 3",
     "They wanted a teacher. They got a weapon."),
]

def render_more_from():
    W, H = 970, 600
    canvas = make_grain_bg(W, H, glow_color=GARNET, glow_anchor=(0.5, 0.12),
                           glow_strength=0.15, grain=6, seed=61).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    kf = load_body(15, variant="SemiBold")
    kw = text_size(draw, "WHERE TO READ NEXT", kf)[0]
    ky = int(H * 0.07)
    draw.text(((W - kw) // 2, ky), "WHERE TO READ NEXT", font=kf, fill=GARNET_BRIGHT)
    tf = load_display(38, variant="SemiBold")
    tt = "More from Alex Savage"
    tw, th = text_size(draw, tt, tf)
    ty = ky + text_size(draw, "X", kf)[1] + 10
    draw.text(((W - tw) // 2, ty), tt, font=tf, fill=BRAND_CREAM)
    ruley = ty + th + 14
    draw.line([((W - 80) // 2, ruley), ((W + 80) // 2, ruley)], fill=GARNET, width=2)
    n = len(MORE)
    side, gap = int(W * 0.045), int(W * 0.02)
    col_w = (W - 2 * side - (n - 1) * gap) // n
    cover_h = int(H * 0.44)
    top = ruley + 30
    series_font = load_body(10, variant="SemiBold")
    title_font = load_display(18, variant="SemiBold")
    hook_font = load_italic(13, variant="Italic")
    for i, (fname, series, title, hook) in enumerate(MORE):
        cx = side + i * (col_w + gap)
        ccx = cx + col_w // 2
        path = COVERS / fname
        if not path.exists():
            continue
        pkg = make_cover_with_layered_shadow(path, cover_h, tilt=0)
        canvas.alpha_composite(pkg, (ccx - pkg.width // 2, top))
        cap_y = top + pkg.height + 4
        sw = text_size(draw, series, series_font)[0]
        draw.text((ccx - sw // 2, cap_y), series, font=series_font, fill=GARNET_BRIGHT)
        tw2 = text_size(draw, title, title_font)[0]
        draw.text((ccx - tw2 // 2, cap_y + 16), title, font=title_font, fill=BRAND_CREAM)
        for j, ln in enumerate(_wrap(draw, hook, hook_font, col_w - 6)[:3]):
            lw = text_size(draw, ln, hook_font)[0]
            draw.text((ccx - lw // 2, cap_y + 40 + j * 17), ln, font=hook_font, fill=MUTED_LAV)
    return canvas.convert("RGB")


# ─── social — reddit-style 1280x384 (cover-led) ──────────────────────────────
def render_social_reddit():
    W, H = 1280, 384
    canvas = make_grain_bg(W, H, glow_color=GARNET, glow_anchor=(0.88, 0.16),
                           glow_strength=0.20, grain=6, seed=31).convert("RGBA")
    draw = ImageDraw.Draw(canvas)
    cover_pkg = make_cover_with_layered_shadow(CHIR_COVER, int(H * 0.86), tilt=-2)
    cover_x = 24
    canvas.alpha_composite(cover_pkg, (cover_x, (H - cover_pkg.height) // 2))
    text_x = cover_x + cover_pkg.width + 30
    draw.text((text_x, 96), "Alex Savage", font=load_display(34, variant="SemiBold"), fill=BRAND_CREAM)
    draw.text((text_x, 150), f"{KICKER_A}   ·   {KICKER_B}",
              font=load_body(13, variant="SemiBold"), fill=GARNET_BRIGHT)
    hf = load_display(58, variant="SemiBold")
    parts = [p.strip() for p in HOOK.split(".") if p.strip()]
    for i, ln in enumerate(parts):
        fill = GARNET_BRIGHT if i == len(parts) - 1 else BRAND_CREAM
        draw.text((text_x, 192 + i * 64), ln + ".", font=hf, fill=fill)
    return canvas.convert("RGB")


def save(img, name):
    if img is None:
        return None
    p = OUT / name
    img.save(p, "JPEG", quality=92, optimize=True, progressive=True)
    print(f"  ✓ {name}  ({img.width}x{img.height}, {p.stat().st_size:,} b)")
    return p


def main():
    print(f"Chirurgeon A+ → {OUT}")
    save(render_header(),        "01-header.jpg")
    save(render_hero(),          "01-hero.jpg")
    save(render_characters(),    "02-characters.jpg")
    save(render_whats_inside(),  "02-whats-inside.jpg")
    save(render_more_from(),     "03-more-from.jpg")
    save(render_social_reddit(), "social-reddit.jpg")


if __name__ == "__main__":
    main()
