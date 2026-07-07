---
name: post-to-bluesky
description:
  Compose one Bluesky post about an existing aspect of Slop University --- a
  recent output, a researcher, a school, or the institution itself --- into
  data/pending-post.json, in a click-through hook voice and linking to a live
  slop.university URL. This skill only COMPOSES; the cron wrapper posts it live
  after a validated push (the agent never holds credentials). Invoked by the
  /publish ladder's 2G rung when the department is coherent and the account has
  been quiet, or manually to stage a one-off post.
---

# post-to-bluesky

Slop University runs an autonomous Bluesky account, `@slop.university`. This
skill composes one post for it and stages the post as `data/pending-post.json`.
It does **not** post. The cron wrapper (`ops/cron-publish.sh`) runs
`ops/post-to-bluesky.py` after its validated push and is the only thing that
holds the account credentials --- the same trust split as "the agent commits,
the wrapper pushes". The reason is sharp: the `/publish` agent ingests untrusted
RSS feeds unattended, so it must never hold live posting rights to a real
account.

One invocation writes at most one `data/pending-post.json`. The action makes
**no commit** --- the staged file is gitignored, and the wrapper deletes it once
posted (or leaves it for the next run to retry on failure).

## Preconditions --- when NOT to compose

Check both before composing. If either fails, do nothing and say so.

1. **A post is already staged.** If `data/pending-post.json` exists, a prior run
   composed a post the wrapper hasn't cleared yet (either not posted, or a
   failed post awaiting retry). Leave it --- don't overwrite.
2. **The account posted recently.** Read the account's own public feed (no
   auth):

   ```
   curl -s 'https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=slop.university&limit=5'
   ```

   If the most recent post's `record.createdAt` is younger than ~20 hours, the
   account is not due --- do nothing. This keeps the hourly publish cron from
   posting more than roughly once a day. If the feed fetch fails or can't be
   parsed, treat the account as _not_ due (fail closed --- never post on a blind
   guess).

The same feed read doubles as subject history: note what the last handful of
posts were about so the new one covers different ground.

## Choose a subject

Post about **any existing, already-live aspect** of Slop University --- not this
run's fresh work (there is none on a 2G run). Read `canon/roster.yml`,
`canon/schools.yml`, and `website/src/content/outputs/*.yml`, and pick one:

- a **research output** worth resurfacing --- `outputs/<id>`, link
  `https://slop.university/outputs/<id>`
- a **researcher** --- `people/<id>`, link `https://slop.university/people/<id>`
- a **school, unit, or lab** --- `schools/<id>`, link
  `https://slop.university/schools/<id>`
- the **institution** in general --- link `https://slop.university`

Favour variety against the recent feed (don't resurface the same output two
posts running) and against imbalance (a school or researcher that has never been
posted about is a good pick). An older output the timeline hasn't seen is better
than the newest one, which its own announcement already covered.

## Compose the post

The register builds on `../publish/comms.md` (institutional media-release),
which defers to `../from-preset/genre.md` for the floor --- but the social
account is its own surface, and it is the one place the department writes for
the scroll. Unlike a news-release headline (`comms.md`: "not clever, just
proud"), a post's whole job is to make someone stop and tap through. Lean
click-baity.

The link now renders a card --- title, description, and image pulled from the
page's OpenGraph meta --- so the card carries the _what_. That frees the text to
be pure hook: don't summarise the thing, bait the tap.

- **Lead with a curiosity gap.** Open on the counterintuitive puzzle, the
  question, the "what happens when...", the tension the work sits on --- not a
  description of it. Say enough to intrigue, not enough to satisfy without the
  click.
- **Front-load the hook, not the letterhead.** The interesting idea comes first;
  the school or researcher name can wait for the second clause or the card.
  Don't open with "Slop University's School of X..." when the idea is the draw.
- **Direct address earns the tap.** "You'd assume the two targets never
  interact" reads as a hook, not a wink. A rhetorical question is fair game.

The deadpan is load-bearing --- it is _how_ the satire reads straight --- so the
hard floors hold even in hook mode. The clickbait is curiosity and framing,
never punctuation or hype:

- **No exclamation marks, no hype superlatives.** `novel`/`significant` stays
  the ceiling; no `groundbreaking`, `world-first`, `shocking`,
  `you won't believe`. A post that reaches for those has stopped being deadpan.
- **No verifiable claims** --- no grant dollars, rankings, dated targets,
  partner names, or invented statistics ("a 40% jump" is out even as bait).
  Significance asserted without a checkable referent (the hedged-commitment
  discipline in `comms.md`).
- **No satire signals** --- reads straight. A curiosity hook is fine; a knowing
  wink at the fiction is not.
- **Roster names only** (`canon/roster.yml`), canonical name and title; never a
  real person, never a name invented in this run. Org units from
  `canon/schools.yml` only.
- **Don't reuse phrasing** from recent posts (you just read the feed) or from
  the output's own news post.

Length: **at most ~280 characters** including the URL, so it fits Bluesky's
300-grapheme cap with margin. One sharp idea, teased not told. Write the post
text; you may place the URL inline where it reads naturally, or leave it out of
the text and let the `link` field append it (the card renders either way).

## Write the staged file

Write `data/pending-post.json` (create `data/` if absent):

```json
{
  "text": "Sign the strategy, and watch the enthusiasm for it quietly evaporate --- long after anyone remembers why it was signed. The School of Emergent Priorities has been mapping exactly where it goes.",
  "link": "https://slop.university/outputs/anu-poster-enthusiasm-drift-xxxx",
  "subject": "outputs/anu-poster-enthusiasm-drift-xxxx"
}
```

- `text` (required) --- the post body, comms register, no trailing URL unless
  you want it mid-sentence.
- `link` (optional but usual) --- the canonical slop.university URL. The poster
  makes it a clickable link facet, appending it on its own line when it isn't
  already in `text`.
- `subject` (optional) --- the site path, for the run log only; not posted.

Do not stamp `createdAt` --- the poster stamps it at post time.

## Report and stop

Surface the choice in the run's text output: the subject, the link, and the
exact `text`. Make no commit --- the staged file is the whole deliverable, and
the wrapper takes it from here. Then exit.

## Credentials (wrapper only)

`ops/post-to-bluesky.py` hard-codes the `slop.university` handle and reads only
the app password, as `SLOPU_TOKEN`, from the wrapper's mise env --- a Bluesky
**app password** (Settings → App Passwords), never the account password, and
never in a tracked file. It belongs in the same untracked mise env block as
`REPLICATE_API_TOKEN`. The agent side of this skill needs no credentials.
