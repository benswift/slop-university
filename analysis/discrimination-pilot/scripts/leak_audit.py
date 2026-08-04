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


# The detector occasionally degenerates into repeating one span forever, and at
# temperature 0 a retry reproduces it exactly. So the length is capped (a
# 200--340-word excerpt has never needed more than a few dozen spans) and a
# truncated body is salvaged for the objects that did complete, rather than
# taking the whole run down with a JSONDecodeError.
MAX_TOKENS = 2000
LEAK_OBJ_RE = re.compile(
    r'\{\s*"text"\s*:\s*("(?:[^"\\]|\\.)*")\s*,\s*"category"\s*:\s*("(?:[^"\\]|\\.)*")\s*\}'
)


def parse_leaks(content: str) -> tuple[list, bool]:
    """Return (leaks, salvaged). Salvage keeps the complete objects of a
    truncated array instead of discarding a whole excerpt's audit."""
    try:
        return json.loads(content).get("leaks", []), False
    except json.JSONDecodeError:
        pass
    seen: set[tuple[str, str]] = set()
    leaks = []
    for t, c in LEAK_OBJ_RE.findall(content):
        try:
            pair = (json.loads(t), json.loads(c))
        except json.JSONDecodeError:
            continue
        if pair not in seen:
            seen.add(pair)
            leaks.append({"text": pair[0], "category": pair[1]})
    return leaks, True


def detect_one(client: httpx.Client, stim: dict) -> dict:
    last: Exception | None = None
    for attempt in range(3):
        try:
            r = client.post(
                API,
                headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": PROMPT % stim["text"]}],
                    # a retry at temperature 0 would reproduce a degenerate
                    # completion character for character
                    "temperature": 0 if attempt == 0 else 0.3,
                    "max_tokens": MAX_TOKENS,
                    "response_format": {"type": "json_object"},
                },
                timeout=180,
            )
            r.raise_for_status()
            leaks, salvaged = parse_leaks(r.json()["choices"][0]["message"]["content"])
            if salvaged and attempt < 2:
                continue  # a clean answer is worth one more call
            return {"item": stim["id"], "leaks": leaks, "salvaged": salvaged}
        except Exception as e:  # noqa: BLE001 - retried, then reported
            last = e
    # Fail visibly. The gazetteer pass has already run on this excerpt, so it is
    # not unredacted, but the second pass did not cover it and detect() says so.
    return {"item": stim["id"], "leaks": [], "detector_error": str(last)[:200]}


def detect() -> None:
    stims = json.loads(STIM.read_text())

    # Cache on the excerpt TEXT, not its id. Ids shift whenever the prose filter
    # changes what counts as an excerpt, but the detector's answer depends only
    # on the words it was shown --- so keying on the text means a re-run after a
    # pipeline fix, or after the corpus grows, pays only for excerpts that are
    # genuinely new. At 600-odd excerpts a full re-detect is not ruinous, but it
    # is pure waste, and this corpus is meant to keep growing.
    # A failed detection is never cached: caching it would turn one bad call
    # into a permanent hole in the second redaction pass.
    cached: dict[str, list] = {}
    if SPANS.exists():
        for row in json.loads(SPANS.read_text()):
            if "text_sha1" in row and not row.get("detector_error"):
                cached[row["text_sha1"]] = row["leaks"]

    def key(s: dict) -> str:
        return hashlib.sha1(s["text"].encode()).hexdigest()

    todo = [s for s in stims if key(s) not in cached]
    print(f"{len(stims) - len(todo)} excerpts cached, {len(todo)} to detect")

    fresh: dict[str, dict] = {}
    if todo:
        with httpx.Client() as client, ThreadPoolExecutor(max_workers=8) as pool:
            for r in pool.map(lambda s: detect_one(client, s), todo):
                fresh[r["item"]] = r

    results = []
    for s in stims:
        row = {"item": s["id"], "text_sha1": key(s)}
        got = fresh.get(s["id"])
        if got is None:
            row["leaks"] = cached[key(s)]
        else:
            row["leaks"] = got["leaks"]
            if got.get("salvaged"):
                row["salvaged"] = True
            if got.get("detector_error"):
                row["detector_error"] = got["detector_error"]
        results.append(row)
    SPANS.write_text(json.dumps(results, indent=1))
    n = sum(len(r["leaks"]) for r in results)
    print(f"detected {n} candidate leaks across {len(results)} excerpts")
    salvaged = [r["item"] for r in results if r.get("salvaged")]
    failed = [r["item"] for r in results if r.get("detector_error")]
    if salvaged:
        print(f"salvaged {len(salvaged)} truncated responses: {', '.join(salvaged)}")
    if failed:
        print(f"DETECTOR FAILED on {len(failed)}: {', '.join(failed)}")


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
            # Substitute on word boundaries, not as a bare substring. A
            # detector that flags the acronym `OU` and a `str.replace` turned
            # "OUR STRATEGIC PROCESS" into "[ORGANISATION]R STRATEGIC PROCESS"
            # --- a mangled word that reads as damaged extraction, which is the
            # one thing this pipeline works hardest to keep off the real side.
            pat = (
                (r"\b" if frag[0].isalnum() else "")
                + re.escape(frag)
                + (r"\b" if frag[-1].isalnum() else "")
            )
            text, n = re.subn(pat, f"[{cat}]", text)
            if not n:
                continue
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
