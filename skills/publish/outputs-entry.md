# Outputs entry and staging (rung 2A)

### Companion press release + news post


Write the press release per `comms.md` (the media-release register: quotes from
roster researchers, institutional pride, hedged-commitment discipline --- no
verifiable numbers). Then:

- **News post** → `website/src/content/news/<date>-<slug>.md` with frontmatter
  `title` (headline, comms register), `date` (today, ISO), `description`
  (one-sentence standfirst), `output` (the outputs entry id, which is the run
  id). Body: the press release.
- **Outputs entry** → `website/src/content/outputs/<run-id>.yml` with: `title`
  (the artefact's main title --- the punchy part before the colon; it becomes
  the hero heading and listing card), `subtitle` (optional; the explanatory part
  after the colon, shown as a deck under the heading --- split an academic
  "Main: Subtitle" title here rather than storing the whole string in `title`),
  `authors` (the roster authors used), `preset`, `school` (the lead author's
  school), `date`, `publishedAt` (the exact `SLOPU_PUBLISHED_AT` value supplied
  by the unattended wrapper; omit only for a manual run without it), `doi`,
  `summary` (1-2 sentence abstract of the fictional work, institutional
  register --- not the press release's standfirst), `topic` (the steering line),
  `pdfDark` (poster-format runs only --- `research-poster`, `marketing-poster`:
  `true`, meaning a dark signage render exists --- see staging below), `pages`
  (from pdfinfo), `version: "1.0"`, and `grants` (optional --- see below). The
  thumbnail and hero carry no yml field --- they resolve by matching a file
  basename to the entry id (see below).
- **Grant attachment.** Read `website/src/content/grants/*.yml`: if a grant's
  `grantees` include one of this output's authors, its `date` precedes the
  output's, and its remit plausibly covers the topic, list its entry id under
  `grants:` in the outputs entry --- the landing page renders the funding
  acknowledgement and the dashboard counts the income. Attach every grant that
  qualifies (a mundane study propped up by several internal schemes is the genre
  working); omit the field when none does. Never invent a grant here ---
  awarding one is action 2I.
- **Citation harvest.** Run `ops/extract-citations.py --id <run-id> --write`. It
  reads the DOIs out of the compiled `.typ`/`.bib` you just produced and records
  them as `cites:` on the entry --- the edges the site counts citations, "cited
  by" lists, and h-indices from. Do not hand-write the field: the source is the
  evidence, and a hand-written edge with nothing printed behind it is a
  fabricated citation. If the run cited prior canon and the script writes
  nothing, the DOIs never made it into the document --- fix the document, not
  the ledger. The sources are gitignored and the press worktree is reset each
  tick, so an edge not harvested now is lost.

### Stage assets into website/

- Stage the final PDF into the staging dir, downsampling it on the way in ---
  never copy it verbatim. The compiled PDF embeds imagery at ~360 PPI and runs
  1--5 MB; the served copy only needs screen resolution.

  **Resolve the staging dir once, as an absolute path, and use it everywhere:**

  ```sh
  STAGING="${SLOPU_PENDING_DIR:-$(git rev-parse --show-toplevel)/data/pending-uploads}"
  mkdir -p "$STAGING"
  ```

  A concurrent generator slot sets `SLOPU_PENDING_DIR` to its own
  `data/pending-uploads/<run-id>/`, so two runs staging at the same moment
  cannot see or clobber each other's files; unset, this is the single staging
  root an interactive run uses. Either way it is ABSOLUTE, which is the point: a
  bare `data/pending-uploads/…` resolved against `website/` silently creates
  `website/data/pending-uploads/`, the wrapper finds nothing to upload, and the
  whole tick is rescued and thrown away. Use `$STAGING`, never a relative path.

  `gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dPDFSETTINGS=/ebook -sColorConversionStrategy=RGB -sOutputFile="$STAGING/<run-id>.pdf" ./output/pdf/<group>/<run-id>.pdf`

  (~80% smaller on the image-heavy formats, visually identical at reading size;
  the PDF metadata title survives the round-trip). Keep the explicit RGB
  strategy: without it `/ebook` falls back to a legacy one that paints
  translucent fills opaque on the Ghostscript mise.toml pins. The
  full-resolution original stays in gitignored `output/pdf/<group>/`. Confirm
  the file landed before moving on --- `ls "$STAGING"`.

  PDFs are **not committed** and do not live under `website/public/` --- they
  are served from the bucket at `pdf.slop.university` (why:
  `website/src/lib/pdfs.ts`). The staging dir is the gitignored handoff channel:
  you stage the file there, and the wrapper uploads it and only then pushes, so
  a failed upload aborts the tick rather than publishing an entry that points at
  a missing object. Never write to
  `website/public/outputs/pdf/`; the wrapper's allowlist rejects it.

  The key is the run id, so nothing records a path: the entry carries no `pdf`
  field at all.

- **Dark sibling (poster-format runs: `research-poster`,
  `marketing-poster`)** --- the from-preset step also compiled
  `output/pdf/<group>/<run-id>-dark.pdf` (same source, `--input theme=dark`);
  stage it through the identical gs downsample → `"$STAGING/<run-id>-dark.pdf"`
  and set `pdfDark: true` in the outputs entry. The signage endpoints prefer it;
  every other surface (landing page, DOI, downloads) keeps using the light PDF.
  The thumbnail and hero are rendered from the light variant as before.
- Thumbnail --- the PDF's first page, rasterised here at publish time (the image
  pipeline resizes rasters but cannot render a PDF):
  `typst compile --root . --pages 1 --format png --ppi 144 output/<run-id>.typ /tmp/<run-id>-thumb.png`,
  then encode its rung ladder into the staging tree (the encoder resolves its
  own destination --- the repo's staging dir, or `$SLOPU_PENDING_DIR` when a
  generator slot set one --- so it is cwd-independent):
  `ops/encode-images.py encode thumb --source /tmp/<run-id>-thumb.png --id <run-id>`.
  The command prints a `thumb:` dims snippet --- copy it verbatim into the
  outputs entry's frontmatter. Nothing is committed under `website/src/assets/`;
  the wrapper's allowlist rejects it.
- Hero --- a landscape 16:9 banner in the two-ink house style, reused on the
  output landing page, its outputs-listing card, and the announcing news post (a
  post that announces an output has no image of its own; it inherits that
  output's hero. A post announcing no output --- a grant award or an
  institutional notice --- carries its own; see 2H and 2I). Author the prompt
  per `skills/_shared/visual-style.md` and pick refs per
  `skills/_shared/image-workflow.md`; generate at `--aspect-ratio 16:9`
  `--resolution 2K` (the largest encoded rung is 2560 px; 2K feeds it with room
  to spare), then encode its ladder + og card from the repo root:
  `ops/encode-images.py encode hero --source output/<image-folder>/<name>.jpg --id <run-id>`
  and copy the printed `hero:` dims snippet into the outputs entry's
  frontmatter.

Like the PDF, the images are served from a bucket (img.slop.university) keyed by
the run id --- the entry records only the intrinsic dims; the wrapper validates
that every new entry has its rungs staged and uploads them. The site derives all
URLs and srcsets from the dims (`src/lib/images.ts`).

The outputs entry is the canonical record of the run: the dedup check reads the
collection, the outputs page charts it, and the People/Schools pages join on its
`authors` and `school`.