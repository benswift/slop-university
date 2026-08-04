#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Restore any corpus PDF listed in provenance.json but missing from disk.

The raw PDFs are not committed --- 114 documents is well over half a gigabyte,
and they are all published on the open web. The first run relied on that
reasoning too and lost the corpus: nothing re-downloaded them, so when the
working tree was cleaned only `provenance.json` survived and the whole real side
had to be rebuilt from its URLs by hand.

This is the missing half of that argument. Provenance plus a refetch script is a
reproducible corpus; provenance alone is a list of things you used to have.

    uv run --script scripts/refetch_corpus.py           # fetch what's missing
    uv run --script scripts/refetch_corpus.py --check   # just report

Link rot is expected on a corpus this size and this old: a document whose URL has
died is reported rather than silently dropped, so the loss is visible and can be
recorded in the provenance note.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "corpus" / "raw"
PROVENANCE = ROOT / "corpus" / "provenance.json"
FETCH = Path(__file__).resolve().parent / "fetch_doc.py"


def main() -> None:
    check_only = "--check" in sys.argv
    prov = json.loads(PROVENANCE.read_text())
    rows = (
        prov.get("real_strategy", [])
        + prov.get("real_impact", [])
        + prov.get("real_vision_pairs", [])
    )

    missing = [r for r in rows if not (RAW / r["file"]).exists()]
    print(
        f"{len(rows)} documents in provenance, {len(rows) - len(missing)} on disk, {len(missing)} missing"
    )

    if check_only or not missing:
        for r in missing:
            print(f"  - {r['file']}  {r['url']}")
        return

    failed = []
    for r in missing:
        if r["url"].startswith("local:"):
            print(f"  ! {r['file']} is a local file, not a URL --- restore it by hand")
            failed.append(r)
            continue
        proc = subprocess.run(
            [
                str(FETCH),
                "--url",
                r["url"],
                "--file",
                r["file"],
                "--title",
                r["title"],
                "--institution",
                r["institution"],
                "--country",
                r["country"],
                "--tier",
                r["tier"],
                "--doc-type",
                r["doc_type"],
                "--year",
                str(r["year"]),
                "--shard",
                r.get("shard", "refetch"),
            ],
            capture_output=True,
            text=True,
        )
        print(f"  {proc.stdout.strip() or proc.stderr.strip()[:120]}")
        if proc.returncode != 0:
            failed.append(r)

    if failed:
        print(f"\n{len(failed)} could not be restored --- link rot, or a login wall:")
        for r in failed:
            print(f"  - {r['institution']}: {r['url']}")


if __name__ == "__main__":
    main()
