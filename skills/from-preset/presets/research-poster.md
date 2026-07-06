---
name: research-poster
description:
  Slop University research poster --- a single-page A3 (landscape or portrait),
  light-mode, chart-heavy academic poster describing a plausible-but-fake
  research project. Steering-driven topic in straight academic-present voice;
  fabricated charts in the slop brand colours are the visual spine. Poster
  format (no cover, contents, or back cover).
---

# Research-poster preset

Produce one Slop University research poster from a single steering prompt. The
output should pass for a real conference poster pinned to a corridor board ---
recognisably institutional at a glance, academically straight on a close read,
with the joke living entirely in the subversive fictional project it describes.

The genre is the **academic research poster**: title, group/affiliation,
background, aims, methods, results (charts), discussion, conclusion, references.
Present-tense findings, past-tense methods, hedged claims, deadpan throughout.
The reader knows immediately what the steering prompt was; the pleasure is
watching the poster render it in unbroken research register.

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `../genre.md` for the steering philosophy and the voice floor
- `../../_shared/chart-workflow.md` for the gribouille → SVG chart pipeline and
  brand styling
- `../../_shared/image-workflow.md` for the concept image generation
- `../../_shared/output-naming.md` for slug, seed, output paths
- `../../_shared/typst-layout.md` only for the template import and PDF-metadata
  rules --- **not** the booklet AoC / back-cover / parity sections, which the
  poster format skips

## Doc identity

| Field                      | Value                                                                                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Canonical name             | Slop University research poster                                                                                                                        |
| Format                     | **poster** (single-page A3, light theme; orientation set by the layout roll)                                                                           |
| Visible title              | the fabricated project's title --- **steering-driven** (see note below)                                                                                |
| Author line                | 2-3 roster researchers (`canon/roster.yml`) + the lead author's school --- the only place people are named                                             |
| Paper / orientation        | `a3`; set by the layout roll --- feature-right = `page-settings: (flipped: true)` (landscape); feature-top = portrait (no `flipped`)                   |
| Theme                      | `light`                                                                                                                                                |
| Cover lockup               | `slop` --- feature-right: rendered automatically (top-left masthead); feature-top: overlaid white on the hero via `slop-lockup` (auto masthead hidden) |
| Filename prefix            | `slop-poster`                                                                                                                                          |
| Page count                 | exactly **1** (no parity-fix; "fits one page" check instead)                                                                                           |
| Register                   | academic-present (present-tense findings, past-tense methods, hedged)                                                                                  |
| PDF metadata title formula | `This Slop University Research Poster Does Not Exist: <steering verbatim>`                                                                             |

**Title is steering-driven (unlike the booklet presets).** `strategy` and
`impact-report` lock a fixed cover title and let steering drive only the
content. A poster's title _is_ its content --- the fabricated project's name ---
so here the visible title is generated from the steering prompt (dressed up into
academic-poster register). The PDF metadata title still uses the fixed satirical
formula above; that remains the only satirical tell and is not visible on the
rendered page.

**Split the title at the colon.** Academic poster titles love the
`Punchy phrase: descriptive gloss` shape --- e.g.
`Reading the Drift Before the Workaround: Forecasting Exam-Integrity Vulnerability from Capability Trajectories`.
Don't set the whole thing as the title band's title and _then_ invent a separate
subtitle underneath --- that stacks two long lines and reads as a title plus its
own subtitle plus a third descriptive line. Instead, when the title contains a
colon, the part **before** the colon becomes the visible title (the big
gold/white line) and the part **after** becomes the subtitle line. Only when the
title has no colon do you write a fresh one-line subtitle / research question.
Keep the title to ≤2 lines and the subtitle to one.

