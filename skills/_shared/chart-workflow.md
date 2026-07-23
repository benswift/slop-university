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
--- see the menu below for the file-per-type mapping, and
`examples/charts-gallery.typ` there for every one rendered on a page. Each
example wraps its `#plot` in `layout(size => plot(..., width: size.width, ...))`
so the figure fills its column --- copy that shape; don't copy the data, and
swap the examples' neutral `chart-theme(default-brand)` / local palettes for the
slop values below.

## Procedure

1. Author each chart as `{chart-folder}/chart-N.typ`: a gribouille `#plot`
   wrapped in `layout` so it fills whatever column it lands in, exported as
   `chart`. Theme and palettes come from the brand package. Use plausible data
   in plausible bands; chart type per the preset's variation roll. Skeleton:

   ```typst
   #import "@preview/gribouille:0.5.0": *
   #import "@local/slop-university-brand:0.1.0": (
     slop-theme-auto, slop-fill, slop-colour, slop-gold, slop-ink-auto,
     slop-ordinal-auto, slop-gold-tints,
   )

   #let data = ( /* inline records */ )

   #let chart = layout(size => plot(
     data: data,
     mapping: aes(/* ... */),
     layers: (/* geom-* */),
     scales: scales(/* colour: slop-colour(...) / fill: slop-fill(...) /
                       x: scale-continuous(...) --- keyed by aesthetic */),
     guides: guides(/* colour or fill: guide-legend(position: "top") */),
     labels: labels(x: none, y: "<axis title>", colour: none),  // no title -- it lives in the caption
     theme: slop-theme-auto,
     width: size.width,
     height: 0.34 * size.width,  // wide and short; ~0.3 poster, ~0.45 a roomier figure
   ))
   ```

   **Gribouille 0.5.0 API notes** (the 0.3.0-era names fail to compile):
   - `labels(...)` --- the old `labs(...)` was renamed.
   - `scales:` takes the keyed `scales(x: ..., colour: ..., fill: ...)` binder,
     not a positional tuple. Scale constructors are aesthetic-agnostic
     (`scale-continuous`, `scale-discrete`, `scale-gradient`, ...); the
     aesthetic comes from the `scales()` key. `slop-colour(...)` /
     `slop-fill(...)` return such specs --- key them explicitly:
     `scales(colour: slop-colour(...))`.
   - Typst gotcha (not gribouille): a `#let` binding ends at the line break, so
     a method chain split across lines (`#let order = data\n.sorted(...)`)
     silently binds only `data`. Keep derivations on one line or wrap the whole
     expression in parentheses.

2. Embed each chart in the document by importing it (see "Embedding"). No render
   step --- the chart renders when the document compiles.

3. Verify: compiling the document is the integration test; a gribouille error
   surfaces there. To check one chart in isolation before assembling, place it
   in a one-line scratch doc and compile it:
   `#import "/{chart-folder}/chart-1.typ": chart; #chart`.

## Chart types

Pick from this menu (all well-supported by gribouille and brand-themed). Each
maps to a worked example in the core package's `examples/charts/`. Each chart
type appears at most once per document --- and the corpus must not converge on
the same two or three types: **most runs should carry at least one chart from
the second table**, and a type you'd reach for by reflex (line, bar) needs a
reason the more specific form below doesn't fit.

The staples:

- **line** (`results.typ`) --- trends over time; one or several series.
- **area** (`area.typ`) --- a single-series trend with a filled body; a warmer,
  more emphatic register than a line.
- **grouped-bar** (`grouped-bar.typ`) --- compare a few categories across groups
  (`geom-col(position: "dodge")`).
- **stacked-bar** (`stacked-bar.typ`) --- composition. Normalise to 100%
  (`position: "fill"`, `format-percent()`) for parts of a whole (a Likert
  split); prefer **waffle** below when the whole is one population.
- **scatter** (`scatter.typ`) --- a relationship between two quantities, with an
  optional linear fit (`geom-smooth(method: "lm")`).
- **boxplot** (`boxplot.typ`) --- a distribution across categories; prefer
  **violin**, **ridgeline**, or **beeswarm** below when the shape of the
  distribution (or the individual observations) is the story.

The distinctive forms --- these carry the institutional-dashboard register the
satire wants, and they keep the corpus's figures from all looking alike:

