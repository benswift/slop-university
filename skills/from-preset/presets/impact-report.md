---
name: impact-report
description:
  School of Continuous Improvement Impact Report 2021-2026 --- past-tense
  reflective institutional voice, steering-driven topic, impact-area / vignette
  / chart scaffolding. School-level doc; carries a persona system, chart
  workflow, and the School's in-house terminology.
---

# Impact-report preset

Produce one School of Continuous Improvement Impact Report from a single
steering prompt. The output should be indistinguishable from a real five-year
impact report to a tea-room reader and recognisably institutional at a glance
(via the template's gold, Public Sans and layout), with the Slop University
lockup on the cover and back.

The genre is past-tense and reflective: an impact report looks back at what was
done, not forward at what will be. The only future-tense section is the closing
"Looking ahead".

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `../genre.md` for voice doctrine and steering rules
- `../../_shared/typst-layout.md` for template import, metadata, back cover,
  parity-fix workflow
- `../../_shared/image-workflow.md` for parallel image generation
- `../../_shared/visual-style.md` for the two-ink house imagery style
- `../../_shared/chart-workflow.md` for the chart pipeline and brand styling
- `../../_shared/output-naming.md` for slug, seed, output paths
- `canon/roster.yml` and `canon/schools.md` for people and org units

## Doc identity

| Field                      | Value                                                                    |
| -------------------------- | ------------------------------------------------------------------------ |
| Canonical name             | School of Continuous Improvement Impact Report                           |
| Cover title                | `Impact Report 2021–2026` (en-dash U+2013, not hyphen)                   |
| Cover subtitle             | drawn from the Cover-subtitle reservoir                                  |
| Period covered             | 2021-2026 (fixed)                                                        |
| Cover lockup               | `slop`                                                                   |
| Back-cover lockup          | `slop` (`#slop-back-cover(config: (bleed: 3mm))`)                        |
| Filename prefix            | `slop-impact`                                                            |
| Page-count range           | 12-18, even                                                              |
| Register                   | past-tense reflective (except "Looking ahead", which is future-tense)    |
| PDF metadata title formula | `This Slop University Impact Report Does Not Exist: <steering verbatim>` |

The `slop` lockup is the university-level Slop University wordmark --- it does
**not** carry the school's name, so surface "School of Continuous Improvement"
in the cover subtitle or opening matter for the report to still read as a School
document. The back-cover lockup renders at a fixed 10cm width (the `back-width`
in the brand package's lockup entry); making it visually bigger is a
brand-package change rather than a per-doc tweak.

`logos:` is left at default (no "Office of Research Outputs" margin wordmark ---
this is a school-level doc, not an Office artefact).

PDF metadata title is the deliberate satirical tell (not visible on rendered
pages). No other metadata fields populated.

Slug is derived from the steering prompt per `../../_shared/output-naming.md`.

## Inputs

One free-text **steering prompt**. 1-3 short sentences, or a phrase. Examples:

- "regional engagement and community knowledge"
- "AI safety and responsible adoption"
- "a quiet pivot to defence"
- "post-pandemic resilience"
- "research that pays its way"
- "impact at the kitchen table"

The prompt is the document's topic. The institutional voice (see `../genre.md`)
is the only floor; everything else --- impact-area names, vignettes, At-a-glance
metrics, pull-quotes, charts, imagery --- bends to the prompt.

## The genre's structural skeleton

| Section             | Length                                                     | Notes                                                                                                                                                                                                         |
| ------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cover               | 1 page                                                     | Slop lockup; subtitle from reservoir                                                                                                                                                                          |
| Director's foreword | ~250 words                                                 | Past-tense, reflective; content driven by the steering prompt; signed by role, not name                                                                                                                       |
| At a glance         | ~1 page                                                    | Headline metrics in a card grid (`slop-highlight-card`); metrics can be driven by the steering prompt                                                                                                         |
| Who we are          | ~200 words                                                 | Brief School framing; mission, ethos, who works there in aggregate                                                                                                                                            |
| Impact areas × N    | ~2 pages each (chart-bearing areas may run a touch longer) | N = 3-5; each: framing paragraph + 1-2 vignettes (partner archetypes; roster researchers may be quoted) [+ one chart if this area carries one] + one pull-quote; ~50% of areas (⌊N/2⌋ to ⌈N/2⌉) carry a chart |
| Looking ahead       | ~250 words                                                 | Future-tense close; the only future-tense section in the doc                                                                                                                                                  |
| Acknowledgements    | ~150 words                                                 | Vague-aggregate ("we thank the dozens of organisations…")                                                                                                                                                     |
| Back cover          | 1 page                                                     | `#slop-back-cover()`                                                                                                                                                                                          |

Total: 12-18 pages, even. No manual page breaks anywhere (the template breaks
after the contents).

Lengths and counts above are baselines. Per-run variation, scoped by the rolled
document persona, is in "Per-run variation rolls › Document persona" and
"Per-run variation rolls › Structural counts".

## Per-run variation rolls

Roll once per run, upfront (the orchestrator workflow lists the order). The
early matter (cover, contents) and the genre voice / image workflow / typst
layout are off-limits to variation; they're fixed elsewhere.

### Document persona

Roll one persona for the run before any other variation. The persona sets the
document's intent --- what shape and register it's reaching for --- and cascades
into the structural-count, vignette, chart, and voice rolls below. Without it,
independent rolls produce runs that vary on the surface but feel structurally
identical.

Roll uniform across the four:

**a) narrative-retrospective** --- the default-shaped run. Partner stories are
the core unit; impact areas read as a sequence of "what we did with these
collaborators". Voice: warm, communal, present-tense-flavoured-past. Director's
foreword warm-pastoral.

**b) data-forward** --- the evidence document. Charts dominate; metrics carry
more weight than vignettes. Adds an optional sidebar section ("How we know" or
"Numbers in context") between At a glance and Impact areas. Director's foreword
goes austere --- fewer flywheel metaphors, more "the data tells the story".
Voice: cooler, registered, slightly auditor-general.

