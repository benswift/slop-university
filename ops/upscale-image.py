#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["replicate", "httpx", "typer"]
# ///
"""Double an image's pixel dimensions for large-format print.

The image generator caps its long edge at 4096 px. That is plenty for a booklet
cover or a signage panel, and about 90 dpi across an 850 mm pull-up banner ---
soft at arm's length. Nothing the generator offers gets past it (a different
aspect ratio moves the cap to the other edge; extending an image re-renders it
at the same cap), so the print presets enlarge after the fact.

Topaz's CGI model is the one used: on the two-ink house style it keeps the flat
shapes flat, sharpens their edges and re-renders the print grain at the new
scale, where a plain resample only blurs. It was compared against a Lanczos
enlargement at 100%; no other upscaler has been evaluated.

Needs `REPLICATE_API_TOKEN` (run under `mise exec --`).

Usage:
  ops/upscale-image.py output/<run>-images/hero.jpg
  ops/upscale-image.py hero.jpg --out hero-2x.jpg --factor 4x
"""

from pathlib import Path
from typing import Annotated

import httpx
import replicate
import typer

MODEL = "topazlabs/image-upscale"


def main(
    src: Annotated[Path, typer.Argument(help="Image to enlarge")],
    out: Annotated[
        Path | None,
        typer.Option(
            help="Where to write the result (default: replace SRC, keeping SRC as <name>-1x)"
        ),
    ] = None,
    factor: Annotated[str, typer.Option(help="2x, 4x or 6x")] = "2x",
) -> None:
    with src.open("rb") as image:
        output = replicate.run(
            MODEL,
            input={
                "image": image,
                "enhance_model": "CGI",
                "upscale_factor": factor,
                "output_format": "jpg",
            },
        )
    url = str(output[0] if isinstance(output, list) else output)
    data = httpx.get(url, timeout=600, follow_redirects=True).raise_for_status().content
    if out is None:
        src.rename(src.with_stem(f"{src.stem}-1x"))
        out = src
    out.write_bytes(data)
    print(out)


if __name__ == "__main__":
    typer.run(main)
