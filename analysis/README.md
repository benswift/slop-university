# analysis

Empirical studies of what the press has published, and the scripts that produce
them. Analysis lives here rather than in the paper repository: the apparatus and
the measurements of it belong together, so a reader who wants to check a number
finds it beside the machinery that generated it.

## Studies

- [`citation-census/`](citation-census/) --- what the fabricated papers borrow
  from the real literature. A census (not a sample) of all 199 published
  `paper`-preset outputs: citation volume, distinct real works, DOI/arXiv
  resolution rates, disciplinary spread, and the internal self-citation graph.
- [`discrimination-pilot/`](discrimination-pilot/) --- whether language models
  can tell this press's institutional prose from genuine university documents,
  from text alone with identities redacted. Three judges across two model
  families.

Each directory carries its own README with method, results, and caveats.

## Reproducibility

Two limits are worth stating up front, because they bound what anyone else can
re-run.

**The census reads local typst sources.** `output/` is gitignored, so the `.typ`
and `.bib` files the census extracts from are not in this repository and
`extract.py` cannot be re-run from a fresh clone. `distinct_works.json` is
committed for that reason --- it is the durable record of the extracted
bibliography, and `verify.py` runs from it against the live Crossref and arXiv
APIs.

**The pilot's judgements are model outputs and will not reproduce exactly.** The
raw judgements are committed under `discrimination-pilot/results/` for that
reason. The stimulus set and the redaction spans are committed too, so the
inputs are checkable even where the outputs cannot be regenerated.

## A note on `verify.py`

Its first version scored title matches against the longer of the two token sets,
which reads Crossref's truncated records ("Web Surveys" for "Web Surveys: A
Review of Issues and Approaches") as mis-keyed DOIs. That reported ~86%
correct-work resolution against a true ~99%, and the six false alarms had to be
cleared by hand. The current version treats a literal prefix match as a
truncation and follows Crossref redirects, and it reproduces 99/100
automatically --- the single remaining mismatch is a genuine mis-key. If a rerun
reports a materially lower rate, suspect the matcher before the corpus.
