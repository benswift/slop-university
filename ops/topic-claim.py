#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Claim a 2A topic before generating it, so two runs can't compose the same one.

The skill's dedup check reads the outputs ledger, which is the canonical record
of what has been PUBLISHED. It cannot see what another run is composing right
now, and it cannot see what this run itself composed and threw away. Both gaps
cost whole generation runs: on 1 August a poster was fully generated --- images,
charts, both themes --- before the agent noticed the topic duplicated an entry
from 29 July, and the entire run was discarded. A claim taken BEFORE generation
turns that from a wasted twenty minutes into a re-roll that costs nothing.

Today the wrapper serialises ticks, so the only claims in flight are this run's
own. The file earns its keep anyway (a claim survives the run that took it, so
a re-roll after a discard cannot circle back to the discarded topic), and it is
the prerequisite for running 2A slots concurrently --- at which point it becomes
the only thing standing between two slots and the same subject.

Claims live in data/topic-claims.json, beside the other gitignored handoff
artefacts, and data/ is canonical in the main checkout (the press worktree's is
a symlink to it), so every slot sees one file no matter where it runs.

Matching is deliberately loose. Two runs describing the same subject will not
phrase it identically, so a claim collides when the candidate's content words
overlap an existing claim's by OVERLAP_THRESHOLD of the smaller set --- with a
floor of MIN_SHARED_TOKENS so two three-word topics can't collide on one
coincidental noun. False positives cost a re-roll; false negatives cost a
duplicate output. Prefer the re-roll.

Claims expire after TTL_HOURS, well beyond the longest observed run (~25 min),
so a crashed run releases its topic without anyone intervening.

Usage:
  ops/topic-claim.py claim "<topic>"   # exit 0 = yours, 1 = someone has it
  ops/topic-claim.py release "<topic>" # give it back after a discarded run
  ops/topic-claim.py list              # show live claims (debugging)
"""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import re
import sys
from pathlib import Path

CLAIMS_PATH = Path("data/topic-claims.json")
LOCK_PATH = Path("data/topic-claims.lock")

TTL_HOURS = 3
# Tuned against the 1 August collision this script exists to prevent ("a
# reminder trial on junior-sport canteen duty rosters" against the published
# "the same eleven households keep turning up on the junior sport canteen
# roster"), which shares four content words out of seven --- 0.57. A stricter
# threshold would have let exactly the run we are trying to save through.
OVERLAP_THRESHOLD = 0.5
MIN_SHARED_TOKENS = 3

# Register words, not subject matter. A topic is a noun phrase about a concrete
# object ("a car wash's boom-gate plate scanner rations an unlimited
# membership"), so the words that distinguish one topic from another are the
# nouns --- these carry no signal and would inflate every overlap score.
STOPWORDS = frozenset(
    """
    a an and are as at be been but by for from has have how in into is it its
    of on or that the their there they this to was were what when where which
    who why will with about after before between during over under
    study studies research paper poster analysis approach method framework
    university school new using use used across within
    """.split()
)


def stem(word: str) -> str:
    """Fold regular plurals so "rosters" matches "roster". Crude on purpose ---
    it only has to be CONSISTENT, since both sides of every comparison go
    through it, and a real stemmer would be a dependency for no gain. The
    length guard keeps short words ("bus", "gas") from being filed to stubs."""
    for suffix, replacement in (("ies", "y"), ("sses", "ss"), ("s", "")):
        if word.endswith(suffix) and len(word) - len(suffix) + len(replacement) >= 3:
            return word[: -len(suffix)] + replacement
    return word


def tokens(topic: str) -> frozenset[str]:
    """Content words of a topic, lowercased, de-pluralised, stopwords dropped.

    Stopwords are matched against the STEM, not the raw word --- otherwise
    "methods" slips past a list containing "method" and then stems into it,
    leaving a register word counted as subject matter."""
    words = re.findall(r"[a-z]+", topic.lower())
    stems = (stem(w) for w in words if len(w) > 2)
    return frozenset(s for s in stems if s not in STOPWORDS and len(s) > 2)


def collides(a: frozenset[str], b: frozenset[str]) -> bool:
    """Overlap as a fraction of the SMALLER set, so a terse topic can still
    collide with a verbose one describing the same thing."""
    if not a or not b:
        return False
    shared = len(a & b)
    if shared < MIN_SHARED_TOKENS:
        return False
    return shared / min(len(a), len(b)) >= OVERLAP_THRESHOLD


def live_claims(now: dt.datetime) -> list[dict]:
    """Unexpired claims. Reads through a missing or malformed file rather than
    failing the run --- a lost claims file must not block publishing, and the
    ledger dedup is still there underneath."""
    if not CLAIMS_PATH.exists():
        return []
    try:
        claims = json.loads(CLAIMS_PATH.read_text())
    except json.JSONDecodeError:
        print("claims file unreadable; starting a fresh one", file=sys.stderr)
        return []
    cutoff = now - dt.timedelta(hours=TTL_HOURS)
    return [c for c in claims if dt.datetime.fromisoformat(c["claimed_at"]) > cutoff]


def write_claims(claims: list[dict]) -> None:
    CLAIMS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLAIMS_PATH.write_text(json.dumps(claims, indent=2) + "\n")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    command = sys.argv[1]

    if command == "list":
        for c in live_claims(dt.datetime.now(dt.UTC)):
            print(f"{c['claimed_at']}  {c['topic']}")
        return 0

    if command not in ("claim", "release") or len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    topic = " ".join(sys.argv[2:]).strip()
    if not topic:
        print("empty topic", file=sys.stderr)
        return 2

    # One lock over the whole read-modify-write: two slots calling `claim` at
    # the same moment must not both read "free" before either writes.
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        now = dt.datetime.now(dt.UTC)
        claims = live_claims(now)
        candidate = tokens(topic)

        if command == "release":
            kept = [c for c in claims if not collides(candidate, tokens(c["topic"]))]
            write_claims(kept)
            print(f"released {len(claims) - len(kept)} claim(s)")
            return 0

        for c in claims:
            if collides(candidate, tokens(c["topic"])):
                print(f"topic already claimed at {c['claimed_at']}: {c['topic']}")
                return 1

        claims.append({"topic": topic, "claimed_at": now.isoformat()})
        write_claims(claims)
        print(f"claimed: {topic}")
        return 0


if __name__ == "__main__":
    sys.exit(main())
