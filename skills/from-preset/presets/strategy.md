---
name: strategy
description:
  Slop University Strategic Plan 2026-2031 --- forward-looking institutional
  voice, steering-driven topic, pillar/KPI/phase scaffolding. The flagship
  preset; output should be indistinguishable from a real plan to a tea-room
  reader and recognisably institutional at a glance.
---

# Strategy preset

Produce one Slop University Strategic Plan 2026-2031 from a single steering
prompt. The output should be indistinguishable from a real plan to a tea-room
reader and recognisably institutional at a glance.

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `../genre.md` for voice doctrine and steering rules
- `../../_shared/typst-layout.md` for template import, metadata, back cover,
  parity-fix workflow
- `../../_shared/image-workflow.md` for parallel image generation
- `../../_shared/output-naming.md` for slug, seed, output paths

## Doc identity

| Field                      | Value                                                               |
| -------------------------- | ------------------------------------------------------------------- |
| Canonical name             | Slop University Strategic Plan 2026-2031                            |
| Cover title                | `Slop University Strategic Plan 2026-2031`                          |
| Cover subtitle             | varies between runs                                                 |
| Period covered             | 2026-2031 (fixed)                                                   |
| Cover lockup               | `slop` (the Slop University lockup, via the brand package)          |
| Back-cover lockup          | `slop` (`#slop-back-cover(config: (bleed: 3mm))`)                   |
| Filename prefix            | `slop-strategy`                                                     |
| Page-count range           | 16-20, even                                                         |
| Register                   | future-tense (will, shall, by 2031)                                 |
| PDF metadata title formula | `This Slop University Strategy Does Not Exist: <steering verbatim>` |

The PDF metadata title is the deliberate satirical tell --- not visible on
rendered pages. No other metadata fields populated (no author, description,
keywords, date, Claude attribution).

Slug is derived from the steering prompt per `../../_shared/output-naming.md`.

## Inputs

One free-text **steering prompt**. 1-3 short sentences, or a phrase. Examples:

- "lean into sovereign capability"
- "post-pandemic resilience and place"
- "rise to the AI moment"
- "regional engagement and community knowledge"
- "research excellence at scale"

The prompt is the document's topic. The institutional voice (see `../genre.md`)
is the only floor; everything else --- pillar names, KPIs, foreword, vision,
initiatives, charts --- bends to the prompt.

## The genre's structural skeleton

| Section                                     | Length          | Notes                                                                                                                                                                                                                                       |
| ------------------------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cover                                       | 1 page          | Title, period, Slop University lockup, hero image                                                                                                                                                                                           |
| (Optional) Chancellor's message             | ~150 words      | Only if rolled in planning                                                                                                                                                                                                                  |
| Foreword from the VC                        | ~250 words      | Heading drawn from the Foreword reservoir. Touchstones: national interest, research excellence, education, place                                                                                                                            |
| Executive summary                           | ~400 words      | Heading is fixed. The pillars-on-one-page move; render the pillars as a `#grid` of `slop-highlight-card`s (one per pillar; grid shape follows the pillar count --- see "Per-run variation rolls › Structural counts")                       |
| (Optional) Our values                       | 3-5 × ~30 words | Only if rolled                                                                                                                                                                                                                              |
| Strategic context                           | ~600 words      | Heading drawn from the Strategic-context reservoir                                                                                                                                                                                          |
| Vision                                      | ~150 words      | Heading drawn from the Vision reservoir; one sentence + one paragraph unpacking it                                                                                                                                                          |
| (Optional) "From / To" transformation table | 4-6 rows        | Only if rolled; sits as intro to the pillars section                                                                                                                                                                                        |
| Strategic pillars × N                       | ~1.5 pages each | N = 3-5 (see "Structural counts"). Heading drawn from the Pillars reservoir. Each pillar: name, premise, 2-5 initiatives, 2-4 KPIs (counts shared across all pillars in the run); section labels drawn from the scaffolding-label reservoir |
| Implementation phases                       | ~400 words      | 3-5 phases spanning 2026-2031 contiguously; verb-set drawn from the Implementation-phase reservoir; section heading drawn from the Implementation reservoir                                                                                 |
| (Optional) "How we developed this plan"     | ~150 words      | Only if rolled; sits near governance                                                                                                                                                                                                        |
| Governance & accountability                 | ~250 words      | Heading drawn from the Governance reservoir; Council, Executive, reporting cadence                                                                                                                                                          |
| Conclusion                                  | ~150 words      | Heading drawn from the Conclusion reservoir; future-tense aspirational close                                                                                                                                                                |
| (Optional) Glossary / acronyms              | ~10-20 entries  | Only if rolled; sits before back cover                                                                                                                                                                                                      |
| Back cover                                  | 1 page          | Inverse-themed full-page Slop University lockup; emit via `#slop-back-cover()`                                                                                                                                                              |

