#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""If not vagueness, then what? Candidate predictors of real-side error.

`vagueness_vs_error.py` answers the question TASK-006 was built to ask and
answers it no: a real document's vagueness does not predict a judge calling
it fabricated. That rules something out. It does not say what is going on,
and a section that only rules things out is weaker than one that finds the
thing.

So this tests the same 82-odd real strategy excerpts against every other
property the apparatus already carries, on exactly the same statistics the
vagueness test used, so the two are read side by side:

  merged      merged tokens per 1,000 words --- extraction damage, and the
              leading candidate. Luna faulted a real Wollongong excerpt
              partly for "the malformed 'realworld impact'". Unlike
              vagueness this is a defect in our stimuli rather than a
              property of the genre, so a hit here is a bug, not a finding
  age         2026 minus the document's year. Older strategy might read as
              generated to a model whose sense of the register is current
  length      words in the excerpt, as a nuisance check
  vagueness   the lexical index, repeated here so the null has company

and four surface-form candidates added for run 4 (TASK-011). The vagueness
null leaves nearly all the real-side error variance unexplained, and the
missing ingredient was a candidate rather than a test, so these are the
properties a reader could plausibly be reacting to that the apparatus was
not yet measuring:

  sentence_len  mean words per sentence
  burstiness    sd/mean of sentence length --- uniform sentence length is the
                most-cited surface signature of generated prose, so a real
                excerpt low on this axis may read as machine-written for a
                reason that has nothing to do with what it says
  first_person  we/our/us per 100 words: the institutional voice
  listiness     share of lines shorter than a clause, i.e. how much of the
                excerpt is list rather than prose after the filter

and, categorically:

  tier        elite / research / regional / mid / specialist
  country     collapsed to the countries with enough excerpts to matter
  doc_type    strategic plan / vision / institutional plan / ...
  recognised  whether THIS judge claimed to recognise the source in the
              memorisation probe. The only per-judge predictor in the list,
              and the one with a mechanism behind it: a judge that recalls
              the document is not judging it

Continuous axes get the point-biserial, permutation test and decile table
from `vagueness_vs_error`; categorical ones get per-level error rates and a
permutation test on the chi-square statistic, which needs no distributional
assumption and copes with the small cells that a 25-country corpus produces.

    uv run --script scripts/error_predictors.py
    uv run --script scripts/error_predictors.py --axis merged
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merged_tokens import rate as merged_rate  # noqa: E402
from vagueness_vs_error import (  # noqa: E402
    PERMUTATIONS,
    SEED,
    check_current,
    deciles,
    mean,
    normal_p,
    permutation_p,
    point_biserial,
    rank_sum_z,
)

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
POOL = ROOT / "stimuli" / "pool_redacted.json"

CONTINUOUS = (
    "merged",
    "age",
    "length",
    "vagueness",
    "sentence_len",
    "burstiness",
    "first_person",
    "listiness",
)
CATEGORICAL = ("damaged", "tier", "country", "doc_type", "recognised")

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-]*")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
FIRST_PERSON = re.compile(r"\b(?:we|our|ours|us|we’re|we'll|we’ll)\b", re.I)


def sentence_lengths(text: str) -> list[int]:
    return [
        n for n in (len(WORD_RE.findall(s)) for s in SENTENCE_SPLIT.split(text)) if n
    ]


def burstiness(text: str) -> float:
    """Coefficient of variation of sentence length.

    Uniform sentence length is the most-cited surface signature of generated
    prose, so the reading under test is the mirror of the vision-document one:
    a real excerpt whose sentences are all the same length may read as
    machine-written for that reason alone. Expressed as sd/mean so it does not
    simply restate `sentence_len`.
    """
    lens = sentence_lengths(text)
    if len(lens) < 2:
        return 0.0
    m = sum(lens) / len(lens)
    if not m:
        return 0.0
    var = sum((x - m) ** 2 for x in lens) / (len(lens) - 1)
    return math.sqrt(var) / m


