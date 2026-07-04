---
name: from-source
description: Typeset arbitrary source material (URL, Word doc, ODT, markdown, plain text) into a nicely-typeset PDF in the ANU visual identity. Faithful to the source --- no rewriting, no invented prose. Small editorial calls (heading hierarchy when ambiguous, lockup choice, cover-image theme) are allowed. Use when invoked with `/from-source <source>`.
---

# from-source

Take a piece of existing source material and typeset it through the
ANU template, faithfully. The source's prose is reproduced verbatim;
the template supplies the visual identity (cover, AoC, back cover, ANU
lockup), and a generated cover image hints at the subject.

## What this skill does --- and does not --- do

**Does:**

- Read or fetch the source material (URL, `.docx`, `.odt`, `.md`,
  `.html`, `.typ`, `.txt`).
- Lay the source's prose into the ANU typst template, preserving the
  original structure (sections, subsections, paragraphs, lists, block
  quotes, code blocks, tables).
- Add the standard ANU furniture: contents page, Acknowledgement of
  Country, back-cover lockup.
- Generate one cover image themed to the source's subject (no inline
  imagery; that would be invention).
- Make small editorial calls when the source is ambiguous --- heading
  hierarchy when levels aren't explicit, the lockup choice
  (`anu` vs `anu-socy`), the cover-image theme.

**Does not:**

- Rewrite, paraphrase, summarise, or "improve" the source's prose.
- Invent new content --- no new sections, no filler paragraphs, no
  generated inline images, no fabricated charts.
- Apply institutional voice. The satirical-voice doctrine in
  `../from-preset/genre.md` is for the preset path; the source's
  voice is whatever the source's voice is, and stays untouched.
- Pad odd page counts with invented content. Parity is fixed with a
  blank page before the back cover (see step 7).

## Inputs

The slash-command argument is the **source identifier**. Examples:

- A URL: `https://www.anu.edu.au/news/all-news/foo`
- A local file path: `~/projects/foo/draft.md`,
  `~/Documents/proposal.docx`, `./talk.odt`,
  `./outline.typ`
- An odt/docx/html file dropped into the project

If the source identifier is ambiguous (e.g. multiple files match a bare
name), stop and ask which one. Don't guess.

## Doc identity (derived from the source)

| Field | Source |
| --- | --- |
| Canonical name | The source's title verbatim (H1, `<title>`, docx `dc:title`, etc.) |
| Cover title | The source's title verbatim |
| Cover subtitle | The source's subtitle if present; otherwise empty |
| Cover lockup | Editorial call: `anu-socy` if the source is clearly School-of-Cybernetics content; otherwise `anu` (the default) |
| Back-cover lockup | Matches the cover lockup |
| Filename prefix | `source` |
| Page-count range | Even; no minimum or maximum (the source determines length) |
| Register | Whatever register the source uses; preserved verbatim |
| PDF metadata title | The source's title verbatim (no satirical formula) |

Slug is derived from the source's title per `../_shared/output-naming.md`.

If the source has no clear title, stop and ask the user for one. Don't
fabricate.

## Workflow

Run these in order.

1. **Parse inputs.**
   - Take the source identifier.
   - Decide how to ingest: URL → WebFetch; `.docx`/`.odt` → pandoc;
     `.md`/`.html`/`.typ`/`.txt` → Read directly.
   - If the identifier is ambiguous, stop and ask.

2. **Ingest the source.**
   - **URL:** use the `WebFetch` tool with a prompt that asks for the
     full article text (not a summary), structured with explicit
     headings. WebFetch returns Claude's view of the page; verify the
     extraction looks complete before proceeding.
   - **`.docx` / `.odt`:**
     `pandoc <path> --to=markdown --wrap=none -o /tmp/source.md`, then
     Read `/tmp/source.md`. `--wrap=none` preserves paragraph breaks
     as single newlines so prose stays intact across the conversion.
   - **`.html` (local file):**
     `pandoc <path> --from=html --to=markdown --wrap=none -o /tmp/source.md`.
   - **`.md` / `.typ` / `.txt`:** Read the file directly.

