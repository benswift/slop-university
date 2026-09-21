// The Slop University brand layer over university-typst-template (the
// de-branded core). Mirrors the website's slopBranding arrangement: the core
// owns layout, this package owns identity. The lockup is a from-scratch
// design (see assets/slop-university/NOTES.md in this repo); nothing here
// derives from any real institution's marks.
#import "@local/university-typst-template:0.1.0" as _uni
#import "@local/university-typst-template:0.1.0": (
  chart-colour, chart-fill, chart-theme, greyscale-ordinal,
  greyscale-ordinal-dark, inline-figure, make-palette,
)

// The document theme, read once from the CLI: `--input theme=dark` renders
// the dark variant (the signage artefact); absent means light, so every
// existing document and plain `typst compile` is unchanged. Documents pass
// this straight through as `config: (theme: slop-doc-theme)`; the `-auto`
// chart exports below key off the same value, so one flag themes the whole
// compilation.
#let slop-doc-theme = sys.inputs.at("theme", default: "light")
#let _slop-dark = slop-doc-theme == "dark"

// The university motto (canon/institution.md): "we publish, therefore we
// are". Set in italics, untranslated; covers and back pages only, sparingly.
#let slop-motto = "Edimus ergo sumus"

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

// Theme-following semantic colours for run-authored content. "Ink" is
// whatever contrasts with the page ground (house ink on light, paper on
// dark); "muted" is the de-emphasised grey for captions, credits, and
// footnote-register text.
#let slop-ink-auto = if _slop-dark { slop-colors.white } else { slop-ink }
#let slop-muted-auto = if _slop-dark { slop-colors.grey-2 } else {
  slop-colors.grey-4
}

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

// Overlay masthead for image bands (the poster feature-top hero): the gold
// spine drawn in two segments with the bare lockup in the gap between them,
// crest axis on the spine --- see `overlay-masthead` in the core. This is
// what the feature-top skeleton uses; it replaces placing `slop-lockup` and
// a continuous spine rect by hand (the spine showed through the crest's open
// line-art).
#let slop-overlay-masthead = _uni.overlay-masthead.with(
  brand: slop-brand,
  name: "slop",
)

// The dx that places a left-aligned `slop-lockup` so its crest axis sits on
// the brand spine (the rule at 1.9cm, 0.75pt wide, so centre 1.9132cm).
// Superseded by `slop-overlay-masthead` (which also breaks the spine around
// the lockup); kept exported so already-generated outputs in `output/` still
// compile.
#let _spine-x = 1.9cm + 0.375pt
#let slop-lockup-dx(height: 1.64cm) = (
  _spine-x - (_spine-x - slop-brand.lockups.slop.mast-dx) * (height / 1.64cm)
)

// --- Gribouille chart styling ---

// The brand chart theme (Public Sans, slop ink, light-grey grid), its dark
// mirror, and the `-auto` pick that follows `slop-doc-theme`. Chart files
// use the auto exports so the same source renders correctly in both the
// light PDF and the dark signage variant.
#let slop-theme = chart-theme(slop-brand)
#let slop-theme-dark = chart-theme(slop-brand, dark: true)
#let slop-theme-auto = if _slop-dark { slop-theme-dark } else { slop-theme }

// Chart palettes, on the two-ink register: gold and ink lead; a gold tint
// and a mid-grey extend to four series without leaving the house palette.
// The dark counterpart swaps ink for paper (white) --- gold + paper on the
// dark ground --- and keeps the same series order.
#let slop-categorical = (
  slop-gold,
  slop-ink,
  slop-colors.primary-2,
  slop-colors.grey-3,
)
#let slop-categorical-dark = (
  slop-gold,
  slop-colors.white,
  slop-colors.primary-2,
  slop-colors.grey-3,
)
#let slop-categorical-auto = if _slop-dark { slop-categorical-dark } else {
  slop-categorical
}
// Ordinal: greyscale ramp for ranked/Likert series --- black-anchored on
// light pages, white-anchored on dark.
#let slop-ordinal = greyscale-ordinal
#let slop-ordinal-dark = greyscale-ordinal-dark
#let slop-ordinal-auto = if _slop-dark { slop-ordinal-dark } else {
  slop-ordinal
}
// Sequential single-hue: slop gold tints (100% -> ~10%) for parts of a
// whole. Every step stays legible on both grounds (the palest tint is
// near-paper, which reads fine on the dark page), so one ramp serves both
// themes.
#let slop-gold-tints = (
  slop-gold,
  color.mix((slop-gold, 75%), (white, 25%)),
  color.mix((slop-gold, 50%), (white, 50%)),
  color.mix((slop-gold, 28%), (white, 72%)),
  color.mix((slop-gold, 10%), (white, 90%)),
)

