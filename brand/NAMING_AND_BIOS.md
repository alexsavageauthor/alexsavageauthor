# Alex Savage — Naming Bible & Unified Bios

Companion to BRAND_FOUNDATION.md. This file covers what things are *called* and how the
author describes himself. Anything visual (palette, marks, typography) lives in the
foundation file, not here.

Last reviewed: 2026-08-22.

---

## 1. Naming bible

### Series names (canonical, locked)

| Canonical series name | Books in it | Never write |
|---|---|---|
| **Ravenwick Academy** | Undercover Archmage 1–4 | The Ravenwick Chronicle, Ravenwick Chronicle, Ravenwick Chronicles |
| **The WarMage of Arkley** | WarMage of Arkley 1–3 | WarMage Arkley, The Arkley WarMage |
| **Hell's Half-Acre** | Book 1 onwards | Hells Half Acre (needs the apostrophe and the hyphen) |
| **Chirurgeon** / **The Hambledon Free Company** | Chirurgeon 1 onwards | Hambledon Company, The Free Company |

Rule of thumb: **Ravenwick Academy everywhere.** It's the series name, it's the school
name in-world, and having the two match is a feature rather than a problem — the reader
searching "Ravenwick Academy" should land on the series page either way.

The 2026-08-22 rename touched index.html, the four Undercover Archmage book pages,
reading-order.html, patreon.html, action-haremlit.html, magic-academy-haremlit.html,
sitemap.xml, BRAND_FOUNDATION.md, the two brand generator scripts, and the A+ comparison
copy files. The series page moved from the-ravenwick-chronicle.html to
ravenwick-academy.html and the old path is now a redirect stub, so any old link still
works.

Chirurgeon is the odd one out: "Chirurgeon" is what readers say and search for, and
"The Hambledon Free Company" is the series-of-record name that appears on the series page
and in schema. Both are fine, but lead with Chirurgeon in anything a reader sees first.

### Book titles

Book titles never change to match a series rename. Undercover Archmage 1–4 stay
Undercover Archmage. On covers and listings the pattern is
`<Book Title>` with `<Series Name> Book N` as the series line beneath it.

### Author name and imprint

- Author: **Alex Savage** (no middle initial, no periods).
- Imprint: **Savagery & Co.** — used on Patreon, the copyright line, and eventual merch.
- Patreon: Savagery & Co. at patreon.com/c/SavageryandCo.
- Instagram handle is @alex_savageauthor, which is not the same shape as the site domain
  alexsavageauthor.com, so copy both from here rather than typing from memory.

### Spelling and style

UK spelling in site copy and back matter. Apostrophes are curly in HTML (`&rsquo;`) and
straight in plain-text files. "Haremlit" is one word, lowercase unless it starts a
sentence. "LitRPG" keeps its capitalisation.

---

## 2. Unified bios

Voice target is dry British understatement — the same register as the site's About block.
These are drop-in replacements, so use them as written rather than rewriting for each
platform, which is how the versions drift apart in the first place.

### Long (Amazon author page, harem-lit.com, press)

Alex Savage is a pen name, and it's staying that way — the books are real, which is more
or less all a reader needs. He writes action haremlit: overpowered men trying very hard
not to be noticed, in worlds that won't stop noticing them.

Four series so far. Ravenwick Academy follows a Null-mage black-ops operator working
under deep cover at a magic academy full of postgraduates who are dangerous in ways their
parents pay extra not to acknowledge. The WarMage of Arkley is what happens when a
supremacy-grade mage is raising his daughter and the apocalypse turns up next door.
Chirurgeon drops a Pittsburgh ER nurse into a dying world with a system bracer on his
arm and a mercenary company that can't afford to lose him. Hell's Half-Acre is a town
that's behind on the payments and a hellmouth that isn't.

Expect tradecraft, magic-on-magic violence, single-dad domesticity ruined by
inter-dimensional tears, fireballs answered with 9mm, and women who refuse to let any of
it stay quiet. Books are on Kindle Unlimited; early chapters go up on Patreon ahead of
Amazon.

### Medium (Facebook, Patreon, Reddit profile, newsletter footer)

Alex Savage writes action haremlit — overpowered men trying very hard not to be noticed,
in worlds that won't stop noticing them. Four series: Ravenwick Academy, The WarMage of
Arkley, Chirurgeon, and Hell's Half-Acre. Tradecraft, magic-on-magic violence, fireballs
answered with 9mm, and women who refuse to let any of it stay quiet. Early chapters go up
on Patreon ahead of Amazon.

### Short (Instagram, anywhere with a character limit)

Action haremlit. Overpowered men trying not to be noticed, in worlds that won't stop
noticing them. Ravenwick Academy · WarMage of Arkley · Chirurgeon · Hell's Half-Acre.

### One-liner (bylines, ads, guest posts)

Alex Savage writes action haremlit — fireballs answered with 9mm.

---

## 3. Calls to action

The conversion path is free sample → Kindle Unlimited or Patreon, and the site already
runs it. Keep the wording consistent:

- **Start Reading Free** → Patreon (early chapters, not email-gated).
- **Free on Kindle Unlimited** → the book's buy link, never a bare Amazon URL.
- **A Day in the Life of a Battle Mage** is the BookFunnel freebie for newsletter signup.
  When the final BookFunnel URL is settled it goes on the newsletter blocks and in book
  back matter — not on the Patreon buttons, which have their own job.

Buy links always route through alexsavage-links.vercel.app/<slug> (ua1–ua4, wa1–wa3,
chir, hha, author). Unknown slugs fall through to the reading-order page, so a typo degrades
gracefully rather than 404ing.

---

## 4. Cross-platform caption patterns

Same voice everywhere, different lengths. The pattern that works is a concrete detail
from the book first, then the series name, then one link — rather than opening with the
series name, which reads like an advert and gets scrolled past.

- **New release:** one line of situation, one line of what goes wrong, series name and
  book number, buy link, "Free on Kindle Unlimited".
- **Quote card:** the quote does the work; caption is one line of context and the series
  name. No link stuffing.
- **Character post:** who she is, what she wants, why that's a problem for the hero.
- **Behind the scenes:** what the writing week actually looked like, including the boring
  parts. This is the one that gets replies.
- **Patreon push:** what's up there right now and how far ahead of Amazon it is.

Instagram gets the short bio in the profile and hashtags in the first comment. Facebook
and Reddit take the medium bio. Reddit especially — r/haremlit reacts badly to anything
that reads as marketing copy, so post as a person who wrote a book, not as a book.
