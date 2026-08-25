#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pillow>=11.2", "pyyaml>=6"]
# ///
"""Encode per-publish images into the ladders the img bucket serves.

Heroes, thumbnails, and og cards used to be committed under
`website/src/assets/` and pushed through astro:assets at build time. They now
live in the img bucket (see bucket-sync.py), pre-encoded here at publish time,
and the site derives URLs from the entry id + the dims recorded in frontmatter.

The rung ladders and the ≤-source-width filter are duplicated, deliberately and
exactly, in `website/src/lib/images.ts` — the site must reconstruct the same
rung set from the recorded dims that this script actually encoded. Change one,
change both. When no ladder rung fits (source narrower than the smallest rung),
both sides fall back to a single rung at the source width.

Encoding: Pillow decodes (AVIF included) and resizes; `avifenc` encodes with
the house recipe (same parameters as skills/_shared/image-workflow.md); og
cards are JPEG quality 70 at width ≤1200 — matching what the site's OpenGraph
component used to ask of astro:assets. og heights round half-up, mirrored in
images.ts (a 1px disagreement would only mis-state a meta tag, but why allow
it).

Usage:
  ops/encode-images.py encode hero      --source F --id ID   # → heroes/outputs + og/outputs
  ops/encode-images.py encode news-hero --source F --id ID   # → heroes/news + og/news
  ops/encode-images.py encode thumb     --source F --id ID   # → thumbs (no og: outputs og from hero)
  ops/encode-images.py backfill [--write-frontmatter]        # all existing entries

`encode` stages under data/pending-uploads/img/ --- or $SLOPU_PENDING_DIR/img
when a generator slot set one (override: --pending-dir) --- and
prints the dims snippet to record in the entry's frontmatter. `backfill`
iterates every outputs entry and own-hero news post, encodes from the committed
assets (AVIF→AVIF generational loss accepted: these are 2K+ masters going to
smaller display rungs), reports orphans in both directions, and with
--write-frontmatter inserts the dims into each yml/md.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import yaml
from PIL import Image

REPO = Path(__file__).resolve().parent.parent

# Coupled to website/src/lib/images.ts (HERO_WIDTHS / THUMB_WIDTHS).
HERO_WIDTHS = [800, 1600, 2560]
THUMB_WIDTHS = [320, 640, 960]
OG_MAX_WIDTH = 1200
OG_JPEG_QUALITY = 70

# The house AVIF recipe, verbatim from skills/_shared/image-workflow.md.
AVIFENC_ARGS = [
    "-j",
    "4",
    "-s",
    "6",
    "--min",
    "0",
    "--max",
    "63",
    "-a",
    "end-usage=q",
    "-a",
    "cq-level=28",
]

# Where a run's encoded rungs wait for the wrapper to upload them. Resolved
# against the repo, never the cwd --- the agent runs the site checks from
# website/, and a cwd-relative default is what put three ticks' assets in
# website/data/pending-uploads/ and threw the runs away.
#
# SLOPU_PENDING_DIR overrides it. A concurrent generator slot sets it to its own
# data/pending-uploads/<run-id>/, so two slots encoding at the same moment
# cannot see or clobber each other's rungs; unset, this is the serial
# pipeline's single staging root, unchanged.
DEFAULT_PENDING = (
    Path(os.environ["SLOPU_PENDING_DIR"]) / "img"
    if os.environ.get("SLOPU_PENDING_DIR")
    else REPO / "data" / "pending-uploads" / "img"
)

OUTPUTS_DIR = REPO / "website" / "src" / "content" / "outputs"
NEWS_DIR = REPO / "website" / "src" / "content" / "news"
HERO_ASSETS = REPO / "website" / "src" / "assets" / "heroes" / "outputs"
NEWS_HERO_ASSETS = REPO / "website" / "src" / "assets" / "heroes" / "news"
THUMB_ASSETS = REPO / "website" / "src" / "assets" / "outputs" / "thumbs"


def rungs(widths: list[int], source_width: int) -> list[int]:
    r = [w for w in widths if w <= source_width]
    return r or [source_width]


def og_dims(width: int, height: int) -> tuple[int, int]:
    w = min(OG_MAX_WIDTH, width)
    # round half-up, mirrored in images.ts ogImage()
    h = int(height * w / width + 0.5)
    return w, h


def encode_avif(img: Image.Image, width: int, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    h = int(img.height * width / img.width + 0.5)
    resized = img if width == img.width else img.resize((width, h), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(suffix=".png", delete_on_close=False) as tmp:
        tmp.close()
        resized.save(tmp.name, "PNG")
        subprocess.run(
            ["avifenc", *AVIFENC_ARGS, tmp.name, str(dest)],
            check=True,
            capture_output=True,
        )


def encode_og_jpeg(img: Image.Image, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    w, h = og_dims(img.width, img.height)
    resized = img if w == img.width else img.resize((w, h), Image.LANCZOS)
    resized.convert("RGB").save(dest, "JPEG", quality=OG_JPEG_QUALITY, progressive=True)


def dims_snippet(kind: str, width: int, height: int) -> str:
    key = "thumb" if kind == "thumb" else "hero"
    return f"{key}:\n  width: {width}\n  height: {height}"


def encode_one(
    kind: str, source: Path, entry_id: str, pending: Path, quiet: bool = False
) -> tuple[int, int]:
    """Encode one image's ladder (+og for heroes). Returns source dims."""
    img = Image.open(source)
    if kind == "thumb":
        widths, subdir, og_subdir = THUMB_WIDTHS, "thumbs", None
    elif kind == "hero":
        widths, subdir, og_subdir = HERO_WIDTHS, "heroes/outputs", "og/outputs"
    elif kind == "news-hero":
        widths, subdir, og_subdir = HERO_WIDTHS, "heroes/news", "og/news"
    else:
        sys.exit(f"unknown kind: {kind}")

    for w in rungs(widths, img.width):
        encode_avif(img, w, pending / subdir / f"{entry_id}-{w}.avif")
    if og_subdir:
        encode_og_jpeg(img, pending / og_subdir / f"{entry_id}.jpg")
    if not quiet:
        print(
            f"{entry_id}: {kind} {img.width}x{img.height} → rungs {rungs(widths, img.width)}"
        )
        print(dims_snippet(kind, img.width, img.height))
    return img.width, img.height


