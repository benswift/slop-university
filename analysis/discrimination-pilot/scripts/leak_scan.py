#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Scan a redacted excerpt pool for residual one-sided identity leakage.

The first run of the pilot ran a version of this by hand and reported that "a
scan for capitalised proper-noun sequences appearing on only one side found no
residual identity leakage". Two judges then found `Unit M` --- Manchester's real
innovation unit, left standing after the institution's name was removed --- and
read it as an unreplaced placeholder, which is a cue pointing real ->
fabricated. The hand scan missed it because `Unit M` is a `Word + single
capital` form, not a sequence of capitalised words. Three excerpts also kept
untranslated `mātauranga` and `chéile`, which the gazetteer never saw because it
redacted the *name* of a language, not its vocabulary.

Committing the scan is the point: an audit that lives in someone's shell history
cannot be re-run, and its claims cannot be checked. Six families of cue:

  proper-sequence     two or more capitalised words in a row      (the original)
  word-capital        a word followed by a lone capital letter    (`Unit M`)
  lone-capital        a bare single capital standing as a token   (placeholder-ish)
  non-english         a diacritic-bearing token in neither of the
                      system word lists                           (`mātauranga`)
  redaction-artefact  a doubled redaction bracket                 (`[[ORGANISATION]]`)
  digit-merge         two four-digit years run together           (`20272030`)

The last two were added after the run-4 review: both are pipeline damage
rather than identity leakage, both sat one-sided on the real side (24 real
excerpts against 1 fabricated carried `[[`), and judges cited both in
Wollongong vision excerpts they got wrong. A cue family this scan does not
look for is a cue family a clean bill of health says nothing about.

Anything appearing on exactly one side is a candidate tell. The output is a
worklist for the gazetteer, not a verdict --- plenty of one-sided forms are
legitimately part of what the test measures.

    uv run --script scripts/leak_scan.py [stimuli/pool_redacted.json]
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalise import wordlists  # noqa: E402

# Words that start a sentence or a heading and so capitalise for grammatical
# reasons rather than because they name anything.
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "our",
    "the",
    "this",
    "to",
    "we",
    "with",
    "it",
    "its",
    "their",
    "they",
    "these",
    "those",
    "that",
    "will",
    "must",
    "is",
    "are",
    "was",
    "were",
    "be",
}

REDACTION_TAG = re.compile(r"\[(?:ORGANISATION|PERSON|PLACE|REF|UNIVERSITY|SCHOOL)\]")

PROPER_SEQUENCE = re.compile(
    r"\b([A-Z][a-z]{2,}(?:\s+(?:of|for|and|the|de|van)\s+)?(?:\s+[A-Z][a-z]{2,})+)\b"
)
WORD_CAPITAL = re.compile(r"\b([A-Z][a-z]{2,}\s+[A-Z])\b(?![a-z])")
# The lookarounds have to exclude `&` as well as word characters, or the scan
# reports `R&D` and `I&E` as four separate bare capitals. Those are ordinary
# English and were most of what this family found: without the exclusion the
# residual reads as eleven one-sided leaks when it is really two documents.
# The hyphen matters. Without it `K-12`, `E-research`, `H-index` and `B-IQ` all
# report their first letter as a bare capital, and the family fills up with
# ordinary hyphenated vocabulary --- which is how a genuine defect (a mangled
# `[ORGANISATION]R`) sat unnoticed among twelve false positives.
LONE_CAPITAL = re.compile(r"(?<![\w'’.&\-])([A-Z])(?![\w'’.&\-])")
NON_ENGLISH = re.compile(r"\b([A-Za-zÀ-ÿĀ-ž]*[À-ÿĀ-ž][A-Za-zÀ-ÿĀ-ž]*)\b")
# On the RAW text: REDACTION_TAG.sub eats the inner tag of `[[ORGANISATION]]`,
# so the doubled form is invisible in `clean`.
REDACTION_ARTEFACT = re.compile(r"\[\[|\]\]")
DIGIT_MERGE = re.compile(r"\b((?:19|20)\d{2}(?:19|20)\d{2})\b")


def load(path: Path) -> list[dict]:
    rows = json.loads(path.read_text())
    return rows if isinstance(rows, list) else rows["items"]


def side_of(row: dict) -> str:
    for key in ("truth", "side", "label"):
        if key in row:
            value = str(row[key]).lower()
            return "fabricated" if "fab" in value else "real"
    raise KeyError(f"no side field in {sorted(row)}")