- **ridgeline** (`ridgeline.typ`) --- overlapping density silhouettes, one per
  category (`geom-density-ridges`). Distributions across weekdays, cohorts,
  sites; handsome at poster scale.
- **violin** (`violin.typ`) --- mirrored densities per category (`geom-violin`);
  shows bimodality a boxplot hides.
- **beeswarm** (`beeswarm.typ`) --- every observation placed in a density-shaped
  swarm (`geom-beeswarm`); the honest form when n is small enough to show.
- **waffle** (`waffle.typ`) --- counts as unit cells (`stat-waffle` +
  `geom-tile`); parts-of-a-whole at dashboard glance. Uses `theme-void` with the
  brand text element restated (see the example).
- **bump** (`bump.typ`) --- ranks across rounds with sigmoid connectors
  (`stat-connect(connection: "sigmoid")`, reversed y); the league-table form,
  irresistible for anything the institution ranks.
- **dumbbell** (`dumbbell.typ`) --- before/after per category (`geom-segment` +
  two `geom-point` layers); the audit-vs-re-audit form.
- **lollipop** (`lollipop.typ`) --- a ranked magnitude per category, quieter
  than bars (`geom-segment` from zero + `geom-point`).
- **heatmap** (`heatmap.typ`) --- intensity over two categorical axes
  (`geom-tile` + `scale-gradient`); the occupancy/telemetry grid.
- **step** (`step.typ`) --- values that hold until revised (`geom-step`);
  thresholds, quotas, policy settings.
- **difference** (`difference.typ`) --- the signed band between two series
  (`stat-difference` + `geom-ribbon`); forecast-vs-actual, target-vs-observed.

## Chart styling

The brand package supplies the theme plus the brand palettes and two scale
helpers. **Always use the `-auto` exports in chart files** --- they follow the
document theme (`--input theme=dark` compiles the dark signage sibling from the
same source; without the flag they are exactly the light values), so a chart
authored once renders correctly in both variants. Use the helpers rather than
hard-coding hex:

- `slop-theme-auto` --- the chart theme (Public Sans; slop ink on a light grid
  normally, paper ink on a dimmed grid under the dark flag). The fixed
  `slop-theme` / `slop-theme-dark` exist but chart files shouldn't pin them.
- `slop-categorical-auto` --- slop gold, ink (black on light pages, paper on
  dark), a gold tint, a mid-grey, **in that order** (the two-ink register: gold
  and ink lead, tints extend). For distinct series (line, scatter, grouped bar).
  Most charts need only the gold/ink pair; the helper takes the first N.
- `slop-ordinal-auto` --- a greyscale ramp for ordered bar categories (a Likert
  ramp); black-anchored on light pages, white-anchored on dark.
- `slop-gold-tints` --- a single-hue slop-gold ramp. For a sequential
  single-series breakdown (warm parts-of-a-whole). One ramp serves both themes.
- `slop-ink-auto` --- the page-ground ink for hardcoded strokes and outlines
  (e.g. `geom-boxplot(colour: ...)`): house ink on light pages, paper on dark.
  Never hardcode `slop-ink` in a chart file for this job.
- `slop-fill(levels, palette: ...)` / `slop-colour(levels, palette: ...)` ---
  map a palette onto a discrete scale's levels, in the order you pass them; key
  the result by aesthetic in `scales(...)`. Default palette is
  `slop-categorical-auto`; pass `palette: slop-ordinal-auto` (or
  `slop-gold-tints`) for a ramp.

**Line / scatter / bump (few, distinct series):** map the series to `colour` and
add `scales(colour: slop-colour(("Series A", "Series B")))` --- gold then ink,
distinct for clear separation. A single-series line wants no `colour` aesthetic;
draw it in gold directly (`geom-line(colour: slop-gold)`,
`geom-point(..., fill: slop-gold)`).

**Bars (especially stacked):** use a single-hue ramp, not the multi-colour
categorical palette --- the categorical palette reads as visual chaos on bars
whose categories aren't strongly distinct. Pass `palette: slop-ordinal-auto`
(the conservative choice, when the chart is the document's data spine and
shouldn't compete) or `palette: slop-gold-tints` (warmer, on-brand, for positive
framings) to `slop-fill`. A **grouped** bar comparing genuinely distinct
entities is the exception --- `slop-categorical-auto` is fine there. The
**waffle** takes the same guidance: `slop-gold-tints` for a warm single-story
composition, `slop-categorical-auto` when the segments are genuinely distinct
things.

