---
name: banner
description:
  Slop University pull-up banner --- a single 850 × 2060 mm printed roll-up, the
  foyer and open-day furniture every university owns a cupboard of. Lockup,
  campaign line and call to action in vector type at eye level; one house-style
  hero band below. Fixed geometry, so any banners from this preset stand in a
  row as a set and each still works alone. Poster format; print artefact, run on
  demand only.
---

# Banner preset

Produce one Slop University pull-up banner from a single steering prompt. The
output should pass for the roll-up a real university stands beside its
registration desk: a lockup, a line, a picture, a QR code. It is the marketing
poster's joke at physical scale --- an institution whose whole identity is
measurement, announcing itself in a foyer, completely straight.

This is a **print artefact**. It is run by hand, never by `/publish`: it has no
place in `ops/select-preset.sh`, no ledger entry, no DOI, and no dark sibling.

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `marketing-poster.md` for everything about what the banner may say: "What the
  ad may reference", the ranking rules, "Read the work line", the CTA reservoir
  and "Voice". A banner is that preset's display ad on a different sheet; only
  the differences are stated here
- `../genre.md` for the voice floor
- `../../_shared/image-workflow.md` + `../../_shared/visual-style.md` for the
  hero
- `../../_shared/output-naming.md` for slug, seed, output paths
- `../../_shared/typst-layout.md` only for the template import and PDF-metadata
  rules

## Doc identity

| Field                      | Value                                                                                    |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| Canonical name             | Slop University pull-up banner                                                           |
| Format                     | **poster** (single page, all content `place`d)                                           |
| Visible title              | the campaign line --- **steering-derived**                                               |
| Paper / orientation        | 850 × 2060 mm trim plus 3 mm bleed on every edge (see "Print production"); portrait only |
| Theme                      | none --- the ground is rolled (`ink` or `cream`); no dark sibling                        |
| Cover lockup               | `slop`, via `slop-overlay-masthead` on the solid ground (white on ink, black on cream)   |
| Filename prefix            | `slop-banner`                                                                            |
| PDF subfolder (`<group>`)  | `banner`                                                                                 |
| Page count                 | exactly **1**; two PDFs per run, the print file and a quarter-scale `-proof.pdf`         |
| Register                   | aspirational marketing at display scale (`marketing-poster.md` › "Voice")                |
| PDF metadata title formula | `This Slop University Banner Does Not Exist: <steering verbatim>`                        |

## Inputs

One free-text **steering prompt** --- what this banner stands for. Examples:

- "australia's most measured university"
- "the School of Continuous Improvement"
- "study measurement"
- "research outputs, produced continuously"

The steering may also pin the angle and the ground ("…, cream ground"). Honour a
pin; roll whatever is left open.

## Sets

Banners are usually ordered as a set and stood in a row. The geometry below is
**identical on every banner** --- lockup, campaign line, CTA row and hero band
at the same heights --- so any banners from this preset line up, the hero bands
reading as one frieze. That is the whole mechanism; there is no "set" run. Each
banner is its own run and must be complete alone.

When the steering says a banner is one of a set:

- alternate the ground along the row (ink, cream, ink, cream)
- give each banner a different angle or subject, and a different hero scene type
  (a campus exterior, an interior, an apparatus close-up, a works floor)
- never refer to a neighbouring banner, number the banners, or run a sentence or
  an image across two of them

## The genre's structural skeleton

Heights are printed millimetres from the top of the 2060 mm sheet; the bracketed
figure is the height above the floor once the banner stands.

| Element         | Band (from top)          | Notes                                                                                                                 |
| --------------- | ------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Masthead        | 72--192 (≈ 1.9 m)        | `slop-overlay-masthead` on the ground; spine runs from the top edge to the hero. Read over heads from across the room |
| Eyebrow         | 264 (≈ 1.8 m)            | one gold line: the rolled angle's canon name, or the motto                                                            |
| Campaign line   | from 300 (≈ 1.5--1.75 m) | steering-derived, ≤ 6 words, ≤ 4 lines at 224 pt printed. Eye level --- the one thing a passer-by reads               |
| Supporting line | under the campaign line  | one sentence, ≤ 22 words, ≤ 4 lines at 72 pt printed                                                                  |
| CTA row         | 764--884 (≈ 1.2 m)       | gold rule, CTA + address, read-the-work line, social line; QR at the right. Waist-to-chest: where a phone can scan it |
| Hero band       | 920--2060                | the run's one image, full width, 3:4, running off the bottom edge. Nothing is overlaid on it                          |
| Cassette        | bottom 66                | inside the base, never seen. The hero simply continues into it                                                        |

