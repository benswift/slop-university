# Slop University citation-borrowing census

Read-only empirical census of the bibliographies in Slop University's `paper`
preset outputs, run against the local checkouts of `slop-university-press` and
`slop-university`, and against the published ledger
(`slop-university/website/src/content/outputs/*.yml`). Compiled 2026-08-01.

## Headline numbers

| Metric                                                                    | Value                                                                                                               |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Published `paper`-preset outputs in the ledger                            | 199                                                                                                                 |
| Published papers with a local source recovered                            | 199 / 199 (**100%**)                                                                                                |
| Local-only paper sources not in the ledger (drafts, excluded from census) | 17                                                                                                                  |
| Total reference-list entries (incl. self-citations)                       | 3,714                                                                                                               |
| External (real-literature) citation instances                             | 3,402                                                                                                               |
| Self-citation instances (prior Slop University outputs)                   | 312                                                                                                                 |
| Mean / median references per paper (all)                                  | 18.7 / 18                                                                                                           |
| Mean / median external references per paper                               | 17.1 / 17                                                                                                           |
| Distinct real works cited (deduplicated)                                  | 2,559–2,568 (see note)                                                                                              |
| Reuse ratio (external instances ÷ distinct works)                         | ≈1.33×                                                                                                              |
| Distinct works cited more than once                                       | 307 (12.0% of distinct works, 33.5% of instances)                                                                   |
| Most-cited real work                                                      | Bevan & Hood (2006), _What's Measured Is What Matters_ — 40×                                                        |
| **DOI/arXiv resolution rate (n=100 sample)**                              | **100% resolve to a real record; 99% resolve to the _correct_ claimed work; 1% mis-keyed to a different real work** |
| Papers containing ≥1 self-citation                                        | 152 / 199 (76.4%)                                                                                                   |
| Self-citation DOIs resolving to a real ledger entry                       | 312 / 312 (100%)                                                                                                    |
| Distinct slop outputs targeted by self-citation                           | 189                                                                                                                 |
| Most self-cited slop output                                               | _Flagged, Not Retired_ (10.5555/slop.03ley4) — 13×                                                                  |
| Longest self-citation chain found                                         | 7 hops                                                                                                              |

## 1. Extraction

**How references are encoded.** Every `slop-paper-*.typ` file uses Typst's
native bibliography mechanism: in-text `@key` citation marks resolved against a
companion `.bib` file loaded via `#bibliography("/output/<slug>.bib", ...)` at
the end of the document. There is no manual reference list and no inline
citation dumping — this is a real BibTeX-format bibliography per paper, one
`.bib` file per `.typ` file, sharing the same six-character slug (e.g.
`slop-paper-a-checklist-tool-a1axjp.typ` / `.bib`, ledger DOI
`10.5555/slop.a1axjp`).

**Method.**

1. `extract.py` globs `slop-paper-*.bib` in both
   `~/projects/slop-university-press/output/` and
   `~/projects/slop-university/output/`, parses each with `bibtexparser`, and
   tags every entry `is_self_citation` if its BibTeX key starts with `slop-` or
   its `doi` field contains `10.5555/slop.`.
2. Each paper is joined to the published ledger by extracting the six-character
   slug from both the `.bib` filename and the ledger's
   `doi: 10.5555/slop.<slug>` field (only `preset: paper` ledger entries
   considered).
3. Output: `papers.json` (one row per paper) and `entries.json` (one row per
   citation instance), from which everything below is derived.

**Coverage achieved: 199/199 (100%).** Contrary to the brief's expectation that
local sources would be a partial sample of the 199 published papers, every
single published `paper`-preset output has a `.typ`+`.bib` pair surviving in one
of the two local checkouts (177 in `slop-university-press`, 39 in
`slop-university`, with a small number of slug collisions resolved by repo). No
PDF `pdftotext` fallback was needed — the source-truth `.bib` files were
available for the entire published population. There are also 17 additional
local `slop-paper-*.bib` files with no matching ledger entry (presumably drafts
or withdrawn runs); these are reported separately in the Coverage section and
excluded from all headline counts.

## 2. Headline counts (detail)

