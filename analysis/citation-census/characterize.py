#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""
Characterization pass: publication years, venues/publishers, rough
disciplinary split (ML/AI vs other), and most-cited authors, over the
external (non-self) citation instances for the 199 ledger-matched papers.
"""

import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).parent
entries = json.loads((OUT / "entries.json").read_text())
papers = json.loads((OUT / "papers.json").read_text())
led_ids = {p["paper_id"] for p in papers if p["in_ledger"]}
ext = [e for e in entries if e["paper_id"] in led_ids and not e["is_self_citation"]]

# --- years ---
years = []
for e in ext:
    y = e.get("year", "")
    m = re.match(r"(\d{4})", y or "")
    if m:
        years.append(int(m.group(1)))
print(f"=== Publication years (external, n={len(years)}) ===")
print(f"range: {min(years)}-{max(years)}")
print(f"median: {sorted(years)[len(years) // 2]}")
decade_counts = Counter((y // 10) * 10 for y in years)
for d in sorted(decade_counts):
    print(f"  {d}s: {decade_counts[d]}")
print(
    "Last 10 years (2016-2026):",
    sum(1 for y in years if y >= 2016),
    f"({sum(1 for y in years if y >= 2016) / len(years) * 100:.1f}%)",
)

# --- venues (journal / booktitle) ---
venues = Counter()
for e in ext:
    v = e.get("journal") or e.get("booktitle") or e.get("publisher") or "(unknown)"
    v = re.sub(r"arXiv preprint arXiv:[\d.]+.*", "arXiv preprint", v)
    venues[v] += 1
print(
    f"\n=== Top 25 venues (journal/booktitle/publisher field, n={len(ext)} instances) ==="
)
for v, c in venues.most_common(25):
    print(f"  {c:4d}  {v[:80]}")

arxiv_n = sum(c for v, c in venues.items() if "arxiv" in v.lower())
print(
    f"\narXiv-preprint-labelled instances: {arxiv_n} ({arxiv_n / len(ext) * 100:.1f}%)"
)

# --- rough discipline classification via keyword heuristic on venue+title ---
AI_KW = [
    "arxiv",
    "neurips",
    "icml",
    "iclr",
    "acl",
    "emnlp",
    "aaai",
    "ijcai",
    "cvpr",
    "machine learning",
    "artificial intelligence",
    "neural",
    "deep learning",
    "language model",
    "nlp",
    "computer vision",
    "reinforcement learning",
    "chi conference",
    "human factors in computing",
    "acm",
    "ieee",
    "uist",
    "human-computer interaction",
    "hci",
]
CS_ADJACENT = [
    "ieee",
    "acm",
    "computer",
    "computing",
    "software",
    "algorithm",
    "data mining",
    "sigkdd",
    "www conference",
]


def classify(e):
    blob = " ".join(
        [
            e.get("journal", ""),
            e.get("booktitle", ""),
            e.get("title", ""),
            e.get("publisher", ""),
        ]
    ).lower()
    if any(k in blob for k in AI_KW):
        return "AI/ML/HCI/CS"
    if any(k in blob for k in CS_ADJACENT):
        return "CS-adjacent (other)"
    return "other field"


disc = Counter(classify(e) for e in ext)
print(f"\n=== Rough disciplinary split (keyword heuristic, n={len(ext)}) ===")
for k, v in disc.most_common():
    print(f"  {k}: {v} ({v / len(ext) * 100:.1f}%)")


# --- most-cited authors (first author surname, rough) ---
def first_author_surname(author_field):
    if not author_field:
        return None
    first = re.split(r"\s+and\s+", author_field)[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    parts = first.split()
    return parts[-1] if parts else None


author_counter = Counter()
for e in ext:
    a = first_author_surname(e.get("author", ""))
    if a:
        author_counter[a] += 1
print(f"\n=== Top 20 first-authors by citation instance count (external) ===")
for a, c in author_counter.most_common(20):
    print(f"  {c:4d}  {a}")

# also: any author appearing across many DISTINCT papers-cited (i.e., prolific
# not just one heavily-repeated paper)
distinct = json.loads((OUT / "distinct_works.json").read_text())
author_distinct_counter = Counter()
for d in distinct:
    a = first_author_surname(d.get("author", ""))
    if a:
        author_distinct_counter[a] += 1
print(f"\n=== Top 15 first-authors by NUMBER OF DISTINCT WORKS cited ===")
for a, c in author_distinct_counter.most_common(15):
    print(f"  {c:4d}  {a}")
