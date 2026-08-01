#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Fetch one real-side corpus document, verify it, and record its provenance.

Used by the corpus-gathering pass for TASK-006. Every candidate goes through
the same checks so that a document only enters the corpus if it is a real,
text-bearing PDF of plausible length --- no scanned images, no HTML error
pages served with a .pdf name, no two-page executive summaries.

    uv run --script scripts/fetch_doc.py \
        --url https://example.edu/strategy.pdf \
        --file real-strategy-uk-lancaster.pdf \
        --title "Strategic Plan 2021-2026" \
        --institution "Lancaster University" \
        --country UK --tier mid --doc-type strategic-plan --year 2021 \
        --shard uk-england

Writes/updates `corpus/incoming/<shard>.json` and prints a one-line verdict.
Exit status is 0 on acceptance, 1 on rejection, so a caller can branch on it.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "corpus" / "raw"
INCOMING = ROOT / "corpus" / "incoming"

MIN_PAGES = 6
MIN_WORDS = 1200
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def fail(msg: str) -> None:
    print(f"REJECT {msg}")
    sys.exit(1)


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            "curl",
            "-sSL",
            "--max-time",
            "120",
            "--retry",
            "2",
            "-A",
            UA,
            "-o",
            str(dest),
            url,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        dest.unlink(missing_ok=True)
        fail(f"download failed: {proc.stderr.strip()[:200]}")


def verify(dest: Path) -> tuple[int, int, str]:
    """Return (pages, words, extracted_text) or exit non-zero."""
    kind = subprocess.run(
        ["file", "-b", str(dest)], capture_output=True, text=True
    ).stdout.strip()
    if "PDF" not in kind:
        dest.unlink(missing_ok=True)
        fail(f"not a PDF ({kind[:80]})")

    info = subprocess.run(["pdfinfo", str(dest)], capture_output=True, text=True).stdout
    m = re.search(r"^Pages:\s+(\d+)", info, re.M)
    pages = int(m.group(1)) if m else 0
    if pages < MIN_PAGES:
        dest.unlink(missing_ok=True)
        fail(f"only {pages} pages (min {MIN_PAGES})")

    text = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(dest), "-"],
        capture_output=True,
        text=True,
    ).stdout
    words = len(text.split())
    if words < MIN_WORDS:
        dest.unlink(missing_ok=True)
        fail(f"only {words} extractable words (min {MIN_WORDS}) --- scanned or empty?")

    return pages, words, text


def record(shard: str, entry: dict) -> None:
    INCOMING.mkdir(parents=True, exist_ok=True)
    path = INCOMING / f"{shard}.json"
    rows = json.loads(path.read_text()) if path.exists() else []
    rows = [r for r in rows if r["file"] != entry["file"]]
    rows.append(entry)
    path.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--file", required=True, help="target filename under corpus/raw/")
    p.add_argument("--title", required=True)
    p.add_argument("--institution", required=True)
    p.add_argument("--country", required=True)
    p.add_argument(
        "--tier",
        required=True,
        choices=["elite", "research", "mid", "regional", "specialist"],
    )
    p.add_argument(
        "--doc-type",
        required=True,
        choices=[
            "strategic-plan",
            "corporate-plan",
            "vision",
            "institutional-plan",
            "research-strategy",
            "annual-plan",
        ],
    )
    p.add_argument("--year", required=True, type=int)
    p.add_argument("--shard", required=True)
    args = p.parse_args()

    if not args.file.endswith(".pdf"):
        fail("--file must end in .pdf")

    dest = RAW / args.file
    download(args.url, dest)
    pages, words, _ = verify(dest)

    record(
        args.shard,
        {
            "file": args.file,
            "title": args.title,
            "institution": args.institution,
            "country": args.country,
            "tier": args.tier,
            "doc_type": args.doc_type,
            "year": args.year,
            "pages": pages,
            "words": words,
            "url": args.url,
            "retrieved": "2026-08-01",
        },
    )
    print(f"ACCEPT {args.file} ({pages}pp, {words}w)")


if __name__ == "__main__":
    main()
