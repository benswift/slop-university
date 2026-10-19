# The Queue as Leading Indicator, Explained

The research explainer of `slop-poster-coffee-cart-queue-lengths-sn9kzr` (doi
10.5555/slop.sn9kzr), by Casimir Beng and Osei Vandermeer of the School of
Continuous Improvement and Anneke Tolan of the School of Emergent Priorities.
Every number is the poster's; the closing line is the poster's own pull quote,
in Beng's voice. The poster's chart overprints its y-axis labels, so the chart
is cut from the PDF without its y-axis, at 1250 dpi, into `assets/chart.png`
after `fetch` (which resolves no `file` reference):
`pdftoppm -png -singlefile -r 1250 -x 8221 -y 5792 -W 5050 -H 1500 <pdf> assets/chart`.
After `voice`, and before `mix`, on `assets/voice.wav`: Tolan's four segments
and Beng's two are matched to the narrator's median segment loudness (hers come
back 7--11 dB under, his last 8.6 dB under); the 0.5 s of dead air that ends
Vandermeer's "afterwards." is zeroed (hence its short `[beat]`); and the breath
after Tolan's "proxy," and "causal," is faded out.

## Key idea

The queue at nine campus coffee carts ran two quarters ahead of the University's
international ranking, steadily enough (peak cross-correlation 0.78) that the
authors propose letting the live queue index steer a fixed share of
discretionary grant strategy, with no manual override.

## Script

**VO:** A university's international ranking moves slowly, [beat 0.3] and it's
read late, often a year after the work that drove it. [beat 0.9]

_Visual:_ beat 0 (hero): the poster's hero, a queue at a campus coffee cart
under a rising line, under the scrim with the title block.

**VO:** A research poster from the School of Continuous Improvement asks whether
everyday campus data could see those moves coming. [beat 0.3] Does the coffee
queue know first? [beat 1.4]

_Visual:_ beat 1 (figure): the poster's page, whole; then from "Does" beat 2
(statement): the question in type, "know first" in gold.

**VO:** Nine coffee carts were fitted with overhead depth sensors. [beat 0.3]
Every five minutes, for twenty-four months, [beat 0.1] each sensor counted the
queue below it. [beat 0.9]

_Visual:_ beat 3 (stats): 9 carts, 5 minutes and 24 months, each as it is said.

**VO (osei-vandermeer):** We counted heads, not faces, [beat 0.2] and kept no
transactions. [beat 0.3] We registered the lag window and thresholds in advance,
[beat 0.2] and adjusted none of them afterwards. [beat 0.4]

_Visual:_ beat 4 (people): Osei Vandermeer, large, with his title and school.

**VO:** Set against the University's monthly ranking, [beat 0.2] the queue ran
two quarters ahead. [beat 0.3] It peaked in March twenty twenty-four, [beat 0.2]
and the ranking rose that September. [beat 0.9]

_Visual:_ beat 5 (figure): the poster's chart, the queue-length index in gold
over the ranking index in ink, pushing in on quarters four to eight on "peaked".

**VO:** At that lag, cross-correlation reached point seven eight. [beat 0.4] The
lead held for both morning and afternoon queues, [beat 0.2] strongest at the
carts nearest the senior common room. [beat 0.9]

_Visual:_ beat 6 (stat): 0.78; then from "lead" beat 7 (quote, spoken): the
poster's own sentence over its hero, lighting as the narrator reads it.

**VO (anneke-tolan):** Our results are consistent with the queue as an early,
low-cost proxy, [beat 0.2] for the activity that ranking bodies later reward.
[beat 0.3] It's correlational, not causal, [beat 0.2] but it held steady across
the whole trial. [beat 0.9]

_Visual:_ beat 8 (people): Anneke Tolan, large, with her title and school; then
from "It's" beat 9 (statement): "stable across the trial" in gold.

**VO (osei-vandermeer):** Next, we propose closing the loop: [beat 0.2] a pilot
that steers a fixed share of discretionary grant strategy from the live queue
index, [beat 0.2] with no manual override. [beat 0.9]

_Visual:_ beat 10 (statement): the pilot in type, "with no manual override" in
gold.

**VO (casimir-beng):** Queue length led every ranking movement we observed, by a
stable two quarters. [beat 1.0]

_Visual:_ beat 11 (quote, spoken): his words, the poster's pull quote, over his
portrait, lighting as he says them, then the close: the lockup.