**c) capstone-essay** --- the Director's voice expands and dominates. The whole
doc reads like an extended Director's reflection. Impact areas compress;
vignettes become inline anecdotes within the framing prose rather than separate
vignette blocks. Pull-quotes thin out and become more central when they appear.
Voice: essayistic, personal, ruminative; the Director's register bleeds into the
impact-area framing too.

**d) case-study book** --- each impact area is a self-contained mini-paper with
internal structure: framing → "Background" → "What we did" → "Outcomes" →
pull-quote. The School describing its own work for someone who wants the
case-study detail. Director's foreword shrinks to a one-page introduction.
Voice: registered research-centre annual review.

Quantitative consequences (lengths, counts, ranges) are in "Structural counts"
below.

### Section-name reservoirs

Sections from the Director's foreword onwards draw from per-section reservoirs
(one choice per section per run). Reservoirs grow over time; aim for ~4-5
entries each.

| Section role         | Reservoir                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------- |
| Director's foreword  | "From the Director", "A message from the Director", "Director's foreword", "Director's reflection" |
| At a glance          | "At a glance", "By the numbers", "Five years in numbers", "Highlights"                             |
| Who we are           | "Who we are", "About the School", "Our School", "What we do"                                       |
| Impact areas heading | "Impact areas", "Where we've made a difference", "Our work in five domains", "How we've delivered" |
| Looking ahead        | "Looking ahead", "What's next", "The next chapter", "Where we're headed"                           |
| Acknowledgements     | "Acknowledgements", "Thank you", "Our partners", "With thanks"                                     |
| Cover subtitle       | "Five years of impact", "Our first five years", "A retrospective", "Looking back"                  |

### Structural counts (scoped by persona)

