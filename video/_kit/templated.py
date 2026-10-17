#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "pyyaml", "typer"]
# ///
"""Scaffold, fill and stage a templated video: one whose picture is the beat
engine (_kit/beats.js) driven by its spec.json, so a run writes a script and a
spec and no animation code. skills/video/SKILL.md is the method.

    templated.py new --kind explainer|promo --title "..."   # prints the id
    templated.py fetch <id>     # assets/ from the spec's image references
    templated.py stage <id>     # the outputs entry, images and encodes, for landing

A video is a research output like any other: its id is
`slop-explainer-<slug>-<seed>` or `slop-promo-<slug>-<seed>` (the slug and seed
as skills/_shared/output-naming.md makes them), its DOI is 10.5555/slop.<seed>,
and video/<id>/ is its project. `new` writes video/<id>/ (both cuts' HTML, the
HyperFrames files, the kit link and a spec skeleton) and scripts/<id>.md.
`fetch` resolves every image reference in the spec's beats the way beats.js
does and writes assets/people.json. `stage`, once `video.py signage` and `web`
have run, writes the outputs entry from the spec (its title, subtitle, summary,
topic, authors and school) and the videos entry, encodes the hero, thumbnail
and og card from the landscape cut, and copies the encodes into
data/pending-uploads/<id>/, where `bin/slopu land <id>` finds them.
"""

import json
import re
import secrets
import shutil
import string
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Annotated

import httpx
import typer
import yaml

VIDEO = Path(__file__).resolve().parent.parent
ROOT = VIDEO.parent
OUTPUTS = ROOT / "website" / "src" / "content" / "outputs"
IMG = "https://img.slop.university"
PDF = "https://pdf.slop.university"
HERO_WIDTHS = [800, 1600, 2560]
THUMB_WIDTHS = [320, 640, 960]
TEMPLATE = VIDEO / "_kit" / "template"

app = typer.Typer(add_completion=False, no_args_is_help=True)


def project(slug: str) -> Path:
    return VIDEO / slug


def rung(widths: list[int], width: int) -> int:
    fit = [w for w in widths if w <= width]
    return fit[-1] if fit else width


def output(oid: str) -> dict:
    return yaml.safe_load((OUTPUTS / f"{oid}.yml").read_text())


def download(url: str, dest: Path) -> None:
    if dest.is_file():
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = httpx.get(url, timeout=120, follow_redirects=True)
    r.raise_for_status()
    dest.write_bytes(r.content)


def refs(x) -> list[dict]:
    """Every image reference in a spec's beats, as beats.js finds them: a
    `pages` beat's outputs are their first pages."""
    if isinstance(x, dict) and x.get("type") == "pages":
        return [{"thumb": oid} for oid in x["outputs"]]
    if isinstance(x, dict):
        if any(k in x for k in ("output", "person", "thumb", "headshot", "page")):
            return [x]
        return [r for v in x.values() for r in refs(v)]
    if isinstance(x, list):
        return [r for v in x for r in refs(v)]
    return []


def slugify(title: str) -> str:
    """The slug output-naming.md derives: the first three words, kebab-cased,
    the last dropped while over 30 characters."""
    words = title.split()[:3]
    while True:
        slug = re.sub(
            r"-+", "-", re.sub(r"[^a-z0-9]", "-", " ".join(words).lower())
        ).strip("-")
        if len(slug) <= 30 or len(words) == 1:
            return slug
        words = words[:-1]


@app.command()
def new(
    kind: Annotated[str, typer.Option(help="explainer or promo")],
    title: Annotated[str, typer.Option(help="the video's title")],
) -> None:
    """Scaffold video/<id>/ and scripts/<id>.md, and print the id."""
    if kind not in ("explainer", "promo"):
        raise SystemExit("--kind is explainer or promo")
    seed = "".join(
        secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6)
    )
    vid = f"slop-{kind}-{slugify(title)}-{seed}"
    proj = project(vid)
    (proj / "compositions").mkdir(parents=True)
    (proj / "kit").symlink_to("../_kit")
    for name in ("index.html", "compositions/portrait.html"):
        html = (
            (TEMPLATE / name)
            .read_text()
            .replace("{{slug}}", vid)
            .replace("{{title}}", title)
        )
        (proj / name).write_text(html)
    for name in ("package.json", "hyperframes.json"):
        (proj / name).write_text((TEMPLATE / name).read_text().replace("{{slug}}", vid))
    spec = {
        "kind": kind,
        "title": title,
        "subtitle": "",
        "summary": "",
        "topic": "",
        "authors": [],
        "school": "",
        "beats": [],
    }
    (proj / "spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    (VIDEO / "scripts" / f"{vid}.md").write_text(
        f"# {title}\n\n## Key idea\n\n## Script\n"
    )
    print(vid)


