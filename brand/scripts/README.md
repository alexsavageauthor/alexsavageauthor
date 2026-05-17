# Alex Savage — Brand Scripts

Automation scripts that apply the brand foundation to real production work.

---

## Setup (one-time)

These scripts use Python 3 (already on your Mac) and the **Pillow** image library. Install Pillow:

```
pip3 install Pillow --break-system-packages
```

To verify Pillow installed:

```
python3 -c "import PIL; print(PIL.__version__)"
```

You should see a version number (e.g. `10.4.0`).

Fonts are bundled in `../fonts/` (Fraunces, Inter, Caveat). No installation needed — the scripts load them directly.

---

## `gen_covers.py` — Cover Variant Generator

Generates store-ready variants from a finished master cover.

### Usage

**Single file:**
```
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_covers.py ~/Desktop/ua5.jpg
```

**Folder of covers (processes all):**
```
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_covers.py ~/Desktop/new-covers/
```

**Custom output location:**
```
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_covers.py ~/Desktop/ua5.jpg -o ~/Desktop/store-uploads/
```

### Outputs

For input `ua5.jpg`, you get a folder `ua5-variants/` containing:

| File | Size | For |
|---|---|---|
| `ebook.jpg` | 1600×2560 | Amazon KDP, Kobo |
| `apple.jpg` | 1400×2100 | Apple Books |
| `audible.jpg` | 2400×2400 | Audible (cover padded on brand purple) |
| `thumb-1200.jpg` | 1200×1800 | Website hero, OG card source |
| `thumb-600.jpg` | 600×900 | Website medium / blog |
| `thumb-300.jpg` | 300×450 | Website thumbnail / store grid |

Use source masters at 3200×5120 (or as close as you can get) for best results.

---

## `gen_quote_cards.py` — Quote Card Generator

Builds branded quote cards for Instagram, Facebook, and inside-book teasers.

### Usage (one quote)

```
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_quote_cards.py \
  --quote "He was Null. Magic-immune. Off the spectrum." \
  --book "Undercover Archmage" \
  --cover ~/Desktop/alex-savage-website/alexsavageauthor/assets/covers/ua1_hi.jpg \
  -o ~/Desktop/quote-cards/
```

### Usage (config file — recommended for batches)

Save a quote config as JSON:

`my-quote.json`
```json
{
  "quote": "He was Null. Magic-immune. Off the spectrum. Which made him invisible to the wards — and a beacon to every dangerous woman on campus.",
  "book": "Undercover Archmage",
  "cover": "/Users/paul-jamesmerrell/Desktop/alex-savage-website/alexsavageauthor/assets/covers/ua1_hi.jpg",
  "author": "Alex Savage",
  "cta": "Available on Kindle Unlimited"
}
```

Then run:

```
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_quote_cards.py --config my-quote.json -o ~/Desktop/quote-cards/
```

Building a library of quote configs (one per shareable moment per book) means you can regenerate everything if the brand changes.

### Outputs

For a quote, you get a folder `{book-slug}-{first-word}/` containing:

| File | Size | For |
|---|---|---|
| `ig-square.jpg` | 1080×1080 | Instagram feed / Facebook square |
| `ig-story.jpg` | 1080×1920 | Instagram / Facebook stories |
| `fb-landscape.jpg` | 1200×630 | Facebook link preview / shareable |
| `teaser-2000.jpg` | 2000×2000 | Inside-book back-matter, high quality |

### Defaults

- Author defaults to **"Alex Savage"**
- CTA defaults to **"Available on Kindle Unlimited"**
- Override either with `--author` and `--cta` flags or in the config file

---

## `gen_series_cover.py` — Series Cover Frame

Applies the locked brand frame to **finished cover artwork** for a new book. Designed for use when you're producing a new cover: artist delivers flat art with the title painted in but **no author name**, and this script adds the consistent brand layer.

### Usage

```
# Add UA series frame (gold anchor)
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_series_cover.py ~/Desktop/ua5-art.jpg --series ua

# Add WA series frame (coral anchor)
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_series_cover.py ~/Desktop/wa3-art.jpg --series wa

# Frame + produce all store variants in one go
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_series_cover.py ~/Desktop/ua5-art.jpg --series ua --variants
```

### What it adds

- **Series color anchor rule** along the top edge (gold for UA, coral for WA)
- **"Alex Savage" wordmark** in Fraunces SemiBold cream, centered below the rule, on a soft fade band for legibility against bright artwork
- **"SAVAGERY & CO." imprint mark** in the bottom-right corner, subtle (~70% opacity)

### What it deliberately does NOT do

Render the book title. Title typography (size, font, treatment, embossing, decorative flourishes) is hand-tuned designer work — the UA1 chunky gold serif with the magical eye-in-the-O can't be reproduced by a script, and trying would deliver something obviously generic. Your cover designer paints in the title; the script adds the brand layer around it.

### Adding a new series

Edit the `SERIES_ANCHORS` dict near the top of `gen_series_cover.py`:

```python
SERIES_ANCHORS = {
    "ua": BRAND_GOLD,
    "wa": BRAND_CORAL,
    "new-series-key": MUTED_LAV,   # add here
}
```

The key becomes the `--series` argument value.

### Caveat — existing covers with author text baked in

