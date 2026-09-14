---
name: post-to-socials
description:
  Compose posts about one existing aspect of Slop University --- a recent
  output, a researcher, a school, or the institution itself --- for each due
  social platform (Bluesky and the LinkedIn Page), with separate copy written to
  each platform's own conventions, staged as data/pending-post.json and
  data/pending-linkedin-post.json. This skill only COMPOSES; the cron wrapper
  posts after a validated push (the agent never holds credentials). Invoked by
  the /publish ladder's 2G rung, or manually to stage a one-off post.
---

# post-to-socials

Slop University runs two autonomous social accounts: `@slop.university` on
Bluesky and the Slop University Page on LinkedIn
(`linkedin.com/company/slop-university`). This skill picks one subject and
writes a post about it for each due platform, staging one file per platform. It
does **not** post. The cron wrapper runs the posters (`flush_staged_posts` in
`ops/publish-lib.sh`) and is the only thing that holds the credentials --- the
same trust split as "the agent commits, the wrapper pushes". The reason is
sharp: the `/publish` agent ingests untrusted RSS feeds unattended, so it must
never hold live posting rights to a real account.

The action makes **no commit** --- the staged files are gitignored, and the
wrapper deletes each one once posted (or leaves it for the next run to retry on
failure).

## Which platforms

On a 2G run the invocation line's `platforms` parameter names the due platforms.
Compose for exactly those; the assessor has already applied the gates.

Invoked by hand, check each platform yourself and skip any that fails either
test. If none is due, do nothing and say so.

1. **A post is already staged.** `data/pending-post.json` (Bluesky) or
   `data/pending-linkedin-post.json` (LinkedIn) exists: a prior run's post is
   still waiting to go out or to be retried. Leave it --- don't overwrite.
