#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""Draw a publish run's givens outside the model, like select-preset.sh.

A model left to choose a run's discipline, subject or lead author converges on
its favourites, and two slots reading the same corpus choose alike. So the
givens are drawn here, with OS randomness, and passed on the invocation line;
everything else about the piece is the run's own judgement (the brief is
`skills/from-preset/genre.md`).

A 2A run is given three things:

- a **subject**, from `canon/subjects.tsv` --- what the piece is about. The
  pool is a snapshot of OpenAlex's research topics (CC0), drawn field-first so
  the fields are equally likely whatever their topic counts. Left free, the
  subject was the one choice every run made alike (a humble everyday object,
  every time). `ops/subject-primer.py` prints real recent titles for the drawn
  id. The Health Sciences domain is never drawn: a fabricated paper that looks
  clinical is the one kind that could hurt someone who believed it.
- a **tradition** --- the scholarly tradition the piece is written from.
  Usually the subject's own field. One run in three (CROSS_READING_SHARE) it
  is instead drawn from the pool in `canon/axes.yml`, independently of the
  subject, so that some of the corpus is one discipline reading another's
  material; all of it would be a formula.
- a **lead author** and, with them, the output's school, drawn from the
  `--root` checkout's `canon/roster.yml` against its live attribution counts,
  inversely weighted so the draw corrects imbalance instead of a run inferring
  it. Two stages, because the two imbalances are separate: school first (by
  that school's share of published outputs), then a lead author inside it (by
  their share of lead authorships).

The pools are doctrine and are read from this script's own checkout, never
from `--root`.

Some presets fix the school, and a draw that does not know which preset it is
drawing for can contradict the document it is drawing for. `impact-report`
is the School of Continuous Improvement's own report, and on 2026-08-26 the
draw handed one to a professor of Emergent Priorities. The agent, correctly,
refused to guess past it and asked; unattended, that asked nobody and cost the
tick. So `--preset` confines the school stage to whatever the blueprint's
`school:` says.

Usage:
  ops/draw-axes.py                     # prose lines, for the /publish invocation
  ops/draw-axes.py --json              # the same draw as JSON, for spread checks
  ops/draw-axes.py --root <checkout>   # draw against another checkout's corpus
  ops/draw-axes.py --preset <name>     # honour that preset's fixed school
  ops/draw-axes.py --thesis            # a thesis run's fiction: setting, school, supervisors

A thesis run (rung 2T, run by hand) draws neither tradition nor subject: its
blueprint gives that run its own licence. What it does draw is a setting from
`canon/axes.yml`, the school the new doctoral candidate joins, and two
supervisors from that school, the primary weighted exactly as a lead author
is. `canon/burnt-shapes.yml` retires values from the thesis pools.
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
SUBJECTS_PATH = DOCTRINE_DIR / "canon/subjects.tsv"
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

# The one roster title that cannot supervise; see thesis_slot().
DOCTORAL_TITLE = "Doctoral Candidate"

# The pools canon/axes.yml must carry: one a 2A run draws from, and the two the
# thesis reads.
POOL_AXES = ("tradition", "finding-shape", "setting")

CROSS_READING_SHARE = 1 / 3
UNDRAWN_DOMAINS = frozenset({"Health Sciences"})

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


def load_axes() -> dict[str, list[dict]]:
    """The static pools, with retired values removed.

    An `excludes:` id may name a value on any pool axis, not just a
    finding-shape: a title form can be spent the same way a study design can."""
    axes = yaml.safe_load(AXES_PATH.read_text())
    missing = [axis for axis in POOL_AXES if not axes.get(axis)]
    if missing:
        sys.exit(f"canon/axes.yml has no values for: {missing}")

    retired = {
        shape for entry in burnt_entries() for shape in (entry.get("excludes") or [])
    }

    unknown = retired - {e["id"] for axis in POOL_AXES for e in axes[axis]}
    if unknown:
        # A typo in an `excludes:` would silently retire nothing, which is the
        # one failure mode of this file that nobody would notice.
        sys.exit(f"burnt-shapes.yml excludes unknown pool id(s): {sorted(unknown)}")

    for axis in POOL_AXES:
        axes[axis] = [e for e in axes[axis] if e["id"] not in retired]
        if not axes[axis]:
            sys.exit(f"every {axis} value is retired; nothing left to draw")

    return axes