Nothing that must be read sits below 1.1 m, and no type sits on the image, so
the hero needs no scrim and the words stay vector-sharp whatever the image's
resolution.

Total on-sheet text: ≤ 40 words (the DOIs don't count). A banner that needs a
second sentence of persuasion is a brochure.

## Per-run variation rolls

Roll once per run, upfront, unless the steering pins the value.

### Ground (roll: ink / cream, 50/50)

The solid field behind the type. `ink` sets white type on house black; `cream`
sets ink type on warm cream. Gold is the accent on both and never the ground
(the lockup's gold crest disappears into it).

### Angle (roll uniform across five)

Each angle sets the eyebrow and bends the supporting line. Everything named is
canon; `marketing-poster.md` › "What the ad may reference" governs.

**a) the University.** Eyebrow is the motto (`#emph(slop-motto)`,
untranslated --- `canon/institution.md`). The campaign line is an institutional
brag under the ranking rules: self-referential or unfalsifiable.

**b) a school.** Eyebrow is the school's canon name. The supporting line names
its flagship lab and what it convenes, close to the `canon/schools.yml` blurb.

**c) a unit, lab, or initiative.** Eyebrow is its canon name (the Office of
Research Outputs, the Living Dashboard, Demo Quarter). The supporting line says
what it does in the institution's own flat terms.

**d) come-study.** Eyebrow is a canon program name. Supporting line is
you-focused. The CTA and QR point to `courses.slop.university`.

**e) research showcase.** Eyebrow is the lead author's school; the campaign line
is one real published output's title (skip the angle if no ledger title fits six
words); its DOI leads the read-the-work line.

### Hero scene

The banner's subject as one scene in the two-ink house style, composed for a 3:4
portrait band seen from across a room: one clear subject, bold shapes, readable
at thumbnail size. See "Imagery" for the composition clause.

## Imagery (preset specifics for image-workflow.md)

- Image folder: `output/slop-banner-<slug>-<seed>-images/`
- **One image**: `hero.jpg`, `--aspect-ratio 3:4`, `--resolution 4K`. Not 9:16:
  the generator's 4K caps the _long_ edge at 4096 px, so 3:4 delivers 3072 px
  across the banner where 9:16 delivers 2286, and 3:4 is the band's own shape
  (nothing is cropped away).
- Append this composition clause to the scene, before the fixed style clause:

  > Portrait composition, full bleed: the artwork runs off all four edges of the
  > frame with no border, margin or blank band, and the scene continues to the
  > bottom edge as plain foreground, with faces and fine detail kept out of the
  > lowest tenth.

  Asking for a "quiet" bottom instead gets a blank slab.

- **Crop the paper margin.** Whatever the prompt says, the model usually frames
  the scene as a print on paper, with a ragged cream margin that differs from
  one banner to the next and breaks the frieze. Keep the raw generation and crop
  to the artwork's bounding box, found on a blurred copy so the print grain
  cannot defeat the trim. A hero with no left margin is already full bleed ---
  leave it alone, or the trim eats its cream sky:

  ```bash
  cd output/slop-banner-<slug>-<seed>-images && mv hero.jpg hero-raw.jpg
  box=$(convert hero-raw.jpg -blur 0x6 -fuzz 14% -format '%@' info:)
  if [ "$(echo "$box" | cut -d+ -f2)" -gt 30 ]; then
    convert hero-raw.jpg -crop "$box" +repage -shave 0.6%x0.6% +repage \
      -quality 95 hero.jpg
  else
    cp hero-raw.jpg hero.jpg
  fi
  ```

  The crop should cost about 100 px a side. If it took much more off the height
  than the width, the model left a blank band; `fit: "cover"` will then crop the
  sides to refill the 3:4 band, so re-roll if what remains would fill the band
  from under ~2400 px of width.

