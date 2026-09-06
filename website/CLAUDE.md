# website/ --- slop.university

The public face of Slop University: an Astro site consuming
`astro-theme-university` (pinned release tag) with the `slopBranding` preset
from `astro-theme-slop` (the extracted web brand package, also git-pinned),
spread into the site config in `src/site-config.ts`. The repo-level `CLAUDE.md`
satire rules apply to everything here; this file adds the doctrine for the
autonomous publish agent, which grows this site over time.

## Hard floors

Mechanically enforced: the push wrapper validates every publish commit against a
path allowlist, and resets violating paths.

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
  partners. Two carve-outs. **Internal award values**: a dollar figure on a
  grant or prize from a `canon/grants.yml` scheme is fiction-internal (the
  funder is a Slop University body; there is no registry to check it against)
  and may be stated exactly. **The University's ranking claim** (the homepage
  line, `/girt/`, and the human-authored recognition news post): checkable, and
  it checks out against the self-published GIRT table and The World University
  Index. All three surfaces are human-maintained --- the tick never edits
  `girt.md` and never states a ranking itself (`skills/publish/comms.md`).
- **No real people.** Every named person comes from `canon/roster.yml` (with
  their canonical title and school); every org unit from `canon/schools.yml`.
  The single exception is the Vice-Chancellor in `canon/leadership.yml`, who is
  a real person (the artist) and is therefore outside the roster and outside the
  tick's reach: never credit him with an output, a grant, or a quote, never add
  a second leadership entry, and in page prose name the office rather than the
  occupant. His profile page already exists; the agent does not edit it.
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
- **Grants and prizes** --- award entries (`src/content/grants/`) from the
  schemes in `canon/grants.yml`, each announced by a news post (the 2I rung).
  The schemes themselves are human-added only --- `canon/grants.yml` is outside
  the wrapper's allowlist.

The research-performance dashboard and the page routes under `src/pages/` are
built by hand, not grown by the tick.

- All imagery follows the two-ink house style
  (`skills/_shared/visual-style.md`), generated via `references/slop-style/`. No
  stock photos, no off-style one-offs.
- **Every page carries a hero**, landscape 16:9, rendered by the theme via
  `ContentLayout heroImage=` (or `Hero` directly). The slow-growing families ---
  page, person and school heroes, plus roster headshots --- go through
  `astro:assets` and resolve by id: `pageHero(name)`, `personHero(id)` and
  `schoolHero(id)` in `src/lib/heroes.ts`, `headshot(id)` in
  `src/lib/headshots.ts`. The per-tick families (output heroes, news heroes,
  output thumbnails) are pre-encoded into the `img.slop.university` bucket, and
  their URLs derive from the entry id plus the dims recorded in frontmatter
  (`src/lib/images.ts`). A missing hero resolves to `undefined` and the page
  falls back to a plain `<h1>`, so pages render before their art exists.
- Longer pages may break up the text with the occasional inline image. In
  markdown, reference it by a **relative** path (`![alt](./foo.avif)`) so it
  routes through the pipeline --- never an absolute `public/` path or a remote
  URL. `public/` holds only `CNAME` and `robots.txt`.
- Any chart on a web page is Vega-Lite in the theme colours --- never
  library-default palettes. Generated PDFs use gribouille instead.
- Voice: pages stay in the institutional register (`skills/from-preset/`
  `genre.md`); news posts use the comms register (`skills/publish/comms.md`).

## Content model

- `people` and `schools` collections load the canon **in place** from
  `../canon/roster.yml` and `../canon/schools.yml` (see `src/content.config.ts`;
  the schema is the shape enforcement). A third collection, `leadership`, loads
  `../canon/leadership.yml` on the same schema; `getPeople()` unions it with
  `people` for the `/people/` pages, while everything resolving an author or
  grantee reads the roster alone. That split is the mechanical guarantee that a
  run drawing authors "from `canon/roster.yml`" can never reach the real person
  in `leadership.yml`, and the content test asserts it. There are no
  people/school files under `src/` --- editing the canon is how those pages
  change. Headshots resolve from `canon/headshots/` via `src/lib/headshots.ts`.
  The content test (`src/content/content.test.ts`) enforces the seams: output
  authors and schools must exist in the canon.
- `src/content/outputs/*.yml` --- one entry per published artefact; the schema
  in `src/content.config.ts` is the field list. `title` is the main/head title
  and `subtitle` the optional deck; the two rejoin with ": " (`fullTitle` in
  `src/lib/outputs.ts`) for the citation, document `<title>`, DOI resolver, and
  announcing news post. `publishedAt` is the exact wrapper timestamp used to
  order same-day signage candidates; `date` remains the human-facing publication
  date. No entry stores a URL: the PDF (`src/lib/pdfs.ts`), hero and thumbnail
  (`src/lib/images.ts`) all derive from the entry id, and only the images'
  intrinsic dims are recorded.
- `src/content/news/*.md` --- press releases; frontmatter `output:` references
  the outputs entry id. `title` is the punchy headline (hero h1 and listing
  card); the optional `subtitle` renders as a deck beneath the hero (mirroring
  the output landing page), carrying the specificity the headline trims.
  `description` is the card body and social/meta text --- not shown on the post
  itself. A grant announcement instead carries `grant:` (the grants entry id);
  the post appends the award's details box and is the award's public record. A
  post announcing an output shows that output's hero; a post announcing a grant,
  or announcing nothing (an institutional notice), records its own `hero:` dims.
- `src/content/grants/*.yml` --- one entry per awarded grant or prize
  (`<date>-<slug>.yml`: name, scheme, date, grantees, value, summary), each
  referencing a scheme in `canon/grants.yml` (loaded in place as the
  `grantSchemes` collection). No per-grant pages: grants render on people
  profiles ("Grants and awards" + the research-income indicator), on the output
  landing pages that attach them (outputs frontmatter `grants:` list), and on
  the outputs dashboard (funding tiles and chart). The content test enforces the
  seams: grantees resolve to roster pages, schemes exist in the canon, and
  attached grants exist and predate their outputs.
- Landing pages (`/outputs/<id>/`) and the DOI resolver (`/doi/10.5555/...`) are
  generated from the outputs collection --- no per-output page authoring.

## Checks

Before any publish commit, from this directory:
`pnpm lint && pnpm typecheck && pnpm test && pnpm build` all green (`lint` runs
`lint:css`). A failed build means no publish --- never commit a red state.