// Map the first N brand colours onto a discrete aesthetic. Pass the factor
// levels in the order you want them coloured; override `palette` for a
// different ramp (e.g. slop-ordinal-auto, slop-gold-tints). The default
// follows the document theme. Key the result by aesthetic in gribouille's
// `scales(...)` binder --- e.g. `scales: scales(fill: slop-fill(levels))`;
// since gribouille 0.5.0 the spec is aesthetic-agnostic, so slop-colour and
// slop-fill are the same function under two readable names.
#let slop-colour(levels, palette: slop-categorical-auto) = chart-colour(
  levels,
  palette,
)
#let slop-fill(levels, palette: slop-categorical-auto) = chart-fill(
  levels,
  palette,
)

// --- Social furniture ---

// The Bluesky butterfly, recoloured at use. The university runs a real
// Bluesky account (@slop.university); posters carry the mark in their footer
// furniture. Default fill follows the page ground; pass `fill:` to override
// (e.g. `white` over a baked-dark hero band).
#let _bluesky-svg = read("logos/bluesky.svg")
#let slop-bluesky-logo(height: 0.85em, fill: auto) = {
  let f = if fill == auto { slop-ink-auto } else { fill }
  image(
    bytes(_bluesky-svg.replace("#1185fe", f.to-hex())),
    format: "svg",
    height: height,
    alt: "Bluesky",
  )
}

// The standard social line for poster footers: butterfly + handle +
// institutional hashtag. One helper so every poster renders it identically;
// muted by default (footnote register), `fill:` for overlays.
#let slop-social-line(size: 8.5pt, fill: auto) = {
  let f = if fill == auto { slop-muted-auto } else { fill }
  text(
    size: size,
    fill: f,
  )[#box(baseline: 14%, slop-bluesky-logo(height: 0.95em, fill: f))#h(
      0.4em,
    )#"@slop.university · #slopU"]
}

// --- PhD thesis ---
//
// The one long-form output: front / main / appendix / back matter, each with
// its own page and heading numbering. `slop-thesis` is the document wrapper
// (house base styles via `slop(...)`, plus the title page and the thesis-wide
// rules); the four matter wrappers switch numbering and the shape of a
// level-1 heading. Everything else --- fonts, colours, tables, links, charts
// --- is the ordinary house base.
//
// Two core behaviours are deliberately replaced here: the automatic masthead
// (it keys off "page counter reads 1", which a thesis hits three times) and
// the full-bleed image figure (a thesis figure stays in the text block).

// Which matter the document is in. Read back at a heading's or figure's own
// location, so the contents can label an entry "Chapter 3" or "Appendix A"
// and figure numbers can follow the chapter they sit in.
#let _thesis-matter = state("slop-thesis-matter", "front")

// The core's own masthead, placed on the title page by hand because
// `slop-thesis` hides the automatic one. Never re-derive the geometry here:
// a hand-rolled copy drifts from the core's and the crest leaves the spine.
// Like the core's, this MUST go in the title page's `background`, not its
// flow --- `place` in the flow anchors to the text block, and the book
// margins would then throw the crest 30mm right of the spine and 28mm down.
#let _thesis-masthead() = {
  let (bg-color, ..) = _uni._theme-colors(slop-brand, _slop-dark)
  _uni._place-masthead(slop-brand, bg-color, _slop-dark, 2cm, lockup: "slop")
}

