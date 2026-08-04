#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Does a long-horizon vision document draw more FABRICATED calls than an
ordinary strategic plan?

Run 3 said yes and could not be believed: six excerpts from five institutions,
35% against 14%, from judges at every level of the panel. Six excerpts is a
direction, not a result, and the obvious rival explanation was never ruled out
--- the institutions that publish a separate vision document might simply write
differently from the ones that do not, in which case the axis is house style and
`vision` is its label.

Run 4 attacks both problems. The vision arm takes every prose excerpt the
corpus's vision documents yielded rather than the seven the tag-density matching
happened to draw, and for five of those institutions it adds the SAME
institution's ordinary planning document, which controls house style by
construction.

Three tests, weakest confound control to strongest:

  unpaired   every vision excerpt against every ordinary-plan excerpt, pooled
             across the headline sample and the arm. Most power, no control for
             house style
  arm-only   the arm alone, where vision excerpts meet the institution-matched
             plans rather than the whole corpus
  paired     institutions contributing BOTH a vision document and a plan. House
             style cancels; n is small and the test is a sign test over
             judge x institution cells rather than over excerpts

    uv run --script scripts/vision_effect.py
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vagueness_vs_error import PERMUTATIONS, SEED  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
ARM_RESULTS = RESULTS / "arm-vision"

VISION = "vision"
# Everything the corpus calls a plan rather than a vision. `research-strategy`
# is left out of the contrast: two documents, and a research strategy is a
# third genre rather than the ordinary case.
PLAN_TYPES = {"strategic-plan", "institutional-plan", "corporate-plan"}


def load_pool() -> dict[str, dict]:
    """Item -> its stimulus record, over both sets.

    The pool file predates the content-derived item id, so the join has to come
    from the sampled sets, which carry `item` alongside the provenance fields.
    """
    out: dict[str, dict] = {}
    for name in ("stimuli.json", "arm_vision.json"):
        path = ROOT / "stimuli" / name
        if path.exists():
            out.update({r["item"]: r for r in json.loads(path.read_text())})
    if not out:
        raise SystemExit("no sampled stimuli --- run sample_stimuli.py first")
    return out


def load_side(directory: Path) -> list[dict]:
    rows: list[dict] = []
    for f in sorted(directory.glob("judgements-*.json")):
        if f.name == "judgements-all.json":
            continue
        rows.extend(json.loads(f.read_text()))
    return [
        r
        for r in rows
        if r.get("truth") == "real"
        and r.get("judgement")
        and r.get("condition") == "strategy"
    ]


def label(rec: dict) -> str | None:
    t = rec.get("doc_type")
    if t == VISION:
        return VISION
    if t in PLAN_TYPES:
        return "plan"
    return None


def rate(rows: list[dict]) -> tuple[int, int]:
    return sum(r["judgement"] == "FABRICATED" for r in rows), len(rows)


def fmt(hits: int, n: int) -> str:
    return f"{hits}/{n} = {hits / n:>5.0%}" if n else "     ---"


