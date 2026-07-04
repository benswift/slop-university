# Shared: parallel image generation

The calling skill (`from-preset/SKILL.md`, `from-source/SKILL.md`, a preset
blueprint, or the publish pipeline) cross-refs this file in its image-generation
step. The caller supplies: (a) the image-folder path (used as `{image-folder}`
in the sample prompt below), (b) the prompt count and shape (cover + N inlines,
where N may be zero), (c) any thematic constraints from the steering theme or
source material.

## Two reference regimes

- **Preset and publish runs (the default)** use the Slop University house style:
  prompts follow the fixed formula in `visual-style.md` (two-ink risograph
  illustration) and references come **only** from `references/slop-style/` (the
  curated, fully-generated seed set). No photographic references, ever.
- **Faithful from-source runs (local-only)** keep the photographic workflow:
  references come from the real-ANU campus photos in `references/*.avif`, and
  the prompt language rules in "Prompt language for ANU photo scenes" below
  apply. These photos are never used on the preset/publish path.

## Procedure

The parent does prompt design and reference selection; subagents handle the I/O.
Use `--jpg` for the format (the script writes `.jpg`; reference as `.jpg` in
typst).

1. **Pick references for all prompts upfront** (parent only). 3--5
   `--input-image` refs per call, from the regime's reference directory.
   House-style runs: choose exemplars matching each prompt's scene type (the
   campus scene for outdoor scenes, the interior for lab/indoor, the abstract
   motif for concept images, the portrait exemplar for any figure-led image) and
   vary the selection across the run's prompts and between runs. Faithful runs:
   choose photos whose filenames hint at different subjects (exterior / interior
   / event / wildlife) and vary likewise. Subagents must not pick references ---
   variety is a global property the parent owns.

2. **Dispatch in parallel** via the `Agent` tool: a single message with one tool
   use per image. Each subagent uses `subagent_type: general-purpose` and
   `model: sonnet`. The subagent's job is mechanical --- it shouldn't make
   creative decisions. Sample prompt:

   > Invoke the `ben:styled-image-gen` skill with prompt '\<p\>', `--jpg`,
   > `--resolution 4K`, `--aspect-ratio <AR>`, and
   > `--input-image <ref1> ... <refN>`. Output to
   > `output/{image-folder}/<name>.jpg` (use `cover.jpg` for the cover,
   > `inline-N.jpg` for inlines, `feature.jpg` for a poster feature). Report the
   > output path or any errors. Do nothing else.

   Pass the aspect ratio explicitly --- `16:9`, `9:16`, `1:1`, and `3:4` are
   available. The calling preset declares which ratio each image slot uses; the
   parent owns this choice along with the references.

   **Generate cover and feature/hero images at `--resolution 4K`** --- the
   model's largest, and the right choice at A3/booklet scale; it's slower than
   1K/2K but the detail matters, so don't downscale the hero to save time. A
   small _secondary_ image (e.g. the research poster's wide body strip, shown
   only a column wide) can be `2K` --- it never fills the page, so 4K would be
   wasted.

   `ben:styled-image-gen` calls Replicate, which needs `REPLICATE_API_TOKEN`.
   It's provided by the mise environment, so run the generation under mise (e.g.
   `mise exec -- …`); in a headless or cron context where mise isn't
   auto-activated, that prefix is what makes the token available.

3. **Don't generate the spare inline yet** --- only generate it if the compile
   step's parity fix needs it (single call, no need to dispatch a subagent for
   it).

## Prompt language (house style)

Use the formula in `visual-style.md` verbatim --- only the \<scene\> slot
varies. Describe activity, scale, and mood in the scene slot; the style clause
carries palette, texture, and register. Never prompt for photographs, real
places, real people, or text in the image. Eyeball every output against the
visual-style curation bar before it ships (two inks only, no photoreal passages,
no text artefacts, no real-person likeness).

## Style-canon promotion (house style)

The seed set grows from real runs. When a run produces an image that clearly
clears the curation bar in `visual-style.md` and adds coverage the set lacks (a
new scene type, a better exemplar of an existing one), promote it: resize to
1280px on the long edge, encode with
`avifenc -j 4 -s 6 --min 0 --max 63 -a end-usage=q -a cq-level=28`, and drop it
in `references/slop-style/` with a descriptive kebab-case name. Keep the set
curated, not comprehensive --- prefer ~8--15 strong exemplars over an archive;
replace weaker exemplars rather than accumulating near-duplicates.

## Prompt language for ANU photo scenes (faithful path only)

Describe activity, scale, and mood --- not architecture. The reference images
carry the architectural context; the prompt only needs to describe what's
happening in the scene.

**Never write _sandstone_.** Avoid adjacent terms that bias toward Oxbridge /
ivy-league / heritage-stone aesthetics: _ivy_, _ivy-covered_, _neo-Gothic_,
_gothic_, _Oxford-style_, _Cambridge-style_, _cloistered_, _quadrangle_,
_spires_, _stone facade_, _historic university_. ANU's campus is mid-century
modernist with brutalist and contemporary additions (Kambri); it doesn't read as
a heritage-stone institution, and prompts that reach for that register produce a
generic "old university" image that obviously isn't ANU.

## Parity-fix spare

The compile step may produce an odd page count. For preset-driven runs, the
calling preset specifies one extra inline figure prompt as a spare: don't
generate it during the parallel dispatch, but have the prompt and reference set
chosen so it can be generated on demand if the parity-fix step needs it. For
faithful from-source runs, the parity-fix uses a blank page rather than an
invented figure --- see `skills/_shared/typst-layout.md`.
