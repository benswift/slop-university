---
name: questions-on-notice
description:
  The Department of Policy Settings' written answers to questions taken on
  notice at a hearing of the Committee on Settings Oversight. A bundle of 3-6
  questions from roster researchers on the Committee, each with its reference
  block, the question as asked, and the Department's answer. Paper format,
  department lockup.
---

# Questions on notice preset

Produce one bundle of answers to questions taken on notice at a hearing of the
Committee on Settings Oversight (`canon/schools.yml`). It should pass for a real
tabled answers document: a reference block per question, the question as asked,
and an answer that discloses as little as procedure allows.

Loaded by `skills/from-preset/SKILL.md`. Defers to `../genre.md` (the brief, its
floors, and the departmental register), `paper.md` (the paper-format typst
pattern), `../../_shared/typst-layout.md` and `../../_shared/output-naming.md`.

## Doc identity

| Field                      | Value                                                             |
| -------------------------- | ----------------------------------------------------------------- |
| Format                     | **paper** (A4 portrait, single column)                            |
| Visible title              | `Answers to questions on notice`                                  |
| Visible subtitle           | `Committee on Settings Oversight, <hearing>, <date of hearing>`   |
| Issuing unit               | Department of Policy Settings                                     |
| Lockup                     | `dept` (`config: (lockup: "dept")`)                               |
| Filename prefix            | `slop-qon`                                                        |
| PDF subfolder (`<group>`)  | `questions-on-notice`                                             |
| Page count                 | 2-5 (no parity requirement)                                       |
| Register                   | public service (`../genre.md` › Register by genre)                |
| PDF metadata title formula | `These Slop University Answers Do Not Exist: <steering verbatim>` |

`<hearing>` is one of "Autumn hearings", "Spring hearings" or "Supplementary
hearings". On a publish run the DOI renders under the title; on a manual run,
omit it.

## Inputs

The steering prompt names the subject the Committee pressed the Department on: a
setting, a consultation, a delay, a figure. With none, compose one. The
questions all come from one hearing and circle that subject from different
directions.

## People

- **Questioners** are members of the Committee: roster researchers, never
  doctoral candidates, each by canonical title and name ("Dr Verity Marris").
  Use at least two. A member asks what their school and bio would make them ask.
- **The Department's witnesses** appear in a transcript only by office: "First
  Assistant Secretary, Settings Maintenance Division", "the Secretary". Never a
  name.
- The University Council and the Vice-Chancellor are never questioners and never
  quoted. The Department may refer to "the Office of the Vice-Chancellor" as the
  office that makes an instrument.

## Each question

A reference block (a two-column table), then the question, then the answer:

| Field       | Content                                                     |
| ----------- | ----------------------------------------------------------- |
| Reference   | `CSO-<yy>-<nnn>`, numbers ascending through the bundle      |
| Division    | one of the Department's divisions, from `canon/schools.yml` |
| Topic       | a few words                                                 |
| Asked by    | the member's title and name                                 |
| Type        | `Spoken (proof transcript, p. <n>)` or `Written`            |
| Date lodged | after the hearing date                                      |

A **spoken** question is the transcript excerpt in which it was asked: the
member's words as spoken (looser and more pointed than the answer), the
witness's reply by office, ending where the witness takes it on notice. A
**written** question is the member's question as lodged.

The **answer** is the Department's, in its register. Across the bundle, use
several of the forms real answers take:

- a direct answer with a small table of the Department's own figures (internal
  to the fiction, so specific)
- "The Department does not hold this information in the form requested."
- a decline on resourcing: providing it "would require an unreasonable diversion
  of the Department's resources"
- a referral to a published output or an earlier answer, by DOI
- a partial answer that answers a narrower question than the one asked

Answers never apologise and never argue with the member.

## Citations

Where an answer refers to research or to an earlier document, it gives the real
title and `doi:10.5555/slop.<seed>` of a published output from
`website/src/content/outputs/*.yml`, found with `ops/topic-neighbours.py`. An
earlier `questions-on-notice` or `consultation-paper` output is the most natural
reference. A claim about an output must be true of its ledger summary. Never
invent an output or a DOI.

## Typst structure

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-colors

#set document(
  title: "These Slop University Answers Do Not Exist: <steering prompt verbatim>",
)

#show: doc => slop(
  title: [Answers to questions on notice],
  subtitle: [Committee on Settings Oversight, <hearing>, <date>],
  author: [
    Department of Policy Settings, Slop University \
    #text(fill: slop-colors.grey-4)[doi:10.5555/slop.<seed>] // publish runs only
  ],
  paper: "a4",
  config: (theme: "light", style: "compact", font-size: 10.5pt, lockup: "dept"),
  doc,
)

#let reference(..rows) = table(
  columns: (auto, auto), // ops/check-table-fit.py rejects fr columns
  stroke: (x, y) => (bottom: 0.4pt + slop-colors.grey-2),
  inset: (x: 0pt, y: 5pt),
  ..rows.pos().map(((k, v)) => (text(weight: "semibold")[#k], v)).flatten(),
)

= <Topic of question 1>
#reference(
  ([Reference], [CSO-26-<nnn>]),
  ([Division], [<division>]),
  ([Topic], [<topic>]),
  ([Asked by], [<Title Name>]),
  ([Type], [Spoken (proof transcript, p. <n>)]),
  ([Date lodged], [<date>]),
)

*Question* \
<transcript excerpt or written question>

*Answer* \
<the Department's answer>

// ... one heading per question ...
```

Compile to `output/pdf/questions-on-notice/` and expect 2-5 A4 pages.

## Pre-ship checklist (preset-specific)

- [ ] Dept lockup on the masthead
- [ ] 3-6 questions from one hearing, reference numbers ascending, each with the
      full reference block
- [ ] Questioners are roster researchers who are not doctoral candidates, by
      canonical title and name; at least two of them
- [ ] Witnesses by office only; no Council member or Vice-Chancellor quoted
- [ ] At least three of the answer forms used across the bundle
- [ ] Every DOI is a real ledger entry, each claim true of its summary
- [ ] 2-5 pages, A4, single column

## Common failure modes (preset-specific)

- **Every answer stonewalls.** The bundle reads true only if some answers
  answer, and the evasions sit among them.
- **The members sound like the Department.** A member speaking at a hearing is
  impatient, specific and sometimes rhetorical; the transcript should sound
  spoken.
- **The answer winks.** It is never sarcastic, and never more forthcoming than
  the form allows.
