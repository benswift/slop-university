# Lighter by Design

The Slop University Sustainability Initiative, as a three-minute sizzle reel:
the University's research output and the real energy and carbon cost of making
it, set against the sector's. It plays straight until the University's footprint
is on screen, then steps outside the fiction as the colophon does, says the
numbers are real and how they were counted, and steps back in to close.
Landscape, about three minutes, for HORIZONS (Venice, 18--22 November 2026) and
for a sustainability page on the site that carries the same figures and the
method.

Every figure is a central estimate as of 9 November 2026 (the working is in
`analysis/sustainability/estimate.py`). The sector figures are sums built from
members' own reports, since no group publishes one: Go8 (ANU, Melbourne, Sydney,
UNSW and Monash, 2025) and LERU (Imperial, Copenhagen and Helsinki, 2023--24),
each about 16 tCO2e per publication on OpenAlex counts; the Go8 five publish
about 1.5 works per staff member a year.

## Key idea

Slop University is the most productive and, per output, the greenest university
there is, because it has no buildings, no commutes and no flights; the numbers
are real, and so is the trade it makes for them.

## Timing

HORIZONS takes 3:00 to 5:00; target 3:15 to 3:30 so trimming holds can't push it
under. Time the generated voice before animating, then lengthen the holds at the
bar-chart pull-back, the fine-print fill and the final grid to reach the target.
Hold the final website address for six seconds beyond its marked pause. Check
the duration of the exported 1080p30 file, not the composition.

The narrator is a voice made with ElevenLabs Voice Design (from a description,
no one's recordings), not the house Voice Library voice, which is a clone of a
real person. Render the submission natively at 1920×1080, 30 fps
(`data-fps="30"`); the 4K50 master can follow after the deadline.

## The fine print

Every figure on screen carries its working in a small source line in the bottom
left corner, above the caption band. From "Measured*" on, each straight claim
also leaves an asterisked footnote that stacks in the bottom right corner and
stays there; the _Visual_ notes name each one. The stack is the greenwashing
advert's small print, and at the turn it becomes the screen.

## Generated clips and the QR code

Four shots are short Veo 3.1 clips animated from house-style stills (the only
generated motion; everything else is the composition): the document press
opening, the campus quad emptying, the server-room technician leaving, and the
empty lecture theatre going dark. Each counts in the film's own footprint.

A viewer can arrive or leave at any point of a looping programme, so a QR code
for `slop.university/sustainability` returns in the top right corner every forty
seconds or so, held for about twelve, and fills the frame at the close.

## Script

**VO (horizons-narrator):** At Slop University, we publish more research than
ever. [beat 0.4] And we do it lighter than anyone. [beat 1.0]

_Visual:_ the document press clip (the press running flat out, its operator's
chair empty) under the scrim with the title block: the lockup, "Lighter by
Design", a gold rule, "The Slop University Sustainability Initiative". On
"lighter" the title block clears.

_Reads:_ 1. this is the University's sustainability initiative.

**VO (horizons-narrator):** Since July, our forty-one researchers have published
three thousand, two hundred and twenty-one research outputs. [beat 0.3] Papers,
posters, theses, strategies, [beat 0.2] and films. [beat 1.0]

_Visual:_ covers drop into a grid, faster and faster, and a counter climbs to
3,221; on each of "papers", "posters", "theses", "strategies" and "films" one
cover of that kind lifts out of the grid and settles back.

_Reads:_ 1. there are thousands; 2. of every kind.

**VO (horizons-narrator):** That's more than two hundred outputs per staff
member, every year. [beat 0.4] Australia's leading research universities manage
about one and a half. [beat 1.0]

_Visual:_ two stats side by side: "224" in gold, "per staff member per year",
and "1.5" in ink.

_Reads:_ 1. ours is a hundred and fifty times theirs.

**VO (horizons-narrator):** Every one of those outputs has a carbon footprint.
[beat 0.3] So we measured it. [beat 1.0]

_Visual:_ the grid stills; one output's cover lifts out and comes forward; a
gold meter draws on beside it, empty. On "measured", the word "Measured*"
appears beside the meter, and the first footnote, "*estimated", starts the stack
in the bottom right corner.

_Reads:_ 1. we're following one output now.

**VO (horizons-narrator):** A Slop University output takes about one kilowatt
hour of electricity. [beat 0.4] About five full kettles. [beat 1.0]

_Visual:_ the meter fills to "1 kWh"; five kettles draw on in a row beneath it,
one per beat of the line's last phrase. Footnote: "*average of all outputs".

_Reads:_ 1. one output, one kilowatt hour; 2. that's small.

**VO (horizons-narrator):** That's about four hundred grams of carbon dioxide
per output. [beat 0.4] At leading research universities, in Europe and in
Australia, [beat 0.2] it's about sixteen tonnes. [beat 1.2]

_Visual:_ two bars from a shared baseline. Ours, "0.4 kg", is a sliver of gold.
The sector's, in ink, grows past the top of the frame; the camera pulls back,
logarithmically, until its top comes into view and the gold sliver is a speck.
Footnotes: "*US grid, 2025 average"; "*theirs counts buildings, travel and
teaching".

_Reads:_ 1. ours is tiny; 2. theirs is forty thousand times larger.

**VO (horizons-narrator):** And we're getting lighter. [beat 0.3] Since July,
the energy behind each output has fallen by more than half. [beat 1.0]

_Visual:_ the gold sliver splits into a row of monthly slivers, July to
November, each shorter than the last. Footnote: "*per output".

_Reads:_ 1. a proud efficiency gain.

**VO (horizons-narrator):** How do we do it? [beat 0.4] We have no buildings to
heat or cool. [beat 0.3] No car parks. [beat 0.2] No commutes. [beat 0.3] And no
conference travel. [beat 1.0]

_Visual:_ the campus quad clip, locked off: the people walk out of frame one by
one until the quad is empty, and it holds empty to the end of the line.

_Reads:_ 1. the things a university burns carbon on; 2. we have none of them.

**VO (horizons-narrator):** Our doctoral theses run to about a hundred and forty
pages. [beat 0.3] Each one takes about two hours to write, [beat 0.2] and emits
about five kilograms of carbon dioxide. [beat 1.0]

_Visual:_ the ten theses' covers stand in a row like spines on a shelf; one
comes forward and its pages riffle through; a clock face beside it sweeps two
hours; a gold "4.9 kg" lands under it. Footnote: "*unexamined".

_Reads:_ 1. these are our theses; 2. two hours and five kilograms each.

**VO (horizons-narrator):** One study of a human PhD put it at twenty-one
tonnes, [beat 0.3] over four years. [beat 1.0]

_Visual:_ beside our thesis, a human one in ink; a stack of calendar pages piles
up behind it, four years' worth, and its bar climbs past ours and out of frame.
Footnote: "*one study, 2013".

_Reads:_ 1. a human PhD; 2. thousands of times more.

**VO (horizons-narrator):** Our researchers' working day starts the moment it's
needed, [beat 0.2] and ends the moment it's done. [beat 1.0]

_Visual:_ the roster's headshots fill a grid; each lights as a clock hand passes
over it, then dims.

_Reads:_ 1. these are the researchers; 2. they only exist while they work.

**VO (horizons-narrator):** Since it opened, the whole University has emitted
about one point three tonnes. [beat 0.4] Less than one return flight from
Australia to Venice. [beat 1.4]

_Visual:_ a map line arcs from Canberra to Venice and back; beside it, the
flight's bar in ink and the University's in gold, the gold one shorter.
Footnote: "*economy class, CO2 only".

_Reads:_ 1. this is the whole University's footprint; 2. it is less than one
flight.

**VO (horizons-narrator):** These numbers are real. [beat 0.6] Slop University
is an artwork. [beat 0.3] Its researchers and their outputs are generated by
language models, [beat 0.2] running on a timer. [beat 1.0]

_Visual:_ on "real", the footnote stack rises out of its corner and fills the
frame, every asterisk at full size; on "an artwork", a hard cut to the server
room clip, where the technician turns and wheels his trolley away down the
aisle; on "timer", a hard cut to the colophon's plain ground and the clock face
from the colophon draws on, its hand ticking once a beat.

_Reads:_ 1. we've stepped outside the fiction; 2. the same machine as the
colophon.

**VO (horizons-narrator):** We counted every token the models read and wrote,
[beat 0.2] and the images they made, [beat 0.3] then turned them into energy
with the best published estimates. [beat 0.3] The method is on our website.
[beat 1.0]

_Visual:_ two counters on the clock face: "40 billion tokens", "8,759 images";
arrows from both run into a single gold figure, "3.3 MWh".

_Reads:_ 1. what was counted; 2. what it came to.

**VO (horizons-narrator):** We didn't count the training of the models, [beat
0.2] the chips they run on, [beat 0.2] or the water that cools them. [beat 0.3]
The companies that make the models don't publish those figures. [beat 1.0]

