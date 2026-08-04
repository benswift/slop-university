#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""How much does a judge disagree with itself?

Every small movement this pilot has reported --- a judge up two points between
runs, a repair that "moved no judge's accuracy by more than a point" --- has
been read against an assumption that nobody measured: that the panel is stable
when the text is unchanged. No judge had ever been run twice on identical
stimuli, so "the change is within noise" was an assertion with no noise floor
behind it.

Run 4 supplies one for free. The vision arm reuses fabricated excerpts from the
headline sample to keep its presented set balanced, and item ids are derived
from the excerpt's text, so every reused excerpt is the same judge reading the
same words a second time --- a separate call, a separate results file, an
independently shuffled presentation order, and no shared context between them.

    uv run --script scripts/repeatability.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
ARM_RESULTS = RESULTS / "arm-vision"
ARM_MANIFEST = ROOT / "stimuli" / "arm_vision_manifest.json"


def load(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    return {
        r["item"]: r
        for r in json.loads(path.read_text())
        if r.get("judgement") and r.get("item")
    }


def main() -> None:
    if not ARM_RESULTS.exists():
        raise SystemExit("no arm judgements --- run judge.py --stimuli arm_vision")

    repeated = set(json.loads(ARM_MANIFEST.read_text())["repeated_from_headline"])
    print(f"{len(repeated)} excerpts appear in both the headline sample and the arm\n")
    print(
        f"{'judge':<22}{'n':>5}{'agree':>14}{'flips to FAB':>14}"
        f"{'flips to REAL':>15}{'mean |dconf|':>14}"
    )

    totals = [0, 0]
    for path in sorted(RESULTS.glob("judgements-*.json")):
        a = load(path)
        b = load(ARM_RESULTS / path.name)
        if not b:
            continue
        items = [i for i in sorted(repeated) if i in a and i in b]
        if not items:
            continue
        same = sum(a[i]["judgement"] == b[i]["judgement"] for i in items)
        to_fab = sum(
            a[i]["judgement"] == "REAL" and b[i]["judgement"] == "FABRICATED"
            for i in items
        )
        to_real = sum(
            a[i]["judgement"] == "FABRICATED" and b[i]["judgement"] == "REAL"
            for i in items
        )
        confs = [
            abs(a[i]["confidence"] - b[i]["confidence"])
            for i in items
            if isinstance(a[i].get("confidence"), (int, float))
            and isinstance(b[i].get("confidence"), (int, float))
        ]
        dconf = sum(confs) / len(confs) if confs else float("nan")
        judge = path.stem.removeprefix("judgements-")
        print(
            f"{judge:<22}{len(items):>5}{f'{same}/{len(items)} = {same / len(items):.0%}':>14}"
            f"{to_fab:>14}{to_real:>15}{dconf:>14.1f}"
        )
        totals[0] += same
        totals[1] += len(items)

    if totals[1]:
        print(
            f"\n{'pooled':<22}{totals[1]:>5}"
            f"{f'{totals[0]}/{totals[1]} = {totals[0] / totals[1]:.0%}':>14}"
        )
        print(
            f"\nThe disagreement rate is {1 - totals[0] / totals[1]:.1%} pooled. That is the\n"
            "floor under every per-judge comparison in this report: a difference smaller\n"
            "than a judge's disagreement with itself is not evidence of anything.\n"
            "\n"
            "Note what this does and does not measure. Both elicitations are of the same\n"
            "text under the same prompt, so it captures sampling variability in the\n"
            "decoder and nothing else --- not drift in a served model, and not\n"
            "sensitivity to rewording the prompt."
        )


if __name__ == "__main__":
    main()
