#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Build the redacted stimulus set for the Slop University discrimination pilot.

Both sides go through the *same* pipeline: PDF -> pdftotext (default reading
order, no -layout) -> extraction normalisation -> paragraph segmentation ->
prose filter -> excerpt assembly -> symmetric redaction -> sampling.

The normalisation step repairs ligatures dropped by pdftotext and maps American
spelling to British; see `normalise.py` for why both were real-side-only defects
in the first run and why that direction mattered.
"""

from __future__ import annotations

import json
import random
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path

from gazetteer import derive as derive_terms, non_english_tokens
from merged_tokens import fit as fit_merges, repair as repair_merges
from normalise import normalise

SCRATCH = Path(__file__).resolve().parent.parent
RAW = SCRATCH / "corpus" / "raw"
TEXT = SCRATCH / "corpus" / "text"
OUT = SCRATCH / "stimuli"

SLOP_U = Path.home() / "projects" / "slop-university" / "output" / "pdf"
SLOP_PRESS = Path.home() / "projects" / "slop-university-press" / "output" / "pdf"

SEED = 20260801
TARGET_WORDS = 260
MIN_WORDS = 200
MAX_WORDS = 340

# --------------------------------------------------------------------------
# Redaction gazetteers. Applied symmetrically to BOTH sides.
# --------------------------------------------------------------------------

# Fictional institution + real institutions -> [UNIVERSITY]
UNIVERSITIES = [
    # fictional
    "Slop University",
    "Slop U",
    # real (long forms first so they win the longest-match ordering)
    "The Australian National University",
    "Australian National University",
    "University College London",
    "The University of Edinburgh",
    "University of Edinburgh",
    "The University of Manchester",
    "University of Manchester",
    "Michigan State University",
    "University of Toronto",
    "Trinity College Dublin",
    "The University of Dublin",
    "University of Dublin",
    "Delft University of Technology",
    "The University of Sydney",
    "University of Sydney",
    "University of New South Wales",
    "The University of Auckland",
    "University of Auckland",
    "Waipapa Taumata Rau",
    "Arizona State University",
    "TU Delft",
    "UCL",
    "ANU",
    "UNSW",
    "MSU",
    "ASU",
    "TCD",
    "U of T",
    "UoE",
    "UofA",
]

# Fictional + real org units -> [SCHOOL]
SCHOOLS = [
    # fictional canon
    "School of Continuous Improvement",
    "School of Emergent Priorities",
    "Institute for Measurable Outcomes",
    "Office of Research Outputs",
    "Adaptive Metrics Lab",
    "Trajectory Analytics Group",
    "Review Cadence Observatory",
    "Master of Applied Measurement",
    "Master of Priority Studies",
    "Impact Pathway Atlas",
    "Indicator Commons",
    "Living Dashboard",
    "Horizon Register",
    "Strategic Drift Survey",
    "Evaluation of Evaluation",
    "Improvement Grand Rounds",
    "Capability Sprints",
    "Futures in Committee",
    "Demo Quarter",
    # real
    "College of Health and Medicine",
    "College of Asia and the Pacific",
    "College of Science and Medicine",
    "College of Business and Economics",
    "Crawford School of Public Policy",
    "John Curtin School of Medical Research",
    "Research School of Physics",
    "School of Cybernetics",
    "Faculty of Arts and Social Sciences",
    "Faculty of Engineering",
    "Faculty of Medicine",
    "Faculty of Law",
    "Faculty of Science",
    "Alliance Manchester Business School",
    "Rotman School of Management",
    "Bartlett School",
    "Sydney Medical School",
    "Business School",
    "Medical School",
]

# Fictional canon roster (all 25) -> [NAME]
ROSTER = [
    "Anneke Tolan",
    "Anouk Mensah",
    "Bram Ntuli",
    "Casimir Beng",
    "Dagny Okafor",
    "Fenna Okoro",
    "Iben Chikere",
    "Ingeborg Nwachukwu",
    "Ingrid Vasseur",
    "Joost Nwosu",
    "Kwame Lindqvist",
    "Lindiwe Achterberg",
    "Marek Solheim",
    "Marit Osayande",
    "Mirela Hanke",
    "Osei Vandermeer",
    "Petra Umbile",
    "Renke Sabel",
    "Ronja Oyelaran",
    "Runa Adegoke",
    "Solveig Adeyemi",
    "Sten Okwuosa",
    "Thandiwe Solberg",
    "Torun Ezeigwe",
    "Verity Marris",
]

# Place names, demonyms, peoples -> [PLACE]
PLACES = [
    "Australian Capital Territory",
    "New South Wales",
    "United Kingdom",
    "Great Britain",
    "Northern Ireland",
    "New Zealand",
    "Aotearoa",
    "United States of America",
    "United States",
    "the Netherlands",
    "Netherlands",
    "Australia",
    "Australian",
    "Australians",
    "Canberra",
    "Acton",
    "Sydney",
    "Melbourne",
    "Brisbane",
    "Adelaide",
    "Perth",
    "Hobart",
    "Darwin",
    "Auckland",
    "Wellington",
    "Christchurch",
    "London",
    "Bloomsbury",
    "Manchester",
    "Edinburgh",
    "Scotland",
    "Scottish",
    "England",
    "English",
    "Wales",
    "Welsh",
    "Ireland",
    "Irish",
    "Dublin",
    "Toronto",
    "Ontario",
    "Canada",
    "Canadian",
    "Delft",
    "Dutch",
    "Holland",
    "Rotterdam",
    "Amsterdam",
    "Michigan",
    "East Lansing",
    "Arizona",
    "Phoenix",
    "Tempe",
    "America",
    "American",
    "Europe",
    "European",
    "Britain",
    "British",
    "Indo-Pacific",
    "Asia-Pacific",
    "Ngunnawal",
    "Ngambri",
    "Kamberri",
    "Ngunawal",
    "Torres Strait",
    "Waitangi",
    "Te Tiriti",
    "Tiriti",
    "Maori",
    "Māori",
    "Pasifika",
    "Pakeha",
    "Pākehā",
    "Whanau",
    "Whānau",
    "Taumata Teitei",
    "Aotearoa New Zealand",
    "Commonwealth of Australia",
    "the Commonwealth",
    "Commonwealth",
    "Westminster",
    "The Hague",
    "Hague",
    "Leiden",
    "Eindhoven",
    "Utrecht",
    "Glasgow",
    "Belfast",
    "Cardiff",
    "Vancouver",
    "Whitehall",
    "Ottawa",
    "Washington",
    "Brussels",
    "Canberran",
    "Kiwi",
    "Antipodean",
]

# Funders, regulators, sector bodies, rankings -> [AGENCY]
AGENCIES = [
    "Australian Research Council",
    "National Health and Medical Research Council",
    "Tertiary Education Quality and Standards Agency",
    "Higher Education Statistics Agency",
    "Research Excellence Framework",
    "Knowledge Exchange Framework",
    "Teaching Excellence Framework",
    "Office for Students",
    "UK Research and Innovation",
    "Engineering and Physical Sciences Research Council",
    "Economic and Social Research Council",
    "Medical Research Council",
    "Natural Sciences and Engineering Research Council",
    "Social Sciences and Humanities Research Council",
    "Canadian Institutes of Health Research",
    "National Science Foundation",
    "National Institutes of Health",
    "Horizon Europe",
    "Horizon 2020",
    "Erasmus",
    "Marie Sklodowska-Curie",
    "Marie Skłodowska-Curie",
    "Department of Education",
    "Australian Universities Accord",
    "Universities Australia",
    "Universities UK",
    "Russell Group",
    "Group of Eight",
    "Go8",
    "Times Higher Education",
    "QS World University",
    "Academic Ranking of World Universities",
    "Shanghai Ranking",
    "Nederlandse Organisatie voor Wetenschappelijk Onderzoek",
    "Dutch Research Council",
    "NWO",
    "UKRI",
    "EPSRC",
    "ESRC",
    "NHMRC",
    "TEQSA",
    "HESA",
    "NSERC",
    "SSHRC",
    "CIHR",
    "ARC",
    "NSF",
    "NIH",
    "OfS",
    "REF",
    "TEF",
    "KEF",
    "ATAR",
    "HECS",
    "Athena SWAN",
    "Athena Swan",
    "Universitas 21",
    "Wattle",
    "Vice-Chancellor's Committee",
]

MOTTOES = ["Edimus ergo sumus", "we publish, therefore we are"]

# --- second pass: terms found by the mechanical leakage audit -------------
# Institution shards, brand taglines and named house programmes that survived
# the first pass. Both sides are represented; nothing here is a content term.
UNIVERSITIES += [
    "Trinity",
    "Monash",
    "Waipapa",
    "Cybernetics",
    "Grant Museum",
    "Futures Institute",
    "Graduate Research School",
    "National Library",
    "Public Service",
    "Parliament",
    "School of Art",
    "College of Engineering",
    "Computing and Cybernetics",
    "Master of Applied Cybernetics",
    "Academic Affairs",
]

# Brand taglines / named house frameworks -> [ORGANISATION]
TAGLINES = [
    "Progress for All",
    "Societal Impact Goals",
    "Impact Focus Areas",
    "Strategic Pillars",
    "Grand Challenges",
    "Giving Day",
    "Innovation Day",
    "Reconciliation Action Plan",
    "Learning and Teaching Strategy",
    "Mission-based Compact",
    "Enabling Impact",
    "Vision 2030",
    "Strategy 2030",
    "Strategic Agenda",
    "Corporate Plan",
    "Athena SWAN",
    "Race Equality Charter",
    "Living Wage",
    "Widening Participation",
    "Access and Participation Plan",
]

# Statutes, charters, external frameworks -> [REF] (identity removed, the fact
# that the document cites *something* external is preserved)
STATUTES = [
    "Public Governance, Performance and Accountability Act",
    "Public Sector Equality and Human Rights Duty",
    "Public Sector Equality Duty",
    "Sustainable Development Goals",
    "Higher Education and Research Act",
    "Equality Act",
    "Freedom of Information Act",
    "Modern Slavery Act",
    "Charities Act",
    "Australian National University Act",
    "Universities Accord",
    "Paris Agreement",
    "Net Present Value",
    "Doctorate of Science",
]

# Fictional-side invented proper nouns of the *person/place* kind. Content
# terms (e.g. "Microdose Curriculum") are deliberately NOT redacted -- they are
# content, not identity, and redacting them would gut the experiment.
ROSTER += ["Hoke", "Hokean", "Henry Hoke"]

# Real people encountered in the corpus (signature blocks, quotes)
REAL_PEOPLE = [
    "Janet Legrand",
    "Legrand",
    "Peter Mathieson",
    "Mathieson",
    "Michael Spence",
    "Spence",
    "Duncan Ivison",
    "Ivison",
    "Attila Brungs",
    "Brungs",
    "Mark Scott",
    "Genevieve Bell",
    "Linda Doyle",
    "Doyle",
    "Dawn Freshwater",
    "Freshwater",
    "Nancy Wright",
    "Meric Gertler",
    "Gertler",
    "Kevin Guskiewicz",
    "Guskiewicz",
    "Michael Crow",
    "Tim van der Hagen",
    "van der Hagen",
    "Julie Bishop",
    "Girrawah House",
    "Paul Girrawah",
    "Jamie Kidston",
    "Tatiana Bur",
]

# Demographic / national-context proper nouns that identify the country
PLACES += [
    "Hispanic",
    "Latinx",
    "Latino",
    "Latina",
    "African American",
    "Aboriginal",
    "Torres Strait Islander",
    "First Nations",
    "Indigenous",
    "Nordic",
    "Scandinavian",
    "African",
    "French",
    "Pacific",
    "Asian",
    "Chinese",
    "Indian",
    "Japanese",
    "Korean",
    "Vietnamese",
    "Indonesian",
    "German",
    "Spanish",
    "Italian",
    "Russian",
    "Royal",
    "State of",
]

# Honorific-triggered person-name capture (catches real people we can't enumerate)
TITLE_RE = re.compile(
    r"\b(Professor|Prof\.?|Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Sir|Dame|Lord|Lady|Baroness|Rev\.?|Hon\.?|Emeritus Professor|The Hon\.?)\s+"
    r"([A-Z][A-Za-zÀ-ÿ'’\-]+(?:\s+(?:van|van der|de|den|der|von|di|le|la|Mc|Mac)?\s*[A-Z][A-Za-zÀ-ÿ'’\-]+){0,3})"
)

# Signature-block / role lines that carry a name on the next line
ROLE_NAME_RE = re.compile(
    r"\b(Vice-Chancellor|Chancellor|President|Provost|Principal|Rector|Dean|Director|Registrar|Chair|Treasurer|Secretary)\s*,?\s+"
    r"([A-Z][a-zÀ-ÿ'’\-]+\s+[A-Z][a-zÀ-ÿ'’\-]+)\b"
)

URL_RE = re.compile(
    r"\b(?:https?://|www\.)\S+|\b[\w.\-]+\.(?:edu|ac|org|com|net|gov)(?:\.[a-z]{2})?(?:/\S*)?\b"
)
EMAIL_RE = re.compile(r"\b[\w.\-+]+@[\w.\-]+\.\w+\b")
DOI_RE = re.compile(r"\b(?:doi:|DOI:|https?://doi\.org/)?\b10\.\d{4,5}/\S+")
ISBN_RE = re.compile(r"\bISBN[\s:]*[\d\-Xx]+")
ABN_RE = re.compile(
    r"\b(?:ABN|ACN|CRICOS|Charity No\.?|Company No\.?|Registered (?:charity|company))[\s:.]*[\w\s]{0,20}\d[\d\s]*"
)

CURRENCY_RE = re.compile(r"(?:A\$|US\$|NZ\$|C\$|CA\$|CAD|AUD|USD|NZD|GBP|EUR|£|€|¥)\s?")


def _alt(terms: list[str]) -> re.Pattern:
    terms = sorted(set(terms), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")\b")


# Tag vocabulary is deliberately COARSE. Distinct tags per category would
# themselves leak (only real documents name a statutory regulator; only the
# fabricated side names a fictional lab), so everything institutional collapses
# to one tag and everything referential to another.
# The hand-written lists above cover the fictional canon and the first run's
# twelve real institutions. Everything gathered since is derived from
# corpus/provenance.json, so adding a document to the corpus adds its
# institution to the gazetteer and the two cannot drift apart.
DERIVED = derive_terms()

ORG_RE = _alt(UNIVERSITIES + SCHOOLS + AGENCIES + TAGLINES + DERIVED["ORGANISATION"])
PERSON_RE = _alt(ROSTER + REAL_PEOPLE)
PLACE_RE = _alt(PLACES + DERIVED["PLACE"])
REF_RE = _alt(STATUTES)
MOTTO_RE = _alt(MOTTOES)

# `Unit M` --- Manchester's real innovation unit --- survived the first run's
# gazetteer, and two judges read the leftover as an unreplaced placeholder and
# inferred fabrication. A generic organisational noun followed by a lone
# capital is the shape that got through.
UNIT_LETTER_RE = re.compile(
    r"\b(Unit|Campus|Building|Block|Site|House|Wing|Centre|Center|Hub|Lab|Laboratory"
    r"|Programme|Program|Project|Faculty|Division|Team|Group|Stream|Pillar|Phase"
    r"|Cluster|Institute|School|Hall|Court|Tower|Precinct)\s+[A-Z]\b(?![a-z])"
)

TAGS = ("ORGANISATION", "PERSON", "PLACE", "REF")


def redact(text: str) -> str:
    t = text
    # identifiers -> [REF]
    t = EMAIL_RE.sub("[REF]", t)
    t = DOI_RE.sub("[REF]", t)
    t = URL_RE.sub("[REF]", t)
    t = ISBN_RE.sub("[REF]", t)
    t = ABN_RE.sub("[REF]", t)
    # named entities (longest-match gazetteers, applied before the regex
    # heuristics so that e.g. "Professor" + a place name isn't miscaptured)
    t = MOTTO_RE.sub("[REF]", t)
    t = REF_RE.sub("[REF]", t)
    t = PERSON_RE.sub("[PERSON]", t)
    t = UNIT_LETTER_RE.sub("[ORGANISATION]", t)
    t = ORG_RE.sub("[ORGANISATION]", t)
    t = PLACE_RE.sub("[PLACE]", t)
    # Non-English vocabulary. The first run redacted the name of a language and
    # not the language, so `mātauranga` and `chéile` survived and were cited by
    # judges as evidence of authenticity. Anything diacritic-bearing that is in
    # neither English word list is a national tell, whichever side carries it.
    for token in non_english_tokens(t):
        t = re.sub(rf"\b{re.escape(token)}\b", "[PLACE]", t)
    # honorific-triggered names (catches real people not in the gazetteer)
    t = TITLE_RE.sub(lambda m: f"{m.group(1)} [PERSON]", t)
    t = ROLE_NAME_RE.sub(lambda m: f"{m.group(1)} [PERSON]", t)
    # currency normalisation: every side speaks dollars
    t = CURRENCY_RE.sub("$", t)
    # collapse repeated tags and whitespace
    tagalt = "|".join(TAGS)
    t = re.sub(rf"(\[(?:{tagalt})\])(?:[\s,]+\1)+", r"\1", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------


NORMALISATION_STATS: dict[str, int] = {"ligature_repairs": 0, "orthography_changes": 0}


def pdf_to_text(pdf: Path) -> str:
    """Identical extraction for both sides: pdftotext, default reading order,
    then the symmetric normalisation pass."""
    res = subprocess.run(
        ["pdftotext", "-enc", "UTF-8", str(pdf), "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    text, stats = normalise(res.stdout)
    for k, v in stats.items():
        NORMALISATION_STATS[k] += v
    return text


WORD_RE = re.compile(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'’\-]*")

# Four or more single letters in a row: the signature of letter-spaced display
# type flattened by pdftotext.
LETTERSPACED_RE = re.compile(r"(?:\b[A-Z]\s+){4,}")


def is_prose(par: str) -> bool:
    """Keep running prose; drop covers, contents, chart labels, tables, figures."""
    words = WORD_RE.findall(par)
    if len(words) < 35:
        return False
    lines = [ln for ln in par.split("\n") if ln.strip()]
    if not lines:
        return False
    # chart-label / table blocks: many short lines
    if sum(len(ln.split()) < 6 for ln in lines) / len(lines) > 0.45:
        return False
    # digit-heavy blocks (financial tables, KPI grids)
    digits = sum(c.isdigit() for c in par)
    if digits / max(len(par), 1) > 0.075:
        return False
    # needs sentences
    if par.count(".") < 2:
        return False
    # mostly-uppercase headings
    caps = sum(1 for w in words if w.isupper() and len(w) > 1)
    if caps / len(words) > 0.25:
        return False
    # contents pages / dotted leaders
    if "...." in par or ". . . ." in par:
        return False
    # Letter-spaced display type. Designers track headings out --- "W H AT W E
    # D O" --- and pdftotext emits the tracking as real spaces, so the heading
    # arrives as a run of single characters. It is a real-side-only artefact
    # (typst generates no letter-spaced headings) and it points the same way the
    # dropped ligatures did: towards "this text is damaged, so it is fabricated".
    # Dropping the paragraph is better than trying to reassemble the words,
    # which cannot be done reliably once the word boundaries are gone.
    if LETTERSPACED_RE.search(par):
        return False
    singles = sum(1 for w in words if len(w) == 1 and w.isupper() and w != "I")
    if singles / len(words) > 0.05:
        return False
    return True


def excerpts_from_pdf(pdf: Path) -> list[str]:
    raw = pdf_to_text(pdf)
    if not raw.strip():
        return []
    # page-form-feeds -> paragraph breaks; then split on blank lines
    raw = raw.replace("\f", "\n\n")
    pars = [p.strip() for p in re.split(r"\n\s*\n", raw)]
    good = [p for p in pars if is_prose(p)]
    # drop the first prose paragraph of the doc (usually a foreword's first
    # line off the cover) -- symmetric across both sides
    out: list[str] = []
    buf: list[str] = []
    n = 0
    for p in good:
        w = len(WORD_RE.findall(p))
        if w > MAX_WORDS:
            # a long single paragraph: take a sentence window
            sents = re.split(r"(?<=[.!?])\s+", " ".join(p.split()))
            cur, cw = [], 0
            for s in sents:
                sw = len(WORD_RE.findall(s))
                if cw + sw > MAX_WORDS and cw >= MIN_WORDS:
                    out.append(" ".join(cur))
                    cur, cw = [], 0
                cur.append(s)
                cw += sw
            if cw >= MIN_WORDS:
                out.append(" ".join(cur))
            continue
        buf.append(" ".join(p.split()))
        n += w
        if n >= TARGET_WORDS:
            if MIN_WORDS <= n <= MAX_WORDS:
                out.append("\n\n".join(buf))
            buf, n = [], 0
    return out


@dataclass
class Stim:
    id: str
    condition: str  # "strategy" | "impact"
    truth: str  # "fabricated" | "real"
    source_file: str
    source_repo: str
    subtype: str  # provenance tag, e.g. "slop-brand", "anu-brand", "real"
    words: int
    text: str
    # Breadth metadata, carried through from corpus/provenance.json so the
    # re-run can report misclassification by country, tier, type and year
    # without joining back to the corpus by filename.
    country: str = ""
    tier: str = ""
    doc_type: str = ""
    year: int = 0
    institution: str = ""


def collect(pdfs: list[tuple[Path, str, str, str, str, dict]]) -> list[Stim]:
    """pdfs: (path, condition, truth, repo, subtype, metadata)"""
    rng = random.Random(SEED)
    stims: list[Stim] = []
    for path, cond, truth, repo, subtype, meta in pdfs:
        exs = excerpts_from_pdf(path)
        if not exs:
            continue
        # skip the first excerpt (cover/foreword boilerplate) when we can afford to
        pool = exs[1:] if len(exs) > 2 else exs
        rng.shuffle(pool)
        for k, ex in enumerate(pool[:4]):
            red = redact(ex)
            stims.append(
                Stim(
                    id=f"{path.stem}--{k}",
                    condition=cond,
                    truth=truth,
                    source_file=str(path),
                    source_repo=repo,
                    subtype=subtype,
                    words=len(WORD_RE.findall(red)),
                    text=red,
                    country=meta.get("country", ""),
                    tier=meta.get("tier", ""),
                    doc_type=meta.get("doc_type", ""),
                    year=int(meta.get("year") or 0),
                    institution=meta.get("institution", ""),
                )
            )
    return stims


def main() -> None:
    TEXT.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    pdfs: list[tuple[Path, str, str, str, str, dict]] = []

    # --- fabricated side -------------------------------------------------
    for repo, base in (
        ("slop-university", SLOP_U),
        ("slop-university-press", SLOP_PRESS),
    ):
        for p in sorted((base / "strategy").glob("*.pdf")):
            subtype = "anu-brand" if p.stem.startswith("anu2026") else "slop-brand"
            pdfs.append((p, "strategy", "fabricated", repo, subtype, {}))
        for p in sorted((base / "impact-report").glob("*.pdf")):
            pdfs.append((p, "impact", "fabricated", repo, "slop-brand", {}))

    # --- real side -------------------------------------------------------
    # The real side is driven by corpus/provenance.json rather than by a glob,
    # so a PDF only enters the pool if its provenance was recorded. The first
    # run dropped the two US documents because American orthography was an
    # unremovable tell against a uniformly Australian/British fabricated
    # corpus; normalise.py now maps American spelling to British on BOTH sides,
    # so exclusion by nationality is no longer needed and the US is in.
    prov = json.loads((SCRATCH / "corpus" / "provenance.json").read_text())
    for cond, key in (("strategy", "real_strategy"), ("impact", "real_impact")):
        for row in prov.get(key, []):
            path = RAW / row["file"]
            if not path.exists():
                print(f"  ! missing {row['file']} --- skipped")
                continue
            pdfs.append((path, cond, "real", "web", "real", row))

    stims = collect(pdfs)

    # Merged tokens, the last one-sided extraction defect. This cannot run
    # inside pdf_to_text with the ligature repair, because the detector is
    # fitted to the corpus's own hyphenation and so needs every excerpt in
    # hand; see merged_tokens.py for why a dictionary alone will not do it.
    split = fit_merges([(s.id.rsplit("--", 1)[0], s.text) for s in stims])
    merges = 0
    for s in stims:
        s.text, k = repair_merges(s.text, split)
        s.words = len(WORD_RE.findall(s.text))
        merges += k

    (OUT / "pool.json").write_text(json.dumps([asdict(s) for s in stims], indent=1))

    from collections import Counter

    c = Counter((s.condition, s.truth, s.subtype) for s in stims)
    for k, v in sorted(c.items()):
        print(k, v)
    print("total pool:", len(stims))
    print(
        f"normalisation: {NORMALISATION_STATS['ligature_repairs']} ligature repairs, "
        f"{NORMALISATION_STATS['orthography_changes']} spellings normalised, "
        f"{merges} merged tokens split"
    )


if __name__ == "__main__":
    main()
