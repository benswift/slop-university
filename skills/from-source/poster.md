---
name: from-source-poster
description:
  Poster format for the faithful from-source path --- lay real source material
  out as a genuine ANU A0 conference poster. Extractive rather than generative
  --- every line on the poster appears verbatim in the source. Loaded by
  `SKILL.md` when the run is invoked with `--poster`.
---

# from-source: poster format

Typeset real source material --- a paper, an abstract, a report --- as an ANU A0
conference poster (841 x 1189mm portrait). The booklet format's doctrine carries
over unchanged: the source's prose goes through verbatim, and nothing is
invented. What changes is that a poster cannot hold a whole paper, so this
format is allowed to **select**.

## Fidelity under compression

A poster holds perhaps 700 words. The source usually holds far more, so
selection is unavoidable and is the one thing this format adds:

- **Extract, never rewrite.** Every sentence on the poster must appear verbatim
  in the source. Dropping a sentence is allowed; dropping a clause mid-sentence
  is allowed only if the remainder is still the source's own sentence and still
  means what it meant. Rewriting, paraphrasing, stitching two sentences into
  one, and "tightening" are all out.
- **Keep the source's headings.** Don't rename an "Introduction" to "Background"
  to fit the poster genre, and don't invent a heading the source doesn't have.
  Select and reorder headings; leave their words alone. (Adjusting heading
  _level_ is the same small editorial call the booklet format already allows.)
- **Omit, don't fabricate.** If the source carries no Methods section, the
  poster has no Methods section. A poster with four sections faithfully
  extracted beats one with seven, three of them invented.
- **Report the cut.** The run's text output must state what was left out ---
  which sections were dropped entirely, and roughly what proportion of the
  source's prose made it on. The user is the one who knows whether the omitted
  material was load-bearing.

If the source is already poster-shaped (a structured abstract, a one-page
summary), selection may be close to a no-op. Say so rather than padding.

## No charts, no invented figures

This is the sharpest difference from the satirical `research-poster` preset,
which fabricates its charts freely. **The faithful path fabricates nothing**, so
by default a from-source poster is prose plus one hero image:

- The source's own embedded figures are dropped, exactly as in the booklet
  format. Flag this in the run's text output --- on a research poster, missing
  figures are usually a bigger loss than missing prose, and the user may want to
  supply them.
- If the user supplies figure images or chart data explicitly, use them: that is
  the user's material, not invention. Charts built from user-supplied data
  follow `../_shared/chart-workflow.md`, with the poster-scale theme below.
- Never reconstruct a chart by reading values off a figure in the source, and
  never illustrate a claim with a plausible-looking plot.

A text-only poster with generous white space is the correct output when the
source brings no usable figures. Don't fill the gap.

## Acknowledgement of Country

**The poster format carries no Acknowledgement of Country.** The booklet
format's AoC is a full page of fixed, verbatim institutional text, and
`../_shared/typst-layout.md` forbids abbreviating or paraphrasing it; a
single-page poster has nowhere to put it and no licence to shorten it.

Omitting it is a deliberate call, not an oversight, so **say so in the run's
text output**. If the user's context requires an acknowledgement on the poster,
they supply the approved wording and it goes in the footer furniture verbatim.
Never draft that wording.

## Doc identity

| Field              | Value                                                                                    |
| ------------------ | ---------------------------------------------------------------------------------------- |
| Format             | `poster` --- one A0 page; no cover, contents, AoC or back cover                          |
| Paper              | `page-settings: (width: 841mm, height: 1189mm)`                                          |
| Cover title        | The source's title verbatim                                                              |
| Subtitle           | The source's subtitle if present, else omitted                                           |
| Authors            | The source's own author line, verbatim; omitted if the source has none                   |
| Lockup             | Same editorial call as the booklet format: `anu-socy` for School-of-Cybernetics material |
| Masthead           | Overlaid white on the hero band via `anu-overlay-masthead` (auto masthead hidden)        |
| Filename prefix    | `source-poster`                                                                          |
| PDF metadata title | The source's title verbatim; title only, `date: none`                                    |
| Page count         | Exactly 1 --- no parity rule applies                                                     |

## The worked skeleton

**Do not write the typst from scratch.** The ANU template ships a complete,
compiling A0 poster; read it and adapt it to the source's sections:

```
~/.local/share/typst/packages/local/anu-typst-template/0.3.0/examples/poster.typ
```

Its README section (`…/0.3.0/README.md` › "Posters") carries the reasoning. The
parts that matter and are easy to get wrong:

