#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["boto3>=1.35"]
# ///
"""Manage the Tigris buckets that serve slop.university's output PDFs and images.

Two buckets, two policies, selected with `--target` (default `pdf`):

- **pdf** (`pdf.slop.university`, env `SLOPU_S3_BUCKET`): output PDFs, keyed by
  bare basename. The PDFs used to live in `website/public/outputs/pdf/` and
  ship inside the GitHub Pages artifact; they were the largest and
  fastest-growing category there and, being committed, they grew `.git`
  permanently too. Two properties of this bucket are load-bearing and applied
  by `setup`:

  - **robots.txt with `Disallow: /`.** This is what keeps fabricated documents
    citing real literature out of Google Scholar (the rationale is published on
    /colophon/). S3 has no way to attach an `X-Robots-Tag` header, and the
    site's own robots.txt does not reach this origin.
  - **CORS.** The signage kiosk (`/signage/<orientation>/`) fetches PDFs
    client-side with pdf.js, a cross-origin read.

- **img** (`img.slop.university`, env `SLOPU_IMG_BUCKET`): per-publish images
  (hero/thumb AVIF ladders + og JPEGs), keyed by their path relative to the
  staging root (`heroes/outputs/<id>-<w>.avif`, `thumbs/<id>-<w>.avif`,
  `og/outputs/<id>.jpg`, ...). Deliberately a SEPARATE bucket from the PDFs:
  these images serve as og:image cards, and Twitterbot respects robots.txt for
  card images, so they must not sit behind the PDF origin's `Disallow: /`.
  `setup --target img` uploads an explicitly permissive robots.txt (so `verify`
  has something to assert) and applies no CORS — every consumer is a plain
  `<img>` or a link-preview scraper, and neither preflights.

Credentials come from the untracked `[env]` block in
`~/.config/mise/config.local.toml`, which the cron wrapper's `mise activate`
already exports --- the same channel as REPLICATE_API_TOKEN and SLOPU_TOKEN.
They are deliberately not named AWS_* so they cannot hijack unrelated S3
clients. Both buckets share the endpoint and key pair; only the bucket name
env var differs per target.

The credential the publish tick carries is scoped to upload-only on these two
buckets (see `upload_policy`). `setup` and `create-upload-key` need the admin
key instead --- they are rare, deliberate operations, so supply it inline for
the one run rather than leaving it in the env.

Usage:
  ops/bucket-sync.py upload FILE...                 # upload PDFs, keyed by basename
  ops/bucket-sync.py upload --target img ROOT_DIR   # upload a staged image tree
  ops/bucket-sync.py verify [ID]                    # check the served PDF origin
  ops/bucket-sync.py verify --target img [KEY]      # check the served image origin
  ops/bucket-sync.py setup [--target img]           # create/configure bucket (admin key)
  ops/bucket-sync.py create-upload-key [NAME]       # mint the scoped key (admin key)
"""

import os
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import boto3

# Every origin that reads a PDF cross-origin: the live site (output landing
# pages and the signage route) and a local `astro dev` while working on them.
ALLOWED_ORIGINS = [
    "https://slop.university",
    "http://localhost:4321",
]

PDF_ROBOTS_TXT = """\
# Slop University output PDFs. Disallowed wholesale so that fabricated documents
# citing real literature can never feed citation databases (Google Scholar
# respects this). This mirrors the Disallow on slop.university/robots.txt, which
# does not reach this origin. The rationale is published on
# https://slop.university/colophon/.
User-agent: *
Disallow: /
"""

IMG_ROBOTS_TXT = """\
# Slop University images (heroes, thumbnails, og cards). Explicitly permissive:
# og:image fetchers (Twitterbot respects robots.txt for card images) and image
# indexing are wanted here, unlike the PDF origin's Disallow. Kept as a file so
# `verify --target img` can assert the policy rather than infer it from a 404.
User-agent: *
Disallow:
"""


