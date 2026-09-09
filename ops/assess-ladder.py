#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml>=6"]
# ///
"""Assess the /publish gap ladder deterministically, outside the model.

The publish skill used to assess "1. Assess the department" itself, each
tick: read the same canon and content files a fresh model would, then choose
the first rung of the ladder that fired. That worked until the invocation
line started naming a 2A preset alongside the ladder instructions --- the
model anchored on 2A regardless of what the ladder actually said, and rung
2H (institutional news) went seventeen days without firing (2026-08-25 to
2026-09-10) while the newsroom sat stale. A script cannot anchor on a preset
name it never sees, costs no generation tokens to run, and --- unlike a model
re-deriving the ladder from prose each tick --- gives two concurrent slots
reading the same state the same answer.

This script performs steps 1-8 of the ladder (schools.yml blurbs, roster bio
stubs, the about page, roster/lab coverage, socials, grants, news, and the
2A fallback) and prints the winning rung plus the parameters the chosen
action needs. It does not act on the result --- the cron wrapper hands the
decision to the agent, which still performs the write.

Rung 2D (thin about page): the live about.md runs 227 words at the time this
script was written, so the floor is set at 200 --- under the current page,
clear of the false-positive that would otherwise fire every tick.

Rung 2I (award a grant) used to fire on "two or more authored outputs and no
grant at all". That gate exhausted itself on 2026-08-06, once every active
researcher held at least one grant, and the rung went quiet for five weeks.
A lag rule --- outputs authored since a researcher's most recent grant,
against all their outputs if they hold none --- keeps awarding as the corpus
keeps growing instead of stopping once the roster is "covered" once.

Usage:
  ops/assess-ladder.py                  # human-readable decision
  ops/assess-ladder.py --json           # the same decision as JSON
  ops/assess-ladder.py --root <dir>     # assess another checkout (default: cwd)
  ops/assess-ladder.py --only-2a        # concurrent generator slot: always 2A
  ops/assess-ladder.py --no-network     # skip the Bluesky feed fetch (2G)
  ops/assess-ladder.py --now <iso>      # override the clock, for tests
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

# Sections of canon/schools.yml that name an org unit with a blurb. `history`
# is deliberately excluded --- it records what the University used to be
# called, not something a run can edit forward.
SCHOOL_SECTIONS = ("schools", "units", "labs", "programs", "initiatives")

# Below this word count, or at a single sentence, a bio reads as a stub
# regardless of length --- a fluent one-clause placeholder is still a stub.
BIO_STUB_WORDS = 25
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")

# The live about.md runs 227 words (see module docstring); set the floor
# comfortably under that so the current page does not trip it.
ABOUT_STUB_WORDS = 200

ROSTER_CAP = 24
OUTPUTS_PER_RESEARCHER = 12

SOCIALS_QUIET_HOURS = 20
GRANTS_STALE_DAYS = 2
FUNDING_LAG_FLOOR = 3
NEWS_STALE_DAYS = 3
NEWS_KINDS = ("event", "appointment", "milestone")

BLUESKY_FEED_URL = (
    "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
    "?actor=slop.university&limit=5"
)


class MalformedInput(Exception):
    """A canon or content file doesn't match the shape this script expects."""


def parse_date(value: object) -> dt.date:
    """Parse a ledger date. Dates in the ledger are ISO, sometimes quoted,
    sometimes carrying a time and offset --- take the date component and
    ignore the rest, since every ladder rung reasons in whole days."""
    text = str(value).strip().strip("\"'")
    try:
        return dt.datetime.fromisoformat(text).date()
    except ValueError as exc:
        raise MalformedInput(f"unparseable date {value!r}") from exc


