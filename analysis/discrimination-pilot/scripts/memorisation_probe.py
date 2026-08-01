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
       memorisation_probe.py gpt-5.6-terra claude:sonnet
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
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
    """One probe, with retries --- a single transient 500 from the provider
    killed an entire six-model run, which is an expensive way to learn that a
    long batch job needs to tolerate a flaky request."""
    for attempt in range(4):
        try:
            return _ask_once(model, text)
        except Exception:  # noqa: BLE001 - retry, then give up on this item
            if attempt == 3:
                return {"recognised": None, "error": True}
            time.sleep(2**attempt)
    return {"recognised": None, "error": True}


def _ask_once(model: str, text: str) -> dict:
    # The Anthropic judges reach the model through the `claude` CLI rather than
    # an API key, the same way judge.py does. They are 3/8 of the panel now, and
    # a recall control that cannot be run on the judges from the vendor that
    # also wrote the corpus is the one place it is least safe to skip.
    if model.startswith("claude:"):
        p = subprocess.run(
            ["claude", "-p", "--model", model.split(":", 1)[1], PROMPT % text],
            capture_output=True,
            text=True,
            timeout=300,
        )
        m = re.search(r"\{.*\}", p.stdout, re.S)
        try:
            return json.loads(m.group(0)) if m else {"recognised": None}
        except json.JSONDecodeError:
            return {"recognised": None}

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


# Maps a source-file stem to the institution that published it. Derived from
# corpus/provenance.json rather than hand-written: the hand-written version
# covered the first run's twelve institutions, and against a corpus of 143 it
# would score almost every correct recognition as a miss --- silently turning a
# memorisation result into an understatement.
def _load_truth() -> dict[str, str]:
    prov = json.loads((ROOT / "corpus" / "provenance.json").read_text())
    out: dict[str, str] = {}
    for row in prov.get("real_strategy", []) + prov.get("real_impact", []):
        stem = row["file"].rsplit(".", 1)[0]
        name = row["institution"].lower()
        # Match on the distinctive part: a judge naming "Manchester" should
        # count as having named "The University of Manchester".
        for filler in (
            "the ",
            "university of ",
            " university",
            "college of ",
            " college",
        ):
            name = name.replace(filler, " ")
        out[stem] = " ".join(name.split())
    return out


TRUTH = _load_truth()


def main() -> None:
    stims = json.loads(STIM.read_text())
    rows = []
    for model in sys.argv[1:]:
        workers = 4 if model.startswith("claude:") else 8
        with ThreadPoolExecutor(max_workers=workers) as pool:
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
