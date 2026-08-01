#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""Run the discrimination pilot.

Each excerpt is presented independently (never in pairs -- a pair leaks relative
information), in randomised order, to a judge that returns a binary label, a
confidence, and a one-line reason.

Backends:
  openai:<model>   OpenAI chat completions
  claude:<model>   the `claude -p` CLI (Anthropic)

Usage: judge.py <backend> [outfile]
"""

from __future__ import annotations

import json
import os
import random
import re
import subprocess
import sys
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

SCRATCH = Path(__file__).resolve().parent.parent
STIM = SCRATCH / "stimuli" / "stimuli.json"
RESULTS = SCRATCH / "results"

PROMPT = """You are shown ONE excerpt of prose taken from a university document.

It is one of exactly two kinds:

  REAL        - an excerpt from a genuine document actually published by a real
                university (a strategic plan, corporate plan, annual report or
                impact report).
  FABRICATED  - an excerpt from a document produced by an AI document generator
                for a university that does not exist. The prose was written by a
                language model and describes activities, findings and
                commitments that never happened.

Both kinds have been redacted the SAME way: names of institutions, people,
places, funders and external references have been replaced by the tags
[ORGANISATION], [PERSON], [PLACE] and [REF]. Excerpt length and the number of
redaction tags have been matched across the two kinds, so neither is a clue.

Across the full set, half the excerpts are REAL and half are FABRICATED. Judge
this excerpt on its own merits.

Reply with JSON only, no other text:
{"judgement": "REAL" or "FABRICATED", "confidence": <integer 50-100>, "reason": "<one sentence naming the specific feature that decided it>"}

EXCERPT:
---
%s
---"""


def parse(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {
            "judgement": None,
            "confidence": None,
            "reason": raw[:200],
            "parse_error": True,
        }
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {
            "judgement": None,
            "confidence": None,
            "reason": raw[:200],
            "parse_error": True,
        }
    j = str(d.get("judgement", "")).strip().upper()
    return {
        "judgement": j if j in ("REAL", "FABRICATED") else None,
        "confidence": d.get("confidence"),
        "reason": d.get("reason", ""),
    }


def ask_openai(model: str, text: str) -> dict:
    with httpx.Client() as c:
        r = c.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": PROMPT % text}],
                "response_format": {"type": "json_object"},
            },
            timeout=300,
        )
        r.raise_for_status()
        return parse(r.json()["choices"][0]["message"]["content"])


def ask_claude(model: str, text: str) -> dict:
    p = subprocess.run(
        ["claude", "-p", "--model", model, PROMPT % text],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return parse(p.stdout)


def main() -> None:
    backend = sys.argv[1]
    kind, model = backend.split(":", 1)
    ask = {"openai": ask_openai, "claude": ask_claude}[kind]
    out = RESULTS / (sys.argv[2] if len(sys.argv) > 2 else f"judgements-{model}.json")

    stims = json.loads(STIM.read_text())
    # independent randomisation of presentation order per judge
    order = list(range(len(stims)))
    # Stable per-judge seed. Python salts str hashing per process, so the
    # earlier hash(model) form was not reproducible between runs; crc32 is.
    # Presentation order cannot in fact affect the result -- every item is an
    # independent stateless call with no shared context -- but a reproducible
    # order keeps the record honest.
    random.Random(zlib.crc32(model.encode())).shuffle(order)

    def one(k: int) -> dict:
        s = stims[k]
        for attempt in range(3):
            try:
                res = ask(model, s["text_redacted"])
                if res.get("judgement"):
                    break
            except Exception as e:  # noqa: BLE001 - retry then record
                res = {"judgement": None, "confidence": None, "reason": f"error: {e}"}
        return {
            "item": s["item"],
            "presentation_index": order.index(k),
            "judge": model,
            "truth": s["truth"],
            "condition": s["condition"],
            "subtype": s["subtype"],
            "source_doc": s["id"].rsplit("--", 1)[0],
            "words": s["words"],
            "tag_density": s["tag_density"],
            **res,
        }

    workers = 8 if kind == "openai" else 4
    with ThreadPoolExecutor(max_workers=workers) as pool:
        rows = list(pool.map(one, order))

    rows.sort(key=lambda r: r["item"])
    RESULTS.mkdir(exist_ok=True)
    out.write_text(json.dumps(rows, indent=1))
    ok = sum(1 for r in rows if r["judgement"])
    acc = sum(
        1
        for r in rows
        if r["judgement"]
        and r["judgement"].lower() == ("real" if r["truth"] == "real" else "fabricated")
    )
    print(
        f"{model}: {ok}/{len(rows)} parsed, accuracy {acc}/{ok} = {acc / max(ok, 1):.1%}"
    )


if __name__ == "__main__":
    main()
