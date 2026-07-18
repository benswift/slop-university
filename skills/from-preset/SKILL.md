---
name: from-preset
description:
  Generate a satirical Slop University document from a named preset (e.g.
  strategy, impact-report) and a single steering prompt. Drives the shared
  workflow --- planning, writing, image generation, chart generation if the
  preset declares them, compile, parity-fix --- while the preset blueprint
  supplies the doc identity, structural skeleton, reservoirs, and skeleton
  typst. Use when invoked with `/from-preset <preset-name> <steering>`.
---

# from-preset

Orchestrate a satirical-document run from a named preset. The preset declares
**what** the doc looks like (identity, skeleton, reservoirs, checklist); this
skill drives **how** the run executes (planning, writing, imagery, charts,
compile, parity).

## Inputs

The slash command argument splits on the first whitespace:

- **preset name** (first whitespace-separated word) --- one of the blueprints in
  `presets/`. Examples: `strategy`, `impact-report`.
- **steering prompt** (everything after the first whitespace) --- 1-3 short
  sentences, or a phrase. The preset's blueprint defines what the prompt is
  allowed to drive; `genre.md` defines the voice floor.

Example: `/from-preset strategy lean into sovereign capability` → preset =
`strategy`, steering = `lean into sovereign capability`. Workflow step 1 defines
how the name resolves.

## Available presets

Run `ls skills/from-preset/presets/` (and `ls private/*/presets/` if present) to
discover what's currently defined. As of this writing: `strategy.md`,
`impact-report.md`, `research-poster.md`, `paper.md`, and `brochure.md` in
`presets/`.

Each preset is a single self-contained markdown file. To add a new one, drop a
`presets/<name>.md` file shaped like the existing ones --- the authoring guide
is `presets/README.md` (not needed for generation runs).

## Document format

Each preset declares a **format** in its "Doc identity" --- `booklet` (the
default), `poster`, or `paper`. The format determines which of the
booklet-shaped workflow steps and checklist items apply.

- **`booklet`** (`strategy`, `impact-report`, `brochure`) --- a multi-page
  portrait booklet: cover image, auto-generated contents, body sections, and a
  full-page back cover; no manual page breaks (the template breaks after the
  contents); even page count, parity-fixed. The steps below assume this format
  unless a preset says otherwise.
- **`poster`** (`research-poster`) --- a single-page poster: no cover, no
  contents, no back cover, no manual page breaks. It drives `slop(...)` directly
  for a light, single page (landscape or portrait per the layout roll). Steps 4,
  6, and 7 and several generic checklist items have poster-specific behaviour,
  flagged inline below; the preset's blueprint carries the details.
- **`paper`** (`paper`) --- an A4 two-column conference-style paper: no cover,
  contents, or back cover; multi-page (4-8) with **no parity requirement**; a
  verified real bibliography step (the poster verifies its shorter references
  list the same way). Treat the poster-format workflow tags as applying (no
  booklet furniture), except the page-fit check: the paper's own blueprint
  replaces the one-page rule with its 4-8 page range and bibliography
  verification.

When a step or checklist item is format-specific, it's tagged "(booklet format)"
or "(poster format)".

## Workflow

Run these in order. The preset blueprint fills in the doc-specific details at
each step.

1. **Parse inputs.**
   - Split the slash-command argument on the first whitespace into
     `<preset-name>` and `<steering>`.
   - Resolve `<preset-name>` to `presets/<preset-name>.md`, falling back to
     `private/*/presets/<preset-name>.md` (local-only, gitignored preset
     overlays --- documented in `CLAUDE.local.md` where present; absent in most
     clones). **If the `SLOPU_PUBLIC_ONLY` env var is set** (the cron wrapper
     sets it for every unattended run), skip the `private/` fallback entirely
     and read nothing under `private/` --- a preset that only resolves there is
     treated as nonexistent. If nothing resolves, stop and list available
     presets. Don't guess.
   - Derive `<slug>` and `<seed>` from `<steering>` per
     `../_shared/output-naming.md`.