UA1, WA1, etc. already have "ALEX SAVAGE" painted into the artwork. Running this script on them stacks the new wordmark on top of the old one. The script is for **new covers being produced**, not for retroactively framing already-published ones.

---

## `gen_portrait_variants.py` — Author Profile Photos

Takes the Alex Savage author portrait and produces profile-photo sizes for every platform you upload to. Profile pictures only — banner formats are deliberately omitted because tall portraits don't crop into wide banners well.

### Usage

```
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_portrait_variants.py ~/Desktop/alex-savage-website/alexsavageauthor/assets/alex-savage-portrait.jpg
```

### Outputs

For a portrait `alex-savage-portrait.jpg`, you get a folder `alex-savage-portrait-social/` containing:

| File | Size | For |
|---|---|---|
| `amazon-author.jpg` | 1500×1500 | Amazon Author Central profile photo |
| `profile-2048.jpg` | 2048×2048 | Max-resolution master, any future need |
| `profile-1024.jpg` | 1024×1024 | High-res universal |
| `profile-800.jpg` | 800×800 | Universal social profile (Facebook, Instagram, Reddit) |
| `profile-400.jpg` | 400×400 | Smaller avatar use, mobile-optimized |
| `profile-180.jpg` | 180×180 | Favicon source / website nav mark |

### Crop strategy

All outputs are square, center-cropped with an upper-third bias so the face stays in the visual sweet spot. Works for portrait-orientation sources where the face is in the upper half (typical headshot composition).

### Source recommendation

Save your finalized portrait as `alex-savage-portrait.jpg` (or `.png`). The largest resolution you have is best — the script downscales cleanly but can't sharpen an already-small source. Aim for **at least 2048px** on the long edge so even the largest output (2048×2048) doesn't upscale. Square or portrait orientation works; landscape is allowed but the upper-third bias assumes the face is high in the frame.

### Adding banners back if you ever need them

The script still contains the `wide_left` and `tall_fit` rendering modes. To add a Facebook cover or IG story output, edit the `VARIANTS` list near the top:

```python
VARIANTS = [
    {"name": "amazon-author", "size": (1500, 1500), "mode": "square_face", "quality": 94},
    # ... existing profiles ...
    {"name": "fb-cover",      "size": (1640, 624),  "mode": "wide_left",   "quality": 92},  # add
    {"name": "ig-story",      "size": (1080, 1920), "mode": "tall_fit",    "quality": 92},  # add
]
```

---

## `gen_banners.py` — Catalog Showcase Banners

Builds Facebook cover and Reddit banner combining your portrait, book covers, and the brand wordmark in a cinematic cascade layout.

### Usage

```
python3 ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/gen_banners.py \
  --portrait ~/Desktop/alex-savage-website/alexsavageauthor/assets/alex-savage-portrait.jpg \
  --covers ~/Desktop/alex-savage-website/alexsavageauthor/assets/covers/ua1_hi.jpg \
           ~/Desktop/alex-savage-website/alexsavageauthor/assets/covers/ua2_hi.jpg \
           ~/Desktop/alex-savage-website/alexsavageauthor/assets/covers/ua3_hi.jpg \
           ~/Desktop/alex-savage-website/alexsavageauthor/assets/covers/ua4_hi.jpg \
           ~/Desktop/alex-savage-website/alexsavageauthor/assets/covers/wa1_hi.jpg \
           ~/Desktop/alex-savage-website/alexsavageauthor/assets/covers/wa2_hi.jpg \
  -o ~/Desktop/alex-savage-website/alexsavageauthor/assets/
```

### Outputs (in `alex-savage-banners/`)

| File | Size | For |
|---|---|---|
| `fb-cover.jpg` | 1640×624 | Facebook cover photo |
| `reddit-banner.jpg` | 1280×384 | Reddit profile banner |

### Layout

- Portrait full-height on the left, fading into the brand purple gradient
- Book covers cascading right-to-left with alternating ±2–3° tilts and drop shadows (most recent book sits on top of the stack)
- Brand wordmark + "ACTION HAREMLIT" tagline in the top-right corner
- Subtle gold embers scattered across the upper area
- Brand primary-deep gradient with radial gold glow upper-right

### Adding new books

Just include their cover path in the `--covers` list. Up to ~8 fit comfortably; beyond that the overlap gets aggressive. The script automatically tightens the cascade if covers don't fit comfortably side-by-side.

### Re-run after a new release

Whenever you add a new book to the catalog, re-run the script with the updated `--covers` list to refresh both banners. Then re-upload to FB and Reddit.

---

## Coming next (if needed)

- GIMP menu-item versions of these scripts (for in-GIMP workflow when you're actively editing a cover)
- Twitter/X header and LinkedIn cover variants (similar layout, different dimensions) — add to `BANNERS` list in `gen_banners.py` if you need them

---

## Editing the brand

When the brand foundation changes (new color, font swap, layout tweak):

1. Update `../BRAND_FOUNDATION.md`
2. Update the brand constants near the top of each `.py` script (look for the `─── Brand ───` section)
3. Re-run any cards/covers you want updated

Everything pulls from one source of truth: the foundation doc.

---

## Quick install command

```
pip3 install Pillow --break-system-packages && echo "Ready. Scripts at ~/Desktop/alex-savage-website/alexsavageauthor/brand/scripts/"
```
