#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Derive redaction terms from the corpus provenance, rather than by hand.

The first run's gazetteer was hand-curated for twelve institutions, which was
tractable and still leaked: it removed Manchester's name but left `Unit M`
standing. At a hundred-odd institutions a hand-written list is not merely
tedious, it is unauditable --- nobody can tell from reading it which entries are
missing. So the identity terms are generated from `corpus/provenance.json`,
which means adding a document to the corpus automatically adds its institution
to the gazetteer, and the two cannot drift apart.

Three things are derived per institution:

  full forms      "The University of Manchester", "University of Manchester",
                  "Manchester University" --- the same body under the article
                  and word-order variants that actually appear in prose
  distinctive     the tokens left once generic higher-education vocabulary is
                  stripped: "Manchester", "Otago", "Wageningen", "Karlsruhe"
  acronyms        initialisms of 2-5 characters: ANU, UCL, UNSW, UBC, RMIT

Matching is case-sensitive, so a distinctive token only fires in its
capitalised form: `Thrive` from a plan's title is redacted, the verb "thrive"
in running prose is not.

Two further passes close gaps the first run found after the fact:

  demonyms        derived from each document's country, so a corpus spanning 25
                  countries does not let nationality stand in for authenticity
  non-English     te reo Māori, Irish and Welsh vocabulary. The first run's
                  gazetteer redacted the *name* `Māori` but not the language, so
                  `mātauranga` and `chéile` survived in three excerpts and were
                  cited by judges. Detection is by diacritic plus dictionary
                  miss, with a curated list for the undiacriticked terms.

    uv run --script scripts/gazetteer.py          # show what is derived
    uv run --script scripts/gazetteer.py --terms  # dump the raw term list
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "corpus" / "provenance.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from normalise import wordlists  # noqa: E402

# Higher-education vocabulary shared by every institution: carries no identity,
# and redacting it would gut both sides equally for no gain.
GENERIC = {
    "university",
    "universities",
    "univ",
    "college",
    "institute",
    "institution",
    "school",
    "academy",
    "polytechnic",
    "technological",
    "technology",
    "technical",
    "science",
    "sciences",
    "applied",
    "research",
    "studies",
    "education",
    "higher",
    "national",
    "state",
    "royal",
    "metropolitan",
    "federal",
    "public",
    "open",
    "the",
    "of",
    "for",
    "and",
    "in",
    "at",
    "de",
    "der",
    "van",
    "von",
    "di",
    "du",
    "vrije",
    "universiteit",
    "universitat",
    "universität",
    "universidad",
    "universidade",
    "universita",
    "università",
    "université",
    "universite",
    "hochschule",
    "fachhochschule",
    "instituut",
    "institut",
    "eidgenossische",
    "campus",
    "centre",
    "center",
    "faculty",
    "graduate",
    "business",
    "management",
    # domain and direction words: they say what an institution teaches or where
    # it sits, not which institution it is
    "art",
    "arts",
    "agricultural",
    "agriculture",
    "music",
    "medical",
    "medicine",
    "law",
    "engineering",
    "economics",
    "veterinary",
    "catholic",
    "christian",
    "western",
    "eastern",
    "northern",
    "southern",
    "central",
    "new",
    "old",
    "saint",
}

# Words that a plan's *title* shares with every other plan's title.
TITLE_GENERIC = {
    "strategy",
    "strategic",
    "plan",
    "plans",
    "planning",
    "vision",
    "mission",
    "our",
    "we",
    "the",
    "a",
    "an",
    "of",
    "for",
    "to",
    "and",
    "in",
    "on",
    "with",
    "future",
    "futures",
    "forward",
    "ahead",
    "beyond",
    "towards",
    "toward",
    "corporate",
    "annual",
    "institutional",
    "development",
    "agenda",
    "framework",
    "report",
    "review",
    "delivering",
    "delivery",
    "roadmap",
    "blueprint",
    "excellence",
    "impact",
    "together",
    "next",
    "new",
    "one",
    "first",
    "world",
    "global",
    "international",
    "sustainable",
    "society",
    "change",
    "changing",
    "years",
    "year",
    "part",
    "edition",
    "version",
    "final",
    "draft",
    "web",
}

