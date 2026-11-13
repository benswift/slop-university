# News, socials and grants rungs

## 2G. Post to socials (no commit)

Pick one existing, already-live aspect of the department --- an older output
worth resurfacing, a researcher, a school, or the institution --- and compose a
post about it for each platform the `platforms` parameter names (Bluesky, the
LinkedIn Page, or both), each in its own platform's conventions. The assessor
has already applied the due-ness gates; follow `../post-to-socials/SKILL.md` for
the subject choice, the per-platform compose rules, and the staged-file schema.

This action makes no commit. The staged files are gitignored; the cron wrapper
runs the posters after its validated push and is the only thing that posts.
Verify (§3) and commit (§4) do not apply --- once the files are written and the
choice logged, the run is done.

**Files:** `data/pending-post.json` (Bluesky) and
`data/pending-linkedin-post.json` (LinkedIn), gitignored working-tree only;
never committed.

## 2H. Institutional news (no new output)

A news post that announces something other than a research artefact --- the
genre that makes a university newsroom read as a newsroom. One post per run,
`website/src/content/news/<date>-<slug>.md`, same frontmatter as a 2A news post
but with **no `output` field** (the page and homepage card render fine without
one) and with `publishedAt` (the `SLOPU_PUBLISHED_AT` value), which a post with
no output needs to sort among the day's posts. Comms register per `comms.md`;
every name and unit from the canon; no verifiable claims; reads straight.

Write the ONE kind the assessor named (it rotates the three):

- **Event or seminar announcement** --- a session of an existing canon program
  or initiative (`canon/schools.yml` already defines a seminar series and a
  showcase, among others): a named roster speaker, a topic in the school's
  register, a "details to follow" close. No dates more specific than a month or
  a teaching period (a dated event is a verifiable claim; "later this semester"
  is not).
- **Appointment or recognition** --- a roster researcher named to lead an
  existing canon unit, program, or initiative, or recognised with an internal
  distinction. If the appointment changes their `title`, update
  `canon/roster.yml` in the same commit (nothing else about the entry). Never a
  new unit and never a new person --- those are 2F and 2E.
- **Institutional milestone** --- a consultation launched, a program intake
  opened, an annual theme announced, a review begun. The hedged-commitment
  discipline binds hardest here: significance asserted, nothing checkable.

The satire brief carries over from 2A: each of these genres is itself a
pathology exhibit (the seminar about dashboards, the award for measurement
excellence, the consultation about a decision already made).

The post announces no output, so it has no output hero to inherit: generate its
own, per **News heroes** below.

## 2I. Award a grant or prize

An award event: one grant or prize from a canon scheme to roster grantees, plus
the news post announcing it. Grants are not outputs --- no DOI, no PDF, no
generated artefact; the entry and its announcement are the whole deposit, and
the news post is the award's public record (grants have no landing page). The
announcement still carries a hero: it announces no output, so there is none to
inherit, and it generates its own per **News heroes** below.

- **Scheme**: the one the assessor named (the scheme awarded least recently),
  from `canon/grants.yml` --- never invent one, and never edit that file (adding
  a scheme is a human action; the wrapper's allowlist excludes it).
- **Grantees**: roster names, led by the researcher the assessor named (their
  output has run ahead of their funding), plus at most one co-grantee whose
  school fits the scheme's funder.
- **Name**: the funded project's title (for a grant) or the prize citation (for
  a prize), in the funder's register, on a subject the grantee's own outputs
  make plausible. Dedup against existing grant names and output titles.
- **Value discipline (hard)**: whole australian dollars, oddly precise --- never
  a round thousand, never an amount any earlier grant used. Grants land in
  roughly $50,000-$1,000,000; prizes in $5,000-$50,000. A scale comically
  mismatched to the work's triviality is encouraged. The amount is the one
  sanctioned class of precise institutional numbers --- an internal scheme has
  no external registry to falsify it (see the carve-out in `comms.md`).
- **Grant entry** → `website/src/content/grants/<date>-<slug>.yml` with: `name`,
  `scheme` (the canon scheme id), `date` (today, ISO --- it must match the
  filename prefix), `grantees` (roster names), `value`, `summary` (1-2
  sentences, institutional register: what the money is for).
- **News post** → `website/src/content/news/<date>-<slug>.md`, comms register
  per `comms.md`, frontmatter `grant: <grant entry id>`, `publishedAt` (the
  `SLOPU_PUBLISHED_AT` value) and no `output` field. The release may state the
  value exactly (the carve-out); the site appends the award's details box from
  the entry, so the body needn't restate every field.

## News heroes (2H and 2I)

A news post that announces an output inherits that output's hero. A post that
announces none --- a grant award (2I) or an institutional notice (2H) ---
carries its own, so that every page on the site has one.

Same recipe as the output hero in 2A, keyed by the **news entry id** rather than
a run id: author the prompt per `skills/_shared/visual-style.md`, pick refs per
`skills/_shared/image-workflow.md`, generate at `--aspect-ratio 16:9`
`--resolution 2K`, then from the repo root
`ops/encode-images.py encode news-hero --source <generated image> --id <date>-<slug>`
(the id is the post's filename without `.md`) and copy the printed `hero:` dims
snippet into the post's frontmatter. The site derives the URLs from the id +
dims (`src/lib/images.ts`); the rungs are staged under `$STAGING/img/heroes/news/`
and nothing is committed under `website/src/assets/`.

The scene is the post's own subject under the house style's flat two-ink
treatment --- the apparatus the grant funds, the object the notice concerns ---
never a portrait of the named researcher (headshots are the canon's job, and a
hero that tries to depict a specific roster face invites the drift the portrait
convention exists to prevent).