- **The hero band is reserved in the top margin.** `margin.top` is the band
  height plus the gap beneath it; the image is `place`d flush to the page edge
  with negative `dx`/`dy` cancelling the margins.
- **Chart type must be sized explicitly.** gribouille pins its base text at an
  absolute 9pt, so chart labels ignore the document's body size and an
  unmodified chart is illegible at A0. Build the theme once ---
  `chart-theme(anu-brand, size: 19pt)` --- and pass it to each chart.
- **Restyle headings with the `it => …` show-rule form.** A bare `set text(...)`
  as the show body loses to the size the template's own heading rule sets. Keep
  `==` headings so the structure survives into the PDF tag tree.
- **Scrims are constant-alpha fills, never gradients** --- see
  `../_shared/typst-layout.md` › "PDF transparency".
- **Three columns, `rows: 1fr`**, with a `height: 1fr` trailing block in the
  short columns and `#v(1fr)` above the last column's footer, so all three
  columns bottom out level.

Body type sits at 28pt and headings at 34pt in the worked example. Treat 24pt as
the floor: below that the poster stops being readable at poster distance, and
the fix for overset content is to cut, not to shrink.

## Imagery

One hero image, per `../_shared/image-workflow.md` and the booklet format's
rules (evoke the subject, don't depict it; no inline imagery invented):

- Image folder: `output/source-poster-<slug>-<seed>-images/`
- Prompt count: 1 (`feature.jpg`), referenced from the typst root-relative as
  `/output/source-poster-<slug>-<seed>-images/feature.jpg` and compiled with
  `--root .` (step 8). The worked example uses a package-relative path because
  it lives inside the package --- don't copy that part of it.
- Aspect: **16:9 wide** --- it full-bleeds the top band, which is much wider
  than it is tall.
- The band's lower portion carries white title type, so the darkening under it
  is a constant-alpha rect in the typst (as in the worked example) or baked into
  the JPEG at prep. Never a typst alpha gradient.
- **The band's top-left must be dark too.** The white lockup is overlaid there,
  outside the scrim, so a hero whose top-left corner is bright sky or pale
  render makes the masthead disappear. Check the render rather than assuming; if
  the image won't cooperate, pick a different one or extend the scrim to the
  full band height.

## Workflow deltas

Run `SKILL.md`'s steps 1-4 unchanged (parse, ingest, derive identity, editorial
calls), then:

5. **Select the poster's content** before writing any typst. List the source's
   sections, mark which survive, and extract the verbatim sentences for each.
   Keep the running word count near 700. This is the step that decides whether
   the poster works; do it explicitly rather than while writing.
6. **Write `output/source-poster-<slug>-<seed>.typ`**, adapting the worked
   skeleton. No `#outline()`, no AoC, no `#anu-back-cover()`, no `#pagebreak()`
   anywhere.
7. **Generate the hero image** (above).
8. **Compile and fit-check.** Note `--root .`: the hero image is referenced
   root-relative, and without it typst resolves that path against the `.typ`
   file's own directory and fails with "file not found".
   ```sh
   typst compile --root . output/source-poster-<slug>-<seed>.typ \
     output/pdf/from-source/source-poster-<slug>-<seed>.pdf
   pdfinfo output/pdf/from-source/source-poster-<slug>-<seed>.pdf | grep Pages
   ```
   `Pages: 1` is the pass condition. If it reports 2, the content overset: **cut
   extracted material**, lowest-priority first, and recompile. Do not shrink the
   body below 24pt, and do not tighten leading to buy space. Underfill is the
   opposite failure and is fixed the same way --- by restoring material you cut,
   never by inventing any.
9. **Stop.** Same as the booklet format: outputs are local and gitignored.

## Pre-ship checklist

- [ ] Every sentence on the poster appears verbatim in the source
- [ ] No heading renamed; no section invented
- [ ] The run's text output states what was cut and roughly how much of the
      source made it on
- [ ] No fabricated charts or figures; if the source had embedded imagery, the
      run's output flags that it was dropped
- [ ] The run's output states that the poster carries no Acknowledgement of
      Country, and why
- [ ] PDF metadata title is the source's title verbatim, no author/keywords/date
- [ ] `pdfinfo` reports `Pages: 1` and A0 page size
- [ ] Body type at 24pt or above; chart theme built with an explicit `size:`
- [ ] No `#pagebreak()`, no `#outline()`, no back cover in the file
- [ ] Compiles with no warnings
