---
name: paper
description:
  Slop University research paper --- an A4 scholarly paper reporting a fictional
  piece of research in whatever form its tradition publishes, authored by roster
  researchers, with a REAL, verified bibliography (every entry resolves via DOI
  or arXiv). Paper format (no cover, contents, or back cover; multi-page, no
  parity requirement).
---

# Paper preset

Produce one Slop University paper. It should pass, on a close read, for a real
paper in its field: the form, the apparatus and the prose are what a specialist
would expect, and the work it reports is invented.

**The bibliography is real.** The paper cites genuine literature, every entry
verified to resolve --- borrowed legitimacy via the citation graph. (This is
also why the site's `robots.txt` blocks indexing of output PDFs: the borrowing
must never flow back into citation databases.)

Loaded by `skills/from-preset/SKILL.md`. Defers to `../genre.md` (the brief and
its floors), `../../_shared/chart-workflow.md` (charts),
`../../_shared/image-workflow.md` + `../../_shared/visual-style.md` (generated
images), `../../_shared/output-naming.md` (slug, seed, paths) and
`../../_shared/typst-layout.md` (template import, PDF metadata, tables --- not
its booklet sections).

## Doc identity

| Field                      | Value                                                            |
| -------------------------- | ---------------------------------------------------------------- |
| Format                     | **paper** (A4 portrait)                                          |
| Visible title              | the paper's own title                                            |
| Authors                    | 1-4 from `canon/roster.yml`, with school affiliations            |
| Theme                      | `light`                                                          |
| Filename prefix            | `slop-paper`                                                     |
| PDF subfolder (`<group>`)  | `paper`                                                          |
| Page count                 | 4-8 (no parity requirement)                                      |
| PDF metadata title formula | `This Slop University Paper Does Not Exist: <steering verbatim>` |

The PDF metadata title is the one satirical tell and is not visible on the page.
No other metadata fields are populated. On a publish run the DOI
(`10.5555/slop.<seed>`) renders in the title block; on a manual run, omit it.

## Form follows the field

There is no fixed section map. An experimental paper has methods and results; a
proof has definitions, lemmas and a theorem; a close reading has an argument
that moves through its texts; a legal note has its authorities; an ethnography
has its scenes. Give the paper the sections, apparatus and length its tradition
would, and name them as that tradition does. Only the abstract (where the field
uses one) and the reference list are constant.

- **Columns.** Two-column is the default and what the skeleton below sets up.
  Fields that publish single-column (most of the humanities, law, mathematics)
  may drop `#set page(columns: 2)` and set the body at 10.5pt.
- **Citation style.** Pass the field's own to `bibliography(style: ...)`:
  `"ieee"`, `"apa"`, `"chicago-author-date"`, `"chicago-notes"` (footnotes),
  `"mla"` or `"harvard-cite-them-right"`.
- **Figures.** Whatever the field would carry, and nothing it would not:
  gribouille charts (per `../../_shared/chart-workflow.md`, into
  `output/slop-paper-<slug>-<seed>-charts/`, embedded with
  `slop-inline-figure`), typst-native tables (sizing in
  `../../_shared/typst-layout.md` › "Tables"), display equations, theorem
  statements, code listings, block quotations, and at most two generated images
  in the house style. A paper with no figures at all is fine.

## Authors

The lead author and school arrive on the invocation line when the wrapper drew
them; otherwise choose a lead from `canon/roster.yml`. Add co-authors only if
the field would (a sole-authored essay is normal in many). Affiliations are the
authors' canonical schools plus "Slop University".

The title block carries the authors' addresses in the brace-group form ---
`{verity.marris, casimir.beng}@slop.university` --- built from each author's
`email` field in the roster; a sole author's address is printed plainly, without
braces. Never invent an address in any other shape.

## Bibliography --- real references, verified (hard requirement)

Per-run `references.bib` harvested from genuine literature:

1. **Search** the fabricated topic's real adjacent fields (web search: the
   steering topic's serious neighbours --- e.g. biscuit redistribution →
   multi-agent resource allocation, fair division, workplace commensality
   studies). Collect the candidate entries the field would carry (ten at the
   least): journal/conference papers and arXiv preprints, mixed venues and
   years.
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
   one; ten verified beats twenty mixed.

   **Nobiliary particles**: hayagriva reads an unbraced `von`, `van`, `de` or
   `di` as a middle name and drops it, printing Heinz von Foerster as
   "Foerster". Brace the whole surname --- `author = {{von Foerster}, Heinz}`,
   `author = {{van Niekerk}, Johan}` --- and check the rendered reference list,
   because this misnames a real person and the bib file looks right.

4. Write `output/slop-paper-<slug>-<seed>.bib` and load it with
   `#bibliography("/output/slop-paper-<slug>-<seed>.bib", title: "References", style: "ieee")`.
   (The whole `output/` tree is gitignored, the per-run bib included.)

   **arXiv entry form**: typst's BibTeX conversion drops `eprint` /
   `archivePrefix` (the entry renders as a bare title + year), and a `url` field
   suppresses the year. Write arXiv entries as
   `@article{key, author = {...}, title = {...}, year = {...}, journal = {arXiv preprint arXiv:<id>}}`.