// The gold eyebrow over a chapter or appendix title ("Chapter 3"). Public
// Sans ships no small-cap feature, so the small-caps register is upper case
// at small size with tracking.
#let _thesis-eyebrow(body) = text(
  size: 10pt,
  weight: "medium",
  tracking: 0.14em,
  fill: slop-gold,
  upper(body),
)

// A level-1 heading in thesis register: always opens a page, optional gold
// eyebrow above the title. `eyebrow` is content or none.
#let _thesis-h1(it, eyebrow: none, lead: 1.6cm) = {
  pagebreak(weak: true)
  v(lead)
  block(above: 0em, below: 0.85cm, {
    if eyebrow != none {
      eyebrow
      // The eyebrow is 10pt against a 26pt title, so a gap that looks right
      // between two body lines reads as a collision here.
      v(0.35cm)
    }
    text(size: 26pt, weight: "regular", fill: slop-ink-auto, it.body)
  })
}

// Chapter/appendix number of the level-1 heading being shown.
#let _thesis-h1-number(pattern) = context counter(heading).display(pattern)

// Figure and table numbers run within the chapter they sit in (Figure 3.2,
// Table A.1). `chapters` is the heading counter and `n` the figure counter,
// both read AT THE FIGURE'S OWN LOCATION --- typst evaluates a numbering
// function wherever the number is printed (a cross-reference, a list of
// figures), not where the figure is, so every caller resolves the two
// counters itself and passes them in.
#let _thesis-chapter-patterns = (main: "1.1", appendix: "A.1")
#let _thesis-fig-number(matter, chapters, n) = {
  let pattern = _thesis-chapter-patterns.at(matter, default: none)
  if pattern != none and chapters.len() > 0 {
    numbering(pattern, chapters.first(), n)
  } else {
    numbering("1", n)
  }
}

// The number a figure or table carries, resolved at its own location.
#let _thesis-fig-number-at(el) = {
  let loc = el.location()
  _thesis-fig-number(
    _thesis-matter.at(loc),
    counter(heading).at(loc),
    counter(figure.where(kind: el.kind)).at(loc).first(),
  )
}

// "Figure" / "Table", however the element spells it.
#let _thesis-fig-supplement(el) = {
  let s = el.supplement
  if s in (auto, none) {
    if el.kind == table { [Table] } else { [Figure] }
  } else { s }
}

// The standard Australian declaration, deadpan. Returns the body only; put it
// under your own `= Declaration` heading inside `slop-thesis-frontmatter`.
#let slop-thesis-declaration(candidate: "", date: "") = {
  [
    I declare that this thesis is my own original work. To the best of my
    knowledge it contains no material previously published or written by another
    person, except where due reference is made in the text of the thesis.

    This thesis has not been submitted, in whole or in part, for any other
    degree or diploma at Slop University or at any other institution. The
    research reported here was carried out during the period of my candidature,
    and any assistance received in its preparation, and all sources used, have
    been acknowledged.
  ]
  v(2.4em)
  block(text(weight: "medium", candidate))
  v(0.3em)
  block(text(size: 0.9em, fill: slop-muted-auto, date))
}

// A chapter epigraph: right-aligned italic, attribution beneath. Use
// sparingly --- at most one per chapter, immediately after the opener.
#let slop-thesis-epigraph(quote, attribution) = block(
  width: 100%,
  above: 0.6em,
  below: 2.4em,
  align(right, block(width: 72%, {
    set align(left)
    set par(justify: false, leading: 0.7em)
    text(style: "italic", fill: slop-ink-auto, quote)
    if attribution != none {
      v(0.55em, weak: true)
      text(size: 0.88em, fill: slop-muted-auto)[--- #attribution]
    }
  })),
)

// Front matter: roman numerals from i, unnumbered level-1 headings, each on
// a new page. Declaration, Acknowledgements, Abstract, Contents, List of
// figures, List of tables.
#let slop-thesis-frontmatter(body) = {
  set page(numbering: "i")
  counter(page).update(1)
  _thesis-matter.update("front")
  set heading(numbering: none)
  show heading.where(level: 1): it => _thesis-h1(it, lead: 0.6cm)
  body
}