2. **The account posted recently** (within ~20 hours):
   - Bluesky: read the public feed (no auth) and check the newest
     `record.createdAt`:

     ```
     curl -s 'https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?actor=slop.university&limit=5'
     ```

     If the fetch fails or can't be parsed, treat Bluesky as _not_ due (fail
     closed --- never post on a blind guess).

   - LinkedIn: the Page can't be read back, so read the last line of
     `data/linkedin-ledger.jsonl` (the poster's delivery record) and check its
     `at`. No ledger means nothing has been posted yet.

The same reads double as subject history: the Bluesky feed's recent posts, and
the `subject` and `text` of the ledger's recent lines. Note what they covered so
the new post covers different ground.

## Choose a subject

One subject for the whole run, shared by every platform you compose for. Post
about **any existing, already-live aspect** of Slop University --- not this
run's fresh work (there is none on a 2G run). Read `canon/roster.yml`,
`canon/schools.yml`, `website/src/content/outputs/*.yml`, and
`website/src/content/grants/*.yml`, and pick one:

- a **research output** worth resurfacing --- `outputs/<id>`, link
  `https://slop.university/outputs/<id>`
- a **researcher** --- `people/<id>`, link `https://slop.university/people/<id>`
- a **school, unit, or lab** --- `schools/<id>`, link
  `https://slop.university/schools/<id>`
- a **grant or prize** (`website/src/content/grants/*.yml`) --- link its
  announcing news post, `https://slop.university/news/<news id>` (grants have no
  landing page of their own). The internal-award-value carve-out in
  `../publish/comms.md` applies: the exact dollar figure is fair game as hook
  material.
- the **institution** in general --- link `https://slop.university`

Favour variety against the recent posts (don't resurface the same output two
posts running) and against imbalance (a school or researcher that has never been
posted about is a good pick). An older output the timeline hasn't seen is better
than the newest one, which its own announcement already covered.

## Floors for every platform

The register builds on `../publish/comms.md` (institutional media-release),
which defers to `../from-preset/genre.md` for the floor. Each platform then
bends it to its own medium, but these hold everywhere:

- **No verifiable claims** --- no grant dollars (outside the carve-out above),
  rankings, dated targets, partner names, or invented statistics ("a 40% jump"
  is out even as bait). Significance asserted without a checkable referent (the
  hedged-commitment discipline in `comms.md`).
- **No hype superlatives** --- no `groundbreaking`, `world-first`,
  `revolutionary`, `shocking`, `you won't believe`; `novel`/`significant` stays
  the ceiling.
- **No satire signals** --- reads straight. A knowing wink at the fiction is
  never fine.
- **Roster names only** (`canon/roster.yml`), canonical name and title; never a
  real person, never a name invented in this run. Org units from
  `canon/schools.yml` only.
- **Don't reuse phrasing** from recent posts (you just read them) or from the
  output's own news post, and don't reuse one platform's sentences on the other.
- **End with the `#slopU` tag**, the last thing in `text`. It is how posts join
  the wider `#slopU` feed, so it is not optional. Write hashtags literally; the
  Bluesky poster facets them itself.

## Bluesky: the hook

Bluesky is where the department writes for the scroll. Unlike a news-release
headline (`comms.md`: "not clever, just proud"), a post's whole job is to make
someone stop and tap through. Lean click-baity.

The link renders a card --- title, description, and image pulled from the page's
OpenGraph meta --- so the card carries the _what_. That frees the text to be
pure hook: don't summarise the thing, bait the tap.

- **Lead with a curiosity gap.** Open on the counterintuitive puzzle, the
  question, the "what happens when...", the tension the work sits on --- not a
  description of it. Say enough to intrigue, not enough to satisfy without the
  click.
- **Front-load the hook, not the letterhead.** The interesting idea comes first;
  the school or researcher name can wait for the second clause or the card.
  Don't open with "Slop University's School of X..." when the idea is the draw.
- **Direct address earns the tap.** "You'd assume the two targets never
  interact" reads as a hook, not a wink. A rhetorical question is fair game.
- **No exclamation marks.** The clickbait is curiosity and framing, never
  punctuation. The deadpan is load-bearing --- it is _how_ the satire reads
  straight.

Length: **at most ~280 characters** including the URL and the `#slopU` tag, so
it fits Bluesky's 300-grapheme cap with margin. The poster refuses anything over
300, and a refused post blocks the account until someone fixes it by hand, so
count. One sharp idea, teased not told. You may place the URL inline where it
reads naturally, or leave it out of the text and let the `link` field append it.

## LinkedIn: the Page post

The Page posts the way every university Page on LinkedIn posts, and the medium's
conventions are the joke. Played straight, they sit so close to the real thing
that the satire lives in how little separates them. Write a different post from
the Bluesky one, not a longer version of it: a new angle and new sentences on
the same subject.

- **Hook above the fold.** LinkedIn shows roughly the first 200 characters and
  then "...see more". Open with one or two short lines that make the fold worth
  opening: a pride opener ("We're proud to share new work from the School of
  Continuous Improvement."), a question, or a counterintuitive line.
- **Short paragraphs.** One or two sentences each, with a blank line between.
- **A takeaways list.** Three or four lines, each led by the same emoji bullet
  (👉, ✅, 📊 or 🔍 --- one per post). That list is where the emoji go, plus at
  most one 👇 pointing at the link.
- **Credit people in plain text**, by canonical roster name and title
  ("Congratulations to Dr ... and the Adaptive Metrics Lab"). Never an @mention:
  roster researchers have no profiles, and a mention can land on a real person.
- **Close on an engagement question** to the reader ("How is your organisation
  approaching ...? We'd welcome your thoughts in the comments.").
- **The URL on its own line** after the question and before the hashtags. Also
  set it as `link`: the poster appends a link only when it is missing from the
  text, which would put it after the hashtags.
- **A hashtag block last**: three to five broad professional tags
  (`#HigherEducation`, `#Research`, `#Leadership`, `#Innovation`,
  `#FutureOfWork` and the like), then `#slopU`. Never a tag naming a real
  organisation, person, event, or brand.
- **Warmer than a news release.** "Proud", "delighted" and "thrilled" are the
  medium's native feelings and fair game. At most one exclamation mark, in the
  opener if anywhere (`genre.md`'s "singles, very sparingly" is the ceiling).

Length: 600--1,300 characters. The poster refuses anything over LinkedIn's
3,000.

## Write the staged files

Create `data/` if absent, and write one file per platform you are composing for.
The examples show the shape; don't reuse their sentences.

`data/pending-post.json` (Bluesky):

```json
{
  "text": "Sign the strategy, and watch the enthusiasm for it quietly evaporate --- long after anyone remembers why it was signed. The School of Emergent Priorities has been mapping exactly where it goes. #slopU",
  "link": "https://slop.university/outputs/anu-poster-enthusiasm-drift-xxxx",
  "subject": "outputs/anu-poster-enthusiasm-drift-xxxx"
}
```

`data/pending-linkedin-post.json` (LinkedIn):

```json
{
  "text": "What happens to a strategy's momentum after the signing ceremony?\n\nWe're proud to share new work from the School of Emergent Priorities, tracing where institutional commitment goes once the launch event is over.\n\nThe work identifies three stages that will be familiar to anyone who has sat through a planning cycle:\n\n👉 Alignment, where every unit can locate itself in the plan\n👉 Translation, where the plan becomes a set of local priorities\n👉 Drift, where the local priorities quietly become the plan\n\nCongratulations to the Trajectory Analytics Group on a significant contribution to how we understand durable commitment.\n\nHow does your organisation keep a strategy alive past its first year? We'd welcome your thoughts in the comments.\n\nRead the full output 👇\nhttps://slop.university/outputs/anu-poster-enthusiasm-drift-xxxx\n\n#HigherEducation #Strategy #Leadership #OrganisationalChange #slopU",
  "link": "https://slop.university/outputs/anu-poster-enthusiasm-drift-xxxx",
  "subject": "outputs/anu-poster-enthusiasm-drift-xxxx"
}
```

- `text` (required) --- the post body. In JSON, line breaks are `\n`.
- `link` (optional but usual) --- the canonical slop.university URL. The Bluesky
  poster makes it a clickable link facet and builds the card from it.
- `subject` (optional) --- the site path, for the run log and the LinkedIn
  ledger's subject history; not posted.

Do not stamp `createdAt` --- the posters stamp it at post time.

## Report and stop

Surface the choice in the run's text output: the subject, the link, and the
exact `text` of each staged post. Make no commit --- the staged files are the
whole deliverable, and the wrapper takes it from here. Then exit.

## Credentials (wrapper only)

The posters read their credentials from the wrapper's untracked mise env block,
never a tracked file:

- `ops/post-to-bluesky.py` hard-codes the `slop.university` handle and reads a
  Bluesky **app password** (Settings → App Passwords, never the account
  password) as `SLOPU_TOKEN`.
- `ops/post-to-linkedin.py` reads `SLOPU_LINKEDIN_WEBHOOK` and
  `SLOPU_LINKEDIN_WEBHOOK_KEY`, the Make relay that posts as the Page. Its
  docstring says why the relay exists and how the Make scenario is set up.

The agent side of this skill needs no credentials, and doesn't have them: the
wrapper strips all three (and the bucket keys) with `env -u` before invoking the
agent, so an agent talked into posting by something it read in a feed has no
credential to post with.