Total: ~6,500 words at the default 4-pillar / 3-initiative / 3-KPI shape. Counts
at the lower bound (3 / 2 / 2 / no optionals / 3 phases) trim ~1,500 words;
counts at the upper bound (5 / 5 / 4 / 3 optionals / 5 phases) add ~2,000 words.

Word counts are budgets, not targets. Vary by ±20% between runs.

## Per-run variation rolls

Before drafting, decide all variation upfront --- section names, structural
counts, optional sections, scaffolding labels. The orchestrator workflow lists
the order to roll them; this section defines the pools.

The early matter (cover, contents) and the genre voice / image workflow are
off-limits to variation; they're fixed elsewhere.

### Section-name pools

Sections from the Foreword onwards draw from per-section reservoirs (one choice
per section per run). The "Executive summary" name is fixed --- it's a
load-bearing genre convention; varying it would feel forced.

| Section role      | Reservoir                                                                                                                                 |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| Foreword          | "Foreword from the Vice-Chancellor", "Vice-Chancellor's foreword", "A message from the Vice-Chancellor", "Vice-Chancellor's introduction" |
| Strategic context | "Strategic context", "Operating environment", "The world in 2026", "Where we stand", "Our context"                                        |
| Vision            | "Vision", "Our ambition", "Our aspiration", "Where we are headed", "What we will become"                                                  |
| Pillars           | "Strategic pillars", "Strategic priorities", "Our agenda", "Our priorities", "Our focus areas"                                            |
| Implementation    | "Implementation phases", "Roadmap", "Delivering this plan", "Phasing", "How we will deliver this plan"                                    |
| Governance        | "Governance & accountability", "How we will deliver", "Accountability and review", "Oversight and review"                                 |
| Conclusion        | "Conclusion", "Looking ahead", "The decade ahead", "Our next chapter"                                                                     |

Reservoirs can grow over time; aim for ~4-5 entries each. Do not introduce new
section roles here --- that's structural variation, not naming.

### Implementation-phase reservoir

Phase count: **3-5 phases per run**. Phases span 2026-2031 contiguously (no
gaps). Pick one verb-set per run from this reservoir, or build a new one in the
same register:

- Establish 2026 / Build 2027-28 / Embed 2029-30 / Renew 2031 (4 phases)
- Mobilise 2026 / Deliver 2027-29 / Renew 2030-31 (3 phases)
- Foundation 2026 / Acceleration 2027-28 / Consolidation 2029-30 / Legacy 2031
  (4 phases)
- Set in motion 2026 / Deepen 2027-28 / Scale 2029-30 / Sustain 2031 (4 phases)
- Establish 2026 / Build 2027 / Embed 2028-29 / Renew 2030 / Hand on 2031 (5
  phases)

The chosen verb-set is **off-limits to steering** --- phase names stay generic
regardless of prompt.

### Structural counts

Roll once per run; same count applies across all pillars in that run.

| Count                  | Range | Notes                                                                                      |
| ---------------------- | ----- | ------------------------------------------------------------------------------------------ |
| Pillars                | 3-5   | The exec-summary card grid follows: 3 → row of 3, 4 → 2×2, 5 → 3 on top + 2 centred below. |
| Initiatives per pillar | 2-5   | Same count for all pillars.                                                                |
| KPIs per pillar        | 2-4   | Same count for all pillars.                                                                |

### Optional sections

Five candidates. Roll each independently with **~30% probability**, capped at
**3 per run**. Inclusion and position are decided during planning; do not add ad
hoc during drafting.

| Section                                      | Position                            | Length                     | Style                                                                                           |
| -------------------------------------------- | ----------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------------- |
| Chancellor's message                         | Before VC foreword                  | ~150 words                 | Letter-style; signed "Chancellor" (no name)                                                     |
| "Our values" block                           | After exec summary                  | 3-5 values, ~30 words each | Small grid; abstract nouns ("Excellence", "Integrity", "Curiosity", "Belonging", "Stewardship") |
| "From / To" transformation table             | Intro to pillars section            | 4-6 rows                   | `<old framing>` → `<new framing>` per row                                                       |
| Glossary / acronyms                          | After conclusion, before back cover | ~10-20 entries             | Short defs of institutional acronyms                                                            |
| "How we developed this plan" methodology box | Near governance                     | ~150 words                 | Methodology paragraph: who was consulted, over what period, with what process                   |