// What the two numbered matters share: headings numbered to depth 3, a
// cross-reference supplement per depth, and a level-1 heading that opens a
// chapter with its gold eyebrow and restarts the per-chapter figure and table
// counters. `name` is the word for a level-1 unit ("Chapter" / "Appendix"),
// `pattern` the heading numbering ("1.1" / "A.1") and `chapter-pattern` the
// eyebrow's own number ("1" / "A").
#let _thesis-numbered-matter(name, pattern, chapter-pattern, body) = {
  set heading(
    numbering: (..n) => if n.pos().len() <= 3 {
      numbering(pattern, ..n.pos())
    },
    // `@ch-intro` reads "Chapter 1", `@sec-site` "Section 2.3".
    supplement: h => if h.depth == 1 { name } else { [Section] },
  )
  show heading.where(level: 1): it => {
    counter(figure.where(kind: image)).update(0)
    counter(figure.where(kind: table)).update(0)
    _thesis-h1(
      it,
      eyebrow: _thesis-eyebrow[#name #_thesis-h1-number(chapter-pattern)],
    )
  }
  body
}

// Main matter: page counter restarts at 1 in arabic; headings numbered
// "1.1" to depth 3; a level-1 heading opens a chapter.
#let slop-thesis-mainmatter(body) = {
  set page(numbering: "1")
  counter(page).update(1)
  _thesis-matter.update("main")
  _thesis-numbered-matter([Chapter], "1.1", "1", body)
}

// Appendices: numbering restarts as A, B, C (headings "A.1"); page numbering
// carries on from the main matter.
#let slop-thesis-appendices(body) = {
  _thesis-matter.update("appendix")
  counter(heading).update(0)
  _thesis-numbered-matter([Appendix], "A.1", "A", body)
}

// Back matter: unnumbered level-1 headings on a new page. In practice the
// bibliography, whose `title:` is a level-1 heading like any other.
#let slop-thesis-backmatter(body) = {
  _thesis-matter.update("back")
  set heading(numbering: none)
  show heading.where(level: 1): it => _thesis-h1(it)
  body
}

// A contents entry in thesis register: chapter entries carry their unit word
// and number, sub-entries indent, dot leaders to the page number. Replaces
// the core's booklet rule (rule-under-every-entry, number dropped).
#let _thesis-outline-entry(it) = {
  show link: set text(fill: slop-ink-auto)
  let el = it.element
  let top-level = it.level == 1
  let unit = if el.func() == heading and top-level {
    let matter = _thesis-matter.at(el.location())
    if matter == "main" { [Chapter ] } else if matter == "appendix" {
      [Appendix ]
    }
  }
  let prefix = if el.func() == figure {
    [#_thesis-fig-supplement(el)~#_thesis-fig-number-at(el)]
  } else { it.prefix() }
  block(
    width: 100%,
    above: if top-level { 1.3em } else { 0.7em },
    below: 0em,
    link(el.location(), {
      set text(weight: if top-level { "medium" } else { "light" })
      if it.level > 1 { h((it.level - 1) * 1.2em) }
      if prefix != none {
        if unit != none { unit }
        prefix
        h(0.6em)
      }
      it.body()
      box(width: 1fr, inset: (x: 0.4em), {
        set text(fill: slop-muted-auto)
        if it.fill != none { it.fill }
      })
      it.page()
    }),
  )
}

