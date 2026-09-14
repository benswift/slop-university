#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""Publish the staged LinkedIn post (data/pending-linkedin-post.json).

Posts go out as the Slop University Page, not as a person, and LinkedIn only
grants Page posting (`w_organization_social`) to registered legal entities ---
which a fictional university cannot become. So this script never talks to
LinkedIn. It POSTs the post to a Make webhook, and a Make scenario ("Custom
webhook" -> "LinkedIn: Create a company text post", Content mapped to `text`)
publishes it through Make's own approved LinkedIn app, authorised by the Page
admin. Make is only a sink here: swapping vendors is a URL and a header.

The trust split is the same as ops/post-to-bluesky.py's: the /publish agent
composes the staged file, and the cron wrapper runs this script after its
validated push. The wrapper strips both credentials from the agent's
environment (run_agent in ops/publish-lib.sh).

Credentials, from the untracked mise [env] block:
  SLOPU_LINKEDIN_WEBHOOK       the Make catch-hook URL
  SLOPU_LINKEDIN_WEBHOOK_KEY   the hook's API key, sent as x-make-apikey
The URL is never printed: an httpx error message would carry it into the
publish log, which is why the hook also demands the key.

pending-linkedin-post.json schema:
  {
    "text":    "the post body, LinkedIn register, <=3000 chars",  (required)
    "link":    "https://slop.university/outputs/<id>",            (optional)
    "subject": "outputs/<id>"                                     (optional)
  }

If `link` is present and not already in `text`, it is appended on its own
line: the Make module maps only `text`, so the text must carry the URL.

Make answers "Accepted" as soon as it queues the run, before LinkedIn has seen
anything, and it offers no way to read the Page back. So dedup and the
socials gate both read a local ledger, data/linkedin-ledger.jsonl, one line per
delivery. A LinkedIn-side failure after Make accepts shows up in the scenario's
history, not here.

Exit 0 on a delivered (or deduped) post; the wrapper deletes the staged file
only then. Exit 65 (EX_DATAERR) when the file itself can never be accepted ---
malformed JSON, no text, over the cap --- and the wrapper quarantines it. A
definite failure (no connection, or a non-2xx from Make: a bad key is 401, a
scenario switched off is 410) exits 1 and leaves the file staged for the next
run to retry. A failure that may have delivered anyway (the
request went out and the response was lost) is recorded as `uncertain` and
exits non-zero; the retry then finds it in the ledger and stands down, because
a missing post is cheaper than a doubled one.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import NoReturn

import httpx

TIMEOUT = 30.0
DEDUP_WINDOW = dt.timedelta(hours=24)
MAX_CHARS = 3000  # LinkedIn's post commentary cap
LEDGER_NAME = "linkedin-ledger.jsonl"
EXIT_REJECTED = 65  # EX_DATAERR: the staged file is unpostable, so don't retry it


def fail(msg: str) -> NoReturn:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def reject(msg: str) -> NoReturn:
    print(f"rejected: {msg}", file=sys.stderr)
    raise SystemExit(EXIT_REJECTED)


def compose_text(post: dict) -> str:
    text = (post.get("text") or "").strip()
    link = post.get("link")
    if link and link not in text:
        text = f"{text}\n\n{link}"
    return text


def digest(text: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", text).encode()).hexdigest()


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def append_ledger(path: Path, entry: dict) -> None:
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def recent_duplicate(ledger: list[dict], sha: str, now: dt.datetime) -> dict | None:
    for entry in reversed(ledger):
        if now - dt.datetime.fromisoformat(entry["at"]) > DEDUP_WINDOW:
            break
        if entry["sha256"] == sha:
            return entry
    return None


def main() -> None:
    path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("data/pending-linkedin-post.json")
    )
    if not path.exists():
        print("no pending LinkedIn post; nothing to do")
        return

    try:
        post = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        reject(f"{path} is not valid JSON: {exc}")
    if not isinstance(post, dict):
        reject(f"{path} is not a JSON object")
    text = compose_text(post)
    if not text:
        reject(f"{path} has no 'text'")
    if len(text) > MAX_CHARS:
        reject(f"post is {len(text)} chars; LinkedIn caps at {MAX_CHARS}")

    url = os.environ.get("SLOPU_LINKEDIN_WEBHOOK")
    key = os.environ.get("SLOPU_LINKEDIN_WEBHOOK_KEY")
    if not url or not key:
        fail("SLOPU_LINKEDIN_WEBHOOK and SLOPU_LINKEDIN_WEBHOOK_KEY must be set")

    ledger_path = path.parent / LEDGER_NAME
    now = dt.datetime.now(dt.UTC)
    sha = digest(text)
    dup = recent_duplicate(read_ledger(ledger_path), sha, now)
    if dup:
        print(f"identical post already {dup['status']} at {dup['at']} --- skipping")
        return

    payload = {"text": text, "link": post.get("link"), "subject": post.get("subject")}
    entry = {
        "at": now.isoformat(),
        "sha256": sha,
        "subject": post.get("subject"),
        "text": text,
    }
    try:
        resp = httpx.post(
            url,
            json=payload,
            headers={"x-make-apikey": key},
            timeout=TIMEOUT,
        )
    except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
        fail(f"could not reach the webhook ({type(exc).__name__}); nothing sent")
    except httpx.TransportError as exc:
        append_ledger(ledger_path, entry | {"status": "uncertain"})
        fail(
            f"request may have been delivered ({type(exc).__name__}); "
            "recorded as uncertain, so the retry will not resend it"
        )

    if not resp.is_success:
        fail(f"webhook refused the post: HTTP {resp.status_code} {resp.text.strip()}")
    append_ledger(ledger_path, entry | {"status": "sent"})
    print(f"delivered to the Make relay: HTTP {resp.status_code} {resp.text.strip()}")


if __name__ == "__main__":
    main()