def text_of(row: dict) -> str:
    # `text_redacted` FIRST. The pool carries both the gazetteer-only text and
    # the text after the LLM leak pass, and scanning the former reports leaks
    # that were in fact removed --- which is worse than useless, because it
    # sends you hunting for identity residue that is not in the stimulus.
    for key in ("text_redacted", "text", "excerpt", "redacted", "body"):
        if key in row:
            return row[key]
    raise KeyError(f"no text field in {sorted(row)}")


def find_cues(text: str) -> dict[str, set[str]]:
    british, american = wordlists()
    known = british | american
    clean = REDACTION_TAG.sub(" ", text)

    cues: dict[str, set[str]] = defaultdict(set)

    for m in PROPER_SEQUENCE.finditer(clean):
        phrase = " ".join(m.group(1).split())
        if all(w.lower() in STOPWORDS for w in phrase.split()):
            continue
        cues["proper-sequence"].add(phrase)

    for m in WORD_CAPITAL.finditer(clean):
        phrase = " ".join(m.group(1).split())
        if phrase.split()[0].lower() in STOPWORDS:
            continue
        cues["word-capital"].add(phrase)

    for m in LONE_CAPITAL.finditer(clean):
        if m.group(1) not in {"I", "A"}:
            cues["lone-capital"].add(m.group(1))

    for m in NON_ENGLISH.finditer(clean):
        token = m.group(1)
        if token.lower() not in known and len(token) > 2:
            cues["non-english"].add(token)

    for m in REDACTION_ARTEFACT.finditer(text):
        cues["redaction-artefact"].add(m.group(0))

    for m in DIGIT_MERGE.finditer(clean):
        cues["digit-merge"].add(m.group(1))

    return cues


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else ROOT / "stimuli" / "pool_redacted.json"
    )
    if not path.exists():
        raise SystemExit(
            f"no pool at {path} --- run build_stimuli.py and leak_audit.py first"
        )

    rows = load(path)
    seen: dict[str, dict[str, dict[str, set[str]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(set))
    )

    for row in rows:
        side = side_of(row)
        item = str(row.get("id", row.get("item", "?")))
        for family, phrases in find_cues(text_of(row)).items():
            for phrase in phrases:
                seen[family][phrase][side].add(item)

    print(f"{len(rows)} excerpts from {path}\n")

    total_one_sided = 0
    for family in ("word-capital", "lone-capital", "non-english", "proper-sequence"):
        entries = seen.get(family, {})
        one_sided = {
            phrase: sides for phrase, sides in entries.items() if len(sides) == 1
        }
        total_one_sided += len(one_sided)
        print(
            f"## {family}: {len(entries)} distinct forms, {len(one_sided)} appear on one side only"
        )

        ranked = sorted(
            one_sided.items(), key=lambda kv: -sum(len(v) for v in kv[1].values())
        )
        for phrase, sides in ranked[:25]:
            side = next(iter(sides))
            items = sorted(sides[side])
            print(f"  [{side:<10}] {phrase!r}  x{len(items)}  {', '.join(items[:6])}")
        if len(ranked) > 25:
            print(f"  ... and {len(ranked) - 25} more")
        print()

    # The damage families are reported per side rather than one-sided-only: a
    # 24:1 skew (run 4's `[[` count) is a strong cue that a strictly one-sided
    # filter would hide behind the single fabricated hit.
    for family in ("redaction-artefact", "digit-merge"):
        entries = seen.get(family, {})
        print(f"## {family}: {len(entries)} distinct forms, counts per side")
        for phrase, sides in sorted(entries.items()):
            counts = ", ".join(
                f"{side} x{len(items)}" for side, items in sorted(sides.items())
            )
            examples = sorted(items for xs in sides.values() for items in xs)[:4]
            print(f"  {phrase!r}  {counts}  e.g. {', '.join(examples)}")
        print()

    print(f"{total_one_sided} one-sided forms in total.")
    print(
        "Review the `word-capital`, `lone-capital` and `non-english` families first: those\n"
        "are the three the first run's hand scan did not cover, and all three produced\n"
        "cues that judges cited. The `redaction-artefact` and `digit-merge` families are\n"
        "pipeline damage rather than leakage: anything they report should be fixed in\n"
        "leak_audit.py or build_stimuli.py before the next judging run."
    )


if __name__ == "__main__":
    main()