| Count                      | narrative-retrospective | data-forward   | capstone-essay                             | case-study book |
| -------------------------- | ----------------------- | -------------- | ------------------------------------------ | --------------- |
| Impact areas (N)           | 3-5                     | 3-5            | 3                                          | 3-4             |
| Vignettes per area         | 1-2                     | 1              | 0 (inline anecdotes only)                  | 2-3             |
| Vignette length            | ~120 words              | ~80 words      | inline ~80-word anecdotes in framing prose | ~200 words      |
| Charts                     | ⌊N/2⌋ to ⌈N/2⌉          | ⌈N/2⌉ to N     | 1-2 total                                  | ⌊N/2⌋ to ⌈N/2⌉  |
| Pull-quotes                | 1 per area              | half the areas | 1-2 total                                  | 1 per area      |
| At-a-glance cards          | 4                       | 4              | 3                                          | 4               |
| Director's foreword length | ~250 words              | ~180 words     | 600-800 words (subheaded)                  | ~150 words      |

Same vignette count and length apply to every area within a run. Chart count
uses the persona's range, then distributes via the existing rule (avoid two
adjacent chart-bearing areas where possible).

### Chart placement

Distribute charts across impact areas. Avoid two adjacent chart-bearing areas
where possible. Roll which areas carry charts at the same time you roll the
chart count.

### Chart types

Drawn from `{line, area, scatter, grouped-bar, stacked-bar, boxplot}`. Each type
appears at most once per run unless chart count exceeds 4.

### Vignette substance

