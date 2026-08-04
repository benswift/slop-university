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
  deepseek:<model> DeepSeek chat completions (OpenAI-compatible schema)

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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ids import text_sha  # noqa: E402

SCRATCH = Path(__file__).resolve().parent.parent
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


def ask_chat_completions(url: str, key: str, model: str, text: str) -> dict:
    """One turn against any OpenAI-schema chat-completions endpoint."""
    with httpx.Client() as c:
        r = c.post(
            url,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": PROMPT % text}],
                "response_format": {"type": "json_object"},
            },
            timeout=300,
        )
        r.raise_for_status()
        return parse(r.json()["choices"][0]["message"]["content"])


def ask_openai(model: str, text: str) -> dict:
    return ask_chat_completions(
        "https://api.openai.com/v1/chat/completions",
        os.environ["OPENAI_API_KEY"],
        model,
        text,
    )


def ask_deepseek(model: str, text: str) -> dict:
    return ask_chat_completions(
        "https://api.deepseek.com/chat/completions",
        os.environ["DEEPSEEK_API_TOKEN"],
        model,
        text,
    )


def ask_claude(model: str, text: str) -> dict:
    p = subprocess.run(
        ["claude", "-p", "--model", model, PROMPT % text],
        capture_output=True,
        text=True,
        timeout=300,
    )
    return parse(p.stdout)


def main() -> None:
    # `--stimuli NAME` runs the same harness, same prompt and same parser over
    # another stimulus file: the vision arm reuses it, and because it writes to
    # its own results file an excerpt drawn into both sets is judged twice
    # independently rather than resumed from the first answer.
    argv = sys.argv[1:]
    stim_name = "stimuli"
    if "--stimuli" in argv:
        i = argv.index("--stimuli")
        stim_name = argv[i + 1]
        del argv[i : i + 2]

    backend = argv[0]
    kind, model = backend.split(":", 1)
    ask = {"openai": ask_openai, "claude": ask_claude, "deepseek": ask_deepseek}[kind]
    out = RESULTS / (argv[1] if len(argv) > 1 else f"judgements-{model}.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    stim_path = SCRATCH / "stimuli" / f"{stim_name}.json"
    stims = json.loads(stim_path.read_text())

    manifest_path = (
        SCRATCH
        / "stimuli"
        / ("manifest.json" if stim_name == "stimuli" else f"{stim_name}_manifest.json")
    )
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    fingerprint = manifest.get("fingerprint")

    # Resume, and extend. Item ids are content-derived, so judgements already on
    # disk stay valid when the corpus grows: only genuinely new items are sent.
    # A judgement whose id is no longer in the stimulus set is kept rather than
    # dropped --- it is evidence about an excerpt, not about this sample.
    # A judgement is evidence about the excerpt that was judged, so resume keys
    # on the excerpt's text and not only on its id. Ids survive a pool rebuild
    # and a stimulus repair; the text does not, and a judgement of text that no
    # longer exists must be re-elicited rather than reused. Rows written before
    # this stamp existed carry no fingerprint and are trusted, with a warning:
    # there is nothing else to do with them, but the gap should be visible.
    shas = {s["item"]: text_sha(s["text_redacted"]) for s in stims}
    existing: dict[str, dict] = {}
    if out.exists():
        prior = json.loads(out.read_text())
        if prior and "item" in prior[0]:
            existing = {r["item"]: r for r in prior if r.get("judgement")}
        unstamped = sum(1 for r in existing.values() if not r.get("text_sha"))
        if unstamped:
            print(f"note: {unstamped} prior judgements predate the text fingerprint")
        changed = {
            item
            for item, r in existing.items()
            if r.get("text_sha") and item in shas and r["text_sha"] != shas[item]
        }
        if changed:
            print(
                f"note: {len(changed)} excerpts have changed since judging --- re-judging"
            )
            for item in changed:
                del existing[item]
        stale = existing.keys() - {s["item"] for s in stims}
        if stale:
            print(
                f"note: {len(stale)} judged items are not in the current sample --- kept, not re-judged"
            )

    todo = [s for s in stims if s["item"] not in existing]
    if existing:
        print(f"{len(existing)} already judged, {len(todo)} to do")
    if not todo:
        print("nothing new to judge")
        return
    stims = todo
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
            "text_sha": text_sha(s["text_redacted"]),
            "presentation_index": order.index(k),
            "stimulus_fingerprint": fingerprint,
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

    rows = list(existing.values()) + rows
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
