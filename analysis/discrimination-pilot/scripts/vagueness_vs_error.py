#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Does a real document's vagueness predict its being called fabricated?

This is the claim TASK-006 exists to test. The pilot's judges wrongly condemned
real strategic plans for "generic aspirational strategy language" and "sweeping
commitments offering no concrete detail", which suggested the boundary they had
learned runs between the concrete and the vague rather than between the real and
the invented. On four errors that was an anecdote. On a corpus of 130-odd real
documents scored independently for vagueness, it is testable.

The test is deliberately one-sided: it asks only about **real** excerpts, and
whether the ones a judge calls FABRICATED score higher on the vagueness index
than the ones it correctly calls REAL. Pooling both sides would answer a
different and much easier question, because the fabricated side differs from the
real side in register anyway.

Three statistics, none of which needs a dependency:

  point-biserial r   correlation between the vagueness index and the binary
                     error, per judge
  rank-sum           Mann-Whitney U as a normal approximation, which does not
                     assume the index is normally distributed (it is not)
  decile table       misclassification rate by vagueness decile --- the thing
                     actually worth putting in the paper, because a monotone
                     column is legible in a way that r is not

A permutation test backs the correlation, since n per judge is small enough that
the normal approximation is worth checking against something assumption-free.

    uv run --script scripts/vagueness_vs_error.py
    uv run --script scripts/vagueness_vs_error.py --judge gpt-5.6-terra
"""

from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
PROXIES = RESULTS / "vagueness-proxies.json"

PERMUTATIONS = 20000
SEED = 20260801


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def point_biserial(scores: list[float], flags: list[int]) -> float:
    """Correlation between a continuous score and a 0/1 outcome."""
    n = len(scores)
    if n < 3 or len(set(flags)) < 2:
        return float("nan")
    mx, my = mean(scores), mean([float(f) for f in flags])
    sx = math.sqrt(sum((x - mx) ** 2 for x in scores))
    sy = math.sqrt(sum((f - my) ** 2 for f in flags))
    if sx == 0 or sy == 0:
        return float("nan")
    return sum((x - mx) * (f - my) for x, f in zip(scores, flags)) / (sx * sy)


def permutation_p(scores: list[float], flags: list[int], observed: float) -> float:
    """Two-sided p by shuffling the error labels against the scores."""
    if math.isnan(observed):
        return float("nan")
    rng = random.Random(SEED)
    shuffled = list(flags)
    hits = 0
    for _ in range(PERMUTATIONS):
        rng.shuffle(shuffled)
        r = point_biserial(scores, shuffled)
        if not math.isnan(r) and abs(r) >= abs(observed):
            hits += 1
    return (hits + 1) / (PERMUTATIONS + 1)


def rank_sum_z(a: list[float], b: list[float]) -> tuple[float, float]:
    """Mann-Whitney U for group a vs b, returned as (U, z). Ties get mid-ranks."""
    if not a or not b:
        return float("nan"), float("nan")
    pooled = sorted([(v, 0) for v in a] + [(v, 1) for v in b])
    ranks: list[float] = [0.0] * len(pooled)
    i = 0
    while i < len(pooled):
        j = i
        while j + 1 < len(pooled) and pooled[j + 1][0] == pooled[i][0]:
            j += 1
        mid = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[k] = mid
        i = j + 1
    r_a = sum(r for r, (_, g) in zip(ranks, pooled) if g == 0)
    na, nb = len(a), len(b)
    u = r_a - na * (na + 1) / 2
    mu = na * nb / 2
    sigma = math.sqrt(na * nb * (na + nb + 1) / 12)
    return u, (u - mu) / sigma if sigma else float("nan")


def normal_p(z: float) -> float:
    if math.isnan(z):
        return float("nan")
    return math.erfc(abs(z) / math.sqrt(2))


def load() -> tuple[dict[str, float], list[dict]]:
    if not PROXIES.exists():
        raise SystemExit("run `vagueness.py --proxies` first")
    index = {
        r["item"]: r["vagueness_index"]
        for r in json.loads(PROXIES.read_text())
        if r.get("item")
    }

    rows: list[dict] = []
    for f in sorted(RESULTS.glob("judgements-*.json")):
        if f.name == "judgements-all.json":
            continue
        rows.extend(json.loads(f.read_text()))
    if not rows:
        raise SystemExit("no judgements yet --- run judge.py first")
    return index, rows


def deciles(pairs: list[tuple[float, int]], k: int = 10) -> None:
    """Misclassification rate by vagueness decile, pooled across judges."""
    if len(pairs) < k:
        print("  (too few items to bin)")
        return
    pairs = sorted(pairs)
    size = len(pairs) / k
    print(f"  {'decile':<8}{'n':>5}{'median index':>15}{'called FABRICATED':>20}")
    for d in range(k):
        chunk = pairs[int(d * size) : int((d + 1) * size)]
        if not chunk:
            continue
        errs = sum(f for _, f in chunk)
        med = chunk[len(chunk) // 2][0]
        bar = "#" * round(20 * errs / len(chunk))
        print(
            f"  {d + 1:<8}{len(chunk):>5}{med:>15.2f}{errs / len(chunk):>19.0%}  {bar}"
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--judge", help="restrict to one judge")
    p.add_argument(
        "--condition", default="strategy", help="condition to test (default: strategy)"
    )
    args = p.parse_args()

    index, rows = load()

    # Real excerpts only. The question is whether vagueness predicts a real
    # document being mistaken for a fabrication, not whether the two corpora
    # differ in register --- they do, and that is a separate finding.
    rows = [
        r
        for r in rows
        if r.get("truth") == "real"
        and r.get("judgement")
        and r.get("condition") == args.condition
        and r["item"] in index
    ]
    if args.judge:
        rows = [r for r in rows if r["judge"] == args.judge]
    if not rows:
        raise SystemExit("no matching real-side judgements")

    print(
        f"{len(rows)} real-side judgements in the {args.condition} condition, "
        f"{len({r['judge'] for r in rows})} judges, "
        f"{len({r['item'] for r in rows})} distinct excerpts\n"
    )

    by_judge: dict[str, list[tuple[float, int]]] = defaultdict(list)
    for r in rows:
        by_judge[r["judge"]].append(
            (index[r["item"]], int(r["judgement"] == "FABRICATED"))
        )

    print(
        f"{'judge':<22}{'n':>5}{'errors':>8}{'vague|err':>11}{'vague|ok':>10}{'r':>8}{'perm p':>9}{'rank p':>9}"
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
        f"\n{'pooled':<22}{len(pooled):>5}{sum(flags):>8}"
        f"{mean(err):>11.2f}{mean(ok):>10.2f}{r:>8.3f}"
        f"{permutation_p(scores, flags, r):>9.4f}{normal_p(z):>9.4f}"
    )
    print(
        "\nPooling repeats each excerpt once per judge, so the pooled p is anti-conservative\n"
        "--- read it as a description, and the per-judge rows as the test.\n"
    )

    print("Misclassification rate by vagueness decile (pooled):")
    deciles(pooled)


if __name__ == "__main__":
    main()
