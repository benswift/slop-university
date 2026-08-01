#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""Score documents on the concrete/vague axis the pilot's judges appear to use.

The pilot's most interesting error pattern was real strategic plans called
fabricated for "generic aspirational strategy language" and "sweeping
commitments offering no concrete detail" --- suggesting the boundary the judges
learned runs between concrete and vague rather than between real and invented.
Testing that properly needs the axis measured *independently of the judges*,
otherwise the claim is circular: the vague documents would be, by construction,
whatever got misclassified.

So the axis is measured two ways, and `analyse_vagueness.py` reports how well
they agree before either is used.

**Proxies** (`--proxies`, deterministic, no API). Six families counted per
10,000 words, three pulling concrete and three pulling vague:

  concrete   dated       a commitment pinned to a date --- "by 2030", "in
                         2025-26", "within three years", "each September"
             quantified  a target with a number attached --- percentages,
                         currency, counts, ratios, ranks
             accountable a named unit or instrument that would have to act ---
                         committee, directorate, framework, policy, review

  vague      aspirational  the abstract-noun register --- excellence, ambition,
                           journey, transformation, world-class, ecosystem
             hedged        commitment language that commits to nothing ---
                           "seek to", "aspire to", "continue to", "explore"
             nominal       nominalisation density (-tion/-ment/-ity/-ance),
                           which is what makes strategy prose agentless

The index is log((vague + 1) / (concrete + 1)), so it is symmetric around zero:
positive is vaguer than concrete, negative is more concrete than vague, and a
document with neither register scores near zero rather than dividing by zero.

**Model judgement** (`--model openai:gpt-5.6-terra`). Each document's sampled
excerpts are rated 0-100 for concreteness by a model that is not told anything
about real or fabricated, and never sees the truth label. Rating the excerpt
rather than the whole document keeps this comparable with the proxies, which are
also computed per excerpt.

    uv run --script scripts/vagueness.py --proxies
    uv run --script scripts/vagueness.py --model openai:gpt-5.6-terra
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ids import doc_key, item_id  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
POOL = ROOT / "stimuli" / "pool.json"
OUT = ROOT / "results"

# --------------------------------------------------------------------------
# Proxy lexicons
# --------------------------------------------------------------------------

MONTHS = r"January|February|March|April|May|June|July|August|September|October|November|December"

DATED = [
    re.compile(r"\bby\s+(?:the\s+end\s+of\s+)?(?:19|20)\d{2}\b", re.I),
    re.compile(r"\b(?:19|20)\d{2}[/–—-](?:\d{2}|(?:19|20)\d{2})\b"),
    re.compile(r"\bin\s+(?:19|20)\d{2}\b", re.I),
    re.compile(
        r"\bwithin\s+(?:the\s+)?(?:next\s+)?(?:one|two|three|four|five|ten|\d+)\s+years?\b",
        re.I,
    ),
    re.compile(r"\b(?:first|second|third|fourth|final)\s+(?:year|phase|stage)\b", re.I),
    re.compile(rf"\b(?:{MONTHS})\s+(?:19|20)\d{{2}}\b"),
    re.compile(r"\b(?:annually|each year|every year|quarterly|biennially)\b", re.I),
]

QUANTIFIED = [
    re.compile(r"\d+(?:\.\d+)?\s*(?:%|per cent|percent)", re.I),
    re.compile(r"[$£€]\s?\d"),
    re.compile(r"\b\d{1,3}(?:,\d{3})+\b"),
    re.compile(
        r"\b(?:at least|no fewer than|no more than|a minimum of|a maximum of|up to)\s+\d",
        re.I,
    ),
    re.compile(
        r"\b(?:double|triple|halve|increase|reduce|grow)\s+(?:\w+\s+){0,3}by\s+\d", re.I
    ),
    re.compile(r"\btop\s+\d+\b", re.I),
    re.compile(
        r"\b\d+\s+(?:students|staff|places|projects|partnerships|programmes|courses|beds|hectares|jobs)\b",
        re.I,
    ),
]

ACCOUNTABLE = [
    re.compile(
        r"\b(?:Committee|Board|Council|Directorate|Office of|Task ?force|Working Group|Steering Group"
        r"|Executive|Senate|Academic Board|Audit|Secretariat)\b"
    ),
    re.compile(
        r"\b(?:policy|framework|charter|code of practice|terms of reference|memorandum|agreement"
        r"|action plan|implementation plan|roadmap|review|audit|register|scorecard|dashboard)\b",
        re.I,
    ),
    re.compile(
        r"\b(?:reports? to|accountable to|responsible for|overseen by|monitored by|governed by)\b",
        re.I,
    ),
    re.compile(
        r"\bwe will (?:establish|launch|deliver|publish|appoint|allocate|invest|open|create|introduce|require)\b",
        re.I,
    ),
]

