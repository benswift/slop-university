#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6", "typer"]
# ///
"""Pick the output a video run explains, outside the model.

    pick-explainer.py [--root DIR]          # {"output": id, "reason": ...} as JSON, or exit 3
    pick-explainer.py [--root DIR] --list   # the eligible pool, newest first

Left to choose, a run reaching for the most explainable output picks the same
kind every time, and two runs reading the same ledger pick the same one. So the
choice is drawn here, with OS randomness, from the outputs that can be
explained unattended:

- a paper, thesis or research poster (the presets explainers have been made
  of; a booklet's argument has no one finding to follow through);
- that no video entry names as its `output` yet;
- whose every author has a voice in canon/voices.yml, since a researcher
  speaks only in their own voice and the unattended run must not assign one
  (ops/assign-voices.py edits canon, which a run commits only by hand).

The draw takes the newest RECENT outputs first, so the screens show recent
work, and falls back to the whole pool once those are explained. Exit 3 means
nothing is eligible, which is a real answer, not an error.
"""

import json
import secrets
import sys
from pathlib import Path
from typing import Annotated

import typer
import yaml

PRESETS = {"paper", "thesis", "research-poster"}
RECENT = 40  # outputs, newest first


def pool(root: Path) -> list[dict]:
    content = root / "website" / "src" / "content"
    explained = {
        (yaml.safe_load(f.read_text()) or {}).get("output")
        for f in (content / "videos").glob("*.yml")
    }
    roster = yaml.safe_load((root / "canon" / "roster.yml").read_text())["researchers"]
    ids = {p["name"]: p["id"] for p in roster}
    voices = yaml.safe_load((root / "canon" / "voices.yml").read_text()) or {}
    found = []
    for f in (content / "outputs").glob("*.yml"):
        entry = yaml.safe_load(f.read_text())
        if entry.get("preset") not in PRESETS or f.stem in explained:
            continue
        authors = entry.get("authors") or []
        if not authors or not all(ids.get(a) in voices for a in authors):
            continue
        found.append(
            {
                "output": f.stem,
                "preset": entry["preset"],
                "authors": [ids[a] for a in authors],
                "publishedAt": str(entry.get("publishedAt", entry.get("date", ""))),
            }
        )
    return sorted(found, key=lambda e: e["publishedAt"], reverse=True)


def main(
    root: Annotated[Path, typer.Option(help="the checkout to read")] = Path("."),
    list_: Annotated[
        bool, typer.Option("--list", help="print the eligible pool")
    ] = False,
) -> None:
    eligible = pool(root)
    if list_:
        for e in eligible:
            print(f"{e['publishedAt'][:10]}  {e['preset']:<15} {e['output']}")
        print(f"{len(eligible)} eligible", file=sys.stderr)
        return
    if not eligible:
        print(
            json.dumps(
                {"output": None, "reason": "no output is eligible for an explainer"}
            )
        )
        raise typer.Exit(3)
    recent = eligible[:RECENT]
    pick = recent[secrets.randbelow(len(recent))]
    print(
        json.dumps(
            {
                "output": pick["output"],
                "authors": pick["authors"],
                "reason": f"drawn from the {len(recent)} newest of {len(eligible)} unexplained {'/'.join(sorted(PRESETS))} outputs whose authors all have voices",
            }
        )
    )


if __name__ == "__main__":
    typer.run(main)
