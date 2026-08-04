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

**Item ids are stable across re-samples.** They were positional (`E001`, `E002`
... assigned after a shuffle), which is fine for a study run once and fatal for
one meant to grow: adding documents re-runs the greedy matching, every id shifts
to a different excerpt, and a judgements file from the previous run silently
joins to the wrong stimuli. Ids are now derived from the excerpt's own identity,
so a judgement stays attached to the thing that was judged. Extending the corpus
then means judging only the items that are new and pooling with what exists,
instead of paying to re-judge the lot.

The sidecar `stimuli/manifest.json` fingerprints the set. `judge.py` stamps that
fingerprint into its results, so mixing runs is detectable rather than invisible.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ids import item_id, text_sha  # noqa: E402

SCRATCH = Path(__file__).resolve().parent.parent
POOL = SCRATCH / "stimuli" / "pool_redacted.json"
OUT = SCRATCH / "stimuli" / "stimuli.json"
MANIFEST = SCRATCH / "stimuli" / "manifest.json"

SEED = 20260801
# How many matched pairs to draw per condition. `None` means "as many as the
# caliper and the per-document cap allow" --- with a hundred-odd real documents
# the binding constraint should be the data, not a constant left over from a
# 54-item pilot. An integer still forces a fixed n.
#
# The impact condition was dropped for run 4 (TASK-011, TASK-009 item 4). It
# never had more than 26 items, and every judge's near-perfect score on it came
# from accounting and audit boilerplate that a fabricated impact report has no
# reason to carry --- a genre difference, not a discrimination result. The paper
# already quoted the strategy condition alone, so the arm was buying a number
# that could not be used. Its documents stay in the corpus and in the
# corpus-level measurements; only the judged sample drops it.
QUOTA: dict[str, int | None] = {"strategy": None}
MAX_PER_DOC = 3
CALIPER = 0.50  # max tolerated tags/100w difference within a matched pair

# The arm takes every prose excerpt a vision document yielded, not three of
# them. The per-document cap exists to stop one document dominating a sample
# whose unit of analysis is the excerpt; here the unit of analysis is the
# document, and vision documents are short design-led brochures that yield
# few prose paragraphs to begin with.
ARM_MAX_PER_DOC = 4

ARM_OUT = SCRATCH / "stimuli" / "arm_vision.json"
ARM_MANIFEST = SCRATCH / "stimuli" / "arm_vision_manifest.json"

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
    fab: list[dict],
    real: list[dict],
    n: int,
    rng: random.Random,
    cap: int = MAX_PER_DOC,
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
        if used_f[doc_key(f)] >= cap or used_r[doc_key(r)] >= cap:
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
    for cond, quota in QUOTA.items():
        fab = [s for s in pool if s["condition"] == cond and s["truth"] == "fabricated"]
        # `real-pair` documents were gathered for the vision arm, not for the
        # headline sample; including them would let a sub-study change the
        # headline table.
        real = [
            s
            for s in pool
            if s["condition"] == cond
            and s["truth"] == "real"
            and s["subtype"] == "real"
        ]
        # An unbounded request is capped by the caliper and MAX_PER_DOC anyway;
        # the ceiling is whichever side has fewer usable excerpts.
        n = quota if quota is not None else min(len(fab), len(real))
        pf, pr = matched_pick(fab, real, n, rng)
        chosen += pf + pr

    fingerprint = finalise(chosen, OUT, MANIFEST)
    summarise(chosen, "headline sample", fingerprint)

    # The arm's manifest records which of its items the headline sample also
    # carries: same judge, same text, two independent elicitations, which is
    # the run-to-run variability the panel has never been measured for.
    headline_items = {s["item"] for s in chosen}
    arm = vision_arm(pool, rng)
    arm_fingerprint = finalise(
        arm,
        ARM_OUT,
        ARM_MANIFEST,
        extra=lambda xs: {
            "repeated_from_headline": sorted({s["item"] for s in xs} & headline_items)
        },
    )
    summarise(arm, "vision arm", arm_fingerprint)
    repeated = {s["item"] for s in arm} & headline_items
    print(f"   {len(repeated)} items also in the headline sample (repeatability set)")


