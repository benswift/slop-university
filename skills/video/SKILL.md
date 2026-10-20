---
name: video
description: >-
  Make one Slop University video, a research explainer of an output or a promo,
  as a script and a beat spec on the template engine, voiced, scored, reviewed,
  encoded and staged as a research output for `bin/slopu land`. Invoked by
  `bin/slopu video`.
---

# A Slop University video

You make one video and stage it. A video is a research output like any other: it
has an id, a DOI, an outputs entry and a landing page, counts in the
University's numbers, cites the outputs it explains or shows, and is announced
by a news post. You never commit, upload or push: a human watches the drafts and
lands it with `bin/slopu land <id>`.

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
2. **Scaffold.** `video/_kit/templated.py new --kind <kind> --title "<title>"`
   prints the video's id (`slop-explainer-<slug>-<seed>` or `slop-promo-...`);
   every later step takes it. It also draws the video's one orientation,
   landscape or portrait, and says which; pass `--orientation` only when the
   steering names one. In `video/<id>/spec.json` fill the output's metadata as
   an outputs entry has it (`skills/publish/SKILL.md` §2A): `subtitle`
   (optional), `summary` (two to four sentences in the comms register, what the
   video shows), `topic`, `authors` (roster names: an explainer's are its
   output's; a researcher's promo is theirs; a University promo has none) and
   `school`. Set `output` (an explainer's output id) or `person` (a researcher
   promo's id): that page then opens with the video. The outputs a spec explains
   or shows are what the video cites, harvested at landing; never write `cites:`
   yourself.
3. **Script**, `video/scripts/<id>.md`: `## Key idea`, then `## Script` with one
   `**VO:**` (or `**VO (id):**`) paragraph per line, `[beat n]` pauses, and a
   `_Visual:_` line under each saying which beat shows it. The last line is the
   call to action when there is one ("Find out more at the website ..."). Say
   exact strings (addresses, DOIs) by name, never letter by letter; the screen
   shows them.
4. **Spec**, `video/<id>/spec.json`: one beat per line or two (below). Every
   `at` is a word that line really says.
5. **Make it**, from `video/`: `_kit/templated.py fetch <id>`, then `./video.sh`
   (the styled-video skill's `video.py`) `voice`, `music`, `mix` (it must log
   the master on target), `check`, `render`, `stills`, each with the id.
6. **Review**, the gate. Open every contact sheet in `video/out/<id>/stills/`
   and look: nothing overlaps or runs off the frame, each beat shows what its
   line says while it says it, the numbers on screen match the source, no frame
   is empty while a line plays. Listen to `assets/mix.wav` segments where the
   stills look wrong. Fix the spec or the script and go again; at most three
   rounds, then stop and report what is still wrong.
7. **Encode and stage**: `./video.sh signage <id>`, `./video.sh web <id>`, then
   `_kit/templated.py stage <id>`, which writes the outputs and videos entries
   and stages the encodes and images under `data/pending-uploads/<id>/`.
8. **News post**, `website/src/content/news/<date>-<slug>.md`, announcing the
   video with `output: <id>`, per `skills/publish/comms.md` (its
   read-the-recent- eight check included). It links the output it explains, or
   the researcher's profile, wherever it names them.
9. **Report**: the id, the key idea, the orientation, the draft's path
   (`video/out/<id>/<id>-draft.mp4`), and anything the review could not fix.
   Then stop.

## Beats

A beat starts on its `line` (an index into the spoken lines, from 0), or on the
word `from` names in it, and holds until the next beat: a long line can carry
two beats. `at` is a word of that line, or `[line, word]`. Images are
references: `{"output": id}` (its hero), `{"thumb": id}` (its first page),
`{"page": [id, n]}` (page n of its PDF), `{"person": id}` (a researcher's hero),
`{"headshot": id}`. `video/_kit/beats.js` is the engine.

| type        | fields                                                                                           | for                                                        |
| ----------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------- |
| `hero`      | `image`, `title`, `tagline`, `byline`, `clear` (word)                                            | the opening, always first                                  |
| `statement` | `text`, `highlight` (a phrase of it, in gold), `kicker`, `at`                                    | a claim or finding in type                                 |
| `stat`      | `value`, `label`, `format` (`number`, `money`, `decimal`), `prefix`, `suffix`, `at`              | one number, counting up                                    |
| `stats`     | `items`: two or three stats, each with its own `at`                                              | numbers side by side                                       |
| `figure`    | `image` (a `page`), `crop` [x, y, w, h], `label`, `focus`: [{`at`, `box`}]                       | a page or figure, pushing in                               |
| `pages`     | `outputs` (ids), `at`, `until`                                                                   | covers dropping into a grid                                |
| `people`    | `people` (ids), `at` (one word, or one per person)                                               | the researchers; one is shown large                        |
| `quote`     | `text` (verbatim), `highlight` (a phrase of it), `attribution`, `image`, `spoken`, `at`, `until` | a passage quoted from the source, or a speaker's own words |
| `cards`     | `items`: [{`title`, `text`, `at`}] (two to four)                                                 | steps or points in turn                                    |
| `close`     | `line` (the call to action's line), `cta`: true                                                  | where to find the University, then the lockup; always last |

A sentence lifted from the source is a `quote`, never a `figure` crop of the
typeset page: video can set it, build it and light it, and a crop of body text
only shows that a page exists. Its `text` is the source's words exactly (take
them from `pdftotext`); over an `image` (the output's or a speaker's hero) it
sits under a scrim. With `spoken: true` the line's voice reads it and each word
lights as it is said, with the attribution up from the start; otherwise it
builds phrase by phrase until `until`. A `figure` is for what only a picture
holds: a chart, a diagram, a photograph, a table.

Fractions (`crop`, `box`) are of the whole page image. To find a figure, look at
the page: `pdftoppm -png -r 60 -f n -l n` gives a quick view to measure from.
Keep a beat on screen at least three seconds; split a long line's visuals across
two beats rather than crowding one.