ASPIRATIONAL_TERMS = [
    "excellence",
    "excellent",
    "ambition",
    "ambitious",
    "aspiration",
    "aspirational",
    "world-class",
    "world class",
    "world-leading",
    "world leading",
    "globally recognised",
    "globally recognized",
    "cutting-edge",
    "leading-edge",
    "state-of-the-art",
    "best-in-class",
    "transformation",
    "transformative",
    "transformational",
    "journey",
    "vision",
    "visionary",
    "ecosystem",
    "synergy",
    "synergies",
    "holistic",
    "vibrant",
    "dynamic",
    "thriving",
    "thrive",
    "flourish",
    "empower",
    "empowerment",
    "unlock",
    "harness",
    "leverage",
    "catalyse",
    "catalyze",
    "impactful",
    "innovative",
    "innovation",
    "excellence-driven",
    "step change",
    "paradigm",
    "reimagine",
    "reimagining",
    "bold",
    "boldly",
    "inspire",
    "inspiring",
    "aspire",
    "cross-cutting",
    "future-focused",
    "forward-looking",
    "student-centred",
    "student-centered",
    "values-led",
    "purpose-driven",
    "culture of",
    "commitment to excellence",
]

HEDGED = [
    re.compile(r"\b(?:seek|seeks|seeking) to\b", re.I),
    re.compile(r"\b(?:aim|aims|aiming) to\b", re.I),
    re.compile(r"\b(?:aspire|aspires|aspiring) to\b", re.I),
    re.compile(r"\b(?:strive|strives|striving) to\b", re.I),
    re.compile(r"\b(?:continue|continues|continuing) to\b", re.I),
    re.compile(r"\bwork(?:ing)? (?:towards?|to ensure)\b", re.I),
    re.compile(
        r"\b(?:explore|consider|examine|investigate) (?:the )?(?:opportunit|possibilit|option|scope|potential)",
        re.I,
    ),
    re.compile(r"\bwhere (?:possible|appropriate|practicable)\b", re.I),
    re.compile(r"\bwe (?:want|hope|believe|recognise|recognize) (?:to|that)\b", re.I),
    re.compile(
        r"\b(?:support|enable|facilitate|foster|promote|encourage|champion)\b", re.I
    ),
]

NOMINAL_RE = re.compile(
    r"\b[a-z]{4,}(?:tion|tions|ment|ments|ity|ities|ance|ances|ence|ences|ness)\b", re.I
)

ASPIRATIONAL_RE = re.compile(
    r"\b("
    + "|".join(re.escape(t) for t in sorted(ASPIRATIONAL_TERMS, key=len, reverse=True))
    + r")\b",
    re.I,
)

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-]*")


def count(patterns: list[re.Pattern[str]], text: str) -> int:
    return sum(len(p.findall(text)) for p in patterns)


def proxy_scores(text: str) -> dict[str, float]:
    words = max(len(WORD_RE.findall(text)), 1)
    per10k = 10_000 / words

    dated = count(DATED, text)
    quantified = count(QUANTIFIED, text)
    accountable = count(ACCOUNTABLE, text)
    aspirational = len(ASPIRATIONAL_RE.findall(text))
    hedged = count(HEDGED, text)
    nominal = len(NOMINAL_RE.findall(text))

    concrete = dated + quantified + accountable
    vague = aspirational + hedged + nominal

    return {
        "words": words,
        "dated": dated,
        "quantified": quantified,
        "accountable": accountable,
        "aspirational": aspirational,
        "hedged": hedged,
        "nominal": nominal,
        "concrete_per10k": round(concrete * per10k, 2),
        "vague_per10k": round(vague * per10k, 2),
        "vagueness_index": round(
            math.log((vague * per10k + 1) / (concrete * per10k + 1)), 4
        ),
    }


# --------------------------------------------------------------------------
# Model rating
# --------------------------------------------------------------------------