**Roster authors only.** The title band carries a small author line naming 2-3
researchers from the persistent roster (`canon/roster.yml`, with the lead
author's school from `canon/schools.md`) --- the flip of the old
never-name-anyone rule: fictional people, named consistently across outputs, are
part of the institution's verisimilitude. No other person is named anywhere on
the poster. The `slop` lockup and the `logos: ("studio",)` margin wordmark
("Office of Research Outputs") carry the institutional attribution. Reference
citations are real, verified literature (see "References") --- the one place
outside real names appear, as authors of their own real work, correctly
attributed; never a fabricated entry.

## Inputs

One free-text **steering prompt** describing a subversive fictional research
project. 1-3 short sentences, or a phrase. Examples:

- "training magpies as a distributed campus surveillance network"
- "a reinforcement-learning model for optimal tea-room biscuit redistribution"
- "measuring the institutional unconscious via car-park sensor telemetry"
- "a closed-loop controller for undergraduate enthusiasm"
- "using soil moisture sensors to predict committee-meeting sentiment"

The prompt is the project. The academic register (below) is the only floor;
everything else --- title, aims, methods, results, charts, captions --- bends to
the prompt. The institution's voice keeps wrapping the absurd in methods prose,
plausible bands, and hedged findings.

## The genre's structural skeleton

One A3 page, portrait or landscape per the layout roll (see "Per-run variation
rolls › Layout"). The **content** is identical either way --- the regions below
are a content contract, not a fixed geometry. Both layouts carry a feature
image, one chart, a field image, and a two-cell body grid: the left cell holds
the text + an image that fills its leftover height; the right cell holds the
chart, discussion, references, and a bottom-pinned footer. What differs is only
where the feature image and title sit (the "Placement" column below describes
**feature-right**; the **feature-top** differences are in the Layout roll).

| Region                    | Placement                                    | Length / notes                                                                                                                                                             |
| ------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Title band                | full width (left two-thirds), below masthead | Project title (gold, ~32pt) + one-line subtitle. No affiliation line --- attribution rides in the lockup + margin wordmark                                                 |
| Feature image             | full-bleed right third                       | tall (9:16) `references/`-styled photo with a gradient scrim + white hero quote --- the visual hook                                                                        |
| Body image (field)        | foot of the left grid column                 | wide (21:9) `references/`-styled photo as a `height: 1fr` block, cropped (`fit: cover`) to fill the column's leftover height --- pads the left column to balance the right |
| Background                | column flow                                  | ~30-45 words; the gap, ideally framed as a question                                                                                                                        |
| Aims / Research questions | column flow                                  | 3 terse bullets                                                                                                                                                            |
| Methods                   | column flow                                  | ~3 terse bullets (n · instrument · sampling · duration; model; key control)                                                                                                |
| Results                   | left cell                                    | one or two hedged sentences; the chart leads the right cell, with a caption stating a falsifiable claim                                                                    |
| Discussion / conclusions  | column flow                                  | ~2-3 punchy, hedged lines + a "Next:" fragment                                                                                                                             |
| References                | column flow (end)                            | 4-6 real, verified citations (DOI/arXiv-checked) in small (~8pt) text                                                                                                      |
| Footer line               | column flow (end)                            | one deadpan acknowledgements / ethics / data line (never a person)                                                                                                         |

Total body prose: ~150 words at 10pt --- the poster is telegraphic (fragments
and bullets, not paragraphs; see "Voice"). Budget is a guide, not a target ---
the hard constraint is that it fits on **one page** (see "Compile and one-page
fit"). ~150 is a realistic ceiling for column 2 (chart + a 4-6 entry reference
list + footer all sit in the right grid cell). The body image is a `height: 1fr`
block, so it costs the column budget nothing --- it just expands or shrinks
(cropped) to fill whatever the left column has spare. If the poster overflows,
tighten the prose or shorten the chart plot --- never touch the reference list.

## Per-run variation rolls

Roll once per run, upfront. The masthead branding, the academic voice floor, and
the chart pipeline are off-limits to variation; they're fixed.

### Layout (roll: feature-right / feature-top)

Roll one of two layouts per run (50/50). Both carry the **same content** --- the
same sections, the same single chart, the same `1fr` field image, a QR, and a
bottom-pinned footer --- and differ only in orientation and where the feature
image and title sit. Roll the layout **first**, before the other rolls: it sets
the feature image's aspect ratio and which of the two skeletons in "Typst
structure" you write. Everything downstream (sections, chart, references, voice,
one-page fit) is identical across the two.

- **feature-right (A3 landscape).** A tall image full-bleeds the right ~third of
  the page (reserved via the page `margin: (right: 150mm, …)` and a `place`d
  box), with a gradient scrim and a white hero quote over its lower portion; the
  title (gold on white) and a 2-column grid body take the left two-thirds. The
  masthead renders automatically top-left; the QR sits over the image's
  top-right. The **feature image is tall and vertical** (a stack aisle, a
  stairwell, a tower) --- request a **9:16** image from `styled-image-gen`. The
  big image makes the poster pop and the title still gets a comfortable
  two-thirds width.

- **feature-top (A3 portrait).** A wide image full-bleeds a band across the top
  of the page (reserved via an oversized `top` margin and a `place`d box flush
  to the page edge), with **two gradient scrims** --- one darkening the top so
  the **white Slop University lockup** reads, one darkening the bottom so the
  **white title + subtitle + gold rule** read (the "white text, black scrim"
  treatment the template uses for cover and feature-page overlays). The
  automatic masthead is hidden (`hide: (…, "masthead")`) and the lockup overlaid
  manually via `slop-lockup` (white), because the automatic one draws a solid
  rect and sits behind the band. The 2-column body fills the page below. The
  **feature image is wide and horizontal** (a corridor, a courtyard, a bank of
  screens) --- request a **16:9** image.

In both layouts the feature image is `place`d out of flow (right third, or top
band) so it never affects column fit; the body field image is in-flow in the
left grid cell as a `height: 1fr` block --- it consumes exactly the cell's
leftover height and crops (`fit: cover`) to fit, so it can't overflow or
overlap.

### Section-name reservoirs

One choice per section per run. Reservoirs grow over time; aim for ~4 entries
each.

| Section role | Reservoir                                                             |
| ------------ | --------------------------------------------------------------------- |
| Background   | "Background", "Introduction", "Motivation", "The problem"             |
| Aims         | "Aims", "Objectives", "Research questions", "What we set out to test" |
| Methods      | "Methods", "Approach", "Materials & methods", "Study design"          |
| Results      | "Results", "Findings", "What we found", "Results & analysis"          |
| Discussion   | "Discussion", "Implications", "Interpretation", "What it means"       |
| Conclusion   | "Conclusion", "Conclusions & future work", "Where next", "Takeaways"  |
| References   | "References", "Selected references", "Further reading"                |

### Chart count and types

Roll **1 chart** (a 2nd only if the prose stays lean) --- the data spine,
alongside the feature image. Types drawn from
`{line, area, scatter, grouped-bar, stacked-bar, boxplot}`; each appears at most
once. **Omit the chart `title`** (the claim goes in the typst caption). Each
chart is `layout`-responsive, so it fills the right grid cell on its own ---
keep it **wide and short** (set `height` to ~0.3 of the width). The chart leads
the **right grid cell** (with the discussion, references, and footer); the
text + body image take the left cell. Styling and the render pipeline are in
`../../_shared/chart-workflow.md`.

### Attribution (roster + canon)

Authors are **2-3 researchers from `canon/roster.yml`** --- roll which ones per
run (a plausible mix of ranks; the lead author's school supplies the school name
in the author line). Labs, when a lab is named at all, come from
`canon/schools.md` (Trajectory Analytics Group, Adaptive Metrics Lab) --- never
invent a new unit inside a run. Institutional attribution is carried by the
masthead: the `slop` lockup (top-left) gives the Slop University wordmark, and
the `logos: ("studio",)` margin wordmark prints "Office of Research Outputs"
rotated in the bottom-left margin. Beyond the author line, no person is named
anywhere (ethics lines, acknowledgements, and hero quotes stay aggregate and
anonymous).

### Concept images

Two per poster --- the hero `feature.jpg` (aspect set by the Layout roll) and
the wide field image `inline-1.jpg`. Counts, aspects, resolutions, and placement
live in "Imagery (preset specifics)" below; the only rolled element is the scene
content, which should read as the project's field site or apparatus.

### Footer furniture

Fill the trailing column (and vary the foot between runs) with 1-2 small items
after the references --- real poster apparatus, played deadpan:

- **Acknowledgements / funding** --- aggregate only ("we thank the staff of the
  monitored common rooms"; "supported by a School of Continuous Improvement seed
  grant" --- schools from `canon/schools.md`); no person names beyond the author
  line.
- **Ethics / data statement** --- often the funniest line on the poster, played
  straight ("animal ethics approval 2025/047; no birds harmed"; "de-identified
  occupancy only; no number plates retained"; "thresholds pre-registered").
- **Contact line**, optionally with a QR: import `slop-qr-code` and place
  `slop-qr-code("https://slop.university/", width: 2.3cm)` beside a short
  contact line; the QR is theme-aware and fills the column foot nicely.

Keep furniture small (8-9pt); if the foot would overflow, compress it to a
single line.

### Result / metric plausible bands

Fabricated numbers should be specific enough to feel real and vague enough to be
unfalsifiable (commitment-shaped metrics can be more specific):

- sample sizes: n = 12-400 (participants, sites, sensors, birds…)
- accuracy / agreement: 60-95%
- effect sizes / correlations: r = 0.3-0.8, "p < 0.05" sparingly
- deployment duration: 3-24 months
- improvement vs baseline: 1.2×-4×

## Voice (academic-present register)

The poster's register is **academic-present** (distinct from the booklets'
future-tense and past-tense-reflective registers). It defers to `../genre.md`
for the steering philosophy --- institutional/academic voice wrapping an
unhinged topic, hedges at the edges, no exclamation marks, no first-person
passion, no manifesto register --- and specialises it for a research poster:

- **Telegraphic, not prose.** A poster is scanned, not read. Write short
  declarative fragments; bullet the Aims and Methods; frame Background as the
  gap, often a question. Cut the articles and filler a paragraph would carry ---
  each section should land in one glance (Background 1-2 sentences, Methods ~3
  bullets, Discussion / Conclusion a line or two). The academic register below
  still holds; it is just compressed hard.
- **Methods: terse and procedural.** Bullets or short past-tense fragments ("8
  rooms · mass sensors · 5-min sampling · 14 weeks"; "soft actor-critic on the
  redistribution MDP"). No enthusiasm; the deadpan is the joke.
- **Findings in present tense, hedged.** "Results suggest…", "The model
  achieves…", "Performance is consistent with…", "We observe a moderate
  association between…". Hedge even when the wrapped claim is absurd.
- **Background frames the absurd premise as a serious gap.** "Despite growing
  interest in X, little is known about Y" --- the standard poster opener,
  applied straight to a ridiculous Y.
- **Captions state a falsifiable claim straight** (see commitment shapes below).
- **Citations and apparatus complete the costume** --- a references list, an
  optional funding line, plausible bands, the occasional "(p < 0.05)". These are
  the costume of research, worn without a wink.

The poster never signals satire on the page. If the register cracks --- an
exclamation mark, a knowing aside, advocacy for the theme --- the joke dies.

## Voice-preserving commitment shapes (poster)

Charts, captions, and headline numbers are the poster's commitment vectors. Use
these as a menu throughout (the general catalogue in `../genre.md` also
applies):

- **A chart caption that names a falsifiable result with a checkable figure and
  date.** Hedge: "Engagement increased over the trial." One notch: "Mean corvid
  dwell time at monitored nodes rose from 4.2 to 11.8 minutes between March and
  August 2025 (n = 37 birds), tracking the redeployment schedule exactly."
- **A headline number that's too clean.** "92% of monitored car-park bays
  produced a usable sentiment signal at 6-month follow-up, with no drift across
  the cohort."
- **An aim phrased as a precise, structural hypothesis** the data then
  "confirms".
- **A methods detail that commits to an audited, published protocol** with no
  override ("All thresholds were pre-registered; none were adjusted post hoc").

All stay in academic register --- still hedged at the edges, still procedural
--- while committing to something specific, structural, and checkable that real
posters hedge away from.

## References --- real, verified (hard requirement)

A **real** references list (4-6 entries) in small (~8pt) text: genuine adjacent
literature, every entry verified to resolve. This is the same rule the `paper`
preset enforces (`paper.md` › "Bibliography --- real references, verified"),
scaled to a poster's short list. The costume of research is worn straight ---
the apparatus is real, so it holds up to a close read rather than rewarding one
with a wink.

- **Harvest** 4-6 candidates from the fabricated topic's real adjacent fields
  (web search the topic's serious neighbours --- e.g. corvid foraging telemetry
  → animal-movement ecology, sensor networks, multi-agent resource allocation).
- **Verify every entry** before it enters the list --- each must pass one of:
  - **DOI check**:
    `curl -sI -o /dev/null -w '%{http_code}' https://doi.org/<doi>` returns
    2xx/3xx.
  - **arXiv check**: `curl -s 'https://export.arxiv.org/api/query?id_list=<id>'`
    returns an entry whose title matches.

  Drop anything that 404s or mismatches. Never fabricate an entry, never pad
  with an unverified one.

- **Copy fields accurately**: real authors, real title, real venue, real year,
  and the verified DOI or arXiv id --- render it in the entry so a reader can
  resolve it. These are the one place outside real names appear, as authors of
  their own real work, correctly attributed.
- **Citation honesty**: neither the list nor the prose may claim something a
  cited work doesn't support. The fictional project borrows the field's
  legitimacy; it never puts words in a real researcher's mouth.
- Roughly 4-6 entries --- a poster's list is short; verified beats full.

## Imagery (preset specifics for image-workflow.md)

- Image folder: `output/slop-poster-<slug>-<seed>-images/`
- **No cover image** (poster format --- the `slop(...)` call omits `cover:`).
- **`feature.jpg`** (always) --- the hero, generated per
  `../../_shared/image-workflow.md` (house-style prompt formula, 3-5
  `references/slop-style/` refs, dispatched to a subagent). Aspect set by the
  layout roll: **9:16** (`--aspect-ratio 9:16`, tall) for **feature-right**
  (full-bleeds the right third with a scrim + hero quote) or **16:9**
  (`--aspect-ratio 16:9`, wide) for **feature-top** (full-bleeds the top band
  with scrims + the overlaid masthead/title). `place`d out of flow, so it never
  affects column fit.
- **`inline-1.jpg`** (always) --- the wide field image. **21:9**
  (`--aspect-ratio 21:9`), **2K** is fine (shown only a column wide); placed
  in-flow at the foot of the left grid cell as a `height: 1fr` block, cropped
  (`fit: cover`, centre) to fill the cell's leftover height --- it pads the left
  column out to balance the right. No caption (the hero quote carries the text).
  Being a `1fr` block it can't overflow, and being in its own cell it can't
  overlap the text.
- Both images depict the project's apparatus, fieldwork, or setting in the
  two-ink house style (a tagged bird on a walkway, an instrumented common room,
  a sensor-fitted car park --- as risograph illustration, never photography),
  with the prompt formula from `../../_shared/visual-style.md` and 3-5
  references from `references/slop-style/`.
- No parity-fix spare --- the poster is single-page; there is no parity to fix.

## Chart workflow

Charts are the poster's emphasis. Follow `../../_shared/chart-workflow.md` for
the full pipeline (author a gribouille `#plot` at
`output/slop-poster-<slug>-<seed>-charts/chart-N.typ`, import it into the
poster, render inline) and the brand styling rules (lines/scatter = brand
categorical pair; bars = single-hue tint ramp; parts-of-a-whole = gold-tint
normalised stacked bar; legends top/bottom). Poster specifics:

- 1 chart (a 2nd only if the prose stays lean), leading the right grid cell,
  alongside the two concept images.
- **Omit the chart `title`** (the caption carries the falsifiable claim). The
  chart is `layout`-responsive, so it fills the right grid cell with no side
  padding and no upscaling --- keep it wide and short (`height` ~0.3 of width).
- Each chart's falsifiable claim goes in the typst `caption:`, not the chart
  title.

## Style references

Read these before generating:

- **Poster layout cues (feature-right)**:
  `~/projects/perceptron_apparatus/docs/mnist-poster.typ` and `poker-poster.typ`
  --- the A3 + `flipped: true` + `hide: ("page-numbers", "title-block")` recipe
  and the column-grid body. **Note:** those are dark-mode with custom display
  fonts; this preset is **light-mode using the template defaults** (Public Sans,
  gold accents). Copy the page-setup moves, not the dark styling or fonts.
- **Hero scrim + masthead overlay (feature-top)**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/lib.typ`
  --- the core's `feature-page` and cover block both do the
  white-text-on-gradient-scrim treatment the top band reuses; `slop-lockup`
  (from the brand package) is the helper that overlays the masthead on the photo
  (no masking rect). There is no perceptron analogue for this layout --- the
  core is the reference.
- **Chart + card layout**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/examples/design.typ`
  --- chart-in-column usage and the highlight-card grid (under the core's
  neutral names; this preset uses the brand package's `slop-*` names). The
  poster uses the tighter `chartfig` helper instead of inline figures, for the
  reasons in "Critical gotchas".
- **Layout core source**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/lib.typ`
  --- the `slop(...)` options used here (`paper`,
  `page-settings: (flipped: true)`, `config: (theme, hide, qr-url)`). The
  first-page branding (gold rule + slop lockup) renders automatically from the
  brand package.
- **Chart pipeline**: `../../_shared/chart-workflow.md`.

## Typst structure

The poster does **not** use the booklet scaffold (no `cover:`, no `#outline()`,
no Acknowledgement of Country, no `#slop-back-cover()`, no manual
`#pagebreak()`). It drives `slop(...)` directly for a light, single page. There
are **two skeletons, one per layout roll** (see "Per-run variation rolls ›
Layout"); write the one the roll selected. Both share the `chartfig` helper and
an identical two-column body grid --- only the page setup and the feature image
/ title block differ.

### Skeleton A --- feature-right (landscape)

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-colors, slop-qr-code

#set document(
  title: "This Slop University Research Poster Does Not Exist: <steering prompt verbatim>",
)

#show: doc => slop(
  title: "",                          // title block hidden; poster title is in the body
  paper: "a3",
  // Reserve the right third for the full-bleed feature image; the body flows in
  // the left two-thirds.
  margin: (left: 33mm, right: 150mm, top: 25mm, bottom: 25mm),
  config: (
    theme: "light",
    logos: ("studio",),               // rotated "Office of Research Outputs" wordmark
                                       // in the bottom-left margin
    hide: ("page-numbers", "title-block"),
  ),
  page-settings: (flipped: true),     // landscape
  doc,
)

// Import the chart authored in the chart folder (see Chart workflow); it is
// responsive content (`layout(size => plot(...))`), so it fills the column on
// its own.
#import "/output/slop-poster-<slug>-<seed>-charts/chart-1.typ": chart as chart-1

// In-column figure + caption. NOT `#figure` / `slop-inline-figure` (a bare figure
// bleeds to the page edge; `slop-inline-figure` adds loose margins). Pass a
// smaller `w` only for a chart deliberately sized narrower than the column.
#let chartfig(chart, caption, w: 100%) = {
  v(0.5em)
  block(width: w, chart)
  v(0.2em)
  text(size: 8.5pt, fill: slop-colors.grey-4, caption)
  v(0.6em)
}

// ── Feature image: a tall image full-bleeding the reserved right third, with a
//    gradient scrim and a white hero quote over its lower portion. ──
#place(top + right, dx: 150mm, dy: -25mm, box(width: 143mm, height: 297mm, clip: true, {
  image("/output/slop-poster-<slug>-<seed>-images/feature.jpg",
        width: 100%, height: 100%, fit: "cover")
  place(bottom, rect(width: 143mm, height: 48%,
    fill: gradient.linear(angle: 90deg, (rgb("#00000000"), 0%), (rgb("#000000cc"), 100%))))
  place(bottom + left, dx: 10mm, dy: -11mm, box(width: 123mm)[
    #text(fill: white, size: 19pt, weight: "medium")[“<hero quote --- a punchy finding or strapline>”]
    #v(0.35em)
    #text(fill: rgb("#e0e0e0"), size: 10pt)[<one supporting line --- a falsifiable claim>]
  ])
}))

