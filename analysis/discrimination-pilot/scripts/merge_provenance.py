#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Merge the per-region corpus shards into corpus/provenance.json.

The gathering pass (TASK-006) runs one agent per region, each writing its own
shard under `corpus/incoming/` so that concurrent writers never collide. This
folds them into one record, drops rows whose PDF is no longer on disk, refuses
duplicate files, and prints the breadth breakdown the task asks for.

    uv run --script scripts/merge_provenance.py          # report + write
    uv run --script scripts/merge_provenance.py --check  # report only
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "corpus" / "raw"
INCOMING = ROOT / "corpus" / "incoming"
OUT = ROOT / "corpus" / "provenance.json"

# TASK-006 expands the strategy side. The impact documents are the first run's,
# re-fetched and re-verified rather than re-gathered, and they live in their own
# shard so that this split stays visible in the data instead of being a rule
# somewhere in a script.
IMPACT_SHARD = "impact"

# TASK-011 adds a second held-apart shard. These are ordinary strategic plans
# fetched to pair with a vision document from the SAME institution, so that the
# vision-document effect can be tested with house style controlled by
# construction. They are deliberately kept out of `real_strategy`: the headline
# discrimination sample is drawn from the corpus declared final at 164
# documents, and folding five institution-matched extras into it would change
# the headline table as a side effect of a sub-study.
PAIRS_SHARD = "vision-pairs"

FABRICATED_NOTE = {
    "note": (
        "Read-only from the slop-university repos; nothing in them was modified. "
        "Outputs are gitignored and local-only, so they are identified by filename "
        "rather than by URL."
    ),
    "sources": [
        "~/projects/slop-university/output/pdf/strategy/*.pdf (26: 23 anu2026-* ANU-branded, 3 slop-strategy-*)",
        "~/projects/slop-university/output/pdf/impact-report/*.pdf (8)",
        "~/projects/slop-university-press/output/pdf/strategy/*.pdf (4)",
        "~/projects/slop-university-press/output/pdf/impact-report/*.pdf (5)",
    ],
}


def load_shards() -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    warnings: list[str] = []
    seen: dict[str, str] = {}

    for shard in sorted(INCOMING.glob("*.json")):
        for row in json.loads(shard.read_text()):
            name = row["file"]
            if name in seen:
                warnings.append(
                    f"duplicate {name}: {seen[name]} and {shard.name} --- kept first"
                )
                continue
            if not (RAW / name).exists():
                warnings.append(f"missing PDF for {name} (in {shard.name}) --- dropped")
                continue
            seen[name] = shard.name
            rows.append({**row, "shard": shard.stem})

    orphans = {p.name for p in RAW.glob("*.pdf")} - set(seen)
    warnings.extend(f"PDF on disk with no provenance row: {n}" for n in sorted(orphans))
    return rows, warnings


def report(rows: list[dict]) -> None:
    def tally(field: str) -> str:
        counts = Counter(r.get(field, "?") for r in rows)
        return ", ".join(f"{k} {v}" for k, v in counts.most_common())

    institutions = {r["institution"] for r in rows}
    years = sorted(r["year"] for r in rows if r.get("year"))

    print(f"{len(rows)} documents, {len(institutions)} institutions")
    print(f"  country   : {tally('country')}")
    print(f"  tier      : {tally('tier')}")
    print(f"  doc_type  : {tally('doc_type')}")
    if years:
        print(f"  year      : {years[0]}-{years[-1]} ({tally('year')})")
    print(
        f"  words     : {sum(r.get('words', 0) for r in rows):,} total, "
        f"{sum(r.get('words', 0) for r in rows) // max(len(rows), 1):,} mean"
    )


def main() -> None:
    check_only = "--check" in sys.argv
    all_rows, warnings = load_shards()
    all_rows.sort(
        key=lambda r: (r.get("country", ""), r["institution"], r.get("year", 0))
    )

    held_apart = {IMPACT_SHARD, PAIRS_SHARD}
    rows = [r for r in all_rows if r["shard"] not in held_apart]
    impact = [r for r in all_rows if r["shard"] == IMPACT_SHARD]
    pairs = [r for r in all_rows if r["shard"] == PAIRS_SHARD]

    report(rows)
    print(f"  (plus {len(impact)} impact-condition documents)")
    print(
        f"  (plus {len(pairs)} vision-pair documents, held out of the headline sample)"
    )
    if warnings:
        print(f"\n{len(warnings)} warning(s):")
        for w in warnings:
            print(f"  ! {w}")

    if check_only:
        return

    OUT.write_text(
        json.dumps(
            {
                "collected": "2026-08-01",
                "note": (
                    "Real-side documents downloaded from the open web for the "
                    "discrimination pilot's expanded corpus (TASK-006), gathered by "
                    "region and merged from corpus/incoming/. Every document was "
                    "verified as a text-bearing PDF of at least 6 pages and 1200 "
                    "extractable words. US documents are included this time rather "
                    "than excluded: orthography is normalised in the stimulus "
                    "pipeline rather than handled by dropping a country."
                ),
                "real_strategy": rows,
                "real_impact": impact,
                "real_vision_pairs": pairs,
                "fabricated": FABRICATED_NOTE,
            },
            indent=1,
            ensure_ascii=False,
        )
        + "\n"
    )
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
