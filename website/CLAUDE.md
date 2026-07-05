# website/ --- slop.university

The public face of Slop University: an Astro site consuming
`astro-theme-university` (pinned release tag) with the `slopBranding` preset in
`src/site-config.ts`. The repo-level `CLAUDE.md` satire rules apply to
everything here; this file adds the doctrine for the autonomous publish agent,
which grows this site over time.

## Hard floors (mechanically enforced --- the push wrapper validates every

## publish commit against a path allowlist; violating paths are reset)

- **Never edit** `.github/workflows/`, `public/CNAME`, `public/robots.txt`,
  `src/site-config.ts` (nav and branding), `canon/schools.md` (the org
  doctrine), or the doctrine files (this file, the repo `CLAUDE.md`, `skills/`).
  The wrapper's allowlist excludes all of these.
- **Reads straight.** No watermark, footer, disclaimer, or "this is satire"
  signal on any page. The one out-of-fiction page is `/colophon/`
  (`src/content/pages/colophon.md`) --- never edit it, never link it from
  anywhere except the footer's existing "About this project" link.
- **No verifiable factual claims.** Nothing checkable-and-falsifiable; no
  fabricated regulatory codes (CRICOS etc.); no real organisations named as
  partners.
- **No real people.** Every named person comes from `canon/roster.yml` (with
  their canonical title and school); every org unit from `canon/schools.md`.
- **DOIs only under `10.5555/slop.<seed>`**, resolving via the site's own
  `/doi/` route. No external registry, ever.
- **No Acknowledgement of Country** anywhere on the site (real institutional
  speech --- not satire material).

## What the agent may grow

The `/publish` tick is gap-driven (see `skills/publish/SKILL.md`): each run
fills one gap. Its editable surface is exactly the wrapper's allowlist:

- **The canon it renders from** --- `canon/roster.yml` (refine a bio; add a
  collision-checked researcher with a house-style `canon/headshots/` portrait)
  and `canon/schools.yml` (write a unit's blurb; add a collision-checked org
  unit). The People and Schools pages are generated from these collections, so
  editing the canon _is_ how those pages grow --- there are no per-researcher or
  per-school files to author.
- **Grown pages** --- `src/content/pages/` (rendered by `[...slug].astro`), e.g.
  the About page. Never `colophon.md` (the wrapper's denylist rejects it).
- **Research outputs** --- news posts and output entries (the tick's default
  action).

The research-performance dashboard and the page routes under `src/pages/` are
built by hand (like this pass), not grown by the tick.

- All imagery follows the two-ink house style
  (`skills/_shared/visual-style.md`), generated via `references/slop-style/`. No
  stock photos, no off-style one-offs.
- Any chart on a web page is Vega-Lite in the theme colours (`--at-primary`
  gold, ink, greys) --- never library-default palettes. Generated PDFs keep
  using gribouille; that pipeline is unchanged.
- Voice: pages stay in the institutional register (`skills/from-preset/`
  `genre.md`); news posts use the comms register (`skills/publish/comms.md`).

## Content model

- `people` and `schools` collections load the canon **in place** from
  `../canon/roster.yml` and `../canon/schools.yml` (see `src/content.config.ts`;
  the schema is the shape enforcement). There are no people/school files under
  `src/` --- editing the canon is how those pages change. Headshots resolve from
  `canon/headshots/` via `src/lib/headshots.ts`. The content test
  (`src/content/content.test.ts`) enforces the seams: output authors and schools
  must exist in the canon.
- `src/content/outputs/*.yml` --- one entry per published artefact (title,
  authors, preset, school, date, doi, summary, topic, pdf, thumbnail, pages,
  version). PDFs land in `public/outputs/pdf/`, thumbnails in
  `public/outputs/thumbs/`. `robots.txt` disallows `/outputs/pdf/` --- that's
  load-bearing (it keeps fabricated citations out of Google Scholar).
- `src/content/news/*.md` --- press releases; frontmatter `output:` references
  the outputs entry id.
- Landing pages (`/outputs/<id>/`) and the DOI resolver (`/doi/10.5555/...`) are
  generated from the outputs collection --- no per-output page authoring.

## Checks

Before any publish commit:
`pnpm typecheck && pnpm lint && pnpm lint:css && pnpm test && pnpm build` all
green, from this directory. A failed build means no publish --- never commit a
red state.
