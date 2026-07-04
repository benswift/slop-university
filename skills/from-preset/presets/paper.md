---
name: paper
description:
  Slop University research paper --- an A4 two-column conference-style paper
  describing a plausible-but-fake research project, authored by roster
  researchers, with fabricated results charts and a REAL, verified bibliography
  (every entry resolves via DOI or arXiv). Paper format (no cover, contents, or
  back cover; multi-page, no parity requirement).
---

# Paper preset

Produce one Slop University research paper from a single steering prompt. The
output should pass for a real short conference paper --- two columns, title
block and abstract spanning both, numbered citations resolving to a references
section --- academically straight on a close read, with the joke living entirely
in the fictional project it reports.

The sharpest detail: **the bibliography is real.** The fake paper cites only
genuine literature, every entry verified to resolve --- borrowed legitimacy via
the citation graph. (This is also why the site's `robots.txt` blocks indexing of
output PDFs: the borrowing must never flow back into citation databases.)

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `../genre.md` for the steering philosophy, the voice floor, and the roster
  rule
- `../../_shared/chart-workflow.md` for the gribouille chart pipeline and brand
  styling
- `../../_shared/image-workflow.md` + `../../_shared/visual-style.md` for the
  (at most one) generated image
- `../../_shared/output-naming.md` for slug, seed, output paths
- `../../_shared/typst-layout.md` for the template import and PDF-metadata rules
  --- **not** the booklet cover / back-cover / parity sections
- `canon/roster.yml` and `canon/schools.md` for authors and affiliations

## Doc identity

