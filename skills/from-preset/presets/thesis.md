---
name: thesis
description:
  Slop University PhD thesis --- a 100-180 page A4 single-column monograph
  submitted for the degree by a newly fabricated doctoral candidate, with a real
  verified bibliography (60-100 entries) and a long engagement with the Slop
  University canon (30-60 prior outputs by DOI). Thesis format (title page,
  front matter, chapters as separate included files, appendices, references; no
  parity requirement, no dark variant). On-demand only; a run takes 3-4 hours
  and delegates chapters to subagents.
---

# Thesis preset

Produce one Slop University PhD thesis from a single steering prompt. The output
should pass for a real submitted thesis on an examiner's desk: a declaration, an
abstract, a contents page, numbered chapters that argue something, figures the
argument needs, appendices an examiner would ask for, and a reference list that
resolves. The joke lives entirely in the fictional programme of work it reports
--- never in a wink on the page.

**This blueprint states floors and a working method, not a section-by-section
skeleton.** The other presets are formulaic by design; this one is not. Within
the floors below, the shape of the thesis --- monograph or thesis-by-
compilation, how many chapters, what the studies are, where the figures go ---
is the run's own call, and the standard it is held to is whether it would
plausibly survive examination while remaining a Slop University output in the
true sense. A thesis that reads as a longer research paper with the same six
headings has failed the brief even if it passes every checklist item.

Loaded by `skills/from-preset/SKILL.md`. Defers to:

- `../genre.md` for the voice floor, the commission test, and the roster rule
- `../../_shared/chart-workflow.md`, `../../_shared/image-workflow.md` and
  `../../_shared/visual-style.md` for charts and imagery;
  `../../_shared/output-naming.md` for slug, seed and output paths
- `../../_shared/typst-layout.md` for the PDF-metadata rule --- **not** the
  booklet cover / back-cover / parity sections, and **not** its page-break
  discipline (the template breaks the pages a thesis needs)
- `canon/roster.yml`, `canon/schools.yml` and `canon/schools.md` for the
  candidate's school and supervisors
- `paper.md` for the verification procedures this preset reuses at larger scale
  --- restated here only where the thesis changes them

## Doc identity

