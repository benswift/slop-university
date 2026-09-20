#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Reject a generated `.typ` whose tables cannot fit the measure they sit in.

Two table defects ship silently --- typst reports neither, and the run's render
budget (`skills/publish/SKILL.md` › "Budgets") does not stretch to looking at
every table's page, so nothing else catches them.

**An `fr` column in a table.** A `fr` column is handed a share of the space
rather than sized to what is in it: with `auto` columns beside it, the share is
whatever they leave over, and with only other `fr`s it is a fixed fraction. Either
way it never grows to fit, so a word wider than the share prints on top of the
next column. `auto` columns negotiate instead --- typst shrinks them together and
wraps --- and an all-`auto` table cannot collide, at worst stopping short of the
right margin. That is why the rule is absolute rather than a judgement about
whether this table has slack: two tables of identical shape rendered one well
and one starved, and the difference was in the cells.

The rule is for tables only. `grid(columns: (1fr, 1fr))` lays out blocks, not
lines of text, and is left alone.

**Too many columns for the measure.** A paper's body column is ~73mm and a
thesis or booklet text block ~155mm; past the caps below, every column is
narrower than the words in it and each cell flows to five or six lines. A paper
table that needs more columns belongs in a `place(top, scope: "parent",
float: true, ...)`, which gives it the full ~155mm, so a table inside one is
checked against the wide cap.

The caps are rendered thresholds, not a style preference: at 155mm a six-column
table of numbers reads and a seven-column one with two prose columns did not; in
a paper's body column three is the limit. Sizing doctrine is in
`skills/_shared/typst-layout.md` › "Tables"; this script is its enforcement.

Usage:
  ops/check-table-fit.py --preset paper output/slop-paper-<slug>-<seed>.typ
  ops/check-table-fit.py --preset thesis output/slop-thesis-<slug>-<seed>/*.typ
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# preset -> (columns that fit the measure the body sets tables in, measure).
# Posters are absent deliberately: an A0 column is wide enough that no table a
# poster carries has ever been the problem, and their fit is probed already.
NARROW = 3  # a paper's body column, ~73mm
WIDE = 6  # a thesis or booklet text block, ~155mm
CAPS = {
    "paper": NARROW,
    "thesis": WIDE,
    "brochure": WIDE,
    "impact-report": WIDE,
    "strategy": WIDE,
}
# A paper table floated across both columns gets the wide measure.
SPAN_CAP = 6
SPAN = re.compile(r'place\s*\(\s*[^)]*scope:\s*"parent"')
# How far above a table to look for the float that carries it.
SPAN_LOOKBACK = 400

# `table(`, but not `table.cell(`, `table.header(` or a grid.
TABLE = re.compile(r"\btable\s*\(")
COLUMNS = re.compile(r"\bcolumns:\s*")


def column_spec(source: str, start: int) -> tuple[str, int] | None:
    """The text of the `columns:` value beginning at `start`, and its length."""
    rest = source[start:]
    if rest.startswith("("):
        depth = 0
        for i, ch in enumerate(rest):
            depth += (ch == "(") - (ch == ")")
            if depth == 0:
                return rest[: i + 1], i + 1
        return None
    end = rest.find(",")
    return (rest[:end], end) if end != -1 else None


def count_columns(spec: str) -> int | None:
    """How many columns the spec declares, or None if it cannot be read.

    `columns: 5` counts itself. A tuple counts its top-level commas, ignoring
    a trailing one and any comma inside a nested call."""
    spec = spec.strip()
    if spec.isdigit():
        return int(spec)
    if not spec.startswith("("):
        return None
    depth, columns, seen = 0, 0, False
    for ch in spec[1:-1]:
        depth += (ch == "(") - (ch == ")")
        if not ch.isspace():
            seen = True
        if ch == "," and depth == 0:
            columns += 1
            seen = False
    return columns + 1 if seen else columns


def table_spans(source: str) -> list[tuple[int, int]]:
    """(start, end) of every `table(...)` call's arguments."""
    spans = []
    for match in TABLE.finditer(source):
        depth = 0
        for i in range(match.end() - 1, len(source)):
            depth += (source[i] == "(") - (source[i] == ")")
            if depth == 0:
                spans.append((match.end(), i))
                break
    return spans


def findings(path: Path, cap: int) -> list[str]:
    source = path.read_text()
    out: list[str] = []
    for start, end in table_spans(source):
        match = COLUMNS.search(source, start, end)
        if match is None:
            continue
        found = column_spec(source, match.end())
        if found is None:
            continue
        spec, _ = found
        line = source.count("\n", 0, match.start()) + 1
        where = f"{path}:{line}"

        if re.search(r"\d\s*fr\b|\bfr\b", spec):
            out.append(
                f"{where}: a table column sized in fr ({' '.join(spec.split())}). "
                "An fr column is handed a share rather than sized to its content, "
                "so a word wider than the share prints over the next column. Size "
                "every column auto."
            )

        columns = count_columns(spec)
        if columns is None:
            continue
        limit = cap
        if cap == NARROW and SPAN.search(
            source[max(0, match.start() - SPAN_LOOKBACK) : match.start()]
        ):
            limit = SPAN_CAP
        if columns > limit:
            out.append(
                f"{where}: {columns} columns is more than the measure holds "
                f"(limit {limit}). Cut or merge columns, shorten the headers, or "
                "float the table across both columns with "
                '`place(top, scope: "parent", float: true, ...)`.'
            )
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", type=Path, nargs="+")
    parser.add_argument("--preset", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    cap = CAPS.get(args.preset)
    if cap is None:
        print(f"tables: {args.preset} sets no table in a narrow measure; skipped")
        return 0

    problems = [f for source in args.sources for f in findings(source, cap)]
    if problems:
        print("\n".join(problems))
        return 1
    print(f"tables: {len(args.sources)} source(s) clean at a {cap}-column limit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
