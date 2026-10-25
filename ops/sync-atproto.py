#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.27", "pyyaml>=6", "typer"]
# ///
"""Reconcile the University's ATproto records with the committed outputs.

slop.university's repo holds one site.standard.publication record, one
site.standard.document per outputs entry (standard.site's long-form lexicons,
so readers such as Leaflet and pckt can find and follow the outputs), and the
University's own lexicons from lexicons/ as com.atproto.lexicon.schema records.
A document's content is a university.slop.output or university.slop.video
object: the DOI, PDF or video link, authors and citation graph that
standard.site has no fields for.

What the records deliberately leave out, and why: no PDF blob (a PDS-hosted
blob would bypass pdf.slop.university's robots.txt), no full text (textContent
is the summary, so no real-literature reference ever reaches the network), and
no self-labels (a label is a rendered "this is satire" signal). Each document
lists the Vice-Chancellor's real account as a contributor under the office's
name, never his own --- the exception canon/leadership.yml records.

Reconcile, not replay: every run computes the wanted record for every entry,
lists what the repo holds, and writes only the difference, so a second run
against an in-sync repo makes zero writes and a failed run is repaired by the
next. Two fields are taken from the existing record rather than recomputed:
coverImage (uploading every OG card each run to learn its CID would cost a
download per output per landing) and a bskyPostRef whose post has since gone.

Record keys carry no state. A document's rkey is a TID built from the entry's
publishedAt and a hash of its id, so the site computes the same AT-URI at build
time (website/src/lib/atproto.ts). Both implementations are pinned to the test
vectors in website/src/lib/atproto.json, checked at every start.

Writes spend the account's PDS rate budget, which the Bluesky poster shares.
The landers run this after their post with --no-wait and a write cap, so a
large reconcile (a lexicon change touching every document) proceeds across
landings without ever holding one up; a hand backfill passes --wait. Cover
uploads draw on a separate, smaller budget (uploadBlob, 1000 a day), which the
poster's link-card thumbnails share too, so a run stops uploading covers while
BLOB_RESERVE uploads are left. A run learns that budget from its first upload,
so each run past the reserve spends one more.

The lexicons resolve through the DNS TXT record _lexicon.slop.university,
value "did=<the University's DID>"; it is set once at the DNS host, by hand.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Annotated, Any

import httpx
import typer
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

SITE_URL = "https://slop.university"
PDF_BASE = "https://pdf.slop.university"  # also serves the video encodes
IMG_BASE = "https://img.slop.university"
DEFAULT_PDS = "https://bsky.social"
HANDLE = "slop.university"  # hard-coded; only the app password (SLOPU_TOKEN) is secret
TIMEOUT = 30.0

DOCUMENT = "site.standard.document"
PUBLICATION = "site.standard.publication"
SCHEMA = "com.atproto.lexicon.schema"
POST = "app.bsky.feed.post"

# The office, never the name: the account is linked, the displayed string is the
# canon's (canon/leadership.yml).
VICE_CHANCELLOR = {
    "did": "did:plc:tevykrhi4kibtsipzci76d76",
    "role": "Vice-Chancellor",
    "displayName": "Office of the Vice-Chancellor",
}

# Whether readers list the publication in their discovery feeds. Set by hand,
# never left to the lexicon default (true). Off while the first backfill runs,
# so ~2550 backdated documents don't reach readers' discovery feeds at once; on
# once it has finished, from when each new output is discoverable as it lands.
SHOW_IN_DISCOVER = False

PUBLICATION_RECORD = {
    "$type": PUBLICATION,
    "url": SITE_URL,
    "name": "Slop University",
    "description": (
        "Research outputs of Slop University: papers, posters, theses, "
        "strategic plans and impact reports from across its schools."
    ),
    "basicTheme": {
        "$type": "site.standard.theme.basic",
        "background": {
            "$type": "site.standard.theme.color#rgb",
            "r": 255,
            "g": 255,
            "b": 255,
        },
        "foreground": {
            "$type": "site.standard.theme.color#rgb",
            "r": 26,
            "g": 26,
            "b": 26,
        },
        "accent": {
            "$type": "site.standard.theme.color#rgb",
            "r": 138,
            "g": 92,
            "b": 19,
        },
        "accentForeground": {
            "$type": "site.standard.theme.color#rgb",
            "r": 255,
            "g": 255,
            "b": 255,
        },
    },
    "preferences": {"showInDiscover": SHOW_IN_DISCOVER},
}

# applyWrites point costs (the PDS's own accounting) and the batch size.
COST = {"create": 3, "update": 2, "delete": 1}
BATCH = 25
# Over this many deletes in one run is a wrong checkout, not retractions.
MAX_DELETES = 10
MAX_BLOB_BYTES = 1_000_000
# uploadBlob calls left to the Bluesky poster's thumbnails; the margin covers the
# one upload each run spends learning the budget.
BLOB_RESERVE = 100

# --- Record keys --------------------------------------------------------------

B32 = "234567abcdefghijklmnopqrstuvwxyz"


def tid(ms: int, clock_id: int) -> str:
    """A TID: 53 bits of microseconds since the epoch, then a 10-bit clock id."""
    value = (ms * 1000) << 10 | clock_id
    return "".join(B32[(value >> (5 * i)) & 31] for i in reversed(range(13)))


def published_at(value: str | dt.datetime) -> dt.datetime:
    """An entry's publishedAt: YAML parses it as a datetime unless it is quoted."""
    return value if isinstance(value, dt.datetime) else dt.datetime.fromisoformat(value)


