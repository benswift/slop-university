#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""Draw a 2A run's enumerable axes outside the model, like select-preset.sh.

The publish skill used to derive these axes by inference: sample twenty
published outputs entries, classify each on six axes, work out the dominant
value, steer away from it. That is a draw done badly, and it fails twice.

It CONVERGES. The sample was weighted towards the newest entries, which read to
a generating model as exemplars rather than as a list of moves to avoid --- over
July and August one topic-sentence frame went from 0% to 93% of weekly output
that way. A draw needs no corpus-tail read at all, which is also why this script
buys throughput: the reads it removes were a meaningful slice of a run.

It COLLIDES. Two runs assessing the same base corpus infer the same dominant
value and steer to the same alternative, so the inference is worse than useless
once 2A slots run concurrently (TASK-12): it actively correlates them. The topic
itself is protected by `ops/topic-claim.py`; nothing else on the list was.

So: the enumerable axes are drawn here, with OS randomness, and passed on the
invocation line. Judgement stays in the skill --- composing a topic that fits
these values, choosing citations by topical fit, deciding whether a bio reads
thin. Constraints first, composition second, which is better generation anyway.

Four axes come from the static pools in `canon/axes.yml`, minus any
finding-shape retired in `canon/burnt-shapes.yml`. Both are doctrine and are
read from this script's own checkout, never from `--root`. The fifth --- the
lead author and, with them, the output's school --- has no static pool: it is
drawn from the `--root` checkout's `canon/roster.yml` against its live
attribution counts, inversely weighted so the draw corrects imbalance instead of
a run inferring it. Two stages, because the two imbalances are separate: school
first (by that school's share of published outputs), then a lead author inside it
(by their share of lead authorships). Every output's school is its lead author's
school, so the school falls out of the author draw and is not a second
decision.

Some presets fix that school, though, and a draw that does not know which preset
it is drawing for can contradict the document it is drawing for. `impact-report`
is the School of Continuous Improvement's own report --- all fifteen published
ones are written by that school about itself --- and on 2026-08-26 the draw
handed one to a professor of Emergent Priorities. The agent, correctly, refused
to guess past it and asked; unattended, that asked nobody and cost the tick. So
`--preset` confines the school stage to whatever the blueprint's `school:` says,
and the author stage inside it is unchanged. Presets that fix no school (most of
them) draw exactly as before.

Usage:
  ops/draw-axes.py                     # prose lines, for the /publish invocation
  ops/draw-axes.py --json              # the same draw as JSON, for spread checks
  ops/draw-axes.py --root <checkout>   # draw against another checkout's corpus
  ops/draw-axes.py --preset <name>     # honour that preset's fixed school
"""

from __future__ import annotations

import argparse
import functools
import json
import os
import random
import sys
from collections import Counter
from pathlib import Path

import yaml

# The pools are doctrine, so they come from the checkout this SCRIPT lives in
# --- a drawer always draws from the pool it shipped with, and the wrapper can
# therefore run against a worktree whose commit predates the pool.
DOCTRINE_DIR = Path(__file__).resolve().parent.parent
AXES_PATH = DOCTRINE_DIR / "canon/axes.yml"
BURNT_PATH = DOCTRINE_DIR / "canon/burnt-shapes.yml"
# A preset's own blueprint is where its doc identity is declared, so it is also
# where a fixed school belongs --- a second copy in this script would be a
# second thing to keep true. Public registry only: the unattended pipeline sets
# SLOPU_PUBLIC_ONLY and can never roll a private preset.
PRESETS_DIR = DOCTRINE_DIR / "skills/from-preset/presets"

# The roster and the outputs ledger are live state, so they come from the
# checkout being drawn against (--root). The cron wrapper points that at the
# press worktree, which it has already reset to the exact state this run will
# build on, so the attribution counts match the corpus the run publishes into
# rather than whatever the human checkout happens to hold.
ROSTER_PATH = Path("canon/roster.yml")
OUTPUTS_DIR = Path("website/src/content/outputs")

# Order matters: it is the order the values reach the agent, and it is the order
# a run should apply them (shape and setting bound the object; the frame and the
# title form dress it).
POOL_AXES = ("finding-shape", "setting", "topic-frame", "title-form")

LABELS = {
    "finding-shape": "finding-shape",
    "setting": "setting",
    "topic-frame": "topic-sentence frame",
    "title-form": "title form",
}

# os.urandom under the hood, so two slots drawing in the same second draw
# independently --- which is the whole point.
RNG = random.SystemRandom()


def collapse(text: str) -> str:
    """One line. YAML folds these across several source lines for readability;
    the invocation line wants them back as sentences."""
    return " ".join(str(text).split())


def draw(pool: list[dict]) -> dict:
    """One weighted value. `weight` defaults to 1 and exists only to ration a
    value the doctrine wants present but rare."""
    weights = [entry.get("weight", 1) for entry in pool]
    return RNG.choices(pool, weights=weights)[0]


@functools.cache
def burnt_entries() -> list[dict]:
    """The retired-shapes ledger. Read once: the draw excludes by `excludes:`
    id, and the run is handed every entry's prose so a composed topic does not
    reinvent a design that was never a pool value in the first place."""
    return yaml.safe_load(BURNT_PATH.read_text()) or []


def pool_axes() -> dict[str, dict]:
    """Draw the four static axes, with retired finding-shapes removed first."""
    axes = yaml.safe_load(AXES_PATH.read_text())
    missing = [axis for axis in POOL_AXES if not axes.get(axis)]
    if missing:
        sys.exit(f"canon/axes.yml has no values for: {missing}")

    retired = {
        shape for entry in burnt_entries() for shape in (entry.get("excludes") or [])
    }

    unknown = retired - {entry["id"] for entry in axes["finding-shape"]}
    if unknown:
        # A typo in an `excludes:` would silently retire nothing, which is the
        # one failure mode of this file that nobody would notice.
        sys.exit(
            f"burnt-shapes.yml excludes unknown finding-shape id(s): {sorted(unknown)}"
        )

    axes["finding-shape"] = [e for e in axes["finding-shape"] if e["id"] not in retired]
    if not axes["finding-shape"]:
        sys.exit("every finding-shape is retired; nothing left to draw")

    return {axis: draw(axes[axis]) for axis in POOL_AXES}


def attribution_counts() -> tuple[Counter, Counter]:
    """Published outputs per school, and lead authorships per researcher name.

    Reads the outputs collection --- the canonical record of what shipped. An
    entry with no authors (some ad and brochure runs) still counts towards its
    school; it just names nobody to count as lead."""
    schools: Counter = Counter()
    leads: Counter = Counter()
    for path in sorted(OUTPUTS_DIR.glob("*.yml")):
        entry = yaml.safe_load(path.read_text()) or {}
        if school := entry.get("school"):
            schools[school] += 1
        if authors := entry.get("authors"):
            leads[authors[0]] += 1
    return schools, leads


def preset_school(preset: str | None) -> str | None:
    """The school a preset's blueprint fixes, or None if it fixes none.

    Scans the frontmatter for the one key it wants rather than parsing the
    block, because a blueprint's frontmatter is a human document and its
    `description:` is prose. `marketing-poster` has "(the e-signage panels'
    native aspect): the snazzy, ..." in its, which is a colon inside a plain
    scalar and makes PyYAML throw --- so a parse here would take the tenth of
    all ticks that roll that preset down with it, over a comma in a sentence
    nobody thought was load-bearing.

    Exits on a preset that has no blueprint. A typo would otherwise read as
    "this preset fixes no school" and silently restore the very draw this
    argument exists to constrain --- the same failure mode as a misspelt
    `excludes:` id above, and just as invisible."""
    if not preset:
        return None
    blueprint = PRESETS_DIR / f"{preset}.md"
    if not blueprint.is_file():
        sys.exit(f"no preset blueprint at {blueprint}")
    lines = blueprint.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        sys.exit(f"{blueprint} has no frontmatter")
    for line in lines[1:]:
        if line.strip() == "---":
            break
        # Top-level key only: a `school:` indented under something else belongs
        # to that something else.
        if line.startswith("school:"):
            return line.removeprefix("school:").strip().strip("\"'") or None
    return None


def author_slot(preset: str | None = None) -> dict:
    """Draw a lead author, inversely weighted by how much the corpus already
    leans on their school and on them.

    Inverse weighting rather than "pick the least-represented": the minimum is a
    function of shared state, so two slots computing it agree, which is exactly
    the collision this script exists to remove. A weighted draw corrects the
    same imbalance in expectation while staying independent per slot. 1/(1+n)
    keeps a fresh researcher's weight finite and, at today's spread, gives the
    thinnest-published roughly three times the pull of the heaviest.

    A preset that fixes its school skips the school stage entirely; the
    correction still operates where it can, over that school's own people."""
    roster = yaml.safe_load(ROSTER_PATH.read_text())["researchers"]
    schools, leads = attribution_counts()

    by_school: dict[str, list[dict]] = {}
    for person in roster:
        by_school.setdefault(person["school"], []).append(person)

    if fixed := preset_school(preset):
        if fixed not in by_school:
            # The blueprint names a school no researcher belongs to, so there is
            # nobody to lead the document. Loud, because the alternative is a
            # run authored by whoever the unconstrained draw happened to pick.
            sys.exit(
                f"preset '{preset}' fixes school {fixed!r}, "
                f"which no researcher in {ROSTER_PATH} belongs to"
            )
        school = {"name": fixed, "people": by_school[fixed]}
    else:
        school_pool = [
            {
                "name": school,
                "weight": 1 / (1 + schools.get(school, 0)),
                "people": people,
            }
            for school, people in by_school.items()
        ]
        school = draw(school_pool)

    people_pool = [
        {"person": person, "weight": 1 / (1 + leads.get(person["name"], 0))}
        for person in school["people"]
    ]
    person = draw(people_pool)["person"]

    return {
        "id": person["id"],
        "name": person["name"],
        "school": school["name"],
        "lead_authorships": leads.get(person["name"], 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of prose"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path("."),
        help="checkout to draw against (default: the working directory)",
    )
    parser.add_argument(
        "--preset",
        help="the preset this run rolled, so a fixed school constrains the draw",
    )
    args = parser.parse_args()
    os.chdir(args.root)

    drawn = pool_axes()
    author = author_slot(args.preset)
    retired = [collapse(entry["shape"]) for entry in burnt_entries()]

    if args.json:
        payload = {axis: drawn[axis]["id"] for axis in POOL_AXES}
        payload["lead_author"] = author["id"]
        payload["school"] = author["school"]
        print(json.dumps(payload))
        return 0

    for axis in POOL_AXES:
        print(f"{LABELS[axis]}: {collapse(drawn[axis]['value'])}")
    print(f"lead author: {author['name']} ({author['school']})")
    print("retired finding-shapes, never the primary design: " + "; ".join(retired))
    return 0


if __name__ == "__main__":
    sys.exit(main())
