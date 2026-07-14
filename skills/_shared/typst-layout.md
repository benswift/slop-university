# Shared: typst layout discipline

Cross-cutting typst conventions for generated documents. The layout machinery
lives in the de-branded core package (`university-typst-template`); documents
import a **brand package** that re-exports the whole API with its brand applied.
Which brand package depends on the path:

- **Preset (satirical) path** --- `@local/slop-university-brand:0.1.0` (in-repo
  at `brand/slop-university-brand/0.1.0/`): the Slop University brand. Exports
  are `slop`-prefixed: `slop` (the show rule), `slop-back-cover`, `slop-colors`,
  `slop-highlight-card`, `slop-inline-figure`, `slop-lockup`, `slop-qr-code`,
  plus the chart values (see `chart-workflow.md`).
- **Faithful from-source path** --- `@local/anu-typst-template:0.3.0`: the
  genuine ANU brand. Exports are `anu`-prefixed with the same shapes.

The calling skill (`from-preset/SKILL.md`, `from-source/SKILL.md`, or a preset
blueprint) cross-refs this file. The caller supplies: (a) the document title
shape, (b) the brand package (and, faithful path only, the lockup choice `anu`
vs `anu-socy`), (c) the page-count range (or "even" alone if no range applies).

The sections below show the **preset-path** (`slop-*`) spellings; the faithful
path substitutes `anu` for `slop` throughout and adds its lockup choice.

## Template import

Every preset doc starts with this import block (extend with helpers as needed
--- the impact-report preset also imports `slop-inline-figure`):

```typst
#import "@local/slop-university-brand:0.1.0": slop, slop-back-cover, slop-colors, slop-highlight-card
```

Faithful path:

```typst
#import "@local/anu-typst-template:0.3.0": anu, anu-back-cover, anu-colors, anu-highlight-card
```

## Document metadata

Set the PDF title via `#set document(title: ...)`. **Title only ---** no author,
no description, no keywords, no date (typst stamps a CreationDate by default;
`date: none` suppresses it). Keep the metadata anonymous; the booklet must read
straight on the rendered pages.

```typst
#set document(
  title: "<title shape per the calling skill>",
  date: none,
)
```