RATING_PROMPT = """You are shown one excerpt of prose from a university planning document.

Rate how CONCRETE it is, on a scale from 0 to 100.

  0   purely abstract: aspirational language, no dates, no numbers, no named
      body that would have to act, nothing that could later be checked
  50  a mixture: some specific commitments, a good deal of general ambition
  100 wholly concrete: dated, quantified commitments, with named responsible
      bodies and deliverables that could be audited

Judge only concreteness. Do not consider whether the document is well written,
whether you agree with it, or where it came from.

Reply with JSON only, no other text:
{"concreteness": <integer 0-100>, "reason": "<one sentence naming the deciding feature>"}

EXCERPT:
---
%s
---"""


def parse_rating(raw: str) -> dict:
    m = re.search(r"\{.*\}", raw, re.S)
    if not m:
        return {"concreteness": None, "reason": raw[:200], "parse_error": True}
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"concreteness": None, "reason": raw[:200], "parse_error": True}
    v = d.get("concreteness")
    return {
        "concreteness": int(v)
        if isinstance(v, (int, float, str)) and str(v).strip().lstrip("-").isdigit()
        else None,
        "reason": d.get("reason", ""),
    }


def ask_chat(url: str, key_env: str, model: str, text: str) -> dict:
    import httpx

    with httpx.Client() as c:
        r = c.post(
            url,
            headers={"Authorization": f"Bearer {os.environ[key_env]}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": RATING_PROMPT % text}],
                "response_format": {"type": "json_object"},
            },
            timeout=300,
        )
        r.raise_for_status()
        return parse_rating(r.json()["choices"][0]["message"]["content"])