Stock register examples (so the optional sections read in genre):

- **Chancellor's message** --- opens "As Chancellor, I am pleased to commend
  this Strategic Plan to the University community…"; closes with the signature
  block on its own line.
- **Our values** --- each value is a single abstract noun in bold, followed by a
  one-sentence gloss in genre voice ("**Excellence** --- we hold ourselves to
  the standards expected of a national university of international standing.").
- **From / To** --- left column carries the hedged/incumbent framing
  ("Disconnected research effort"), right column the bridging framing ("Coherent
  national capability"). Avoid sharp left columns; they sound like a critique.
- **Glossary** --- alphabetical; defs are one short clause ("HDR --- Higher
  Degree by Research; PhD and Masters by Research candidatures.").
- **Methodology box** --- names categories of people consulted (staff, students,
  alumni, partners), gestures at process ("…through a series of facilitated
  workshops over twelve months…"), avoids dates and numbers that could be
  checked.

### Pillar-internal scaffolding labels

The Premise / Initiatives / KPIs label triplet varies per run. Pick **one set**
and use it across **all pillars** in that run.

- Premise / Initiatives / KPIs
- Premise / Initiatives / Measures
- Why this matters / What we'll do / How we'll know
- Our position / Our actions / Our targets
- Context / Commitments / Indicators

Substance is unchanged: a premise paragraph, then numbered initiatives, then
measurable KPIs. Only the framing labels vary.

### Pillar-name reservoir

Draw 3-5 distinct pillars per run (count rolled). Names should be 3-6 words,
noun-led, abstract:

- Research Excellence and Discovery
- A University for the Public Good
- Education That Shapes the Future
- Place, Partnership, and Belonging
- A Connected and Capable Institution
- Sustainable Foundations
- Institutional Distinctiveness in a Connected World
- Knowledge for Public Purpose
- A University Ready for What Comes Next
- Capability, Talent, and Impact
- The Regional Settings
- Engaged Scholarship and Civic Contribution

Combine, paraphrase, or invent within the same register --- do not use these
verbatim every run.

### KPI plausible bands

- Research income: $X00M-$X.5B over the plan period
- HDR completions: 2,500-4,000 over the plan period
- Top-50/100 global ranking aspirations
- First-generation student %: low double digits, "double" by 2031
- Industry partnerships: 50-150 "strategic" partnerships
- Carbon: net-zero by some date between 2030 and 2050

Numbers should be specific enough to feel real and vague enough to be
unfalsifiable.

## Never vary

Everything in "Per-run variation rolls" varies per run. These don't, ever:

- document title (`Slop University Strategic Plan 2026-2031`)
- cover and contents (position); the "Executive summary" heading
- genre voice and tone (institutional, future-tense-heavy; steering doctrine per
  `../genre.md`)
- image workflow (cover + 4-5 inline + parity fix)
- hard-infrastructure off-limits set (`../genre.md` › Off-limits to steering)
- length envelope (16-20 pages, even)

## Imagery (preset specifics for image-workflow.md)

- Image folder: `output/slop-strategy-<slug>-<seed>-images/`
- Prompts: 1 cover (3:4 portrait) + 4 inline (16:9 landscape); reserve a 5th
  inline prompt as the parity-fix spare (don't generate yet).
- Resolution: cover at `--resolution 4K` (it full-bleeds the A4 cover); inlines
  at `--resolution 2K` --- they land as part-page full-bleed-right figures, so
  2K is ample and 4K would just be wasted pixels and generation time.
- Image prompts can carry thematic overlays freely.

## Style references

Read these before generating:

- **Primary structural reference**: `~/.nb/home/studio-business-plan-2026.typ`
  --- same layout core, ANU-branded. Copy the section break / image patterns and
  the shape of the show-rule call; do NOT copy its import block or content (this
  preset imports the slop brand package, not the ANU one).
- **Genre PDF**: `~/.nb/home/anu-corporate-plan-2026-v5.pdf` --- a real
  university corporate plan, for tone, layout conventions, sentence rhythm (tone
  reference only --- imagery follows the two-ink house style, not its
  photography).
- **Layout core source**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0` --- for
  the available helpers and theme machinery. Branding (Slop University lockup,
  slop gold palette) comes from the brand package below.

## Typst structure

The brand package (`@local/slop-university-brand:0.1.0`, over the
`university-typst-template` layout core) does most of the layout work for you.
Get out of its way. **Page-break discipline:** see
`../../_shared/typst-layout.md`.

**Figure placement:**

- 1 cover image, passed as
  `cover: read("/output/slop-strategy-<slug>-<seed>-images/cover.jpg", encoding: none)`
  to the `slop()` call.
- 4-5 inline landscape figures via
  `#figure(image("/output/slop-strategy-<slug>-<seed>-images/inline-N.jpg"))`.
  The template's `show figure.where(kind: image)` rule already extends them to
  the right page edge (full-bleed-right). No template tweaks needed.
- Place inline figures **within** sections --- between paragraphs, or at the
  natural end of a section's text --- not at section boundaries with forced
  breaks around them. Text flows above and below the figure on the same page.

**Highlight cards (executive summary):**

In the executive summary, after a short opening paragraph naming the pillars,
render them as a card grid --- one card per pillar. Card count tracks the rolled
pillar count (3, 4, or 5). Each card title is the pillar name (no "Pillar N:"
prefix); each body is a 1-2 sentence summary; pick one Iconoir glyph per pillar
that matches its actual content. The card helper, grid shapes per count, and the
icon-name lookup procedure live in `../../_shared/typst-layout.md` › "Highlight
cards and icon lookup".

**Skeleton** (working pattern; see `../../_shared/typst-layout.md` for the
import / metadata / back-cover patterns; no manual page breaks):

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-back-cover, slop-colors, slop-highlight-card

#set document(
  title: "This Slop University Strategy Does Not Exist: <steering prompt verbatim>",
)

#show: slop.with(
  title: "Slop University Strategic Plan 2026-2031",
  subtitle: "<varies between runs>",
  cover: read("/output/slop-strategy-<slug>-<seed>-images/cover.jpg", encoding: none),
  config: (bleed: 3mm),  // 3mm print bleed (trimmed, saddle-stitched booklet); slop branding comes with the package
)

#outline(title: [Contents], depth: 1)

= Foreword from the Vice-Chancellor
[paragraphs...]
#figure(image("/output/slop-strategy-<slug>-<seed>-images/inline-1.jpg"))
[more paragraphs, or signature]

= Executive summary
[opening paragraph naming the pillars]

[card grid --- columns and card count follow the rolled pillar count;
 see "Highlight cards" above for the 3/4/5 layouts]

[closing paragraphs that lead into the rest of the document]

= Strategic context
[paragraphs...]
#figure(image("/output/slop-strategy-<slug>-<seed>-images/inline-2.jpg"))
[more paragraphs]

[...and so on through the rest of the skeleton]

= Looking ahead
[conclusion paragraphs]

#slop-back-cover(config: (bleed: 3mm))
```

## Pre-ship checklist (preset-specific)

Generic checklist items (PDF metadata title, voice is institutional, hedging
present, etc.) live in `../SKILL.md`. Strategy-specific items:

- [ ] Title is exactly "Slop University Strategic Plan 2026-2031"
- [ ] Title and implementation-phase verb-set are unaffected by the steering
      (other elements --- pillar names, KPIs, foreword, vision, initiatives,
      imagery --- can be driven by it)
- [ ] No real person's name appears anywhere; the foreword signature is the
      unnamed role "Vice-Chancellor and President" (roster researchers may be
      quoted in body sections, per `../genre.md` › People and attribution)
- [ ] Executive summary contains a `#grid` of `slop-highlight-card`s --- one per
      pillar --- with Iconoir glyphs that match each pillar's theme
- [ ] Pillar count is 3, 4, or 5; the exec-summary card grid matches that count
- [ ] Initiative count is 2-5 per pillar and consistent across all pillars in
      this run
- [ ] KPI count is 2-4 per pillar and consistent across all pillars in this run
- [ ] Phase count is 3, 4, or 5; phases span 2026-2031 contiguously with no
      gaps; verb-set from the reservoir
- [ ] Optional-section count is 0-3, all rolled at planning time (not added ad
      hoc during drafting)
- [ ] All pillars use the same scaffolding label set (Premise/Initiatives/KPIs
      or alternative)
- [ ] Section names (Foreword onwards, except "Executive summary") came from the
      reservoirs
- [ ] Page count is even and within **16-20 pages**

## Common failure modes (preset-specific)

- **Output reads bland**: pillar names, KPIs, initiatives, foreword and vision
  aren't visibly driven by the prompt. Crank the structural commitments more
  specifically --- structural, falsifiable, particular --- across multiple
  slots, while keeping the institutional voice intact.
