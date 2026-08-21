# Slop University course catalogue

Dormant build for `courses.slop.university`. It validates and ingests the
versioned `/api/index.json` emitted by published course sites, rejects duplicate
`SLOPxxxx` codes with reroll guidance, and provides progressive-enhancement
search and level filtering.

`src/data/sources.json` is the publication registry (`apiUrl`, `sourceUrl`). Run
`pnpm catalogue:sync` to refresh the checked-in catalogue, then the normal
typecheck/test/lint/format/build suite. No workflow, CNAME or DNS is included
yet: activation is intentionally a separate release gate.

The canonical URL contract reserves `https://courses.slop.university/SLOPxxxx/`.
Serving the complete student sites at those paths requires an origin mirror or
reverse proxy; do not activate the canonical URLs until that layer exists.