def listiness(text: str) -> float:
    """Share of lines that are shorter than a clause.

    The prose filter rejects a paragraph where more than 45% of lines are short,
    which leaves a wide band of surviving passages that are still half bullet
    list. A judge reading fragments rather than sentences is reading something
    the genre produces and the press mostly does not.
    """
    lines = [ln for ln in text.split("\n") if ln.strip()]
    if not lines:
        return 0.0
    return sum(len(ln.split()) < 8 for ln in lines) / len(lines)


# A level with fewer than this many judgements is folded into "other". Chi-square
# is unreliable on tiny cells even under permutation, and a country contributing
# one excerpt tells us nothing either way.
MIN_LEVEL = 12


def load_judgements(condition: str) -> list[dict]:
    rows: list[dict] = []
    for f in sorted(RESULTS.glob("judgements-*.json")):
        if f.name == "judgements-all.json":
            continue
        rows.extend(json.loads(f.read_text()))
    if not rows:
        raise SystemExit("no judgements yet --- run judge.py first")
    return [
        r
        for r in rows
        if r.get("truth") == "real"
        and r.get("judgement")
        and r.get("condition") == condition
    ]


def load_axes() -> tuple[dict[str, dict[str, float]], dict[str, dict[str, str]]]:
    """Per-item values for every axis, continuous and categorical."""
    pool = {r["item"]: r for r in json.loads(POOL.read_text()) if r.get("item")}
    if not pool:
        # pool_redacted predates the item id; fall back to the stimulus set,
        # which carries the same fields plus the id.
        pool = {
            r["item"]: r
            for r in json.loads((ROOT / "stimuli" / "stimuli.json").read_text())
        }

    proxies = json.loads((RESULTS / "vagueness-proxies.json").read_text())
    check_current(proxies, "vagueness-proxies.json")
    vagueness = {r["item"]: r["vagueness_index"] for r in proxies if r.get("item")}

    numeric: dict[str, dict[str, float]] = {a: {} for a in CONTINUOUS}
    labels: dict[str, dict[str, str]] = {a: {} for a in CATEGORICAL}
    for item, r in pool.items():
        numeric["merged"][item] = merged_rate(r["text_redacted"])
        # Most excerpts carry no merged token at all, so the rate is zero-heavy
        # and a decile table on it is unreadable. The binary form is the one to
        # look at: does an excerpt with visible extraction damage draw more
        # FABRICATED calls than a clean one?
        labels["damaged"][item] = (
            "merged token present" if numeric["merged"][item] else "clean"
        )
        if r.get("year"):
            numeric["age"][item] = 2026 - int(r["year"])
        numeric["length"][item] = float(r["words"])
        text = r["text_redacted"]
        lens = sentence_lengths(text)
        numeric["sentence_len"][item] = sum(lens) / len(lens) if lens else 0.0
        numeric["burstiness"][item] = burstiness(text)
        numeric["first_person"][item] = (
            len(FIRST_PERSON.findall(text)) / max(r["words"], 1) * 100
        )
        numeric["listiness"][item] = listiness(text)
        if item in vagueness:
            numeric["vagueness"][item] = vagueness[item]
        for a in ("tier", "country", "doc_type"):
            if r.get(a):
                labels[a][item] = str(r[a])
    return numeric, labels


def load_recognition() -> dict[tuple[str, str], str]:
    """(judge, item) -> 'recognised' / 'not recognised', where probed."""
    path = RESULTS / "memorisation.json"
    if not path.exists():
        return {}
    # The probe records the backend it was called through (`claude:opus`) while
    # a judgement records the model (`opus`). Joining on the raw string silently
    # drops every Anthropic judge from this axis.
    return {
        (r["model"].split(":", 1)[-1], r["item"]): (
            "recognised" if r["recognised"] else "not recognised"
        )
        for r in json.loads(path.read_text())
        if r.get("item") and r.get("model")
    }