| Field                      | Value                                                                                      |
| -------------------------- | ------------------------------------------------------------------------------------------ |
| Canonical name             | Slop University research paper                                                             |
| Format                     | **paper** (A4 portrait, two-column body, title block spanning both)                        |
| Visible title              | the fabricated project's title --- **steering-derived** (a paper's title _is_ its content) |
| Authors                    | 2-4 from `canon/roster.yml`, with school affiliations                                      |
| Theme                      | `light`                                                                                    |
| Filename prefix            | `slop-paper`                                                                               |
| PDF subfolder (`<group>`)  | `paper`                                                                                    |
| Page count                 | 4-8 (no parity requirement --- papers aren't saddle-stitched)                              |
| Register                   | methods-section deadpan (see "Voice")                                                      |
| PDF metadata title formula | `This Slop University Paper Does Not Exist: <steering verbatim>`                           |

PDF metadata title is the deliberate satirical tell (not visible on rendered
pages). No other metadata fields populated. The DOI (`10.5555/slop.<seed>`, when
the run is a /publish run) renders in the title block --- papers are the one
genre where an inline DOI is expected furniture. For a manual (non-publish) run,
omit the DOI line.

## Inputs

One free-text **steering prompt** describing a subversive fictional research
project. Same register as the research-poster examples ("a reinforcement-
learning model for optimal tea-room biscuit redistribution"). The prompt is the
project; everything --- title, abstract, method, results, ablations --- bends to
it in unbroken paper register.

## The genre's structural skeleton

| Section                | Length          | Notes                                                                                   |
| ---------------------- | --------------- | --------------------------------------------------------------------------------------- |
| Title block + abstract | spans both cols | Title, authors + affiliations (+ DOI on publish runs), 150-220 word abstract            |
| Introduction           | ~350 words      | The gap, framed seriously; contributions as a 3-bullet list (each hedged)               |
| Related work           | ~250 words      | Where most citations live; every claim about a cited work must be true of that work     |
| Method                 | ~400 words      | Deadpan procedural; one display equation and/or a short code listing earn the costume   |
| Experiments / Results  | ~450 words      | 2-4 gribouille charts + optionally a table; baselines, an ablation that changes nothing |
| Discussion             | ~200 words      | Hedged interpretation; "we observe consistent improvements in most settings"            |
| Limitations            | ~120 words      | Concedes nothing: every "limitation" quietly reasserts a strength                       |
| Conclusion             | ~120 words      | One-paragraph close; "future work" fragment                                             |
| References             | 15-25 entries   | **Real, verified literature** (see "Bibliography"); `bibliography(..., style: "ieee")`  |

Section names may vary in the usual reservoir spirit (e.g. "Background" for
Related work, "Evaluation" for Experiments); "Abstract", "Limitations", and
"References" are load-bearing genre conventions --- keep them.

## Authors (roster)

Roll 2-4 researchers from `canon/roster.yml` --- a plausible rank mix (a
professor or associate professor plus fellows reads right; four postdocs
doesn't). Affiliations are their canonical schools + "Slop University".
Superscript affiliation markers only when the authors span two schools. Never
anyone off-roster; never a real person. Author order: lead author is the one
whose school the project best fits.

## Bibliography --- real references, verified (hard requirement)

Per-run `references.bib` harvested from genuine literature:

1. **Search** the fabricated topic's real adjacent fields (web search: the
   steering topic's serious neighbours --- e.g. biscuit redistribution →
   multi-agent resource allocation, fair division, workplace commensality
   studies). Collect 15-25 candidate entries: journal/conference papers and
   arXiv preprints, mixed venues and years.
2. **Verify every entry** before it enters the bib --- each must pass one of:
   - **DOI check**:
     `curl -sI -o /dev/null -w '%{http_code}' https://doi.org/<doi>` returns
     2xx/3xx. Drop entries that 404.
   - **arXiv check** (much of the ML literature has no DOI):
     `curl -s 'https://export.arxiv.org/api/query?id_list=<id>'` returns an
     entry whose title matches. Drop mismatches.
3. **Copy fields accurately**: real authors, real title, real venue, real year,
   the verified `doi = {...}` or `eprint`/`archivePrefix` fields. The entries
   are the one place real names appear --- as authors of their own real work,
   correctly attributed. Never fabricate an entry, never pad with an unverified
   one; 15 verified beats 25 mixed.
4. Write `output/slop-paper-<slug>-<seed>.bib` and load it with
   `#bibliography("/output/slop-paper-<slug>-<seed>.bib", title: "References",
   style: "ieee")`. (The whole `output/` tree is gitignored, the per-run bib
   included.)

   **arXiv entry form**: typst's BibTeX conversion drops `eprint` /
   `archivePrefix` (the entry renders as a bare title + year), and a `url`
   field suppresses the year. Write arXiv entries as
   `@article{key, author = {...}, title = {...}, year = {...},
   journal = {arXiv preprint arXiv:<id>}}`.

**Citation honesty rule**: prose claims about a cited work must be true of that
work ("resource-allocation mechanisms have been studied extensively @real2019"
--- fine; "@real2019 first proposed biscuit telemetry" --- never). The fictional
project borrows the field's legitimacy; it does not misrepresent real
researchers' actual claims. Cite generously in Introduction and Related work;
2-4 callbacks in Method/Results keep the costume on.

## Figures and tables

- **2-4 gribouille charts** in the results-figure register: a baselines
  comparison (line or grouped-bar), an ablation (grouped-bar or boxplot --- the
  ablation that changes nothing: bars statistically indistinguishable, reported
  straight), error bars where the type supports them. Charts are authored per
  `../../_shared/chart-workflow.md` into
  `output/slop-paper-<slug>-<seed>-charts/` and embedded with
  `slop-inline-figure` (single-column) --- captions state a falsifiable claim
  with a figure in it.
- **Tables welcome** (hyperparameters, dataset statistics) --- typst-native,
  small, 8-9pt.
- **At most one generated image** (apparatus/setting, house style per
  `visual-style.md`, `references/slop-style/` refs) --- papers are chart-shaped,
  not photo-shaped. Most runs carry none.

## Voice (methods-section deadpan)

The paper register is the project's fourth voice (strategy = future-tense;
impact report = past-tense reflective; poster = telegraphic academic-present).
It defers to `../genre.md` for the floor and specialises:

- **Hedged contributions.** "We observe consistent improvements in most
  settings"; "our results suggest the approach may generalise". The
  contributions list makes three claims, each pre-softened.
- **An ablation that changes nothing**, reported with full apparatus: "removing
  the commensality prior degrades mean utility by 0.3% (n.s.); we retain it for
  completeness."
- **A limitations section that concedes nothing.** Every limitation is a
  strength wearing a hedge: "our evaluation is limited to eight tea rooms,
  though the consistency across all eight suggests broader applicability."
- **Past-tense method, present-tense findings**, passive voice tolerated in
  Method only. No enthusiasm anywhere; the deadpan is the joke.
- Plausible bands as per the poster preset (n, accuracies, effect sizes); "(p <
  0.05)" sparingly.

Never signals satire on the page: no winks, no absurd venue names in _this_
doc's own header (the venue is simply absent --- a preprint), no exclamation
marks.

## Typst structure

A4 portrait, two-column body. The `slop()` show rule doesn't do page columns
(its `columns:` option is a header grid) --- set columns in the document, and
span the title block + abstract across both with
`place(top + center, scope: "parent", float: true)`:

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-colors, slop-inline-figure
// one import per chart:
//   #import "/output/slop-paper-<slug>-<seed>-charts/chart-1.typ": chart as chart-1

#set document(
  title: "This Slop University Paper Does Not Exist: <steering prompt verbatim>",
)

#show: doc => slop(
  title: "",                    // title block is manual --- it must span both columns
  paper: "a4",
  config: (theme: "light", hide: ("title-block",)),
  doc,
)

#set page(columns: 2)
#set text(size: 9.5pt)
#set par(justify: true)

// Level-1 headings at paper scale: the template's booklet-display rule (26pt
// gold) is a function-style show rule, so a show-set won't override it ---
// replace it outright.
#show heading.where(level: 1): it => block(
  above: 1.4em,
  below: 0.7em,
  text(size: 13pt, weight: "bold", fill: slop-colors.primary, it.body),
)

