# slop-university

Slop University's document press: a PDF typesetter with two paths. The
**satirical** path is driven by named presets that generate plausible-but-fake
institutional documents in the Slop University identity (strategy, impact
report, research poster, etc.). The **faithful** path typesets arbitrary source
material (URL or document) without rewriting it, in the genuine ANU template ---
a local-only tool. See [README.md](README.md) for the why; see
[skills/from-source/SKILL.md](skills/from-source/SKILL.md) and
[skills/from-preset/SKILL.md](skills/from-preset/SKILL.md) for the two
workflows.

## Workflow

Two slash commands:

- `/from-preset <preset-name> <steering>` → `skills/from-preset/SKILL.md` ---
  generate a fake doc from a named preset blueprint. The registry is
  `skills/from-preset/presets/` (currently `strategy`, `impact-report`,
  `research-poster`, `paper`); each blueprint declares its own format
  (`booklet`, `poster`, or `paper`), identity, and title policy. Drop a new file
  in to add another (authoring guide: `skills/from-preset/presets/README.md`).
- `/from-source <source>` → `skills/from-source/SKILL.md` --- typeset a URL or
  local file (`.docx`, `.odt`, `.md`, `.html`, `.typ`, `.txt`) faithfully into
  the ANU template. No rewriting; small editorial calls for heading hierarchy /
  lockup / cover theme only.

Both paths cross-ref shared visual doctrine in `skills/_shared/` (parallel image
workflow, the two-ink house visual style, typst layout discipline, output
naming). The preset path additionally loads `skills/from-preset/genre.md` for
the satirical institutional-voice doctrine --- the faithful path does not load
this file (the source's own voice is preserved).

Generated outputs (`output/<prefix>-<slug>-<seed>.typ`, the matching
`output/<prefix>-<slug>-<seed>-images/` folder, charts where applicable in
`output/<prefix>-<slug>-<seed>-charts/`, and the final PDF in
`output/pdf/<preset>/` --- e.g. `output/pdf/research-poster/`) are kept locally
only --- they're gitignored. Don't commit them or tag the run.

## The institutional canon (`canon/`)

Slop University is a persistent fiction: its people, schools, and units live in
`canon/` and are reused across every output.

- `canon/roster.yml` --- the fabricated researcher roster (name, title, school,
  bio, headshot). Any named person in any generated artefact comes from here;
  never a real person, never a name invented inside a run. Roster additions
  require a name-collision check (web search incl. the ANU staff directory ---
  the nearest institution is the likeliest collision) and a house-style headshot
  in `canon/headshots/`, eyeballed for accidental real-person likeness.
- `canon/schools.md` --- school, unit, and lab names. Never invent an org unit
  inside a run; add it to the canon first.

## Conventions

- **Preset path:** one steering prompt per run. The prompt is the document's
  topic; the institutional voice is the only floor. See
  `skills/from-preset/genre.md`.
- **Faithful path:** no rewriting. The source's prose, structure, and voice pass
  through verbatim. Small editorial calls (heading levels when ambiguous, lockup
  choice, cover-image theme) are allowed and surfaced in the run's text output.
  See `skills/from-source/SKILL.md`.
- Titles: each preset's blueprint ("Doc identity" table) declares its title
  policy --- the booklets fix their cover titles; `research-poster` and `paper`
  derive the visible title from the steering prompt (a poster's or paper's title
  _is_ its content). The satirical formula lives only in the PDF metadata title,
  for every preset.
- Output filenames (prefix, slug, seed, and the per-preset `output/pdf/<group>/`
  folders) are defined in `skills/_shared/output-naming.md`; preset blueprints
  declare their own prefix and group.
- Never include footers, watermarks, or other "this is satire" signals on the
  rendered pages of a preset run. The PDF metadata title is the deliberate
  exception (per each preset's "Doc identity"). The booklets and posters must
  read straight; the joke is the genre.
- The faithful path uses the source's actual title as the PDF metadata title ---
  no satirical formula. The source's content is real, not satire.

## Style references

- Closest typst reference: `~/.nb/home/studio-business-plan-2026.typ` (same
  layout core, ANU-branded; copy structural moves, not content or its import
  block)
- Genre PDF: `~/.nb/home/anu-corporate-plan-2026-v5.pdf` (real institutional
  document, for tone and visual convention)
- Typst packages (all `@local`, symlinked into
  `~/.local/share/typst/packages/local/`):
  - `university-typst-template:0.1.0` --- the de-branded layout core (lives in
    the `anu-typst-template` repo under `packages/`); all layout machinery,
    branding injected as data
  - `slop-university-brand:0.1.0` --- the Slop University brand layer, in this
    repo at `brand/slop-university-brand/0.1.0/` (`slop-*` exports; palette from
    the lockup gold `#b97d1c`). The **preset path** imports this
  - `anu-typst-template:0.3.0` --- the genuine ANU brand layer (private repo;
    `anu-*` exports). The **faithful from-source path** imports this
- **Generated imagery** follows the two-ink house style in
  `skills/_shared/visual-style.md` (risograph register, lockup gold + ink black
  on warm cream), steered by the curated seed set in `references/slop-style/`
  (fully generated; no real photos). The real-ANU campus photos
  (`references/*.avif`, local-only, not redistributed) serve only the faithful
  path --- see `skills/_shared/image-workflow.md` for the two regimes and the
  style-canon promotion mechanism.
- Chart workflow (any preset whose blueprint declares charts): native
  [gribouille](https://m.canouil.dev/gribouille) charts. Theme + palettes +
  scale helpers come from the brand package (`slop-theme`, `slop-categorical`,
  `slop-colour` / `slop-fill` --- no theme file to copy); worked `*.typ`
  examples per chart type live in the core package's `examples/charts/`. Each
  chart is a `#plot` authored as a `.typ` file, imported into the document and
  rendered inline (no SVG, no Python / `uv` / `vl-convert`). Pipeline, chart
  types, and brand styling are in `skills/_shared/chart-workflow.md`.
- Closest typst reference for chart / card layout (impact-report and
  research-poster):
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0/examples/design.typ`

## Don't

- Don't add a footer like "Generated by Claude" or "Satirical artwork". The
  booklets and posters have to read straight to land the point.
- (Preset path) Don't insert verifiable factual claims that could be checked and
  falsified ("$200M committed by 30 June 2026" → no; "significant investment in
  research infrastructure over the plan period" → fine).
- (Preset path) Don't reuse content verbatim across runs --- vary phrasing,
  section names, initiative or vignette wording, and KPI/metric targets even
  when the steering prompt is similar.
- (Preset path) Don't name anyone outside `canon/roster.yml`, and don't invent
  schools or units outside `canon/schools.md`.
- (Faithful path) Don't paraphrase, summarise, or "improve" the source. Don't
  invent new sections, filler paragraphs, inline images, or fabricated charts.
  Editorial latitude is limited to heading hierarchy when the source is
  ambiguous, lockup choice, and the cover-image theme --- surface every
  editorial call in the run's text output.
