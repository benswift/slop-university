# Where the Maybe Goes

A researcher promo for Dr Ingrid Vasseur, Lecturer and Convenor of Futures in
Committee in the School of Emergent Priorities: mostly in her own voice, with
the narrator framing it. Her numbers are the site's own
(`website/dist/facts.json`): 895 citations and an h-index of 25 from 159
research outputs, the fewest of any researcher at an h-index of 25 or above (the
next fewest, 168, reached 26). Her example is her first-authored paper on the
School's own committee work, _Minuted Into Certainty_
(`slop-paper-coding-how-much-bbdyys`, with Dr Anneke Tolan): 96 Horizon Register
scan entries matched to their minutes, the median hedge count falling from five
per entry to zero in the minute.

Two hand steps outside the spec (`assets/` is gitignored), to redo before a
re-render. Beat 4's chart is the paper's Figure 1 rendered on its own at 1000
dpi, so it stays sharp in the 4K cut. From `video/`:
`pdftoppm -png -singlefile -f 3 -l 3 -r 1000 -x 1265 -y 7916 -W 2778 -H 1345 slop-promo-where-the-maybe-odv1lx/assets/pdf/slop-paper-coding-how-much-bbdyys.pdf slop-promo-where-the-maybe-odv1lx/assets/fig1`
(the PDF from `https://pdf.slop.university/<id>.pdf`). And after every `voice`,
before `mix`, on `assets/voice.wav` (written float32): three takes end in a gap
and a click, so zero 11.94--12.50 s ("Priorities."), 23.45--23.79 s ("minuted,")
and 30.46--30.85 s ("twenty-five.") behind a 30 ms fade; and "I want to know"
comes back ~5 dB hot, so lower 38.85--39.46 s by 5 dB. The times hold while the
takes come from the TTS cache and the `[beat]`s stand.

## Key idea

Ingrid Vasseur follows the maybes of foresight talk into the committee room to
see which survive the minutes (in ninety-six scan entries, the typical five were
gone by the time each was minuted), and no one at Slop University has reached an
h-index of twenty-five with fewer outputs.

## Script

**VO (ingrid-vasseur):** Ask people about the future, [beat 0.2] and you'll hear
a lot of maybes. [beat 0.6]

_Visual:_ beat 0 (hero): her person hero, at a committee table where a ribbon of
road runs in from the horizon to a stack of papers, under the scrim, with the
title block: "Where the Maybe Goes", "Dr Ingrid Vasseur and Futures in
Committee", "School of Emergent Priorities".

**VO:** Dr Ingrid Vasseur convenes Futures in Committee, [beat 0.15] the seminar
series of the School of Emergent Priorities. [beat 0.1]

_Visual:_ beat 1 (people): her headshot, large, with her name, title and school,
on "Dr", dissolving in as the hero's backdrop clears.

**VO (ingrid-vasseur):** I follow those maybes into the committee room, [beat
0.2] to see which ones survive. [beat 0.5]

_Visual:_ beat 2 (statement): the line in type, "to see which ones survive" in
gold, under "Futures in Committee".

**VO (ingrid-vasseur):** We matched ninety-six scan entries to their minutes.
[beat 0.5] A typical entry had five maybes. [beat 0.2] By the time it was
minuted, [beat 0] none were left. [beat 0.7]

_Visual:_ beat 3 (figure): the hero of _Minuted Into Certainty_, a stack of
marked-up papers beside a clean sheet in a hand, labelled with its title,
pushing in on the marked-up stack at "matched"; from "A", beat 4 (figure): the
paper's Figure 1, the median hedge count per scan entry against its minute, gold
bars for the entries and none for the minutes, whole.

**VO:** Eight hundred and ninety-five citations, [beat 0.2] and an h-index of
twenty-five. [beat 0.1]

_Visual:_ beat 5 (stats): 895 and 25 count up, the first as the line begins and
the second on "an", held through the next sentence.

**VO:** No one at Slop University has got there with fewer outputs. [beat 0.3]
She needed just a hundred and fifty-nine. [beat 0.9]

_Visual:_ beat 5 holds; from "She", beat 6 (stat): 159 counts up, "research
outputs".

**VO (ingrid-vasseur):** Every decision starts as a maybe. [beat 0.3] I want to
know [beat 0.15] where the maybe goes. [beat 1.0]

_Visual:_ beat 7 (quote, spoken): her words over her person hero, under the
scrim, each word lighting as she says it, "where the maybe goes." in gold, her
name up from the start.

**VO:** Read her work on our website, [beat 0.15] and find us on Bluesky. [beat
0.4]

_Visual:_ the close: the website address on "Read", then Bluesky on its word,
then the lockup.
