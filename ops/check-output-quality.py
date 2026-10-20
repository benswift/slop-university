#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer"]
# ///
"""Reject a generated PDF whose last content page has collapsed.

The failure this catches is a real one in the corpus: the tail of a glossary,
an acknowledgements paragraph, or a reference block spills past the page it
belongs on and strands a few lines at the top of an otherwise empty page.

Booklet back covers are deliberately sparse, so their penultimate page is the
one under test. Papers use their final page. One-page poster formats already
have their own fit probes and are outside this check.

Calibration matters more than strictness here: a false failure rescues a run
and stalls the queue. Three signals separate the defect from a page that is
simply short, and every one of them was checked against the published corpus
(92 booklets, ~180 papers) before the thresholds below were set:

* a **heading** on the page means a section legitimately starts there. A
  booklet's closing "With thanks" or "The decade ahead" routinely runs half a
  page and is not a defect. Headings are found by type size, not by text.
* a **figure** on the page means the page carries content the text layer
  cannot see. (Raster figures only --- a purely vector chart would be missed,
  but no closing page in the corpus carries one.)
* a **well-filled** page passes on either measure: text reaching far enough
  down the page, or enough words on it.

A page fails only when it has none of the three.

The fill bar differs by format because the same number means different things.
A booklet page is one full-width column, so text stopping a third of the way
down is a visible hole. A paper page is two columns and the measure only sees
the deeper one, so references ending part-way down the left column --- which
every real two-column paper does --- must pass; only a scrap of a column is a
defect. Both bars sit inside a wide gap in the published corpus.
"""

from __future__ import annotations

import statistics
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import typer

# preset -> (page under test, minimum fill of that page). Booklet back covers
# are deliberately sparse, so their penultimate page is the one that matters.
BOOKLETS = {"brochure", "impact-report", "strategy"}
PAPERS = {"paper"}
# A thesis ends on an appendix page, whose fill says nothing; what a collapsed
# thesis run looks like is a short document. The blueprint's range starts at
# 100 pages; the floor sits under it so a lean but complete thesis passes.
THESES = {"thesis"}
THESIS_MIN_PAGES = 80
# A runaway run repeating itself is the other failure a page count sees.
THESIS_MAX_PAGES = 220
# Booklets: published defects reach 0.375, the shallowest legitimate page 0.656.
BOOKLET_MIN_FILL = 0.66
# Papers: two lines alone on a page reach 0.11; three reference entries reach
# 0.29 and read as an ordinary paper. 8% of the published corpus sits below.
PAPER_MIN_FILL = 0.30

# Running furniture (folio, rules) lives in the bottom tenth. It must not make
# a stranded paragraph at the top of a page look like a full page.
FURNITURE_BAND = 0.9
# A heading is set larger than body text. The house booklets run ~1.9x, papers
# ~1.15x; the margin below is wide enough to catch both and tight enough that
# no run of body text trips it.
HEADING_RATIO = 1.35


@dataclass(frozen=True)
class PageMeasure:
    page: int
    pages: int
    words: int
    endpoint: float
    heading: str
    figures: int


def page_count(pdf: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(pdf)], check=True, capture_output=True, text=True
    )
    for line in result.stdout.splitlines():
        if line.startswith("Pages:"):
            return int(line.split(":", 1)[1].strip())
    raise ValueError(f"pdfinfo returned no page count for {pdf}")


def target(preset: str, pages: int) -> tuple[int, float] | None:
    if preset in BOOKLETS:
        if pages < 2:
            raise ValueError(
                f"{preset} needs a back cover but the PDF has {pages} page(s)"
            )
        return pages - 1, BOOKLET_MIN_FILL
    if preset in PAPERS:
        return pages, PAPER_MIN_FILL
    return None


def figure_count(pdf: Path, page: int) -> int:
    result = subprocess.run(
        ["pdfimages", "-list", "-f", str(page), "-l", str(page), str(pdf)],
        check=True,
        capture_output=True,
        text=True,
    )
    # Two header lines, then one row per image.
    return max(0, len(result.stdout.strip().splitlines()) - 2)


