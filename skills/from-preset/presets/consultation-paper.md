---
name: consultation-paper
description:
  Department of Policy Settings consultation paper --- the Department proposes a
  change to one of the settings under which the schools work, sets out options,
  and invites submissions against numbered consultation questions. Booklet
  format, department lockup, public-service register.
---

# Consultation paper preset

Produce one consultation paper issued by the Department of Policy Settings
(`canon/schools.yml`). It should pass for a real discussion paper from a
government department: the apparatus (numbered questions, options with the
status quo first, a timeline, how to make a submission) is exact, and the
setting it proposes to change is internal to the University.

Loaded by `skills/from-preset/SKILL.md`. Defers to `../genre.md` (the brief, its
floors, and the departmental register), `../../_shared/typst-layout.md` (import,
metadata, page-break discipline, parity), `../../_shared/image-workflow.md` and
`../../_shared/output-naming.md`.

## Doc identity

| Field                      | Value                                                                         |
| -------------------------- | ----------------------------------------------------------------------------- |
| Format                     | `booklet`                                                                     |
| Cover title                | the paper's own title, naming the setting under review                        |
| Cover subtitle             | `Consultation paper` and the month and year of issue                          |
| Issuing unit               | Department of Policy Settings, Consultation and Uptake Division               |
| Cover and back lockup      | `dept` (`config: (lockup: "dept")` on both `slop` and `slop-back-cover`)      |
| Filename prefix            | `slop-consult`                                                                |
| PDF subfolder (`<group>`)  | `consultation-paper`                                                          |
| Page-count range           | 12-16, even                                                                   |
| Register                   | public service (`../genre.md` › Register by genre)                            |
| PDF metadata title formula | `This Slop University Consultation Paper Does Not Exist: <steering verbatim>` |

The document has no authors. Officials appear only by office (the Secretary, a
First Assistant Secretary, the Director of a branch), never by name. On a
publish run the DOI renders under "Publication details"; on a manual run, omit
it.

## Inputs

The steering prompt names the setting, or the trouble with it. With none,
compose one. A setting is any rule the University sets for its own work: the
minimum interval between a researcher's outputs, how co-authorship credit is
divided, the threshold at which a seminar series is reviewed, the length of a
grant round, how desks are allocated, whether an output may cite itself. It is
always internal to the University. Where a steering prompt reaches for real law
or public policy, the paper takes up the University's own setting nearest to it
and offers no legal or regulatory view (`../genre.md` › Harmless).

The paper may name the instrument that holds the setting in force, in the form
`Slop University (<Subject>) Determination <year>` or
`<Subject> Guidelines <year>`. Instruments are not org units, so a run may name
one; it may not name a new division, branch or committee.

## Structural skeleton

| Section                                      | Length       | Notes                                                                                                                                                         |
| -------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cover                                        | 1 page       | Title, subtitle, dept lockup, cover image                                                                                                                     |
| Contents                                     | ---          | Auto                                                                                                                                                          |
| (Optional) Secretary's foreword              | ~200 words   | Only if rolled. Signed "Secretary, Department of Policy Settings", no name                                                                                    |
| Have your say                                | ~150 words   | Fixed heading. Who should respond, the closing date, how to lodge, the contact officer by position, that submissions may be published unless marked otherwise |
| Purpose of this paper                        | ~250 words   | What the Department proposes to review and why now; what is out of scope                                                                                      |
| Background                                   | ~500 words   | The setting as it stands: the instrument, when and why it was made, how it operates across the schools                                                        |
| The case for review                          | ~700 words   | The issues, with evidence from the University's own outputs, cited by DOI (see "Evidence")                                                                    |
| Options                                      | ~1,000 words | 2-4 options. Option 1 is always to retain the current setting. Each: description, how it would operate, considerations. A comparison table closes the section |
| (Optional) The Department's preliminary view | ~200 words   | Only if rolled. Hedged, conditional on consultation                                                                                                           |
| Next steps                                   | ~200 words   | A timeline table: consultation closes, report on what was heard, instrument drafted, commencement                                                             |
| Summary of consultation questions            | ---          | Fixed heading. Every question again, in order, rendered from the same array                                                                                   |
| (Optional) Attachment                        | ~300 words   | Only if rolled: an extract of the current instrument, or a glossary                                                                                           |
| Publication details                          | ~60 words    | Issuing division, date, mailbox, DOI on publish runs                                                                                                          |
| Back cover                                   | 1 page       | `#slop-back-cover(config: (bleed: 3mm, lockup: "dept"))`                                                                                                      |

Consultation questions sit in boxes through the body, where the text that raises
them ends, and are numbered in one sequence across the paper. Every section
after "Have your say" carries at least one.

Word counts are budgets. Vary by ±20% between runs.

## Per-run variation rolls

Roll these before drafting:

