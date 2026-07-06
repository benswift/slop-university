#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""Publish the staged social post (data/pending-post.json) to Bluesky.

The trust-boundary counterpart to the /publish agent. The unattended agent,
which ingests untrusted RSS, only ever COMPOSES a post into
data/pending-post.json (a gitignored working-tree file it cannot push). This
script --- run by the cron wrapper AFTER the validated push, with the SLOPU_TOKEN
credential the agent never sees --- is the only thing that posts live. Same
split as "the agent commits, the wrapper pushes".

The handle is hard-coded (BSKY_HANDLE below); only the app password is secret,
supplied as SLOPU_TOKEN (a Bluesky *app password*, not the account password).
createSession runs against bsky.social, then we follow the didDoc to the
account's real PDS so the write hits the right server even when AppView lags.

pending-post.json schema:
  {
    "text":      "the post body, <=300 chars, comms register",   (required)
    "link":      "https://slop.university/outputs/<id>",          (optional)
    "subject":   "outputs/<id>",                                  (optional, provenance only)
    "createdAt": "2026-...Z"                                      (optional, stamped if absent)
  }

If `link` is present it is faceted as a clickable link --- in place when the URL
is already in `text`, otherwise appended on its own line.

Exit 0 on a successful (or deduped) post; the wrapper deletes the file only
then. Any non-zero exit leaves it staged for the next run to retry --- the dedup
guard means a lost-response retry can't double-post.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import httpx

DEFAULT_PDS = "https://bsky.social"
BSKY_HANDLE = (
    "slop.university"  # hard-coded; only the app password (SLOPU_TOKEN) is secret
)
TIMEOUT = 20.0
# A staged post is retried across hourly wrapper runs; collapse a re-issue of the
# same text within a day so a lost createRecord response can't double-post.
DEDUP_WINDOW_MIN = 24 * 60
MAX_CHARS = (
    300  # Bluesky's post length cap (graphemes; chars is a close, conservative proxy)
)


def fail(msg: str):
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def get_session() -> dict:
    password = os.environ.get("SLOPU_TOKEN")
    if not password:
        fail("SLOPU_TOKEN must be set (the @slop.university Bluesky app password)")
    resp = httpx.post(
        f"{DEFAULT_PDS}/xrpc/com.atproto.server.createSession",
        json={"identifier": BSKY_HANDLE, "password": password},
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        fail(f"createSession {resp.status_code}: {resp.text}")
    data = resp.json()
    pds = DEFAULT_PDS
    for svc in data.get("didDoc", {}).get("service") or []:
        if svc.get("type") == "AtprotoPersonalDataServer":
            pds = svc["serviceEndpoint"]
            break
    return {"did": data["did"], "jwt": data["accessJwt"], "pds": pds}


def link_facet(text: str, url: str) -> tuple[str, list[dict]]:
    """Return (text, facets) with `url` present in text and faceted as a link.

    ATProto facet byteStart/byteEnd are UTF-8 byte offsets, not code points.
    """
    if url not in text:
        text = f"{text.rstrip()}\n\n{url}"
    encoded = text.encode("utf-8")
    start = encoded.find(url.encode("utf-8"))
    end = start + len(url.encode("utf-8"))
    facet = {
        "index": {"byteStart": start, "byteEnd": end},
        "features": [{"$type": "app.bsky.richtext.facet#link", "uri": url}],
    }
    return text, [facet]


def recent_duplicate(session: dict, text: str) -> str | None:
    """Best-effort, fail-open: the URI of a recent identical post, else None."""
    try:
        resp = httpx.get(
            f"{session['pds']}/xrpc/com.atproto.repo.listRecords",
            params={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "limit": 25,
            },
            headers={"Authorization": f"Bearer {session['jwt']}"},
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        norm = re.sub(r"\s+", " ", text.strip())
        cutoff = dt.datetime.now(dt.UTC) - dt.timedelta(minutes=DEDUP_WINDOW_MIN)
        for item in resp.json().get("records", []):
            value = item.get("value") or {}
            try:
                when = dt.datetime.fromisoformat(
                    value.get("createdAt", "").replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                continue
            if when < cutoff:
                continue
            if re.sub(r"\s+", " ", (value.get("text") or "").strip()) == norm:
                return item.get("uri")
    except Exception:
        return None
    return None


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/pending-post.json")
    if not path.exists():
        print("no pending post; nothing to do")
        return

    post = json.loads(path.read_text())
    text = (post.get("text") or "").strip()
    if not text:
        fail(f"{path} has no 'text'")
    link = post.get("link")
    now = post.get("createdAt") or dt.datetime.now(dt.UTC).strftime(
        "%Y-%m-%dT%H:%M:%S.000Z"
    )

    facets: list[dict] = []
    if link:
        text, facets = link_facet(text, link)
    if len(text) > MAX_CHARS:
        fail(f"post is {len(text)} chars; Bluesky caps at {MAX_CHARS}")

    session = get_session()
    dup = recent_duplicate(session, text)
    if dup:
        print(f"identical post within dedup window; already at {dup} --- skipping")
        return

    record = {
        "$type": "app.bsky.feed.post",
        "text": text,
        "createdAt": now,
        "langs": ["en"],
    }
    if facets:
        record["facets"] = facets
    body = {
        "repo": session["did"],
        "collection": "app.bsky.feed.post",
        "record": record,
    }
    resp = httpx.post(
        f"{session['pds']}/xrpc/com.atproto.repo.createRecord",
        headers={"Authorization": f"Bearer {session['jwt']}"},
        json=body,
        timeout=TIMEOUT,
    )
    if resp.status_code != 200:
        fail(f"createRecord {resp.status_code}: {resp.text}")
    print(f"posted: {resp.json().get('uri', '?')}")


if __name__ == "__main__":
    main()
