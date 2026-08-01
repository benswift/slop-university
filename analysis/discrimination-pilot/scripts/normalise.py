#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Extraction normalisation, applied symmetrically to both sides of the pilot.

Two defects in the first run were real-side-only, and both pushed real documents
towards "fabricated" --- which is the direction that manufactures the pilot's
most interesting finding, so both had to be fixed before a larger corpus was
scored rather than after.

**Dropped ligatures.** `pdftotext` loses `fi`/`fl`/`ff`/`ffi` from PDFs whose
fonts carry no ToUnicode mapping, leaving `effcient`, `beneft`, `fnd`, `frst`,
`refecting` in the extracted text. Ten such tokens appeared across two real
excerpts and zero fabricated ones --- the typst-generated PDFs have no ligature
to lose --- and DeepSeek cited the resulting "spelling errors" as grounds for
calling a real document fabricated. `repair_ligatures` reinserts the dropped
characters, but only where the repair is unambiguous against the system word
lists, so a genuine misspelling or an unusual proper noun is left alone.

**Orthography.** American spelling was an unremovable national tell against a
uniformly Australian/British fabricated corpus, and the first run handled it by
dropping the two US documents. At corpus scale exclusion is not good enough, so
`normalise_orthography` maps American spellings to British ones. It is likewise
dictionary-verified: a candidate is only accepted if the transformed token is a
British-dictionary word and the original was not, which is what keeps `size`,
`prize` and `capsize` out of the `-ize` rule without an exception list.

What this does NOT fix is American institutional *vocabulary* --- Provost,
Board of Trustees, Regents, the semester calendar. Those are content rather
than spelling, and rewriting them would edit what the document says. `audit`
counts them per side instead, so the residual can be reported honestly.

    uv run --script scripts/normalise.py audit    # measure both sides
    uv run --script scripts/normalise.py demo     # show the repairs on a sample