def resolve_now(now_arg: str | None) -> dt.datetime:
    """The clock this run reasons against: real time, or --now for tests."""
    if now_arg is None:
        return dt.datetime.now(dt.UTC)
    text = now_arg.strip().strip("\"'")
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError as exc:
        raise MalformedInput(f"unparseable --now {now_arg!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.UTC)
    return parsed


def iso(value: dt.date | None) -> str | None:
    return value.isoformat() if value is not None else None


def read_frontmatter(path: Path) -> dict:
    """The YAML block between the first two `---` lines of a .md file."""
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        raise MalformedInput(f"{path} has no frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise MalformedInput(f"{path} frontmatter never closes")
    data = yaml.safe_load("\n".join(lines[1:end]))
    if not isinstance(data, dict):
        raise MalformedInput(f"{path} frontmatter is not a mapping")
    return data


# --- 2C: a school/unit/lab/program/initiative with no blurb ---------------


def load_schools(root: Path) -> dict:
    path = root / "canon" / "schools.yml"
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise MalformedInput(f"{path} is not a mapping")
    return data


def find_missing_blurb(schools: dict) -> dict | None:
    for section in SCHOOL_SECTIONS:
        for entry in schools.get(section) or []:
            blurb = entry.get("blurb")
            if not blurb or not str(blurb).strip():
                return {
                    "id": entry.get("id"),
                    "name": entry.get("name"),
                    "section": section,
                }
    return None


# --- 2B: a roster researcher with a stub bio -------------------------------


def load_roster(root: Path) -> list[dict]:
    path = root / "canon" / "roster.yml"
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or "researchers" not in data:
        raise MalformedInput(f"{path} has no 'researchers' list")
    return data["researchers"]


def is_stub_bio(bio: str) -> bool:
    words = len(bio.split())
    sentences = [s for s in SENTENCE_SPLIT.split(bio.strip()) if s]
    return words < BIO_STUB_WORDS or len(sentences) <= 1


def find_stub_bio(roster: list[dict]) -> dict | None:
    stubs = [p for p in roster if is_stub_bio(p.get("bio", ""))]
    if not stubs:
        return None
    shortest = min(stubs, key=lambda p: len(p.get("bio", "").split()))
    return {"id": shortest["id"], "name": shortest["name"]}


# --- 2D: a thin page (about.md) --------------------------------------------


def about_word_count(root: Path) -> int:
    path = root / "website" / "src" / "content" / "pages" / "about.md"
    lines = path.read_text().splitlines()
    if not lines or lines[0].strip() != "---":
        raise MalformedInput(f"{path} has no frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise MalformedInput(f"{path} frontmatter never closes")
    body = "\n".join(lines[end + 1 :])
    return len(body.split())


# --- 2E/2F: roster and lab coverage against output volume -----------------


def load_outputs(root: Path) -> list[dict]:
    outputs = []
    for path in sorted(
        (root / "website" / "src" / "content" / "outputs").glob("*.yml")
    ):
        entry = yaml.safe_load(path.read_text())
        if not isinstance(entry, dict) or "date" not in entry:
            raise MalformedInput(f"{path} has no 'date' field")
        entry = dict(entry)
        entry["date"] = parse_date(entry["date"])
        outputs.append(entry)
    return outputs


def required_roster_size(output_count: int) -> int:
    return min(ROSTER_CAP, math.ceil(output_count / OUTPUTS_PER_RESEARCHER))


def find_school_without_lab(schools: dict) -> dict | None:
    lab_school_ids = {lab.get("school") for lab in schools.get("labs") or []}
    for school in schools.get("schools") or []:
        if school.get("id") not in lab_school_ids:
            return school
    return None


# --- 2G: socials due ---------------------------------------------------------


def assess_socials(root: Path, now: dt.datetime, no_network: bool) -> dict:
    if (root / "data" / "pending-post.json").exists():
        return {
            "due": False,
            "reason": "a post is already staged",
            "last_post": None,
            "hours_since": None,
        }
    if no_network:
        return {
            "due": False,
            "reason": "--no-network: feed not checked",
            "last_post": None,
            "hours_since": None,
        }

    try:
        with urllib.request.urlopen(BLUESKY_FEED_URL, timeout=10) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "due": False,
            "reason": f"feed fetch failed: {exc}",
            "last_post": None,
            "hours_since": None,
        }

    feed = payload.get("feed") or []
    if not feed:
        return {
            "due": False,
            "reason": "feed empty",
            "last_post": None,
            "hours_since": None,
        }
    try:
        created = dt.datetime.fromisoformat(feed[0]["post"]["record"]["createdAt"])
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "due": False,
            "reason": f"feed shape unexpected: {exc}",
            "last_post": None,
            "hours_since": None,
        }

    hours_since = (now - created).total_seconds() / 3600
    return {
        "due": hours_since > SOCIALS_QUIET_HOURS,
        "reason": None,
        "last_post": created.isoformat(),
        "hours_since": round(hours_since, 2),
    }


# --- 2I: award a grant (funding lag) ---------------------------------------


def load_grants(root: Path) -> list[dict]:
    grants = []
    for path in sorted((root / "website" / "src" / "content" / "grants").glob("*.yml")):
        entry = yaml.safe_load(path.read_text())
        if not isinstance(entry, dict) or "date" not in entry or "scheme" not in entry:
            raise MalformedInput(f"{path} is missing 'date' or 'scheme'")
        entry = dict(entry)
        entry["date"] = parse_date(entry["date"])
        grants.append(entry)
    return grants


def load_grant_schemes(root: Path) -> list[dict]:
    path = root / "canon" / "grants.yml"
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict) or "schemes" not in data:
        raise MalformedInput(f"{path} has no 'schemes' list")
    return data["schemes"]


