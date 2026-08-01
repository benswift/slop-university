#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Merged tokens: the last known one-sided extraction artefact.

`pdftotext` loses the space between two words when the PDF sets them in
adjacent text runs with no explicit gap, which multi-column and heavily
kerned layouts do constantly. The result is `realworld`, `worldclass`,
`researchintensive` --- and Luna flagged a real Wollongong excerpt partly
for "the malformed 'realworld impact'". The press's PDFs are cleanly
typeset from typst, so merges land overwhelmingly on the real side and
point real -> fabricated, which is the direction that manufactures this
pilot's finding.

Detection cannot be done from a dictionary alone. The first attempt asked
only whether a non-word split into two words, and it spent most of its
output on `sustainability` (sustain + ability), `transformative` (trans +
formative) and `entrepreneurship` (entrepreneur + ship): ordinary words
that the Debian lists happen not to carry, split at a morpheme boundary.
No allowlist fixes that, because the failure is productive morphology and
the list would need every derived form in the genre.

So the evidence comes from the corpus instead, in two parts. A token
counts as merged only if

  * the corpus elsewhere writes those two words apart, with a space or a
    hyphen --- the condition a lost space implies, and one that
    `sustain ability` never satisfies; and
  * the closed form appears in fewer than three distinct source documents.
    A lost space is an accident of one document's typesetting. A form that
    three independent institutions all write closed is that genre's
    spelling, which is what separates `realworld` from `wellbeing`,
    `multidisciplinary` and `underrepresented` --- all of which pass the
    bigram test, because the corpus also hyphenates them.

Both halves must still be real words of at least three letters, and the
token itself must not be one.

Both measuring and repairing live here. `build_stimuli.py` calls `fit` and
`repair` at extraction time so a rebuilt pool is already clean; the `repair`
mode retrofits a pool that has already been through the LLM leak pass, which
is not worth paying for twice.

    uv run --script scripts/merged_tokens.py audit      # per-side rates
    uv run --script scripts/merged_tokens.py worst      # the actual tokens
    uv run --script scripts/merged_tokens.py repair     # rewrite the pool
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ids import item_id  # noqa: E402
from normalise import TOKEN_RE, wordlists  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "stimuli" / "pool_redacted.json"
RESULTS = ROOT / "results"

MIN_PART = 3
MIN_TOKEN = 8
MAX_DOCS = 3
BIGRAM_RE = re.compile(r"([A-Za-z]{3,})[ \-‐-―]([A-Za-z]{3,})")


@lru_cache(maxsize=1)
def known() -> frozenset[str]:
    british, american = wordlists()
    return british | american


def fit(corpus: list[tuple[str, str]]):
    """Fit the detector to a corpus of (document id, text) pairs, and return
    its split_point function.

    Both sides contribute the evidence. Fitting on the real side alone would
    let the real side define what counts as damage to itself, and the whole
    point of the measure is to compare the two."""
    bigrams: set[tuple[str, str]] = set()
    seen: dict[str, set[str]] = {}
    for doc, text in corpus:
        for m in BIGRAM_RE.finditer(text):
            bigrams.add((m.group(1).lower(), m.group(2).lower()))
        for m in TOKEN_RE.finditer(text):
            seen.setdefault(m.group(0).lower(), set()).add(doc)
    spread = Counter({tok: len(docs) for tok, docs in seen.items()})
    words = known()

    @lru_cache(maxsize=200_000)
    def split_point(token: str) -> tuple[str, str] | None:
        lower = token.lower()
        if len(lower) < MIN_TOKEN or not lower.isalpha() or lower in words:
            return None
        if spread[lower] >= MAX_DOCS:
            return None
        for i in range(MIN_PART, len(lower) - MIN_PART + 1):
            head, tail = lower[:i], lower[i:]
            if (head, tail) in bigrams and head in words and tail in words:
                return head, tail
        return None

    return split_point


def load_pool() -> list[dict]:
    if not POOL.exists():
        raise SystemExit("run `build_stimuli.py` first")
    return json.loads(POOL.read_text())


@lru_cache(maxsize=1)
def corpus_splitter():
    """The detector fitted to the stimulus pool on disk, for the analyses that
    read the pool rather than rebuild it."""
    return fit([(r["id"].rsplit("--", 1)[0], r["text"]) for r in load_pool()])


def merged(text: str, split=None) -> list[str]:
    """Every merged token in a passage, in order, with repeats."""
    split = split or corpus_splitter()
    return [m.group(0) for m in TOKEN_RE.finditer(text) if split(m.group(0))]


