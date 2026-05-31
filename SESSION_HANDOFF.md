# Session Handoff — Alex Savage Author Site

A working summary of the May 2026 build & QA pass on **alexsavageauthor.com**. Hand this file to any new Claude chat that has access to `~/Desktop/alex-savage-website/alexsavageauthor/` and it will have the context it needs.

---

## The brand direction

Set in **`brand/BRAND_FOUNDATION.md`** — that file is the source of truth. Read it first. TL;DR:

- **Pen name kept anonymous on purpose.** No press, no podcasts, no bio that links to a real identity.
- **Genre:** action haremlit. Two series — *The Ravenwick Chronicle* (magic-academy sub-genre) and *The WarMage of Arkley* (system-apocalypse / single-dad LitRPG sub-genre).
- **Visual register:** painterly, mature, modern romantasy with an action edge. Purple/gold like an old grimoire kept somewhere warm, with coral when the cover needs to flirt.
- **Palette:** midnight `#160C24` / `#1F1336` / `#271847`, gold `#E8B756`, coral `#FF7E94`, ivory `#F5EFE6`.
- **Typography:** Fraunces (display + author lockup), Inter (UI/body), Caveat (handwritten accent).
- **Series anchors:**
  - The Ravenwick Chronicle → gold `#E8B756`
  - The WarMage of Arkley → coral `#FF7E94`

---

## What's in the site

- **13 HTML pages:** homepage + 6 book pages + 2 series pages + 4 subgenre pages (no press page — pen name anonymous)
- **`brand/` folder:** BRAND_FOUNDATION.md, alex-savage-wordmark.svg, alex-savage-mark-simple.svg (the AS monogram in nav)
- **`assets/`:** the painted hooded-figure portrait (`alex-savage-portrait.jpg` + sized variants in `alex-savage-portrait-social/`), pre-built FB cover and Reddit banner in `alex-savage-banners/`, all book covers + WebP variants + responsive sizes in `covers/`, 14 bespoke OG social cards in `og/`
- **Custom home OG card:** built from the portrait — hooded figure left, wordmark + "Two pen names / Two terrible cover stories" tagline right
- **Channels promoted:** Patreon (Savagery & Co.), Newsletter form (Mailerlite-ready), harem-lit.com (top nav link + dedicated homepage callout)

---

## What was done in this session

### Build-out
- 13 generated pages produced by `outputs/generate_alexsavage_pages.py` (book pages, series pages, subgenre pages)
- 14 bespoke OG cards by `outputs/generate_alexsavage_og.py` — every page has a unique social preview
- Newsletter signup form on homepage with native POST-to-Mailerlite handler
- Live image optimisation: 26 WebP variants + responsive 200/400/600px widths

### Brand rollout
- Created BRAND_FOUNDATION.md
- Swapped the old square-photo nav logo for the SVG AS monogram (`assets/alex-savage-mark.svg`) on all 13 pages
- Painted hooded-figure portrait surfaced in the About section, 4:5 aspect ratio, with the responsive `<picture>` element
- Schema.org Person.image points at the portrait

### QA fixes from review
- **UA1 cover** — was a 100×160 thumbnail; replaced with Amazon's 354×500 ebook cover; the `*_hi.jpg` files were all thumbnails despite the name and are now actual hi-res copies
- **Press page slug-collision orphans** — cleared
- **"Mossad-style" line** on the magic-academy page — softened to "high-pressure ops environment"
- **End-of-series dead-ends** — UA4 and WarMage 2 now have "Full series reading order →" CTAs
- **Press page entirely removed** at user's request (pen name anonymous)

### harem-lit.com promotion
- Top-nav link (coral-tinted) on every page
- Dedicated homepage callout block between Books and About
- Existing "Also on harem-lit.com →" links under each Amazon CTA preserved
- Footer chip upgraded ("harem-lit.com — the genre hub ↗")

---

## How to push changes

```
cd ~/Desktop/alex-savage-website/alexsavageauthor
git add -A
git commit -m "your message"
git push
```

Git is authenticated as the `alexsavageauthor` GitHub account via a Personal Access Token stored in macOS Keychain. If a push fails with "authentication failed," the token has expired — regenerate at `github.com/settings/tokens` while logged in as `alexsavageauthor`, then `git config --global credential.helper osxkeychain` and the next push prompt will save the new one.

GitHub Pages rebuilds in ~30s. Hard-refresh (Cmd+Shift+R) to see changes.

---

## Outstanding / future work

Nothing is broken or pending. Optional next moves:

1. **Goodreads review strip** on book pages — currently skipped because the books are too new and have no reviews. Revisit when reviews exist.
2. **Cover Band rule** — defined in BRAND_FOUNDATION §3 (`#1A0F2C` at 88% over artwork). Not enforced on book covers yet — needs the cover designer.
3. **Mailerlite hookup** — the homepage form posts to a generic Mailerlite endpoint. Swap to the real list URL when the Mailerlite account is wired up (search index.html for `ns-form` to find the form action).
4. **Larger UA1 cover** — current is 354×500 from Amazon (the public ceiling). If you have a 1500px+ original on disk, drop it over `assets/covers/ua1.jpg` and rerun the WebP/OG generation.

---

## Sister site

Malory (main pen name) lives at `~/malory-author-site/` and got the same kind of brand pass — its own BRAND_FOUNDATION.md is at `brand/BRAND_FOUNDATION.md` in that folder, with a separate SESSION_HANDOFF.md. The two sites share no code; they're independent.

---

*Last updated by this Claude session: May 2026. Update this doc whenever a brand decision changes or a significant batch of work lands.*