def find_funding_lag_candidate(
    roster: list[dict], outputs: list[dict], grants: list[dict]
) -> dict | None:
    """The researcher whose authored-output count since their most recent
    grant (or ever, if they hold none) is largest. Ties go to whoever holds
    fewer grants, then alphabetically, so a researcher never falls behind
    just because the corpus happens to have listed them last."""
    grants_by_person: dict[str, list[dt.date]] = {}
    for grant in grants:
        for name in grant.get("grantees") or []:
            grants_by_person.setdefault(name, []).append(grant["date"])

    outputs_by_person: dict[str, list[dt.date]] = {}
    for output in outputs:
        for name in output.get("authors") or []:
            outputs_by_person.setdefault(name, []).append(output["date"])

    candidates = []
    for person in roster:
        name = person["name"]
        grant_dates = sorted(grants_by_person.get(name, []))
        output_dates = outputs_by_person.get(name, [])
        if grant_dates:
            lag = sum(1 for d in output_dates if d > grant_dates[-1])
        else:
            lag = len(output_dates)
        candidates.append(
            {
                "id": person["id"],
                "name": name,
                "lag": lag,
                "grants_held": len(grant_dates),
            }
        )

    if not candidates:
        return None
    candidates.sort(key=lambda c: (-c["lag"], c["grants_held"], c["name"]))
    return candidates[0]


def least_recently_awarded_scheme(schemes: list[dict], grants: list[dict]) -> dict:
    """The scheme id due for its turn: never-awarded first, then whichever
    was last awarded longest ago."""
    last_awarded: dict[str, dt.date] = {}
    for grant in grants:
        scheme_id = grant["scheme"]
        if scheme_id not in last_awarded or grant["date"] > last_awarded[scheme_id]:
            last_awarded[scheme_id] = grant["date"]
    ranked = sorted(
        schemes, key=lambda s: (last_awarded.get(s["id"], dt.date.min), s["id"])
    )
    return ranked[0]


# --- 2H: institutional news due ---------------------------------------------


def load_news_without_output_or_grant(root: Path) -> list[dict]:
    posts = []
    for path in sorted((root / "website" / "src" / "content" / "news").glob("*.md")):
        front = read_frontmatter(path)
        if "output" in front or "grant" in front:
            continue
        if "date" not in front:
            raise MalformedInput(f"{path} frontmatter has no 'date'")
        posts.append({"path": path, "date": parse_date(front["date"])})
    return posts


# --- reporting ---------------------------------------------------------------


def emit(rung: str, reason: str, params: dict, checked: dict, as_json: bool) -> int:
    if as_json:
        print(
            json.dumps(
                {"rung": rung, "reason": reason, "params": params, "checked": checked},
                default=str,
            )
        )
    else:
        print(f"rung: {rung}")
        print(f"reason: {reason}")
        print(f"params: {json.dumps(params, default=str)}")
    return 0