def ask(backend: str, text: str) -> dict:
    kind, model = backend.split(":", 1)
    if kind == "openai":
        return ask_chat(
            "https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY", model, text
        )
    if kind == "deepseek":
        return ask_chat(
            "https://api.deepseek.com/chat/completions",
            "DEEPSEEK_API_TOKEN",
            model,
            text,
        )
    if kind == "claude":
        p = subprocess.run(
            ["claude", "-p", "--model", model, RATING_PROMPT % text],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return parse_rating(p.stdout)
    raise SystemExit(f"unknown backend {backend!r}")


# --------------------------------------------------------------------------


def load_pool() -> list[dict]:
    if not POOL.exists():
        raise SystemExit(f"no pool at {POOL} --- run build_stimuli.py first")
    rows = json.loads(POOL.read_text())
    return rows if isinstance(rows, list) else rows["items"]


def report() -> None:
    """Breakdown of the proxy scores, and the overlap between the two sides.

    The overlap is the number that matters. If the fabricated documents were
    simply more concrete than every real one, the axis would separate the sides
    and would be a discriminator rather than a confound. What makes the pilot's
    error pattern interesting is that the distributions overlap heavily: a large
    share of genuine university strategy sits on the fabricated side of the
    boundary.
    """
    path = OUT / "vagueness-proxies.json"
    if not path.exists():
        raise SystemExit("run --proxies first")
    rows = json.loads(path.read_text())
    pool = {
        r["id"]: r for r in json.loads((ROOT / "stimuli" / "pool.json").read_text())
    }

    by_doc: dict[str, list[dict]] = {}
    for r in rows:
        by_doc.setdefault(r["source_doc"], []).append(r)

    docs = []
    for doc, items in by_doc.items():
        meta = pool.get(items[0]["id"], {})
        docs.append(
            {
                "doc": doc,
                "truth": items[0]["truth"],
                "country": meta.get("country", ""),
                "tier": meta.get("tier", ""),
                "year": meta.get("year", 0),
                "index": sum(i["vagueness_index"] for i in items) / len(items),
                "concrete": sum(i["concrete_per10k"] for i in items) / len(items),
                "vague": sum(i["vague_per10k"] for i in items) / len(items),
            }
        )

    real = sorted((d["index"] for d in docs if d["truth"] == "real"))
    fab = sorted((d["index"] for d in docs if d["truth"] == "fabricated"))

    def median(xs: list[float]) -> float:
        n = len(xs)
        return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2

    print(f"{len(docs)} source documents: {len(real)} real, {len(fab)} fabricated\n")
    print(f"{'':<12}{'n':>5}{'median':>9}{'min':>8}{'max':>8}")
    for name, xs in (("real", real), ("fabricated", fab)):
        print(f"{name:<12}{len(xs):>5}{median(xs):>9.2f}{xs[0]:>8.2f}{xs[-1]:>8.2f}")

    fab_med = median(fab)
    vaguer = [d for d in docs if d["truth"] == "real" and d["index"] > fab_med]
    fab_max = max(fab)
    above_all = [d for d in docs if d["truth"] == "real" and d["index"] > fab_max]
    print(
        f"\n{len(vaguer)}/{len(real)} ({len(vaguer) / len(real):.0%}) real documents are vaguer than the "
        f"median fabricated one;\n{len(above_all)}/{len(real)} ({len(above_all) / len(real):.0%}) are vaguer "
        f"than EVERY fabricated one."
    )

    print("\nreal side by tier:")
    for tier in ("elite", "research", "mid", "regional", "specialist"):
        xs = sorted(
            d["index"] for d in docs if d["truth"] == "real" and d["tier"] == tier
        )
        if xs:
            print(f"  {tier:<12} n={len(xs):<4} median {median(xs):+.2f}")

    print("\nvaguest real documents:")
    for d in sorted(
        (d for d in docs if d["truth"] == "real"), key=lambda d: -d["index"]
    )[:8]:
        print(
            f"  {d['index']:+.2f}  {d['doc']}  ({d['country']}, {d['tier']}, {d['year']})"
        )
    print("\nmost concrete real documents:")
    for d in sorted(
        (d for d in docs if d["truth"] == "real"), key=lambda d: d["index"]
    )[:5]:
        print(
            f"  {d['index']:+.2f}  {d['doc']}  ({d['country']}, {d['tier']}, {d['year']})"
        )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--proxies", action="store_true", help="deterministic lexical proxies, no API"
    )
    p.add_argument(
        "--model", help="backend for the model rating, e.g. openai:gpt-5.6-terra"
    )
    p.add_argument("--workers", type=int, default=8)
    p.add_argument(
        "--report",
        action="store_true",
        help="breakdown of the proxy scores already computed",
    )
    args = p.parse_args()

    if args.report:
        report()
        return

    if not args.proxies and not args.model:
        p.error("give --proxies, --model, or both")

    rows = load_pool()
    OUT.mkdir(exist_ok=True)

    if args.proxies:
        scored = [
            {
                "id": r.get("id"),
                # Derived, not read: the pool is scored BEFORE sampling, so these
                # rows have no "item" of their own. Deriving it here is what
                # lets the proxies join to judgements later.
                "item": item_id(r["id"]) if r.get("id") else None,
                "truth": r.get("truth"),
                "condition": r.get("condition"),
                "source_doc": doc_key(str(r.get("id", ""))),
                **proxy_scores(r.get("text") or r.get("text_redacted", "")),
            }
            for r in rows
        ]
        path = OUT / "vagueness-proxies.json"
        path.write_text(json.dumps(scored, indent=1) + "\n")

        for side in ("real", "fabricated"):
            side_rows = [s for s in scored if s["truth"] == side]
            if not side_rows:
                continue
            n = len(side_rows)
            print(
                f"{side:<11} n={n:<4} "
                f"concrete/10k {sum(s['concrete_per10k'] for s in side_rows) / n:7.1f}  "
                f"vague/10k {sum(s['vague_per10k'] for s in side_rows) / n:7.1f}  "
                f"index {sum(s['vagueness_index'] for s in side_rows) / n:+.3f}"
            )
        print(f"wrote {path.relative_to(ROOT)}")

    if args.model:
        texts = [
            (i, r.get("text_redacted") or r.get("text", "")) for i, r in enumerate(rows)
        ]

        def one(pair: tuple[int, str]) -> dict:
            i, text = pair
            res = {"concreteness": None, "reason": ""}
            for _ in range(3):
                try:
                    res = ask(args.model, text)
                    if res.get("concreteness") is not None:
                        break
                except Exception as e:  # noqa: BLE001 - retry then record
                    res = {"concreteness": None, "reason": f"error: {e}"}
            return {
                "id": rows[i].get("id"),
                "item": rows[i].get("item"),
                "truth": rows[i].get("truth"),
                "rater": args.model,
                **res,
            }

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            scored = list(pool.map(one, texts))

        model_name = args.model.split(":", 1)[1]
        path = OUT / f"vagueness-model-{model_name}.json"
        path.write_text(json.dumps(scored, indent=1) + "\n")
        ok = [s for s in scored if s["concreteness"] is not None]
        print(
            f"{args.model}: {len(ok)}/{len(scored)} rated, mean concreteness {sum(s['concreteness'] for s in ok) / max(len(ok), 1):.1f}"
        )
        print(f"wrote {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