"""

from __future__ import annotations

import re
import sys
from functools import lru_cache
from pathlib import Path

BRITISH = Path("/usr/share/dict/british-english")
AMERICAN = Path("/usr/share/dict/american-english")

TOKEN_RE = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)*")


@lru_cache(maxsize=1)
def wordlists() -> tuple[frozenset[str], frozenset[str]]:
    def load(p: Path) -> frozenset[str]:
        if not p.exists():
            raise SystemExit(
                f"missing word list {p} --- install the wbritish/wamerican packages"
            )
        return frozenset(
            w.strip().lower()
            for w in p.read_text(errors="ignore").splitlines()
            if w.strip()
        )

    return load(BRITISH), load(AMERICAN)


def _match_case(original: str, replacement: str) -> str:
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


# --------------------------------------------------------------------------
# Dropped ligatures
# --------------------------------------------------------------------------

# What pdftotext drops when the ligature glyph has no ToUnicode entry. `fi` and
# `fl` collapse to a bare `f`; `ffi` and `ffl` collapse to `ff` or to `f`.
LIGATURE_INSERTS = ("i", "l", "fi", "fl", "f")


def _ligature_candidates(token: str) -> set[str]:
    lower = token.lower()
    out: set[str] = set()
    for i, ch in enumerate(lower):
        if ch != "f":
            continue
        for ins in LIGATURE_INSERTS:
            out.add(lower[: i + 1] + ins + lower[i + 1 :])
    return out


def repair_ligatures(text: str) -> tuple[str, int]:
    """Reinsert characters lost with ligature glyphs. Returns (text, n_repairs)."""
    british, american = wordlists()
    known = british | american
    repairs = 0

    def fix(m: re.Match[str]) -> str:
        nonlocal repairs
        token = m.group(0)
        lower = token.lower()
        if len(lower) < 3 or "f" not in lower or lower in known:
            return token
        hits = {c for c in _ligature_candidates(token) if c in known}
        if len(hits) != 1:
            return token
        repairs += 1
        return _match_case(token, hits.pop())

    return TOKEN_RE.sub(fix, text), repairs


# --------------------------------------------------------------------------
# Orthography
# --------------------------------------------------------------------------

# Each rule is (pattern, replacement) applied to the lowercased token. A rule
# only fires if it turns a non-British token into a British-dictionary word, so
# the list can be generous without needing exceptions.
ORTHOGRAPHY_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"iz(e|es|ed|ing|er|ers|ation|ations|able)\b"), r"is\1"),
    (re.compile(r"yz(e|es|ed|ing)\b"), r"ys\1"),
    (re.compile(r"or(\b|s\b|ed\b|ing\b|al\b|ally\b|ism\b|ist\b)"), r"our\1"),
    (re.compile(r"er(\b|s\b|ed\b|ing\b)"), r"re\1"),
    (re.compile(r"ll"), "l"),
    (re.compile(r"l(\b|ed\b|ing\b|er\b)"), r"ll\1"),
    (re.compile(r"se(\b|s\b)"), r"ce\1"),
    (re.compile(r"og(\b|s\b)"), r"ogue\1"),
    (re.compile(r"e(\b)"), r"ue\1"),
    (re.compile(r"^(judg|ag|acknowledg)"), r"\1e"),
    (re.compile(r"^e(sthet|on)"), r"ae\1"),
    (re.compile(r"fet"), "foet"),
    (re.compile(r"^maneuver"), "manoeuvre"),
]


def _british_form(token: str) -> str | None:
    british, american = wordlists()
    lower = token.lower()
    if lower in british or lower not in american:
        return None
    hits = set()
    for pattern, repl in ORTHOGRAPHY_RULES:
        for candidate in {pattern.sub(repl, lower, count=1), pattern.sub(repl, lower)}:
            if candidate != lower and candidate in british:
                hits.add(candidate)
    return hits.pop() if len(hits) == 1 else None


def normalise_orthography(text: str) -> tuple[str, int]:
    """Map American spellings to British ones. Returns (text, n_changes)."""
    changes = 0

    def fix(m: re.Match[str]) -> str:
        nonlocal changes
        token = m.group(0)
        british = _british_form(token)
        if british is None:
            return token
        changes += 1
        return _match_case(token, british)

    return TOKEN_RE.sub(fix, text), changes


def normalise(text: str) -> tuple[str, dict[str, int]]:
    """The full pass. Ligatures first: a broken token is not a dictionary word,
    and the orthography rules only fire on words the American list knows."""
    text, ligatures = repair_ligatures(text)
    text, spellings = normalise_orthography(text)
    return text, {"ligature_repairs": ligatures, "orthography_changes": spellings}


# --------------------------------------------------------------------------
# The residual: American institutional vocabulary, measured not rewritten
# --------------------------------------------------------------------------

US_VOCABULARY = [
    "provost",
    "board of trustees",
    "trustees",
    "regents",
    "chancellor emeritus",
    "president emeritus",
    "executive vice president",
    "senior vice president",
    "vice president",
    "vice provost",
    "dean of students",
    "semester",
    "semesters",
    "freshman",
    "freshmen",
    "sophomore",
    "junior year",
    "senior year",
    "undergraduate majors",
    "major",
    "minors",
    "tenure-track",
    "tenure track",
    "tenured",
    "gpa",
    "sat",
    "act scores",
    "land-grant",
    "land grant",
    "carnegie classification",
    "title ix",
    "fafsa",
    "pell",
    "state legislature",
    "system office",
    "flagship campus",
]

US_VOCAB_RE = re.compile(
    r"\b("
    + "|".join(re.escape(t) for t in sorted(US_VOCABULARY, key=len, reverse=True))
    + r")\b",
    re.I,
)


def us_vocabulary_hits(text: str) -> list[str]:
    return [m.group(0).lower() for m in US_VOCAB_RE.finditer(text)]


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

DEMO = (
    "The most effcient use of resources will beneft the whole university, and we "
    "must fnd the fnancial headroom to make signifcant progress, refecting our "
    "commitment to a diffcult but necessary set of frst-order choices. Our center "
    "will organize a program to analyze the behavior of the whole catalog, "
    "prioritizing enrollment and recognizing the labor involved."
)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "demo"

    if mode == "demo":
        out, stats = normalise(DEMO)
        print("BEFORE:\n" + DEMO + "\n")
        print("AFTER:\n" + out + "\n")
        print(stats)
        return

    if mode == "audit":
        import json
        import subprocess

        root = Path(__file__).resolve().parent.parent
        totals: dict[str, dict[str, int]] = {}
        prov = json.loads((root / "corpus" / "provenance.json").read_text())

        groups: dict[str, list[Path]] = {
            "real": [
                root / "corpus" / "raw" / r["file"] for r in prov["real_strategy"]
            ],
            "fabricated": sorted(
                (
                    Path.home()
                    / "projects"
                    / "slop-university"
                    / "output"
                    / "pdf"
                    / "strategy"
                ).glob("*.pdf")
            )
            + sorted(
                (
                    Path.home()
                    / "projects"
                    / "slop-university-press"
                    / "output"
                    / "pdf"
                    / "strategy"
                ).glob("*.pdf")
            ),
        }

        for side, pdfs in groups.items():
            agg = {
                "docs": 0,
                "words": 0,
                "ligature_repairs": 0,
                "orthography_changes": 0,
                "us_vocab": 0,
            }
            for pdf in pdfs:
                if not pdf.exists():
                    continue
                text = subprocess.run(
                    ["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
                    capture_output=True,
                    text=True,
                ).stdout
                _, stats = normalise(text)
                agg["docs"] += 1
                agg["words"] += len(text.split())
                agg["ligature_repairs"] += stats["ligature_repairs"]
                agg["orthography_changes"] += stats["orthography_changes"]
                agg["us_vocab"] += len(us_vocabulary_hits(text))
            totals[side] = agg

        print(
            f"{'side':<12}{'docs':>6}{'words':>10}{'ligature':>10}{'ortho':>8}{'us-vocab':>10}   per 10k words"
        )
        for side, a in totals.items():
            per = 10_000 / max(a["words"], 1)
            print(
                f"{side:<12}{a['docs']:>6}{a['words']:>10,}{a['ligature_repairs']:>10}"
                f"{a['orthography_changes']:>8}{a['us_vocab']:>10}   "
                f"lig {a['ligature_repairs'] * per:.2f}  ortho {a['orthography_changes'] * per:.2f}  "
                f"vocab {a['us_vocab'] * per:.2f}"
            )
        return

    raise SystemExit(f"unknown mode {mode!r} --- use 'demo' or 'audit'")


if __name__ == "__main__":
    main()