def assess(root: Path, now: dt.datetime, no_network: bool, as_json: bool) -> int:
    checked: dict = {}

    schools = load_schools(root)
    missing_blurb = find_missing_blurb(schools)
    checked["missing_blurb"] = missing_blurb
    if missing_blurb:
        return emit(
            "2C",
            f"{missing_blurb['section']} entry '{missing_blurb['id']}' has no blurb",
            {
                "id": missing_blurb["id"],
                "name": missing_blurb["name"],
                "section": missing_blurb["section"],
            },
            checked,
            as_json,
        )

    roster = load_roster(root)
    stub = find_stub_bio(roster)
    checked["stub_bio"] = stub
    if stub:
        return emit(
            "2B",
            f"{stub['name']}'s bio reads as a stub",
            {"id": stub["id"], "name": stub["name"]},
            checked,
            as_json,
        )

    about_words = about_word_count(root)
    checked["about_words"] = about_words
    if about_words < ABOUT_STUB_WORDS:
        return emit(
            "2D",
            f"about.md body is {about_words} words, under the {ABOUT_STUB_WORDS}-word floor",
            {"page": "about.md", "words": about_words},
            checked,
            as_json,
        )

    outputs = load_outputs(root)
    required = required_roster_size(len(outputs))
    checked["roster_vs_required"] = {"roster": len(roster), "required": required}
    if len(roster) < required:
        return emit(
            "2E",
            f"roster has {len(roster)} researchers against a required {required}",
            {"roster": len(roster), "required": required},
            checked,
            as_json,
        )

    missing_lab_school = find_school_without_lab(schools)
    checked["missing_lab_school"] = (
        missing_lab_school["id"] if missing_lab_school else None
    )
    if missing_lab_school:
        return emit(
            "2F",
            f"{missing_lab_school['name']} has no lab or group",
            {"school": missing_lab_school["id"]},
            checked,
            as_json,
        )

    socials = assess_socials(root, now, no_network)
    checked["socials"] = socials
    if socials["due"]:
        return emit(
            "2G",
            "the account has been quiet past the socials gate",
            {"last_post": socials["last_post"], "hours_since": socials["hours_since"]},
            checked,
            as_json,
        )

    grants = load_grants(root)
    newest_grant_date = max((g["date"] for g in grants), default=None)
    grants_stale = (
        newest_grant_date is None
        or (now.date() - newest_grant_date).days > GRANTS_STALE_DAYS
    )
    lag_candidate = (
        find_funding_lag_candidate(roster, outputs, grants) if grants_stale else None
    )
    fires_2i = (
        grants_stale
        and lag_candidate is not None
        and lag_candidate["lag"] >= FUNDING_LAG_FLOOR
    )
    checked["grants"] = {
        "newest_grant_date": iso(newest_grant_date),
        "stale": grants_stale,
        "candidate": lag_candidate["name"] if lag_candidate else None,
        "candidate_lag": lag_candidate["lag"] if lag_candidate else None,
    }
    if fires_2i:
        schemes = load_grant_schemes(root)
        scheme = least_recently_awarded_scheme(schemes, grants)
        return emit(
            "2I",
            f"{lag_candidate['name']} has {lag_candidate['lag']} outputs since their last grant",
            {
                "researcher": lag_candidate["name"],
                "lag": lag_candidate["lag"],
                "grants_held": lag_candidate["grants_held"],
                "scheme": scheme["id"],
                "scheme_name": scheme["name"],
            },
            checked,
            as_json,
        )

    news = load_news_without_output_or_grant(root)
    newest_news_date = max((n["date"] for n in news), default=None)
    news_due = (
        newest_news_date is None
        or (now.date() - newest_news_date).days > NEWS_STALE_DAYS
    )
    checked["news"] = {
        "newest_news_date": iso(newest_news_date),
        "due": news_due,
        "count": len(news),
    }
    if news_due:
        kind = NEWS_KINDS[len(news) % len(NEWS_KINDS)]
        return emit(
            "2H",
            "the newsroom has been quiet past the 3-day window",
            {"kind": kind, "last_post": iso(newest_news_date)},
            checked,
            as_json,
        )

    return emit(
        "2A",
        "the department is coherent; default to a new research output",
        {},
        checked,
        as_json,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="checkout to assess (default: cwd)",
    )
    parser.add_argument(
        "--json", action="store_true", help="emit JSON instead of prose"
    )
    parser.add_argument(
        "--only-2a",
        action="store_true",
        help="concurrent generator slot: always return 2A",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="skip the Bluesky feed fetch (2G reads as not due)",
    )
    parser.add_argument("--now", help="override the clock (ISO datetime), for tests")
    args = parser.parse_args()

    if args.only_2a:
        return emit(
            "2A",
            "generator slot pinned to 2A; concurrent slots never garden",
            {},
            {},
            args.json,
        )

    now = resolve_now(args.now)
    return assess(args.root, now, args.no_network, args.json)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except MalformedInput as exc:
        print(f"malformed input: {exc}", file=sys.stderr)
        sys.exit(2)
