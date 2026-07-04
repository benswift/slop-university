# Shared: the Slop University house visual style

One visual style for **every generated image in the project** --- PDF covers and
inline figures, poster heroes and field images, website page heroes,
department-page art, and roster headshots. Charts are the one exception: they
follow `chart-workflow.md` (gribouille + the brand palette), not this file.

The style: **two-ink editorial illustration in a risograph / screen-print
register**.

- **Two inks on paper**: lockup gold `#b97d1c` and ink black `#1a1a1a` on warm
  cream. Tints of either ink (screened dots, flat tint blocks) are allowed; no
  third hue, ever.
- **Flat shapes, drawn not photographed**: bold simplified geometry, cut-paper /
  screen-print flatness, mid-century editorial-illustration register. The
  drawing geometry sits in the same register as Public Sans and the crest's flat
  heraldry.
- **Visible print grain**: risograph texture, slight ink noise; subtle
  misregistration between the two inks is welcome (it sells the print).
- **No photorealism.** No photographic rendering, no camera depth-of-field, no
  lens artefacts. If it could be mistaken for a photo, it's off-style.
- **No text baked into images.** No lettering, signage, labels, or wordmarks
  inside the artwork --- typography belongs to the document layer.

## Why this style (doctrine, not taste)

- a two-ink constraint holds consistent across image-gen runs --- the practical
  failure mode of generated imagery is drift, and a hard palette is the anchor
- stylised portraits are the **resemblance guard** that makes fictional
  headshots safe --- an illustrated bust can't be mistaken for a photograph of a
  real person
- it dissolves the ANU-campus-photo tether entirely: nothing in the imagery
  points at a real place or person
- the satire lands: an artisanal, hand-printed aesthetic applied by a fully
  automated firehose --- the brand more coherent than the research

## Prompt formula

Every `ben:styled-image-gen` call for project imagery uses this shape:

> Two-ink risograph illustration of \<scene --- activity, apparatus, mood\>.
> Flat gold and black ink shapes on warm cream paper, visible print grain,
> subtle misregistration, screen-print texture, bold simplified geometry,
> mid-century editorial illustration style. No text, no lettering, no
> photorealism.

Fill in only the \<scene\>. Describe activity, scale, and mood --- the style
clause is fixed and carries the rest. Never ask for a photo, a specific real
place, or a recognisable person.

**References**: pass 3--5 `--input-image` refs from `references/slop-style/`
(the curated seed set) chosen to match the scene type --- e.g. a campus scene
exemplar for a campus scene, the portrait exemplar for a headshot. The refs
carry the palette and print texture; vary the selection across a run's prompts
and between runs.

## Portraits (roster headshots)

- bust-length, facing the viewer or a relaxed three-quarter turn, neutral
  academic ground (flat cream or a single flat tint block)
- same two inks; face and features as flat shapes with minimal linework ---
  stylised, warm, unmistakably an illustration
- generated **once per researcher**, stored in `canon/headshots/`, and reused
  everywhere the genre expects an author photo (site profiles, press releases
  where apt, paper-adjacent bios) --- a researcher's face must not drift between
  outputs
- **resemblance guard**: stylisation makes accidental likeness unlikely, but
  still eyeball every portrait against "could this be read as a specific real
  person?" before it enters the canon; regenerate on any doubt

## The seed set (`references/slop-style/`)

A curated, fully-generated exemplar set --- no real photos, ever. Minimum
viable: ~5--8 images covering at least one campus scene, one interior/lab, one
abstract research motif, one portrait. Preset and publish runs steer
`ben:styled-image-gen` with these instead of any photographic reference.

Curation bar for adding an image (seed or promoted from a run):

- reads as two-ink print at a glance --- gold + black on cream, nothing else
- flat illustration, not a filtered photo; no photoreal passages
- no text artefacts, no watermark-like marks
- no resemblance to a real person, and no recognisable real building or place
- carries print grain / texture (a too-clean vector look is off-style)

Encode additions to AVIF per the references recipe: resize to 1280px on the long
edge, then `avifenc -j 4 -s 6 --min 0 --max 63 -a end-usage=q -a cq-level=28`
(~100 KB).

The canon grows from real runs: promote the best generated images back into
`references/slop-style/` over time (the promotion mechanism lives in
`image-workflow.md`), so the institution accretes its own visual world.

## Off-limits

- real photographs as references or outputs (the real-ANU `references/*.avif`
  photos are retired from preset/publish runs; they serve only the local-only
  faithful path)
- any third colour; full-colour "riso-ish" images are the drift this doctrine
  exists to stop
- photorealistic portraits (the resemblance guard is the style)
- text, logos, or lockups inside generated artwork