def rate(text: str, split=None) -> float:
    """Merged tokens per 1,000 words --- the axis the error tests use."""
    n = len(TOKEN_RE.findall(text))
    return 1000 * len(merged(text, split)) / n if n else 0.0


def repair(text: str, split=None) -> tuple[str, int]:
    """Reinsert the lost space. Returns (text, n_repairs)."""
    split = split or corpus_splitter()
    fixed = 0

    def one(m: re.Match[str]) -> str:
        nonlocal fixed
        parts = split(m.group(0))
        if not parts:
            return m.group(0)
        fixed += 1
        head, tail = parts
        original = m.group(0)
        # Preserve the leading capital; the second word starts lower unless the
        # whole token was upper case.
        if original.isupper():
            return f"{head.upper()} {tail.upper()}"
        if original[:1].isupper():
            return f"{head[:1].upper() + head[1:]} {tail}"
        return f"{head} {tail}"

    return TOKEN_RE.sub(one, text), fixed


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "audit"
    pool = load_pool()

    if mode == "audit":
        print(
            f"{'side':<12}{'condition':<12}{'n':>5}{'words':>9}{'merged':>8}{'/10k':>8}"
        )
        buckets: dict[tuple[str, str], list[dict]] = {}
        for r in pool:
            buckets.setdefault((r["truth"], r["condition"]), []).append(r)
        for (truth, cond), rows in sorted(buckets.items()):
            words = sum(len(TOKEN_RE.findall(r["text_redacted"])) for r in rows)
            hits = sum(len(merged(r["text_redacted"])) for r in rows)
            print(
                f"{truth:<12}{cond:<12}{len(rows):>5}{words:>9}{hits:>8}"
                f"{10000 * hits / max(words, 1):>8.1f}"
            )
        print()
        for truth in ("real", "fabricated"):
            rows = [r for r in pool if r["truth"] == truth]
            carry = sum(1 for r in rows if merged(r["text_redacted"]))
            print(
                f"{truth:<12}{carry / max(len(rows), 1):>6.0%} of excerpts carry at "
                f"least one merged token ({carry}/{len(rows)})"
            )
        return

    if mode == "worst":
        split = corpus_splitter()
        counts: Counter[str] = Counter()
        by_side: dict[str, Counter[str]] = {"real": Counter(), "fabricated": Counter()}
        for r in pool:
            for tok in merged(r["text_redacted"]):
                counts[tok.lower()] += 1
                by_side[r["truth"]][tok.lower()] += 1
        print(
            f"{len(counts)} distinct merged tokens, {sum(counts.values())} occurrences\n"
        )
        print(f"{'token':<26}{'n':>4}{'real':>6}{'fab':>5}   split")
        for tok, n in counts.most_common(80):
            head, tail = split(tok)
            print(
                f"{tok:<26}{n:>4}{by_side['real'][tok]:>6}"
                f"{by_side['fabricated'][tok]:>5}   {head} | {tail}"
            )
        return

    if mode == "repair":
        # Retrofit an existing pool rather than rebuilding it from the PDFs.
        # build_stimuli.py applies the same transform at extraction time, so a
        # rebuild does not need this; it exists so that a pool already through
        # the LLM leak pass can be fixed without paying for that pass again.
        split = corpus_splitter()
        total = 0
        changed: set[str] = set()
        for path in (ROOT / "stimuli" / "pool.json", POOL):
            if not path.exists():
                continue
            rows = json.loads(path.read_text())
            n = 0
            for r in rows:
                for field in ("text", "text_redacted"):
                    if field in r:
                        r[field], k = repair(r[field], split)
                        if k:
                            changed.add(r["id"])
                        n += k
            path.write_text(json.dumps(rows, indent=1))
            print(f"{path.name}: {n} spaces reinserted")
            total += n

        # The item id is derived from the excerpt's identity, not from its
        # text (see ids.py), so a repaired excerpt keeps its id and judge.py
        # would resume straight past it. The judgements for the text that no
        # longer exists have to be dropped by hand, or the re-run silently
        # reports the old ones.
        stale = {item_id(i) for i in changed}
        print(f"\n{total} in all, across {len(changed)} excerpts.")
        for path in sorted(RESULTS.glob("judgements-*.json")):
            rows = json.loads(path.read_text())
            keep = [r for r in rows if r["item"] not in stale]
            if len(keep) != len(rows):
                path.write_text(json.dumps(keep, indent=1))
                print(f"{path.name}: dropped {len(rows) - len(keep)} stale judgements")
        print("\nNow re-run sample_stimuli.py, then judge.py for every judge.")
        return

    raise SystemExit(f"unknown mode {mode!r} --- try audit, worst or repair")


if __name__ == "__main__":
    main()