- 3,714 total reference-list rows across 199 papers; 3,402 (91.6%) are external
  real-literature citations and 312 (8.4%) are self-citations of prior Slop
  University outputs.
- Per-paper external reference count: mean 17.1, median 17, range 13–23 — tight
  and centrally clustered, consistent with a generation preset that targets a
  fixed citation-count band rather than organically varying by topic.
- Deduplication of the 3,402 external instances by DOI (falling back to a
  normalised title when no DOI is present) yields **2,568 distinct works**. A
  secondary pass matching on normalised title alone found **9 title groups where
  the same work carries two different DOIs across different papers** (18
  DOI-distinct entries collapsing to 9 real works — see §3 for a concrete
  example). Adjusting for this gives **2,559 truly distinct works**. The gap
  between the two numbers (2,568 vs. 2,559) is itself a data point: a small but
  non-zero fraction of "distinct" entries are actually DOI-keying variance on
  the _same_ underlying work, not new borrowing.
- 307 of the 2,568 distinct-by-DOI works (12.0%) are cited by more than one
  paper; those repeats account for 1,141 of the 3,402 external instances
  (33.5%). In other words, a third of all borrowed citations point at a shared
  pool of ~300 works rather than a unique source per instance — Slop University
  has assembled a recurring canon, not just per-paper window-dressing.

**Top 10 most-cited real works** (author, year, title, count):

| #   | Count | Work                                                                                                                |
| --- | ----- | ------------------------------------------------------------------------------------------------------------------- |
| 1   | 40    | Bevan & Hood (2006), _What's Measured Is What Matters: Targets and Gaming in the English Public Health Care System_ |
| 2   | 36    | Espeland & Sauder (2007), _Rankings and Reactivity: How Public Measures Recreate Social Worlds_                     |
| 3   | 31    | Braun & Clarke (2006), _Using Thematic Analysis in Psychology_                                                      |
| 4   | 27    | Meyer & Rowan (1977), _Institutionalized Organizations: Formal Structure as Myth and Ceremony_                      |
| 5   | 23    | Landis & Koch (1977), _The Measurement of Observer Agreement for Categorical Data_                                  |
| 6   | 19    | Manheim & Garrabrant (2018), _Categorizing Variants of Goodhart's Law_                                              |
| 7   | 19    | Campbell (1979), _Assessing the Impact of Planned Social Change_                                                    |
| 8   | 18    | Cohen (1960), _A Coefficient of Agreement for Nominal Scales_                                                       |
| 9   | 15    | Dietvorst, Simmons & Massey (2015), _Algorithm Aversion_                                                            |
| 10  | 13    | Strathern (1997), _'Improving Ratings': Audit in the British University System_ (two DOI variants, see §3)          |

This is a coherent, recognisable canon: Goodhart's-law / audit-culture social
science (Espeland, Strathern, Bevan & Hood, Meyer & Rowan, Campbell, Manheim &
Garrabrant) plus measurement-methodology staples (Cohen's kappa, Landis & Koch,
Braun & Clarke thematic analysis) — exactly the literature a paper about metrics
gaming and qualitative coding would organically cite. Entry-type breakdown of
external citations: 3,257 `article`, 89 `inproceedings`, 33 `book`, 15
`incollection`, 6 `inbook`, 2 `techreport`.

## 3. Verification

**Doctrine under test:** every cited work resolves via DOI or arXiv.

**Method.** `verify.py` drew a random sample of 100 distinct external works
(seeded, reproducible: `random.seed(20260801)` over the 2,568-item
`distinct_works.json`) and tested resolution:

- If a `doi` field was present, queried `https://api.crossref.org/works/{doi}`.
- If no `doi` field but an arXiv identifier could be extracted from the
  `journal`/`eprint` field, queried the arXiv API
  (`export.arxiv.org/api/query`).
- Compared the _claimed_ title against the _resolved_ title (word-overlap
  Jaccard similarity) to catch DOIs that resolve to a real but _different_ work
  — the failure mode a naive "does the DOI 200 or 404" check would miss.

**Result: 100/100 sampled entries resolved to a real DOI or arXiv record — zero
fabricated/dead identifiers.** Breaking down the 100:

