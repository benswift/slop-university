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
- **Every image goes through the Astro pipeline (`astro:assets`).** Import from
  `src/` (or resolve via an `import.meta.glob` helper) and render with `<Image>`
  or a theme component (`Hero`, `Card`) --- never a raw `<img src>` at a
  `public/` path. `public/` holds only the download PDFs.
- **Every page carries a hero.** Heroes are landscape 16:9, resolved by id/name
  and rendered by the theme via `ContentLayout heroImage=` (or `Hero` directly).
  Resolvers live in `src/lib/heroes.ts`: `pageHero(name)` for standalone/index
  pages (`src/assets/heroes/<name>.avif`), `outputHero(id)` for outputs
  (`src/assets/heroes/outputs/<id>.avif`, reused on the announcing news post),
  and `personHero(id)` / `schoolHero(id)` for canon profiles
  (`canon/heroes/{people,schools}/<id>.avif`, generated with the headshot as a
  reference so the researcher appears in a landscape scene). A missing hero
  resolves to `undefined` and the page falls back to a plain `<h1>`, so pages
  render before their art exists.
- Longer pages may break up the text with the occasional inline image. In
  markdown, reference it by a **relative** path (`![alt](./foo.avif)`) so it
  routes through the pipeline --- never an absolute `public/` path or a remote
  URL.
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
  optional subtitle, authors, preset, school, date, doi, summary, topic, pdf,
  pages, version). `title` is the main/head title and `subtitle` the optional
  deck; the two rejoin with ": " (`fullTitle` in `src/lib/outputs.ts`) for the
  citation, document `<title>`, DOI resolver, and announcing news post. Only the
  PDF lives in `public/` (`public/outputs/pdf/`); `robots.txt` disallows
  `/outputs/pdf/`, which is load-bearing (it keeps fabricated citations out of
  Google Scholar). The first-page thumbnail and the landscape hero are pipeline
  assets under `src/assets/outputs/thumbs/<id>.avif` and
  `src/assets/heroes/outputs/<id>.avif`, resolved by basename === entry id (no
  yml field), via `src/lib/thumbnails.ts` and `src/lib/heroes.ts`.
- `src/content/news/*.md` --- press releases; frontmatter `output:` references
  the outputs entry id.
- Landing pages (`/outputs/<id>/`) and the DOI resolver (`/doi/10.5555/...`) are
  generated from the outputs collection --- no per-output page authoring.

## Checks

Before any publish commit:
`pnpm typecheck && pnpm lint && pnpm lint:css && pnpm test && pnpm build` all
green, from this directory. A failed build means no publish --- never commit a
red state.