- **Options:** 2, 3 or 4 (status quo always first).
- **Questions:** 6-12.
- **Secretary's foreword:** ~30%.
- **Preliminary view:** ~50%. Without it, the paper says the Department has
  formed no view, which is also genre-true.
- **Attachment:** ~30%; if rolled, extract or glossary, one of the two.
- **Numbered headings:** ~50% (`#set heading(numbering: "1.")`).

## Evidence

"The case for review" cites 2-4 published Slop University outputs from
`website/src/content/outputs/*.yml` as the evidence base, each by real title and
`doi:10.5555/slop.<seed>` in prose ("a recent study of seminar attendance in the
School of Settled Matters (doi:10.5555/slop.xxxxxx) found..."). Find them with
`ops/topic-neighbours.py "<the setting>"` and
`ops/extract-citations.py --suggest`. A claim about an output must be true of
its ledger `summary`; a department misquoting the research it relies on reads as
careless, not institutional. Never invent an output or a DOI.

Figures the Department reports about its own settings (how many schools apply
one, how often it has been varied) are internal to the fiction and may be
specific.

## Contact and lodging

The contact officer is a position: "Director, Consultation Branch, Consultation
and Uptake Division". The mailbox is `policy.settings@slop.university`, always
that one. Submissions are lodged by email; the paper never gives a postal
address, a phone number or a web form.

## Imagery (preset specifics)

- Image folder: `output/slop-consult-<slug>-<seed>-images/`
- Prompts: 1 cover (3:4 portrait, `--resolution 4K`) + 2 inline (16:9,
  `--resolution 2K`); reserve a third inline prompt as the parity-fix spare.
- Departmental documents carry few pictures, and those are of the business of
  administration: rooms where people meet, papers, a corridor, a counter. Keep
  them in the two-ink house style (`../../_shared/visual-style.md`).

## Style references

- Layout core:
  `~/.local/share/typst/packages/local/university-typst-template/0.1.0`
- `strategy.md` for the booklet image and back-cover patterns.

## Typst structure

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-back-cover, slop-colors

#set document(
  title: "This Slop University Consultation Paper Does Not Exist: <steering prompt verbatim>",
)

#show: slop.with(
  title: "<Paper title>",
  subtitle: "Consultation paper | <Month Year>",
  cover: read("/output/slop-consult-<slug>-<seed>-images/cover.jpg", encoding: none),
  config: (bleed: 3mm, lockup: "dept"),
)

// Every consultation question, once. The boxes and the summary both render
// from this array, so the two can never disagree.
#let questions = (
  [<Question 1>],
  [<Question 2>],
)
#let ask(n) = block(
  width: 100%,
  inset: (x: 12pt, y: 10pt),
  fill: slop-colors.gold.lighten(88%),
  stroke: (left: 3pt + slop-colors.gold),
  breakable: false,
)[#text(weight: "semibold")[Question #n] \ #questions.at(n - 1)]

#outline(title: [Contents], depth: 1)

= Have your say
<...>

= Purpose of this paper
<...>
#ask(1)

= Background
<...>
#figure(image("/output/slop-consult-<slug>-<seed>-images/inline-1.jpg"))
<...>

// ... The case for review, Options (with a comparison table), Next steps ...

= Summary of consultation questions
#for (i, q) in questions.enumerate() [
  #text(weight: "semibold")[Question #(i + 1).] #q \
]

= Publication details
<Issued by the Consultation and Uptake Division, Department of Policy Settings,
Slop University, <Month Year>. Enquiries: policy.settings\@slop.university.
doi:10.5555/slop.<seed> --- publish runs only.>

#slop-back-cover(config: (bleed: 3mm, lockup: "dept"))
```

Tables (the options comparison, the timeline) follow
`../../_shared/typst-layout.md` › "Tables".

## Pre-ship checklist (preset-specific)

- [ ] Dept lockup on the cover masthead and the back cover
- [ ] Option 1 is to retain the current setting; 2-4 options in all; a
      comparison table closes the section
- [ ] 6-12 questions, boxed in the body, numbered in one sequence, and repeated
      under "Summary of consultation questions" from the same array
- [ ] "Have your say" gives a closing date after the issue date, the contact
      officer by position, and `policy.settings@slop.university`
- [ ] No official named; offices only
- [ ] 2-4 University outputs cited by real title and DOI, each claim true of its
      ledger summary
- [ ] The setting is internal to the University; no view on real law or policy
- [ ] Even page count within 12-16

## Common failure modes (preset-specific)

- **The status quo is a straw man.** Real papers give it a fair hearing; Option
  1 should be one a reasonable school would choose.
- **The Department takes a position too early.** Without a rolled preliminary
  view, nothing in the body may prefer an option.
- **The register slips into the University's corporate voice** (capability,
  ecosystem, nexus). The Department is drier: it notes, considers, proposes and
  invites.
