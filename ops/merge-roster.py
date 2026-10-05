#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Git merge driver for canon/roster.yml: replay an admission as an append.

Admitting a researcher appends one entry to the end of the roster, and every
thesis admits its candidate. Theses are written several at a time, each on its
own branch off the same base, so when the lander replays the second one the
roster has already grown at the very line the candidate wants to append to ---
a textual conflict between two changes that have nothing to do with each
other. git's own `merge=union` is no answer: it merges the two appended
entries line by line and folds the lines they share (a title, a date) into
one, leaving entries with fields missing.

So this driver reads the roster as what it is, a header and a list of entries.
When the incoming side only APPENDED entries, they are appended to the current
side and the merge is clean. Anything else --- an edited bio, a changed header,
an id the current side already has --- goes to git's ordinary three-way text
merge, conflicts and all.

    ops/merge-roster.py <base> <current> <incoming>     # git's %O %A %B

The result is written over <current>; the exit status is non-zero on conflict.
.gitattributes names the driver and ops/publish-lib.sh defines it for the
pipeline's own git calls; a checkout without the definition gets the ordinary
text merge.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ENTRY = re.compile(r"^  - id: (\S+)", re.MULTILINE)


def split(text: str) -> tuple[str, list[str]]:
    """The roster as (everything before the first entry, [entry, ...])."""
    starts = [m.start() for m in ENTRY.finditer(text)]
    if not starts:
        return text, []
    return text[: starts[0]], [
        text[a:b] for a, b in zip(starts, [*starts[1:], len(text)])
    ]


def entry_id(entry: str) -> str:
    match = ENTRY.match(entry)
    assert match is not None
    return match.group(1)


def appended(base: str, incoming: str) -> list[str] | None:
    """The entries <incoming> added to the end of <base>, or None if it did more."""
    base_head, base_entries = split(base)
    head, entries = split(incoming)
    if not base_entries or head != base_head or len(entries) <= len(base_entries):
        return None
    # The last base entry gains a newline if the file had none at its end.
    kept = [e.rstrip("\n") for e in entries[: len(base_entries)]]
    if kept != [e.rstrip("\n") for e in base_entries]:
        return None
    return entries[len(base_entries) :]


def main() -> int:
    base, current, incoming = (Path(p) for p in sys.argv[1:4])
    new = appended(base.read_text(), incoming.read_text())
    ours = current.read_text()
    if new is not None:
        have = {entry_id(e) for e in split(ours)[1]}
        if not have & {entry_id(e) for e in new}:
            current.write_text(ours.rstrip("\n") + "\n" + "".join(new))
            return 0
    return subprocess.run(
        ["git", "merge-file", str(current), str(base), str(incoming)]
    ).returncode


if __name__ == "__main__":
    sys.exit(main())
