---
name: marketing-poster
description:
  Slop University marketing poster --- a single-page 16:9 landscape or 9:16
  portrait display ad (the e-signage panels' native aspect): the snazzy,
  image-led recruitment/brand piece a university runs on bus-stop and campus
  screens. Steering-driven campaign line in the aspirational marketing
  register; full-bleed house-style hero, big display type, almost no body
  copy. Like the brochure it cross-references the existing fiction (roster
  researchers, canon schools, published outputs). Poster format (no cover,
  contents, or back cover); dark sibling for signage.
---

# Marketing-poster preset

Produce one Slop University marketing poster from a single steering prompt. The
output should pass for the display advertising a real university buys ---
digital signage at a bus stop, a campus screen between lectures, the airport
lightbox --- image-led, typographically confident, nearly wordless. The joke is
the same joke as the brochure's, compressed to ad scale: an institution whose
whole identity is measurement, selling itself completely straight.

The genre is the **institutional display ad**: one hero image, one campaign
line, one supporting line, a call to action, the lockup. No sections, no charts,
no references. Where the research poster is dense, this is sparse --- 25-60
words total on the page.

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `../genre.md` for the voice floor (the marketing register bends it warm, but
  every language move holds --- no exclamation marks, no manifesto)
- `../../_shared/image-workflow.md` + `../../_shared/visual-style.md` for the
  hero image (the two-ink house style is the whole look)
- `../../_shared/output-naming.md` for slug, seed, output paths
- `../../_shared/typst-layout.md` only for the template import and PDF-metadata
  rules --- **not** the booklet sections
- `canon/roster.yml`, `canon/schools.yml` / `canon/schools.md`, and
  `website/src/content/outputs/*.yml` for anything the ad names (see "What the
  ad may reference")

## Doc identity

| Field                      | Value                                                                                                                                                |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Canonical name             | Slop University marketing poster                                                                                                                     |
| Format                     | **poster** (single page at screen aspect; orientation set by the layout roll)                                                                        |
| Visible title              | the campaign line --- **steering-derived** (an ad's title _is_ its campaign)                                                                         |
| Paper / orientation        | screen aspect via explicit `page-settings` --- landscape = `(width: 528mm, height: 297mm)` (16:9); portrait = `(width: 297mm, height: 528mm)` (9:16) |
| Theme                      | `light` by default; a **dark sibling** (`<name>-dark.pdf`) is compiled from the same source with `--input theme=dark` --- the e-signage artefact     |
| Cover lockup               | `slop`, overlaid white on the hero via `slop-overlay-masthead` (auto masthead hidden --- the image full-bleeds the page)                             |
| Filename prefix            | `slop-ad`                                                                                                                                            |
| PDF subfolder (`<group>`)  | `marketing-poster`                                                                                                                                   |
| Page count                 | exactly **1** (all content is `place`d; nothing can overflow)                                                                                        |
| Register                   | aspirational marketing, compressed to display-ad scale (see "Voice")                                                                                 |
| PDF metadata title formula | `This Slop University Advertisement Does Not Exist: <steering verbatim>`                                                                             |

The visible title is the campaign line, per the poster/paper/brochure title
policy; the satirical formula lives only in the PDF metadata. The university
name is carried by the lockup, never spelled out in the headline.

## Inputs

One free-text **steering prompt** --- the campaign's angle or theme. A phrase is
plenty. Examples:

- "come study where studying is studied"
- "we count what others overlook"
- "a degree in what actually happens"
- "the university that reads its own dashboards"
- "measurement is a calling"
- "open day --- see the instruments"

The prompt drives the campaign line, the supporting line, the hero scene, and
the rolled ad angle's content. The institutional voice is the only floor.

## What the ad may reference (canon cross-referencing)

Like the brochure, the ad markets the _existing_ fiction and invents nothing
institutional:

- **Roster researchers** (`canon/roster.yml`) --- a featured-researcher ad names
  one, with their canonical title and school; the quote rules from `brochure.md`
  › "Site cross-referencing" apply (warm, aspirational, no verifiable claim).
- **Schools, programs, units** --- only entities in `canon/schools.yml` /
  `canon/schools.md` (e.g. a program-intake ad names the Master of Priority
  Studies, never an invented degree).
- **Published outputs** --- a research-teaser ad quotes a real entry from
  `website/src/content/outputs/*.yml` (real title, real DOI in the small print).
  Never invent an output or DOI.
- **The site** --- the CTA points to `slop.university` (rendered text and/or the
  QR). No other URLs, no phone numbers, no street addresses, no dates more
  specific than a month or teaching period.

**Rankings are the trap in this genre.** A real-world ranking claim ("top 50
worldwide", any named ranking body) is a verifiable factual claim --- forbidden.
A ranking brag must be either **self-referential** (an instrument the fiction
owns: "ranked first on our own Indicator Commons composite, four quarters
running" --- the university grading itself with its own apparatus is the satire
working) or **semantically unfalsifiable** ("Australia's most measured
university"). If a claim could be checked against any real registry, recompose
it.

## The genre's structural skeleton

Everything is `place`d over the full-bleed hero; there is no flowed body.

| Element         | Placement                       | Notes                                                                                                     |
| --------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Hero image      | full-bleed, whole page          | the run's one image; house-style scene keyed to the campaign; scrims baked at prep (see Imagery)          |
| Masthead        | top, on the spine               | `slop-overlay-masthead` (white lockup, gold spine bisected around it); auto masthead hidden               |
| Campaign line   | lower third, left-anchored      | steering-derived, ≤ 8 words, white display type (~64pt landscape / ~54pt portrait), ≤ 2 lines             |
| Supporting line | under the campaign line         | one sentence, ≤ 18 words, white/near-white (~17pt); carries the rolled angle's substance                  |
| Angle furniture | with the supporting line        | the rolled angle's one extra element (researcher name-line, program name, output title + DOI small print) |
| CTA line        | under the supporting block      | short imperative + `slop.university` (~13pt); gold rule above it                                          |
| QR              | bottom-right                    | `slop-qr-code("https://slop.university/", ...)` --- white-on-transparent reads over the baked-dark region |
| Social line     | bottom-left, with the CTA block | `slop-social-line(fill: white)` --- butterfly + `@slop.university` + `#slopU`; fixed furniture            |

Total on-page text: 25-60 words. If a draft wants a third paragraph, it has
drifted toward the brochure --- cut it.

## Per-run variation rolls

Roll once per run, upfront. The masthead, QR, social line, CTA presence, and the
voice floor are fixed.

### Layout (roll: landscape / portrait, 50/50)

Same signage split as the research poster: roll 1-2, take 1 as 16:9 landscape
(528 × 297 mm), 2 as 9:16 portrait (297 × 528 mm). Both drive the live e-signage
panels (`/signage/landscape`, `/signage/portrait`). Roll first --- it sets the
hero's aspect and the type sizes. Content is identical across the two; only
geometry differs (see the table in "Typst structure").

### Ad angle (roll uniform across five)

**a) come-study (prospectus).** Selling the student experience. Supporting line
is you-focused ("you'll learn to see what everyone else stops noticing"); angle
furniture is a canon program name where it fits. CTA invites applying.

**b) featured researcher.** One roster researcher as the face of the
institution. Angle furniture is their name-line (canonical name · title ·
school) plus a short warm quote (the brochure's marketing-quote rules). The hero
depicts them in a field scene --- generate it with their headshot as the lead
reference (the person-hero mechanics in `../../_shared/visual-style.md`), at
this run's aspect. CTA invites meeting the researchers (people page exists on
the site).

**c) ranking brag.** The metric win, per the ranking rules above ---
self-referential instrument or unfalsifiable superlative. Angle furniture is the
brag rendered as a stat lockup: one big number or ordinal ("№ 1", "four quarters
running") in gold display type above the supporting line. This is the angle
where the satire is sharpest; play it completely straight.

**d) program / campaign event.** An intake or standing event from the canon
(Master of Applied Measurement intake, Open Day, Demo Quarter public session).
No dates more specific than a month or teaching period ("Open Day, this
spring"). CTA invites registering interest.

**e) research teaser.** One real published output as the hook ("we found out.
read it."). Angle furniture is the output's real title + `doi:` in small print.
Prefer a recent, picturable output; skip this angle if the ledger has nothing
that carries a headline.

### CTA reservoir

One per run (grow over time): "Come and count with us", "Apply now", "See the
work", "Visit us --- slop.university", "Register your interest", "Meet the
researchers". Render with `slop.university` unless the QR + social line already
crowd the corner.

### Hero scene

Rolled with the angle: the scene is the campaign's object in the two-ink house
style --- an instrumented everyday setting (the bus stop itself, a supermarket
queue, a kitchen bench with a sensor), a person-scene for angle (b), a
campus-adjacent scene for (a)/(d). The prompt formula and refs come from
`../../_shared/visual-style.md` + `references/slop-style/`; this preset's hero
is the run's single strongest image --- it does the selling.

## Voice (display-ad marketing register)

Defers to `../genre.md` for the floor and compresses the brochure's register to
ad scale:

- **The campaign line is a slogan, not a sentence.** Short, declarative, no
  punctuation beyond an em-dash or full stop. The steering prompt is its seed
  --- sharpen it, don't pad it.
- **The supporting line does the one piece of persuading.** Warm, second person
  where the angle wants it, hedged where it commits ("consistently among the
  most cited voices in measurement studies" --- unfalsifiable).
- **No exclamation marks** --- the genre's confidence is typographic, not
  punctuational. This is the rule most display ads break; ours doesn't, and the
  restraint is part of the deadpan.
- **Reads straight.** No winks, no "(really)", no self-aware hashtag beyond the
  fixed `#slopU`. The satire is carried by what the institution chooses to brag
  about, never by how it phrases the brag.

## Imagery (preset specifics for image-workflow.md)

- Image folder: `output/slop-ad-<slug>-<seed>-images/`
- **One image**: `hero.jpg`, full-bleed. Aspect per the layout roll ---
  `--aspect-ratio 16:9` (landscape) or `--aspect-ratio 9:16` (portrait), 4K (it
  fills the whole panel). House style per `../../_shared/visual-style.md`, 3-5
  refs from `references/slop-style/`; angle (b) leads with the researcher's
  headshot as reference.
- **Scrim bake (both orientations).** The overlays need darkening baked into the
  JPEG --- never typst gradient scrims (they render black in iOS Safari/Firefox;
  see `../../_shared/typst-layout.md` › "PDF transparency"). Centre-crop to the
  page aspect, then multiply in a uniform legibility base, a darker top strip
  (lockup) and a darker lower-third (campaign block):

  ```bash
  # landscape --- crop to 16:9 exactly (528x297), then bake
  W=$(identify -format %w hero.jpg); H=$(( W * 297 / 528 ))
  convert hero.jpg -gravity center -crop ${W}x${H}+0+0 +repage \
    \( -size ${W}x${H} xc:'gray(70%)' \) -compose multiply -composite \
    \( -size ${W}x$(( H * 30 / 100 )) gradient:'gray(35%)'-white -background white -gravity north -extent ${W}x${H} \) -compose multiply -composite \
    \( -size ${W}x$(( H * 55 / 100 )) gradient:white-'gray(22%)' -background white -gravity south -extent ${W}x${H} \) -compose multiply -composite \
    -quality 92 hero.jpg

  # portrait --- crop to 9:16 exactly (297x528), same bake bands
  H=$(identify -format %h hero.jpg); W=$(( H * 297 / 528 ))
  convert hero.jpg -gravity center -crop ${W}x${H}+0+0 +repage \
    \( -size ${W}x${H} xc:'gray(70%)' \) -compose multiply -composite \
    \( -size ${W}x$(( H * 22 / 100 )) gradient:'gray(35%)'-white -background white -gravity north -extent ${W}x${H} \) -compose multiply -composite \
    \( -size ${W}x$(( H * 45 / 100 )) gradient:white-'gray(22%)' -background white -gravity south -extent ${W}x${H} \) -compose multiply -composite \
    -quality 92 hero.jpg
  ```

  (The crop matches `fit: cover` on the full page, so the baked bands land
  exactly under the overlaid text. If the campaign block still reads faintly,
  deepen the south mask's dark end and re-run the bake --- don't move the type.)

- No inline images, no charts, no parity spare.

## Style references

Read before generating:

- **Overlay mechanics**: `research-poster.md` › Skeleton B (feature-top) --- the
  overlaid masthead, baked-scrim discipline, and `place` geometry this preset
  generalises to the full page.
- **Layout core source**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/lib.typ`
  --- `page-settings`, `hide`, and `overlay-masthead`.
- **Register**: `brochure.md` › "Voice" and "Site cross-referencing" (this
  preset compresses both); `../genre.md` for the floor.

## Typst structure

One parametric skeleton; the roll sets the geometry constants:

| Knob            | landscape (16:9)                   | portrait (9:16)                    |
| --------------- | ---------------------------------- | ---------------------------------- |
| `page-settings` | `(width: 528mm, height: 297mm)`    | `(width: 297mm, height: 528mm)`    |
| Campaign type   | 64pt                               | 54pt                               |
| Campaign block  | `dx: 2.6cm, dy: -3.4cm`, width 60% | `dx: 2.2cm, dy: -4.2cm`, width 80% |
| `pdfinfo` size  | ≈ 1497 × 842 pt                    | ≈ 842 × 1497 pt                    |

```typst
#import "@local/slop-university-brand:0.1.0": (
  slop, slop-colors, slop-doc-theme, slop-overlay-masthead, slop-qr-code,
  slop-social-line,
)

#set document(
  title: "This Slop University Advertisement Does Not Exist: <steering prompt verbatim>",
)

#let page-w = 528mm  // per the roll (297mm portrait)
#let page-h = 297mm  // per the roll (528mm portrait)
#let m = 20mm        // nominal margin; everything is placed relative to it

#show: doc => slop(
  title: "",
  page-settings: (width: page-w, height: page-h),
  margin: (left: m, right: m, top: m, bottom: m),
  config: (
    theme: slop-doc-theme,
    // The hero covers the page: hide everything the template would draw
    // behind it and overlay our own masthead.
    hide: ("page-numbers", "title-block", "masthead"),
  ),
  doc,
)

// ── Hero: full-bleed, whole page. Scrims are baked into hero.jpg at prep
//    (see Imagery) --- never typst gradient scrims. ──
#place(top + left, dx: -m, dy: -m, box(
  width: page-w,
  height: page-h,
  clip: true,
  {
    image(
      "/output/slop-ad-<slug>-<seed>-images/hero.jpg",
      width: 100%,
      height: 100%,
      fit: "cover",
    )
    // White lockup on the gold spine, bisected around the crest --- spans the
    // full page height (the whole page is the "band").
    slop-overlay-masthead(page-h, variant: "white", dy: 1.2cm, height: 1.7cm)
    // QR bottom-right
    place(bottom + right, dx: -1.8cm, dy: -1.8cm, slop-qr-code(
      "https://slop.university/",
      width: 2.6cm,
      config: (theme: slop-doc-theme),
    ))
    // ── Campaign block, lower-left over the baked-dark lower third ──
    place(bottom + left, dx: 2.6cm, dy: -3.4cm, box(width: 60% * page-w)[
      // (angle c only) stat lockup above the campaign line, gold display type
      // #text(fill: slop-colors.gold, size: 40pt, weight: "medium")[<№ 1 / four quarters running>]
      #text(fill: white, size: 64pt, weight: "medium")[<campaign line --- steering-derived, ≤ 2 lines>]
      #v(0.45em)
      #text(fill: rgb("#ececec"), size: 17pt)[<supporting line --- the angle's one persuading sentence>]
      // (angle furniture: researcher name-line / program name / output title +
      //  doi small print --- one small muted line, ~11pt)
      #v(0.7em)
      #line(length: 96mm, stroke: 0.75pt + slop-colors.gold)
      #v(0.55em)
      #text(fill: white, size: 13pt)[<CTA from the reservoir> --- slop.university]
      #v(0.5em)
      #slop-social-line(size: 10pt, fill: white)
    ])
  },
))
```

Notes:

- The document body is empty --- every element is `place`d inside the hero box,
  so the poster cannot overflow to a second page and there is no fill probe.
- The dark sibling comes free: the overlays are already white-on-baked-scrim
  (the dark idiom), and `config: (theme: slop-doc-theme)` + the QR's `config`
  are the only theme-sensitive pieces. Compile both per the shared workflow.
- The social line is `fill: white` here (it sits on the baked scrim), unlike the
  research poster's muted footer rendering.

## Compile and one-page fit

1. `typst compile --root . output/slop-ad-<slug>-<seed>.typ output/pdf/marketing-poster/slop-ad-<slug>-<seed>.pdf`
   (create `output/pdf/marketing-poster/` if absent), then the dark sibling with
   `--input theme=dark` →
   `output/pdf/marketing-poster/slop-ad-<slug>-<seed>-dark.pdf`.
2. `pdfinfo`: expect **1 page** at the rolled screen aspect (≈ 1497 × 842 pt
   landscape / 842 × 1497 pt portrait).
3. Eyeball both renders at thumbnail size --- an ad must land at a glance. The
   campaign line must clear the lockup and the QR; the type must read over the
   bake (deepen the mask, not the text, if it doesn't).

## Pre-ship checklist (preset-specific)

Generic format-aware items live in `../SKILL.md`. Marketing-poster items:

- [ ] Single screen-format page in the rolled orientation; `pdfinfo` confirms 1
      page; dark sibling compiled from the same source
- [ ] Full-bleed house-style hero with baked scrims (no typst gradient scrims);
      white overlaid lockup on the bisected gold spine (auto masthead hidden);
      QR to slop.university
- [ ] Campaign line is steering-derived, ≤ 8 words, ≤ 2 lines; total on-page
      text 25-60 words; no section headings, charts, or references
- [ ] `#slop-social-line(fill: white)` present (butterfly + `@slop.university` +
      `#slopU`); CTA from the reservoir