def measure_page(pdf: Path, page: int, pages: int) -> PageMeasure:
    result = subprocess.run(
        ["pdftotext", "-f", str(page), "-l", str(page), "-bbox", str(pdf), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    root = ET.fromstring(result.stdout)
    page_node = root.find(".//{*}page")
    if page_node is None:
        raise ValueError(f"pdftotext returned no page geometry for page {page}")

    height = float(page_node.attrib["height"])
    words = [
        node
        for node in page_node.findall(".//{*}word")
        if float(node.attrib["yMax"]) < height * FURNITURE_BAND
    ]
    sizes = [float(node.attrib["yMax"]) - float(node.attrib["yMin"]) for node in words]
    body = statistics.median(sizes) if sizes else 0.0
    heading = " ".join(
        (node.text or "")
        for node, size in zip(words, sizes)
        if size >= body * HEADING_RATIO
    ).strip()
    endpoint = max((float(node.attrib["yMax"]) for node in words), default=0.0)
    return PageMeasure(
        page=page,
        pages=pages,
        words=len(words),
        endpoint=endpoint / height,
        heading=heading,
        figures=figure_count(pdf, page),
    )


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command(help=__doc__)
def main(
    pdf: Path,
    preset: Annotated[str, typer.Option("--preset")],
    # Overrides the per-format default above.
    min_fill: Annotated[float | None, typer.Option("--min-fill")] = None,
    # A page this wordy is carrying a section, however far down it reaches.
    full_words: Annotated[int, typer.Option("--full-words")] = 230,
    # A heading or a figure earns the page its place, but not if it is bare.
    min_fill_with_content: Annotated[
        float, typer.Option("--min-fill-with-content")
    ] = 0.2,
) -> None:
    raise typer.Exit(check(pdf, preset, min_fill, full_words, min_fill_with_content))


def check(
    pdf: Path,
    preset: str,
    min_fill: float | None,
    full_words: int,
    min_fill_with_content: float,
) -> int:
    if not pdf.is_file():
        raise FileNotFoundError(pdf)

    pages = page_count(pdf)
    if preset in THESES:
        if pages < THESIS_MIN_PAGES:
            print(
                f"quality failure: thesis has {pages} pages; "
                f"the floor is {THESIS_MIN_PAGES}",
                file=sys.stderr,
            )
            return 1
        if pages > THESIS_MAX_PAGES:
            print(
                f"quality failure: thesis has {pages} pages; "
                f"the ceiling is {THESIS_MAX_PAGES}",
                file=sys.stderr,
            )
            return 1
        print(
            f"quality: thesis has {pages} pages "
            f"(floor {THESIS_MIN_PAGES}, ceiling {THESIS_MAX_PAGES})"
        )
        return 0
    chosen = target(preset, pages)
    if chosen is None:
        print(f"quality: {preset} uses its preset-specific one-page fit check")
        return 0
    page, default_fill = chosen
    min_fill = min_fill if min_fill is not None else default_fill

    measure = measure_page(pdf, page, pages)
    carries = []
    if measure.heading:
        carries.append(f"heading {measure.heading[:40]!r}")
    if measure.figures:
        carries.append(f"{measure.figures} figure(s)")
    print(
        f"quality: page {measure.page}/{measure.pages}: {measure.words} words; "
        f"text reaches {measure.endpoint:.1%} of page height"
        + (f"; carries {', '.join(carries)}" if carries else "")
    )

    filled = measure.endpoint >= min_fill or measure.words >= full_words
    if carries:
        # A section opening here, or a figure, is content in its own right.
        floor = min_fill_with_content
        if filled or measure.endpoint >= floor:
            return 0
        reason = (
            f"text ends at {measure.endpoint:.1%} of page height (minimum {floor:.0%})"
        )
    elif filled:
        return 0
    else:
        reason = (
            f"{measure.words} words ending at {measure.endpoint:.1%} of page height "
            f"(needs {min_fill:.0%} fill, {full_words} words, "
            f"a section heading, or a figure)"
        )

    print(
        "quality failure: final content page is orphaned or substantially "
        f"underfilled: {reason}",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    app()