// ── QR over the image's top-right (manual: the config `qr-url` would render
//    behind the placed feature image). ──
#place(top + right, dx: 140mm, dy: -15mm,
  slop-qr-code("https://slop.university/", width: 2.6cm))

// ── Body --- defined here, placed below by the outer grid. Two equal columns:
//    LEFT the text sections then a `height: 1fr` body image that fills the column's
//    leftover height; RIGHT the chart, discussion, references, then a `#v(1fr)`-pinned
//    footer. The image and the footer pin make BOTH columns fill to the page foot and
//    balance. The `set` rules are scoped to the body so the title block keeps its own
//    sizes. ──
#let body = {
  set text(size: 10pt)
  set par(leading: 0.54em)        // tighten line spacing for the dense one-pager
  set block(spacing: 0.7em)       // tighten gaps between headings, paragraphs, figures
  grid(
    columns: (1fr, 1fr),
    rows: 1fr,
    gutter: 1.0cm,
    [
      == Background
      <30-45 words --- the gap, ideally framed as a question>

      == Aims
      - <terse aim>
      - <terse aim>
      - <terse aim>

      == Methods
      - <terse bullet: n · instrument · sampling · duration>
      - <terse bullet: model / method>
      - <terse bullet: key control --- pre-registered, held constant>

      == Results
      <one or two punchy, hedged sentences>

      // Body image: `height: 1fr` makes this block consume exactly the column's
      // leftover height, and `fit: "cover"` crops the wide (21:9) image symmetrically
      // (centre gravity) to that height --- so it pads column 1 out to match column 2.
      #v(0.5em)
      #block(width: 100%, height: 1fr, clip: true,
        image("/output/slop-poster-<slug>-<seed>-images/inline-1.jpg", width: 100%, height: 100%, fit: "cover"))
    ],
    [
      #chartfig(
        chart-1,
        [<falsifiable, slightly-whacked claim with a checkable figure/date>],
      )

      == Discussion & conclusions
      <2-3 punchy, hedged lines, then a "Next:" fragment>

      == References
      #block[
        #set text(size: 8pt)
        // 4-6 REAL, verified citations (DOI resolves or arXiv id matches --- see the
        // "References" section). Real authors, title, venue, year; render the DOI/arXiv
        // id so a reader can resolve it. Never a fabricated entry.
        + <Real, A., & Author, B. (2023). Real title. Real Venue, 12(3), 45--67. doi:10.xxxx/yyyy>
        + <...>
        + <...>
        + <...>
      ]

      // Fill probe: this zero-height marker and the `<fill-bot>` label on the footer
      // bracket the `#v(1fr)` gap, so `typst eval` can read the leftover-whitespace
      // band (see "Compile and one-page fit"). Inline + 0pt --- never shifts layout.
      #box(width: 100%, height: 0pt)<fill-top>
      // Pin the footer to the bottom of the column so both columns reach the page foot.
      #v(1fr)
      #text(size: 8.5pt, fill: slop-colors.grey-4)[<deadpan ethics / data line>]<fill-bot>
      #v(0.35em)
      #text(size: 8.5pt, fill: slop-colors.grey-4)[Office of Research Outputs · slop.university]
    ],
  )
}