**Parts of a whole:** a **waffle** (`stat-waffle`, `palette: slop-gold-tints`)
or a normalised stacked bar --- `geom-col(position: "fill")` with
`scales(y: scale-continuous(labels: format-percent()))` and
`palette: slop-gold-tints` --- primary tints are preferred over reaching for
extra hues. (A ranked **lollipop** is the alternative when one quantity
dominates; gribouille has no doughnut, by design.)

**Distributions (ridgeline / violin / beeswarm):** single-hue --- fill or point
in `slop-gold` with `alpha: ~0.55-0.85` and any outline in `slop-ink-auto`. Fill
by category (`slop-fill` + tints) only when categories genuinely need
distinguishing beyond their axis position.

**Heatmap:** a continuous white-to-gold gradient ---
`scales(fill: scale-gradient(low: <near-paper>, high: slop-gold))`; on dark runs
the low end can stay light (the framed-print look is the house idiom). See
`heatmap.typ` for the discrete-axis pinning.

**Dumbbell / lollipop / difference:** connective furniture (segments, bands
against a baseline) in mid-grey (`slop-colors.grey-3`) or gold tints; the
emphasis point/series in `slop-gold`; a "before" or baseline point in
`slop-ink-auto`.

**Legends:** position on `top` or `bottom`, never the sides --- a side legend
eats the horizontal space these wide-short charts need. Attach by the mapped
aesthetic: `guides(colour: guide-legend(position: "top"))` for a line/scatter,
`guides(fill: guide-legend(position: "bottom", ncolumn: N))` for bars. A
single-series chart needs no legend. Suppress the legend _title_ with the
matching `labels` key set to `none` (`labels(..., colour: none)` /
`fill: none`).

**Title:** pass the chart's heading via `labels(title: ...)` if you want one,
but supplementary context --- including a commitment-shaped chart annotation's
falsifiable claim --- goes in the typst `caption: [...]`, not the chart title.
**On the dense research poster, omit `title` entirely** --- the caption carries
everything and a title only adds height.

**Sizing.** The `layout(size => plot(width: size.width, ...))` wrapper makes the
chart fill the width of whatever column it's placed in --- no fixed width, no
"design wide then display at 100%" dance, no upscaling. The one knob is the
**aspect**: set `height` as a fraction of `size.width`. Wide and short reads
best for a column figure --- **~0.3 for a dense poster**, up to ~0.45 for a
roomier report figure. A bar chart with a bottom legend wants a touch more
height than a line; a heatmap wants enough height for its rows to stay near
square.

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
- **`unknown variable: labs` / `expected string, found dictionary` in scale
  training**: 0.3.0-era API from memory. `labs` is `labels` since 0.4.0, and
  `scales:` takes the keyed `scales(...)` binder since 0.5.0 --- a positional
  tuple (or a limits list that accidentally bound whole records; see the
  `#let`-line-break gotcha in step 1) produces exactly these errors.
- **Year axis shows `2,024`**: a quantitative year picks up thousands
  separators. Format it plainly with
  `scales(x: scale-continuous(labels: format-number(big-mark: "", digits: 0)))`.
- **Two legends appear** (scatter/line with both `colour` and `fill` mapped):
  suppress the duplicate in `guides` --- e.g.
  `guides(colour: guide-legend(...), fill: none)`.
- **Categorical x-axis in the wrong order** (months, quarters, ordinal stages):
  gribouille sorts string categories alphabetically, so a March-to-August series
  plots Apr/Aug/Jul/Jun/Mar/May. Pin the order with
  `scales(x: scale-discrete(limits: ("Mar", "Apr", "May", "Jun", "Jul", "Aug")))`
  (the levels in plot order).
- **Lollipop/dumbbell stems missing under `coord-flip`**: don't flip --- author
  them horizontally instead (discrete aesthetic on `y`, segments mapped
  `x`/`xend`), as the worked examples do.
- **Chart bleeds past its column** (poster / multi-column layouts): it was
  placed with a bare `#figure(...)` instead of `slop-inline-figure` /
  `chartfig`. The template's full-bleed figure rule pads negative-right to the
  page edge; inside a column that overflows into the gutter.
