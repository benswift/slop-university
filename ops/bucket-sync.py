#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["boto3>=1.35"]
# ///
"""Manage the Tigris bucket that serves slop.university's output PDFs.

The PDFs used to live in `website/public/outputs/pdf/` and ship inside the
GitHub Pages artifact. They were the largest and fastest-growing category there
(203 MB of a 533 MB artifact against Pages' hard 1 GB limit, ~0.6 MB per publish
tick) and, being committed, they grew `.git` permanently too. They now live in a
public Tigris bucket fronted by `pdf.slop.university`.

Two properties of that bucket are load-bearing and are applied by `setup`:

- **robots.txt.** `website/public/robots.txt` disallows `/outputs/pdf/`, which
  is what keeps fabricated documents citing real literature out of Google
  Scholar (the rationale is published on /colophon/). A bucket on another origin
  is not covered by the site's robots.txt, and S3 has no way to attach an
  `X-Robots-Tag` response header to an object. The custom domain gives the
  bucket its own origin, so a `Disallow: /` robots.txt at its root is the exact
  same mechanism the site relies on today.
- **CORS.** The signage kiosk (`/signage/<orientation>/`) fetches PDFs
  client-side with pdf.js, a cross-origin read now that the bytes are elsewhere.
  Without an allowed origin the kiosk silently falls back to thumbnails.

Credentials come from the untracked `[env]` block in
`~/.config/mise/config.local.toml`, which the cron wrapper's `mise activate`
already exports --- the same channel as REPLICATE_API_TOKEN and SLOPU_TOKEN.
They are deliberately not named AWS_* so they cannot hijack unrelated S3 clients.

Usage:
  ops/bucket-sync.py setup              # apply CORS + robots.txt (idempotent)
  ops/bucket-sync.py upload FILE...     # upload PDFs, keyed by basename
  ops/bucket-sync.py verify [ID]        # check the served object, live
"""

import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import boto3

PUBLIC_BASE = "https://pdf.slop.university"

# Every origin that reads a PDF cross-origin: the live site (output landing
# pages and the signage route) and a local `astro dev` while working on them.
ALLOWED_ORIGINS = [
    "https://slop.university",
    "http://localhost:4321",
]

ROBOTS_TXT = """\
# Slop University output PDFs. Disallowed wholesale so that fabricated documents
# citing real literature can never feed citation databases (Google Scholar
# respects this). This mirrors the Disallow on slop.university/robots.txt, which
# does not reach this origin. The rationale is published on
# https://slop.university/colophon/.
User-agent: *
Disallow: /
"""


def client():
    """S3 client for the bucket, or exit with a usable message."""
    missing = [
        k
        for k in (
            "SLOPU_S3_BUCKET",
            "SLOPU_S3_ENDPOINT",
            "SLOPU_S3_ACCESS_KEY_ID",
            "SLOPU_S3_SECRET_ACCESS_KEY",
        )
        if not os.environ.get(k)
    ]
    if missing:
        sys.exit(
            f"missing bucket credentials in env: {', '.join(missing)}\n"
            "they live in the [env] block of ~/.config/mise/config.local.toml; "
            "run this under `mise exec` or an activated shell"
        )
    return boto3.client(
        "s3",
        endpoint_url=os.environ["SLOPU_S3_ENDPOINT"],
        aws_access_key_id=os.environ["SLOPU_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["SLOPU_S3_SECRET_ACCESS_KEY"],
        region_name="auto",
    )


def setup() -> None:
    s3 = client()
    bucket = os.environ["SLOPU_S3_BUCKET"]

    s3.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration={
            "CORSRules": [
                {
                    "AllowedOrigins": ALLOWED_ORIGINS,
                    # pdf.js issues ranged GETs, and HEAD to size the document.
                    "AllowedMethods": ["GET", "HEAD"],
                    "AllowedHeaders": ["*"],
                    "ExposeHeaders": [
                        "Content-Length",
                        "Content-Range",
                        "Accept-Ranges",
                    ],
                    "MaxAgeSeconds": 3600,
                }
            ]
        },
    )
    print(f"CORS applied: {', '.join(ALLOWED_ORIGINS)}")

    s3.put_object(
        Bucket=bucket,
        Key="robots.txt",
        Body=ROBOTS_TXT.encode(),
        ContentType="text/plain; charset=utf-8",
        CacheControl="public, max-age=3600",
    )
    print(f"robots.txt uploaded ({len(ROBOTS_TXT)} bytes)")


def upload(paths: list[Path]) -> None:
    s3 = client()
    bucket = os.environ["SLOPU_S3_BUCKET"]

    for p in paths:
        if not p.is_file():
            sys.exit(f"not a file: {p}")
        if p.suffix != ".pdf":
            sys.exit(f"refusing to upload a non-PDF: {p}")

    def put(p: Path) -> str:
        s3.upload_file(
            str(p),
            bucket,
            p.name,
            ExtraArgs={
                "ContentType": "application/pdf",
                # Content-addressed by seed: a given key's bytes never change,
                # so this can be cached hard.
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )
        return p.name

    # Uploads are latency-bound, not CPU-bound; the backfill is 565 files.
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, key in enumerate(pool.map(put, paths), 1):
            print(f"[{i}/{len(paths)}] {key}")


def verify(sample: str | None) -> None:
    """Check the live origin the way a browser and a crawler each would."""
    ok = True

    def fetch(url: str, headers: dict[str, str] | None = None):
        req = urllib.request.Request(url, headers=headers or {})
        return urllib.request.urlopen(req, timeout=30)

    try:
        r = fetch(f"{PUBLIC_BASE}/robots.txt")
        body = r.read().decode()
        if "Disallow: /" in body:
            print(f"robots.txt: OK ({PUBLIC_BASE}/robots.txt serves Disallow: /)")
        else:
            print(f"robots.txt: WRONG BODY\n{body}")
            ok = False
    except urllib.error.URLError as e:
        print(f"robots.txt: FAILED --- {e}")
        ok = False

    if sample:
        url = f"{PUBLIC_BASE}/{sample}.pdf"
        try:
            r = fetch(url, {"Origin": ALLOWED_ORIGINS[0]})
            acao = r.headers.get("Access-Control-Allow-Origin")
            ctype = r.headers.get("Content-Type")
            print(f"{sample}.pdf: HTTP {r.status}, Content-Type: {ctype}, ACAO: {acao}")
            if acao not in (ALLOWED_ORIGINS[0], "*"):
                print(
                    "  CORS: FAILED --- the signage kiosk will fall back to thumbnails"
                )
                ok = False
            if ctype != "application/pdf":
                print("  Content-Type: FAILED")
                ok = False
        except urllib.error.URLError as e:
            print(f"{sample}.pdf: FAILED --- {e}")
            ok = False

    sys.exit(0 if ok else 1)


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "setup":
        setup()
    elif cmd == "upload":
        if not rest:
            sys.exit("upload needs at least one file")
        upload([Path(p) for p in rest])
    elif cmd == "verify":
        verify(rest[0] if rest else None)
    else:
        sys.exit(f"unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
