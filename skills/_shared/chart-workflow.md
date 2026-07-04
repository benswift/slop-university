# Shared: chart workflow (native gribouille, inline)

Cross-cutting chart doctrine for any preset whose blueprint declares charts (the
blueprint's chart section is authoritative). The calling preset cross-refs this
file in its chart-generation step and supplies: (a) the chart-folder path (used
as `{chart-folder}` below --- e.g. `output/slop-impact-<slug>-<seed>-charts` or
`output/slop-poster-<slug>-<seed>-charts`), (b) the chart count and the type for
each chart (drawn from the menu in "Chart types" below), and (c) where each
chart embeds in the typst source.

Charts are drawn natively with [gribouille](https://m.canouil.dev/gribouille), a
grammar-of-graphics package for typst. Each chart is a small `.typ` file holding
one `#plot`; the document **imports it and renders it inline** --- there is no
SVG, no separate render step, and no Python / `uv` / `vl-convert`. The only
toolchain is typst itself. Brand typography and palette come straight from the
brand package (`@local/slop-university-brand:0.1.0` --- no theme file to copy);
chart text is Public Sans because the theme sets it.

Worked examples (one per chart type) live in the de-branded core package:
`~/.local/share/typst/packages/local/university-typst-template/0.1.0/examples/charts/`
--- `results.typ` = line, `scatter.typ`, `grouped-bar.typ`, `stacked-bar.typ`,
`area.typ`, `boxplot.typ`. Each wraps its `#plot` in
`layout(size => plot(..., width: size.width, ...))` so the figure fills its
column --- copy that shape; don't copy the data, and swap the examples' neutral
`chart-theme(default-brand)` / local palettes for the slop values below.

## Procedure

1. Author each chart as `{chart-folder}/chart-N.typ`: a gribouille `#plot`
   wrapped in `layout` so it fills whatever column it lands in, exported as
   `chart`. Theme and palettes come from the brand package. Use plausible data
   in plausible bands; chart type per the preset's variation roll. Skeleton:

   ```typst
   #import "@preview/gribouille:0.3.0": *
   #import "@local/slop-university-brand:0.1.0": (
     slop-theme, slop-fill, slop-colour, slop-gold, slop-ink, slop-ordinal,
     slop-gold-tints,
   )

   #let data = ( /* inline records */ )

   #let chart = layout(size => plot(
     data: data,
     mapping: aes(/* ... */),
     layers: (/* geom-* */),
     scales: (/* slop-colour(...) / slop-fill(...) / scale-*-continuous(...) */),
     guides: guides(/* colour or fill: guide-legend(position: "top") */),
     labs: labs(x: none, y: "<axis title>", colour: none),  // no title -- it lives in the caption
     theme: slop-theme,
     width: size.width,
     height: 0.34 * size.width,  // wide and short; ~0.3 poster, ~0.45 a roomier figure
   ))
   ```

2. Embed each chart in the document by importing it (see "Embedding"). No render
   step --- the chart renders when the document compiles.

3. Verify: compiling the document is the integration test; a gribouille error
   surfaces there. To check one chart in isolation before assembling, place it
   in a one-line scratch doc and compile it:
   `#import "/{chart-folder}/chart-1.typ": chart; #chart`.

## Chart types

Pick from this menu (all well-supported by gribouille and brand-themed). Each
maps to a worked example in the core package's `examples/charts/`:

- **line** (`results.typ`) --- trends over time; one or several series.
- **area** (`area.typ`) --- a single-series trend with a filled body; a warmer,
  more emphatic register than a line.
- **grouped-bar** (`grouped-bar.typ`) --- compare a few categories across groups
  (`geom-col(position: "dodge")`).
- **stacked-bar** (`stacked-bar.typ`) --- composition. Normalise to 100%
  (`position: "fill"`, `format-percent()`) for **parts of a whole** --- this is
  the replacement for the old doughnut, which gribouille (being Cartesian) has
  no clean way to draw.
- **scatter** (`scatter.typ`) --- a relationship between two quantities, with an
  optional linear fit (`geom-smooth(method: "lm")`).
- **boxplot** (`boxplot.typ`) --- a distribution across categories.

Each chart type appears at most once per document.

## Chart styling

The brand package supplies the theme (`slop-theme` --- Public Sans, slop ink, a
light-grey grid) plus the brand palettes and two scale helpers. Use the helpers
rather than hard-coding hex:

- `slop-categorical` --- slop gold, ink black, a gold tint, a mid-grey, **in
  that order** (the two-ink register: gold and ink lead, tints extend). For
  distinct series (line, scatter, grouped bar). Most charts need only the
  gold/ink pair; the helper takes the first N.
- `slop-ordinal` --- a black greyscale ramp (dark → light). For ordered bar
  categories (a Likert ramp).
- `slop-gold-tints` --- a single-hue slop-gold ramp. For a sequential
  single-series breakdown (warm parts-of-a-whole).
- `slop-fill(levels, palette: ...)` / `slop-colour(levels, palette: ...)` ---
  map a palette onto a discrete scale's levels, in the order you pass them.
  Default palette is `slop-categorical`; pass `palette: slop-ordinal` (or
  `slop-gold-tints`) for a ramp.

**Line / scatter (few, distinct series):** map the series to `colour` and add
`slop-colour(("Series A", "Series B"))` --- gold then ink, distinct for clear
separation. A single-series line wants no `colour` aesthetic; draw it in gold
directly (`geom-line(colour: slop-gold)`, `geom-point(..., fill: slop-gold)`).

**Bars (especially stacked):** use a single-hue ramp, not the multi-colour
categorical palette --- the categorical palette reads as visual chaos on bars
whose categories aren't strongly distinct. Pass `palette: slop-ordinal` (the
conservative choice, when the chart is the document's data spine and shouldn't
compete) or `palette: slop-gold-tints` (warmer, on-brand, for positive framings)
to `slop-fill`. A **grouped** bar comparing genuinely distinct entities is the
exception --- `slop-categorical` is fine there.

**Parts of a whole (the old doughnut's job):** a normalised stacked bar ---
`geom-col(position: "fill")` with `scale-y-continuous(labels: format-percent())`
and `palette: slop-gold-tints` --- primary tints are preferred over reaching for
extra hues. (A ranked horizontal bar via `coord-flip()` is the alternative when
one quantity dominates.)

**Legends:** position on `top` or `bottom`, never the sides --- a side legend
eats the horizontal space these wide-short charts need. Attach by the mapped
aesthetic: `guides(colour: guide-legend(position: "top"))` for a line/scatter,
`guides(fill: guide-legend(position: "bottom", ncolumn: N))` for bars. A
single-series chart needs no legend. Suppress the legend _title_ with the
matching `labs` key set to `none` (`labs(..., colour: none)` / `fill: none`).

**Title:** pass the chart's heading via `labs(title: ...)` if you want one, but
supplementary context --- including a commitment-shaped chart annotation's
falsifiable claim --- goes in the typst `caption: [...]`, not the chart title.
**On the dense research poster, omit `title` entirely** --- the caption carries
everything and a title only adds height.

**Sizing.** The `layout(size => plot(width: size.width, ...))` wrapper makes the
chart fill the width of whatever column it's placed in --- no fixed width, no
"design wide then display at 100%" dance, no upscaling. The one knob is the
**aspect**: set `height` as a fraction of `size.width`. Wide and short reads
best for a column figure --- **~0.3 for a dense poster**, up to ~0.45 for a
roomier report figure. A bar chart with a bottom legend wants a touch more
height than a line.

## Embedding in typst

The document imports each chart and drops it into the brand package's
`slop-inline-figure` (or the poster's `chartfig`), which keeps the figure within
the text column instead of bleeding to the right page edge. The chart is
content, not an image path:

```typst
#import "/{chart-folder}/chart-1.typ": chart

#slop-inline-figure(
  chart,
  caption: [<chart caption --- a falsifiable claim belongs here, not in the chart title>],
)
```

For more than one chart in a document, alias each on import so the names don't
collide:

```typst
#import "/{chart-folder}/chart-1.typ": chart as chart-1
#import "/{chart-folder}/chart-2.typ": chart as chart-2
```

Import paths are project-root-relative (leading slash + the `output/` prefix ---
e.g. `/output/slop-poster-<slug>-<seed>-charts/chart-1.typ`), matching how
images are referenced elsewhere; the document is compiled with
`typst compile --root .`.

## Common failure modes

- **Chart fails to compile**: read the typst error --- it surfaces when the
  document compiles, since the chart renders inline. The usual cause is a
  gribouille syntax slip (compare against the worked example for that chart type
  in the core package's `examples/charts/`); the next is importing chart helpers
  under the examples' neutral names instead of the brand package's `slop-*`
  names. Isolate a suspect chart with the scratch-compile in step 3.
- **Year axis shows `2,024`**: a quantitative year picks up thousands
  separators. Format it plainly with
  `scale-x-continuous(labels: format-number(big-mark: "", digits: 0))`.
- **Two legends appear** (scatter/line with both `colour` and `fill` mapped):
  suppress the duplicate in `guides` --- e.g.
  `guides(colour: guide-legend(...), fill: none)`.
- **Categorical x-axis in the wrong order** (months, quarters, ordinal stages):
  gribouille sorts string categories alphabetically, so a March-to-August series
  plots Apr/Aug/Jul/Jun/Mar/May. Pin the order with
  `scale-x-discrete(limits: ("Mar", "Apr", "May", "Jun", "Jul", "Aug"))` (the
  levels in plot order).
- **Chart bleeds past its column** (poster / multi-column layouts): it was
  placed with a bare `#figure(...)` instead of `slop-inline-figure` /
  `chartfig`. The template's full-bleed figure rule pads negative-right to the
  page edge; inside a column that overflows into the gutter.