_Visual:_ three new footnotes type on beneath the gold figure, one per phrase:
"*excludes model training", "*excludes hardware", "*excludes water". The gold
figure stays the same size.

_Reads:_ 1. what wasn't counted; 2. and why.

**VO (horizons-narrator):** Much of that energy went on the models rereading
what they had already read, [beat 0.2] again and again. [beat 1.0]

_Visual:_ one block of text passes through a model box; the same block loops
back and passes through again, faster, leaving a gold trace each time.

_Reads:_ 1. the same text, read over and over.

**VO (horizons-narrator):** Each output now takes less than half the energy it
did in July. [beat 0.4] We didn't use less. [beat 0.3] We made more than twice
as many. [beat 1.2]

_Visual:_ the monthly slivers return, shrinking left to right; behind each, a
stack of covers for that month's outputs rises, until the stacks' total gold
area matches from month to month.

_Reads:_ 1. the efficiency gain again; 2. it all went into more.

**VO (horizons-narrator):** Making this film took about twenty kilowatt hours.
[beat 0.3] As much as twenty of our outputs. [beat 1.0]

_Visual:_ this film's own timeline as a strip of thumbnails; a gold meter beside
it fills to its figure, and covers drop in beside the meter, one per kilowatt
hour.

_Reads:_ 1. the film counted too.

_Reads note:_ "twenty" is provisional until the film's own energy is measured
(voice, music, generated clips, renders, the session's tokens); re-voice this
line with the real figure.

**VO (horizons-narrator):** Per output, Slop University may be the greenest
university in the world. [beat 0.6] It has also never taught anyone anything.
[beat 1.6]

_Visual:_ the gold sliver from the bar chart returns, alone on the ground. On
"never taught", a cut to the empty lecture theatre clip: rows of empty seats, no
lecturer, and the projection screen's light slowly going out.

_Reads:_ 1. the claim is true; 2. and so is this.

**VO (horizons-narrator):** Slop University. [beat 0.3] More research, [beat
0.3] less of everything else. [beat 1.0]

_Visual:_ back into the sizzle: the cover grid fills the frame again, at full
speed, and the counter keeps climbing past 3,221.

_Reads:_ 1. it is still running.

**VO (horizons-narrator):** Read our full sustainability report on the website.
[beat 2.0]

_Visual:_ `slop.university/sustainability` appears beside its QR code, full
size; it clears to the closing lockup: the rules grow, then the crest and
wordmark fade in.

_Reads:_ 1. where to find the figures.
