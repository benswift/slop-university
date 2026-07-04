# Slop University --- brand assets

A standalone lockup for the fictional **Slop University** (the project lives at
`slop.university`). It replaces the earlier "Australian National Slopiversity"
mark, which spliced the real ANU wordmark + crest; this one is drawn from
scratch, so it no longer parodies a specific institution --- it just reads as a
plausible university lockup whose name is the joke.

The mark: a heater shield containing a **steaming bowl** (slop), with a one-line
**"Slop / University"** wordmark (Public Sans Medium, gold slash). Gold is
`#b97d1c`, ink is `#1a1a1a` black / `#ffffff` white, all in Public Sans. The
crest is single-weight gold line-art to match the classic line-art crest style;
the documents still read straight --- the brand is the joke.

## Where the brand lives

The lockup ships inside `brand/slop-university-brand/0.1.0/` --- a typst package
(`@local/slop-university-brand:0.1.0`) that layers the Slop University brand
over `university-typst-template`, the de-branded layout core (in the
`anu-typst-template` repo under `packages/`). The brand package owns the palette
(built from the lockup gold via `make-palette`, ink pinned to `#1a1a1a`), the
four lockup SVGs, the masthead placement geometry, and the gribouille chart
values (`slop-theme`, `slop-categorical`, `slop-ordinal`, `slop-gold-tints`,
`slop-colour` / `slop-fill`). Generated documents import the brand package only;
nothing slop-branded lives in the ANU template from 0.3.0 (the frozen 0.2.0
still carries the old `lockup: "slop"` branch so pre-split outputs re-compile).

This directory keeps the _generator_ toolchain.

## Files

- `lockup-gen.typ` --- the generator. Crest drawn natively as one gold-stroke
  `curve` (so it exports as vector, not a rasterised embed); wordmark is Public
  Sans, outlined to paths by typst's SVG export. `--input variant=black|white`.
- `svgo.config.mjs` --- svgo config; **keeps the viewBox** (see file comment ---
  losing it breaks masthead placement).
- `build-all.sh` --- canonical entry point: compiles both variants, runs svgo,
  and installs the four SVGs into the brand package's `logos/`.

## Regenerating

```sh
./build-all.sh
```

Needs Public Sans (`$PUBLIC_SANS_PATH`, default
`~/.local/share/fonts/PublicSans-static`) and writes into the brand package
logos dir (`$SLOP_BRAND_LOGOS`, default
`../../brand/slop-university-brand/0.1.0/logos`). Both env vars are overridable.

## Masthead placement (the `slop` lockup entry in the brand package)

The lockup viewBox is `0 0 285.658 56.693`; rendered at `height: 1.64cm` the
crest's symmetry axis (box centre, `u(40)`) sits `0.656cm` in from the art's
left edge. With the gold rule centre at `1.9132cm` and the art left-aligned:

```
dx = 1.9132cm - 0.656cm = 1.2564cm
```

The one-line wordmark makes the art **~8.3cm wide** at masthead height (vs
~5.2cm for the old one-word mark), so the lockup entry's masking rect
(`mast-width`) is `8.7cm` to clear it. The rect is `bg-color`, so it is
invisible on a solid first page. On a full-bleed image cover it would show as a
pale block behind the wordmark --- revisit with a compact (stacked or
crest-only) masthead variant if that case matters.

These values live as data in the brand package's lockup entry (`mast-width`,
`mast-dx`, `mast-align`, `back-width`); masthead (`slop-secondary`) + back cover
(`slop-primary`). All three satirical presets brand with the slop package; the
faithful from-source path keeps the genuine `anu` / `anu-socy` via
`@local/anu-typst-template`.
