#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27", "pyyaml>=6"]
# ///
"""Fetch the colophon video's images into assets/ (gitignored): the colophon
page's hero, the roster's headshots, and the thumbnails of the newest A-series
outputs (portrait, 1:√2), with assets/outputs.json listing them and the count
of every output published."""

import json
import shutil
from pathlib import Path

import httpx
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
ASSETS = HERE / "assets"
THUMBS = 120
IMG = "https://img.slop.university/thumbs"


def main() -> None:
    (ASSETS / "thumbs").mkdir(parents=True, exist_ok=True)
    (ASSETS / "headshots").mkdir(exist_ok=True)
    shutil.copy(
        REPO / "website/src/content/pages/_heroes/colophon.avif", ASSETS / "hero.avif"
    )
    roster = yaml.safe_load((REPO / "canon/roster.yml").read_text())
    people = roster["researchers"]
    heads = sorted(
        p["id"] for p in people if (REPO / f"canon/headshots/{p['id']}.jpg").is_file()
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
    picked = []
    with httpx.Client(timeout=60) as http:
        for _, oid, e in entries:
            t = e.get("thumb")
            if not t or not 1.40 <= t["height"] / t["width"] <= 1.43:
                continue
            out = ASSETS / "thumbs" / f"{len(picked):03d}.avif"
            if not out.is_file():
                r = http.get(f"{IMG}/{oid}-320.avif")
                r.raise_for_status()
                out.write_bytes(r.content)
            picked.append({"id": oid, "title": e["title"], "doi": e["doi"]})
            if len(picked) == THUMBS:
                break
    (ASSETS / "outputs.json").write_text(
        json.dumps(
            {"total": len(entries), "headshots": heads, "outputs": picked}, indent=1
        )
    )
    print(f"{len(picked)} thumbnails, {len(heads)} headshots, {len(entries)} outputs")


if __name__ == "__main__":
    main()
