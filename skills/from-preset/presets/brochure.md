---
name: brochure
description:
  Slop University glossy marketing brochure --- an image-led institutional
  showcase in the aspirational prospectus register. Steering-driven campaign
  theme; the one preset that quotes and cross-references the rest of the site
  (published outputs by DOI, canon schools and roster researchers). Booklet
  format, lighter and shorter than strategy/impact-report.
---

# Brochure preset

Produce one Slop University marketing brochure from a single steering prompt.
The output should read as the glossy showcase publication a real university
prints for prospective students, donors, and partners --- image-led, punchy,
aspirational --- and be indistinguishable from one to a tea-room reader, with
the Slop University lockup on the cover and back.

The genre is present-and-near-future and promotional: a brochure sells what the
institution _is_ and _offers_, in warm confident marketing prose. It is not
retrospective (that's `impact-report`) and not a governance document (that's
`strategy`). Think campus prospectus, case-for-support, or research-showcase
booklet.

The distinctive move: **the brochure references the rest of the site.** Unlike
every other preset, it is allowed --- encouraged --- to name published Slop
University research outputs (by real title and DOI), name canon schools/units,
and quote canon roster researchers by name. It is a marketing piece _about the
university that already exists in the fiction_, so it draws on that fiction's
real (fabricated) record rather than inventing fresh institutional facts. See
"Site cross-referencing" below --- this is a hard rule, not a flourish.

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `../genre.md` for voice doctrine and steering rules
- `../../_shared/typst-layout.md` for template import, metadata, back cover,
  parity-fix workflow
- `../../_shared/image-workflow.md` for parallel image generation
- `../../_shared/visual-style.md` for the two-ink house imagery style
- `../../_shared/chart-workflow.md` for the chart pipeline (only if a run rolls
  a chart --- charts are optional here)
- `../../_shared/output-naming.md` for slug, seed, output paths
- `canon/roster.yml` and `canon/schools.md`/`canon/schools.yml` for people and
  org units
- `website/src/content/outputs/*.yml` for the published outputs the brochure may
  cite (see "Site cross-referencing")

## Doc identity

| Field                      | Value                                                                                 |
| -------------------------- | ------------------------------------------------------------------------------------- |
| Canonical name             | Slop University brochure                                                              |
| Cover title                | **steering-derived** --- a short campaign line (a brochure's title _is_ its campaign) |
| Cover subtitle             | a supporting line (steering-derived or from the Cover-subtitle reservoir)             |
| Cover lockup               | `slop`                                                                                |
| Back-cover lockup          | `slop` (`#slop-back-cover(config: (bleed: 3mm))`)                                     |
| Filename prefix            | `slop-brochure`                                                                       |
| PDF subfolder (`<group>`)  | `brochure`                                                                            |
| Page-count range           | 8-12, even                                                                            |
| Register                   | aspirational marketing, present / near-future (warm, confident, image-led)            |
| PDF metadata title formula | `This Slop University Brochure Does Not Exist: <steering verbatim>`                   |

Unlike the strategy and impact-report booklets (fixed cover titles), the
brochure **derives its cover title from the steering line** --- a campaign
tagline, not a fixed document name. This matches the poster/paper title policy
and means the visible title varies per run. Keep it short (a few words to a
short phrase); the university name is carried by the lockup, not the title.

The `slop` lockup is the university-level Slop University wordmark. PDF metadata
title is the deliberate satirical tell (not visible on rendered pages). No other
metadata fields populated. Slug is derived from the steering prompt per
`../../_shared/output-naming.md`.

## Inputs

One free-text **steering prompt** --- the brochure's campaign theme. 1-3 short
sentences, or a phrase. Examples:

- "why study measurement"
- "a university built around the question, not the answer"
- "research that pays its way"
- "the case for the counted"
- "come and count with us"
- "we measure the everyday"

The prompt is the campaign theme. The institutional voice (see `../genre.md`) is
the only floor; the cover line, section headings, featured schools/outputs,
pull-quotes, stat cards, and imagery all bend to the prompt.

## Site cross-referencing (the defining feature --- hard rule)

The brochure markets the _existing_ fiction, so it quotes and references real
site content rather than inventing institutional facts.

- **Published outputs.** Read every `website/src/content/outputs/*.yml`. A
  brochure may feature 2-4 published outputs: use the entry's real `title` (and
  `subtitle`), its real `doi`, its `authors`, and paraphrase its `summary` into
  one marketing sentence. Render a citation the reader could look up:
  `<Title> --- doi:10.5555/slop.<seed>`. **Never invent an output, a title, or a
  DOI**; if fewer than 2 published outputs exist, feature the schools and people
  instead and skip the outputs showcase.
