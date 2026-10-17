#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "pyyaml", "typer"]
# ///
"""Give each roster researcher without one an ElevenLabs Voice Library voice,
recorded in canon/voices.yml (researcher id -> voice id).

A researcher keeps their voice in every video: their profile promo, and the
lines they speak in an explainer of their own work. The voices live in their
own file rather than the roster, whose entries are only ever appended
(canon/roster.yml's header); a run that needs a voice the file lacks runs this
first.

The choice is mechanical, so the same roster gets the same voices: gender from
the bio's pronouns, age from the title (a doctoral candidate or postdoc sounds
young, a professor older), and an English accent drawn by hashing the id, from
the accents of the University's own invented names and its Australian home.
Within that, the most-used professional voice for informative or narrative
work that no other researcher has. A voice whose name or description suggests
an impression of someone, or that sounds like a recognisable public figure,
is never taken: a voice speaks only as the invented researcher it is given to.

Usage: ops/assign-voices.py [--dry-run]   (needs ELEVENLABS_API_KEY)
"""

import hashlib
import os
import re
from pathlib import Path
from typing import Annotated

import httpx
import typer
import yaml

ROOT = Path(__file__).resolve().parent.parent
ROSTER = ROOT / "canon" / "roster.yml"
VOICES = ROOT / "canon" / "voices.yml"
API = "https://api.elevenlabs.io/v1/shared-voices"
ACCENTS = ["australian", "british", "nigerian", "american", "irish", "south african"]
USES = ["informative_educational", "narrative_story", "conversational"]
# an impression, or a name that points at a public figure
SHUNNED = re.compile(
    r"impression|celebrity|parody|famous|imitat|like\b"
    r"|\b(elon|musk|attenborough|freeman|obama|trump|biden|oprah|morgan)\b",
    re.IGNORECASE,
)

HEADER = """\
# Each roster researcher's ElevenLabs Voice Library voice, by researcher id.
# Written by ops/assign-voices.py (its docstring says how a voice is chosen);
# a video run that needs a voice this file lacks runs it first. A voice speaks
# only as the invented researcher it is given to.
"""


def gender(bio: str) -> str:
    if re.search(r"\b(she|her|hers)\b", bio, re.IGNORECASE):
        return "female"
    if re.search(r"\b(he|his|him)\b", bio, re.IGNORECASE):
        return "male"
    return "neutral"


def age(title: str) -> str:
    if re.search(r"Doctoral|Postdoctoral", title):
        return "young"
    if re.match(r"Professor\b", title):
        return "old"
    return "middle_aged"


def accent(rid: str) -> str:
    return ACCENTS[int(hashlib.sha256(rid.encode()).hexdigest(), 16) % len(ACCENTS)]


def candidates(key: str, g: str, a: str, acc: str) -> list[dict]:
    params = {"language": "en", "gender": g, "age": a, "accent": acc, "page_size": 100}
    voices = []
    for use in USES:
        r = httpx.get(
            API,
            params={**params, "use_cases": use},
            headers={"xi-api-key": key},
            timeout=60,
        )
        r.raise_for_status()
        voices += r.json()["voices"]
    usable = [
        v
        for v in voices
        if v["category"] == "professional"
        and not SHUNNED.search(f"{v['name']} {v.get('description') or ''}")
    ]
    return sorted(usable, key=lambda v: -(v.get("usage_character_count_1y") or 0))


def main(
    dry_run: Annotated[bool, typer.Option(help="print, don't write")] = False,
) -> None:
    key = os.environ["ELEVENLABS_API_KEY"]
    roster = yaml.safe_load(ROSTER.read_text())["researchers"]
    have = yaml.safe_load(VOICES.read_text()) if VOICES.is_file() else {}
    have = have or {}
    taken = {v["id"] for v in have.values()}
    pools: dict[tuple, list[dict]] = {}
    for p in roster:
        if p["id"] in have:
            continue
        g, a, acc = gender(p["bio"]), age(p["title"]), accent(p["id"])
        tried = [(g, a, acc), (g, a, None), (g, "middle_aged", None)]
        pick = None
        for g2, a2, acc2 in tried:
            pool = pools.setdefault((g2, a2, acc2), candidates(key, g2, a2, acc2 or ""))
            pick = next((v for v in pool if v["voice_id"] not in taken), None)
            if pick:
                break
        if pick is None:
            raise SystemExit(f"no voice left for {p['id']} ({g}, {a})")
        taken.add(pick["voice_id"])
        have[p["id"]] = {
            "id": pick["voice_id"],
            "name": pick["name"],
            "accent": pick["accent"],
        }
        print(f"{p['id']:24} {g:6} {a:11} {pick['accent']:13} {pick['name']}")
    if not dry_run:
        body = yaml.safe_dump(have, sort_keys=False, allow_unicode=True, width=100)
        VOICES.write_text(HEADER + "\n" + body)


if __name__ == "__main__":
    typer.run(main)
