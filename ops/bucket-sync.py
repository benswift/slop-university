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

The credential the publish tick carries is scoped to upload-only on this one
bucket (see `upload_policy`). `setup` and `create-upload-key` need the admin key
instead --- they are rare, deliberate operations, so supply it inline for the one
run rather than leaving it in the env.

Usage:
  ops/bucket-sync.py upload FILE...     # upload PDFs, keyed by basename
  ops/bucket-sync.py verify [ID]        # check the served object, live
  ops/bucket-sync.py setup              # apply CORS + robots.txt (admin key)
  ops/bucket-sync.py create-upload-key [NAME]   # mint the scoped key (admin key)
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


IAM_ENDPOINT = "https://fly.iam.storage.tigris.dev"

# The credential the unattended publish tick carries. It can add an object to
# this one bucket and do nothing else: no delete, no listing, no read, no reach
# into any other bucket. That matters because the tick's key lives in the mise
# [env] block, which every service on the host can read --- so the useful
# question is not "can it leak" but "what can the holder of a leaked copy do".
# The answer is: upload a PDF to a bucket of fabricated PDFs. It cannot destroy
# the archive, enumerate it, or pivot.
#
# The multipart actions are here because boto3's upload_file silently switches
# to multipart above 8 MB; a PutObject-only key would work for years and then
# fail on the first oversized poster. GetObject is absent on purpose --- the
# objects are public, so reads never need a credential.
UPLOAD_POLICY_ACTIONS = [
    "s3:PutObject",
    "s3:AbortMultipartUpload",
    "s3:ListMultipartUploadParts",
]


def upload_policy(bucket: str) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublishTickUploadOnly",
                "Effect": "Allow",
                "Action": UPLOAD_POLICY_ACTIONS,
                "Resource": f"arn:aws:s3:::{bucket}/*",
            }
        ],
    }


POLICY_NAME = "slopu-publish-upload-only"


def create_upload_key(name: str) -> None:
    """Mint the scoped upload credential. Run with an admin key in the env.

    Tigris implements a useful subset of the IAM API, and the shape matters:
    PutUserPolicy (inline policies) returns NotImplemented, so the policy has to
    be a MANAGED one --- CreatePolicy, then AttachUserPolicy by ARN. CreatePolicy
    also validates the resource ARN against real buckets, which is a good sign it
    is genuinely enforced rather than stored and ignored.

    Order matters for a different reason: attach the policy BEFORE handing the
    key out, and never create the key until the policy exists. Creating first
    leaves a live unscoped credential if the second call fails --- which is
    exactly what happened on the first attempt here, stranding a key whose
    secret was lost with the traceback.
    """
    import json

    bucket = os.environ["SLOPU_S3_BUCKET"]
    iam = boto3.client(
        "iam",
        endpoint_url=IAM_ENDPOINT,
        aws_access_key_id=os.environ["SLOPU_S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["SLOPU_S3_SECRET_ACCESS_KEY"],
        region_name="auto",
    )

    arn = next(
        (
            p["Arn"]
            for p in iam.list_policies().get("Policies", [])
            if p["PolicyName"] == POLICY_NAME
        ),
        None,
    )
    if arn:
        print(f"reusing existing policy {arn}")
    else:
        arn = iam.create_policy(
            PolicyName=POLICY_NAME,
            PolicyDocument=json.dumps(upload_policy(bucket)),
        )["Policy"]["Arn"]
        print(f"created policy {arn}")

    key = iam.create_access_key(UserName=name)["AccessKey"]
    try:
        # In Tigris the access key IS the user, so every subsequent call
        # identifies it by AccessKeyId --- passing the human-readable name here
        # fails with "Access key doesn't exist".
        iam.attach_user_policy(UserName=key["AccessKeyId"], PolicyArn=arn)
    except Exception:
        # Never leave an unscoped credential alive on a partial failure.
        iam.delete_access_key(UserName=name, AccessKeyId=key["AccessKeyId"])
        print(f"attach failed; deleted the unscoped key {key['AccessKeyId']}")
        raise

    print(f"\nscoped key '{name}': {UPLOAD_POLICY_ACTIONS} on {bucket}/* only\n")
    print(f'SLOPU_S3_ACCESS_KEY_ID = "{key["AccessKeyId"]}"')
    print(f'SLOPU_S3_SECRET_ACCESS_KEY = "{key["SecretAccessKey"]}"')


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
    elif cmd == "create-upload-key":
        create_upload_key(rest[0] if rest else "slopu-publish-upload")
    else:
        sys.exit(f"unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