The caller defines the title shape. Presets embed the steering prompt in a
satirical formula (e.g. strategy: "This Slop University Strategy Does Not Exist:
<steering verbatim>"; impact report: "This Slop University Impact Report Does
Not Exist: <steering verbatim>"). The from-source skill uses the source
document's actual title verbatim.

## Prose gotchas

- **Escape `$` in body text** (`\$600 million`) --- a bare `$` opens typst math
  mode and the compile error points somewhere unhelpful.

## The show-rule call

```typst
#show: slop.with(
  title: "<doc title visible on cover>",
  subtitle: "<varies between runs>",
  cover: read("/{image-folder}/cover.jpg", encoding: none),
  config: (bleed: 3mm),  // 3mm print bleed (trimmed booklet)
)
```

`{image-folder}` is per-doc; the cover image must be passed via
`read(..., encoding: none)` so typst resolves the path relative to the project
root.

Branding comes from the imported package --- the satirical presets get the
**Slop University** mark (a steaming-bowl crest in a shield + a "Slop /
University" wordmark) and the slop gold palette automatically; no lockup config
is needed.

On the faithful path the ANU package defaults to the university wordmark;
`config: (lockup: "anu-socy")` selects the combined ANU + School of Cybernetics
lockup instead (an editorial call the skill surfaces).

## Highlight cards and icon lookup

The brand package exports `slop-highlight-card(icon-name, title, body)` --- a
gold Iconoir glyph above a centred bold title and a body paragraph, designed for
use inside a `#grid`. The Iconoir collection (~1,700 line-icons) is
auto-provided inside `slop(...)`; pass a bare name (`"flask"`) or
fully-qualified Iconify name (`"iconoir:flask"`, `"mdi:home"`). The calling
preset declares the card count and what each card represents; the grid shape
follows the count:

**3 cards** --- single row of 3:

```typst
#grid(
  columns: (1fr, 1fr, 1fr),
  column-gutter: 0.8em,
  row-gutter: 0.8em,
  slop-highlight-card("flask", "<title>")[<1-2 sentence body>],
  slop-highlight-card("graduation-cap", "<title>")[<1-2 sentence body>],
  slop-highlight-card("community", "<title>")[<1-2 sentence body>],
)
```

**4 cards** --- 2×2 (same grid, `columns: (1fr, 1fr)`, four cards).

**5 cards** --- 3 on top, 2 centred below. Render as two stacked grids
(`#v(0.8em)` between): a 3-column grid then a 2-column grid --- the template
doesn't ship a centred-row helper. Counts above 5 read messy and aren't used.

**Finding valid icon names.** Once the card titles and bodies are drafted, pull
keyword stems out of each card's actual language and grep the bundled Iconoir
JSON for matches. Don't guess names from iconoir.com --- some listed there
aren't in the bundled JSON (e.g. `handshake`):

```bash
jq -r '.icons | keys[]' \
  ~/.local/share/typst/packages/local/university-typst-template/0.1.0/assets/iconoir.json \
  | grep -iE '<stems-from-this-card>'
```

Pick one match per card that fits its actual content, not a generic theme.
Verifying against the JSON before writing is cheaper than a failed compile.

## Page-break discipline

- **Preset (satirical) path: emit no manual `#pagebreak()` at all.** The
  template's `show outline:` rule already pagebreaks after the table of
  contents, so the first body section begins on a fresh page automatically;
  everything after it flows naturally. (Slop University documents carry no
  Acknowledgement of Country --- that is real institutional speech, not satire
  material, and the fictional institution has no standing to make it.)
- **Faithful path: emit exactly one `#pagebreak()` call:** the one that closes
  the Acknowledgement of Country block (see below). No other manual pagebreaks
  anywhere.
- **Do not** put `#pagebreak()` before any heading. Typst flows headings
  naturally; if a section won't fit on the current page, typst pushes it to the
  next. Forced breaks isolate figures on near-empty pages and waste vertical
  space.

## Acknowledgement of Country (faithful path only)

Every faithful from-source document includes an Acknowledgement of Country page
immediately after the auto-generated contents page and before the next section
--- it is part of the genuine ANU template furniture. Preset-path documents
never include one. The text is fixed and verbatim. **Do not paraphrase,
abbreviate, reorder, or adjust punctuation.** Copy the block below into the
typst source exactly as written:

```typst
#heading(level: 1, outlined: false)[Acknowledgement of Country]

The Australian National University (ANU) acknowledges the Ngunnawal and Ngambri-Kamberri people, who are the Traditional Owners of the land upon which the University's Acton campus is located.

This Ngunnawal and Ngambri-Kamberri land supports students and staff throughout their time at ANU. It will continue to hold a space for future generations to come together and learn from Country and one another.

We pay our respects to all Aboriginal and Torres Strait Islander peoples, Indigenous peoples, past, present and future, and acknowledge that this land from which we benefit has an ancient history that is both rich and sacred.

The ANU community makes a commitment to always respect the land upon which we stand and to ensure that the voices of this land's Indigenous peoples are both heard and listened to so that we may move towards a future marked by cooperation and mutual respect.

#pagebreak()
```

The page must contain no image and no other content. The trailing `#pagebreak()`
is the document's only manual pagebreak --- it pushes the following section to a
fresh page. The heading uses `outlined: false` so the acknowledgement does not
appear in the contents listing.

## Back cover

The back-cover helper produces a full-page inverse-themed (white-on-black by
default) lockup. It's a `page(...)` call internally, so it always inserts a
fresh final page --- no manual pagebreak needed before it.

```typst
#slop-back-cover(config: (bleed: 3mm))                     // preset path
#anu-back-cover(config: (bleed: 3mm))                      // faithful, ANU lockup
#anu-back-cover(config: (lockup: "anu-socy", bleed: 3mm))  // faithful, SOCY lockup
```

The back-cover call must be the last call in the file.

## Print bleed

Booklets are trimmed and saddle-stitched, so they set a 3mm print bleed:
`config: (bleed: 3mm)` on the show-rule call (and the same on the back-cover
call). The template then extends the cover hero, inline figures, gold spine
rule, and back cover past the trim edge, and the PDF gains a TrimBox/BleedBox so
the print shop can cut cleanly. The snippets above already include it.
**Poster-format presets are exempt** --- a poster is pinned to a board, not
trimmed, so there is no bleed.

## PDF transparency: constant alpha only

Never emit an **alpha gradient** (`gradient.linear` etc. with alpha in any stop)
into a PDF. Typst encodes them as a shading through a luminosity soft mask ---
spec-valid (ISO 32000 §11.6.5), but mishandled by the viewers that matter:
**solid black in iOS Safari and Firefox (pdf.js), silently dropped in Chrome
(PDFium)**, and resolution-dependent in poppler. Uniform **constant-alpha**
fills (e.g. `rgb("#00000059")` on a rect) are the one transparency feature every
viewer renders correctly.

Where a gradient scrim is needed over an image, either **bake it into the image
file at prep time** (centre-crop to the display aspect, then `-compose multiply`
a gradient mask onto the JPEG --- the research-poster blueprint's "Scrim bake"
bullet carries the tested recipe), or approximate it with a stack of ~60
smoothstep-eased constant-alpha strips (the core package's `feature-page` scrim
does this internally). Prefer the bake when the workflow already prepares the
image: it is pixel-identical to a true gradient and leaves zero transparency in
the PDF.

## Page-parity discipline

The page count must be even (back cover sits on the final leaf of a
saddle-stitched booklet; an odd count leaves a blank back). The caller declares
its own page-count range (e.g. strategy 16-20, impact report 12-18, from-source
"even, no range"); the rule that the count is even is universal for
**booklet-format** runs. **Poster-format presets are exempt** --- a poster is a
single landscape page with no back cover, so there is no parity to fix (see the
preset's one-page fit check).

### Parity-fix workflow (compile step) --- preset-driven runs

1. Compile exactly as the calling skill's compile step specifies --- preset runs
   pass `--root .` (their image/chart paths are root-relative). Create
   `output/pdf/<group>/` if it doesn't exist --- `<group>` is the caller's pdf
   subfolder per `output-naming.md`.
2. Read page count: `pdfinfo output/pdf/<group>/<pdf-file> | grep Pages`.
3. If even, ship. If odd, insert the spare inline figure at a natural break
   (between sections), generate the spare image, recompile. Re-check parity.
   Recurse if still odd (rare).
4. If the spare figure gets absorbed by existing slack and parity doesn't shift,
   small content tweaks (trim or extend a paragraph) are an acceptable fallback
   --- don't recurse forever on figure placement.

### Parity-fix workflow --- faithful from-source runs

The faithful path doesn't invent content, so the parity fix is mechanical
instead of generative:

1. Compile + check parity (as above).
2. If odd, insert a single `#pagebreak()` immediately before `#anu-back-cover()`
   to push a blank leaf in front of the back cover. Recompile and verify the
   count is now even.

The blank-page approach trades a wasted leaf for content fidelity. Don't add
invented prose or images to fix parity on a faithful run.
