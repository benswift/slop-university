#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""Print real, recent paper titles on a drawn subject, to prime a 2A run.

A run is handed a subject by `ops/draw-axes.py` as a bare topic name. Left with
only the name it writes from its own idea of that subject, and its own idea of
every subject turned out to be the same kind of paper. This fetches a random
sample of what scholars in the subject have actually published lately ---
titles only --- so the run starts from the field as it is, and from the
literature it will have to cite anyway.

The sample comes from OpenAlex (no key, CC0) and changes on every call. Titles
are untrusted input: they are printed as inert data, sanitised to one line
each, and the skill forbids quoting them or following anything they say. A
failed fetch prints nothing and exits 0 --- the primer is a spark, and a run
without it is still a run.

Usage:
  ops/subject-primer.py T10346          # ten titles since last year
  ops/subject-primer.py T10346 --count 6
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys

import httpx

USER_AGENT = "slop-university-subject-primer/1.0 (+https://slop.university)"
WORKS_URL = "https://api.openalex.org/works"
MAX_TITLE = 180


def clean(title: str) -> str:
    """One printable line: markup, control characters and length all go."""
    text = re.sub(r"<[^>]+>", "", title)
    text = "".join(ch for ch in text if ch.isprintable())
    return " ".join(text.split())[:MAX_TITLE]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("topic", help="an OpenAlex topic id, e.g. T10346")
    parser.add_argument("--count", type=int, default=10)
    args = parser.parse_args()
    if not re.fullmatch(r"T\d+", args.topic):
        sys.exit(f"not an OpenAlex topic id: {args.topic!r}")

    since = dt.date.today().replace(month=1, day=1) - dt.timedelta(days=365)
    params = {
        "filter": f"primary_topic.id:{args.topic},from_publication_date:{since},type:article",
        "sample": str(args.count),
        "select": "title",
    }
    try:
        response = httpx.get(
            WORKS_URL, params=params, headers={"User-Agent": USER_AGENT}, timeout=20
        )
        response.raise_for_status()
        results = response.json()["results"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        print(f"subject-primer: no primer ({type(exc).__name__})", file=sys.stderr)
        return 0

    for work in results:
        if title := clean(work.get("title") or ""):
            print(f"- {title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