**Citation honesty rule**: prose claims about a cited work must be true of that
work ("resource-allocation mechanisms have been studied extensively
@real2019" --- fine; "@real2019 first proposed biscuit telemetry" --- never).
The fictional project borrows the field's legitimacy; it does not misrepresent
real researchers' actual claims. Cite generously in Introduction and Related
work; 2-4 callbacks in Method/Results keep the costume on.

### Citing the University's own outputs

Cite **at least two** prior Slop University outputs, as a scholar cites
colleagues down the corridor: for a method borrowed, a setting shared, a finding
this paper extends or declines to. The citation graph is the University's only
bibliometric and is built one reference list at a time. Find them with
`ops/topic-neighbours.py "<this paper's topic>"` (nearest prior topics) and
`ops/extract-citations.py --suggest` (ranked by what a citation would do for a
colleague's h-index); cite the ones the paper can honestly be read against, and
never pad with one it cannot.

- **Source of truth**: `website/src/content/outputs/*.yml`. Copy `title` (append
  the `subtitle` after a colon), `authors` verbatim and in order, year from
  `date`, and `doi`. An entry that does not match its ledger record
  field-for-field is a fabricated reference.
- **Verify against the ledger**, not doi.org:
  `grep -l '10.5555/slop.<seed>' website/src/content/outputs/*.yml` must hit
  exactly the entry you copied from.
- **BibTeX shape**, under `"ieee"`:
  `@article{slop-<seed>, author = {...}, title = {...}, journal = {Slop University technical report}, year = {...}, doi = {10.5555/slop.<seed>}}`
  (typst's BibTeX conversion drops `@techreport`'s `institution`). Under the
  author-date and notes styles that shape prints "ahead of print"; use
  `@techreport{slop-<seed>, ..., type = {Slop University technical report}, doi = {...}}`
  there, and check how the entry renders.
- A prose claim about a cited output must be true of that entry's `summary`.

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
  #text(size: 17pt, weight: "medium")[<Paper title>]
  #v(0.5em)
  #text(size: 10.5pt)[<Author A>, <Author B>, <Author C>]
  #v(0.15em)
  #text(size: 9pt, fill: slop-colors.grey-4)[<Lead school>, Slop University]
  #v(0.15em)
  // roster emails, brace-grouped; a string, so the @ doesn't parse as a ref
  #text(size: 9pt, fill: slop-colors.grey-4)[#("{<lead>.<surname>, <coauthor>.<surname>}@slop.university")]
  #v(0.15em)
  #text(size: 9pt, fill: slop-colors.grey-4)[doi:10.5555/slop.<seed>]  // publish runs only
  #v(0.9em)
  #block(width: 82%)[
    #set align(left)
    #set text(size: 9pt)
    #set par(justify: true)
    *Abstract.* <150-220 words>
  ]
]

= <First section, named as the field would>
<...body flows in two columns; #cite entries as @key...>

// a figure, where the paper has one:
#slop-inline-figure(
  chart-1,
  caption: [<caption>],
)

= <...the sections this paper needs...>
<...>

#bibliography("/output/slop-paper-<slug>-<seed>.bib", title: "References", style: "ieee")
```

(Set `title:` to what the field calls its list --- "References", "Works cited",
"Bibliography". The default heading is "Bibliography".)

Structural reference: the ANU layer's worked example at
`~/projects/anu-typst-template/packages/anu-typst-template/0.3.0/examples/paper.typ`
(single-column, but demonstrates `bibliography()` + `references.bib`, subpar
grouped figures, display equations, code listings, and a gribouille chart
import --- copy those moves, not its import block). If the two-column pattern
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

- [ ] A4 portrait, 4-8 pages; the title block (and abstract, where present)
      spans the full width
- [ ] Authors all from `canon/roster.yml`, with roster emails in the brace-group
      form; no other person named outside the reference list
- [ ] **Every external reference verified** (DOI resolves or arXiv ID returns a
      matching title), fields copied accurately, each one cited in the prose
- [ ] Every claim about a cited work is true of that work
- [ ] At least two Slop University self-citations, each matching its ledger
      entry field-for-field and honestly related to the paper
- [ ] Charts in brand styling; every figure and table sits inside its column
- [ ] PDF metadata title matches the formula; no other metadata populated
- [ ] Output at `output/pdf/paper/slop-paper-<slug>-<seed>.pdf`

## Common failure modes (preset-specific)

- **An unverified or fabricated reference slips in**: hard failure. Re-verify
  the full list; drop anything that does not resolve.
- **Prose misattributes a claim to a real cited work**: rewrite the sentence to
  a claim that is true of that work, or generalise to the field.
- **Column overflow / floats stacking in one column**: shorten the chart plots,
  check every float goes through `slop-inline-figure`, and keep the single
  full-width float (if any) early.
