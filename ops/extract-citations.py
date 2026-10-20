#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6", "typer"]
# ///
"""Harvest the canon's internal citation graph from published source files.

Every generated document is compiled from a `.typ` (plus a companion `.bib` for
the paper preset) under a checkout's gitignored `output/`, and every video
output from its committed `video/<id>/spec.json`. Where those sources
name a prior output's DOI --- a paper's bibliography entry, a poster's "prior
work" line --- that is a real citation edge, and it is the only citation data
the canon has. This script reads the edges out of the sources and records them
on the citing entry as `cites:`, so the site can derive citation counts, "cited
by" lists, and h-indices at build time from committed content alone.

The sources are local-only and gitignored, and the press worktree's `output/`
can be cleaned at any time: an edge not harvested into the ledger is an edge
lost. The publish wrapper therefore runs this per tick (`--id`), and `--all`
re-harvests the whole corpus from whatever sources survive locally. Both modes
are idempotent and additive: a `cites:` block already in the ledger is merged
with, never truncated by, a run whose sources have since disappeared.

Edges are deduplicated per citing document (one document citing one target is
one citation, however many times its `.bib` repeats the DOI), self-edges are
dropped, and an edge is kept only when both ends resolve to a ledger entry and
the cited output does not postdate the citing one.

Usage:
  ops/extract-citations.py --all [--write]     # backfill the whole ledger
  ops/extract-citations.py --id ENTRY [--write]  # one just-published entry
  ops/extract-citations.py --suggest [N]       # what a fresh run should cite
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Annotated

import typer
import yaml

REPO = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = REPO / "website" / "src" / "content" / "outputs"

# Compiled sources live in whichever checkouts exist side by side: the main
# tree and the press worktree the lander runs in (see ops/publish-land.sh).
# The script runs from either, so it names both rather
# than assuming which one it is --- deduplicated, since from inside the press
# worktree the sibling lookup resolves back onto itself.
SOURCE_DIRS = list(
    dict.fromkeys(
        [
            REPO / "output",
            REPO.parent / "slop-university" / "output",
            REPO.parent / "slop-university-press" / "output",
        ]
    )
)

VIDEO_DIR = REPO / "video"
DOI_RE = re.compile(r"10\.5555/slop\.([a-z0-9]+)")
SLUG_RE = re.compile(r"-([a-z0-9]{6})\.(?:typ|bib)$")


def ledger() -> dict[str, dict]:
    """Every published entry, keyed by entry id."""
    return {
        yml.stem: yaml.safe_load(yml.read_text()) or {}
        for yml in sorted(OUTPUTS_DIR.glob("*.yml"))
    }


def harvest(entries: dict[str, dict]) -> tuple[dict[str, set[str]], list[str]]:
    """Scan local sources for DOI mentions; return citing id → cited DOIs."""
    id_by_slug = {
        doi.rsplit(".", 1)[-1]: entry_id
        for entry_id, data in entries.items()
        if (doi := data.get("doi"))
    }
    dated = {entry_id: as_date(data.get("date")) for entry_id, data in entries.items()}

    edges: dict[str, set[str]] = defaultdict(set)
    notes: list[str] = []
    unpublished: set[str] = set()

    for source_dir in SOURCE_DIRS:
        if not source_dir.is_dir():
            notes.append(f"source dir absent, skipped: {source_dir}")
            continue
        for path in sorted([*source_dir.glob("*.typ"), *source_dir.glob("*.bib")]):
            slug = SLUG_RE.search(path.name)
            if slug is None:
                continue
            citing = id_by_slug.get(slug.group(1))
            if citing is None:
                unpublished.add(path.stem)  # a draft or withdrawn run
                continue
            for cited_slug in set(DOI_RE.findall(path.read_text(errors="replace"))):
                cited = id_by_slug.get(cited_slug)
                if cited is None:
                    notes.append(
                        f"{path.name} cites 10.5555/slop.{cited_slug}, not in the ledger"
                    )
                    continue
                if cited == citing:
                    continue
                if (a := dated[citing]) and (b := dated[cited]) and b > a:
                    notes.append(
                        f"{citing} cites {cited}, which postdates it --- dropped"
                    )
                    continue
                edges[citing].add(entries[cited]["doi"])

    # A video output's compiled source is its spec (video/<id>/spec.json,
    # committed): the output it explains and every output it shows are cited.
    for spec_path in sorted(VIDEO_DIR.glob("*/spec.json")):
        citing = spec_path.parent.name
        if citing not in entries:
            continue
        for cited in video_refs(json.loads(spec_path.read_text())):
            if cited == citing or cited not in entries:
                continue
            if (a := dated[citing]) and (b := dated[cited]) and b > a:
                continue
            edges[citing].add(entries[cited]["doi"])

    if unpublished:
        notes.append(
            f"{len(unpublished)} local source(s) with no ledger entry (drafts), ignored"
        )
    return edges, notes


def video_refs(spec: dict) -> set[str]:
    """The output ids a video spec explains or shows."""
    found = {spec["output"]} if spec.get("output") else set()

    def walk(x) -> None:
        if isinstance(x, dict):
            if x.get("type") == "pages":
                found.update(x.get("outputs", []))
            for key in ("output", "thumb"):
                if isinstance(x.get(key), str):
                    found.add(x[key])
            if isinstance(x.get("page"), list):
                found.add(x["page"][0])
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(spec.get("beats", []))
    return found


def as_date(value) -> date | None:
    return value if isinstance(value, date) else None


def write_cites(yml: Path, dois: list[str]) -> None:
    """Replace (or append) the entry's `cites:` block, leaving the rest byte-identical."""
    text = yml.read_text()
    block = "cites:\n" + "".join(f"  - {doi}\n" for doi in dois)
    existing = re.search(r"^cites:\n(?:  - .*\n)*", text, re.MULTILINE)
    if existing:
        text = text[: existing.start()] + block + text[existing.end() :]
    else:
        text = text.rstrip("\n") + "\n" + block
    yml.write_text(text)


