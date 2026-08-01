#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Analyse the discrimination pilot: accuracy, confusion, breakdowns, calibration."""

from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent.parent
RESULTS = SCRATCH / "results"


def binom_p_two_sided(k: int, n: int, p: float = 0.5) -> float:
    """Exact two-sided binomial test against p."""

    def pmf(i: int) -> float:
        return math.comb(n, i) * p**i * (1 - p) ** (n - i)

    obs = pmf(k)
    return min(1.0, sum(pmf(i) for i in range(n + 1) if pmf(i) <= obs * (1 + 1e-9)))


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    s = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - s) / d, (c + s) / d)


def correct(r: dict) -> bool | None:
    if not r.get("judgement"):
        return None
    return r["judgement"].upper() == r["truth"].upper()


def report(rows: list[dict], label: str) -> dict:
    rows = [r for r in rows if r.get("judgement")]
    n = len(rows)
    k = sum(correct(r) for r in rows)
    lo, hi = wilson(k, n)
    p = binom_p_two_sided(k, n)
    print(f"\n{'=' * 72}\n{label}   n={n}")
    print(f"{'=' * 72}")
    print(
        f"accuracy {k}/{n} = {k / n:.1%}   95% CI [{lo:.1%}, {hi:.1%}]   binomial p = {p:.4g}"
    )

    # confusion matrix
    cm = Counter((r["truth"], r["judgement"].lower()) for r in rows)
    print("\nconfusion (rows = truth, cols = judged)")
    print(f"{'':14}{'fabricated':>12}{'real':>8}")
    for t in ("fabricated", "real"):
        print(f"{t:14}{cm[(t, 'fabricated')]:>12}{cm[(t, 'real')]:>8}")
    nf = sum(1 for r in rows if r["truth"] == "fabricated")
    nr = n - nf
    print(
        f"\nsensitivity to fabrication {cm[('fabricated', 'fabricated')]}/{nf} = "
        f"{cm[('fabricated', 'fabricated')] / max(nf, 1):.1%}"
    )
    print(
        f"specificity (real called real) {cm[('real', 'real')]}/{nr} = {cm[('real', 'real')] / max(nr, 1):.1%}"
    )
    bias = sum(1 for r in rows if r["judgement"].lower() == "fabricated") / n
    print(f"response bias: called FABRICATED {bias:.1%} of the time")

    # breakdowns
    for key in ("condition", "subtype"):
        print(f"\nby {key}:")
        g = defaultdict(list)
        for r in rows:
            g[r[key]].append(r)
        for kk in sorted(g):
            v = g[kk]
            c = sum(correct(x) for x in v)
            l, h = wilson(c, len(v))
            print(
                f"  {kk:18} {c:3d}/{len(v):<3d} = {c / len(v):6.1%}  CI [{l:.0%},{h:.0%}]"
            )

    # condition x truth
    print("\nby condition x truth:")
    g = defaultdict(list)
    for r in rows:
        g[(r["condition"], r["truth"])].append(r)
    for kk in sorted(g):
        v = g[kk]
        c = sum(correct(x) for x in v)
        print(f"  {kk[0]:10} {kk[1]:11} {c:3d}/{len(v):<3d} = {c / len(v):6.1%}")

    # calibration
    print("\ncalibration:")
    bins = [(50, 69), (70, 84), (85, 94), (95, 100)]
    for lo_b, hi_b in bins:
        v = [r for r in rows if r.get("confidence") and lo_b <= r["confidence"] <= hi_b]
        if not v:
            continue
        c = sum(correct(x) for x in v)
        mc = sum(x["confidence"] for x in v) / len(v)
        print(
            f"  conf {lo_b:3d}-{hi_b:3d}  n={len(v):3d}  stated {mc:5.1f}%  actual {c / len(v):6.1%}"
        )
    conf_c = [r["confidence"] for r in rows if correct(r) and r.get("confidence")]
    conf_w = [r["confidence"] for r in rows if not correct(r) and r.get("confidence")]
    if conf_c and conf_w:
        print(
            f"  mean confidence when right {sum(conf_c) / len(conf_c):.1f}  when wrong {sum(conf_w) / len(conf_w):.1f}"
        )
    return {"n": n, "k": k, "acc": k / n, "ci": (lo, hi), "p": p}


def main() -> None:
    files = sorted(RESULTS.glob("judgements-*.json"))
    allrows: list[dict] = []
    for f in files:
        rows = json.loads(f.read_text())
        report(rows, f"JUDGE: {rows[0]['judge']}")
        allrows += rows

    if len(files) > 1:
        report(allrows, "POOLED (all judges)")

        # per-item agreement
        by_item = defaultdict(list)
        for r in allrows:
            if r.get("judgement"):
                by_item[r["item"]].append(r)
        unan = [v for v in by_item.values() if len({x["judgement"] for x in v}) == 1]
        print(
            f"\nunanimous on {len(unan)}/{len(by_item)} items ({len(unan) / len(by_item):.0%})"
        )
        unan_correct = sum(1 for v in unan if correct(v[0]))
        print(
            f"  of those, correct on {unan_correct}/{len(unan)} = {unan_correct / max(len(unan), 1):.0%}"
        )

        # majority vote
        maj_correct = 0
        for v in by_item.values():
            votes = Counter(x["judgement"] for x in v)
            top = votes.most_common(1)[0][0]
            if top.upper() == v[0]["truth"].upper():
                maj_correct += 1
        n_items = len(by_item)
        lo, hi = wilson(maj_correct, n_items)
        print(
            f"majority vote accuracy {maj_correct}/{n_items} = {maj_correct / n_items:.1%} "
            f"CI [{lo:.0%},{hi:.0%}] p={binom_p_two_sided(maj_correct, n_items):.4g}"
        )

    # tag-density baseline: how much could a judge get from counting tags alone?
    stims = json.loads((SCRATCH / "stimuli" / "stimuli.json").read_text())
    best = 0.0
    for thr in [x / 100 for x in range(0, 800, 5)]:
        for sign in (1, -1):
            hit = sum(
                1
                for s in stims
                if (s["tag_density"] > thr)
                == (s["truth"] == ("real" if sign == 1 else "fabricated"))
            )
            best = max(best, hit / len(stims))
    print(
        f"\ntag-density-only baseline (best single threshold, fitted on the test set): {best:.1%}"
    )


if __name__ == "__main__":
    main()
