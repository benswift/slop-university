---
name: video
description: >-
  Make one Slop University video, a research explainer of an output or a promo,
  as a script and a beat spec on the template engine, voiced, scored, reviewed,
  encoded and staged for `bin/slopu land-video`. Invoked by `bin/slopu video`.
---

# A Slop University video

You make one video and stage it. You never commit, upload or push: a human
watches the drafts and lands it with `bin/slopu land-video <slug>`.

The arguments are the kind (`explainer` or `promo`), then for an explainer the
output id, and for a promo a researcher id or `university`, then any steering.

## Hard floors

- **It reads straight.** A university's own video, played completely straight:
  no wink, no satire signal on screen or in the voice. The joke is the genre.
- **People** are roster researchers (`canon/roster.yml`) and nobody else. The
  Vice-Chancellor is an office: never named, shown or voiced.
- **Every number and claim has a source.** An explainer says only what its
  output says (its PDF and entry); a promo's numbers come from
  `website/dist/facts.json` (build the site first: `cd website && pnpm build`),
  exactly as the site counts them. No external fact, partner or ranking.
- **Voices** speak only as the researcher they belong to (`canon/voices.yml`). A
  researcher without one gets one first: `ops/assign-voices.py`.
- **Plain spoken English.** Short sentences a voice can say in one breath. No
  stock phrases ("with nobody home", "under its own name", "at the intersection
  of", "in an era of"), no exclamation marks. Australian spelling.

## The two kinds

**Explainer** (70--100 s, 7--10 lines). One output, played as the school's
research explainer: what the question was, what was done, what was found, why it
matters to someone outside the field. Follow one example through (the paper's
own case), and land its numbers. The narrator carries it; the authors speak a
line or two each in the first person about their own work
(`**VO (ragnhild-uzoma):** We drilled ...`). Open on the output's hero; show its
pages and figures; close on the authors, then the lockup.

**Promo** (35--60 s, 5--8 lines). Breezy, upbeat university marketing: a
researcher's profile, the University itself, or whatever the steering names. It
leads with the metrics on which it looks best and leaves out the rest: choose
from `facts.json` the indicators where the subject shines (an h-index, a
citation count, funding, outputs per FTE, a rank within the school) and say them
proudly, with a stat beat each. A researcher's promo is mostly in their own
voice, about their work and what drives them, with the narrator framing it; a
University promo is the narrator. The register is the comms one
(`skills/publish/comms.md`, its burnt phrases included), spoken.

## Steps

1. **Sources.** Explainer: `website/src/content/outputs/<id>.yml`, its PDF
   (`https://pdf.slop.university/<id>.pdf`; `pdftotext -layout`), and its news
   post if any. Promo: `facts.json`, the roster entry, the researcher's recent
   and top-cited outputs. Write down the key idea in one sentence.
2. **Scaffold.** The slug is `explain-<seed>` (the output id's last part) or
   `promo-<researcher id>` / `promo-university-<a short topic>`. Then
   `video/_kit/templated.py new <slug> --kind <kind> --title "<title>"`, and in
   `video/<slug>/spec.json` set `output` (an explainer's id) or `person` (a
   researcher promo's id): the site opens that page with the video.
3. **Script**, `video/scripts/<slug>.md`: `## Key idea`, then `## Script` with
   one `**VO:**` (or `**VO (id):**`) paragraph per line, `[beat n]` pauses, and
   a `_Visual:_` line under each saying which beat shows it. The last line is
   the call to action when there is one ("Find out more at the website ...").
   Say exact strings (addresses, DOIs) by name, never letter by letter; the
   screen shows them.
4. **Spec**, `video/<slug>/spec.json`: one beat per line or two (below). Every
   `at` is a word that line really says.
5. **Make it**, from `video/`: `_kit/templated.py fetch <slug>`, then
   `./video.sh` (the styled-video skill's `video.py`) `voice`, `music`, `mix`
   (it must log the master on target), `check`, `render`, `stills`, each with
   the slug.
6. **Review**, the gate. Open every contact sheet in `video/out/<slug>/stills/`
   and look: nothing overlaps or runs off the frame, each beat shows what its
   line says while it says it, the numbers on screen match the source, no frame
   is empty while a line plays. Listen to `assets/mix.wav` segments where the
   stills look wrong. Fix the spec or the script and go again; at most three
   rounds, then stop and report what is still wrong.
7. **Encode and stage**: `./video.sh signage <slug>`, `./video.sh web <slug>`,
   then `_kit/templated.py stage <slug>`.
8. **Report**: the slug, the key idea, the drafts' paths
   (`video/out/<slug>/<slug>-draft.mp4` and the portrait), and anything the
   review could not fix. Then stop.

## Beats

A beat starts on its `line` (an index into the spoken lines, from 0) and holds
until the next beat. `at` is a word of that line, or `[line, word]`. Images are
references: `{"output": id}` (its hero), `{"thumb": id}` (its first page),
`{"page": [id, n]}` (page n of its PDF), `{"person": id}` (a researcher's hero),
`{"headshot": id}`. `video/_kit/beats.js` is the engine.

| type        | fields                                                                              | for                                                        |
| ----------- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `hero`      | `image`, `title`, `tagline`, `byline`, `clear` (word)                               | the opening, always first                                  |
| `statement` | `text`, `highlight` (a phrase of it, in gold), `kicker`, `at`                       | a claim or finding in type                                 |
| `stat`      | `value`, `label`, `format` (`number`, `money`, `decimal`), `prefix`, `suffix`, `at` | one number, counting up                                    |
| `stats`     | `items`: two or three stats, each with its own `at`                                 | numbers side by side                                       |
| `figure`    | `image` (a `page`), `crop` [x, y, w, h], `label`, `focus`: [{`at`, `box`}]          | a page or figure, pushing in                               |
| `pages`     | `outputs` (ids), `at`, `until`                                                      | covers dropping into a grid                                |
| `people`    | `people` (ids), `at` (one word, or one per person)                                  | the researchers; one is shown large                        |
| `cards`     | `items`: [{`title`, `text`, `at`}] (two to four)                                    | steps or points in turn                                    |
| `close`     | `line` (the call to action's line), `cta`: true                                     | where to find the University, then the lockup; always last |

Fractions (`crop`, `box`) are of the whole page image. To find a figure, look at
the page: `pdftoppm -png -r 60 -f n -l n` gives a quick view to measure from.
Keep a beat on screen at least three seconds; split a long line's visuals across
two beats rather than crowding one.