3. **Derive doc identity.**
   - Extract the source's title (H1 if present, docx `dc:title`,
     `<title>` from HTML, or the most prominent heading).
   - Extract the subtitle if present (typically the second-level
     heading immediately under the H1, or a `subtitle` metadata
     field).
   - Generate `<slug>` from the title per
     `../_shared/output-naming.md`; generate a fresh 6-character
     `<seed>`.
   - Decide the lockup: if the source mentions "School of
     Cybernetics", "SOCY", or is clearly a school-level doc, use
     `anu-socy`; otherwise default to `anu`. State the choice in the
     run's text output so the user can correct it if wrong.

4. **Decide editorial calls** (the user has authorised small calls
   when the source is ambiguous; anything beyond this stops and asks):
   - **Heading hierarchy.** If the source uses one heading level for
     what are logically sections vs subsections, demote some to
     subsections so the typst outline reads naturally. Don't rename
     headings; only adjust their level.
   - **Front-matter handling.** If the source has front-matter
     (frontmatter blocks, abstracts, summaries), decide whether to
     render as a separate section, as a subtitle, or to drop the
     frontmatter syntax and render the contents as the first body
     paragraph. The default is to render the abstract as the first
     section if labelled, or drop the YAML frontmatter and use its
     `title`/`subtitle` fields for the cover.
   - **Cover-image theme.** Pick a theme from the source's subject
     matter that translates to an ANU-scene prompt (e.g. classroom,
     workshop, landscape, artefact). Avoid literal-illustrative
     prompts that read like stock-photo invention.
   - **Pre-existing satirical-tells.** If the source happens to
     contain language that reads as a satirical-tell ("This Does Not
     Exist", etc.), leave it alone --- that's the source's call, not
     the skill's.

   Surface every editorial call you make in the run's text output so
   the user can spot anything that looks off.

5. **Write `output/source-<slug>-<seed>.typ`** in one pass.
   - Use the import block from `../_shared/typst-layout.md`.
   - Set the PDF metadata title to the source's title verbatim ---
     **no satirical formula**. Title only; no author, description,
     keywords, date.
   - Call `anu.with(title: <source title>, subtitle: <source subtitle if present, else "">, cover: read("/source-<slug>-<seed>-images/cover.jpg", encoding: none), config: (lockup: "<chosen lockup>"))`.
     Drop the `config:` argument if the lockup is the default `anu`.
   - Emit the outline (`#outline(title: [Contents], depth: 1)`).
   - Paste the Acknowledgement of Country block verbatim from
     `../_shared/typst-layout.md`. It ends with the only
     `#pagebreak()` call in the document.
   - Transcribe the source's body faithfully. Headings become `=`
     (level 1), `==` (level 2), and so on per the editorial-call
     hierarchy. Paragraphs, lists, block quotes, code blocks, and
     tables map to their typst equivalents. Preserve emphasis,
     inline code, links, and footnotes.
   - End the file with `#anu-back-cover()` (or
     `#anu-back-cover(config: (lockup: "anu-socy"))` if the lockup
     is `anu-socy`).

6. **Generate the cover image.** See `../_shared/image-workflow.md`.
   From-source specifics:
   - Image folder: `output/source-<slug>-<seed>-images/`
   - Prompt count: 1 (cover only). Inlines are not generated --- the
     source either has its own imagery (in which case quote it) or
     doesn't (in which case we don't invent).
   - Prompt theme: derived from the source's subject. Avoid
     literal-illustrative prompts; the cover should evoke the
     subject, not depict it.
   - Aspect: 3:4 portrait.
   - Reference selection: per the image-workflow rules. Pick 3-5
     references that match the cover prompt's mood.