def frontmatter_has_key(text: str, key: str) -> bool:
    return re.search(rf"^{key}:", text, re.MULTILINE) is not None


def backfill(write_frontmatter: bool, pending: Path) -> None:
    problems: list[str] = []

    output_ids = {p.stem for p in OUTPUTS_DIR.glob("*.yml")}
    hero_ids = {p.stem for p in HERO_ASSETS.glob("*.avif")}
    thumb_ids = {p.stem for p in THUMB_ASSETS.glob("*.avif")}

    # Orphans in both directions, before anything is encoded or deleted.
    for label, assets in (("hero", hero_ids), ("thumb", thumb_ids)):
        for stray in sorted(assets - output_ids):
            problems.append(f"{label} asset without an outputs entry: {stray}.avif")
    for missing in sorted(output_ids - hero_ids):
        problems.append(f"outputs entry without a hero asset: {missing}")
    for missing in sorted(output_ids - thumb_ids):
        problems.append(f"outputs entry without a thumb asset: {missing}")

    if problems:
        print("orphan report (resolve before deleting the asset dirs):")
        for p in problems:
            print(f"  - {p}")

    # Collect every encode job, fan out over a process pool (avifenc already
    # uses -j 4 internally, so cap workers well below the core count), then do
    # all frontmatter writes serially in the parent.
    jobs: list[tuple[str, Path, str]] = []
    for yml in sorted(OUTPUTS_DIR.glob("*.yml")):
        entry_id = yml.stem
        if (HERO_ASSETS / f"{entry_id}.avif").is_file():
            jobs.append(("hero", HERO_ASSETS / f"{entry_id}.avif", entry_id))
        if (THUMB_ASSETS / f"{entry_id}.avif").is_file():
            jobs.append(("thumb", THUMB_ASSETS / f"{entry_id}.avif", entry_id))

    news_ids: list[str] = []
    for md in sorted(NEWS_DIR.glob("*.md")):
        entry_id = md.stem
        text = md.read_text()
        m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if not m:
            problems.append(f"news post without frontmatter: {md.name}")
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        if fm.get("output"):
            continue  # announcement posts inherit the output's hero
        hero_src = NEWS_HERO_ASSETS / f"{entry_id}.avif"
        if not hero_src.is_file():
            problems.append(f"own-hero news post without a hero asset: {md.name}")
            continue
        jobs.append(("news-hero", hero_src, entry_id))
        news_ids.append(entry_id)

    dims: dict[tuple[str, str], tuple[int, int]] = {}
    with ProcessPoolExecutor(max_workers=8) as pool:
        futures = {
            pool.submit(encode_one, kind, src, entry_id, pending, True): (
                kind,
                entry_id,
            )
            for kind, src, entry_id in jobs
        }
        for i, fut in enumerate(as_completed(futures), 1):
            kind, entry_id = futures[fut]
            dims[(kind, entry_id)] = fut.result()
            if i % 100 == 0:
                print(f"[{i}/{len(jobs)}] encodes done")

    total = 0
    for yml in sorted(OUTPUTS_DIR.glob("*.yml")):
        entry_id = yml.stem
        text = yml.read_text()
        additions = []
        for kind, key in (("hero", "hero"), ("thumb", "thumb")):
            if (kind, entry_id) in dims and not frontmatter_has_key(text, key):
                w, h = dims[(kind, entry_id)]
                additions.append(f"{key}:\n  width: {w}\n  height: {h}\n")
        if write_frontmatter and additions:
            yml.write_text(text.rstrip("\n") + "\n" + "".join(additions))
        total += 1

    news_count = 0
    for entry_id in news_ids:
        md = NEWS_DIR / f"{entry_id}.md"
        text = md.read_text()
        m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        assert m is not None  # already validated above
        fm = yaml.safe_load(m.group(1)) or {}
        w, h = dims[("news-hero", entry_id)]
        if write_frontmatter and "hero" not in fm:
            fm_text = m.group(1) + f"\nhero:\n  width: {w}\n  height: {h}"
            md.write_text(f"---\n{fm_text}\n---\n" + text[m.end() :])
        news_count += 1

    staged = sum(1 for p in pending.rglob("*") if p.is_file())
    print(
        f"\nencoded {total} outputs + {news_count} own-hero news posts → {staged} files under {pending}"
    )
    if problems:
        print(f"{len(problems)} problem(s) — see orphan report above")
        sys.exit(1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    enc = sub.add_parser("encode", help="encode one image for a publish tick")
    enc.add_argument("kind", choices=["hero", "news-hero", "thumb"])
    enc.add_argument("--source", required=True, type=Path)
    enc.add_argument("--id", required=True, dest="entry_id")
    enc.add_argument("--pending-dir", type=Path, default=DEFAULT_PENDING)

    bf = sub.add_parser("backfill", help="encode every existing entry's images")
    bf.add_argument("--write-frontmatter", action="store_true")
    bf.add_argument("--pending-dir", type=Path, default=DEFAULT_PENDING)

    args = ap.parse_args()
    if args.cmd == "encode":
        if not args.source.is_file():
            sys.exit(f"source not found: {args.source}")
        encode_one(args.kind, args.source, args.entry_id, args.pending_dir)
    else:
        backfill(args.write_frontmatter, args.pending_dir)


if __name__ == "__main__":
    main()