- **Then double it**: `mise exec -- ops/upscale-image.py <images>/hero.jpg` (the
  script's docstring says why). The generator's ceiling is about 85 dpi across
  850 mm; doubled, the hero prints at 145--185 dpi. Crop first, upscale second,
  so the trim's thresholds see the image they were tuned on. The 1× file is kept
  beside it as `hero-1x.jpg`.
- **Lettering creeps in on instruments.** Compass points on a weathervane,
  numerals on a dial, a maker's plate on a machine. Name the instrument's blank
  form in the scene ("cup anemometers", "blank-faced meters") and check every
  hero at 100% before upscaling it.
- No scrim bake, no inline images, no charts, no parity spare.

## Style references

Read before generating:

- **Layout core source**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/lib.typ` ---
  `page-settings`, `hide`, and `overlay-masthead`
- **Sibling**: `marketing-poster.md` --- the same all-`place`d, empty-body
  construction on a screen-shaped sheet

## Typst structure

The banner is drawn on a **quarter-scale canvas** (212.5 × 515 mm) and enlarged
4× by one `scale` at compile. This is what lets the brand furniture, whose spine
offset and rule weight are fixed lengths, come out in proportion on a two-metre
sheet --- and it makes the proof a one-flag recompile. Every length and type
size in the source is a canvas value; the printed value is four times it.

Only the "This banner" block changes between runs. **Do not alter the geometry
block or any placement**: a banner whose bands have moved no longer lines up
with the others.

```typst
#import "@local/slop-university-brand:0.1.0": (
  slop, slop-colors, slop-gold, slop-ink, slop-motto, slop-overlay-masthead,
  slop-qr-code, slop-social-line,
)

#set document(
  title: "This Slop University Banner Does Not Exist: <steering prompt verbatim>",
)

// ── This banner ──
#let ground = "ink" // "ink" or "cream", per the roll
#let hero = "/output/slop-banner-<slug>-<seed>-images/hero.jpg"
#let eyebrow = [<the angle's canon name>] // angle a: emph(slop-motto)
#let campaign = [<campaign line --- steering-derived, ≤ 6 words>]
#let supporting = [<supporting line --- one sentence, ≤ 22 words>]
#let cta = [<CTA from the reservoir> --- slop.university]
#let qr-url = "https://slop.university/" // the CTA's address
#let dois = ("10.5555/slop.<seed>", "10.5555/slop.<seed>") // real ledger DOIs

// ── Geometry (fixed across every banner, so a row lines up). Designed on a
//    quarter-scale canvas and enlarged by `k` at compile: 4 = the print file,
//    1 = a proof (--input scale=1). ──
#let k = float(sys.inputs.at("scale", default: "4"))
#let w = 212.5mm // trim width  (850mm printed)
#let h = 515mm // trim height (2060mm printed)
#let b = 0.75mm // bleed       (3mm printed)
#let hero-y = 230mm // top edge of the hero band (a 3:4 band to the bottom)

#let dark = ground == "ink"
#let bg = if dark { slop-ink } else { rgb("#f3ead8") }
#let fg = if dark { white } else { slop-ink }
#let muted = if dark { rgb("#d9d9d9") } else { slop-colors.grey-4 }

#show: doc => slop(
  title: "",
  page-settings: (width: (w + 2 * b) * k, height: (h + 2 * b) * k),
  margin: 0mm,
  config: (hide: ("page-numbers", "title-block", "masthead")),
  doc,
)