- 80 resolved directly to the claimed work via Crossref.
- 13 had no `doi` field but resolved via arXiv (all had genuine arXiv IDs
  embedded in the `journal` field, e.g. `arXiv preprint arXiv:2309.06196`).
- 6 initially flagged as "title mismatch" by the automated similarity check
  turned out, on manual inspection, to be correct matches — Crossref simply
  returns a truncated `short-container-title`-style short title (e.g. bib title
  _"Faster Progress Bars: Manipulating Perceived Duration with Visual
  Augmentations"_ vs. Crossref's stored _"Faster progress bars"_ for the same
  DOI). This is a methodology artefact, not a bibliography defect — logged as a
  caveat below.
- **1 genuine mis-keyed DOI** (1% of sample): the entry titled _"Typologies as a
  Unique Form of Theory Building: Toward Improved Understanding and Modeling"_
  (Doty & Glick, 1994 — correct DOI `10.2307/258704`) was found in one paper's
  bibliography keyed to `10.5465/amr.1994.9412190216`, which Crossref redirects
  to a _completely different_ 1994 Academy of Management Review paper (Lado &
  Wilson, _Human Resource Systems and Sustained Competitive Advantage_). Both
  the correct DOI (2×, across other papers) and the wrong one (1×) appear in the
  corpus for the same claimed title — i.e. this is not systematic fabrication,
  it's an occasional keying error that happens to collide with another real DOI
  in the same publisher/year range.

**Net verdict:** the "real bibliography" doctrine holds almost exactly — 100% of
sampled entries point at _something_ real, 99% point at the _correct_ thing.
With n=100, the 99% figure carries a 95% Wilson CI of roughly 94.6–99.8%, so
"the doctrine is true to within a percent or so, with one demonstrated
exception" is the honest framing, not "flawlessly true."

Two smaller structural observations from the full corpus (not just the sample),
consistent with the finding above:

- 90.5% of the 3,402 external instances carry an explicit `doi` field; 9.5%
  carry only an arXiv preprint number in the `journal` field with no `doi` field
  populated (all of these resolved successfully in the sample).
- The 9 title-duplicate-with-different-DOI groups found in §2 are the same
  phenomenon as the Doty & Glick case, at the corpus level: e.g. Hood (2006)
  _"Gaming in Targetworld"_ appears with DOI `10.1111/j.1540-6210.2006.00612.x`
  (9×, correct) and `10.1111/j.1540-6210.2006.00697.x` (1×, a different real
  article in the same journal issue range); Manheim & Garrabrant (2018) appears
  with and without a `{G}` LaTeX brace around "Goodhart" (cosmetic, same DOI
  target in substance); Strathern (1997) appears under two different real DOIs
  (13× and 9×) for what reads as the same paper. These look like generation-time
  citation-key noise rather than deliberate fabrication — genuine papers,
  occasionally the wrong (but real) identifier.

## 4. Characterisation of what was borrowed

**Publication years** (3,402 external instances): range 1907–2026, median 2014.
Distribution by decade:

| Decade   | Count |
| -------- | ----- |
| pre-1950 | 6     |
| 1950s    | 18    |
| 1960s    | 48    |
| 1970s    | 139   |
| 1980s    | 114   |
| 1990s    | 274   |
| 2000s    | 738   |
| 2010s    | 1,108 |
| 2020s    | 955   |

43.7% of citations are to work from the last decade (2016–2026), but the tail is
long and genuine — pulling in foundational mid-century social science (Campbell
1959, Cohen 1960) alongside contemporary arXiv preprints.

**Venues.** Top venues by citation-instance count: arXiv preprint (322, 9.5%),
_American Journal of Sociology_ (70), _Public Administration_ (44), _Science_
(44), _PLOS ONE_ (36), _Journal of Personality and Social Psychology_ (36),
_Human Factors_ (33), _Qualitative Research in Psychology_ (32), _Frontiers in
Psychology_ (29), _Biometrics_ (28). The spread is wide — no single venue
dominates outside arXiv itself.

**Disciplinary spread** (keyword heuristic over journal/booktitle/publisher/
title — AI/ML/HCI/CS keyword list vs. general CS-adjacent vs. everything else;
see `characterize.py` for the exact keyword list, which is necessarily
approximate):

