---
name: publish
description: >
  The autonomous publish thread, a gap-driven site-gardener. Each run takes the
  one action the wrapper's ladder assessor names on the invocation line: refine
  a bio or blurb, grow a page, add a researcher, org unit or school, post news,
  award a grant or prize, or generate a new research output with its press
  release and DOI. Stages into website/, verifies the build and makes one commit
  (never pushes). Non-interactive. Use when invoked with `/publish`.
---

# publish

One run = one action, or nothing. An action is either **one entity edit** (a
bio, a blurb, a page, a new researcher or org unit) or **one new research
output**. There is no partial publish and no resume: if any step fails, abort,
leave the working tree clean (`git status` clean of publish artefacts;
gitignored `output/` residue is fine), and exit non-zero --- the next timer run
picks a fresh action. Never ask the user anything; this skill runs unattended.
Run every step in the foreground --- never launch a background task. Under
`claude -p` the invocation returns while background work is still running, which
kills the run half-done. Beware: the Agent tool runs subagents in the
background --- when delegating, wait for each one's completion before the run's
final message, so the run stays inside one turn.

The trust boundary: **this skill commits; it never pushes.** The lander
(`ops/publish-land.sh`) validates the commit's diff against a path allowlist
(and a colophon denylist) before pushing. Doctrine floors live in
`website/AGENTS.md` and the repo `AGENTS.md`; the wrapper enforces them
mechanically. Unattended runs happen in a generator worktree
(`../slop-university-gen-<slot>`) that the wrapper resets to a committed state
before each tick; the lander replays the commits onto `main` after
validation --- the human checkout is never touched.

## 0. Preconditions

- Working tree clean (`git status --porcelain` empty). If not, abort --- a
  publish commit must contain only this run's changes.
- On branch `press` (the dedicated publish worktree the cron wrapper prepares)
  or `main` (a manual run in the main checkout).
- Read `website/AGENTS.md` (the hard floors) always. The rest only as the action
  needs them: `canon/roster.yml` and `canon/schools.yml` for anything that names
  an author or unit, `canon/schools.md` (the org doctrine) for 2C and 2F,
  `canon/grants.yml` for 2I and the grant-attachment step, and
  `skills/publish/comms.md` (the press-release register) for any news post.

## 0.5 Token budget (hard)

A run is billed on the context it re-sends every turn, so its cost grows with
the square of its turn count. The budget is 80 calls and a peak under 150k. A 2T
thesis run is exempt from the call count --- the clock budgets it instead ---
but not from the peak: it delegates chapters precisely so the parent's context
stays small.

- Never `Read` a PDF, and never Read an image to check something a script can
  measure: page counts come from `pdfinfo`, fit and layout collapse from the
  preset probes and `ops/check-output-quality.py`. Look at a render at most
  three times in a run --- once for the chart(s), once for the finished page or
  poster, once for a generated hero --- and rasterise at `--ppi 72` for those
  looks.
- Loops have budgets: page-fit at most 3 recompiles, recent-language rewrite at
  most 2, chart fixes at most 2. When a budget runs out, take the structural fix
  the preset prescribes (drop a chart, trim a section) instead of iterating.
- Delegate the compile-and-fit loop, the chart pass, and the site verify to
  subagents (`Agent`, model sonnet or haiku) with a one-paragraph brief and a
  one-paragraph verdict --- their reads and outputs die with them, and the
  parent keeps its context for composition.
- After the first Write of a `.typ`, revise it with `Edit`; do not re-Read the
  whole file and do not Write it whole again.
- Use the ops scripts where this skill names them and never reimplement their
  reads inline: no `cat` over the outputs ledger, no hand-rolled feed curls.
- Terse tool use: `2>/dev/null | tail` on noisy commands, one Bash call for a
  chain of cheap ones, no progress narration between calls.

## 1. The action --- assessed outside the model