- **Schools, units, labs.** Name only entities that exist in `canon/schools.yml`
  / `canon/schools.md`, with their canonical names and (where present) blurbs.
  Don't invent an org unit.
- **Roster researchers.** Name only `canon/roster.yml` people, with their
  canonical `title` and `school`. A brochure quote from a named researcher is a
  marketing quote --- warm, aspirational, institutional; it must obey the
  genre's no-verifiable-claims rule (`../genre.md`). The Director/VC voice,
  where used, stays a role, never a name (as in the other booklets).
- **The site itself.** A call-to-action may point to `slop.university` (the
  fiction's real home). No other URLs, addresses, phone numbers, dates, dollar
  figures, or rankings --- those are verifiable and off-limits.

When a run features outputs, prefer a spread of schools/authors over stacking
the same author, and lean toward under-represented schools (the publish flow's
imbalance steering, applied to what the brochure showcases).

## The genre's structural skeleton

| Section                | Length            | Notes                                                                                                                             |
| ---------------------- | ----------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Cover                  | 1 page            | Campaign line (steering-derived) + supporting subtitle; `slop` lockup; hero image                                                 |
| Welcome / invitation   | ~200 words        | Aspirational opener framing the campaign theme; heading from reservoir; role-signed if signed at all (never a name)               |
| At a glance            | ~1 page           | Marketing stat cards in a `#grid` of `slop-highlight-card` (3-4); reach/scale/research framing, no verifiable figures             |
| Feature sections × N   | ~1-1.5 pages each | N = 3-4; each showcases a school / research theme / programme: framing + inline image + one roster pull-quote [+ chart if rolled] |
| Featured research      | ~0.5-1 page       | 2-4 published outputs cited by real title + DOI, each with a one-sentence marketing gloss (see "Site cross-referencing")          |
| Our people             | ~0.5 page         | 2-3 roster researchers profiled in a sentence each (canonical name + title + school); optional if a feature already carried them  |
| Come and join us (CTA) | ~150 words        | Warm close + call to action; may point to `slop.university`                                                                       |
| Back cover             | 1 page            | `#slop-back-cover()`                                                                                                              |

Total: 8-12 pages, even. No manual page breaks (the template breaks after the
contents). Lengths are baselines; per-run variation is scoped by the persona
below.

A brochure has **no contents page by default** --- it's short and image-led. If
a run lands at the top of the range (12 pages) a one-line contents strip is
optional; below that, omit `#outline`.

## Per-run variation rolls

Roll once per run, upfront (the orchestrator workflow lists the order). The
cover early-matter, genre voice, image workflow, and typst layout are off-limits
to variation.

### Document persona

Roll one persona before other variation. It sets who the brochure is selling to,
and cascades into the feature mix and voice.

Roll uniform across the four:

**a) prospectus** --- selling the university to prospective students. Features
lean toward programmes and student experience; people section prominent; warm,
you-focused ("you'll join a School that…"). CTA is an invitation to apply/enrol.

**b) case-for-support** --- selling to donors and partners. Features lean toward
research impact and partnership; featured-research section prominent (outputs do
heavy lifting); register is confident-institutional, "your support makes X
possible". CTA is an invitation to partner/give.

**c) research showcase** --- selling the university's ideas. Features are
research themes; featured-research section is the spine; roster researchers
quoted as the voices of the work. Register is intellectually assured. CTA points
to the outputs on `slop.university`.

**d) civic / place** --- selling the university's role in its community and
public life. Features lean toward engagement and public benefit; pull-quotes
communal; register warm-public. CTA is an invitation to visit/connect.

### Section-name reservoirs

One choice per section per run. Grow over time; aim for ~4-5 entries each.

| Section role      | Reservoir                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------ |
| Welcome           | "Welcome", "An invitation", "Why Slop University", "Come and count with us"                |
| At a glance       | "At a glance", "Slop University in brief", "The short version", "By the numbers"           |
| Feature heading   | "What we do", "Our research", "Where ideas count", "The work"                              |
| Featured research | "Read the work", "From our researchers", "Published this year", "Ideas in print"           |
| Our people        | "Our people", "The people behind the work", "Meet the researchers", "Who you'll work with" |
| Call to action    | "Come and join us", "Your next step", "Get in touch", "Be part of it"                      |
| Cover subtitle    | "An invitation", "A university that counts", "Ideas worth measuring", "Come and see"       |

