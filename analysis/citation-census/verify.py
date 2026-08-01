#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx"]
# ///
"""
Verification pass: take a random sample of distinct external works
(from distinct_works.json) and check DOI/arXiv resolution against
Crossref / arXiv / OpenAlex, plus a fuzzy title-match check against
the resolved record so we catch "resolves but to the wrong work"
(mis-keyed DOIs), not just "doesn't resolve at all".
"""

import json
import random
import re
import time
from pathlib import Path

import httpx

OUT = Path(__file__).parent
random.seed(20260801)

distinct = json.loads((OUT / "distinct_works.json").read_text())

SAMPLE_N = 100
sample = random.sample(distinct, min(SAMPLE_N, len(distinct)))


def norm(s: str) -> set[str]:
    s = re.sub(r"[{}\\^'\"]", "", s or "")
    words = re.findall(r"[a-z0-9]+", s.lower())
    stop = {
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "for",
        "and",
        "to",
        "with",
        "is",
        "are",
        "as",
        "at",
        "by",
    }
    return {w for w in words if w not in stop and len(w) > 2}


def title_match(a: str, b: str) -> float:
    """Similarity over the LONGER token set --- strict, and the right default.

    Crossref stores some titles truncated, which makes this measure read a
    correct resolution as a mismatch: the intersection is bounded by the short
    title while the denominator is the long one. On the first census run that
    turned six correct resolutions into apparent mis-keyed DOIs and reported
    ~86% correct-work resolution instead of the true ~99%. See `is_match`,
    which is what callers should use."""
    sa, sb = norm(a), norm(b)
    if not sa or not sb:
        return 0.0
    inter = len(sa & sb)
    return inter / max(len(sa), len(sb))


def containment(a: str, b: str) -> float:
    """Overlap as a fraction of the SHORTER token set: ~1.0 when one title is a
    truncation of the other."""
    sa, sb = norm(a), norm(b)
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / min(len(sa), len(sb))


def words(s: str) -> list[str]:
    """Word SEQUENCE, unlike norm()'s set --- prefix testing needs the order."""
    return re.findall(r"[a-z0-9]+", re.sub(r"[{}\\^'\"]", "", s or "").lower())


def is_truncation(a: str, b: str) -> bool:
    """True when the shorter title is a literal prefix of the longer.

    This is the exact signature of Crossref's truncated records ("Web Surveys"
    for "Web Surveys: A Review of Issues and Approaches"), and it is a far
    better test than token containment: a two-word title carries too few tokens
    to clear any sensible containment floor, yet a prefix match on it is strong
    evidence rather than weak. A wrong DOI does not normally resolve to a
    record whose title is a word-for-word opening fragment of the cited one."""
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return False
    short, long = (wa, wb) if len(wa) <= len(wb) else (wb, wa)
    return len(short) >= 2 and long[: len(short)] == short


def is_match(a: str, b: str) -> tuple[bool, str]:
    """A cited title matches a resolved record if it is similar outright, or if
    one is a truncation of the other."""
    sim = title_match(a, b)
    if sim >= 0.5:
        return True, f"sim={sim:.2f}"
    if is_truncation(a, b):
        return True, f"sim={sim:.2f} truncated record (prefix match)"
    return False, f"sim={sim:.2f} containment={containment(a, b):.2f}"


def extract_arxiv_id(entry: dict) -> str | None:
    j = (entry.get("journal") or "") + " " + (entry.get("eprint") or "")
    m = re.search(r"(\d{4}\.\d{4,5})(v\d+)?", j)
    if m:
        return m.group(1)
    return None


# Crossref 301s some DOIs (case-normalised suffixes); without following them
# a live, correct record reads as an HTTP failure rather than a resolution.
client = httpx.Client(
    timeout=15, follow_redirects=True, headers={"User-Agent": "slop-census/1.0 (mailto:ben@benswift.me)"}
)

results = []
for i, e in enumerate(sample):
    row = {
        "title": e["title"],
        "author": e["author"],
        "year": e["year"],
        "doi": e.get("doi"),
        "count": e["count"],
    }
    doi = (e.get("doi") or "").strip()
    arxiv_id = extract_arxiv_id(e)

    status = None
    detail = None
    resolved_title = None

    if doi:
        try:
            r = client.get(f"https://api.crossref.org/works/{doi}")
            if r.status_code == 200:
                msg = r.json()["message"]
                resolved_title = (msg.get("title") or [""])[0]
                ok, why = is_match(e["title"], resolved_title)
                status = "resolved_match" if ok else "resolved_title_mismatch"
                detail = f"crossref {why}"
            elif r.status_code == 404:
                status = "doi_not_found_crossref"
            else:
                status = f"crossref_http_{r.status_code}"
        except Exception as ex:
            status = "crossref_error"
            detail = str(ex)[:200]

        # if crossref failed/mismatched and doi looks like an arXiv DOI, try arXiv API too
        if status in ("doi_not_found_crossref",) and "10.48550" in doi:
            m = re.search(r"arxiv\.(\d{4}\.\d{4,5})", doi)
            if m:
                arxiv_id = m.group(1)

    if not doi and arxiv_id:
        status = "no_doi_has_arxiv_id"

    if arxiv_id and status in (
        None,
        "doi_not_found_crossref",
        "no_doi_has_arxiv_id",
        f"crossref_http_404",
    ):
        try:
            r = client.get(
                "https://export.arxiv.org/api/query", params={"id_list": arxiv_id}
            )
            if r.status_code == 200 and "<entry>" in r.text:
                m = re.search(
                    r"<title>(.*?)</title>", r.text.split("<entry>", 1)[1], re.S
                )
                resolved_title = (m.group(1).strip() if m else "").replace("\n", " ")
                ok, why = is_match(e["title"], resolved_title)
                status = (
                    "arxiv_resolved_match" if ok else "arxiv_resolved_title_mismatch"
                )
                detail = f"arxiv {why}"
            else:
                status = (status or "") + "+arxiv_not_found"
        except Exception as ex:
            status = (status or "") + "+arxiv_error"
            detail = str(ex)[:200]

    if status is None:
        status = "no_doi_no_arxiv_id"

    row["arxiv_id"] = arxiv_id
    row["status"] = status
    row["detail"] = detail
    row["resolved_title"] = resolved_title
    results.append(row)
    print(f"[{i + 1}/{len(sample)}] {status:35s} {e['title'][:60]}")
    time.sleep(0.15)

(OUT / "verification_sample.json").write_text(json.dumps(results, indent=2))

from collections import Counter

print("\n=== Summary ===")
c = Counter(r["status"] for r in results)
for k, v in c.most_common():
    print(f"  {k}: {v}")