2. **Read references** (in order):
   - the resolved blueprint (`presets/<preset-name>.md`, or the private overlay
     fallback)
   - `genre.md` --- voice doctrine and steering rules (a private-overlay
     blueprint may point at a sibling doctrine snapshot instead --- follow the
     blueprint)
   - `../_shared/image-workflow.md` --- parallel image generation
   - `../_shared/chart-workflow.md` --- chart pipeline + brand styling (only if
     the preset declares charts)
   - `../_shared/typst-layout.md` --- import, metadata, page-break discipline,
     parity
   - `../_shared/output-naming.md` --- filename shape
   - Any "Style references" the preset names (typst examples, genre PDFs, the
     layout core under
     `~/.local/share/typst/packages/local/university-typst-template/0.1.0/`)

3. **Plan the document** (internal, not written to disk). Roll the preset's
   variation upfront, in the order the preset's "Per-run variation rolls"
   section lists them. Typical order:
   1. Document persona (if the preset has one --- e.g. impact-report)
   2. Section names from per-section reservoirs
   3. Structural counts (e.g. pillar count, impact-area count, vignette count,
      KPI count, persona-scoped where applicable)
   4. Optional sections / persona-specific extras
   5. Pillar- or area-internal scaffolding labels
   6. Imagery prompt assignment (cover + inlines + parity-fix spare; preset
      declares the count and shape)
   7. Chart count / placement / types (only if the preset declares charts)
   8. Partner / participant pre-rolls (only if the preset declares one)
   9. Substance --- pillar/area names, KPIs/metrics, vignettes, foreword
      opening, vision, image prompts. The steering prompt drives any element the
      preset designates as steerable; the institutional voice (per `genre.md`)
      is preserved throughout.
   10. Word-budget apportionment across the resulting section list.

4. **Write `output/<prefix>-<slug>-<seed>.typ`** in one pass. Use the preset's
   "Typst structure" skeleton and include the `#set document(title: ...)` block
   per the preset's PDF metadata title formula.
   - _(booklet format)_ end with the preset's back-cover call. No manual page
     breaks (see `../_shared/typst-layout.md` › Page-break discipline).
   - _(poster format)_ no cover, contents, back cover, or manual page breaks ---
     drive `slop(...)` directly per the preset's poster skeleton (landscape or
     portrait, light, single page).

5. **Generate imagery in parallel.** Follow `../_shared/image-workflow.md`,
   using the preset's image-folder path, prompt count, and thematic shape (the
   preset's "Imagery (preset specifics)" section).

6. **Generate charts in parallel** (only if the preset's blueprint declares
   charts). Follow `../_shared/chart-workflow.md`; the preset supplies the
   chart-folder path and the per-chart count and types.

7. **Compile and check page fit.**
   - Compile invocation:
     `typst compile --root . output/<prefix>-<slug>-<seed>.typ output/pdf/<group>/<prefix>-<slug>-<seed>.pdf`
     (create `output/pdf/<group>/` if absent --- `<group>` is the preset's pdf
     subfolder per `../_shared/output-naming.md`; `--root .` makes the
     leading-slash `/output/...` image and chart paths resolve from the project
     root).
   - If the blueprint declares a **dark variant** (currently `research-poster`),
     also compile
     `typst compile --root . --input theme=dark output/<prefix>-<slug>-<seed>.typ output/pdf/<group>/<prefix>-<slug>-<seed>-dark.pdf`
     --- same source, themed by the `--input` flag (the blueprint's skeletons
     wire `slop-doc-theme` and the `-auto` chart exports for exactly this).
     Eyeball both renders; the page-fit check runs on the light one (the layout
     is identical).
   - Check `pdfinfo output/pdf/<group>/<prefix>-<slug>-<seed>.pdf | grep Pages`.
     (`pdfinfo` prints a benign `Syntax Error ... Suspects object is wrong type`
     line to stderr on Typst-generated PDFs --- a metadata-parser quirk, not a
     compile failure; the page count and title are correct. Ignore it, or add
     `2>/dev/null`.)
   - _(booklet format)_ use the parity-fix workflow in
     `../_shared/typst-layout.md`: the count must be even and within the
     preset's declared range. If odd, insert the spare inline figure at a
     natural break, generate the spare image, recompile.
   - _(poster format)_ the count must be exactly **1**. If it spills to a second
     page, follow the preset's one-page fit procedure (trim, then drop a chart
     to the smaller end of its range); recompile. Never add a page break.