// ── Title + body. Wrap them in an OUTER grid (`rows: (auto, 1fr)`): row one is the
//    title block at its natural height, row two is the body filling the REMAINING
//    page height. Without this wrapper the body grid's `rows: 1fr` resolves against
//    the FULL page height (not the height left below the title), overshoots the page
//    foot, and pushes the pinned footer off the bottom edge. The author line names
//    roster researchers; the lockup and margin wordmark carry the institution. ──
#grid(
  rows: (auto, 1fr),
  [
    #v(2.6cm)
    #text(size: 32pt, weight: "regular", fill: slop-colors.gold)[<Project title --- steering-driven; part before the colon>]
    #v(0.15em)
    #text(size: 15pt)[<part after the colon, else a one-line research question>]
    #v(0.4em)
    #text(size: 11pt, fill: slop-colors.grey-4)[<2-3 roster authors, middot-separated> --- <lead author's school>]
    #v(0.35cm)
    #line(length: 100%, stroke: 0.5pt + slop-colors.gold)
    #v(0.4cm)
  ],
  body,
)
```

### Skeleton B --- feature-top (portrait)

Portrait A3. A wide hero image is `place`d flush to the top edge; the body flows
below it in the same two-column grid as Skeleton A. The masthead is overlaid
(white `slop-lockup`) rather than auto-rendered, and the title is **white over
the bottom scrim** (not gold-on-white as in Skeleton A). The `body` definition
is identical to Skeleton A (set rules, both cells, the `1fr` image, the fill
probe, the pinned footer); only its placement differs --- Skeleton A nests it as
row two of an outer `grid(rows: (auto, 1fr))` below its in-flow title, whereas
here the title lives in the hero band (out of flow), so the body grid is the
first in-flow content (its `rows: 1fr` already resolves against the correct
height) and is placed directly with `#body`.

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-colors, slop-lockup, slop-qr-code

