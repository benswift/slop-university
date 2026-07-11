#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27"]
# ///
"""Publish the staged social post (data/pending-post.json) to Bluesky.

When `link` is present the script also builds an app.bsky.embed.external link
card --- Bluesky does not unfurl links server-side, so without this a linked post
renders as bare text. The card's title/description/image come from the target
page's OpenGraph meta (slop.university emits og:image as JPEG on every output,
news, and profile page); card assembly is fail-open, so a fetch/parse failure
still posts the faceted link, just without the preview.

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
is already in `text`, otherwise appended on its own line. Every #hashtag in the
text (the house tag is #slopU) is faceted as a tappable tag, so the composer
only ever writes literal text.

Exit 0 on a successful (or deduped) post; the wrapper deletes the file only
then. Any non-zero exit leaves it staged for the next run to retry --- the dedup
guard means a lost-response retry can't double-post.
"""

from __future__ import annotations

import datetime as dt
import html
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
# Bluesky rejects image blobs at/above 1,000,000 bytes; over this we post the
# card without a thumbnail (title + description still render) rather than fail.
MAX_BLOB_BYTES = 1_000_000


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


_TAG_RE = re.compile(r"(?<!\w)#([A-Za-z][A-Za-z0-9_]*)")


def tag_facets(text: str) -> list[dict]:
    """Facet every #hashtag in text (byteStart/byteEnd are UTF-8 byte offsets)."""
    facets = []
    for m in _TAG_RE.finditer(text):
        start = len(text[: m.start()].encode("utf-8"))
        end = start + len(m.group(0).encode("utf-8"))
        facets.append(
            {
                "index": {"byteStart": start, "byteEnd": end},
                "features": [
                    {"$type": "app.bsky.richtext.facet#tag", "tag": m.group(1)}
                ],
            }
        )
    return facets


_META_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_ATTR_RE = re.compile(r'(\w[\w:-]*)\s*=\s*"([^"]*)"')


def _parse_og(page: str) -> dict[str, str]:
    """Map og:*/twitter:* meta properties to their (HTML-unescaped) content."""
    og: dict[str, str] = {}
    for tag in _META_RE.findall(page):
        attrs = dict(_ATTR_RE.findall(tag))
        key = attrs.get("property") or attrs.get("name")
        content = attrs.get("content")
        if key and content is not None:
            og[key.lower()] = html.unescape(content)
    return og


def upload_blob(session: dict, data: bytes, mime: str) -> dict | None:
    """uploadBlob and return the blob ref, or None (fail-open) on any failure."""
    try:
        resp = httpx.post(
            f"{session['pds']}/xrpc/com.atproto.repo.uploadBlob",
            headers={
                "Authorization": f"Bearer {session['jwt']}",
                "Content-Type": mime,
            },
            content=data,
            timeout=TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        return resp.json().get("blob")
    except Exception:
        return None


def external_embed(session: dict, url: str) -> dict | None:
    """Build an app.bsky.embed.external card from `url`'s OpenGraph meta.

    Fail-open: any fetch/parse/upload failure returns None so the post still
    goes out as a faceted link, just without the preview card. Bluesky does not
    fetch OG tags itself --- the card only exists if we assemble it here.
    """
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=TIMEOUT)
        if resp.status_code != 200:
            return None
        og = _parse_og(resp.text)
    except Exception:
        return None

    title = og.get("og:title") or og.get("twitter:title")
    if not title:
        return None  # no card worth showing without at least a title
    external: dict = {
        "uri": url,
        "title": title,
        "description": og.get("og:description") or og.get("twitter:description") or "",
    }

    img_url = og.get("og:image") or og.get("twitter:image")
    if img_url:
        try:
            img = httpx.get(img_url, follow_redirects=True, timeout=TIMEOUT)
        except Exception:
            img = None
        if img is not None and img.status_code == 200:
            data = img.content
            mime = img.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            if data and len(data) < MAX_BLOB_BYTES and mime.startswith("image/"):
                blob = upload_blob(session, data, mime)
                if blob:
                    external["thumb"] = blob

    return {"$type": "app.bsky.embed.external", "external": external}


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
    facets.extend(tag_facets(text))
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
    if link:
        embed = external_embed(session, link)
        if embed:
            record["embed"] = embed
            thumb = "with thumbnail" if "thumb" in embed["external"] else "no thumbnail"
            print(f"attached link card ({thumb})")
        else:
            print("could not build link card; posting bare link", file=sys.stderr)
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