#place(top + left, scale(k * 100%, origin: top + left, box(
  width: w + 2 * b,
  height: h + 2 * b,
  fill: bg,
  clip: true,
  {
    // ── Hero band: full width, running off the bottom into the cassette ──
    place(top + left, dy: b + hero-y, image(
      hero,
      width: w + 2 * b,
      height: h + b - hero-y,
      fit: "cover",
    ))
    // ── Everything else sits on the trim box, above the hero ──
    place(top + left, dx: b, dy: b, box(width: w, height: h, {
      slop-overlay-masthead(
        hero-y,
        variant: if dark { "white" } else { "black" },
        dy: 18mm,
        height: 30mm,
      )
      // Eyebrow, campaign line, supporting line: top-anchored at eye level
      place(top + left, dx: 30mm, dy: 66mm, box(width: 166mm)[
        #set par(leading: 0.42em, spacing: 0pt)
        #text(fill: slop-gold, size: 15pt, eyebrow)
        #v(7mm)
        #text(fill: fg, size: 56pt, weight: "medium", campaign)
        #v(8mm)
        #set par(leading: 0.62em)
        #text(fill: muted, size: 18pt, supporting)
      ])
      // CTA row: bottom-anchored just above the hero, QR at scanning height
      place(top + left, dx: 30mm, dy: hero-y - 39mm, box(
        width: 166mm,
        height: 30mm,
        {
          place(top + left, line(length: 100%, stroke: 0.75pt + slop-gold))
          place(bottom + left, box(width: 132mm)[
            #set par(leading: 0.55em, spacing: 0pt)
            #text(fill: fg, size: 15pt, cta)
            #v(3.2mm)
            #text(fill: muted, size: 8.5pt)[Read the work: #dois.map(d => "doi:" + d).join(" · ")]
            #v(2.6mm)
            #slop-social-line(size: 8.5pt, fill: muted)
          ])
          place(bottom + right, slop-qr-code(qr-url, width: 26mm, padding: 1.6mm))
        },
      ))
    }))
  },
)))
```

Notes:

- The opaque ground box covers the page, so the template's own page-background
  spine (drawn at an unscaled 1.9 cm) never shows; the masthead helper redraws
  it on the canvas.
- The QR is always dark modules on a white tile, on either ground --- a banner
  QR is scanned in bad foyer light, and the inverted form the signage posters
  use is the less reliable one.
- The campaign block is top-anchored and the CTA row bottom-anchored, so a
  shorter campaign line leaves air between them instead of moving either.

## Compile and fit

1. Print file:
   `typst compile --root . output/slop-banner-<slug>-<seed>.typ output/pdf/banner/slop-banner-<slug>-<seed>.pdf`
   (create `output/pdf/banner/` if absent). Proof: the same command with
   `--input scale=1` → `…-proof.pdf`.
2. `pdfinfo`: **1 page** each, ≈ 2426 × 5856 pt (print) and ≈ 607 × 1464 pt
   (proof).
3. Eyeball the proof at thumbnail size, then at full size. The campaign block
   must end above the gold rule with visible air; if it collides, the line is
   too long --- shorten the words, never the type.

## Print production

The sheet is sized for Vistaprint's Large pull-up (85 × 206 cm, bottom 6.6 cm
inside the cassette), the common 850 mm Australian roll-up with a slightly
taller sheet. The PDF page is the trim plus 3 mm bleed on every edge (856 × 2066
mm), with the ground and hero filling the bleed and all type at least 100 mm
inside the trim.

- **Confirm the document size against the printer's own template before
  ordering** --- it is shown in their upload tool, not published as a spec. A
  different sheet changes `w`, `h` and `b` in the geometry block, in every
  banner of the set alike, and nothing else.
- The PDF is RGB (typst emits no PDF/X) and the printer converts it. The lockup
  gold shifts under that conversion; order one banner and look at it before
  ordering the set.

## Pre-ship checklist (preset-specific)

Generic format-aware items live in `../SKILL.md`. Banner items:

- [ ] One page at 856 × 2066 mm, plus the quarter-scale proof; geometry block
      and placements unchanged from the skeleton
- [ ] Ground is `ink` or `cream`; lockup variant matches it; no type or
      furniture on the hero band
- [ ] Campaign line is steering-derived, ≤ 6 words, ≤ 4 lines, clear of the gold
      rule; total text ≤ 40 words
- [ ] Hero is 3:4 at 4K, margin-cropped then doubled (≥ 5600 px wide), no blank
      band and no lettering, nothing that matters in its lowest tenth; reads at
      thumbnail size and holds at 100%
- [ ] Eyebrow and everything else named is canon; read-the-work line carries 2-3
      real ledger DOIs; CTA from the reservoir; QR resolves to the CTA's address
- [ ] No verifiable claims; any brag is self-referential or unfalsifiable; no
      exclamation marks
- [ ] (Set) grounds alternate along the row; no banner refers to another
- [ ] PDF metadata title is
      `This Slop University Banner Does Not Exist: <steering verbatim>`; no
      other metadata fields populated

## Common failure modes (preset-specific)

- **Designed like a poster**: type sized to be read at arm's length, a block of
  body copy, detail at knee height. A banner is read from across a room; the
  campaign line carries it and the rest is furniture.
- **The hero still shows a paper margin**: the crop step was skipped, or its
  bounding box missed. Fix the crop; don't hide a margin by zooming the image in
  typst.
- **Bands nudged to fit a long line**: breaks the row. Cut words.
- **Published by reflex**: no outputs entry, news post, or DOI for a banner.

## What this preset is not

- Not a marketing poster: no screen aspect, no dark sibling, no type over the
  image, and not in the publish mix.
- Not exhibition signage. A banner that explains the artwork, credits the
  artist, or names the show is a different object with a different rulebook; it
  does not come from a preset.