### Structural counts (scoped by persona)

| Count                | prospectus    | case-for-support  | research showcase | civic / place |
| -------------------- | ------------- | ----------------- | ----------------- | ------------- |
| Feature sections (N) | 3-4           | 3                 | 3-4               | 3             |
| Featured outputs     | 2             | 3-4               | 3-4               | 2-3           |
| People profiled      | 3             | 2                 | 2-3               | 2             |
| At-a-glance cards    | 4             | 4                 | 3                 | 3             |
| Pull-quotes          | 1 per feature | half the features | 1 per feature     | 1 per feature |
| Charts               | 0             | 0-1               | 0-1               | 0             |

Featured-output counts are capped by how many published outputs actually exist;
never fabricate to hit the range.

### Imagery-forward bias

The brochure is the most image-led preset. Every feature section carries an
inline image; the cover and one feature should be the run's strongest scenes.
Charts are the exception, not the rule (glossy sells with photography, not data)
--- roll a chart only under the case-for-support or research-showcase persona,
and at most one.

## Imagery (preset specifics for image-workflow.md)

- Image folder: `output/slop-brochure-<slug>-<seed>-images/`
- Prompts: 1 cover (3:4 portrait) + 4 inline (16:9 landscape); reserve a 5th
  inline as the parity-fix spare. All in the two-ink house style
  (`../../_shared/visual-style.md`), steered by `references/slop-style/`.
- Resolution: cover at `--resolution 4K` (it full-bleeds the A4 cover); inlines
  at `--resolution 2K` --- they land as part-page feature-section figures, so 2K
  is ample and 4K would just be wasted pixels and generation time.
- Cover image should be the run's most aspirational, campaign-worthy scene ---
  the brochure's hero. Inline scenes match their feature (a lab, a public
  lecture, fieldwork in an ordinary street or market, a reading room), keyed to
  the campaign theme.
- Record an explicit `inline-N` → section assignment when planning.

## Chart workflow (preset-specific, optional)

Charts are optional here and off by default (see "Imagery-forward bias"). If a
run rolls one, the full pipeline and brand-styling rules live in
`../../_shared/chart-workflow.md`. Brochure specifics: chart folder
`output/slop-brochure-<slug>-<seed>-charts/`; one chart maximum; keep it a clean
marketing figure (a single trend or a simple comparison), not a dense analytic
plot. Types drawn from `{line, area, grouped-bar}`.

## Style references

Read these before generating:

- **Closest typst reference**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/examples/design.typ`
  --- highlight-card grid, feature-page, and inline-figure usage (under the
  core's neutral names). Copy the structural moves --- NOT the import block or
  content; this preset imports the slop brand package (`slop-*` names).
- **Genre PDF**: `~/.nb/home/anu-corporate-plan-2026-v5.pdf` --- a real
  institutional publication for glossy visual conventions (tone only; imagery
  follows the two-ink house style).
- **Layout core source**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0` --- for
  the available helpers. Branding comes from
  `@local/slop-university-brand:0.1.0`.

## Typst structure

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-back-cover, slop-colors, slop-highlight-card
// slop-inline-figure only if a chart is rolled:
//   #import "@local/slop-university-brand:0.1.0": slop-inline-figure
//   #import "/output/slop-brochure-<slug>-<seed>-charts/chart-1.typ": chart as chart-1

#set document(
  title: "This Slop University Brochure Does Not Exist: <steering prompt verbatim>",
)

#show: slop.with(
  title: "<campaign line --- steering-derived>",
  subtitle: "<supporting line>",
  cover: read("/output/slop-brochure-<slug>-<seed>-images/cover.jpg", encoding: none),
  config: (bleed: 3mm),  // 3mm print bleed: trimmed, saddle-stitched booklet
)

// No #outline by default (short, image-led). Add only at the top of the range.

= Welcome
[~200 words, aspirational opener framing the campaign theme]
#figure(image("/output/slop-brochure-<slug>-<seed>-images/inline-1.jpg"))

= At a glance
[one framing sentence]

#grid(
  columns: (1fr, 1fr),
  column-gutter: 0.8em,
  row-gutter: 0.8em,
  slop-highlight-card("community", "<stat 1 title>")[<framing, no verifiable figure>],
  slop-highlight-card("flask", "<stat 2 title>")[<framing>],
  slop-highlight-card("globe", "<stat 3 title>")[<framing>],
  slop-highlight-card("graduation-cap", "<stat 4 title>")[<framing>],
  // 3 or 4 cards per persona
)