// ── Title block + abstract, spanning both columns ──
#place(top + center, scope: "parent", float: true, clearance: 1.6em)[
  // The template's first-page header spacer shifts flowed content but NOT
  // top-placed parent-scope floats --- without this the title collides with
  // the lockup.
  #v(2.4cm)
  #set align(center)
  #text(size: 17pt, weight: "medium")[<Paper title --- steering-derived>]
  #v(0.5em)
  #text(size: 10.5pt)[<Author A>, <Author B>, <Author C>]
  #v(0.15em)
  #text(size: 9pt, fill: slop-colors.grey-4)[<Lead school>, Slop University]
  #v(0.15em)
  #text(size: 9pt, fill: slop-colors.grey-4)[doi:10.5555/slop.<seed>]  // publish runs only
  #v(0.9em)
  #block(width: 82%)[
    #set align(left)
    #set text(size: 9pt)
    #set par(justify: true)
    *Abstract.* <150-220 words, hedged throughout>
  ]
]

= Introduction
<...body flows in two columns; #cite entries as @key...>

= Related work
<...>

= Method
<...display equation and/or short code listing...>

= Results
#slop-inline-figure(
  chart-1,
  caption: [<falsifiable claim with a figure in it>],
)
<...>

= Discussion
<...>

= Limitations
<...>

= Conclusion
<...>

#bibliography("/output/slop-paper-<slug>-<seed>.bib", title: "References", style: "ieee")
```

(`title: "References"` matters --- the default heading is "Bibliography", and
"References" is the load-bearing genre convention.)

Structural reference: the ANU layer's worked example at
`~/projects/anu-typst-template/packages/anu-typst-template/0.3.0/examples/paper.typ`
(single-column, but demonstrates `bibliography()` + `references.bib`, subpar
grouped figures, display equations, code listings, and a gribouille chart import
--- copy those moves, not its import block). If the two-column pattern
stabilises after a few runs, consider promoting a `paper` mode into the template
package --- not before.

### Gotchas

- **Charts must fit a column.** `slop-inline-figure` keeps figures in-column;
  keep chart aspect wide-short (`height` ~0.55 of width at column scale) and
  text sizes legible at ~8.5cm column width. A chart that needs full page width
  can be `place(scope: "parent", float: true, ...)`d like the title block --- at
  most one.
- **Two-column + floats**: give every float a caption and reference it in prose
  (@fig:...); typst places floats top/bottom of columns.
- **Don't fight underfull final columns** --- papers end where they end; no
  fill-probe, no parity fix. If the last page is a lone references column,
  tighten prose rather than padding.
- Compile per the shared workflow:
  `typst compile --root . output/slop-paper-<slug>-<seed>.typ output/pdf/paper/slop-paper-<slug>-<seed>.pdf`,
  then `pdfinfo` --- expect A4 portrait, 4-8 pages.

## Pre-ship checklist (preset-specific)

- [ ] A4 portrait, two-column body; title block + abstract span both columns;
      4-8 pages
- [ ] 2-4 authors, all from `canon/roster.yml`, affiliations from
      `canon/schools.md`; no other person named outside the References
- [ ] 15+ references, **every entry verified** (DOI resolves or arXiv ID returns
      a matching title); fields copied accurately; loaded via
      `bibliography(..., style: "ieee")` and actually cited in prose
- [ ] Citation honesty: every prose claim about a cited work is true of that
      work
- [ ] 2+ gribouille charts in brand styling (incl. the do-nothing ablation);
      captions carry falsifiable claims; at most one generated image
- [ ] Voice holds: hedged contributions, deadpan method, limitations that
      concede nothing, no exclamation marks, no satire signals on the page
- [ ] PDF metadata title matches the formula; no other metadata populated
- [ ] Output at `output/pdf/paper/slop-paper-<slug>-<seed>.pdf`

## Common failure modes (preset-specific)

- **An unverified or fabricated reference slips in**: hard failure --- the
  entire point is that the bibliography is real. Re-verify the full list; drop
  anything that doesn't resolve.
- **Prose misattributes a claim to a real cited work**: rewrite the sentence to
  a claim that is true of that work (or generalise to the field).
- **Reads like a poster**: prose too telegraphic. A paper carries full sentences
  and connective tissue; the compression lives in the hedges, not in fragments.
- **Reads bland**: the title, abstract, and chart captions aren't visibly driven
  by the prompt. Crank the commitment shapes (a too-clean headline number, a
  pre-registered-protocol methods detail) while keeping the paper register
  intact.
- **Column overflow / floats stacking at one column**: shorten the chart plots,
  check every float has `float: true` placement via `slop-inline-figure`, and
  keep the single full-width float (if any) early in Results.

## What this preset is not

- Not a booklet and not a poster: no cover, contents, back cover, parity, or
  one-page fit; its own two-column mechanics live here.
- Not a venue submission. It's a preprint-shaped object; it never claims
  acceptance anywhere.
- Not a place for new chart or genre conventions --- those belong in
  `../../_shared/chart-workflow.md` / `../genre.md`.