def permutation_diff(
    pairs: list[tuple[str, int]], observed: float, rng: random.Random
) -> float:
    """Two-sided p for the difference in error rate between two labels."""
    labels = [x for x, _ in pairs]
    flags = [f for _, f in pairs]
    hits = 0
    for _ in range(PERMUTATIONS // 10):
        rng.shuffle(flags)
        a = [f for lab, f in zip(labels, flags) if lab == VISION]
        b = [f for lab, f in zip(labels, flags) if lab != VISION]
        if not a or not b:
            continue
        if abs(sum(a) / len(a) - sum(b) / len(b)) >= abs(observed):
            hits += 1
    return (hits + 1) / (PERMUTATIONS // 10 + 1)


def contrast(title: str, rows: list[dict], pool: dict[str, dict]) -> None:
    tagged = [
        (label(pool[r["item"]]), r)
        for r in rows
        if r["item"] in pool and label(pool[r["item"]])
    ]
    if not tagged:
        print(f"\n=== {title} ===\n  (no excerpts)")
        return

    print(f"\n=== {title} ===\n")
    print(f"{'judge':<22}{'vision':>16}{'plan':>16}{'difference':>13}")
    by_judge: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for lab, r in tagged:
        by_judge[r["judge"]].append((lab, r))

    for judge, xs in sorted(by_judge.items()):
        vh, vn = rate([r for lab, r in xs if lab == VISION])
        ph, pn = rate([r for lab, r in xs if lab == "plan"])
        d = (vh / vn - ph / pn) if vn and pn else float("nan")
        print(f"{judge:<22}{fmt(vh, vn):>16}{fmt(ph, pn):>16}{d:>12.0%}")

    vh, vn = rate([r for lab, r in tagged if lab == VISION])
    ph, pn = rate([r for lab, r in tagged if lab == "plan"])
    d = vh / vn - ph / pn
    rng = random.Random(SEED)
    p = permutation_diff(
        [(lab, int(r["judgement"] == "FABRICATED")) for lab, r in tagged], d, rng
    )
    print(f"{'pooled':<22}{fmt(vh, vn):>16}{fmt(ph, pn):>16}{d:>12.0%}")
    print(
        f"\n  permutation p {p:.4f} on the pooled difference. Pooling repeats each\n"
        f"  excerpt once per judge, so this p is anti-conservative; the per-judge rows\n"
        f"  say whether the effect is panel-wide or one judge's habit."
    )
    print(
        f"  {len({r['item'] for lab, r in tagged if lab == VISION})} distinct vision excerpts from "
        f"{len({r['source_doc'] for lab, r in tagged if lab == VISION})} documents; "
        f"{len({r['item'] for lab, r in tagged if lab == 'plan'})} plan excerpts from "
        f"{len({r['source_doc'] for lab, r in tagged if lab == 'plan'})} documents"
    )


def paired(rows: list[dict], pool: dict[str, dict]) -> None:
    """Within-institution: the same university's vision document and plan."""
    cells: dict[tuple[str, str, str], list[int]] = defaultdict(list)
    for r in rows:
        rec = pool.get(r["item"])
        if not rec:
            continue
        lab = label(rec)
        inst = rec.get("institution")
        if not lab or not inst:
            continue
        cells[(r["judge"], inst, lab)].append(int(r["judgement"] == "FABRICATED"))

    institutions = sorted(
        {
            inst
            for (_, inst, lab) in cells
            if lab == VISION and any((j, inst, "plan") in cells for j, _, _ in cells)
        }
    )
    print("\n=== within-institution pairs ===\n")
    if not institutions:
        print("  no institution contributes both a vision document and a plan")
        return
    print(f"  {len(institutions)} institutions: {', '.join(institutions)}\n")
    print(f"{'judge':<22}{'vision':>16}{'plan':>16}{'difference':>13}")

    diffs: list[float] = []
    judges = sorted({j for j, _, _ in cells})
    for judge in judges:
        v = [f for inst in institutions for f in cells.get((judge, inst, VISION), [])]
        p = [f for inst in institutions for f in cells.get((judge, inst, "plan"), [])]
        if not v or not p:
            continue
        d = sum(v) / len(v) - sum(p) / len(p)
        diffs.append(d)
        print(
            f"{judge:<22}{fmt(sum(v), len(v)):>16}{fmt(sum(p), len(p)):>16}{d:>12.0%}"
        )

    if not diffs:
        return
    pos = sum(d > 0 for d in diffs)
    neg = sum(d < 0 for d in diffs)
    # Sign test over judges. The unit is the judge, not the excerpt: within one
    # judge the same institutions are compared to themselves, so house style,
    # country, tier and age are all held constant and only the register moves.
    n = pos + neg
    p_two = (
        sum(_choose(n, k) for k in range(0, min(pos, neg) + 1)) * 2 / 2**n
        if n
        else float("nan")
    )
    print(
        f"\n  sign test over {n} judges with a non-zero difference: "
        f"{pos} vision-worse, {neg} plan-worse, p {min(p_two, 1.0):.4f}"
    )
    print(
        "  House style, country, tier and document age are all held constant here,\n"
        "  which the unpaired contrasts cannot claim. What is NOT held constant is\n"
        "  publication date: an institution's vision document and its ordinary plan\n"
        "  are rarely of the same year."
    )


def _choose(n: int, k: int) -> int:
    from math import comb

    return comb(n, k)


# Two rival explanations for the effect, both testable here.


# 1. Vagueness in disguise. Vision excerpts sit higher on the lexical vagueness
#    index than ordinary plans, and vagueness is what the judges name. If the
#    contrast survives inside a vagueness stratum it is not the index restated.
def stratified(rows: list[dict], pool: dict[str, dict]) -> None:
    path = RESULTS / "vagueness-proxies.json"
    if not path.exists():
        print("\n=== within vagueness strata ===\n  (no proxies file)")
        return
    idx = {
        r["item"]: r["vagueness_index"]
        for r in json.loads(path.read_text())
        if r.get("item")
    }
    tagged = [
        (label(pool[r["item"]]), r)
        for r in rows
        if r["item"] in pool and label(pool[r["item"]]) and r["item"] in idx
    ]
    if not tagged:
        return
    scores = sorted(idx[r["item"]] for _, r in tagged)
    cut = scores[len(scores) // 2]

    print("\n=== within vagueness strata ===\n")
    print(f"  median vagueness index {cut:.2f}; the contrast is run inside each half\n")
    print(f"{'stratum':<24}{'vision':>16}{'plan':>16}{'difference':>13}")
    for name, keep in (
        ("less vague half", lambda v: v <= cut),
        ("vaguer half", lambda v: v > cut),
    ):
        xs = [(lab, r) for lab, r in tagged if keep(idx[r["item"]])]
        vh, vn = rate([r for lab, r in xs if lab == VISION])
        ph, pn = rate([r for lab, r in xs if lab == "plan"])
        d = (vh / vn - ph / pn) if vn and pn else float("nan")
        print(f"{name:<24}{fmt(vh, vn):>16}{fmt(ph, pn):>16}{d:>12.0%}")
    mv = mean_index([r for lab, r in tagged if lab == VISION], idx)
    mp = mean_index([r for lab, r in tagged if lab == "plan"], idx)
    print(f"\n  mean vagueness index: vision {mv:.2f}, plan {mp:.2f}")


def mean_index(rows: list[dict], idx: dict[str, float]) -> float:
    xs = [idx[r["item"]] for r in rows if r["item"] in idx]
    return sum(xs) / len(xs) if xs else float("nan")


# 2. Extraction damage. A vision document is a design-led brochure --- pull
#    quotes, display type, marginal text, multi-column spreads --- and
#    pdftotext mangles that harder than it mangles a text-heavy plan. Damage
#    points real -> fabricated, which is the direction that manufactures this
#    finding. The judges say which they reacted to, so count it: a keyword
#    split of the stated reason, indicative rather than exact, but the two
#    vocabularies barely overlap in practice.
SURFACE = (
    "grammatical",
    "grammar",
    "typo",
    "malformed",
    "merged",
    "punctuation",
    "garbled",
    "artifact",
    "artefact",
    "glitch",
    "misspell",
    "spelling",
    "missing a separator",
    "duplicated",
    "repetition '",
    "mid-sentence",
    "fragment",
    "incoherence",
    "disjointed",
    "awkward",
    "unnatural",
    "inconsistent hyphen",
    "non-standard",
)
REGISTER = (
    "generic",
    "aspirational",
    "buzzword",
    "vague",
    "slogan",
    "boilerplate",
    "platitude",
    "no concrete",
    "without concrete",
    "lacks concrete",
    "abstractions",
    "clich",
    "sweeping",
    "promotional",
    "grandiose",
    "superlative",
)


def reasons(rows: list[dict], pool: dict[str, dict]) -> None:
    print("\n=== what the vision-document errors cite ===\n")
    print(
        f"{'judge':<22}{'errors':>8}{'register':>10}{'surface':>9}{'both':>7}{'neither':>9}"
    )
    per: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        rec = pool.get(r["item"])
        if not rec or label(rec) != VISION or r["judgement"] != "FABRICATED":
            continue
        per[r["judge"]].append((r.get("reason") or "").lower())

    tot = [0, 0, 0, 0]
    for judge, xs in sorted(per.items()):
        c = [0, 0, 0, 0]
        for text in xs:
            s = any(k in text for k in SURFACE)
            g = any(k in text for k in REGISTER)
            c[
                0 if (g and not s) else 1 if (s and not g) else 2 if (s and g) else 3
            ] += 1
        tot = [a + b for a, b in zip(tot, c)]
        print(f"{judge:<22}{len(xs):>8}{c[0]:>10}{c[1]:>9}{c[2]:>7}{c[3]:>9}")
    print(f"{'pooled':<22}{sum(tot):>8}{tot[0]:>10}{tot[1]:>9}{tot[2]:>7}{tot[3]:>9}")
    print(
        "\n  Keyword split, so read the shape and not the decimals. What matters is\n"
        "  whether the judges that carry the effect are reacting to the register or to\n"
        "  damage our own pipeline introduced --- the second would make this finding an\n"
        "  artefact of typesetting rather than a fact about institutional prose."
    )


def main() -> None:
    pool = load_pool()
    headline = load_side(RESULTS)
    arm = load_side(ARM_RESULTS) if ARM_RESULTS.exists() else []
    if not headline and not arm:
        raise SystemExit("no judgements yet --- run judge.py first")

    print(
        f"{len(headline)} real-side strategy judgements in the headline sample, "
        f"{len(arm)} in the vision arm"
    )

    # An excerpt drawn into both sets was judged twice by the same judge. For
    # the unpaired contrast that would be double counting, so the headline
    # answer wins and the arm supplies only what the headline never showed.
    seen = {(r["judge"], r["item"]) for r in headline}
    merged = headline + [r for r in arm if (r["judge"], r["item"]) not in seen]
    contrast("unpaired, headline + arm pooled", merged, pool)
    contrast("the vision arm alone", arm, pool)
    paired(merged, pool)
    stratified(merged, pool)
    reasons(merged, pool)


if __name__ == "__main__":
    main()