#set document(
  title: "This Slop University Research Poster Does Not Exist: <steering prompt verbatim>",
)

// Geometry. The top margin is oversized to RESERVE the hero band: the body flows
// below it, while the band is `place`d flush to the page edge (negative dx/dy
// cancel the margins). Keep `band-h` + the band→body gap ≈ `m-top`.
#let band-h = 152mm
#let m-left = 25mm
#let m-right = 20mm
#let m-top = 170mm
#let m-bottom = 18mm

#show: doc => slop(
  title: "",                          // title hidden; poster title is overlaid on the hero
  paper: "a3",                        // PORTRAIT --- no `page-settings: (flipped: true)`
  margin: (left: m-left, right: m-right, top: m-top, bottom: m-bottom),
  config: (
    theme: "light",
    logos: ("studio",),               // rotated "Office of Research Outputs" wordmark, bottom-left margin
    // Hide the auto masthead: it draws a solid white rect in the page background,
    // which the top hero band would cover. We overlay our own white lockup on
    // the band instead (`slop-lockup`, below).
    hide: ("page-numbers", "title-block", "masthead"),
  ),
  doc,
)

// chartfig: identical to Skeleton A (responsive chart content, never `#figure`
// / `slop-inline-figure`; see Critical gotchas).
#import "/output/slop-poster-<slug>-<seed>-charts/chart-1.typ": chart as chart-1
#let chartfig(chart, caption, w: 100%) = {
  v(0.5em)
  block(width: w, chart)
  v(0.2em)
  text(size: 8.5pt, fill: slop-colors.grey-4, caption)
  v(0.6em)
}