| Bucket                                                                                        | Instances | Share |
| --------------------------------------------------------------------------------------------- | --------- | ----- |
| AI/ML/HCI/CS (arXiv, NeurIPS/ICML/CHI-style venues, ACM/IEEE, "neural"/"language model"/etc.) | 519       | 15.3% |
| CS-adjacent (other IEEE/ACM/computing/algorithms)                                             | 171       | 5.0%  |
| Other field (social science, psychology, public administration, statistics, medicine, etc.)   | 2,712     | 79.7% |

So roughly one citation in five touches AI/ML/CS/HCI; four in five are drawn
from social science, psychology, public administration, statistics and adjacent
fields — matching the corpus's actual subject matter (audit culture, measurement
validity, qualitative coding, bureaucratic gaming) rather than papering over AI
claims with AI citations.

**Most-cited authors.** By raw citation-instance count (first author): Espeland
(45, across 3 distinct works), Bevan (40, 1 work), Braun (36, 4 works),
Strathern (29, 5 works — including the DOI-duplicate pair above), Meyer (28, 2
works), Cohen (25, 6 works), Campbell (24, 4 works), Landis (23, 1 work),
Dietvorst (21), Manheim (20, 2 works). The authors who recur across _multiple
distinct works_ (Espeland, Braun, Strathern, Cohen, Campbell, Weick, Hood)
represent genuine authorial concentration on the audit/measurement-methodology
canon, not just one blockbuster paper being repeated. By contrast, the top names
ranked by _number of distinct works cited_ (Liu, Lee, Zhang, Wang, Kim, Li,
Chen, Huang) are almost certainly a common-surname artefact of the arXiv/CS
citation pool rather than a small number of prolific individuals — this ranking
method is unreliable for East Asian surnames without full given-name
disambiguation and should not be read as "author X is unusually favoured."

## 5. The self-citation loop

**Method.** `selfcite_graph.py` takes the 312 self-citation instances from the
199 ledger-matched papers, resolves each cited `doi` against the _full_
published ledger (495 entries, all presets — a paper can cite a research-poster
or other non-paper output as a "Slop University technical report"), and builds a
directed citing→cited graph restricted to the subset of self-citations whose
target is itself one of our 199 paper-preset sources, to look for chains.

**Findings:**

- 152 of 199 papers (76.4%) contain at least one self-citation.
- 312 self-citation instances total; of papers with ≥1, mean 2.05, median 2, max
  3 per paper (the preset appears to cap self-citations at 1–3, per the design
  doctrine).
- 189 distinct slop outputs are targeted across those 312 instances.
- **All 312 self-citation DOIs (100%) resolve to a real entry in the published
  ledger.** No fabricated or dangling self-citations were found.
- Cited works split by their own preset: 201 instances cite another `paper`, 111
  cite a `research-poster`; no other preset (ad, brochure, impact report, etc.)
  was targeted in this population.
- Most self-cited slop output: _"Flagged, Not Retired: A Twelve-Month Deployment
  of the Indicator Commons' Sunset Scorer..."_ (`10.5555/slop.03ley4`) — cited
  by 13 other papers.
- **The internal citation graph has real depth.** Restricting to self-citations
  that target one of the 199 paper-preset papers: 129 papers cite at least one
  other paper in the set; 71 papers are _both_ a citer and a citee (i.e. sit
  inside the graph, not just at its edges); 188 three-hop chains (A→B→C) exist.
  The **longest chain found is 7 hops**:
  `p3oadh → qkclqm → xrw9lu → 3av1kp → w45vmw → ll5xcj → 03ley4` (terminating,
  fittingly, at the most-cited slop output). No mutual 2-cycles (A↔B) were found
  — the graph is a DAG in this sample, not a closed citation ring.

This is the clearest evidence for the paper's "borrowed legitimacy via the
citation graph" argument extended inward: Slop University isn't just citing real
external literature, it has also built a self-referential citation lattice among
its own fabricated outputs, several links deep, entirely resolvable and entirely
fictional in content.

## Caveats and coverage