// The title page. The masthead and the brand rule go in the page background,
// not its flow --- passing `background` overrides the core's for this page,
// so the rule is redrawn alongside the masthead that masks it.
#let _thesis-title-page(
  title: "",
  subtitle: none,
  candidate: "",
  degree: "",
  school: "",
  supervisors: (),
  submitted: "",
) = page(
  footer: none,
  background: {
    _uni._brand-rule(slop-brand)
    _thesis-masthead()
  },
  {
    // The thesis body is justified and hyphenated; display type on the title
    // page is neither.
    set par(justify: false, leading: 0.42em)
    set text(hyphenate: false)
    v(5.2cm)
    text(size: 30pt, weight: "regular", title)
    if subtitle != none {
      v(0.45em)
      text(
        size: 17pt,
        weight: "regular",
        style: "italic",
        fill: slop-gold,
        subtitle,
      )
    }
    v(2.6cm)
    text(size: 15pt, candidate)
    v(1.4cm)
    set text(size: 10.5pt, fill: slop-muted-auto)
    set par(justify: false, leading: 0.9em)
    [A thesis submitted for the degree of #degree]
    linebreak()
    [#school, Slop University]
    if supervisors.len() > 0 {
      linebreak()
      if supervisors.len() == 1 [Supervisor:] else [Supervisors:]
      [ ]
      supervisors.map(s => [#s]).join([, ], last: [ and ])
    }
    v(1fr)
    text(submitted)
  },
)

// The thesis document wrapper: `#show: slop-thesis.with(...)`. Renders the
// title page, then the body (which is the four matter wrappers in order).
#let slop-thesis(
  title: "",
  subtitle: none,
  candidate: "",
  degree: "Doctor of Philosophy",
  school: "",
  supervisors: (),
  submitted: "",
  body,
) = {
  slop(
    title: title,
    subtitle: subtitle,
    paper: "a4",
    // Book margins: the binding edge is wider, and the brand rule (1.9cm
    // from the paper's left edge) stays clear of the text block on both.
    margin: (inside: 30mm, outside: 25mm, top: 28mm, bottom: 28mm),
    config: (theme: slop-doc-theme, hide: ("title-block", "masthead")),
    {
      // No running header; the footer's centred page number is the only
      // running furniture (it comes from the house base).
      set page(header: none)
      set par(justify: true, leading: 0.8em)
      set outline(depth: 3)
      show figure.where(kind: table): set figure.caption(position: top)

      // Tables run tighter than the house default and set ragged-right. Over
      // five columns the default 0.75em of padding either side of every one
      // spends a fifth of the text block on air, and justifying a cell that
      // narrow rivers it.
      set table(inset: (x: 0.5em, y: 0.55em))
      show table.cell: set par(justify: false)

      // Figures and tables number by the chapter they sit in (Figure 3.2,
      // Table A.1); the matter wrappers reset the two counters per chapter.
      set figure(numbering: n => context _thesis-fig-number(
        _thesis-matter.get(),
        counter(heading).get(),
        n,
      ))

      // A cross-reference to a figure or table prints the number of the
      // TARGET's chapter. Without this, `@fig-x` in chapter 5 renders a
      // chapter-1 figure as "Figure 5.1" --- silently, and wrongly.
      // Citations (`it.element` is none) and every other target fall
      // through to the default reference.
      show ref: it => {
        let el = it.element
        if el != none and el.func() == figure {
          let supp = if it.supplement not in (auto, none) {
            it.supplement
          } else { _thesis-fig-supplement(el) }
          // Ink, not link gold: typst's own cross-references are ink, and
          // a thesis full of gold "Figure 3.2"s reads as noise.
          link(
            el.location(),
            text(fill: slop-ink-auto, [#supp~#_thesis-fig-number-at(el)]),
          )
        } else { it }
      }

      // Thesis figures stay inside the text block --- the core's image
      // figures bleed to the right page edge, which a bound thesis can't
      // use. Caption left-aligned under the figure, as in the core.
      show figure.where(kind: image): it => block(above: 2.2em, below: 2.2em, {
        align(center, it.body)
        if it.caption != none {
          v(0.65em, weak: true)
          it.caption
        }
      })
      show figure.caption: it => align(
        left,
        text(size: 0.88em, fill: slop-muted-auto, it),
      )

      show outline.entry: _thesis-outline-entry

      _thesis-title-page(
        title: title,
        subtitle: subtitle,
        candidate: candidate,
        degree: degree,
        school: school,
        supervisors: supervisors,
        submitted: submitted,
      )

      body
    },
  )
}
