#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Sample the balanced, order-randomised, tag-density-matched stimulus set.

Redaction is symmetric in *method* but not in *effect*: real documents name far
more real entities, so they end up carrying more redaction tags. Left alone,
tag count would be a cue that has nothing to do with the question. This sampler
therefore matches the two sides on tag density within each condition, and
reports the residual difference.
"""

from __future__ import annotations

import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent.parent
POOL = SCRATCH / "stimuli" / "pool_redacted.json"
OUT = SCRATCH / "stimuli" / "stimuli.json"

SEED = 20260801
QUOTA = {"strategy": (16, 16), "impact": (12, 12)}
MAX_PER_DOC = 3
CALIPER = 0.50  # max tolerated tags/100w difference within a matched pair

STATUTORY = {
    "real-impact-anu",
    "real-impact-edinburgh",
    "real-impact-ucl",
    "real-impact-tudelft",
}

TAG_RE = re.compile(r"\[(?:ORGANISATION|PERSON|PLACE|REF)\]")


def doc_key(s: dict) -> str:
    return s["id"].rsplit("--", 1)[0]


def density(s: dict) -> float:
    return len(TAG_RE.findall(s["text_redacted"])) / max(s["words"], 1) * 100


def matched_pick(
    fab: list[dict], real: list[dict], n: int, rng: random.Random
) -> tuple[list[dict], list[dict]]:
    """Global greedy 1:1 matching on tag density, within a caliper.

    Every fabricated x real pair is scored by absolute tag-density difference;
    pairs are accepted cheapest-first subject to a caliper and a per-source-
    document cap, so the two samples end up with near-identical tag-density
    distributions and no single document dominates either side.
    """
    rng.shuffle(fab)
    rng.shuffle(real)
    pairs = sorted(
        (
            (abs(density(f) - density(r)), i, j)
            for i, f in enumerate(fab)
            for j, r in enumerate(real)
        ),
        key=lambda t: t[0],
    )
    used_f: Counter = Counter()
    used_r: Counter = Counter()
    taken_f: set[int] = set()
    taken_r: set[int] = set()
    pf, pr = [], []
    for delta, i, j in pairs:
        if len(pf) >= n or delta > CALIPER:
            break
        if i in taken_f or j in taken_r:
            continue
        f, r = fab[i], real[j]
        if used_f[doc_key(f)] >= MAX_PER_DOC or used_r[doc_key(r)] >= MAX_PER_DOC:
            continue
        taken_f.add(i)
        taken_r.add(j)
        used_f[doc_key(f)] += 1
        used_r[doc_key(r)] += 1
        pf.append(f)
        pr.append(r)
    return pf, pr


def main() -> None:
    rng = random.Random(SEED)
    pool = json.loads(POOL.read_text())

    chosen: list[dict] = []
    for cond, (nf, _nr) in QUOTA.items():
        fab = [s for s in pool if s["condition"] == cond and s["truth"] == "fabricated"]
        real = [s for s in pool if s["condition"] == cond and s["truth"] == "real"]
        pf, pr = matched_pick(fab, real, nf, rng)
        chosen += pf + pr

    for s in chosen:
        if s["truth"] == "real" and s["condition"] == "impact":
            s["subtype"] = (
                "real-statutory" if doc_key(s) in STATUTORY else "real-glossy"
            )
        s["tag_density"] = round(density(s), 2)

    rng.shuffle(chosen)
    for i, s in enumerate(chosen, 1):
        s["item"] = f"E{i:03d}"

    OUT.write_text(json.dumps(chosen, indent=1))

    print(f"sampled {len(chosen)}")
    for k, v in sorted(
        Counter((s["condition"], s["truth"], s["subtype"]) for s in chosen).items()
    ):
        print("  ", k, v)
    print("distinct source docs:", len({doc_key(s) for s in chosen}))
    for cond in QUOTA:
        for t in ("fabricated", "real"):
            xs = [s for s in chosen if s["truth"] == t and s["condition"] == cond]
            if not xs:
                continue
            d = [s["tag_density"] for s in xs]
            w = [s["words"] for s in xs]
            print(
                f"  {cond:9} {t:11} n={len(xs):2d} "
                f"words={sum(w) / len(w):5.0f} tags/100w={sum(d) / len(d):.2f}"
            )


if __name__ == "__main__":
    main()
