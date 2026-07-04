// The Slop University brand layer over university-typst-template (the
// de-branded core). Mirrors the website's slopBranding arrangement: the core
// owns layout, this package owns identity. The lockup is a from-scratch
// design (see assets/slop-university/NOTES.md in this repo); nothing here
// derives from any real institution's marks.
#import "@local/university-typst-template:0.1.0" as _uni
#import "@local/university-typst-template:0.1.0": (
  chart-colour, chart-fill, chart-theme, greyscale-ordinal, inline-figure,
  make-palette,
)

// The two inks (plus paper) of the house style: lockup gold and ink black.
#let slop-gold = rgb("#b97d1c")
#let slop-ink = rgb("#1a1a1a")

// Palette derived from the lockup gold; dark-grey is pinned to the house ink
// so chart ink and dark-theme surfaces sit on the two-ink register. `gold`
// is the name the doctrine uses, aliased onto the semantic key.
#let slop-colors = (
  make-palette(slop-gold)
    + (
      dark-grey: slop-ink,
      gold: slop-gold,
    )
)

// Lockup artwork, read once as bytes so the core can render it (paths
// resolve here, inside this package). Regenerate via
// assets/slop-university/build-all.sh.
#let _logo(name) = read("logos/" + name + ".svg", encoding: none)

// Rotated "Office of Research Outputs" wordmark in the bottom-left margin
// --- the producing unit credited on posters and papers (see
// canon/schools.md). The ornament key stays "studio" (the mechanism came
// from the ANU layer) so `logos: ("studio",)` keeps working.
#let _studio-ornament(bg-color, dark) = pdf.artifact(place(
  left + bottom,
  dx: 1.6cm,
  dy: -2cm,
  rotate(
    -90deg,
    origin: bottom + left,
    text(
      font: ("Public Sans", "DejaVu Sans"),
      size: 12pt,
      fill: if dark { slop-colors.primary-2 } else { slop-colors.grey-3 },
    )[Office of Research Outputs],
  ),
))

// Masthead placement geometry (derivation in assets/slop-university/
// NOTES.md): viewBox 0 0 285.658 56.693, so at 1.64cm the crest axis sits
// 0.656cm in from the left edge; left-aligned art gives dx = 1.9132 - 0.656
// = 1.2564cm, and the ~8.3cm-wide one-line wordmark needs an 8.7cm mask.
// The lockup is one horizontal mark; masthead and back cover share the
// artwork.
#let _art = (
  black: _logo("slop-horizontal-gold-black"),
  white: _logo("slop-horizontal-gold-white"),
)
#let slop-brand = (
  name: "Slop University",
  fonts: (
    body: ("Public Sans", "DejaVu Sans"),
    code: ("Monaspace Argon", "DejaVu Sans Mono"),
  ),
  colors: slop-colors,
  default-lockup: "slop",
  lockups: (
    slop: (
      masthead: _art,
      primary: _art,
      mast-width: 8.7cm,
      mast-dx: 1.2564cm,
      mast-align: left,
    ),
  ),
  ornaments: (
    studio: (scope: "every-page", render: _studio-ornament),
  ),
)

// The core API with the slop brand applied, slop-prefixed. Only the helpers
// the presets actually use are exported; grow this list with the presets.
#let slop = _uni.university.with(brand: slop-brand)
#let slop-back-cover = _uni.back-cover.with(brand: slop-brand)
#let slop-highlight-card = _uni.highlight-card.with(brand: slop-brand)
#let slop-qr-code = _uni.qr-code.with(brand: slop-brand)
#let slop-inline-figure = inline-figure

// The lockup as bare artwork (no masking rect) for overlaying on imagery ---
// e.g. the poster feature-top hero band. Needs a dark backing to read.
#let slop-lockup(variant: "white", height: 1.64cm) = _uni.lockup(
  brand: slop-brand,
  name: "slop",
  variant: variant,
  height: height,
)

// --- Gribouille chart styling ---

// The brand chart theme (Public Sans, slop ink, light-grey grid).
#let slop-theme = chart-theme(slop-brand)

// Chart palettes, on the two-ink register: gold and ink lead; a gold tint
// and a mid-grey extend to four series without leaving the house palette.
#let slop-categorical = (
  slop-gold,
  slop-ink,
  slop-colors.primary-2,
  slop-colors.grey-3,
)
// Ordinal: black greyscale ramp (dark -> light) for ranked/Likert series.
#let slop-ordinal = greyscale-ordinal
// Sequential single-hue: slop gold tints (100% -> ~10%) for parts of a
// whole.
#let slop-gold-tints = (
  slop-gold,
  color.mix((slop-gold, 75%), (white, 25%)),
  color.mix((slop-gold, 50%), (white, 50%)),
  color.mix((slop-gold, 28%), (white, 72%)),
  color.mix((slop-gold, 10%), (white, 90%)),
)

// Map the first N brand colours onto a discrete aesthetic. Pass the factor
// levels in the order you want them coloured; override `palette` for a
// different ramp (e.g. slop-ordinal, slop-gold-tints).
#let slop-colour(levels, palette: slop-categorical) = chart-colour(
  levels,
  palette,
)
#let slop-fill(levels, palette: slop-categorical) = chart-fill(levels, palette)