def draw_subject() -> dict:
    """One research topic, field first.

    OpenAlex files 4,500 topics under 26 fields very unevenly (medicine has
    hundreds, the arts and humanities a few dozen), so a uniform draw over
    topics would make the corpus a medical school. Drawing the field first
    gives every part of the academy the same chance."""
    by_field: dict[str, list[dict]] = {}
    for line in SUBJECTS_PATH.read_text().splitlines():
        topic_id, name, field, domain = line.split("\t")
        if domain in UNDRAWN_DOMAINS:
            continue
        by_field.setdefault(field, []).append(
            {"id": topic_id, "name": name, "field": field}
        )
    if not by_field:
        sys.exit(f"{SUBJECTS_PATH} is empty")
    return RNG.choice(by_field[RNG.choice(sorted(by_field))])


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
        school: dict = {"name": fixed, "people": by_school[fixed]}
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


def thesis_slot() -> dict:
    """Draw a thesis run's fiction: the candidate's school and two supervisors.

    The candidate does not exist yet --- the run fabricates them --- so the
    author stage draws the primary supervisor instead, with the inverse
    weighting a lead author gets, and an associate uniformly from the rest of
    the school. A school with nobody else lends its associate from the whole
    remaining roster, uniformly.

    Doctoral candidates are excluded from both supervisor pools, and so from
    the school draw: a student cannot supervise a student. The filter has to be
    here rather than left to the run's judgement because the inverse weighting
    actively selects for candidates --- a candidate's only possible output is
    their own thesis, so they sit at the top of the lead-authorship draw --- and
    every thesis that lands admits another one. On 2026-09-22 the draw named the
    author of the first thesis as a primary supervisor, and the run substituted
    an eligible member without saying so."""
    roster = yaml.safe_load(ROSTER_PATH.read_text())["researchers"]
    schools, leads = attribution_counts()

    supervisors = [p for p in roster if p["title"] != DOCTORAL_TITLE]
    by_school: dict[str, list[dict]] = {}
    for person in supervisors:
        by_school.setdefault(person["school"], []).append(person)

    school = draw(
        [
            {"name": name, "weight": 1 / (1 + schools.get(name, 0)), "people": people}
            for name, people in by_school.items()
        ]
    )
    primary = draw(
        [
            {"person": person, "weight": 1 / (1 + leads.get(person["name"], 0))}
            for person in school["people"]
        ]
    )["person"]
    others = [p for p in school["people"] if p["id"] != primary["id"]]
    if not others:
        others = [p for p in supervisors if p["id"] != primary["id"]]
    associate = RNG.choice(others)
    return {"school": school["name"], "primary": primary, "associate": associate}


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
    parser.add_argument(
        "--thesis",
        action="store_true",
        help="draw a thesis run's fiction (setting, school, supervisors) and nothing else",
    )
    args = parser.parse_args()
    os.chdir(args.root)

    retired = [collapse(entry["shape"]) for entry in burnt_entries()]

    if args.thesis:
        setting = draw(load_axes()["setting"])
        fiction = thesis_slot()
        if args.json:
            print(
                json.dumps(
                    {
                        "setting": setting["id"],
                        "school": fiction["school"],
                        "primary_supervisor": fiction["primary"]["id"],
                        "associate_supervisor": fiction["associate"]["id"],
                    }
                )
            )
            return 0
        print(f"setting: {collapse(setting['value'])}")
        print(f"school: {fiction['school']}")
        for role in ("primary", "associate"):
            person = fiction[role]
            print(
                f"{role} supervisor: {person['name']} ({person['id']}, {person['school']})"
            )
        print("retired finding-shapes, never the primary design: " + "; ".join(retired))
        return 0

    subject = draw_subject()
    if RNG.random() < CROSS_READING_SHARE:
        tradition = draw(load_axes()["tradition"])
    else:
        tradition = {
            "id": "native",
            "value": f"the subject's own field ({subject['field']})",
        }
    author = author_slot(args.preset)

    if args.json:
        print(
            json.dumps(
                {
                    "tradition": tradition["id"],
                    "subject": subject["id"],
                    "subject_name": subject["name"],
                    "lead_author": author["id"],
                    "school": author["school"],
                }
            )
        )
        return 0

    print(f"tradition: {collapse(tradition['value'])}")
    print(
        f"subject: {subject['name']} (id {subject['id']}, filed under {subject['field']})"
    )
    print(f"lead author: {author['name']} ({author['school']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