- **Coverage: 199/199 published `paper`-preset outputs (100%)** had a local
  `.typ`+`.bib` source recovered — better than the brief's expectation of a
  partial sample. No PDF-text fallback was required for the census population.
  17 additional local `slop-paper-*.bib` files exist with no matching ledger DOI
  (likely drafts/withdrawn runs); these were excluded from every count above and
  are not part of the 199-paper census.
- **Deduplication is DOI/title-based, not semantic.** The 2,568-vs-2,559
  distinct-work count gap (§2) shows DOI-based dedup slightly _overcounts_
  distinct works when the same work is cited under two different DOIs in
  different papers. A full author+year+title fuzzy match might collapse a
  handful more; nine known cases have been manually confirmed and are documented
  in §3.
- **Verification sample is n=100 of 2,568 distinct works (~3.9%).** This is
  within the brief's target (60–100) but is still a sample: the 99% "resolves to
  the correct work" figure has a 95% CI of roughly 94.6–99.8%. Treat "1 in 100"
  as an order-of-magnitude estimate of the mis-keying rate, not an exact
  population parameter.
- **Title-similarity matching under-flags nothing but over-flags truncation.**
  The automated Jaccard check initially flagged 6 correct matches as mismatches
  because Crossref stores short/truncated titles for some records; all 6 were
  manually verified as correct before being counted as resolved. This means the
  _automated_ pipeline alone would have under-reported the resolution rate —
  anyone re-running `verify.py` without the manual review step should expect
  ~86% not ~99%, and should re-check "title_mismatch" rows by hand before
  treating them as failures.
- **Disciplinary classification is a keyword heuristic** (`characterize.py`,
  `AI_KW`/`CS_ADJACENT` lists) applied to venue/title text, not a citation
  database's subject classification. It is good enough to show an
  order-of-magnitude split (roughly 1-in-5 AI/CS-touching vs. 4-in-5 other
  fields) but individual borderline entries (e.g. a _Sensors_ paper on IoT
  sensing, classified "other field" here) could reasonably be recategorised.
- **Author-concentration analysis is unreliable for common surnames.**
  First-author-surname counting conflates distinct individuals who share a
  surname (especially for East-Asian names in the CS/arXiv pool: Liu, Lee,
  Zhang, Wang, Kim, Li). The "most-cited authors" list in §4 uses the
  citation-_instance_ ranking (which is dominated by a few genuinely repeated
  Western-named authors and is more trustworthy) rather than the distinct-works
  ranking for that reason.
- **Self-citation resolution was checked against DOI presence in the ledger, not
  content fidelity.** We confirmed the 312 self-citation DOIs all match a real
  ledger record (title/preset available), but did not independently re-verify
  that the _claimed_ title/authors in the citing paper's `.bib` entry exactly
  match the ledger record's title/authors for every instance — spot checks (e.g.
  `slop-wfyo68` → `slop-03ley4`, used in the chain-length worked example)
  matched exactly.
- **PDFs were not needed and therefore not used** for extraction; this census is
  Typst/BibTeX-source-only. If future work needs to extend coverage beyond
  what's in the two local checkouts, `pdftotext` extraction of
  `output/pdf/paper/*.pdf` reference-list pages would be the fallback path, but
  was not exercised here.

## Reproducing this census

All scripts are `uv run --script` self-contained (PEP 723 inline dependencies)
and live alongside this report:

- `extract.py` — walks both repos' `slop-paper-*.bib` files, joins to the
  published ledger, writes `papers.json` / `entries.json`.
- `analyze.py` — headline counts, distinct-work dedup, top-cited works,
  self-citation summary; writes `distinct_works.json` / `selfcite.json`.
- `verify.py` — draws the seeded random sample from `distinct_works.json`,
  checks Crossref/arXiv resolution, writes `verification_sample.json`.
- `characterize.py` — years, venues, discipline heuristic, author concentration.
- `selfcite_graph.py` — full-ledger self-citation resolution and the
  citing→cited graph/chain search; writes `selfcite_graph.json`.

Run in order:
`uv run extract.py && uv run analyze.py && uv run verify.py && uv run characterize.py && uv run selfcite_graph.py`.
All intermediate JSON artefacts are left alongside the scripts for
spot-checking.
