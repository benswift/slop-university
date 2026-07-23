# slop-university

The document press of Slop University --- a fictional institution with a crest,
a gold-and-black identity, a small roster of researchers who do not exist, and
one real output: glossy, plausible scholarship. Strategic plans, impact reports,
research posters, in the full dress of a real university, none of it true and
all of it, by the only measures the sector actually counts, research.

**The satirical path:** named presets generate complete institutional documents
--- a "Slop University Strategic Plan 2026-2031", a five-year school impact
report, a chart-heavy A3 research poster --- typeset into print-ready PDFs in
the Slop University identity, authored by researchers from the persistent
fictional roster in `canon/`.

The genre is an LLM-shaped object: vague nouns, bridging verbs, transformations
between adjacent abstractions, language designed to commit to nothing in
particular. Claude produces one indistinguishably from a consulting firm because
the genre was already optimised against meaning. Pointing that out, in glossy
A4, is the project.

**The faithful path:** typeset any real source (URL, Word doc, ODT, markdown)
into the same layout machinery, prose preserved verbatim. The content is the
source's, not ours.

## The name

Slop University's name announces the joke. Its branding --- lockup, palette, the
two-ink illustration style of every image it publishes --- is drawn from scratch
rather than borrowed from anyone real, which is the difference between a
critique and a fraud. The institution is fictional by construction: no real
university's marks, no real person's name or face, anywhere in its outputs.

The faithful path borrows the same press for honest work: feed it a real
document and it comes back typeset, prose untouched. Set the two side by side
and they read alike --- once an institutional identity has been pressed over the
content, invented or real, the page looks equally like something an institution
issued.[^1]

[^1]:
    Previously named _imprint_ (the mark left when one surface is pressed into
    another), and before that for the _this-X-does-not-exist_ family of
    generative toys. Each name fit a narrower version of the project than the
    one that grew.

## How it works

Two slash commands:

- `/from-preset <preset-name> <steering>` --- single Claude invocation steered
  by a high-level prompt (e.g.
  `/from-preset strategy lean into sovereign capability`), generates a complete
  satirical typst document from a named preset. The prompt is the document's
  topic; the institutional voice (vague nouns, bridging verbs, hedging at the
  edges) is the only floor --- so however unhinged the content gets, it still
  reads as a recognisably institutional document. Current presets: `strategy`
  and `impact-report` (multi-page booklets), `brochure` (a glossy marketing
  booklet), `research-poster` (a single-page, screen-format, chart-heavy
  poster), `marketing-poster` (a display ad for the signage screens), and
  `paper` (an A4 two-column research paper whose bibliography is real, verified
  literature). New presets land by dropping a file in
  `skills/from-preset/presets/`.

- `/from-source <source>` --- ingest a URL or local document and typeset it
  through the same layout core, faithfully. No rewriting; the source's voice,
  prose, and structure pass through verbatim. Small editorial calls (heading
  levels when ambiguous, lockup choice, cover-image theme) are allowed and
  surfaced in the run's text output.

Styling comes from the `university-typst-template` layout core through a brand
package (`slop-university-brand` for the preset path; `anu-typst-template`, a
private package, for the faithful path). Imagery is generated in the two-ink
house style documented in `skills/_shared/visual-style.md`; charts are native
typst (gribouille) in the brand palette. The fictional people and org units live
in `canon/`. Output: a print-ready PDF.

The orchestrator workflows and per-preset blueprints are spelled out in
[skills/from-preset/SKILL.md](skills/from-preset/SKILL.md),
[skills/from-source/SKILL.md](skills/from-source/SKILL.md), and the preset files
under `skills/from-preset/presets/`. Voice doctrine for the satirical path is in
[skills/from-preset/genre.md](skills/from-preset/genre.md); shared visual
doctrine lives in `skills/_shared/`.

## Running

Satirical:

```sh
claude --dangerously-skip-permissions --effort max -p "/from-preset strategy <steering prompt>"
```

Faithful:

```sh
claude --dangerously-skip-permissions --effort max -p "/from-source <URL or path>"
```

Each command writes a typst file to `output/` and the final PDF to
`output/pdf/<preset>/` (e.g. `output/pdf/research-poster/`). Outputs are
gitignored.

## License

[MIT](LICENSE).