- [ ] Everything the ad names is canon: researcher (with canonical title +
      school), program/unit, or a real published output with its real DOI;
      nothing institutional invented
- [ ] No verifiable claims: no real ranking bodies, no dates beyond
      month/teaching period, no dollar figures, no external URLs; any ranking
      brag is self-referential or unfalsifiable
- [ ] Register holds: no exclamation marks, no winks, reads straight at a bus
      stop
- [ ] PDF metadata title is
      `This Slop University Advertisement Does Not Exist: <steering verbatim>`;
      no other metadata fields populated

## Common failure modes (preset-specific)

- **Reads like a poster-sized brochure**: too many words, a second paragraph, a
  stat-card impulse. Cut to the skeleton's word budget; one idea per ad.
- **The brag is checkable**: a named ranking, a percentage presented as fact, a
  dated promise. Recompose as self-referential or unfalsifiable.
- **Voice cracks into hype**: exclamation marks, imperative stacking ("Apply
  now! Don't wait!"), superlative chains. One CTA, no exclamation marks.
- **The campaign line restates the university name**: the lockup carries the
  name; the headline carries the idea.
- **Type washes out on the hero**: the bake isn't deep enough --- deepen the
  relevant mask band and re-run; never shrink or shadow the type instead.
- **An invented program, person, or output**: hard failure; only canon entities
  and real ledger outputs may appear.

## What this preset is not

- Not a research poster: no sections, charts, references, or fill probe --- and
  not a place to restate that preset's rules.
- Not a brochure: one page, one idea, no feature sections. If it needs a second
  idea, it's a brochure run.
- Not a place for new genre conventions --- cross-preset voice doctrine belongs
  in `../genre.md`; canon admission rules belong in `canon/`.
