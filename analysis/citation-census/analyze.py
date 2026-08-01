#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Headline-numbers pass over entries.json / papers.json produced by extract.py.

Primary census population = the 199 papers matched to the published ledger
(preset: paper). The 17 local-only papers (not in the ledger) are reported
separately and excluded from headline counts.
"""

import json
import re
import statistics as stats
from collections import Counter
from pathlib import Path

OUT = Path(__file__).parent
entries = json.loads((OUT / "entries.json").read_text())
papers = json.loads((OUT / "papers.json").read_text())

papers_led = [p for p in papers if p["in_ledger"]]
led_ids = {p["paper_id"] for p in papers_led}
ent_led = [e for e in entries if e["paper_id"] in led_ids]

ext = [e for e in ent_led if not e["is_self_citation"]]
selfcite = [e for e in ent_led if e["is_self_citation"]]

print(f"=== Population ===")
print(f"Ledger-matched papers: {len(papers_led)}")
print(f"Total reference rows (all): {len(ent_led)}")
print(f"External (real-literature) citation instances: {len(ext)}")
print(f"Self-citation instances (slop-prefixed): {len(selfcite)}")

# per-paper reference counts
refcounts = [p["n_references"] for p in papers_led]
print(f"\n=== Per-paper reference counts (incl. self-cites) ===")
print(
    f"mean={stats.mean(refcounts):.2f} median={stats.median(refcounts)} "
    f"min={min(refcounts)} max={max(refcounts)} stdev={stats.stdev(refcounts):.2f}"
)

extcounts_by_paper = Counter(e["paper_id"] for e in ext)
extcounts = [extcounts_by_paper.get(p["paper_id"], 0) for p in papers_led]
print(f"\n=== Per-paper EXTERNAL (non-self) reference counts ===")
print(
    f"mean={stats.mean(extcounts):.2f} median={stats.median(extcounts)} "
    f"min={min(extcounts)} max={max(extcounts)}"
)


# dedup by DOI (fallback: normalized title) for external works
def norm_title(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


def dedup_key(e):
    doi = (e.get("doi") or "").strip().lower()
    if doi:
        return ("doi", doi)
    return ("title", norm_title(e.get("title", "")))


dedup_counter = Counter(dedup_key(e) for e in ext)
distinct_works = len(dedup_counter)
print(f"\n=== Distinct works cited (external only) ===")
print(f"Distinct works (deduped by DOI/title): {distinct_works}")
print(
    f"Citation instances: {len(ext)}  ->  reuse ratio {len(ext) / distinct_works:.2f}x"
)

repeated = {k: v for k, v in dedup_counter.items() if v > 1}
print(
    f"Distinct works cited more than once: {len(repeated)} "
    f"({len(repeated) / distinct_works * 100:.1f}% of distinct works)"
)
print(
    f"Citation instances accounted for by repeated works: {sum(repeated.values())} "
    f"({sum(repeated.values()) / len(ext) * 100:.1f}% of external instances)"
)

print("\nTop 20 most-cited external works:")
# need title/author for display - build lookup
lookup = {}
for e in ext:
    k = dedup_key(e)
    if k not in lookup:
        lookup[k] = e
for k, cnt in dedup_counter.most_common(20):
    e = lookup[k]
    print(
        f"  {cnt:3d}x  {e.get('author', '')[:50]:50s} ({e.get('year', '?')}) {e.get('title', '')[:70]}  doi={e.get('doi', '')}"
    )

# entry-type breakdown
print(f"\n=== Entry type breakdown (external) ===")
for t, c in Counter(e["entry_type"] for e in ext).most_common():
    print(f"  {t}: {c}")

# doi presence
has_doi = sum(1 for e in ext if e.get("doi"))
has_arxiv_journal = sum(
    1
    for e in ext
    if not e.get("doi")
    and "arxiv" in (e.get("journal", "") + e.get("eprint", "")).lower()
)
neither = len(ext) - has_doi - has_arxiv_journal
print(f"\n=== DOI / arXiv presence in bib records (external, {len(ext)} instances) ===")
print(f"Has explicit doi field: {has_doi} ({has_doi / len(ext) * 100:.1f}%)")
print(
    f"No doi field but arXiv preprint noted in journal/eprint: {has_arxiv_journal} ({has_arxiv_journal / len(ext) * 100:.1f}%)"
)
print(f"Neither: {neither} ({neither / len(ext) * 100:.1f}%)")

# save distinct works list for sampling
distinct_list = []
for k, e in lookup.items():
    distinct_list.append(
        {
            "key": k,
            "count": dedup_counter[k],
            "doi": e.get("doi"),
            "journal": e.get("journal"),
            "eprint": e.get("eprint"),
            "author": e.get("author"),
            "title": e.get("title"),
            "year": e.get("year"),
            "entry_type": e.get("entry_type"),
            "publisher": e.get("publisher"),
            "booktitle": e.get("booktitle"),
        }
    )
(OUT / "distinct_works.json").write_text(json.dumps(distinct_list, indent=2))
print(f"\nWrote {OUT / 'distinct_works.json'} ({len(distinct_list)} distinct works)")

# self-citation summary
print(f"\n=== Self-citation ===")
papers_with_selfcite = set(e["paper_id"] for e in selfcite)
print(
    f"Papers containing >=1 self-citation: {len(papers_with_selfcite)} / {len(papers_led)} "
    f"({len(papers_with_selfcite) / len(papers_led) * 100:.1f}%)"
)
selfcounts = Counter(e["paper_id"] for e in selfcite)
print(f"Self-citation instances: {len(selfcite)}")
print(
    f"Self-citations per citing paper (of those with >=1): "
    f"mean={stats.mean(selfcounts.values()):.2f} median={stats.median(selfcounts.values())} "
    f"max={max(selfcounts.values())}"
)

selfcite_targets = Counter((e.get("doi") or e.get("key")) for e in selfcite)
print(f"Distinct slop DOIs targeted by self-citation: {len(selfcite_targets)}")
print("Most self-cited slop outputs:")
for doi, cnt in selfcite_targets.most_common(10):
    row = next((e for e in selfcite if (e.get("doi") or e.get("key")) == doi), None)
    print(f"  {cnt}x  {doi}  {row.get('title', '')[:70] if row else ''}")

(OUT / "selfcite.json").write_text(json.dumps(selfcite, indent=2))
