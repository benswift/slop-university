# Slop University video style

The project half of the `styled-video` skill (in Ben's `ben` plugin): the skill
carries the method and the craft, this file carries what is particular to Slop
University.

## Where things live

- `video.toml`: the narrator's voice and the music prompt, read by the skill's
  `scripts/video.py` (its docstring lists the commands and the keys). Run it
  from anywhere under `video/`.
- `scripts/<slug>.md`: each video's key idea and its script, with a `_Visual:_`
  direction and a `_Reads:_` list per stretch of picture.
- `<slug>/`: the HyperFrames project: `index.html` (landscape),
  `compositions/portrait.html` (the portrait cut, when there is one),
  `<slug>.js` (the shared `build`), `timing.json` and `captions.vtt` (written by
  `video.py voice`), `assets/` (audio and the output's fetched images, not
  committed) and a `kit -> ../_kit` symlink.
- `_kit/`: `kit.css`, `kit-light.css` (a cream cut) and two symlinks into
  `node_modules` (run `pnpm install` here first): `motion ->` astromotion's
  `video/`, `brand ->` astro-theme-slop.
- `out/`: renders, stills and the TTS cache (gitignored).

`sting/` is the smallest composition: one output's hero and title block, then
the lockup, with no voice. `output.json` names the output; its hero is
`https://img.slop.university/heroes/outputs/<id>-2560.avif`, fetched into
`assets/hero.avif`.

## Sources of truth

- **Stage and brand**: `kit.css` imports astromotion's `video/stage.css` and
  astro-theme-slop's `video/slop-dark.css` (ink ground, cream, lockup gold
  `#b97d1c`). The opening hero, title block and closing lockup are astromotion's
  `video/brand.js`, given astro-theme-slop's `video/brand.js` logos and lockup.
- **What a video says** comes from the output it explains: its entry in
  `website/src/content/outputs/`, its PDF, its figures. A video adds no finding,
  number or claim the output doesn't make.
- **People** are the output's authors, from `canon/roster.yml`. The
  Vice-Chancellor is an office, never a name or a voice.

## The look

- **Two inks on ink.** Cream type and linework with gold accents on the house
  ink, the ground the signage screens show the posters on: the two-ink register
  of the house imagery (`skills/_shared/visual-style.md`) turned dark. Gold is
  for what the viewer should be looking at. A cream cut, when one is wanted,
  links `kit/kit-light.css` and sets `data-theme="light"` on its stage, so a
  `build` takes its logos and inks from the theme, never hard-coded.
- **The output's own imagery opens a video.** Its hero runs full-frame under the
  scrim, which holds the ink solid behind the title block and lifts the top edge
  under the logo (`kit.css`). The title block is the horizontal lockup, the
  title, a gold rule, the subtitle and the byline (authors, school).
- **Light type.** Public Sans; display at weight 300.
- **It reads straight.** A Slop University video is a university's research
  explainer played completely straight: no wink, no satire signal on screen or
  in the voice. The joke is the genre, as in the documents.
- **Captions** are always on, in the band below the scene: a signage screen is
  usually muted.
- **It closes on the lockup**: the rules grow from the frame's edges, then the
  crest and wordmark fade in.
- **Formats.** Landscape 1920×1080 and a portrait cut at 1080×1920 from the same
  `build`. Masters 4K at 50 fps, drafts 1080p25.
- **Signage.** `video.py signage` encodes both cuts for the screens; their files
  go in the PDF bucket (`ops/bucket-sync.py upload`) and are named in
  `website/src/content/videos/<slug>.yml`, which puts the video between the
  posters.

## Sound

The narrator is an ElevenLabs voice (`video.toml`), never a real person's. The
music is an ElevenLabs bed composed from the prompt in `video.toml`;
`video.py mix` ducks it under the voice and fades it to silence at both ends.
