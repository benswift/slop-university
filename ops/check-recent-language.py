#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# ///
"""Compare a draft PDF with recent same-preset outputs for stock language.

A negative audit, never a source of exemplars: it reports what the corpus is
already saying so a run can say something else. Two things are counted --- the
section labels a document uses, and the first six words of each sentence.

A label that appears in nearly every recent output is the blueprint's own
furniture: a paper has a Related work section, a poster carries the Office of
Research Outputs wordmark, and rotating those would break the preset, not the
template. A label in a middling number of them is the scaffold drifting into a
house style --- six of the last eight posters opening with "The problem" is the
thing worth rewriting. The two are reported separately rather than filtered,
because which is which is the blueprint's call, not this script's.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

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


def compare(current: str, references: list[tuple[str, str]]) -> int:
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
    return len(repeated_labels) + len(repeated_frames)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--reference", action="append", type=Path, default=[])
    parser.add_argument("--base-url", default="https://pdf.slop.university")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    current = pdf_text(args.pdf)
    references: list[tuple[str, str]] = []
    if args.reference:
        references = [(path.stem, pdf_text(path)) for path in args.reference]
    else:
        entries = recent_entries(args.root, args.preset, args.pdf.stem, args.limit)
        with tempfile.TemporaryDirectory(prefix="slopu-language-") as directory:
            for entry in entries:
                target = Path(directory) / f"{entry.id}.pdf"
                try:
                    urllib.request.urlretrieve(
                        f"{args.base_url.rstrip('/')}/{entry.id}.pdf", target
                    )
                    references.append((entry.id, pdf_text(target)))
                except (OSError, subprocess.CalledProcessError) as error:
                    print(f"warning: could not inspect {entry.id}: {error}")
    if not references:
        print("recent-language: no reference PDFs were available")
        return 2
    compare(current, references)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
