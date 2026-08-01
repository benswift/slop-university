#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""Memorisation probe: is near-perfect discrimination actually recall?

The real side of this corpus is public web text (published strategic plans and
annual reports); the fabricated side is local-only and gitignored. A model that
has memorised the real documents can identify them without judging anything, and
that shortcut gets *stronger* with newer, larger models -- which is exactly the
pattern a naive reading of the 5.6 results would mistake for better judgement.

This asks each judge to name the source institution of each redacted excerpt. If
it names real sources above chance, recall is available as a confound.

Usage: memorisation_probe.py <model> [...]
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
STIM = ROOT / "stimuli" / "stimuli.json"
OUT = ROOT / "results" / "memorisation.json"

PROMPT = """Below is an excerpt from a university document. Identifying names have
been replaced with tags such as [ORGANISATION], [PERSON], [PLACE] and [REF].

Do you recognise this specific text from your training data? If you do, name the
institution and the document it comes from. Do not guess from general plausibility
-- only answer if you actually recognise the wording.

Reply with JSON only:
{"recognised": true or false, "institution": "<name or null>", "document": "<title or null>", "certainty": <integer 0-100>}

EXCERPT:
---
%s
---"""


# DeepSeek serves the OpenAI chat-completions schema, so one asker covers both;
# the model id selects the endpoint and the key.
ENDPOINTS = {
    "deepseek": ("https://api.deepseek.com/chat/completions", "DEEPSEEK_API_TOKEN"),
    "": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY"),
}


def ask(model: str, text: str) -> dict:
    url, keyvar = ENDPOINTS["deepseek" if model.startswith("deepseek") else ""]
    with httpx.Client() as c:
        r = c.post(
            url,
            headers={"Authorization": f"Bearer {os.environ[keyvar]}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": PROMPT % text}],
                "response_format": {"type": "json_object"},
            },
            timeout=300,
        )
        r.raise_for_status()
        try:
            return json.loads(r.json()["choices"][0]["message"]["content"])
        except json.JSONDecodeError:
            return {"recognised": None}


# maps a source-file stem to the institution that actually published it
TRUTH = {
    "real-strategy-anu": "australian national",
    "real-impact-anu": "australian national",
    "anu-corporate-plan-2026-v5": "australian national",
    "real-strategy-auckland": "auckland",
    "real-impact-auckland": "auckland",
    "real-strategy-edinburgh": "edinburgh",
    "real-impact-edinburgh": "edinburgh",
    "real-strategy-manchester": "manchester",
    "real-impact-manchester": "manchester",
    "real-strategy-toronto": "toronto",
    "real-strategy-trinity-dublin": "trinity",
    "real-strategy-tudelft": "delft",
    "real-impact-tudelft": "delft",
    "real-strategy-ucl": "college london",
    "real-impact-ucl": "college london",
    "real-strategy-univ-sydney": "sydney",
    "real-strategy-unsw": "new south wales",
}


def main() -> None:
    stims = json.loads(STIM.read_text())
    rows = []
    for model in sys.argv[1:]:
        with ThreadPoolExecutor(max_workers=8) as pool:
            res = list(pool.map(lambda s: ask(model, s["text_redacted"]), stims))
        for s, r in zip(stims, res, strict=True):
            doc = Path(s["source_file"]).stem
            want = TRUTH.get(doc)
            got = (r.get("institution") or "").lower()
            rows.append(
                {
                    "item": s["item"],
                    "model": model,
                    "truth": s["truth"],
                    "condition": s["condition"],
                    "source_doc": doc,
                    "recognised": bool(r.get("recognised")),
                    "named": r.get("institution"),
                    "certainty": r.get("certainty"),
                    "correct_source": bool(want and want in got),
                }
            )
        claimed = [x for x in rows if x["model"] == model and x["recognised"]]
        real_hit = [x for x in claimed if x["truth"] == "real" and x["correct_source"]]
        n_real = sum(1 for s in stims if s["truth"] == "real")
        print(
            f"{model}: claimed recognition on {len(claimed)}/{len(stims)}; "
            f"correctly named the real source on {len(real_hit)}/{n_real} real items"
        )
    # Merge rather than overwrite: this file is the record for every judge, and
    # a run naming only some of them must not drop the rest.
    fresh = {r["model"] for r in rows}
    kept = [
        r
        for r in (json.loads(OUT.read_text()) if OUT.exists() else [])
        if r["model"] not in fresh
    ]
    OUT.write_text(json.dumps(kept + rows, indent=1))


if __name__ == "__main__":
    main()