def published_ms(value: str | dt.datetime) -> int:
    when = published_at(value)
    return (when - dt.datetime(1970, 1, 1, tzinfo=dt.UTC)) // dt.timedelta(
        milliseconds=1
    )


def document_rkey(entry_id: str, published_at: str | dt.datetime) -> str:
    digest = hashlib.sha256(entry_id.encode()).digest()
    return tid(published_ms(published_at), int.from_bytes(digest[:2], "big") >> 6)


def check_vectors(constants: dict) -> None:
    for vector in constants["vectors"]:
        got = document_rkey(vector["id"], vector["publishedAt"])
        if got != vector["rkey"]:
            raise SystemExit(
                f"rkey drift for {vector['id']}: {got} != {vector['rkey']}"
            )


# --- The wanted state ---------------------------------------------------------


def load_yaml_dir(path: Path) -> dict[str, dict]:
    return {f.stem: yaml.safe_load(f.read_text()) for f in sorted(path.glob("*.yml"))}


def class_token(preset: str) -> str:
    head, *rest = preset.split("-")
    return f"university.slop.defs#{head}{''.join(w.title() for w in rest)}"


def video_url(video: dict) -> str | None:
    for cuts, key in (
        (video.get("web") or {}, "video"),
        (video.get("signage") or {}, None),
    ):
        for aspect in ("landscape", "portrait"):
            cut = cuts.get(aspect)
            if cut:
                return f"{PDF_BASE}/{cut[key] if key else cut}"
    return None


def post_refs(posts: list[dict]) -> dict[str, dict]:
    """Map each output URL a post links to onto that post's strongRef.

    listRecords returns newest first, so the oldest post (the announcement) wins.
    """
    refs: dict[str, dict] = {}
    for post in posts:
        uri = ((post["value"].get("embed") or {}).get("external") or {}).get("uri", "")
        if uri.startswith(f"{SITE_URL}/outputs/"):
            refs[uri.rstrip("/")] = {"uri": post["uri"], "cid": post["cid"]}
    return refs