def chi_square(table: dict[str, tuple[int, int]]) -> float:
    """Pearson chi-square on a levels x {error, ok} contingency table."""
    total = sum(e + o for e, o in table.values())
    errors = sum(e for e, _ in table.values())
    if not total or not errors or errors == total:
        return float("nan")
    p = errors / total
    stat = 0.0
    for e, o in table.values():
        n = e + o
        for observed, expected in ((e, n * p), (o, n * (1 - p))):
            if expected > 0:
                stat += (observed - expected) ** 2 / expected
    return stat


def permutation_chi_p(pairs: list[tuple[str, int]], observed: float) -> float:
    if math.isnan(observed):
        return float("nan")
    rng = random.Random(SEED)
    levels = [level for level, _ in pairs]
    flags = [f for _, f in pairs]
    hits = 0
    for _ in range(PERMUTATIONS // 10):
        rng.shuffle(flags)
        table: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
        for level, f in zip(levels, flags):
            e, o = table[level]
            table[level] = (e + f, o + (1 - f))
        if chi_square(dict(table)) >= observed:
            hits += 1
    return (hits + 1) / (PERMUTATIONS // 10 + 1)


def collapse_map(pairs: list[tuple[str, int]]) -> dict[str, str]:
    """Level -> level, folding the thin ones into 'other'. Derived once from
    the pooled data and reused for the per-judge rows: fitting it per judge
    would collapse different levels for different judges and make the rows
    incomparable, which is the whole point of showing them."""
    counts: dict[str, int] = defaultdict(int)
    for level, _ in pairs:
        counts[level] += 1
    return {
        level: (level if n >= MIN_LEVEL else "other") for level, n in counts.items()
    }


def tabulate(
    pairs: list[tuple[str, int]], mapping: dict[str, str]
) -> dict[str, tuple[int, int]]:
    table: dict[str, tuple[int, int]] = defaultdict(lambda: (0, 0))
    for level, f in pairs:
        e, o = table[mapping.get(level, level)]
        table[mapping.get(level, level)] = (e + f, o + (1 - f))
    return dict(table)


def report_continuous(axis: str, by_judge: dict[str, list[tuple[float, int]]]) -> None:
    print(f"\n=== {axis} ===\n")
    print(
        f"{'judge':<22}{'n':>5}{'errors':>8}{'axis|err':>11}{'axis|ok':>10}"
        f"{'r':>8}{'perm p':>9}{'rank p':>9}"
    )
    for judge, pairs in sorted(by_judge.items()):
        scores = [s for s, _ in pairs]
        flags = [f for _, f in pairs]
        err = [s for s, f in pairs if f]
        ok = [s for s, f in pairs if not f]
        r = point_biserial(scores, flags)
        _, z = rank_sum_z(err, ok)
        print(
            f"{judge:<22}{len(pairs):>5}{sum(flags):>8}"
            f"{mean(err):>11.2f}{mean(ok):>10.2f}"
            f"{r:>8.3f}{permutation_p(scores, flags, r):>9.4f}{normal_p(z):>9.4f}"
        )
    pooled = [pair for pairs in by_judge.values() for pair in pairs]
    scores = [s for s, _ in pooled]
    flags = [f for _, f in pooled]
    r = point_biserial(scores, flags)
    err = [s for s, f in pooled if f]
    ok = [s for s, f in pooled if not f]
    _, z = rank_sum_z(err, ok)
    print(
        f"{'pooled':<22}{len(pooled):>5}{sum(flags):>8}"
        f"{mean(err):>11.2f}{mean(ok):>10.2f}{r:>8.3f}"
        f"{permutation_p(scores, flags, r):>9.4f}{normal_p(z):>9.4f}"
    )
    print(f"\nMisclassification rate by {axis} decile (pooled):")
    deciles(pooled)


def report_categorical(axis: str, by_judge: dict[str, list[tuple[str, int]]]) -> None:
    print(f"\n=== {axis} ===\n")
    raw = [pair for pairs in by_judge.values() for pair in pairs]
    mapping = collapse_map(raw)
    pooled = [(mapping[level], f) for level, f in raw]
    table = tabulate(raw, mapping)
    stat = chi_square(table)
    print(f"{'level':<24}{'n':>6}{'errors':>8}{'rate':>8}")
    for level, (e, o) in sorted(
        table.items(), key=lambda kv: -kv[1][0] / max(sum(kv[1]), 1)
    ):
        n = e + o
        bar = "#" * round(20 * e / n)
        print(f"{level:<24}{n:>6}{e:>8}{e / n:>8.0%}  {bar}")
    print(
        f"\npooled chi-square {stat:.2f} on {len(table) - 1} df, "
        f"permutation p {permutation_chi_p(pooled, stat):.4f}"
    )
    print(
        "Pooling repeats each excerpt once per judge, so this p is anti-conservative,\n"
        "and the two DeepSeek judges contribute most of the errors. Read the per-judge\n"
        "rows for whether the effect is a panel-wide one or two judges' habit."
    )

    levels = sorted({level for level, _ in pooled})
    if len(levels) > 6:
        return
    print(f"\n{'judge':<22}" + "".join(f"{level[:13]:>15}" for level in levels))
    for judge, pairs in sorted(by_judge.items()):
        cells = tabulate(pairs, mapping)
        row = ""
        for level in levels:
            e, o = cells.get(level, (0, 0))
            row += f"{f'{e}/{e + o}':>9}" + (
                f"{e / (e + o):>6.0%}" if e + o else " " * 6
            )
        print(f"{judge:<22}{row}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--axis", help="one axis only (default: all)")
    p.add_argument("--judge", help="restrict to one judge")
    p.add_argument("--condition", default="strategy")
    args = p.parse_args()

    rows = load_judgements(args.condition)
    if args.judge:
        rows = [r for r in rows if r["judge"] == args.judge]
    numeric, labels = load_axes()
    labels["recognised"] = {}  # per-judge; filled below
    recognition = load_recognition()

    print(
        f"{len(rows)} real-side judgements in the {args.condition} condition, "
        f"{len({r['judge'] for r in rows})} judges, "
        f"{len({r['item'] for r in rows})} distinct excerpts"
    )

    wanted = [args.axis] if args.axis else [*CONTINUOUS, *CATEGORICAL]
    for axis in wanted:
        if axis in CONTINUOUS:
            by_judge: dict[str, list[tuple[float, int]]] = defaultdict(list)
            for r in rows:
                if r["item"] in numeric[axis]:
                    by_judge[r["judge"]].append(
                        (numeric[axis][r["item"]], int(r["judgement"] == "FABRICATED"))
                    )
            report_continuous(axis, dict(by_judge))
        elif axis == "recognised":
            by_judge_c: dict[str, list[tuple[str, int]]] = defaultdict(list)
            for r in rows:
                key = (r["judge"], r["item"])
                if key in recognition:
                    by_judge_c[r["judge"]].append(
                        (recognition[key], int(r["judgement"] == "FABRICATED"))
                    )
            if not by_judge_c:
                print(
                    "\n=== recognised ===\n\n  (no memorisation probe for these judges)"
                )
                continue
            print(f"\n(probed judges: {', '.join(sorted(by_judge_c))})")
            report_categorical(axis, dict(by_judge_c))
        elif axis in CATEGORICAL:
            by_judge_c = defaultdict(list)
            for r in rows:
                if r["item"] in labels[axis]:
                    by_judge_c[r["judge"]].append(
                        (labels[axis][r["item"]], int(r["judgement"] == "FABRICATED"))
                    )
            report_categorical(axis, dict(by_judge_c))
        else:
            raise SystemExit(f"unknown axis {axis!r}")


if __name__ == "__main__":
    main()