def finalise(
    chosen: list[dict],
    out: Path,
    manifest: Path,
    extra: Callable[[list[dict]], dict] | None = None,
) -> str:
    for s in chosen:
        if s["truth"] == "real" and s["condition"] == "impact":
            s["subtype"] = (
                "real-statutory" if doc_key(s) in STATUTORY else "real-glossy"
            )
        s["tag_density"] = round(density(s), 2)
        # Stable, content-derived ids. A judgement keyed on one of these stays
        # attached to the excerpt that was actually judged, however the pool
        # grows --- and an excerpt drawn into both the headline sample and the
        # arm gets the SAME id in both, which is what makes the two elicitations
        # comparable item for item.
        s["item"] = item_id(s["id"])

    chosen.sort(key=lambda s: s["item"])
    if len({s["item"] for s in chosen}) != len(chosen):
        raise SystemExit("id collision --- widen the hash prefix")

    out.write_text(json.dumps(chosen, indent=1))

    # Over the text, not just the ids. Ids survive a rebuild, so a fingerprint
    # taken over ids alone reports "same stimulus set" after the excerpts under
    # those ids have changed --- which is the failure this sidecar exists to
    # make visible.
    fingerprint = hashlib.sha1(
        "".join(
            f"{s['item']}:{text_sha(s['text_redacted'])}"
            for s in sorted(chosen, key=lambda s: s["item"])
        ).encode()
    ).hexdigest()[:16]
    manifest.write_text(
        json.dumps(
            {
                "fingerprint": fingerprint,
                "n": len(chosen),
                "seed": SEED,
                "caliper": CALIPER,
                "max_per_doc": MAX_PER_DOC,
                "by_condition": {
                    f"{c}-{t}": sum(
                        1 for s in chosen if s["condition"] == c and s["truth"] == t
                    )
                    for c in {s["condition"] for s in chosen}
                    for t in ("fabricated", "real")
                },
                **(extra(chosen) if extra else {}),
            },
            indent=1,
        )
        + "\n"
    )
    return fingerprint


def summarise(chosen: list[dict], label: str, fingerprint: str) -> None:
    print(f"\n{label}: {len(chosen)} items  fingerprint {fingerprint}")
    for k, v in sorted(
        Counter((s["condition"], s["truth"], s["subtype"]) for s in chosen).items()
    ):
        print("  ", k, v)
    print("  distinct source docs:", len({doc_key(s) for s in chosen}))
    for cond in sorted({s["condition"] for s in chosen}):
        for t in ("fabricated", "real"):
            xs = [s for s in chosen if s["truth"] == t and s["condition"] == cond]
            if not xs:
                continue
            d = [s["tag_density"] for s in xs]
            w = [s["words"] for s in xs]
            print(
                f"  {cond:9} {t:11} n={len(xs):3d} "
                f"words={sum(w) / len(w):5.0f} tags/100w={sum(d) / len(d):.2f}"
            )


def vision_arm(pool: list[dict], rng: random.Random) -> list[dict]:
    """The arm that tests the vision-document effect with real power.

    The headline sample is capped by the fabricated side --- 30 press strategy
    PDFs --- so a plain re-run draws whatever vision excerpts the tag-density
    matching happens to pick, which in run 4 was seven. Seven excerpts cannot
    replicate or refute anything. This arm therefore takes every vision
    document up to the per-document cap, adds the ordinary strategic plans
    gathered from the SAME institutions, and matches the lot against fabricated
    excerpts drawn afresh from the same pool the headline sample used.

    Reusing fabricated excerpts across the two sets is deliberate. It keeps the
    presented set balanced, so the judge prompt's stated 50/50 base rate stays
    true and the instrument is identical to the headline run --- and because
    ids are content-derived, every reused excerpt is the same judge reading the
    same text a second time, which is exactly the run-to-run variability
    measurement the panel has never had.
    """

    def capped(cands: list[dict]) -> list[dict]:
        by_doc: dict[str, list[dict]] = defaultdict(list)
        for s in sorted(cands, key=lambda s: s["id"]):
            by_doc[doc_key(s)].append(s)
        return [s for xs in by_doc.values() for s in xs[:ARM_MAX_PER_DOC]]

    real = capped(
        [
            s
            for s in pool
            if s["condition"] == "strategy"
            and s["truth"] == "real"
            and s["subtype"] == "real"
            and s.get("doc_type") == "vision"
        ]
    ) + capped([s for s in pool if s["subtype"] == "real-pair"])

    fab = [
        s for s in pool if s["condition"] == "strategy" and s["truth"] == "fabricated"
    ]
    pf, pr = matched_pick(fab, list(real), len(real), rng, cap=ARM_MAX_PER_DOC)
    dropped = len(real) - len(pr)
    if dropped:
        print(
            f"  ! {dropped} of {len(real)} arm excerpts found no fabricated partner "
            f"within the {CALIPER} caliper --- dropped to keep the set balanced"
        )
    return pf + pr


if __name__ == "__main__":
    main()
