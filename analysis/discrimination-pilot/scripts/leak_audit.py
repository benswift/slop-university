#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""Second-pass leakage audit.

An LLM *detector* (not a rewriter) returns the exact identifying substrings it
can find in each excerpt. Substitution is then done mechanically here, so the
prose is never paraphrased and every redacted span is logged. Runs on a model
family separate from the primary judge.

Usage:
  leak_audit.py detect   # call the detector, write leak_spans.json
  leak_audit.py apply    # apply spans, write stimuli_redacted.json
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

SCRATCH = Path(__file__).resolve().parent.parent
STIM = SCRATCH / "stimuli" / "pool.json"
SPANS = SCRATCH / "stimuli" / "pool_leak_spans.json"
OUT = SCRATCH / "stimuli" / "pool_redacted.json"

MODEL = "gpt-4.1"
API = "https://api.openai.com/v1/chat/completions"

PROMPT = """You are auditing an excerpt from a university document for IDENTITY LEAKAGE before it is used as a blind stimulus in an experiment.

Return every substring that would let a reader identify WHO issued the document or WHICH real-world entities it names. Specifically flag:
- names of universities, colleges, schools, faculties, institutes, centres, labs, museums, campuses or named buildings (real or invented)
- personal names of any kind, including bare first names used in quotes or profiles
- place names at any scale: countries, states, provinces, cities, suburbs, regions, and demonyms derived from them
- names of governments, funding bodies, regulators, rankings, charities, companies and partner organisations
- named strategies, brand taglines, house programmes and prize/scholarship names
- statutes, Acts, charters and named external frameworks
- URLs, emails, DOIs, registration numbers
- dates or figures that establish the institution's AGE, FOUNDING or HERITAGE (e.g. "since 1826", "our 150-year history")
- specific calendar dates of named events (e.g. "11 June 2025")

Do NOT flag:
- ordinary subject-matter vocabulary, however unusual or implausible the content is
- generic role titles (Vice-Chancellor, Dean, Director, Provost, Council, Senate)
- generic governance nouns (Audit and Risk Committee, Academic Board)
- plan-period years (2026-2031), ordinary statistics, or money amounts
- text already replaced by a tag such as [ORGANISATION], [PERSON], [PLACE], [REF]

For each item give the substring EXACTLY as it appears in the text (character for character), and one category from: ORGANISATION, PERSON, PLACE, REF.

Respond with JSON only: {"leaks": [{"text": "...", "category": "..."}]}
If there is nothing to flag, respond {"leaks": []}.

EXCERPT:
---
%s
---"""


def detect_one(client: httpx.Client, stim: dict) -> dict:
    r = client.post(
        API,
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": PROMPT % stim["text"]}],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        timeout=180,
    )
    r.raise_for_status()
    body = json.loads(r.json()["choices"][0]["message"]["content"])
    return {"item": stim["id"], "leaks": body.get("leaks", [])}


def detect() -> None:
    stims = json.loads(STIM.read_text())

    # Cache on the excerpt TEXT, not its id. Ids shift whenever the prose filter
    # changes what counts as an excerpt, but the detector's answer depends only
    # on the words it was shown --- so keying on the text means a re-run after a
    # pipeline fix, or after the corpus grows, pays only for excerpts that are
    # genuinely new. At 600-odd excerpts a full re-detect is not ruinous, but it
    # is pure waste, and this corpus is meant to keep growing.
    cached: dict[str, list] = {}
    if SPANS.exists():
        for row in json.loads(SPANS.read_text()):
            if "text_sha1" in row:
                cached[row["text_sha1"]] = row["leaks"]

    def key(s: dict) -> str:
        return hashlib.sha1(s["text"].encode()).hexdigest()

    todo = [s for s in stims if key(s) not in cached]
    print(f"{len(stims) - len(todo)} excerpts cached, {len(todo)} to detect")

    fresh: dict[str, list] = {}
    if todo:
        with httpx.Client() as client, ThreadPoolExecutor(max_workers=8) as pool:
            for r in pool.map(lambda s: detect_one(client, s), todo):
                fresh[r["item"]] = r["leaks"]

    results = [
        {
            "item": s["id"],
            "text_sha1": key(s),
            "leaks": fresh.get(s["id"], cached.get(key(s), [])),
        }
        for s in stims
    ]
    SPANS.write_text(json.dumps(results, indent=1))
    n = sum(len(r["leaks"]) for r in results)
    print(f"detected {n} candidate leaks across {len(results)} excerpts")


TAGS = {"ORGANISATION", "PERSON", "PLACE", "REF"}
# Never redact these even if flagged: they are generic institutional vocabulary
# and removing them would damage both sides' prose without removing identity.
KEEP = {
    "university",
    "the university",
    "council",
    "senate",
    "faculty",
    "school",
    "college",
    "campus",
    "government",
    "department",
    "committee",
    "board",
    "vice-chancellor",
    "chancellor",
    "provost",
    "dean",
    "director",
    "plan",
    "strategy",
    "the plan",
    "the strategy",
    "report",
    "annual report",
}


def apply() -> None:
    stims = json.loads(STIM.read_text())
    spans = {r["item"]: r["leaks"] for r in json.loads(SPANS.read_text())}
    log: list[dict] = []
    for s in stims:
        text = s["text"]
        leaks = spans.get(s["id"], [])
        # longest first so nested spans don't leave fragments
        # the detector occasionally returns bare strings instead of objects
        leaks = [
            lk
            if isinstance(lk, dict)
            else {"text": str(lk), "category": "ORGANISATION"}
            for lk in leaks
        ]
        leaks = sorted(leaks, key=lambda x: -len(str(x.get("text", ""))))
        applied = []
        for lk in leaks:
            frag, cat = lk.get("text", "").strip(), lk.get("category", "").upper()
            if not frag or cat not in TAGS:
                continue
            if frag.lower() in KEEP or len(frag) < 2:
                continue
            if frag.startswith("[") and frag.endswith("]"):
                continue
            # the detector over-flags bare years and month-years; these carry no
            # institutional identity and redacting them only inflates tag counts
            if re.fullmatch(r"(?:19|20)\d{2}(?:[-/–](?:19|20)?\d{2})?", frag):
                continue
            if re.fullmatch(
                r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+(?:19|20)\d{2}",
                frag,
            ):
                continue
            if frag not in text:
                continue
            text = text.replace(frag, f"[{cat}]")
            applied.append({"text": frag, "category": cat})
        # tidy: collapse adjacent/possessive tag runs
        alt = "|".join(TAGS)
        text = re.sub(rf"(\[(?:{alt})\])(?:[\s,]*\1)+", r"\1", text)
        text = re.sub(r"[ \t]+", " ", text).strip()
        s["text_redacted"] = text
        s["leaks_applied"] = applied
        log.append({"item": s["id"], "n": len(applied)})
    OUT.write_text(json.dumps(stims, indent=1))
    print(
        f"applied redactions to {len(stims)} excerpts; total spans {sum(x['n'] for x in log)}"
    )


if __name__ == "__main__":
    {"detect": detect, "apply": apply}[sys.argv[1]]()
