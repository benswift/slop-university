#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "httpx",
# ]
# ///
"""Compare a draft PDF with recent same-preset outputs for stock language.

A negative audit, never a source of exemplars: it reports what the corpus is
already saying so a run can say something else. Three things are counted ---
the section labels a document uses, the first six words of each sentence, and
(within the current document only) self-reference to the University's own
prior outputs.

A label that appears in nearly every recent output is the blueprint's own
furniture: a paper has a Related work section, a poster carries the Office of
Research Outputs wordmark, and rotating those would break the preset, not the
template. A label in a middling number of them is the scaffold drifting into a
house style --- six of the last eight posters opening with "The problem" is the
thing worth rewriting. The two are reported separately rather than filtered,
because which is which is the blueprint's call, not this script's.

Between July and September the share of outputs whose prose is about the
University's own prior programme (rather than the world) rose from 1% to 14%:
brochures and strategies started reading as retrospectives of the corpus
instead of studies of something out there. Citing prior outputs in the
reference furniture is fine and encouraged; the prose treating them as the
subject is the drift this check flags.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import httpx

# A label in at least this share of the recent outputs is the preset's standing
# furniture rather than a scaffold that has stopped rotating.
FURNITURE_SHARE = 0.85
# Never reported at all: furniture common to every preset.
FIXED_LABELS = {
    "acknowledgements",
    "contents",
    "executive summary",
    "how we developed this plan",
    "our values",
    "references",
    "the evidence base",
    "underpinning research",
}
WORD_RE = re.compile(r"[a-z0-9]+(?:['’-][a-z0-9]+)?", re.IGNORECASE)
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")

# A line matching one of these headings marks the start of the reference /
# bibliography furniture. Self-reference is only counted in the body text
# before the last such heading (best effort; if none is found, the whole text
# is treated as body).
FURNITURE_HEADING_RE = re.compile(
    r"^(References|The evidence base|Read the work|Underpinning research|Builds on)"
)
DOI_RE = re.compile(r"10\.5555/slop\.[a-z0-9]+", re.IGNORECASE)
# Short, easy to extend: phrases that treat a prior Slop University output as
# the subject of the prose rather than reference furniture.
SELF_REFERENCE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"the university's own (research|programme|instrument|finding|earlier)",
        r"slop university's own",
        r"an? earlier (slop university )?(finding|study|instrument)",
        r"the (maturity-model|scoring|register) programme",
        r"since published and cited",
        r"the university's (research|measurement) programme",
        r"(builds|building) on the university's",
        r"the same (method|instrument|ladder) (that|the university)",
    ]
]


@dataclass(frozen=True)
class Entry:
    id: str
    published_at: str


def scalar(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?([^\n\"']+)", text)
    return match.group(1).strip() if match else ""


def recent_entries(root: Path, preset: str, current_id: str, limit: int) -> list[Entry]:
    entries: list[Entry] = []
    for path in (root / "website/src/content/outputs").glob("*.yml"):
        text = path.read_text()
        if scalar(text, "preset") != preset or path.stem == current_id:
            continue
        entries.append(
            Entry(
                id=path.stem,
                published_at=scalar(text, "publishedAt") or scalar(text, "date"),
            )
        )
    return sorted(entries, key=lambda entry: entry.published_at, reverse=True)[:limit]


def pdf_text(pdf: Path) -> str:
    result = subprocess.run(
        # NOT -layout: it interleaves a two-column paper's columns into single
        # lines, which buries every heading in the neighbouring column's prose.
        # Raw reading order follows the columns and keeps headings on their own.
        ["pdftotext", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def normalise(value: str) -> str:
    return " ".join(WORD_RE.findall(value.lower()))


def labels(text: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for raw in text.splitlines():
        line = " ".join(raw.split()).strip(" •|—–-")
        words = WORD_RE.findall(line)
        if not (2 <= len(words) <= 10 and len(line) <= 80):
            continue
        if line.endswith((".", ":", ";", "?", "!")) or any(
            char.isdigit() for char in line
        ):
            continue
        key = normalise(line)
        if key not in FIXED_LABELS:
            found.setdefault(key, line)
    return found


def sentence_frames(text: str) -> dict[str, str]:
    heading_keys = set(labels(text))
    prose_lines = [
        "." if normalise(line) in heading_keys else line
        for line in text.replace("\u00ad", "").splitlines()
    ]
    flattened = " ".join(" ".join(prose_lines).split())
    found: dict[str, str] = {}
    for sentence in SENTENCE_RE.split(flattened):
        words = WORD_RE.findall(sentence)
        if len(words) < 12 or "doi" in sentence.lower() or "http" in sentence.lower():
            continue
        # A flattened table of contents is not a sentence.
        if sum(character.isdigit() for character in sentence) > 2:
            continue
        frame = " ".join(word.lower() for word in words[:6])
        found.setdefault(frame, sentence[:180].strip())
    return found


def ledger_titles(root: Path, current_id: str) -> dict[str, str]:
    """Map output id -> title for every ledger entry except the current one.

    Titles under 3 words are skipped: too short to count as a distinctive
    verbatim match rather than a coincidence.
    """
    titles: dict[str, str] = {}
    for path in (root / "website/src/content/outputs").glob("*.yml"):
        if path.stem == current_id:
            continue
        title = scalar(path.read_text(), "title")
        if len(WORD_RE.findall(title)) < 3:
            continue
        titles[path.stem] = title
    return titles


def prior_titles_named(body: str, titles: dict[str, str]) -> list[tuple[str, str]]:
    """Prior output ids/titles that appear verbatim (case-insensitive,
    whitespace-normalised) in the body text --- named by title, not just cited
    by DOI."""
    normalised_body = normalise(body)
    found = [
        (output_id, title)
        for output_id, title in titles.items()
        if normalise(title) in normalised_body
    ]
    found.sort(key=lambda item: item[1])
    return found


def body_before_furniture(text: str) -> str:
    """Return the text up to (excluding) the last reference-furniture heading.

    Best effort: scanning from the end of the document, the first line to
    match `FURNITURE_HEADING_RE` marks the cut. If no such heading is found,
    the whole text is returned.
    """
    lines = text.splitlines()
    cut_index = len(lines)
    for index in range(len(lines) - 1, -1, -1):
        if FURNITURE_HEADING_RE.match(lines[index].strip()):
            cut_index = index
            break
    return "\n".join(lines[:cut_index])


def self_reference_findings(body: str) -> list[tuple[str, str]]:
    flattened = " ".join(body.replace("\u00ad", "").split())
    findings: list[tuple[str, str]] = []
    for sentence in SENTENCE_RE.split(flattened):
        for pattern in SELF_REFERENCE_PATTERNS:
            match = pattern.search(sentence)
            if match:
                findings.append((match.group(0), sentence[:180].strip()))
    return findings


def self_reference_report(
    current: str,
    threshold: int,
    prior_title_threshold: int,
    root: Path,
    current_id: str,
) -> int:
    body = body_before_furniture(current)
    findings = self_reference_findings(body)
    doi_count = len(set(DOI_RE.findall(body)))
    count = len(findings)
    named = prior_titles_named(body, ledger_titles(root, current_id))
    prior_count = len(named)
    print(
        f"Self-reference: {count} phrases in the body (threshold {threshold}), "
        f"{doi_count} DOIs cited in running prose, {prior_count} prior outputs "
        f"named in the body (threshold {prior_title_threshold})"
    )
    for phrase, sentence in findings[:8]:
        print(f'  "{phrase}" — {sentence}')
    for output_id, title in named[:8]:
        print(f"  {output_id} — {title!r}")
    if count > threshold or prior_count > prior_title_threshold:
        print(
            "  → the document is about the University's own programme; "
            "recompose the body so the object of study is in the world and "
            "prior outputs stay in the reference furniture."
        )
        return 1
    return 0


def compare(
    current: str,
    references: list[tuple[str, str]],
    self_reference_threshold: int,
    prior_title_threshold: int,
    root: Path,
    current_id: str,
) -> int:
    current_labels = labels(current)
    current_frames = sentence_frames(current)
    label_docs: dict[str, set[str]] = defaultdict(set)
    frame_docs: dict[str, set[str]] = defaultdict(set)
    for name, text in references:
        for value in labels(text):
            label_docs[value].add(name)
        for value in sentence_frames(text):
            frame_docs[value].add(name)

    furniture_cut = max(2, round(len(references) * FURNITURE_SHARE))
    repeated_labels = [
        (len(label_docs[label]), current_labels[label])
        for label in current_labels
        if 2 <= len(label_docs[label]) < furniture_cut
    ]
    furniture = [
        (len(label_docs[label]), current_labels[label])
        for label in current_labels
        if len(label_docs[label]) >= furniture_cut
    ]
    repeated_frames = [
        (len(frame_docs[frame]), frame, current_frames[frame])
        for frame in current_frames
        if len(frame_docs[frame]) >= 2
    ]

    print(f"recent-language: compared with {len(references)} same-preset outputs")
    if repeated_labels:
        print("Repeated non-fixed section labels:")
        for count, label in sorted(repeated_labels, reverse=True):
            print(f"  {label!r} — {count} recent documents")
    if repeated_frames:
        print("Repeated six-word sentence openings:")
        for count, frame, sentence in sorted(repeated_frames, reverse=True):
            print(f'  "{frame} …" — {count} recent documents')
            print(f"    current: {sentence}")
    if not repeated_labels and not repeated_frames:
        print("No repeated non-fixed labels or stock sentence openings found.")
    if furniture:
        print(
            "Standing furniture (in nearly every recent output; rotate one only "
            "if the blueprint leaves it free):"
        )
        for count, label in sorted(furniture, reverse=True):
            print(f"  {label!r} — {count} recent documents")
    self_reference_extra = self_reference_report(
        current, self_reference_threshold, prior_title_threshold, root, current_id
    )
    return len(repeated_labels) + len(repeated_frames) + self_reference_extra


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--reference", action="append", type=Path, default=[])
    parser.add_argument("--base-url", default="https://pdf.slop.university")
    parser.add_argument("--self-reference-threshold", type=int, default=3)
    parser.add_argument("--prior-title-threshold", type=int, default=2)
    parser.add_argument(
        "--self-reference-only",
        action="store_true",
        help=(
            "Skip the reference-PDF download/comparison and only report "
            "self-reference for the current PDF. Cheap to run mid-draft "
            "without network."
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = pdf_text(args.pdf)
    if args.self_reference_only:
        self_reference_report(
            current,
            args.self_reference_threshold,
            args.prior_title_threshold,
            args.root,
            args.pdf.stem,
        )
        return 0
    references: list[tuple[str, str]] = []
    if args.reference:
        references = [(path.stem, pdf_text(path)) for path in args.reference]
    else:
        entries = recent_entries(args.root, args.preset, args.pdf.stem, args.limit)
        with tempfile.TemporaryDirectory(prefix="slopu-language-") as directory:
            for entry in entries:
                target = Path(directory) / f"{entry.id}.pdf"
                try:
                    response = httpx.get(
                        f"{args.base_url.rstrip('/')}/{entry.id}.pdf",
                        timeout=30,
                        follow_redirects=True,
                    )
                    response.raise_for_status()
                    target.write_bytes(response.content)
                    references.append((entry.id, pdf_text(target)))
                except (
                    httpx.HTTPError,
                    OSError,
                    subprocess.CalledProcessError,
                ) as error:
                    print(f"warning: could not inspect {entry.id}: {error}")
    if not references:
        print("recent-language: no reference PDFs were available")
        return 2
    compare(
        current,
        references,
        args.self_reference_threshold,
        args.prior_title_threshold,
        args.root,
        args.pdf.stem,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