def wanted_documents(
    root: Path, did: str, publication_uri: str, posts: list[dict]
) -> dict[str, dict]:
    content = root / "website/src/content"
    entries = load_yaml_dir(content / "outputs")
    videos = load_yaml_dir(content / "videos")
    labels = json.loads((root / "website/src/lib/preset-labels.json").read_text())
    roster = {
        r["id"]: r["name"]
        for r in yaml.safe_load((root / "canon/roster.yml").read_text())["researchers"]
    }
    refs = post_refs(posts)

    rkeys = {eid: document_rkey(eid, e["publishedAt"]) for eid, e in entries.items()}
    uri_of = {eid: f"at://{did}/{DOCUMENT}/{rkey}" for eid, rkey in rkeys.items()}
    uri_by_doi = {e["doi"]: uri_of[eid] for eid, e in entries.items()}

    wanted: dict[str, dict] = {}
    for eid, e in sorted(
        entries.items(), key=lambda kv: published_ms(kv[1]["publishedAt"])
    ):
        body: dict[str, Any] = {
            "outputClass": class_token(e["preset"]),
            "doi": e["doi"],
            "authors": e.get("authors") or [],
        }
        if e.get("school"):
            body["school"] = e["school"]
        cites = [uri_by_doi[d] for d in e.get("cites") or [] if d in uri_by_doi]
        if cites:
            body["cites"] = cites
        if e["preset"].startswith("video-"):
            video = videos.get(eid) or {}
            url = video_url(video)
            if not url:
                print(
                    f"skipping {eid}: no videos entry with an encode", file=sys.stderr
                )
                continue
            body = {"$type": "university.slop.video", **body, "video": url}
            if video.get("output") in uri_of:
                body["subjectOutput"] = uri_of[video["output"]]
            if video.get("person") in roster:
                body["featuredResearcher"] = roster[video["person"]]
        else:
            body = {
                "$type": "university.slop.output",
                **body,
                "pdf": f"{PDF_BASE}/{eid}.pdf",
            }
            if e.get("pages"):
                body["pages"] = e["pages"]

        record: dict[str, Any] = {
            "$type": DOCUMENT,
            "site": publication_uri,
            "path": f"/outputs/{eid}/",
            "title": e["title"],
            "description": e.get("subtitle") or e["title"],
            "textContent": e["summary"],
            "tags": [t for t in (labels[e["preset"]], e.get("school")) if t],
            "publishedAt": published_at(e["publishedAt"]).isoformat(),
            "contributors": [VICE_CHANCELLOR],
            "content": body,
        }
        ref = refs.get(f"{SITE_URL}/outputs/{eid}")
        if ref:
            record["bskyPostRef"] = ref
        wanted[rkeys[eid]] = {"id": eid, "record": record}
    return wanted


def canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


# --- The PDS ------------------------------------------------------------------


class RateBudgetSpent(Exception):
    pass


