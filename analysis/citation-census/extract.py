#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "bibtexparser==1.4.4"]
# ///
"""
Extraction pass for the Slop University citation-borrowing census.

Walks every slop-paper-*.bib file in the two local output/ checkouts,
parses each BibTeX entry, joins the paper (by its 6-char slug) against
the published ledger (website/src/content/outputs/*.yml, preset: paper),
and writes two JSON files:

  entries.json  - one row per (paper, citation) pair
  papers.json   - one row per paper (ledger-matched + local-only)

Run: uv run extract.py
"""

import json
import re
from pathlib import Path

import bibtexparser
import yaml

PRESS = Path.home() / "projects/slop-university-press/output"
MAIN = Path.home() / "projects/slop-university/output"
LEDGER = Path.home() / "projects/slop-university/website/src/content/outputs"
OUT = Path(__file__).parent

SLUG_RE = re.compile(r"-([a-z0-9]{6})$")


def slug_from_stem(stem: str) -> str | None:
    m = SLUG_RE.search(stem)
    return m.group(1) if m else None


def load_ledger() -> dict[str, dict]:
    """slug -> ledger record, for preset: paper entries only."""
    out = {}
    for f in LEDGER.glob("*.yml"):
        data = yaml.safe_load(f.read_text())
        if data.get("preset") != "paper":
            continue
        doi = data.get("doi", "")
        m = re.search(r"slop\.([a-z0-9]{6})$", doi)
        if not m:
            continue
        slug = m.group(1)
        data["_slug"] = slug
        data["_ledger_file"] = f.name
        out[slug] = data
    return out


def find_bib_files() -> list[Path]:
    files = list(PRESS.glob("slop-paper-*.bib")) + list(MAIN.glob("slop-paper-*.bib"))
    return sorted(files)


def parse_bib(path: Path) -> list[dict]:
    bib_db = bibtexparser.load(path.open())
    rows = []
    for e in bib_db.entries:
        rows.append(
            {
                "key": e.get("ID"),
                "entry_type": e.get("ENTRYTYPE"),
                "author": e.get("author", ""),
                "title": e.get("title", "").strip("{}"),
                "year": e.get("year", ""),
                "journal": e.get("journal", ""),
                "booktitle": e.get("booktitle", ""),
                "publisher": e.get("publisher", ""),
                "doi": e.get("doi", "").strip().lower(),
                "volume": e.get("volume", ""),
                "number": e.get("number", ""),
                "pages": e.get("pages", ""),
                "eprint": e.get("eprint", ""),
                "archiveprefix": e.get("archiveprefix", ""),
                "primaryclass": e.get("primaryclass", ""),
            }
        )
    return rows


def main():
    ledger = load_ledger()
    print(f"Ledger paper entries: {len(ledger)}")

    bib_files = find_bib_files()
    print(f"Local slop-paper .bib files found: {len(bib_files)}")

    papers = []
    entries = []
    matched = 0
    unmatched_slugs = []

    for bf in bib_files:
        slug = slug_from_stem(bf.stem)
        repo = "press" if PRESS in bf.parents else "main"
        led = ledger.get(slug)
        paper_id = slug or bf.stem
        paper_rec = {
            "paper_id": paper_id,
            "slug": slug,
            "bib_path": str(bf),
            "repo": repo,
            "in_ledger": led is not None,
        }
        if led:
            matched += 1
            paper_rec.update(
                {
                    "ledger_title": led.get("title"),
                    "ledger_authors": led.get("authors"),
                    "ledger_school": led.get("school"),
                    "ledger_date": str(led.get("date")),
                    "ledger_doi": led.get("doi"),
                }
            )
        else:
            unmatched_slugs.append(slug)

        try:
            rows = parse_bib(bf)
        except Exception as ex:
            print(f"PARSE FAIL {bf}: {ex}")
            rows = []

        paper_rec["n_references"] = len(rows)
        papers.append(paper_rec)

        for r in rows:
            r["paper_id"] = paper_id
            r["paper_in_ledger"] = led is not None
            r["is_self_citation"] = bool(
                r["key"] and r["key"].startswith("slop-")
            ) or "10.5555/slop." in (r["doi"] or "")
            entries.append(r)

    print(f"Papers matched to ledger: {matched} / {len(bib_files)}")
    print(
        f"Local-only (not in ledger, likely drafts): {len(unmatched_slugs)} -> {unmatched_slugs}"
    )
    print(f"Total reference rows extracted: {len(entries)}")

    (OUT / "papers.json").write_text(json.dumps(papers, indent=2))
    (OUT / "entries.json").write_text(json.dumps(entries, indent=2))
    print(f"Wrote {OUT / 'papers.json'} and {OUT / 'entries.json'}")


if __name__ == "__main__":
    main()