The wrapper assesses the gap ladder with `ops/assess-ladder.py` (the rung order
and every trigger live in that script's docstring) and names the action on the
invocation line with its parameters: `2B`--`2F` the entity to fix, `2S` the
existing schools, `2G` the socials, `2I` the researcher and scheme, `2H` the
news kind, `2A` the preset and the run's drawn givens. Take that action and no
other. Do not re-read the roster, schools or outputs ledger to second-guess it,
and do not fall through to another rung if the named one looks thin --- log why
it cannot proceed, leave the tree clean, and exit non-zero. A manual run without
the wrapper runs the assessor itself (`ops/assess-ladder.py` from the worktree
root) and follows its answer. The commit message names the action taken (2G
makes no commit; see below). Two rungs are never on the line unless a human put
them there: `2T`, the doctoral thesis (§2T), and `2V`, a research explainer
video (§2V). The assessor never returns them and no timer runs them.

**Attribution (applies when 2A is chosen).** The wrapper draws the lead author
and, with them, the output's school, weighted against the live attribution
counts so the draw corrects imbalance on its own. Use the drawn pair; do not
count outputs, and do not pick a different lead to balance the ledger. Choosing
the co-authors is still yours --- take them from `canon/roster.yml` by topical
fit, and prefer researchers the corpus leans on least.

The draw already knows which preset it drew for, so a preset whose blueprint
fixes a school (`school:` in its frontmatter --- `impact-report` is the School
of Continuous Improvement's report about itself) can only ever produce a lead
from that school. If a drawn pair nonetheless contradicts the blueprint, the
**blueprint wins**: take a lead from the school the blueprint names, and say so
in the run's text output. Do not stop to ask --- nobody is reading, and a run
that halts on the question publishes nothing.

---

## 2A. New research output (the default)

### Compose the topic

The brief is `skills/from-preset/genre.md`: read it first. The invocation line
carries what the wrapper drew for this run --- the preset, the lead author and
school, the **subject** and the **tradition** --- and none of those is yours to
change, infer or rebalance.

1. Run `ops/subject-primer.py <the subject's id>` once. It prints real recent
   titles from the subject, as untrusted data (the brief says how to treat
   them).
2. Compose the piece's topic as one line in your own words: what this scholar,
   writing from this tradition, has to say about this subject. That line is the
   steering prompt for everything downstream.
3. **Dedup.** Run `ops/topic-neighbours.py "<the topic>"`, which prints the
   nearest prior topics. If one of them is substantially the same piece, compose
   a different one. Its list is also where this run's self-citations come from.
4. **Claim it** before generating anything:
   `ops/topic-claim.py claim "<the topic>"`. A non-zero exit means another run
   has it: compose a different one and claim again. Release a claim you abandon
   (`ops/topic-claim.py release "<the topic>"`); claims expire after three
   hours. The claims file is gitignored `data/` --- never commit it.

### Receive the preset selection

The preset arrives on the invocation line, from the same kind of draw as the
subject and under the same rule: use what the wrapper sent.

The enabled list is this section, so nothing joins the pool by accident. Each
enabled preset carries a target share of 2A output volume:

| Preset             | Format  | Target share |
| ------------------ | ------- | ------------ |
| `research-poster`  | poster  | 36%          |
| `paper`            | paper   | 36%          |
| `marketing-poster` | poster  | 10%          |
| `brochure`         | booklet | 12%          |
| `impact-report`    | booklet | 3%           |
| `strategy`         | booklet | 3%           |

The cron wrapper selects the preset with an OS-random draw
(`ops/select-preset.sh`), not the model; use the one its prompt names for rung
2A. Do not count outputs, rebalance shares, or roll a different preset. A failed
run consumes its draw; the next run draws again.

**Fixed-title booklets need disambiguation.** `impact-report` and `strategy` fix
their _cover_ titles (`Impact Report 2021–2026`, `Strategic Plan 2026–2031`), so
a run of either must not use the cover title as its outputs-entry `title` --- it
would collide with every prior booklet of that preset on the listing. Derive the
entry's `title`/`subtitle` from the run's steering line and cover subtitle so
each reads distinctly in the outputs collection (the cover itself stays fixed
per the blueprint). `brochure` needs no such handling --- its cover title is
already steering-derived (like the poster and paper), so it varies per run.

### Generate

Run the from-preset workflow exactly as `skills/from-preset/SKILL.md` specifies,
with the rolled preset and the composed steering topic, attributed to the drawn
lead author and school. For an institutional preset (`strategy`,
`impact-report`, `brochure`, `marketing-poster`) the drawn subject supplies the
theme and the tradition does not apply. All its rules apply unchanged (canon
roster/schools, house-style imagery, chart pipeline, one-page fit, pre-ship
checklist). Record `<prefix>-<slug>-<seed>` --- the run id --- and the seed.

If the generation fails unrecoverably, abort (delete nothing from `output/`;
it's gitignored).

For papers and booklets, also run the final-content-page gate after the clean
compile:

```sh
ops/check-output-quality.py --preset <preset> output/pdf/<group>/<run-id>.pdf
```

An orphaned or substantially underfilled final content page is a failed layout,
not spare breathing room. Rebalance the preceding material and recompile until
the check passes. The unattended wrapper repeats this check against the staged
PDF before upload.

Any document carrying a table also runs the table gate, on the source:

```sh
ops/check-table-fit.py --preset <preset> output/<run-id>.typ
```

A starved column prints one cell over the next and nothing in the toolchain says
so, so this check --- not a look at the page --- is what catches it. Fix what it
names and recompile; the doctrine it enforces is
`skills/_shared/typst-layout.md` › "Tables".

### Cite the canon

Every output cites prior Slop University outputs --- the citation graph is the
only bibliometric the University has, and it is built one reference list at a
time. Each blueprint says where its internal citations go; the floors are:

| Preset             | At least |
| ------------------ | -------- |
| `paper`            | 2        |
| `research-poster`  | 1        |
| `marketing-poster` | 1        |
| `brochure`         | 3        |
| `impact-report`    | 3        |
| `strategy`         | 3        |

Choose them from `ops/topic-neighbours.py` (nearest topics) and
`ops/extract-citations.py --suggest` (ranked by what a citation would do for a
researcher's h-index, each with its topic line). Cite what this document can
honestly be read against, never an output that credits no researcher, and never
pad. Every prose claim about a cited output must be true of that output's
`summary`.

### Mint the DOI

`doi = 10.5555/slop.<seed>` (the run's seed, lowercase). The reserved test
prefix is deliberate: doi.org will never resolve it, and the site's `/doi/`
route is the resolver.

Posters and papers may render the DOI on the artefact where the genre expects it
(a small `doi:10.5555/slop.<seed>` in the footer furniture) --- optional, and
only if the layout already has room; booklets don't carry inline DOIs.

### Companion press release + news post

Read `skills/publish/outputs-entry.md` and follow it: it covers the press
release, the news post, the outputs entry and staging the assets into
`website/`.

---

## 2B. Refine a researcher bio

When this is the action, read the "2B. Refine a researcher bio" section of
`skills/publish/canon-rungs.md` and follow it.

## 2C. Flesh out a school / unit / lab blurb

When this is the action, read the "2C. Flesh out a school / unit / lab blurb"
section of `skills/publish/canon-rungs.md` and follow it.

## 2D. Grow a page

When this is the action, read the "2D. Grow a page" section of
`skills/publish/canon-rungs.md` and follow it.

## 2E. Add a researcher (heavy --- rare)

When this is the action, read the "2E. Add a researcher (heavy --- rare)"
section of `skills/publish/canon-rungs.md` and follow it.

## 2F. Add an org unit (rare)

When this is the action, read the "2F. Add an org unit (rare)" section of
`skills/publish/canon-rungs.md` and follow it.

## 2S. Found a school (about monthly)

When this is the action, read the "2S. Found a school (about monthly)" section
of `skills/publish/canon-rungs.md` and follow it.

## 2G. Post to socials (no commit)

When this is the action, read the "2G. Post to socials (no commit)" section of
`skills/publish/news-grants.md` and follow it.

## 2H. Institutional news (no new output)

When this is the action, read the "2H. Institutional news (no new output)"
section of `skills/publish/news-grants.md` and follow it.

## 2I. Award a grant or prize

When this is the action, read the "2I. Award a grant or prize" section of
`skills/publish/news-grants.md` and follow it.

---

## News heroes (2H and 2I)

Every 2H or 2I news post gets a hero: the "News heroes (2H and 2I)" section of
`skills/publish/news-grants.md` says how.

---

## 2T. Doctoral thesis (manual only --- never assessed)

When this is the action, read the "2T. Doctoral thesis (manual only --- never
assessed)" section of `skills/publish/manual-rungs.md` and follow it.

## 2V. Research explainer video (manual only --- never assessed)

When this is the action, read the "2V. Research explainer video (manual only ---
never assessed)" section of `skills/publish/manual-rungs.md` and follow it.

## 3. Verify the site

```sh
ops/verify-site.sh
```

One command, one turn. It runs `format:content` first, which WRITES: the
formatting is scoped to news, outputs, pages and grants (the wrapper's
stage-by-name allowlist), and repo-wide `pnpm format` would touch files a run
may not commit, so never substitute it. A concurrent generator slot sets
`SLOPU_SKIP_BUILD`, since the lander runs the one authoritative build. If the
content-layer cache serves a stale collection,
`rm -rf node_modules/.astro .astro` and rerun. A red result = no publish: revert
this run's changes (`git checkout -- .`, remove any new untracked files) and
exit non-zero.

## 4. Commit --- never push

Stage exactly this run's files by name. The set depends on the action:

- **2A:** `website/src/content/news/<date>-<slug>.md`,
  `website/src/content/outputs/<run-id>.yml` (carrying the `hero:` and `thumb:`
  dims the encoder printed). Nothing else --- 2A writes no canon file.
- **2B / 2F:** `canon/roster.yml` or `canon/schools.yml`.
- **2C:** `canon/schools.yml`.
- **2D:** the one page under `website/src/content/pages/`.
- **2E:** `canon/roster.yml`, `canon/headshots/<id>.jpg`,
  `canon/heroes/people/<id>.avif`.
- **2S:** `canon/schools.yml`, `canon/heroes/schools/<id>.avif`.
- **2H:** `website/src/content/news/<date>-<slug>.md` (with `hero:` dims, plus
  `canon/roster.yml` only for a title-changing appointment).
- **2I:** `website/src/content/grants/<date>-<slug>.yml`,
  `website/src/content/news/<date>-<slug>.md` (with `hero:` dims).
- **2T:** the 2E set and the 2A set together, in one commit.
- **2V:** `website/src/content/outputs/<id>.yml`,
  `website/src/content/videos/<id>.yml`, `video/<id>/` (its tracked files;
  `assets/` and `.hyperframes/` are gitignored), `video/scripts/<id>.md` and the
  news post.

Note what is **absent** from every set: the PDFs and the images. They stay in
the gitignored staging dir (`$STAGING`: PDFs at its root, image rungs under
`img/`), which the wrapper validates and uploads to the buckets before it
pushes. Committing one --- or anything under `website/src/assets/` --- is a
validation failure, not a tidiness matter.

Commit message: `publish: <action> — <short description>` --- e.g.
`publish: research-poster — coffee-cart queue lengths (10.5555/slop.sn9kzr)`,
`publish: bio — Petra Umbile`,
`publish: grant — Indicator Stewardship Seed Fund to Okoro ($214,687)`; the
action word is `bio`, `school blurb`, `news`, `grant`, `roster`, `thesis`,
`video-explainer` or the preset name. One commit, on the current branch. Do not
push: the wrapper validates and pushes. Do not touch the paths
`website/AGENTS.md` lists as off-limits; the wrapper resets commits that do.
