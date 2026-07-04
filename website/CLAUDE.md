# website/ --- slop.university

The public face of Slop University: an Astro site consuming
`astro-theme-university` (pinned release tag) with the `slopBranding` preset in
`src/site-config.ts`. The repo-level `CLAUDE.md` satire rules apply to
everything here; this file adds the doctrine for the autonomous publish agent,
which grows this site over time.

## Hard floors (mechanically enforced --- the push wrapper validates every

## publish commit against a path allowlist; violating paths are reset)

- **Never edit** `.github/workflows/`, `public/CNAME`, `public/robots.txt`, or
  the doctrine files (this file, the repo `CLAUDE.md`, `skills/`).
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

Everything else: researcher profile pages (from the roster, with their
`canon/headshots/` portraits), school and department pages, an about page, the
research-performance dashboard, news posts and output entries (the /publish
pipeline's main job). New pages go in `src/content/pages/` (rendered by the
`[...slug].astro` route) or as new routes under `src/pages/`.

- All imagery follows the two-ink house style
  (`skills/_shared/visual-style.md`), generated via `references/slop-style/`. No
  stock photos, no off-style one-offs.
- Any chart on a web page is Vega-Lite in the theme colours (`--at-primary`
  gold, ink, greys) --- never library-default palettes. Generated PDFs keep
  using gribouille; that pipeline is unchanged.
- Voice: pages stay in the institutional register (`skills/from-preset/`
  `genre.md`); news posts use the comms register (`skills/publish/comms.md`).

## Content model

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
`pnpm typecheck && pnpm lint && pnpm lint:css && pnpm build` all green, from
this directory. A failed build means no publish --- never commit a red state.