// ── Hero band: a wide image full-bleeding a band across the top, flush to the
//    page edge. Two scrims darken the top (so the white lockup reads) and the
//    bottom (so the white title reads); the lockup, title, subtitle, gold rule,
//    and QR are overlaid. `place`d out of flow, so it never affects column fit. ──
#place(top + left, dx: -m-left, dy: -m-top, box(width: 297mm, height: band-h, clip: true, {
  image("/output/slop-poster-<slug>-<seed>-images/feature.jpg",
        width: 100%, height: 100%, fit: "cover")
  // top scrim (for the lockup)
  place(top, rect(width: 100%, height: 42%,
    fill: gradient.linear(angle: 90deg, (rgb("#000000b3"), 0%), (rgb("#00000000"), 100%))))
  // bottom scrim (for the title block)
  place(bottom, rect(width: 100%, height: 60%,
    fill: gradient.linear(angle: 90deg, (rgb("#00000000"), 0%), (rgb("#000000cc"), 100%))))
  // gold spine continued over the band (the page-background rule is covered here)
  place(top + left, dx: 1.9cm, rect(width: 0.75pt, height: band-h, fill: slop-colors.gold))
  // white Slop University lockup, overlaid (no masking rect --- reads on the top scrim)
  place(top + left, dx: 2.2cm, dy: 1.1cm,
    slop-lockup(variant: "white", height: 1.7cm))
  // QR top-right, balancing the lockup
  place(top + right, dx: -1.6cm, dy: 1.4cm,
    slop-qr-code("https://slop.university/", width: 2.4cm))
  // title block over the bottom scrim --- WHITE (gold lives only in the rule)
  place(bottom + left, dx: 2.2cm, dy: -11mm, box(width: 250mm)[
    #text(fill: white, size: 44pt, weight: "regular")[<Project title --- steering-driven; part before the colon>]
    #v(0.25em)
    #text(fill: rgb("#ececec"), size: 16pt)[<part after the colon, else a one-line research question>]
    #v(0.35em)
    #text(fill: rgb("#e0e0e0"), size: 11.5pt)[<2-3 roster authors, middot-separated> --- <lead author's school>]
    #v(0.55em)
    // gold rule under the subtitle --- 0.75pt to match the gold spine weight
    #line(length: 110mm, stroke: 0.75pt + slop-colors.gold)
  ])
}))

// ── Body: two equal columns filling the page below the band. Write Skeleton A's
//    `#let body = { … }` block here VERBATIM (set rules, both cells, the `1fr`
//    image, the fill probe, the pinned footer) --- it is identical in both
//    skeletons. The title lives in the hero band (out of flow), so the body grid
//    is the first in-flow content and its `rows: 1fr` resolves against the
//    correct height --- no outer wrapper is needed; place it directly: ──
#let body = { /* Skeleton A's body block, verbatim */ }