class Pds:
    def __init__(self, wait: bool) -> None:
        password = os.environ.get("SLOPU_TOKEN")
        if not password:
            raise SystemExit(
                "SLOPU_TOKEN must be set (the @slop.university app password)"
            )
        resp = httpx.post(
            f"{DEFAULT_PDS}/xrpc/com.atproto.server.createSession",
            json={"identifier": HANDLE, "password": password},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        session = resp.json()
        pds = next(
            (
                s["serviceEndpoint"]
                for s in session.get("didDoc", {}).get("service") or []
                if s.get("type") == "AtprotoPersonalDataServer"
            ),
            DEFAULT_PDS,
        )
        self.did: str = session["did"]
        self.wait = wait
        self.remaining: int | None = None
        self.reset_at = 0.0
        self.blobs_left: int | None = None
        self.blobs_reset_at = 0.0
        self.http = httpx.Client(
            base_url=f"{pds}/xrpc/",
            headers={"Authorization": f"Bearer {session['accessJwt']}"},
            timeout=TIMEOUT,
        )

    def _send(self, method: str, nsid: str, **kwargs: Any) -> httpx.Response:
        while True:
            resp = self.http.request(method, nsid, **kwargs)
            blob = nsid == "com.atproto.repo.uploadBlob"
            if method == "POST" and "ratelimit-remaining" in resp.headers:
                left = int(resp.headers["ratelimit-remaining"])
                reset_at = float(resp.headers.get("ratelimit-reset", 0))
                if blob:
                    self.blobs_left, self.blobs_reset_at = left, reset_at
                else:
                    self.remaining, self.reset_at = left, reset_at
            if resp.status_code != 429:
                return resp
            self.pause(blob)

    def pause(self, blob: bool = False) -> None:
        if not self.wait:
            raise RateBudgetSpent
        reset_at = self.blobs_reset_at if blob else self.reset_at
        delay = max(reset_at - time.time(), 0) + 5
        print(f"rate budget spent; waiting {delay:.0f}s", flush=True)
        time.sleep(delay)
        if blob:
            self.blobs_left = None
        else:
            self.remaining = None

    def afford(self, cost: int) -> None:
        if self.remaining is not None and self.remaining < cost:
            self.pause()

    def can_upload(self) -> bool:
        """Whether a cover upload leaves the poster its reserve (waits if --wait)."""
        if self.blobs_left is None or self.blobs_left > BLOB_RESERVE:
            return True
        if not self.wait:
            return False
        self.pause(blob=True)
        return True

    def get(self, nsid: str, **params: Any) -> httpx.Response:
        return self._send("GET", nsid, params=params)

    def post(self, nsid: str, **kwargs: Any) -> dict:
        resp = self._send("POST", nsid, **kwargs)
        if resp.status_code != 200:
            raise RuntimeError(f"{nsid} {resp.status_code}: {resp.text}")
        return resp.json()

    def list_records(self, collection: str) -> list[dict]:
        records, cursor = [], None
        while True:
            params = {"repo": self.did, "collection": collection, "limit": 100}
            if cursor:
                params["cursor"] = cursor
            resp = self.get("com.atproto.repo.listRecords", **params)
            resp.raise_for_status()
            page = resp.json()
            records += page["records"]
            cursor = page.get("cursor")
            if not cursor or not page["records"]:
                return records

    def get_record(self, collection: str, rkey: str) -> dict | None:
        resp = self.get(
            "com.atproto.repo.getRecord",
            repo=self.did,
            collection=collection,
            rkey=rkey,
        )
        if resp.status_code == 400 and "RecordNotFound" in resp.text:
            return None
        resp.raise_for_status()
        return resp.json()["value"]

    def put_record(self, collection: str, rkey: str, record: dict) -> None:
        self.afford(COST["update"])
        self.post(
            "com.atproto.repo.putRecord",
            json={
                "repo": self.did,
                "collection": collection,
                "rkey": rkey,
                "record": record,
            },
        )

    def upload_cover(self, entry_id: str) -> dict | None:
        """The entry's OG card as a blob, or None (fail-open) when it can't be had."""
        try:
            img = httpx.get(f"{IMG_BASE}/og/outputs/{entry_id}.jpg", timeout=TIMEOUT)
        except httpx.HTTPError:
            return None
        if (
            img.status_code != 200
            or not img.content
            or len(img.content) >= MAX_BLOB_BYTES
        ):
            return None
        return self.post(
            "com.atproto.repo.uploadBlob",
            content=img.content,
            headers={"Content-Type": "image/jpeg"},
        )["blob"]


# --- Reconcile ----------------------------------------------------------------


def sync_singletons(pds: Pds, root: Path, publication_rkey: str, dry_run: bool) -> int:
    """The lexicon schemas and the publication; returns the writes made."""
    profile = pds.get_record("app.bsky.actor.profile", "self") or {}
    publication = dict(PUBLICATION_RECORD)
    if profile.get("avatar"):
        publication["icon"] = profile["avatar"]  # the Bluesky avatar's blob, reused
    wanted = [(PUBLICATION, publication_rkey, publication)]
    for path in sorted((root / "lexicons").rglob("*.json")):
        lexicon = json.loads(path.read_text())
        wanted.append((SCHEMA, lexicon["id"], {"$type": SCHEMA, **lexicon}))

    writes = 0
    for collection, rkey, record in wanted:
        existing = pds.get_record(collection, rkey)
        if existing is not None and canonical(existing) == canonical(record):
            continue
        print(f"{'would put' if dry_run else 'put'} {collection}/{rkey}")
        if not dry_run:
            pds.put_record(collection, rkey, record)
        writes += 1
    return writes


def plan_documents(
    wanted: dict[str, dict], existing: dict[str, dict]
) -> tuple[list, list[str]]:
    """The (action, rkey, id, record) writes that differ, and the rkeys to delete."""
    writes = []
    for rkey, want in wanted.items():
        record = want["record"]
        held = existing.get(rkey)
        if held is not None:
            for kept in ("coverImage", "bskyPostRef"):
                if kept in held and kept not in record:
                    record[kept] = held[kept]
            if canonical(held) == canonical(record):
                continue
        writes.append(
            ("update" if held is not None else "create", rkey, want["id"], record)
        )
    return writes, sorted(set(existing) - set(wanted))


def sync_documents(
    pds: Pds,
    wanted: dict[str, dict],
    *,
    dry_run: bool,
    limit: int,
    allow_deletes: bool,
) -> int:
    existing = {
        r["uri"].rsplit("/", 1)[1]: r["value"] for r in pds.list_records(DOCUMENT)
    }
    writes, deletes = plan_documents(wanted, existing)
    if len(deletes) > MAX_DELETES and not allow_deletes:
        raise SystemExit(
            f"refusing to delete {len(deletes)} documents (over {MAX_DELETES}); "
            "a stale or switched checkout looks like this. Rerun with --allow-deletes if meant."
        )
    ops = [*writes, *(("delete", rkey, None, None) for rkey in deletes)]
    if limit:
        ops = ops[:limit]
    print(
        f"{len(writes)} to write and {len(deletes)} to delete; this run takes {len(ops)}"
    )
    if dry_run:
        for action, rkey, eid, _ in ops:
            print(f"  would {action} {rkey} {eid or ''}")
        return len(ops)

    done = 0
    for start in range(0, len(ops), BATCH):
        batch = ops[start : start + BATCH]
        # A document goes out with its cover or waits for the next run: the
        # reconcile never adds a cover to a record that was written without one.
        covers_spent = False
        for i, (action, _, eid, record) in enumerate(batch):
            if action != "delete" and "coverImage" not in record:
                if not pds.can_upload():
                    batch, covers_spent = batch[:i], True
                    break
                cover = pds.upload_cover(eid)
                if cover:
                    record["coverImage"] = cover
        if not batch:
            raise RateBudgetSpent
        pds.afford(sum(COST[op[0]] for op in batch))
        pds.post(
            "com.atproto.repo.applyWrites",
            json={
                "repo": pds.did,
                "writes": [
                    {
                        "$type": f"com.atproto.repo.applyWrites#{action}",
                        "collection": DOCUMENT,
                        "rkey": rkey,
                    }
                    | ({"value": record} if record is not None else {})
                    for action, rkey, _, record in batch
                ],
            },
        )
        done += len(batch)
        print(f"  wrote {done}/{len(ops)}", flush=True)
        if covers_spent:
            raise RateBudgetSpent
    return done


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


@app.command()
def main(
    root: Annotated[
        Path, typer.Option(help="checkout whose committed entries are the truth")
    ] = REPO_ROOT,
    dry_run: Annotated[
        bool, typer.Option(help="print the writes without making them")
    ] = False,
    limit: Annotated[
        int, typer.Option(help="cap the document writes this run (0: none)")
    ] = 0,
    wait: Annotated[
        bool, typer.Option(help="sleep out a spent rate budget rather than stop")
    ] = False,
    allow_deletes: Annotated[
        bool, typer.Option(help=f"permit over {MAX_DELETES} deletes")
    ] = False,
    check_vectors_only: Annotated[
        bool, typer.Option("--check-vectors", help="check the rkey vectors and exit")
    ] = False,
) -> None:
    constants = json.loads((root / "website/src/lib/atproto.json").read_text())
    check_vectors(constants)
    if check_vectors_only:
        print("rkey vectors agree")
        return

    pds = Pds(wait=wait)
    if pds.did != constants["did"]:
        raise SystemExit(
            f"logged in as {pds.did}, but the site renders AT-URIs for {constants['did']}"
        )
    publication_uri = f"at://{pds.did}/{PUBLICATION}/{constants['publicationRkey']}"
    try:
        writes = sync_singletons(pds, root, constants["publicationRkey"], dry_run)
        wanted = wanted_documents(
            root, pds.did, publication_uri, pds.list_records(POST)
        )
        writes += sync_documents(
            pds, wanted, dry_run=dry_run, limit=limit, allow_deletes=allow_deletes
        )
    except RateBudgetSpent:
        print("rate budget spent; the next run resumes")
        return
    print(f"in sync: {writes} {'planned' if dry_run else 'made'}")


if __name__ == "__main__":
    app()
