#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""Retrieval side of the 2A dedup check, so the agent reads a shortlist, not the ledger.

The skill's dedup step (skills/publish/SKILL.md) has the agent read the topic
and summary of every `website/src/content/outputs/*.yml` entry --- 1150+ files
--- plus a random sample of twelve for the object-of-study check. That is a
large context read on every run, done purely to surface candidates a human (or
agent) then judges by hand. This script does the retrieval: a cosine
similarity over the corpus for the topic check, a uniform random sample for the
object check, and a share count for the self-apparatus tell the dedup rule
already names. It makes no dedup decision itself --- the agent still reads the
short output and applies judgement, same as before.
"""

from __future__ import annotations

import argparse
import math
import os
import random
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

OUTPUTS_GLOB = "website/src/content/outputs/*.yml"

TOKEN_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# Register and glue words, not subject matter --- the words that distinguish
# one topic from another are the nouns, so these carry no signal and would
# just inflate every similarity score uniformly.
STOPWORDS = frozenset(
    [
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "been",
        "but",
        "by",
        "for",
        "from",
        "has",
        "have",
        "how",
        "in",
        "into",
        "is",
        "it",
        "its",
        "of",
        "on",
        "or",
        "that",
        "the",
        "their",
        "there",
        "they",
        "this",
        "to",
        "was",
        "were",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "will",
        "with",
        "about",
        "after",
        "before",
        "between",
        "during",
        "over",
        "under",
        "across",
        "using",
        "use",
        "used",
        "new",
        "university",
        "school",
        "research",
        "paper",
        "poster",
        "analysis",
        "approach",
        "method",
        "framework",
        "study",
        "studies",
        "survey",
        "surveys",
    ]
)

# The dedup rule's own self-apparatus tell (skills/publish/SKILL.md, "Dedup"):
# a topic examining a piece of the University's own machinery rather than
# something physical and mundane.
APPARATUS_RE = re.compile(
    r"\b(?:register|dashboard|index|scorer|scorecard|committee|panel|ledger|"
    r"attestation|maturity model|horizon register|living dashboard|"
    r"indicator commons)\b",
    re.IGNORECASE,
)

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True)
class Entry:
    id: str
    title: str
    subtitle: str
    topic: str
    summary: str
    preset: str
    date: str

    @property
    def text(self) -> str:
        return f"{self.title} {self.subtitle} {self.topic} {self.summary}"


def collapse(text: str) -> str:
    return " ".join(str(text or "").split())


def truncate(text: str, limit: int) -> str:
    text = collapse(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def load_entries(root: Path) -> list[Entry]:
    entries: list[Entry] = []
    for path in sorted(root.glob(OUTPUTS_GLOB)):
        data = yaml.safe_load(path.read_text()) or {}
        entries.append(
            Entry(
                id=path.stem,
                title=collapse(data.get("title", "")),
                subtitle=collapse(data.get("subtitle", "")),
                topic=collapse(data.get("topic", "")),
                summary=collapse(data.get("summary", "")),
                preset=str(data.get("preset", "")),
                date=str(data.get("date", "")),
            )
        )
    if not entries:
        sys.exit(f"no entries found under {root / OUTPUTS_GLOB}")
    return entries


def tokenise(text: str) -> list[str]:
    return [
        word
        for word in TOKEN_RE.findall(text.lower())
        if word not in STOPWORDS and len(word) > 2
    ]


def idf_weights(token_lists: list[list[str]]) -> dict[str, float]:
    """Smoothed inverse document frequency over the corpus (sklearn-style),
    so a word in every entry gets weight ~1 rather than 0, and a word seen
    nowhere in the corpus (candidate-only) still gets a defined weight."""
    n = len(token_lists)
    df: Counter[str] = Counter()
    for tokens in token_lists:
        df.update(set(tokens))
    return {word: math.log((1 + n) / (1 + count)) + 1 for word, count in df.items()}


def vectorise(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    tf = Counter(tokens)
    default_idf = math.log(2) + 1  # a word unseen anywhere in the corpus
    return {word: count * idf.get(word, default_idf) for word, count in tf.items()}


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    shared = a.keys() & b.keys()
    if not shared:
        return 0.0
    dot = sum(a[word] * b[word] for word in shared)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def first_sentence(text: str) -> str:
    if not text:
        return ""
    return SENTENCE_RE.split(text, maxsplit=1)[0]


def nearest_topics(
    candidate_vec: dict[str, float],
    vectors: dict[str, dict[str, float]],
    entries: list[Entry],
    top: int,
) -> None:
    by_id = {entry.id: entry for entry in entries}
    scored = sorted(
        ((cosine(candidate_vec, vec), entry_id) for entry_id, vec in vectors.items()),
        reverse=True,
    )[:top]
    print(f"## Nearest prior topics (top {top} by similarity)")
    for score, entry_id in scored:
        entry = by_id[entry_id]
        label = entry.topic or entry.title
        print(
            f"- {score:.2f}  {entry.id}  ({entry.preset}, {entry.date})  {truncate(label, 140)}"
        )


def random_sample(entries: list[Entry], sample_n: int, seed: int | None) -> None:
    rng = (
        random.Random(seed)
        if seed is not None
        else random.Random(int.from_bytes(os.urandom(8), "big"))
    )
    chosen = rng.sample(entries, min(sample_n, len(entries)))
    print(f"## Random object sample ({len(chosen)} entries, whole corpus)")
    for entry in chosen:
        print(f"- {entry.id}: {entry.title} — {first_sentence(entry.summary)}")


def apparatus_share(entries: list[Entry]) -> None:
    def is_apparatus(entry: Entry) -> bool:
        return bool(APPARATUS_RE.search(f"{entry.topic} {entry.summary}"))

    all_matches = sum(is_apparatus(e) for e in entries)
    recent = sorted(entries, key=lambda e: e.date, reverse=True)[:30]
    recent_matches = sum(is_apparatus(e) for e in recent)
    all_pct = 100 * all_matches / len(entries)
    recent_pct = 100 * recent_matches / len(recent) if recent else 0.0
    print("## Apparatus share")
    print(f"{all_pct:.0f}% of all entries; {recent_pct:.0f}% of the last 30")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "topic", help="the candidate topic to check for prior neighbours"
    )
    parser.add_argument(
        "--root", type=Path, default=Path("."), help="checkout to read the ledger from"
    )
    parser.add_argument(
        "--top", type=int, default=10, help="nearest-topics shortlist size"
    )
    parser.add_argument(
        "--sample", type=int, default=12, help="random object-sample size"
    )
    parser.add_argument(
        "--seed", type=int, help="seed the random sample (default: OS randomness)"
    )
    args = parser.parse_args()

    entries = load_entries(args.root)
    token_lists = [tokenise(entry.text) for entry in entries]
    idf = idf_weights(token_lists)
    vectors = {
        entry.id: vectorise(tokens, idf) for entry, tokens in zip(entries, token_lists)
    }
    candidate_vec = vectorise(tokenise(args.topic), idf)

    nearest_topics(candidate_vec, vectors, entries, args.top)
    random_sample(entries, args.sample, args.seed)
    apparatus_share(entries)
    return 0


if __name__ == "__main__":
    sys.exit(main())