Each vignette is a short narrative paragraph about an external partner, project,
or community engagement. Length is per the persona's row in "Structural counts"
above (typically 80-200 words). Partners come from the pre-rolled archetype set
(see "Partner pre-roll" below) and are **described, never named** ("a national
statistics agency", not an invented proper noun and never a real organisation).
Roster researchers (`canon/roster.yml`) may appear by name as the School-side
lead. Use past-tense narrative voice ("In 2023, the School partnered with a
metropolitan transit authority…"; "Working with a regional health network, Dr
Vandermeer's team developed…").

### KPI / metric plausible bands (At a glance)

- HDR completions: 30-90 over 5 years
- Publications: 200-600 over 5 years
- External grants: $5M-$30M total
- Partner organisations: 40-120 over 5 years
- Student cohort: ~30-100 per year
- Capability Sprint completions: 1,500-6,000 over 5 years
- International collaborations: 15-50 partner institutions

Numbers should be specific enough to feel real and vague enough to be
unfalsifiable (though commitment-shaped metrics can be more specific).

### Partner pre-roll

At planning time, pick 4-6 partner **archetypes** from the Common external
partners list (Terminology › Common external partners) before drafting any
vignette or pull-quote. The pre-rolled set is the _only_ allowed partner pool
for the run's vignettes and pull-quote attributions.

Selection rules:

- 4-6 archetypes total
- no more than 2 from any one category --- the categories are the six list
  headers under "Common external partners" (government / cultural /
  universities-domestic / universities-international / industry / consortia)
- at least 3 categories represented
- mix salient and obscure within the set --- if "a national statistics agency"
  is in, balance with a less evocative choice like "a benchmarking consortium"

This counters salience bias: without an explicit roll, the most evocative
archetypes dominate across runs. The pre-roll forces deliberate selection. If a
vignette's narrative needs a partner not in the pre-rolled set, prefer a vaguer
aggregate ("a state government department") over adding to the set mid-draft.

## Voice-preserving commitment shapes (charts and metrics)

Charts and metrics are commitment vectors specific to the impact report. Use
these shapes as a menu throughout the document. (The general voice-preserving
commitment shapes catalogue in `../genre.md` is also applicable.)

- **A metric that's too round and too specific.** Hedge (real report):
  "Participants reported sustained behaviour change at follow-up." One notch:
  "100% of senior-executive participants reported behaviour change at 6-month
  follow-up, with the same effect size at 12 months."
- **A pull-quote that names a falsifiable structural claim.** Hedge: "Our work
  has changed how the department thinks about uncertainty." One notch: "The
  agency's revised risk framework, adopted in March 2024, was drafted with the
  School's methodology team and remains in force without amendment."
- **A chart annotation labelling an outlier with a checkable date and figure.**
  Hedge: a line chart labelled "Strong growth from 2023". One notch: a labelled
  callout reading "March 2024: 117 partner organisations engaged, 3× the 2022
  baseline" pointing to a specific data point.

## Terminology

The impact report is a parody of an in-the-know institutional document; the
genre lands when the terminology is right and falls when it isn't. The School of
Continuous Improvement has an in-house vocabulary (consistent with
`canon/schools.md`); use its preferred forms, not the outsider-plausible
alternatives.

### Programs and degrees

- **Master of Applied Measurement**: the flagship program's official title. In
  body prose, refer to it as "the Master of Applied Measurement", "the Masters
  program", or "the program" --- not "MAM" (informal, off-register in a formal
  report).
- **MAM**: the program's acronym. Use only in space-constrained contexts:
  stat-card titles, chart axes/legends, table headers. Never in running prose.
- **PhD candidates**: the term for higher-degree research students in body
  prose. Not "PhD students", not "doctoral students". The umbrella term **HDR**
  (Higher Degree by Research) is fine for aggregate counts on stat cards but
  rarely in prose.
- **Capability Sprints**: the School's short-course / executive education line.
  The named Sprint titles are canon (`canon/schools.md` › Programs and named
  initiatives). The umbrella category "microcredentials" is also used.

### The School itself

- **Slop University School of Continuous Improvement**: the formal full name.
- **School of Continuous Improvement**: the standard prose form.
- **the School**: the in-prose shorthand. This is the most common form in body
  text.
- **SCI**: informal/internal acronym only --- never in body prose, stat cards,
  or chart labels.
- **the Institute for Measurable Outcomes**: the School's predecessor
  institution. The School "traces its origins" to it. Mention sparingly ---
  never conflate with the School.
- Schools sit directly under the University --- there are no faculties or
  colleges. A common outsider-error is inventing one ("Faculty of Improvement
  Sciences"); don't.

### Roles and people-as-aggregate

- **Faculty** is an Americanism the School does not use. Refer to individuals by
  title (Professor, Senior Lecturer, Research Fellow) or in aggregate as
  "staff", "researchers", or "our people".
- **the cohort** is the in-house term for a Masters-program intake.
- **PhD candidates** or **candidates** for HDR students.
- **Metric Steward**, **Improvement Lead**, **Indicator Convenor**, and
  **Dashboard Resident** are School-specific staff role titles --- use
  sparingly, as roles. Named individuals come only from `canon/roster.yml` (with
  their canonical titles); the role titles here are for aggregate or anonymous
  references.

### Named projects, centres, initiatives

The canonical list (the Adaptive Metrics Lab plus the named initiatives) lives
in `canon/schools.md` › Labs and Programs; surface entries from it when the
run's variation lands a relevant impact area. Don't invent additional project
names that mimic those patterns; reuse the canon or stay generic --- describe
the work in functional terms ("a multi-year program of work", "a curriculum
collaboration", "a residency strand") rather than coining a new fabricated
project name mid-run. If a new named initiative is genuinely needed, it belongs
in the canon first.

### Research themes

The School organises its work into six research themes, with two further strands
in active development. Drawing impact-area names and substance from these
grounds a run in what the School (fictionally) does. When a run rolls 3-5 impact
areas, pick from this list and rephrase per the variation roll (e.g. "Evaluation
ecosystems" → "Making evaluation count"). Vignettes should draw on signature
work.

1. **Measurement systems and instruments** --- how organisations count, and what
   the counting does. Signature work: the Indicator Commons; benchmark
   harmonisation; the Composite Index of Composite Indices; instrument-drift
   studies.
2. **Evaluation ecosystems** --- evaluation as a system property rather than an
   event. Signature work: Evaluation of Evaluation (EoE); the Review Cadence
   Observatory; proportionate-assurance frameworks; the meta-review program.
3. **Organisational learning and improvement** --- capability uplift and the
   improvement cycle at institutional scale. Signature work: the Continuous
   Improvement Handbook; Operational Excellence; the improvement-cycle archive;
   after-action ecologies.
4. **Data cultures and dashboards** --- how dashboards shape attention,
   authority, and organisational time. Signature work: the Living Dashboard;
   Dashboard Literacy; ambient KPIs; the quiet-metrics pilot.
5. **Impact science** --- the pathways by which counted work becomes valued
   work. Signature work: the Impact Pathway Atlas; significance studies;
   citation-flow modelling; narrative-CV instrumentation.
6. **Anticipatory performance** --- measuring what hasn't happened yet.
   Signature work: leading-indicator design; early-warning ensembles;
   pre-registration cultures; the anticipatory-baseline program.

Two further strands sit alongside the six, useful as cross-cutting flavour
rather than as standalone impact areas:

- **Improvement theory and methods** --- intellectual genealogy and
  methodological development; underpins all applied themes. Signature work: the
  improvement-cycle canon; methodological pluralism; the Methods Book; the
  measurement archive.
- **Metric stewardship** --- the ethics and governance of indicators across
  their life cycle. Signature work: indicator retirement protocols; the Metric
  Stewardship Charter; custodianship models for shared measures.

The steering prompt selects which themes to surface and where to lean; it does
not introduce a theme that isn't here. If a steering prompt genuinely doesn't
fit any theme (e.g. "a quiet pivot to defence"), season the closest theme(s) by
emphasis rather than fabricating a new one.

### Common external partners

Partner **archetypes** for vignettes and pull-quote attributions --- described
roles, never proper nouns. Never name a real organisation (a real org named as a
Slop University collaborator is a verifiable false claim about that org), and
never invent a fake proper-noun organisation (a name invites checking; a
description hedges). Pick archetypes that fit the theme being narrated; mix
categories within a run.

- **Government and agencies**: a national statistics agency; a federal
  infrastructure department; a state audit office; a metropolitan transit
  authority; a services-delivery agency; a regulatory commission.
- **Cultural and national institutions**: a national library; a public
  broadcaster; a state museum network; a performing-arts training academy.
- **Universities (domestic)**: a Group-of-Eight-adjacent research university; a
  regional university network; a dual-sector institution.
- **Universities and research bodies (international)**: a European agronomy
  institute; a Nordic evaluation agency; an East Asian metrology laboratory; a
  North American policy school.
- **Industry**: a big-four professional services firm; a national
  telecommunications carrier; a logistics major; an engineering peak body; an
  interactive-theatre company.
- **Research consortia and foundations**: a cooperative research consortium; an
  international economic forum; a family philanthropic foundation; a
  chronic-disease foundation.

If the list doesn't cover a run's need, prefer a vaguer aggregate ("a state
government department") over inventing a new archetype mid-draft.

### Partnership language

- **collaborators** is the School's preferred term, not "industry partners" or
  "stakeholders".
- "**collaboration between [the partner] and the School of Continuous
  Improvement**" or "**working with [the partner]**" are the standard framings.
- The PhD program's "**real-world partnerships with external organisations**" is
  a verbatim phrase worth honouring if a run touches the PhD program.

### Characteristic phrases worth borrowing

These are the School's signature framings and lend authenticity when used
sparingly:

- "measurable, repeatable and improvable" (the recurring three-adjective mantra
  applied to systems)
- "measure, model, monitor and improve" (the four-verb sequence)
- "translational improvement" (preferred over "applied improvement")
- "indicator ecosystems" (technical term preferred over bare "metrics")
- "the counted, the countable and the not-yet-counted" (signature three-part
  framing of scope)
- "evidence-led improvement and innovation"
- "convening, calibrating and curating"

Use these sparingly --- one or two per run. Wall-to-wall mantra parroting reads
as written-from-the-outside-trying-too-hard.

### Common outsider-errors that kill the joke

- Using "MAM" in prose.
- Using "SCI" anywhere in the document.
- Calling the School "the Institute" (it's a School; the Institute for
  Measurable Outcomes is the predecessor).
- "Faculty" used to mean staff (Americanism).
- "Stakeholders" instead of collaborators.
- Attaching the School to an invented faculty or college (schools sit directly
  under the University).

### Director's voice (foreword register)

The Director's foreword is the most voiced section of the report. Its register
is reflective-formal --- more institutional than a weekly community letter, but
carrying recognisable traces of one. The Director is a **role, never a name**:
the foreword signs off "Director, School of Continuous Improvement", and no run
gives the Director a name (the roster has no Director --- an institution whose
most personal document is signed by an office, not a person, is the thesis in
miniature).

Voice features:

- **Sentence rhythm: long and accumulative.** A single sentence piles
  subordinate clauses, parentheticals, and em-dash interruptions before landing.
  Don't break these into shorter sentences for "clarity"; the rhythm is the
  voice.
- **Em-dashes everywhere** (`---` in source, per the project's house style) as
  the dominant aside-marker, not commas or parentheses.
- **"Community" as load-bearing noun.** Used warmly, repeatedly. The School is a
  community; partners are part of a wider community; the five years are
  something the community worked through together.
- **The flywheel / cycle metaphor for institutional effort.** The Director
  reaches for it when describing momentum: _the flywheel turned_, _each cycle
  compounding on the last_, _the loop closed_. One use per foreword is plenty;
  more reads as parody-by-pattern-match.
- **Scene-setting openers.** Open with a reflective image or a direct address to
  the reader ("Five years is a long time in measurement…"), not a
  thesis-statement summary.
- **Aggregate shout-outs.** The warm real-director gesture of naming individuals
  translates here to aggregate naming ("the staff who shaped each cohort") or to
  a single roster researcher named with their canonical title where a body
  section picks the thread up.
- **Self-deprecating institutional aside.** Keep one "we walked back from
  positions we held with confidence" or "the honest answer is partial" moment; a
  Director willing to admit limits is a voice-tell of the genre.
- **Tone: warm, pastorally concerned, emotionally present.** The foreword should
  not read as a press release. It should read as someone who genuinely means it.
- **Closing pattern.** A short, personal-sounding closing paragraph followed by
  the role-not-name signature ("Director, School of Continuous Improvement").
  Off-limits: any name.

**Phrases to avoid** because they read as off-register in a printed report:
all-caps cheering, exclamation runs, "this week / next week" framing (the
foreword is five-years-retrospective, not a weekly update).

The right voice: a Director who normally writes a warm community letter, sitting
down to write a more formal piece for an Impact Report, and not entirely
succeeding in suppressing the warmth. That last bit is the parody.

## Imagery (preset specifics for image-workflow.md)

- Image folder: `output/slop-impact-<slug>-<seed>-images/`
- Prompts: 1 cover (3:4 portrait) + 4 inline (16:9 landscape); reserve a 5th
  inline as the parity-fix spare. All in the two-ink house style
  (`../../_shared/visual-style.md`), steered by `references/slop-style/`.
- Resolution: cover at `--resolution 4K` (it full-bleeds the A4 cover); inlines
  at `--resolution 2K` --- they land as part-page figures within their sections,
  so 2K is ample and 4K would just be wasted pixels and generation time.
- Cover image should evoke past tense / retrospective register --- a quiet
  workshop scene, a closing-day gathering, a thoughtful figure with a research
  artefact --- not the future-facing aspirational scenes typical of a strategy.
- Record an explicit `inline-N` → section assignment when planning, so each
  generated inline matches its target section.

## Chart workflow (preset-specific)

Charts are an impact-report scaffold. The full pipeline (author a gribouille
chart `.typ`, import it into the document, render inline) and the brand-styling
rules (palette helpers, legend placement, title vs caption) live in
`../../_shared/chart-workflow.md`. Impact-report specifics:

- Chart folder: `output/slop-impact-<slug>-<seed>-charts/`.
- Count and types come from the persona rolls above ("Structural counts", "Chart
  placement", "Chart types"); distribute charts across impact areas, avoiding
  two adjacent chart-bearing areas where possible.
- Charts and metrics are commitment vectors here --- see "Voice-preserving
  commitment shapes (charts and metrics)" above for the impact-report shapes (a
  labelled outlier with a checkable date and figure is the workhorse).

## Style references

Read these before generating:

- **Closest typst reference**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/examples/design.typ`
  --- it carries the highlight-card grid, feature-page, and inline-figure chart
  usage (under the core's neutral names). Copy the structural moves --- NOT the
  import block or content; this preset imports the slop brand package and uses
  its `slop-*` names.
- **Genre PDF**: `~/.nb/home/anu-corporate-plan-2026-v5.pdf` --- a real
  university corporate plan, for the glossy-report visual conventions;
  impact-report-specific genre PDFs aren't available, so it doubles as a tonal
  reference (tone only --- imagery follows the two-ink house style).
- **Layout core source**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0` --- for
  the available helpers and theme machinery. Branding comes from
  `@local/slop-university-brand:0.1.0`.
- **Chart examples**:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/examples/charts/`
  --- one worked `*.typ` per chart type. Theme + palettes come from the brand
  package (no theme file to copy); author each `#plot`, then import it inline.

## Typst structure

Imports include `slop-inline-figure` for charts. The skeleton:

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-back-cover, slop-colors, slop-highlight-card, slop-inline-figure
// plus one import per chart you embed (see "Inline figures and charts"):
//   #import "/output/slop-impact-<slug>-<seed>-charts/chart-1.typ": chart as chart-1

#set document(
  title: "This Slop University Impact Report Does Not Exist: <steering prompt verbatim>",
)

#show: slop.with(
  title: "Impact Report 2021–2026",
  subtitle: "<from cover-subtitle reservoir>",
  cover: read("/output/slop-impact-<slug>-<seed>-images/cover.jpg", encoding: none),
  config: (bleed: 3mm),  // 3mm print bleed: trimmed, saddle-stitched booklet
)

#outline(title: [Contents], depth: 1)

= From the Director
[paragraphs, past-tense reflective...]
#figure(image("/output/slop-impact-<slug>-<seed>-images/inline-1.jpg"))
[more paragraphs, then the role-not-name signature]

= At a glance
[opening sentence framing the five years]

#grid(
  columns: (1fr, 1fr),
  column-gutter: 0.8em,
  row-gutter: 0.8em,
  slop-highlight-card("graduation-cap", "<metric 1 title>")[<1-2 sentence framing>],
  slop-highlight-card("flask", "<metric 2 title>")[<1-2 sentence framing>],
  slop-highlight-card("community", "<metric 3 title>")[<1-2 sentence framing>],
  slop-highlight-card("globe", "<metric 4 title>")[<1-2 sentence framing>],
  // 3 or 4 metrics per persona; grid shape follows the count (see Highlight cards subsection)
)

= Who we are
[~200 words on the School's mission, ethos, aggregate description]

= Impact areas

== <Area 1 name>
[framing paragraph...]
[vignette 1: partner archetype (described, not named), ~100-150 words past-tense narrative]
[vignette 2 (if rolled), same shape]

#slop-inline-figure(
  chart-1,
  caption: [<chart caption>],
)

#quote(block: true, attribution: [<partner-archetype role, or a roster researcher>])[
  "<pull-quote text>"
]

== <Area 2 name>
[same shape; charts only on chart-bearing areas]

[...continue for all impact areas...]

= Looking ahead
[~250 words; future-tense close; the only future-tense section]

= Acknowledgements
[~150 words; vague-aggregate; no names]

#slop-back-cover(config: (bleed: 3mm))
```

### Highlight cards (At a glance)

One card per headline metric. Card count is 3 or 4 (per persona --- see "Per-run
variation rolls › Structural counts"); each card title is the metric, each body
its framing, each icon matched to the metric's actual language. The card helper,
grid shapes per count, and the icon-name lookup procedure live in
`../../_shared/typst-layout.md` › "Highlight cards and icon lookup".

### Inline figures and charts

- 4-5 inline image figures via
  `#figure(image("/output/slop-impact-<slug>-<seed>-images/inline-N.jpg"))`. The
  template's `show figure.where(kind: image)` rule extends them to the right
  page edge.
- Charts via `#slop-inline-figure(chart-N, caption: [...])`, where each chart is
  imported with
  `#import "/output/slop-impact-<slug>-<seed>-charts/chart-N.typ": chart as chart-N`.
  `slop-inline-figure` keeps the figure within the text column (charts shouldn't
  bleed to the page edge).
- Place each inline image inside the section whose content it depicts. The
  `inline-N.jpg` numbering is just a sequence; what matters is that the prompted
  scene matches the surrounding text. Keep an explicit prompt-to-section map
  when planning.

### Pull-quotes

Use `#quote(block: true)` --- typst's block-quote form (the template's
`show quote.where(block: true)` rule sets the type/spacing). Markdown-style
`> ...` does NOT render as a block quote in typst; it shows up as a literal
greater-than character.

**Known template bug**: the core template's block-quote show rule renders only
the body and silently drops `attribution:` --- so carry the attribution inside
the body, right-aligned:

```typst
#quote(block: true)[
  "Working with the School over three years gave us the methodology
  vocabulary we now use across the department."
  #align(right)[--- Deputy Secretary, a federal infrastructure department]
]
```

(When the core template's rule learns to render `it.attribution`, revert to the
`attribution:` parameter.)

Attributions name partner-archetype roles (described, never a real or invented
proper-noun organisation) or roster researchers with their canonical title.

## Pre-ship checklist (preset-specific)

Generic checklist items live in `../SKILL.md`. Impact-report-specific items:

- [ ] Canonical name is "School of Continuous Improvement Impact Report"; cover
      title is exactly "Impact Report 2021–2026" with an en-dash
- [ ] Period is 2021-2026 (referenced in body text; subtitle phrasing varies)
- [ ] Cover lockup is `slop`; back-cover lockup is `slop`
- [ ] Title and Acknowledgements content are unaffected by the steering (other
      elements --- impact-area names, vignettes, metrics, pull-quotes, charts,
      foreword content, imagery --- can be driven by it)
- [ ] Any named person is a roster researcher with their canonical title
      (`canon/roster.yml`); the Director is never named; vignette partners and
      pull-quote attributions are archetype descriptions, never real or invented
      proper-noun organisations
- [ ] Document persona was rolled at planning time and the run's structural
      counts (impact areas, vignettes per area, vignette length, pull-quote
      frequency, At-a-glance card count, Director's foreword length) match that
      persona's column in "Per-run variation rolls › Structural counts"
- [ ] Partners drawn exclusively from the pre-rolled archetype set (4-6; ≤2 from
      any one category; ≥3 categories represented)
- [ ] Charts: count matches the persona's range; types drawn from
      `{line, area, scatter, grouped-bar, stacked-bar, boxplot}` with each type
      appearing at most once (unless chart count > 4)
- [ ] At a glance contains a `#grid` of 3 or 4 `slop-highlight-card`s (no 5- or
      6-card layouts) with Iconoir glyphs that match each metric's theme
- [ ] Impact area count matches the persona's range; vignette count and length
      are consistent across areas in this run
- [ ] Section names (Director's foreword onwards) came from the reservoirs
- [ ] Charts inline within their impact areas
- [ ] Terminology follows the School's in-house forms (no "MAM"/"SCI" in prose,
      no "faculty", no "stakeholders", no invented college)
- [ ] Page count is even and within **12-18 pages**

## Common failure modes (preset-specific)

- **Chart fails to render**: read the `typst compile` error --- usually a
  gribouille syntax slip (compare the worked example for that chart type) or
  importing chart helpers under the core examples' neutral names instead of the
  brand package's `slop-*` names.
- **Output reads bland**: impact-area names, vignettes, pull-quotes, metrics,
  and charts aren't visibly driven by the prompt. Crank the structural
  commitments more specifically --- structural, falsifiable, particular ---
  across multiple slots, while keeping the institutional voice intact. Charts
  are particularly amenable to a labelled outlier callout that names a checkable
  date and figure.
- **A real organisation gets named as a partner**: hard failure --- a real org
  named as a Slop University collaborator is a verifiable false claim about that
  org. Re-describe as an archetype and regenerate the vignette.

## What this preset is not

- Not a fact-checked impact report. The output is generative satire.
- Not the strategy preset. Past-tense reflective register; no pillars; no
  implementation phases; charts and pull-quotes are core scaffolding here.
- Not a place for new genre conventions. If a convention emerges that applies to
  multiple presets, add it to `../genre.md` --- not here.
