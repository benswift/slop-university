#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx", "pyyaml", "typer"]
# ///
"""Scaffold, fill and stage a templated video: one whose picture is the beat
engine (_kit/beats.js) driven by its spec.json, so a run writes a script and a
spec and no animation code. skills/video/SKILL.md is the method.

    templated.py new <slug> --kind explainer|promo --title "..."
    templated.py fetch <slug>     # assets/ from the spec's image references
    templated.py stage <slug>     # encodes -> data/pending-uploads/, the site's video entry

`new` writes <slug>/ (both cuts' HTML, the HyperFrames files, the kit link and
a spec skeleton) and scripts/<slug>.md. `fetch` resolves every image reference
in the spec the way beats.js does (an output's hero and first page from the
image bucket, a PDF page rendered from the PDF bucket, a person's hero and
headshot from canon/) and writes assets/people.json, the name, title and school
of everyone the spec shows. `stage` copies the signage and web encodes
(`video.py signage` and `web`) into data/pending-uploads/video-<slug>/ and
writes website/src/content/videos/<slug>.yml, which `bin/slopu land-video`
commits, uploads and pushes.
"""

import json
import shutil
import subprocess
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


@app.command()
def new(
    slug: str,
    kind: Annotated[str, typer.Option(help="explainer or promo")],
    title: Annotated[str, typer.Option(help="the video's title")],
) -> None:
    """Scaffold <slug>/ and scripts/<slug>.md."""
    if kind not in ("explainer", "promo"):
        raise SystemExit("--kind is explainer or promo")
    proj = project(slug)
    if proj.exists():
        raise SystemExit(f"{proj} exists")
    (proj / "compositions").mkdir(parents=True)
    (proj / "kit").symlink_to("../_kit")
    for name in ("index.html", "compositions/portrait.html"):
        html = (
            (TEMPLATE / name)
            .read_text()
            .replace("{{slug}}", slug)
            .replace("{{title}}", title)
        )
        (proj / name).write_text(html)
    for name in ("package.json", "hyperframes.json"):
        (proj / name).write_text(
            (TEMPLATE / name).read_text().replace("{{slug}}", slug)
        )
    spec = {"kind": kind, "title": title, "beats": []}
    (proj / "spec.json").write_text(json.dumps(spec, indent=2) + "\n")
    script = VIDEO / "scripts" / f"{slug}.md"
    if not script.exists():
        script.write_text(f"# {title}\n\n## Key idea\n\n## Script\n")
    print(proj)


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
    print(f"{slug}: {len(refs(spec["beats"]))} images, {len(people)} people")


@app.command()
def stage(slug: str) -> None:
    """Stage the encodes for landing, and write the site's video entry."""
    proj = project(slug)
    spec = json.loads((proj / "spec.json").read_text())
    out = VIDEO / "out" / slug
    pending = ROOT / "data" / "pending-uploads" / f"video-{slug}"
    pending.mkdir(parents=True, exist_ok=True)

    def newest(pattern: str) -> Path:
        found = sorted(out.glob(pattern), key=lambda p: p.stat().st_mtime)
        if not found:
            raise SystemExit(
                f"no {pattern} in {out}: run video.py signage and web first"
            )
        shutil.copy(found[-1], pending)
        return found[-1]

    entry = {
        "title": spec["title"],
        **({"output": spec["output"]} if spec.get("output") else {}),
        **({"person": spec["person"]} if spec.get("person") else {}),
        "signage": {
            "landscape": newest(f"signage/{slug}-[0-9a-f]*.mp4").name,
            "portrait": newest(f"signage/{slug}-portrait-[0-9a-f]*.mp4").name,
        },
        "web": {
            cut: {
                "video": newest(f"web/{name}-web-*.mp4").name,
                "cover": newest(f"web/{name}-cover-*.jpg").name,
            }
            for cut, name in (("landscape", slug), ("portrait", f"{slug}-portrait"))
        },
    }
    dest = ROOT / "website" / "src" / "content" / "videos" / f"{slug}.yml"
    dest.write_text(
        yaml.safe_dump(entry, sort_keys=False, allow_unicode=True, width=100)
    )
    print(f"{dest}\n{pending}")


if __name__ == "__main__":
    app()
