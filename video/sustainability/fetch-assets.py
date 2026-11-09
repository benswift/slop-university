#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27", "pyyaml>=6", "segno>=1.6"]
# ///
"""Fetch the sustainability film's images into assets/ (gitignored): the
newest A-series output covers for the grid, one cover of each kind the script
names, the ten theses, the roster's headshots, and a QR code for the
sustainability page, with assets/outputs.json listing them.

The four generated clips (assets/clips/*.mp4: press, quad, server, hall) are
not fetched: they are Veo 3.1 renders from house-style stills, kept with the
other assets and listed in the script's "Generated clips" section."""

import json
import shutil
from pathlib import Path

import httpx
import segno
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASSETS = HERE / "assets"
IMG = "https://img.slop.university/thumbs"
GRID = 160
URL = "https://slop.university/sustainability/"
# the script's kinds, each with the thumb shape (height / width) to pick
KINDS = {
    "paper": ("slop-paper-", 1.41),
    "poster": ("slop-poster-", 1.78),
    "thesis": ("slop-thesis-", 1.41),
    "strategy": ("slop-strategy-", 1.41),
    "film": ("slop-explainer-", 0.56),
}


def fetch(http: httpx.Client, oid: str, size: int, out: Path) -> None:
    if out.is_file():
        return
    r = http.get(f"{IMG}/{oid}-{size}.avif")
    r.raise_for_status()
    out.write_bytes(r.content)


def main() -> None:
    for d in ("thumbs", "kinds", "theses", "headshots"):
        (ASSETS / d).mkdir(parents=True, exist_ok=True)
    roster = yaml.safe_load((REPO / "canon/roster.yml").read_text())["researchers"]
    heads = sorted(
        p["id"] for p in roster if (REPO / f"canon/headshots/{p['id']}.jpg").is_file()
    )
    for pid in heads:
        shutil.copy(
            REPO / f"canon/headshots/{pid}.jpg", ASSETS / "headshots" / f"{pid}.jpg"
        )

    entries = []
    for f in (REPO / "website/src/content/outputs").glob("*.yml"):
        e = yaml.safe_load(f.read_text())
        entries.append((str(e["publishedAt"]), f.stem, e))
    entries.sort(reverse=True)
    shape = lambda e: (
        round(e["thumb"]["height"] / e["thumb"]["width"], 2) if e.get("thumb") else 0
    )  # noqa: E731

    grid, kinds, theses = [], {}, []
    with httpx.Client(timeout=60) as http:
        for _, oid, e in entries:
            if len(grid) < GRID and 1.40 <= shape(e) <= 1.43:
                fetch(http, oid, 320, ASSETS / "thumbs" / f"{len(grid):03d}.avif")
                grid.append(oid)
            for kind, (prefix, ratio) in KINDS.items():
                if (
                    kind not in kinds
                    and oid.startswith(prefix)
                    and abs(shape(e) - ratio) < 0.02
                ):
                    fetch(http, oid, 640, ASSETS / "kinds" / f"{kind}.avif")
                    kinds[kind] = {"id": oid, "ratio": shape(e)}
            if oid.startswith("slop-thesis-") and shape(e):
                fetch(http, oid, 640, ASSETS / "theses" / f"{len(theses)}.avif")
                theses.append(oid)

    segno.make(URL, error="m").save(
        ASSETS / "qr.svg", scale=10, border=0, dark="#1a1a1a", light=None
    )
    (ASSETS / "outputs.json").write_text(
        json.dumps(
            {
                "grid": grid,
                "kinds": kinds,
                "theses": theses,
                "headshots": heads,
                "qr": URL,
            },
            indent=1,
        )
    )
    print(
        f"{len(grid)} grid covers, {len(kinds)} kinds, {len(theses)} theses, {len(heads)} headshots"
    )


if __name__ == "__main__":
    main()