def h_index(counts: list[int]) -> int:
    """Largest h such that h outputs are cited at least h times each."""
    ordered = sorted(counts, reverse=True)
    h = 0
    while h < len(ordered) and ordered[h] >= h + 1:
        h += 1
    return h


def suggest(entries: dict[str, dict], count: int) -> list[str]:
    """Rank prior outputs by how much a fresh citation would lift the roster.

    The University's citation policy is that a document's reference list should
    do institutional work. Raising a researcher from h to h+1 means getting
    h+1 of their outputs to h+1 citations each: the work is the shortfall
    across their top h+1 outputs, which is a handful of outputs each needing
    one, two, or three more. Those are what this ranks --- cheapest shortfall
    first, and outputs several researchers are all short on before outputs only
    one of them needs.

    Ranking only the one-short outputs (an earlier cut of this) stalls the
    moment a researcher runs out of them, which is why the deficit is computed
    against the whole rung. Which of these a document actually cites remains a
    judgement about topical fit: a reference to an unrelated study is a hollow
    edge, and the corpus reads as gamed rather than generous.
    """
    citations: dict[str, int] = defaultdict(int)
    doi_to_id = {
        data["doi"]: entry_id for entry_id, data in entries.items() if data.get("doi")
    }
    for data in entries.values():
        for doi in data.get("cites") or []:
            if doi in doi_to_id:
                citations[doi_to_id[doi]] += 1

    outputs_by_author: dict[str, list[str]] = defaultdict(list)
    for entry_id, data in entries.items():
        for author in data.get("authors") or []:
            outputs_by_author[author].append(entry_id)

    # For each researcher: the next rung, and the shortfall on each of the
    # outputs that would have to reach it.
    lifts: dict[str, list[str]] = defaultdict(list)
    deficit: dict[str, int] = {}
    for author, owned in outputs_by_author.items():
        rung = h_index([citations[e] for e in owned]) + 1
        climbing = sorted(owned, key=lambda e: -citations[e])[:rung]
        for entry_id in climbing:
            short = rung - citations[entry_id]
            if short <= 0:
                continue
            lifts[entry_id].append(author)
            deficit[entry_id] = min(deficit.get(entry_id, short), short)

    ranked = sorted(
        lifts.items(),
        key=lambda kv: (-len(kv[1]), deficit[kv[0]], entries[kv[0]]["title"]),
    )
    lines = []
    for entry_id, authors in ranked[:count]:
        data = entries[entry_id]
        short = deficit[entry_id]
        lines.append(
            f"{data['doi']}  {data['title']}\n"
            f"    cited {citations[entry_id]}× · {short} short of the next rung"
            f" · lifts {', '.join(sorted(authors))}\n"
            f"    {data.get('topic', '').strip()}"
        )
    return lines


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)

SUGGEST_DEFAULT = 30


@app.command(help=__doc__)
def main(
    all_: Annotated[
        bool, typer.Option("--all", help="re-harvest the whole ledger")
    ] = False,
    id_: Annotated[
        str | None,
        typer.Option("--id", help="harvest one entry (the just-published tick)"),
    ] = None,
    suggest_n: Annotated[
        int | None,
        typer.Option(
            "--suggest",
            metavar="[N]",
            help="list prior outputs a citation would lift onto the next h-index rung"
            f" (N defaults to {SUGGEST_DEFAULT})",
        ),
    ] = None,
    write: Annotated[
        bool, typer.Option("--write", help="write cites: into the ledger")
    ] = False,
) -> None:
    if [all_, id_ is not None, suggest_n is not None].count(True) != 1:
        print("exactly one of --all, --id, --suggest is required", file=sys.stderr)
        raise typer.Exit(2)

    entries = ledger()

    if suggest_n:
        for line in suggest(entries, suggest_n):
            print(line)
        return

    if id_ and id_ not in entries:
        print(f"no ledger entry: {id_}", file=sys.stderr)
        raise typer.Exit(1)

    edges, notes = harvest(entries)
    scope = [id_] if id_ else sorted(entries)

    written = 0
    total = 0
    for entry_id in scope:
        # Union with what the ledger already holds: sources are ephemeral, the
        # recorded edge is the durable one.
        merged = sorted(
            set(entries[entry_id].get("cites") or []) | edges.get(entry_id, set())
        )
        total += len(merged)
        if merged != (entries[entry_id].get("cites") or []):
            if write:
                write_cites(OUTPUTS_DIR / f"{entry_id}.yml", merged)
            written += 1

    for note in notes:
        print(f"  note: {note}")
    verb = "wrote" if write else "would write"
    print(
        f"{verb} cites: on {written} entr{'y' if written == 1 else 'ies'} ({total} edges in scope)"
    )
    if not write:
        print("dry run --- pass --write to record")


def bare_suggest_default(argv: list[str]) -> list[str]:
    """Give a bare `--suggest` (no N) its default, as the optional value it was."""
    out: list[str] = []
    for i, arg in enumerate(argv):
        out.append(arg)
        nxt = argv[i + 1] if i + 1 < len(argv) else None
        if arg == "--suggest" and (
            nxt is None or (nxt.startswith("-") and not re.fullmatch(r"-\d+", nxt))
        ):
            out.append(str(SUGGEST_DEFAULT))
    return out


if __name__ == "__main__":
    app(args=bare_suggest_default(sys.argv[1:]))