COUNTRY_DEMONYMS: dict[str, list[str]] = {
    "Australia": ["Australian", "Australians", "Australia"],
    "New Zealand": [
        "New Zealand",
        "New Zealander",
        "New Zealanders",
        "Aotearoa",
        "Kiwi",
    ],
    "UK": ["British", "Britain", "England", "English", "United Kingdom"],
    "Scotland": ["Scottish", "Scotland", "Scots"],
    "Wales": ["Welsh", "Wales", "Cymru", "Cymraeg"],
    "Northern Ireland": ["Northern Irish", "Northern Ireland", "Ulster"],
    "Ireland": ["Irish", "Ireland", "Éire", "Eire", "Gaeltacht", "Gaeilge"],
    "USA": ["American", "Americans", "United States", "U.S.", "US "],
    "Canada": ["Canadian", "Canadians", "Canada", "Québec", "Quebec"],
    "Netherlands": ["Dutch", "Netherlands", "Holland", "Nederland"],
    "Belgium": ["Belgian", "Belgium", "Flemish", "Flanders", "Wallonia"],
    "Germany": ["German", "Germans", "Germany", "Deutschland", "Länder"],
    "Austria": ["Austrian", "Austria", "Österreich"],
    "Switzerland": ["Swiss", "Switzerland", "Schweiz"],
    "Sweden": ["Swedish", "Sweden", "Sverige"],
    "Norway": ["Norwegian", "Norway", "Norge"],
    "Denmark": ["Danish", "Denmark", "Danmark"],
    "Finland": ["Finnish", "Finland", "Suomi"],
    "Iceland": ["Icelandic", "Iceland", "Ísland"],
    "Spain": ["Spanish", "Spain", "España", "Catalan", "Catalonia", "Catalunya"],
    "Portugal": ["Portuguese", "Portugal"],
    "Italy": ["Italian", "Italy", "Italia"],
    "France": ["French", "France"],
    "Poland": ["Polish", "Poland", "Polska"],
    "Czechia": ["Czech", "Czechia", "Czech Republic", "Česká"],
    "Estonia": ["Estonian", "Estonia", "Eesti"],
    "Latvia": ["Latvian", "Latvia"],
    "Lithuania": ["Lithuanian", "Lithuania", "Lietuva"],
    "Slovenia": ["Slovenian", "Slovene", "Slovenia", "Slovenija"],
    "Hungary": ["Hungarian", "Hungary", "Magyar"],
    "Croatia": ["Croatian", "Croatia", "Hrvatska"],
    "Greece": ["Greek", "Greece", "Hellenic"],
}

# Non-English institutional vocabulary that carries no diacritic, so the
# dictionary-miss rule below cannot catch it.
NON_ENGLISH_TERMS = [
    # te reo Māori
    "matauranga",
    "mātauranga",
    "kaupapa",
    "tikanga",
    "whanau",
    "whānau",
    "iwi",
    "hapu",
    "hapū",
    "marae",
    "mana",
    "manaakitanga",
    "kaitiakitanga",
    "rangatiratanga",
    "tangata whenua",
    "te reo",
    "te ao",
    "wananga",
    "wānanga",
    "aroha",
    "pōwhiri",
    "powhiri",
    "koha",
    "hauora",
    "mahi",
    "taonga",
    "whakapapa",
    "tino",
    "pākehā",
    "pakeha",
    "Pasifika",
    "Te Tiriti",
    "Tiriti",
    "Waitangi",
    "Aotearoa",
    # Irish
    "chéile",
    "cheile",
    "Gaeilge",
    "Gaeltacht",
    "Éire",
    "Fáilte",
    "failte",
    "Oireachtas",
    "Taoiseach",
    "Údarás",
    "Udaras",
    # Welsh
    "Cymraeg",
    "Cymru",
    "Prifysgol",
    "Cymreig",
    # Scots Gaelic
    "Gàidhlig",
    "Gaidhlig",
    "Alba",
]

ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
WORD_RE = re.compile(r"[A-Za-zÀ-ÿĀ-ž][A-Za-zÀ-ÿĀ-ž'’\-]*")
DIACRITIC_RE = re.compile(r"[À-ÿĀ-ž]")