@dataclass(frozen=True)
class Target:
    bucket_env: str
    public_base: str
    # suffix -> content type; anything else is refused at upload
    content_types: dict[str, str]
    # flat: keys are bare basenames (PDFs); tree: keys are paths relative to
    # the staged root directory (images)
    flat_keys: bool
    cors: bool
    robots_txt: str


TARGETS = {
    "pdf": Target(
        bucket_env="SLOPU_S3_BUCKET",
        public_base="https://pdf.slop.university",
        content_types={".pdf": "application/pdf"},
        flat_keys=True,
        cors=True,
        robots_txt=PDF_ROBOTS_TXT,
    ),
    "img": Target(
        bucket_env="SLOPU_IMG_BUCKET",
        public_base="https://img.slop.university",
        content_types={".avif": "image/avif", ".jpg": "image/jpeg"},
        flat_keys=False,
        cors=False,
        robots_txt=IMG_ROBOTS_TXT,
    ),
}


IAM_ENDPOINT = "https://fly.iam.storage.tigris.dev"

# The credential the unattended publish tick carries. It can add an object to
# these buckets and do nothing else: no delete, no listing, no read, no reach
# into any other bucket. That matters because the tick's key lives in the mise
# [env] block, which every service on the host can read --- so the useful
# question is not "can it leak" but "what can the holder of a leaked copy do".
# The answer is: upload a PDF or an image to buckets of fabricated documents.
# It cannot destroy the archive, enumerate it, or pivot.
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


def upload_policy(buckets: list[str]) -> dict:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublishTickUploadOnly",
                "Effect": "Allow",
                "Action": UPLOAD_POLICY_ACTIONS,
                "Resource": [f"arn:aws:s3:::{b}/*" for b in buckets],
            }
        ],
    }


# v1 ("slopu-publish-upload-only") covered the PDF bucket alone; superseded when
# images moved to their own bucket. Mint a NEW key against the new policy and
# delete the old key --- never mutate the live key in place while the hourly
# tick depends on it.
POLICY_NAME = "slopu-publish-upload-only-v2"


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

    buckets = [
        os.environ[TARGETS["pdf"].bucket_env],
        os.environ[TARGETS["img"].bucket_env],
    ]
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
            PolicyDocument=json.dumps(upload_policy(buckets)),
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

    print(f"\nscoped key '{name}': {UPLOAD_POLICY_ACTIONS} on {buckets} only\n")
    print(f'SLOPU_S3_ACCESS_KEY_ID = "{key["AccessKeyId"]}"')
    print(f'SLOPU_S3_SECRET_ACCESS_KEY = "{key["SecretAccessKey"]}"')