#body
```

### Critical gotchas

These are the failure modes that cost the most iterations; honour them and the
poster lands on one page first time.

- **The body is a `#grid(rows: 1fr)`, the body image is a `height: 1fr` block,
  and the footer is pinned with `#v(1fr)`.** `rows: 1fr` makes the grid fill the
  page body; the `height: 1fr` image block consumes exactly the left column's
  leftover height (cropped `fit: cover`, so it can't overflow); the `#v(1fr)`
  before the footer pushes it to the bottom of the right column. Result: both
  columns fill to the page foot and balance, the image is free, and it can't
  overlap the text (it's in its own cell). NB `#v(1fr)`/`height: 1fr` do **not**
  behave inside `#columns` --- the grid with `rows: 1fr` is what gives the `1fr`
  units a definite height (and in feature-right that grid must itself be nested
  --- see the next point).
- **(feature-right) Title + body sit in an OUTER `#grid(rows: (auto, 1fr))`.** A
  top-level `#grid(rows: 1fr)` resolves `1fr` against the _full_ page height,
  not the height left below the in-flow title --- so on its own it overshoots
  the page foot by the title's height and pushes the `#v(1fr)`-pinned footer
  clean off the bottom edge (the footer silently vanishes, and the band above it
  reads as plain underfill). The outer grid (title = row `auto`, body = row
  `1fr`) sizes the body to the _remaining_ height, so the footer lands on-page.
  **feature-top doesn't need it** --- its title is in the hero band (out of
  flow), so the body grid is the first in-flow content and `rows: 1fr` already
  resolves correctly; place `#body` bare.
- **The chart uses the `chartfig` helper (a plain `image()`), never `#figure` or
  `slop-inline-figure`.** A `#figure(image(...))` triggers the template's
  full-bleed-right rule (the chart spills past the column into the gutter);
  `slop-inline-figure` avoids the bleed but its 2.2em margins overflow the page.
  `chartfig` (plain content + tight `v()` spacing) sidesteps both. (The body
  image is a plain `#image` inside a `height: 1fr` block, not `chartfig`.)
- **Charts fill the column; they're responsive.** The chart is
  `layout(size => plot(width: size.width, ...))`, so it fills the grid cell with
  no side padding and no upscaling --- the old fixed-width trap is gone. The one
  knob is aspect: set `height` to ~0.3 of the width and **omit the `title`**
  (the caption carries the claim). High-res JPG images still take `w: 100%`
  cleanly.
- **Body text 10pt** inside the `#columns` block. 11pt with a chart, six
  sections, and references overflows A3; 10pt fits and reads fine at poster
  scale. Section heads stay 15pt (the heading show-rule sets its own size).
- **(feature-right) The `#v(2.6cm)` at the top of the outer grid's title row is
  mandatory** --- it pushes the title below the top-left Slop University lockup
  (top ~4.5cm) and leaves a clear gap between the lockup and the title. Without
  it the gold title collides with the lockup. Because it lives in the `auto`
  title row, it no longer pushes the body grid off the page foot (the outer grid
  absorbs it). (feature-top has no such spacer --- its oversized `top` margin
  already reserves the masthead zone.)
- **(feature-right) Masthead: lockup top-left, QR top-right, margin wordmark
  bottom-left.** The QR (to slop.university) anchors the top-right the
  full-width rule would otherwise frame as empty; the rotated "Office of
  Research Outputs" margin wordmark (`logos: ("studio",)`) carries the
  producing-unit attribution. The QR is **placed manually** over the feature
  image's top-right (the config `"qr-url"` would render in the page background,
  _behind_ the full-bleed feature image, so it isn't used here).
- **(feature-top) The hero band is reserved by an oversized `top` margin, then
  `place`d flush to the page edge with negative `dx/dy`.** Keep `m-top` ≈
  `band-h` + the band→body gap so the body never flows under the band --- this
  mirrors how feature-right reserves the right third with
  `margin: (right: 150mm, …)`.
- **(feature-top) Two scrims, not one.** The bottom scrim carries the white
  title (as feature-right's bottom scrim carries the hero quote); a **second top
  scrim is essential** so the overlaid white lockup reads on a bright photo.
  `slop-lockup` is transparent by design (no masking rect) --- without the top
  scrim it can wash out. If the lockup or title still reads faintly, deepen that
  scrim's end stop (`#000000cc` → `#000000e6`) rather than moving the art.
- **(feature-top) Overlaid masthead means hiding the automatic one**
  (`hide: (…, "masthead")`). The auto masthead draws a solid white rect in the
  page background; the top band would cover it, leaving no masthead at all. The
  gold spine is re-drawn over the band (the background rule is also covered
  there) so it runs unbroken into the body below.
- **(feature-top) The title is WHITE over the scrim, not gold-on-white.** Gold
  lives only in the rule under the subtitle. Keep the title to ≤2 lines and the
  subtitle to one, so the block stays inside the bottom scrim (it grows upward
  from its bottom anchor).
- **Image/chart paths are root-relative with the `output/` prefix**
  (`/output/slop-poster-<slug>-<seed>-charts/chart-1.typ`), matching how the
  booklet presets reference images. Compile with the project root as the typst
  root (see below).
- **Section heads are `==` (level 2, 15pt).** The big gold project title is a
  manual `text()` block, not a heading, so it doesn't inherit the level-1
  heading treatment (and there's no outline anyway).
- **(feature-right) A 32pt title that wraps to two lines is fine**; the title
  band grows and pushes the rule and columns down. Keep the subtitle to one
  line.
- **If a section heading orphans at the bottom of a column**, wrap that section
  in `#block(breakable: false)[ … ]` so it moves to the next column intact. Use
  sparingly --- a section taller than a column can't be unbreakable.

## Compile and one-page fit

The poster replaces the booklet parity-fix with a one-page check:

1. Compile with the project root as the typst root:
   `typst compile --root . output/slop-poster-<slug>-<seed>.typ output/pdf/research-poster/slop-poster-<slug>-<seed>.pdf`
   (create `output/pdf/research-poster/` if absent).
2. Check
   `pdfinfo output/pdf/research-poster/slop-poster-<slug>-<seed>.pdf | grep -E 'Pages|Page size'`.
   Expect **1 page**, A3 in the rolled orientation --- landscape ≈ 1190 × 842 pt
   (feature-right) or portrait ≈ 842 × 1190 pt (feature-top).
3. Measure the right-column fill band --- the backpressure check for
   _under_-fill. The footer is pinned with `#v(1fr)`, so any leftover whitespace
   pools into that one gap, which the `<fill-top>` / `<fill-bot>` markers
   bracket. Read its height in millimetres (no extra scaffolding in the doc ---
   the markers are already in both skeletons):
   `typst eval 'let y = p => query(p).first().location().position().y; calc.round((y(<fill-bot>) - y(<fill-top>)).mm(), digits: 0)' --in output/slop-poster-<slug>-<seed>.typ --root .`
   Treat the number as backpressure on how much content the poster carries:
   - **≲ 40 mm** --- healthy; a few mm is just the normal footer gap. Ship it.
   - **≳ 40 mm** (≈ eight empty body lines) --- the right column underfills, and
     the slack band reads as a hole above the footer. Add content --- lengthen
     the discussion, add a reference, enlarge the chart, or roll in the optional
     second chart --- and recompile. **Fill it, don't hide it:** the band is the
     "too thin" signal, exactly as a second page (step 2) is the "too full" one.

   (~40 mm is a starting threshold --- tune it once you've eyeballed a few runs.
   The check bites hardest on **feature-top**, whose hero band leaves less body
   height.)

4. If it spills to a second page, **a grid cell overflows** (the body image is a
   `1fr` block and never does --- it just shrinks). It's usually the right cell
   (chart + references + footer). The levers, in order: tighten the prose (cut
   to fragments and bullets); shorten the chart plot (bars especially --- a
   bottom legend makes them tall; `height: ~74`); keep body text at 10pt (9.5pt
   is a last resort that still reads fine at poster scale). **Don't trim the
   reference list to fit** --- it's a feature, and at 8pt it's cheap; cut prose
   or the chart first. Recompile after each. Don't add a page break --- a poster
   is one page.

   A standard poster --- feature image, a `1fr` body image, one full-width
   chart, telegraphic sections, and a 4-6 entry reference list --- fits one A3
   page once the prose is terse (~150 words). The body image is free (it absorbs
   slack); the budget is really each grid cell's text + chart + references +
   footer. **feature-top** has slightly less body height (the hero band takes
   ~152mm) but the same content fits; its risk is the opposite one ---
   under-fill, which step 3 owns.

## Pre-ship checklist (preset-specific)

Generic format-aware checklist items live in `../SKILL.md`. Research-poster
items:

- [ ] Single A3 page in the rolled orientation (`paper: "a3"`; feature-right
      adds `page-settings: (flipped: true)`, feature-top is portrait); `pdfinfo`
      confirms 1 page
- [ ] Light theme; `slop` lockup, QR (to slop.university), "Office of Research
      Outputs" wordmark in the bottom-left margin (`logos: ("studio",)`), gold
      spine down the left edge. feature-right: lockup top-left (auto), QR
      top-right, title clear below the lockup (the `#v(2.6cm)`). feature-top:
      white lockup + QR overlaid on the hero band (auto masthead hidden)
- [ ] No `cover:`, no `#outline()`, no Acknowledgement of Country, no
      `#slop-back-cover()`, no `#pagebreak()` anywhere
- [ ] Visible title is the fabricated project name (steering-driven); if it
      carries a colon, the part before is the title band's title and the part
      after is the subtitle (not the whole string as title plus a third invented
      line); the author line names **2-3 roster researchers** with the lead
      author's school (`canon/roster.yml` / `canon/schools.md`); no other person
      named anywhere
- [ ] Layout matches the roll. feature-right: a tall (9:16) image full-bleeds
      the right third with a scrim + white hero quote; title + 2-column body in
      the left two-thirds (right margin reserved). feature-top: a wide (16:9)
      image full-bleeds the top band with two scrims + the overlaid white
      masthead, title, subtitle, and gold rule; 2-column body fills the page
      below
- [ ] Section names drawn from the reservoirs
- [ ] Two house-style images (`references/slop-style/` refs): the 4K feature
      (9:16 for feature-right / 16:9 for feature-top) and the wide (21:9, 2K)
      body image as a `height: 1fr` block (`fit: cover`) filling the left grid
      cell's foot; plus one full-width chart (a 2nd only with room) leading the
      right cell, via `chartfig`, none bleeding past the column; chart captions
      carry the falsifiable claim
- [ ] Both grid columns balanced and full to the page foot (the `1fr` body image
      and the `#v(1fr)` footer pin do this; fill-probe band ≲ 40 mm per step 3
      of "Compile and one-page fit"); the deadpan ethics / data footer line is
      **on-page** (not clipped off the bottom), no person
- [ ] Charts use brand styling per `../../_shared/chart-workflow.md` (no rainbow
      bars; legends top/bottom) and **fill the column** (responsive `layout`,
      wide-short aspect --- no side padding)
- [ ] 4-6 **real, verified** references (each DOI resolves or arXiv id matches);
      real authors/titles/venues, DOI or arXiv id rendered; no fabricated entry
- [ ] Telegraphic, scannable body (fragments and bullets, not paragraphs) in the
      academic-present register (past-tense methods, hedged findings); no
      exclamation marks, no satire signals on the page
- [ ] PDF metadata title is
      `This Slop University Research Poster Does Not Exist: <steering     verbatim>`;
      no other metadata fields populated

## Common failure modes (preset-specific)

- **Spills to a second page**: follow step 4 of "Compile and one-page fit"
  (tighten prose, shorten the chart plot; never trim the references).
- **Chart bleeds into the gutter / next column**: a chart (or image) was
  embedded with a bare `#figure(image(...))` or `slop-inline-figure`. Use the
  `chartfig` helper (a plain image).
- **Reads bland**: the title, aims, captions, and headline numbers aren't
  visibly driven by the prompt. Crank the commitment shapes --- a falsifiable
  caption with a checkable figure and date, a too-clean headline number ---
  while keeping the academic register intact.
- **Voice cracks into advocacy or jokeyness**: an exclamation mark, a knowing
  aside, first-person enthusiasm. Regenerate. The poster reads straight; the
  genre is the joke.
- **Title looks like a heading, not a banner**: the project title was written as
  `=` / `==` instead of a manual `text()` block. Use the title-band block ---
  gold-on-white for feature-right, white-on-scrim in the hero for feature-top.
- **(feature-top) Lockup or title washes out on the hero**: the scrim isn't deep
  enough, or the automatic masthead wasn't hidden. Deepen the relevant scrim's
  end stop (`#000000cc` → `#000000e6`) and confirm `hide: (…, "masthead")` ---
  do not lighten the photo or move the art.
- **(feature-top) Body hidden behind the band, or a white gap below it**:
  `m-top` is out of step with the band height. Keep `m-top` ≈ `band-h` + the
  band→body gap; too small and the body flows under the band, too large and a
  white strip opens between them.
- **Right column underfills** (a slack band above the footer): most common on
  **feature-top**. Step 3 of "Compile and one-page fit" quantifies and fixes it.
  Fill it, don't hide it.
- **Footer missing / clipped off the bottom edge** (feature-right): the title
  and body weren't wrapped in the outer `#grid(rows: (auto, 1fr))`. A big empty
  band with **no footer at all** is the tell --- see the outer-grid gotcha and
  Skeleton A.

## What this preset is not

- Not a booklet. No cover, contents, Acknowledgement of Country, back cover, or
  even-page parity --- those are the `format: booklet` path. This is
  `format: poster`.
- Not a real research poster. The project, data, and charts are generative
  fiction --- but the cited references are real, verified literature (that is
  the point).
- Not a place for new chart or genre conventions. Chart mechanics belong in
  `../../_shared/chart-workflow.md`; cross-preset voice doctrine belongs in
  `../genre.md`.