@lru_cache(maxsize=1)
def _english() -> frozenset[str]:
    british, american = wordlists()
    return british | american


def _tokens(name: str) -> list[str]:
    return [t for t in WORD_RE.findall(name)]


def _distinctive(name: str) -> list[str]:
    return [t for t in _tokens(name) if t.lower() not in GENERIC and len(t) > 2]


def _acronyms(name: str) -> list[str]:
    out = []
    for words in (_tokens(name), _distinctive(name)):
        letters = "".join(
            w[0].upper() for w in words if w[0].isupper() or w.lower() not in GENERIC
        )
        if 2 <= len(letters) <= 5:
            out.append(letters)
    # acronyms already printed in the name, e.g. "UNSW Sydney", "TU Delft"
    out.extend(ACRONYM_RE.findall(name))
    return out


def _name_variants(name: str) -> list[str]:
    out = {name}
    stripped = re.sub(r"^The\s+", "", name)
    out.add(stripped)
    out.add(f"The {stripped}")
    m = re.match(r"(?:The\s+)?University of (.+)$", name)
    if m:
        out.add(f"{m.group(1)} University")
        out.add(f"The University of {m.group(1)}")
    m = re.match(r"(?:The\s+)?(.+) University$", name)
    if m and " of " not in m.group(1):
        out.add(f"University of {m.group(1)}")
    return sorted(out)


@lru_cache(maxsize=1)
def derive() -> dict[str, list[str]]:
    """Return the derived term lists, keyed by the tag they redact to."""
    if not PROVENANCE.exists():
        raise SystemExit(
            f"no provenance at {PROVENANCE} --- run merge_provenance.py first"
        )
    prov = json.loads(PROVENANCE.read_text())
    rows = prov.get("real_strategy", []) + prov.get("real_impact", [])

    orgs: set[str] = set()
    places: set[str] = set()

    for row in rows:
        name = row.get("institution", "")
        if name:
            orgs.update(_name_variants(name))
            orgs.update(_acronyms(name))
            places.update(_distinctive(name))
        # Titles contribute only their coinages and foreign words --- "Taumata
        # Teitei", "Girrawah" --- never ordinary English. A title word like
        # `Ambition` or `Action` names no institution, and redacting it would
        # delete exactly the aspirational register the vagueness axis measures.
        for token in _distinctive(row.get("title", "")):
            if token.lower() in TITLE_GENERIC or token.lower() in _english():
                continue
            orgs.add(token)
        places.update(COUNTRY_DEMONYMS.get(row.get("country", ""), []))

    places.update(NON_ENGLISH_TERMS)

    # A one- or two-character residue is noise, not identity.
    orgs = {t for t in orgs if len(t) > 2}
    places = {t for t in places if len(t) > 2}
    return {"ORGANISATION": sorted(orgs), "PLACE": sorted(places)}


def non_english_tokens(text: str) -> set[str]:
    """Diacritic-bearing tokens in neither English word list.

    This is what the first run's gazetteer had no rule for: it knew the word
    `Māori` and so removed it, and knew nothing of `mātauranga`.
    """
    british, american = wordlists()
    known = british | american
    return {
        t
        for t in WORD_RE.findall(text)
        if DIACRITIC_RE.search(t) and t.lower() not in known and len(t) > 2
    }


def main() -> None:
    terms = derive()
    if "--terms" in sys.argv:
        for tag, ts in terms.items():
            for t in ts:
                print(f"{tag}\t{t}")
        return

    prov = json.loads(PROVENANCE.read_text())
    rows = prov.get("real_strategy", []) + prov.get("real_impact", [])
    print(
        f"derived from {len(rows)} documents, {len({r['institution'] for r in rows})} institutions\n"
    )
    for tag, ts in terms.items():
        print(f"[{tag}] {len(ts)} terms")
        print("  " + ", ".join(ts[:30]))
        if len(ts) > 30:
            print(f"  ... and {len(ts) - 30} more")
        print()


if __name__ == "__main__":
    main()