7. **Compile and parity-fix** (faithful-path workflow per
   `../_shared/typst-layout.md`):
   - Compile: `typst compile output/source-<slug>-<seed>.typ output/pdf/from-source/source-<slug>-<seed>.pdf`
     (create `output/pdf/from-source/` if it doesn't exist).
   - Read page count: `pdfinfo output/pdf/from-source/source-<slug>-<seed>.pdf | grep Pages`.
   - If even, ship. If odd, insert a single `#pagebreak()`
     immediately before `#anu-back-cover()` to push a blank leaf in
     front of the back cover. Recompile and verify the count is now
     even.
   - **Don't invent content** to fix parity. A blank page is the
     correct trade for content fidelity.

8. **Stop.** Generated outputs (`.typ`, the PDF, the
   `source-<slug>-<seed>-images/` folder) are kept locally only ---
   they're gitignored. Don't commit; don't tag the run.

## Source-conversion hints

- **WebFetch** is best for cleanly-structured articles. For pages
  heavy on navigation, asides, or comments, ask WebFetch explicitly
  for the article body and ignore chrome.
- **pandoc** handles `.docx`, `.odt`, `.html`, `.epub`, `.rst`, `.org`,
  and more. Run `pandoc --list-input-formats` if unsure whether a
  format is supported.
- **Embedded images in source documents** are dropped by default ---
  this skill doesn't reproduce the source's imagery, only the prose
  structure. If the source's imagery is load-bearing (figures in a
  paper, photos in a profile), surface that limitation in the run's
  text output so the user knows the typeset version is text-only.
- **Tables in source documents** map to typst tables. For complex
  tables, pandoc-to-markdown sometimes produces a pipe-table that
  doesn't translate cleanly; render those as `#table(...)` in typst
  for control.

## Pre-ship checklist

- [ ] Source content is faithfully reproduced --- no paraphrasing, no
      summarising, no invented sections, no filler paragraphs
- [ ] Editorial calls (heading hierarchy adjustments, lockup choice,
      cover-image theme, abstract/frontmatter handling) are
      reported in the run's text output so the user can spot
      anything off
- [ ] PDF metadata title is the source's actual title verbatim ---
      no "Does Not Exist" satirical formula
- [ ] PDF metadata has no author, description, keywords, or date
      populated (just the title); verify with `pdfinfo`
- [ ] Cover image generated; no inline images invented
- [ ] If the source has embedded imagery, the run's text output
      flags this so the user knows the typeset version is text-only
- [ ] Acknowledgement of Country page sits between contents and the
      first body section, verbatim, no image, no other content
- [ ] Exactly one `#pagebreak()` (after the AoC), unless a blank-page
      parity fix has added a second one immediately before
      `#anu-back-cover()`
- [ ] Back cover (`#anu-back-cover(...)` with the chosen lockup) is
      the last call in the file
- [ ] Page count is even (`pdfinfo … | grep Pages`)
- [ ] PDF compiles cleanly (no missing fonts, broken images, overflow)

## When something goes wrong

- **WebFetch returns a summary instead of full text**: re-issue the
  fetch with an explicit prompt asking for the full article body
  verbatim, preserving headings and paragraph breaks. If the page is
  paywalled or behind JS that WebFetch can't reach, stop and ask the
  user for an alternative source (downloaded copy, paste, etc.).
- **pandoc produces messy markdown**: try `--wrap=none` first; if the
  output is still poor, try a different intermediate format (e.g.
  `--to=plain` then re-paragraph by hand, or `--to=html` then
  hand-extract). Some docx files with heavy formatting are
  pathological for pandoc; in those cases, stop and ask the user
  whether the conversion is acceptable.
- **Source has no clear title**: stop and ask the user for one
  rather than fabricating. The PDF metadata title and the cover
  title both depend on it.
- **typst compile fails**: most failures are conversion artefacts
  (pandoc-produced markdown that doesn't translate cleanly to typst).
  Identify the offending construct (raw HTML, complex table, footnote
  syntax) and convert it manually before recompiling.

## What this skill is not

- Not a satirical generator. For that, use
  `../from-preset/SKILL.md` with an existing preset
  (`strategy`, `impact-report`, `research-poster`, or one of your own).
- Not a translator, paraphraser, or summariser. The source's prose
  goes through verbatim.
- Not a fact-checker. The skill doesn't verify the source's claims;
  it just renders them in the ANU template.
- Not a substitute for the user's judgement about whether the
  source's content is appropriate to wrap in ANU branding. The
  skill applies the template the user asks for; the appropriateness
  call is the user's.
