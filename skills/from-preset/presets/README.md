# Adding a new preset

Authoring guide only --- generation runs never need this file. The directory
`presets/` is the registry; drop a file in and it's available. The new file must
be a self-contained markdown blueprint declaring (at minimum):

- Frontmatter with `name` and `description`
- A "Doc identity" section: canonical name, **format** (`booklet`, `poster`, or
  `paper`), cover/visible title, period, cover lockup, filename prefix,
  page-count range (or "single page" for posters), register, PDF metadata title
  formula
- A "Structural skeleton" table: section list with lengths and notes
- A "Per-run variation rolls" section: any reservoirs, structural counts,
  optional-section rules, personas the preset uses
- An "Imagery (preset specifics)" section: image-folder path, prompt count and
  shape, any thematic constraints on the prompts
- A "Style references" section: typst examples, genre PDFs, template helpers to
  read before generating
- A "Typst structure" section: the skeleton code block plus any preset-specific
  helpers (highlight cards, inline figures, charts, pull-quotes)
- A "Pre-ship checklist (preset-specific)" section: items beyond the generic
  checklist in the orchestrator (`../SKILL.md`)
- A "Common failure modes (preset-specific)" section: bland-output signals,
  terminology slips, etc.

Optional sections to add if the preset needs them:

- "Terminology" --- if the preset relies on a specific institutional vocabulary
  (the impact-report preset has a large one)
- "Voice-preserving commitment shapes" --- doc-specific elaborations on the
  general menu in `../genre.md`
- "Chart workflow" --- a short section pointing at
  `../../_shared/chart-workflow.md` if the preset generates charts; the
  orchestrator's chart step keys off this declaration, so no list elsewhere
  needs updating
- Any other section the preset needs that doesn't fit elsewhere

Existing presets are the worked examples; copy the closest and edit.
`strategy.md` and `impact-report.md` are `booklet`-format (the latter also a
worked chart example); `research-poster.md` is the dense `poster`-format worked
example and `marketing-poster.md` the sparse one (all-placed content, no flowed
body); `paper.md` is the `paper`-format worked example (charts plus a verified
real bibliography). A non-booklet preset overrides the booklet-shaped workflow
steps (4, 6, 7) and checklist items in its own blueprint --- see how
`research-poster.md` handles the single-page layout, the omitted back cover, and
the one-page fit check.