| Field                      | Value                                                                                                                        |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Canonical name             | Slop University doctoral thesis                                                                                              |
| Format                     | **thesis** (A4 portrait, single column, book margins; front matter, main matter, appendices, back matter)                    |
| Visible title              | the thesis title --- **steering-derived** (a thesis's title _is_ its contribution); a subtitle is optional                   |
| Author                     | the candidate alone --- one new `canon/roster.yml` entry, admitted by the same run                                           |
| Supervisors                | two existing roster members of the candidate's school; named on the title page and in the acknowledgements, never as authors |
| Degree                     | Doctor of Philosophy                                                                                                         |
| Theme                      | `light` only --- no dark variant, `pdfDark: false`                                                                           |
| Filename prefix            | `slop-thesis`                                                                                                                |
| PDF subfolder (`<group>`)  | `thesis`                                                                                                                     |
| Page count                 | 100-180 (no parity requirement; no back cover)                                                                               |
| Word budget                | 35,000-60,000 words of body text                                                                                             |
| Register                   | examinable (see "Voice")                                                                                                     |
| PDF metadata title formula | `This Slop University Thesis Does Not Exist: <steering verbatim>`                                                            |

PDF metadata title is the deliberate satirical tell (not visible on rendered
pages). No other metadata fields populated. On a publish run the DOI
(`10.5555/slop.<seed>`) belongs in the outputs ledger entry, not on the title
page --- a submitted thesis carries no DOI.

## Inputs

One free-text **steering prompt** naming the fictional doctoral project, in the
register the other academic presets use. The prompt is the programme of work;
title, research questions, studies, instruments and findings all bend to it.

Everything else the run needs is drawn or fabricated:

- **Setting** (drawn from `canon/axes.yml`) --- one setting for the whole
  thesis. A thesis is a sustained engagement with one corner of ordinary life,
  so unlike a paper it does not wander: every study sits in the drawn setting.
- **School** (drawn) --- the candidate's school, from `canon/schools.yml`.
- **Two supervisors** (drawn) --- a primary and an associate, existing
  `canon/roster.yml` members, normally both of the candidate's school. Never
  three, never one; never the candidate's co-authors.
- **The candidate** --- fabricated in this run: name, roster id, email, title
  `Doctoral Candidate`, school, and a bio that is the backstory this thesis
  implies. The name-collision check in `canon/roster.yml`'s header applies in
  full. The candidate is the sole author of the thesis and of nothing else.

Nothing else is drawn. The finding-shapes in `canon/axes.yml` are a **menu** of
designs the corpus already uses, offered and not mandated --- a thesis may take
one shape per study, mix them, or use none of them if the argument wants
something else. The retired shapes in `canon/burnt-shapes.yml` are never the
primary design of the thesis, though a single subordinate study may use one
where the argument genuinely needs it.

### How the fiction appears on the page

- The title page (rendered by the template) carries the candidate, the degree
  sentence, the school, both supervisors, and the submission month and year; the
  declaration is signed with the candidate's name and that date.
- The acknowledgements thank both supervisors **by canon name** and canonical
  title, the school, and whatever else the fiction needs --- a fieldwork site, a
  technical officer's role (not a name), a scheme from `canon/grants.yml` where
  one fits. Family in generic terms only. **Never the Vice-Chancellor by name**;
  the office may be invoked. Satire here, if any, is in _what_ is thanked, never
  in the tone.
- The candidate's roster bio and the thesis agree on everything: school,
  supervisors, subject, and any background the bio claims. The bio is written
  from the finished thesis, not before it.

## Hard floors

Everything not on this list is the run's call.

1. **Front matter a real Australian thesis has**: title page, declaration,
   acknowledgements, abstract, contents. Add a list of figures and a list of
   tables when there are enough of either to warrant one (roughly ten or more);
   omit either list rather than printing a stub.
2. **Back matter**: references, and at least one appendix an examiner would
   expect --- the survey instrument, an interview schedule, the coding frame, an
   ethics approval summary, supplementary tables. Choose what the design
   actually needs; an appendix nothing in the body refers to is padding.
3. **A literature review that reviews the real adjacent field** --- 60-100
   verified external references, engaged with rather than listed (see
   "Bibliography").
4. **A sustained engagement with the Slop University programme** --- 30-60 prior
   outputs cited by their `10.5555/slop.<seed>` DOIs, each characterised in a
   sentence that is true of that entry's ledger `summary` (see "Citing the
   canon"). **A thesis with no canon in it is a failed run.**
5. **An original contribution stated up front and delivered.** State it in the
   abstract and the introduction; deliver it in the body; restate what was
   actually shown in the conclusion. It may be one or more empirical studies, a
   method, an instrument, a theory, or a defensible combination. Monograph or
   thesis-by-compilation --- the run chooses.
6. **The commission test at thesis scale.** A serious institution could not
   commission, publish, or adopt this programme of work and its central claims
   unchanged. At thesis length the test is specifically: what rule, process or
   measure does the institution now bind itself to on the strength of these
   findings? That consequence is central and high-salience --- it belongs in the
   abstract, the contribution statement, and the conclusion --- not a detachable
   joke in a caption.
7. **The picturable-object satire floor**, and **no visible satire signals**.
   The thesis is about something a reader can see --- an object, a queue, a
   form, a doorway, a roster --- and total institutional rigour applied to that
   ordinary thing is the satire. Nothing an examiner would strike out as
   unserious: no winks, no joke acronyms that announce themselves, no
   exclamation marks, no epigraph that comments on the joke.
8. **Charts, tables and figures where the argument needs them**, house workflow
   and visual style --- not to a quota, and not spaced evenly through the
   chapters to look busy.
9. **100-180 pages, 35,000-60,000 words, Australian English.**

## Working method (a 3-4 hour run)

This section replaces workflow steps 3-7 in `../SKILL.md`. The orchestrator
never drafts chapters itself; it decides everything a chapter needs to be
consistent with its neighbours, then dispatches.

### 1. Plan first, on disk

Before a single chapter is drafted, write
`output/slop-thesis-<slug>-<seed>/plan.md`. Every subagent reads it, so anything
two chapters must agree on lives here and nowhere else:

- the title and subtitle, the candidate, the school, both supervisors, the drawn
  setting, and the shape of the argument (monograph or compilation)
- the **thesis statement** in one sentence and the **contribution** in two or
  three, plus the **institutional consequence** the commission test turns on and
  which chapters build toward it
- the **chapter list**: number, title, one-line purpose, word target, and what
  each chapter must hand to the next
- the **fixed numbers**: sample sizes, sites, waves, dates, instrument names and
  their abbreviations, participant or site labels, the named levels of any
  framework, every headline figure. A thesis that reports n = 214 in chapter 4
  and n = 217 in chapter 6 fails examination; this list is the only defence
- the **reference list**: every bib key, with a one-line note on what each work
  is for and which chapter uses it. No chapter may cite a key that is not here

Word targets sum into the budget with room to spare (aim near 45,000 words), and
no chapter is targeted below 2,500 words except the conclusion.

Write the master file now too, with the includes it will have and placeholder
front matter, and compile it after every chapter batch lands. A run that is
interrupted then leaves a compilable document rather than a directory of parts,
and a chapter's compile errors surface while its author is still in hand.

### 2. Assemble `refs.bib` before drafting

The bibliography is a dependency of every chapter, so it is built first and
frozen. Write `output/slop-thesis-<slug>-<seed>/refs.bib` with all 60-100
verified external entries and all canon entries, then copy it to the harvest
location (see "Citing the canon"). Add nothing to it after the chapters start;
if a chapter needs a work that isn't there, it cites something that is.

### 3. Dispatch the chapters

One subagent per chapter, dispatched in parallel batches of three or four via
the `Agent` tool (`subagent_type: general-purpose`, on the run's own model ---
chapter drafting is the hard part of this run and does not go to a cheaper
model; only the mechanical image and verification jobs do). Each brief:

> Read `output/slop-thesis-<slug>-<seed>/plan.md` and
> `skills/from-preset/genre.md` in full, then write
> `output/slop-thesis-<slug>-<seed>/ch<NN>.typ` --- chapter <N>, "<title>",
> <target> words, whose purpose is <purpose>. Use only the numbers, names and
> instruments in the plan; invent no new ones. Cite only bib keys listed in the
> plan, with `@key` / `#cite(<key>)`. Do not write the chapter number or a
> `= Chapter N` line --- the template renders the chapter opener from the
> level-1 heading. Follow the typst conventions in
> `skills/from-preset/presets/thesis.md` › "Typst structure" for figures, tables
> and chart imports. Report your word count and a list of every figure and table
> you created, with its caption. Do nothing else.

Charts are authored by the chapter subagent that needs them, into
`output/slop-thesis-<slug>-<seed>/charts/`, per
`../../_shared/chart-workflow.md`. Imagery, if the run wants any, is dispatched
separately per `../../_shared/image-workflow.md` (sonnet subagents, the
mandatory Bash timeout of `600000`).

### 4. Read every chapter

The orchestrator reads all of them, end to end, in order. This is the step the
thesis lives or dies on, and it cannot be delegated. Do the numbers match the
plan and each other? Does each chapter pick up what the previous one handed it
and set up the next --- and if not, where do the connective sentences go? Has
any chapter drifted out of register, explained the joke, re-derived something
already established, or invented a person, unit, scheme or instrument that is in
neither the canon nor the plan? Do the captions carry falsifiable claims rather
than restating their axes?

Fix these in place. Redispatch a chapter only if it is unsalvageable.

### 5. Front matter last

Write the abstract, acknowledgements and declaration **from the finished
chapters**, never from the plan --- an abstract written first describes a thesis
that no longer exists. They replace the master file's placeholders; the contents
and the figure and table lists are already there.

### 6. Compile, check, fix

- Compile (see "Typst structure"), read every error, fix, recompile.
- `pdfinfo … | grep Pages` --- the count must land in 100-180. Short means the
  argument is thin somewhere: extend the chapter that most needs it (usually a
  study's method or its discussion), never pad the front matter or inflate the
  appendices. Long means a chapter is repeating itself; cut it.
- Word count: `pdftotext <pdf> - | wc -w`. Expect roughly 350-420 words per page
  once chapter openers, figures and references are counted in.
- Rerun the commission test on the **finished PDF**, not the plan.
- `ops/check-recent-language.py <pdf> --preset thesis --self-reference-only` ---
  there are no prior theses to compare against, so only the self-reference count
  applies. Read its findings knowing the thesis cites the canon deliberately: a
  literature-review chapter discussing prior outputs is the point, a results
  chapter whose object of study is the corpus is the drift.
- `ops/check-output-quality.py <pdf> --preset thesis` --- the page floor.
- Look at a render once, after the page count is right, rasterised at
  `--ppi 72`: the title page, one chapter opener, one page carrying a figure,
  and the first page of the references.

## Bibliography --- real references, verified (hard requirement)

Same rule as `paper.md`, at four times the scale: **every external entry is a
real work, verified to resolve, with its fields copied accurately.** 60-100
entries. Never fabricate one; never pad with an unverified one.

1. **Search** several real adjacent fields, not one: the methodological
   literature the studies borrow from, the substantive literature about the
   setting, and the critical literature the discussion argues with. Mixed
   venues, mixed decades, a handful of books and chapters alongside the papers
   --- a thesis bibliography that is all recent conference papers reads wrong.
2. **Verify every entry** before it enters the bib, exactly as `paper.md`
   specifies: a DOI that returns 2xx/3xx from
   `curl -sI -o /dev/null -w '%{http_code}' https://doi.org/<doi>`, or an arXiv
   id whose `https://export.arxiv.org/api/query?id_list=<id>` response carries a
   matching title. Drop anything that fails. Verify in parallel batches --- a
   mechanical subagent per batch of twenty, reporting pass/fail per key.
3. **Copy fields accurately**: real authors, real title, real venue, real year,
   the verified DOI or the arXiv form `paper.md` documents (typst drops
   `eprint`/`archivePrefix`, so arXiv entries carry
   `journal = {arXiv preprint arXiv:<id>}`).
4. **Citation honesty**: every prose claim about a cited work is true of that
   work. Engaging with sources at length multiplies the chances of
   misattribution --- if a chapter wants a work to have said something it did
   not, the sentence changes, not the citation.
5. The literature review **engages**: groups works into positions, says what
   each position gets right and what it leaves open, and lands on the gap this
   thesis fills. A chapter of "X did A. Y did B. Z did C." is the classic failed
   literature review and reads as one immediately.

## Citing the canon (30-60 prior outputs)

The University's own programme is the second literature this thesis reviews, and
the citation graph is the only bibliometric the institution has. Rules,
unchanged from `paper.md` except in scale:

- **Source of truth**: `website/src/content/outputs/*.yml`. Copy `title` (with
  the `subtitle` appended after a colon), `authors` verbatim and in order,
  `school`, the year from `date`, and `doi`. An entry that does not match its
  ledger record field-for-field is a fabricated reference --- hard failure.
- **Which to cite**: run `ops/extract-citations.py --suggest 60`, which ranks
  prior outputs by how much a citation would lift a researcher's h-index and
  prints each one's topic line. Topical fit still decides; where two candidates
  fit equally, cite the ranked one. Prefer the supervisors' own prior outputs
  where they are genuinely adjacent --- a candidate citing their supervisors is
  the straightest thing in the document.
- **Verify against the ledger**, not doi.org (the `10.5555` prefix never
  resolves there):
  `grep -l '10.5555/slop.<seed>' website/src/content/outputs/*.yml` must hit
  exactly the entry the fields were copied from.
- **BibTeX shape**, per `paper.md`:
  `@article{slop-<seed>, author = {...}, title = {...}, journal = {Slop University technical report}, year = {...}, doi = {10.5555/slop.<seed>}}`.
- **Characterise each one in a sentence** that is true of its ledger `summary`.
  At this density a bare name-drop list is obvious; the literature review should
  read the canon as a programme, with periods, turns and unresolved
  disagreements in it.
- **Placement**: mostly the literature review, but a study's method may cite the
  prior output whose instrument it adapts, and the discussion the one whose
  finding it fails to reproduce. Spread them.

**Harvest copy (load-bearing).** `ops/extract-citations.py` globs `output/*.typ`
and `output/*.bib` non-recursively, so nothing inside
`output/slop-thesis-<slug>-<seed>/` is visible to it and the run's whole
citation graph would be lost. After freezing the bib, copy it up:

```bash
cp output/slop-thesis-<slug>-<seed>/refs.bib output/slop-thesis-<slug>-<seed>.bib
```

Do the copy again if the bib ever changes. The document still loads the copy in
the run directory; the top-level file exists only so the edges land in the
ledger.

## Figures, tables and imagery

- **Charts** per `../../_shared/chart-workflow.md`, into
  `output/slop-thesis-<slug>-<seed>/charts/`, imported by the chapter that uses
  them and embedded with plain `figure`. Each chart type appears at most once in
  the whole document --- a thesis carrying eight charts and reaching for a line
  or a bar eight times has wasted the menu.
- **Tables** are typst-native and expected --- participant characteristics, an
  instrument's items, a coding frame, a results matrix. A thesis carries more
  tables than a paper does.
- **Generated imagery** is optional and sparing: at most two or three, house
  style per `visual-style.md`, references from `references/slop-style/` only,
  into `output/slop-thesis-<slug>-<seed>-images/`. A thesis is chart-shaped and
  table-shaped, not photo-shaped; where an image earns its place it is usually
  the apparatus or the setting, in a methods chapter.
- **Numbering is per chapter** --- Figure 3.2, Table 5.1. See "Typst structure".
- Every figure and table is referred to in the prose that precedes it; a figure
  nothing points at reads as decoration.

## Voice (examinable)

The register is `paper.md`'s methods-section deadpan, sustained over tens of
thousands of words and stretched to carry things a paper never has to: a
literature review that takes positions, a methodology chapter that justifies its
choices against alternatives, a discussion that situates findings in the field,
a conclusion that concedes what remains open. It defers to `../genre.md` for the
floor and specialises:

- **The candidate's "I" is allowed, sparingly and formally** --- "I argue", "I
  collected" --- as an Australian thesis permits; never enthusiastic, never
  confessional. "We" appears only where it means the candidate and their
  supervisors, and mostly not at all.
- **A methodology chapter that justifies rather than describes**: why this
  design, what it rules out, what was considered and rejected, the ethics and
  positionality paragraphs a real thesis carries.
- **Hedged findings, unhedged apparatus.** The claims are softened; the
  instruments, thresholds and procedures are stated with total precision. The
  contrast is the joke.
- **Limitations that concede nothing**, at length --- a limitations section that
  quietly reasserts a strength eight times is funnier and more plausible than
  one that does it once.
- **Sustained tense discipline**: past for what was done, present for what the
  literature says and what the findings mean.
- **No epigraph that comments on the thesis.** `slop-thesis-epigraph` is
  available; used at all it should be a plain line of the kind a real candidate
  picks, at most twice in the document.

## Typst structure

A4 portrait, single column, book margins. The brand package
`@local/slop-university-brand:0.1.0` exports the thesis API; the master file
holds the title-page call, the front matter, the includes and the bibliography,
and nothing else of substance.

```typst
#import "@local/slop-university-brand:0.1.0": (
  slop-thesis, slop-thesis-frontmatter, slop-thesis-mainmatter,
  slop-thesis-appendices, slop-thesis-backmatter, slop-thesis-declaration,
)

#set document(
  title: "This Slop University Thesis Does Not Exist: <steering verbatim>",
  date: none,
)

#show: slop-thesis.with(
  title: "<thesis title --- steering-derived>",
  subtitle: "<optional>",
  candidate: "<candidate name>",
  degree: "Doctor of Philosophy",
  school: "<School of ...>",
  supervisors: ("<Supervisor A>", "<Supervisor B>"),
  submitted: "<Month Year>",
)

#slop-thesis-frontmatter[
  = Declaration
  #slop-thesis-declaration(candidate: "<candidate name>", date: "<D Month Year>")

  = Acknowledgements
  <supervisors by canon name, the school, the fiction's debts; family generic>

  = Abstract
  <400-600 words, written from the finished chapters>

  = Contents
  #outline(title: none, depth: 2)

  = List of figures                  // omit both lists when the counts are thin
  #outline(title: none, target: figure.where(kind: image))
  = List of tables
  #outline(title: none, target: figure.where(kind: table))
]

#slop-thesis-mainmatter[
  #include "/output/slop-thesis-<slug>-<seed>/ch01.typ"
  #include "/output/slop-thesis-<slug>-<seed>/ch02.typ"
  // ... one line per chapter
]

#slop-thesis-appendices[
  #include "/output/slop-thesis-<slug>-<seed>/app-a.typ"
]

#slop-thesis-backmatter[
  #bibliography("/output/slop-thesis-<slug>-<seed>/refs.bib", title: "References", style: "apa")
]
```

`slop-thesis(...)` delegates to the house `slop(...)` show rule with the title
block hidden, so the base fonts, colours, headings, tables and figures are the
ones every other preset gets; it renders the title page itself and carries the
page number in a centred footer, with no running header. The four region
wrappers own all the page numbering, heading numbering and chapter-opener
behaviour --- the document never sets any of it. Write plain `=` headings and
let them. `style: "apa"` is load-bearing: a thesis does not use numbered
citations.

`slop-thesis-epigraph(quote, attribution)` is available for a chapter epigraph
(right-aligned italic); see "Voice" for when it earns its place.

### Chapter files

Each chapter is a standalone file under `output/slop-thesis-<slug>-<seed>/`,
carrying its own imports. The template numbers figures and tables per chapter
and resolves every cross-reference at the element's own chapter, so a chapter
file sets no counters and no numbering:

```typst
#import "@local/slop-university-brand:0.1.0": slop-colors
#import "/output/slop-thesis-<slug>-<seed>/charts/chart-3.typ": chart as chart-3

= <Chapter title --- no number, no "Chapter N"> <ch-measurement>

<body ...>

== <Section> <sec-setting>

#figure(
  chart-3,
  caption: [<a falsifiable claim with a figure in it>],
) <fig-re-shelving-latency>

As @fig-re-shelving-latency shows, <...> (@ch-measurement, @sec-setting and
@app-schedule render as "Chapter 2", "Section 2.1" and "Appendix A").
```

Plain `figure` is already in-column inside the thesis (the core's full-bleed
image rule is replaced there). Label every figure, table, chapter and section
you refer to and reference it with `@`; never hand-write "Figure 3.2" in prose,
because figure numbers run within their chapter and a typed number goes stale
the moment a chapter moves.

Nothing in a chapter file calls `#pagebreak()`: the template starts each chapter
on a new page, and a manual break inside one strands a figure on an empty page.
A chapter that genuinely needs a section to start fresh is a chapter that needs
a better section.

### Compiling

```bash
typst compile --root . \
  output/slop-thesis-<slug>-<seed>.typ \
  output/pdf/thesis/slop-thesis-<slug>-<seed>.pdf
```

`--root .` is what makes the leading-slash includes, chart imports and image
paths resolve from the project root. Create `output/pdf/thesis/` if absent. No
dark variant: the thesis is a submitted document, not signage.

### Gotchas

- **A compile error in a chapter points at the master file's line.** Compile a
  suspect chapter in isolation with a two-line scratch document that includes
  only it.
- **`#include` evaluates the file's content in place, but imports inside it are
  local to it.** Every chapter file needs its own import line; one in the master
  does not reach them.
- **The region order is load-bearing.** Title page, then frontmatter,
  mainmatter, appendices, backmatter: the page-counter resets live in the
  wrappers, so skipping one loses the roman/arabic split. Never reset
  `counter(page)` by hand.
- **Don't fight an underfull final page.** A thesis ends where its references
  end.

## Pre-ship checklist (preset-specific)

- [ ] A4 portrait, single column; 100-180 pages; 35,000-60,000 words; light
      theme only, no `-dark.pdf`
- [ ] Title page carries the candidate, the degree sentence, the school, both
      supervisors, and the submission month and year; it has no page number
- [ ] Declaration and acknowledgements both present; the declaration is signed
      with the candidate's name and date
- [ ] Abstract states the contribution and the institutional consequence, and
      describes the thesis that was actually written
- [ ] Every chapter and appendix appears in the contents, in order, with its
      title matching the chapter opener
- [ ] No chapter under 2,000 words except the conclusion
- [ ] Figures and tables numbered per chapter (3.1, 3.2, 4.1 …); every one
      referred to in the prose; lists of figures/tables present where the counts
      warrant them, absent where they don't
- [ ] The candidate is the only author; both supervisors named on the title page
      and thanked in the acknowledgements; no other person named outside the
      references
- [ ] **Examiners are never named** --- not in the acknowledgements, not in the
      declaration, not anywhere. A submitted thesis does not know who they are
- [ ] No real venue, conference, journal, university or employer named as the
      candidate's own history. Real works appear only as references
- [ ] The candidate's roster bio and the thesis agree on everything: school,
      supervisors, subject, background
- [ ] 60-100 external references, **every one verified** (DOI resolves or arXiv
      id returns a matching title), fields copied accurately, loaded via
      `bibliography(..., style: "apa")`, each actually cited in the body
- [ ] 30-60 canon citations, each matching its
      `website/src/content/outputs/*.yml` entry field-for-field, each
      characterised in a sentence true of that entry's `summary`
- [ ] `refs.bib` copied to `output/slop-thesis-<slug>-<seed>.bib` so the
      citation graph is harvestable
- [ ] Citation honesty holds throughout: no claim attributed to a real work that
      the work does not make
- [ ] The fixed numbers in `plan.md` are the numbers in every chapter
- [ ] Charts in brand styling, each type used at most once; captions carry
      falsifiable claims; at most three generated images
- [ ] Voice holds for the whole length: no exclamation marks, no enthusiasm, no
      prose that names the paradox it is performing
- [ ] The commission test passes on the finished PDF: the binding institutional
      consequence is central and appears in the abstract and the conclusion
- [ ] `ops/check-recent-language.py <pdf> --preset thesis --self-reference-only`
      and `ops/check-output-quality.py <pdf> --preset thesis` both run and their
      findings addressed
- [ ] PDF metadata title matches the formula; no other metadata populated
- [ ] Output at `output/pdf/thesis/slop-thesis-<slug>-<seed>.pdf`

## Common failure modes (preset-specific)

- **A long paper wearing a thesis's clothes.** Six familiar headings, one study,
  40,000 words of it. A thesis has chapters that do different jobs ---
  reviewing, justifying, reporting, arguing --- and a reader should be able to
  say what each one is for.
- **The chapters disagree.** Different n, a participant who changes role, an
  instrument abbreviated two ways, a finding the discussion overstates. This is
  the characteristic failure of a delegated run and the reason the plan file
  fixes the numbers before anything is written.
- **A literature review that lists.** "X did A. Y did B." A review takes
  positions and lands on a gap.
- **The canon becomes the subject.** Citing thirty prior outputs is the brief;
  studying the corpus instead of the world is the drift
  `check-recent-language.py` flags and `genre.md` names outright.
- **Satire leaks into the prose.** At this length the temptation to wink
  compounds. The institution never notices the contradiction; only the reader
  does.
- **An unverified or fabricated reference slips in**, or a canon entry drifts
  from its ledger record. Hard failure either way --- re-verify or drop.
- **Padding to reach the page floor.** Inflated appendices, a restated
  literature review, a conclusion that recaps every chapter in turn. The fix is
  more substance in the chapter that has least, never more words anywhere.
- **The declaration or acknowledgements carry the joke.** They are the two
  places a reader looks for a person, and the two the document must play most
  straight.

## What this preset is not

- Not a booklet, poster or paper: no cover, no back cover, no parity, no
  two-column body, no one-page fit, no dark variant.
- Not a publication. The thesis is submitted for examination; it never claims
  acceptance, a venue, or a degree already conferred. Nobody is graduated by the
  run that produces it.
- Not a place for new chart or genre conventions --- those belong in
  `../../_shared/chart-workflow.md` and `../genre.md`.
