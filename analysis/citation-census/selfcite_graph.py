#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""
Self-citation loop analysis: for every self-citation instance, check whether
the cited DOI resolves to a real entry ANYWHERE in the full published ledger
(all 496 entries, not just preset: paper — a paper could cite a brochure,
impact report, etc.), and build the citing-paper -> cited-paper graph to
look for chains (A cites B, B cites C).
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import yaml

OUT = Path(__file__).parent
LEDGER = Path.home() / "projects/slop-university/website/src/content/outputs"

entries = json.loads((OUT / "entries.json").read_text())
papers = json.loads((OUT / "papers.json").read_text())
papers_led = [p for p in papers if p["in_ledger"]]
led_ids = {p["paper_id"] for p in papers_led}

# full ledger, all presets, doi -> record
full_ledger = {}
for f in LEDGER.glob("*.yml"):
    data = yaml.safe_load(f.read_text())
    doi = data.get("doi", "")
    full_ledger[doi] = data
    full_ledger[doi.lower()] = data

print(f"Full ledger entries (all presets): {len(full_ledger) // 2}")

selfcite = [e for e in entries if e["is_self_citation"] and e["paper_id"] in led_ids]
print(f"Self-citation instances (from ledger-matched papers): {len(selfcite)}")

resolved = 0
unresolved = []
for e in selfcite:
    doi = (e.get("doi") or "").strip()
    if not doi:
        # try key -> doi reconstruction: slop-xxxxxx key, no explicit doi field
        unresolved.append(e)
        continue
    if doi.lower() in full_ledger:
        resolved += 1
    else:
        unresolved.append(e)

print(
    f"Self-citation DOIs resolving to a real ledger entry (any preset): {resolved} / {len(selfcite)} "
    f"({resolved / len(selfcite) * 100:.1f}%)"
)
if unresolved:
    print("Unresolved self-citations:")
    for e in unresolved[:20]:
        print(
            f"  paper={e['paper_id']} key={e['key']} doi={e.get('doi')!r} title={e.get('title', '')[:60]}"
        )

# preset breakdown of cited self-works
preset_counts = defaultdict(int)
for e in selfcite:
    doi = (e.get("doi") or "").strip().lower()
    rec = full_ledger.get(doi)
    if rec:
        preset_counts[rec.get("preset", "?")] += 1
print("\nSelf-citations by preset of the CITED work:")
for k, v in sorted(preset_counts.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

# build slug->slug graph among ledger-matched papers (paper preset only, since
# that's our extracted-bib population) to look for chains
slug_of_paper_id = {p["paper_id"]: p["slug"] for p in papers_led}
doi_to_slug = {}
for p in papers_led:
    doi_to_slug[p["ledger_doi"].lower()] = p["slug"]

edges = defaultdict(set)  # citing_slug -> set(cited_slug)
for e in selfcite:
    doi = (e.get("doi") or "").strip().lower()
    citing = e["paper_id"]
    cited_slug = doi_to_slug.get(doi)
    if cited_slug:
        edges[citing].add(cited_slug)

print(
    f"\nCiting papers with >=1 self-citation target that is ITSELF one of our 199 paper-preset papers: {len(edges)}"
)

# find chains: A -> B -> C where B is both a citer and a citee
citer_slugs = set(edges.keys())
citee_slugs = set(s for v in edges.values() for s in v)
chain_nodes = citer_slugs & citee_slugs
print(
    f"Papers that are BOTH citing and cited (internal to the paper-preset self-citation graph): {len(chain_nodes)}"
)

chains = []
for a, bs in edges.items():
    for b in bs:
        if b in edges:
            for c in edges[b]:
                chains.append((a, b, c))
print(f"3-hop chains (A cites B, B cites C) found: {len(chains)}")
for a, b, c in chains[:15]:
    print(f"  {a} -> {b} -> {c}")

(OUT / "selfcite_graph.json").write_text(
    json.dumps(
        {
            "edges": {k: sorted(v) for k, v in edges.items()},
            "chains": chains,
        },
        indent=2,
    )
)