def client(target: Target):
    """S3 client for the target bucket, or exit with a usable message."""
    missing = [
        k
        for k in (
            target.bucket_env,
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


def setup(target: Target) -> None:
    s3 = client(target)
    bucket = os.environ[target.bucket_env]

    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:
        s3.create_bucket(Bucket=bucket)
        print(f"created bucket {bucket}")

    if target.cors:
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
    else:
        print("CORS skipped: plain <img> and og scrapers never preflight")

    s3.put_object(
        Bucket=bucket,
        Key="robots.txt",
        Body=target.robots_txt.encode(),
        ContentType="text/plain; charset=utf-8",
        CacheControl="public, max-age=3600",
    )
    print(f"robots.txt uploaded ({len(target.robots_txt)} bytes)")


def collect_tree(root: Path, target: Target) -> list[tuple[Path, str]]:
    """(file, key) pairs for a staged directory: key = path relative to root."""
    pairs = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix not in target.content_types:
            sys.exit(
                f"refusing to upload {p}: suffix not in {list(target.content_types)}"
            )
        pairs.append((p, p.relative_to(root).as_posix()))
    return pairs


def upload(target: Target, args: list[str]) -> None:
    s3 = client(target)
    bucket = os.environ[target.bucket_env]

    if target.flat_keys:
        paths = [Path(a) for a in args]
        for p in paths:
            if not p.is_file():
                sys.exit(f"not a file: {p}")
            if p.suffix not in target.content_types:
                sys.exit(f"refusing to upload a non-PDF: {p}")
        pairs = [(p, p.name) for p in paths]
    else:
        if len(args) != 1 or not Path(args[0]).is_dir():
            sys.exit("upload --target img takes exactly one staged directory")
        pairs = collect_tree(Path(args[0]), target)
        if not pairs:
            sys.exit(f"nothing to upload under {args[0]}")

    def put(pair: tuple[Path, str]) -> str:
        p, key = pair
        s3.upload_file(
            str(p),
            bucket,
            key,
            ExtraArgs={
                "ContentType": target.content_types[p.suffix],
                # Content-addressed by seed: a given key's bytes never change,
                # so this can be cached hard.
                "CacheControl": "public, max-age=31536000, immutable",
            },
        )
        return key

    # Uploads are latency-bound, not CPU-bound.
    with ThreadPoolExecutor(max_workers=8) as pool:
        for i, key in enumerate(pool.map(put, pairs), 1):
            print(f"[{i}/{len(pairs)}] {key}")


def verify(target: Target, sample: str | None) -> None:
    """Check the live origin the way a browser and a crawler each would."""
    ok = True

    def fetch(url: str, headers: dict[str, str] | None = None):
        req = urllib.request.Request(url, headers=headers or {})
        return urllib.request.urlopen(req, timeout=30)

    disallowed = "Disallow: /" in target.robots_txt
    try:
        r = fetch(f"{target.public_base}/robots.txt")
        body = r.read().decode()
        if ("Disallow: /" in body) == disallowed:
            policy = "Disallow: /" if disallowed else "permissive"
            print(f"robots.txt: OK ({target.public_base}/robots.txt is {policy})")
        else:
            print(f"robots.txt: WRONG BODY\n{body}")
            ok = False
    except urllib.error.URLError as e:
        print(f"robots.txt: FAILED --- {e}")
        ok = False

    if sample:
        if target.flat_keys:
            key = f"{sample}.pdf"
        else:
            key = sample  # full key, e.g. heroes/outputs/<id>-800.avif
        url = f"{target.public_base}/{key}"
        expected_type = target.content_types[Path(key).suffix]
        try:
            r = fetch(url, {"Origin": ALLOWED_ORIGINS[0]})
            acao = r.headers.get("Access-Control-Allow-Origin")
            ctype = r.headers.get("Content-Type")
            cache = r.headers.get("Cache-Control") or ""
            print(f"{key}: HTTP {r.status}, Content-Type: {ctype}, ACAO: {acao}")
            if target.cors and acao not in (ALLOWED_ORIGINS[0], "*"):
                print(
                    "  CORS: FAILED --- the signage kiosk will fall back to thumbnails"
                )
                ok = False
            if ctype != expected_type:
                print(f"  Content-Type: FAILED (wanted {expected_type})")
                ok = False
            if "immutable" not in cache:
                print(f"  Cache-Control: FAILED (wanted immutable, got {cache!r})")
                ok = False
        except urllib.error.URLError as e:
            print(f"{key}: FAILED --- {e}")
            ok = False

    sys.exit(0 if ok else 1)


def main() -> None:
    argv = sys.argv[1:]
    target_name = "pdf"
    if "--target" in argv:
        i = argv.index("--target")
        try:
            target_name = argv[i + 1]
        except IndexError:
            sys.exit("--target needs a value: pdf or img")
        argv = argv[:i] + argv[i + 2 :]
    if target_name not in TARGETS:
        sys.exit(f"unknown target: {target_name} (expected pdf or img)")
    target = TARGETS[target_name]

    if not argv:
        sys.exit(__doc__)
    cmd, rest = argv[0], argv[1:]
    if cmd == "setup":
        setup(target)
    elif cmd == "upload":
        if not rest:
            sys.exit("upload needs at least one file (pdf) or a directory (img)")
        upload(target, rest)
    elif cmd == "verify":
        verify(target, rest[0] if rest else None)
    elif cmd == "create-upload-key":
        create_upload_key(rest[0] if rest else "slopu-publish-upload")
    else:
        sys.exit(f"unknown command: {cmd}\n{__doc__}")


if __name__ == "__main__":
    main()