@app.command()
def fetch(slug: str) -> None:
    """Fill assets/ from the spec's image references, and assets/people.json."""
    proj = project(slug)
    spec = json.loads((proj / "spec.json").read_text())
    assets = proj / "assets"
    people: set[str] = set()
    for ref in refs(spec["beats"]):
        if "output" in ref:
            oid = ref["output"]
            width = rung(HERO_WIDTHS, output(oid)["hero"]["width"])
            download(
                f"{IMG}/heroes/outputs/{oid}-{width}.avif",
                assets / "heroes" / f"{oid}.avif",
            )
        elif "thumb" in ref:
            oid = ref["thumb"]
            width = rung(THUMB_WIDTHS, output(oid)["thumb"]["width"])
            download(
                f"{IMG}/thumbs/{oid}-{width}.avif", assets / "thumbs" / f"{oid}.avif"
            )
        elif "page" in ref:
            oid, n = ref["page"]
            pdf = assets / "pdf" / f"{oid}.pdf"
            download(f"{PDF}/{oid}.pdf", pdf)
            out = assets / "pages" / f"{oid}-p{n}"
            if not out.with_suffix(".png").is_file():
                out.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["pdftoppm", "-png", "-singlefile", "-f", str(n), "-l", str(n)]
                    + ["-scale-to", "3200", str(pdf), str(out)],
                    check=True,
                )
        elif "person" in ref:
            pid = ref["person"]
            (assets / "people").mkdir(parents=True, exist_ok=True)
            shutil.copy(
                ROOT / "canon" / "heroes" / "people" / f"{pid}.avif", assets / "people"
            )
            people.add(pid)
        elif "headshot" in ref:
            people.add(ref["headshot"])
    for beat in spec["beats"]:
        people.update(beat.get("people", []))
    roster = {
        p["id"]: p
        for p in yaml.safe_load((ROOT / "canon" / "roster.yml").read_text())[
            "researchers"
        ]
    }
    (assets / "headshots").mkdir(parents=True, exist_ok=True)
    for pid in people:
        shutil.copy(ROOT / "canon" / "headshots" / f"{pid}.jpg", assets / "headshots")
    who = {
        pid: {k: roster[pid][k] for k in ("name", "title", "school")}
        for pid in sorted(people)
    }
    (assets / "people.json").write_text(json.dumps(who, indent=1) + "\n")
    print(f"{slug}: {len(refs(spec['beats']))} images, {len(people)} people")


@app.command()
def stage(vid: str) -> None:
    """Write the outputs and videos entries, encode the images, and stage it all."""
    proj = project(vid)
    spec = json.loads((proj / "spec.json").read_text())
    for key in ("title", "summary", "topic"):
        if not spec.get(key):
            raise SystemExit(f"spec.json has no {key}")
    out = VIDEO / "out" / vid
    pending = ROOT / "data" / "pending-uploads" / vid
    pending.mkdir(parents=True, exist_ok=True)

    def newest(pattern: str) -> Path:
        found = sorted(out.glob(pattern), key=lambda p: p.stat().st_mtime)
        if not found:
            raise SystemExit(
                f"no {pattern} in {out}: run video.py signage and web first"
            )
        shutil.copy(found[-1], pending)
        return found[-1]

    signage = {
        "landscape": newest(f"signage/{vid}-[0-9a-f]*.mp4"),
        "portrait": newest(f"signage/{vid}-portrait-[0-9a-f]*.mp4"),
    }
    web = {
        cut: {
            "video": newest(f"web/{name}-web-*.mp4").name,
            "cover": newest(f"web/{name}-cover-*.jpg").name,
        }
        for cut, name in (("landscape", vid), ("portrait", f"{vid}-portrait"))
    }

    # the hero, thumbnail and og card: the landscape cut's cover frame, at 4K
    first = json.loads((proj / "timing.json").read_text())["lines"][0]["start"]
    frame = out / "cover-4k.png"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{max(0.0, first - 0.1)}"]
        + ["-i", str(signage["landscape"]), "-frames:v", "1", str(frame)],
        check=True,
    )
    for kind in ("hero", "thumb"):
        subprocess.run(
            [
                str(ROOT / "ops" / "encode-images.py"),
                "encode",
                kind,
                "--source",
                str(frame),
            ]
            + ["--id", vid, "--pending-dir", str(pending / "img")],
            check=True,
            capture_output=True,
        )
    w, h = (
        int(x)
        for x in subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v",
                "-show_entries",
                "stream=width,height",
            ]
            + ["-of", "csv=p=0", str(frame)],
            capture_output=True,
            text=True,
            check=True,
        )
        .stdout.strip()
        .split(",")
    )

    now = datetime.now().astimezone()
    entry = {
        "title": spec["title"],
        **({"subtitle": spec["subtitle"]} if spec.get("subtitle") else {}),
        "authors": spec.get("authors", []),
        "preset": f"video-{spec['kind']}",
        **({"school": spec["school"]} if spec.get("school") else {}),
        "date": now.date(),
        "publishedAt": now.isoformat(timespec="seconds"),
        "doi": f"10.5555/slop.{vid.rsplit('-', 1)[-1]}",
        "summary": spec["summary"],
        "topic": spec["topic"],
        "version": "1.0",
        "hero": {"width": w, "height": h},
        "thumb": {"width": w, "height": h},
    }
    outputs = ROOT / "website" / "src" / "content" / "outputs" / f"{vid}.yml"
    outputs.write_text(
        yaml.safe_dump(entry, sort_keys=False, allow_unicode=True, width=80)
    )
    videos = {
        "title": spec["title"],
        **({"output": spec["output"]} if spec.get("output") else {}),
        **({"person": spec["person"]} if spec.get("person") else {}),
        "signage": {cut: f.name for cut, f in signage.items()},
        "web": web,
    }
    dest = ROOT / "website" / "src" / "content" / "videos" / f"{vid}.yml"
    dest.write_text(
        yaml.safe_dump(videos, sort_keys=False, allow_unicode=True, width=100)
    )
    print(f"{outputs}\n{dest}\n{pending}")


if __name__ == "__main__":
    app()