8. **Stop.** Generated outputs are gitignored. Don't commit; don't tag the run.

## Generic pre-ship checklist

Common across every preset. Preset blueprints add their own checklist items on
top. Items tagged "(booklet format)" or "(poster format)" apply only to that
format.

- [ ] PDF compiles cleanly (no missing fonts, broken images, broken charts,
      overflow)
- [ ] No _visible_ "this is satire" signals on the rendered pages --- no footer
      disclaimer, no easter eggs visible at a glance
- [ ] **PDF metadata title** matches the preset's formula
      (`<formula>: <steering verbatim>`), set via `#set document(title: ...)`.
      No other metadata fields populated --- no author, description, keywords,
      date, Claude attribution. Verify with `pdfinfo`
- [ ] Voice holds the preset's register throughout (no first-person passion, no
      activist verbs, no exclamation marks, no manifesto register)
- [ ] Hedging language wraps the specific commitments (the doc is unhinged in
      content, not in prose register)
- [ ] _(booklet format)_ No `#pagebreak()` calls anywhere in the typst source
      (the template breaks after the contents)
- [ ] _(booklet format)_ Cover image set; inline figures placed within sections
      (between paragraphs), not at section boundaries with forced breaks
- [ ] _(booklet format)_ Back cover (`#slop-back-cover()` with the preset's
      config) is the last call in the file
- [ ] _(booklet format)_ **Page count is even** and within the preset's declared
      range (`pdfinfo … | grep Pages`)
- [ ] _(poster format)_ Single page (`pdfinfo` shows 1 page), in the orientation
      the preset rolled; no cover, contents, back cover, or manual page breaks;
      figures stay within their column (the research-poster preset uses its own
      `chartfig` helper, not `slop-inline-figure`)

## When something goes wrong

- **typst compile fails**: read the error. Most failures are missing image /
  chart files (regenerate via styled-image-gen or the preset's chart workflow)
  or a stale package symlink (`@local/slop-university-brand:0.1.0` should point
  at `brand/slop-university-brand/0.1.0` in this repo;
  `@local/university-typst-template:0.1.0` at the core package in the
  `anu-typst-template` repo's `packages/` dir).
- **Voice cracks**: the document drops out of the preset's register ---
  exclamation marks, activist verbs, first-person passion, no hedging on the
  wrapped claims. Regenerate. The hedge wraps the unhinged commitment; if the
  wrapper goes too, the joke dies.
- **Figures isolated on near-empty pages** _(booklet format)_: there are stray
  `#pagebreak()` calls in the typst. Booklets carry none at all; remove any you
  find.
- **Odd page count after first compile** _(booklet format)_: expected --- this
  is what the parity-fix step is for. Follow the preset's spare-inline path;
  small content tweaks are an acceptable fallback if the figure gets absorbed by
  existing slack. _(poster format)_ the target is a single page --- see the
  preset's one-page fit step.

Preset-specific failure modes live in each preset's blueprint.

## What this skill is not

- Not a content engine for arbitrary source material. For faithful typesetting
  of an existing URL or document, use `../from-source/SKILL.md` instead.
- Not the place to define a preset's content rules --- those belong in the
  preset's blueprint file. This skill is workflow only.