= What we do

== <Feature 1 --- a canon school / research theme / programme>
[framing paragraph, present-tense marketing prose]
#figure(image("/output/slop-brochure-<slug>-<seed>-images/inline-2.jpg"))

#quote(block: true)[
  "<marketing pull-quote --- no verifiable claim>"
  #align(right)[--- <Roster Name>, <canonical title>, <School>]
]

== <Feature 2 …>
[same shape]

= Read the work
[one framing sentence, then the featured published outputs]

// Each featured output cites a REAL entry from website/src/content/outputs/:
// real title, real doi, one-sentence marketing gloss of its summary.
- *<Real output title>* --- <one marketing sentence>. #text(size: 0.85em)[doi:10.5555/slop.<seed>]
- *<Real output title>* --- <one marketing sentence>. #text(size: 0.85em)[doi:10.5555/slop.<seed>]

= Our people
[2-3 roster researchers, a sentence each: canonical name + title + school]

= Come and join us
[~150 words; warm close + CTA; may point to slop.university]

#slop-back-cover(config: (bleed: 3mm))
```

### Highlight cards (At a glance)

One card per marketing stat; 3 or 4 per persona. The card helper, grid shapes
per count, and icon-name lookup live in `../../_shared/typst-layout.md` ›
"Highlight cards and icon lookup". Card bodies carry framing, not verifiable
figures (a real report says "graduates across every state"; the notch too far is
"93% employment within four months").

### Pull-quotes

Use `#quote(block: true)` (typst's block-quote form). Per the known template bug
(the core rule drops `attribution:`), carry the attribution inside the body,
right-aligned --- see the skeleton above and `impact-report.md` › "Pull-quotes".
Attributions here name **roster researchers** (canonical name + title), the one
preset where a marketing quote is spoken by a named person.

### Featured-research citations

Render each as a real title + a lookup-able DOI (`doi:10.5555/slop.<seed>` from
the entry's `doi` field). This is the recursive conceit: a brochure that markets
the university by pointing at its own published record. The reader can resolve
every DOI on the site's `/doi/` route --- so every one must be real.

## Pre-ship checklist (preset-specific)

Generic checklist items live in `../SKILL.md`. Brochure-specific:

- [ ] Cover title is a short steering-derived campaign line (NOT a fixed
      document name); `slop` cover and back-cover lockups
- [ ] Every featured output, DOI, school, unit, and named person is real ---
      published outputs from `website/src/content/outputs/`, org units from
      `canon/schools`, people from `canon/roster.yml` with canonical titles.
      Nothing institutional is invented
- [ ] No verifiable claims anywhere (no dollar figures, dated commitments,
      rankings, percentages presented as fact, real URLs beyond
      `slop.university`, addresses, or phone numbers)
- [ ] Document persona rolled at planning time; feature count, featured-output
      count, people count, card count, and pull-quote frequency match its column
- [ ] Featured-output count did not exceed the number of published outputs that
      actually exist (never fabricated to fill the range)
- [ ] Every feature section carries an inline image; charts absent unless a
      case-for-support / research-showcase run rolled exactly one
- [ ] Section names came from the reservoirs; no `#outline` unless at the top of
      the page range
- [ ] Page count is even and within **8-12 pages**

## Common failure modes (preset-specific)

- **Invented output or DOI**: hard failure --- the whole conceit is that the
  featured research is real and resolvable. Re-read
  `website/src/content/ outputs/*.yml` and cite only what's there; drop the
  showcase if too few exist.
- **A marketing quote makes a checkable claim**: rewrite to a hedged,
  aspirational framing (the genre's no-verifiable-claims rule applies to quotes
  too).
- **Reads like a strategy or impact report**: wrong register. The brochure is
  present-tense promotional and image-led, not future-tense governance
  (strategy) or past-tense reflective (impact-report). If it grows pillars,
  KPIs, or a five-year retrospective, it's drifted.
- **Chart-heavy**: a glossy brochure sells with photography. If a run has more
  than one chart, or a chart where an image belongs, it's off-genre.

## What this preset is not

- Not a fact-checked prospectus. The output is generative satire.
- Not the strategy or impact-report preset (see failure modes).
- Not a place to invent institutional facts. It markets the _existing_ fiction
  --- canon schools/people and published outputs --- and invents nothing about
  the institution beyond marketing framing.
- Not a place for new genre conventions. A convention that applies to multiple
  presets belongs in `../genre.md`.
