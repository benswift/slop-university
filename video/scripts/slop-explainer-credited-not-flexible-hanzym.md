# Credited, Not Flexible, Explained

The research explainer of `slop-paper-a-regression-discontinuity-gj2xye` (doi
10.5555/slop.gj2xye), by Lindiwe Achterberg and Anneke Tolan of the School of
Emergent Priorities and Casimir Beng of the School of Continuous Improvement.
Every number is the paper's (the 58, 22 and 36 as its abstract and Figure 1 give
them); the closing line is Achterberg's quote in the paper's news post.

The two charts are the paper's own figures, each rendered alone from its PDF
into `assets/figures/` (`fetch` skips `file` references), so they stay sharp at
4K. Figure 2 is cut above its x-axis labels, which overprint each other, and the
figure's label names the bars instead. After `fetch`, from `video/<id>/`, with
the PDF at `assets/pdf/slop-paper-a-regression-discontinuity-gj2xye.pdf`:

    pdftoppm -png -singlefile -r 1400 -f 3 -l 3 -x 6440 -y 2296 -W 3752 -H 1503 <pdf> assets/figures/fig1
    pdftoppm -png -singlefile -r 1400 -f 4 -l 4 -x 2128 -y 2613 -W 3659 -H 1232 <pdf> assets/figures/fig2

After `voice`, and before `mix`, on `assets/voice.wav` (kept first as
`voice-raw.wav`): every researcher segment is matched to the narrator's median
segment loudness (Tolan's come back 4--13 dB under, Beng's "Only the words do."
5 dB over); the release of the narrator's "around." and the final "s" of Tolan's
"results.", which the trim cuts, are written back from their cached takes; and
the 0.25 s that ends Beng's "logged incidents." segment, silence and then a
click, is zeroed.

## Key idea

At one retail and hospitality chain, crossing a rostering app's weekend
fairness-credit threshold (six weekend shifts in a rolling eight weeks) is
followed by a 36-point fall in how often a supervisor's next appraisal calls the
worker flexible, while nothing about the worker's hours, shift swaps or
incidents changes, and the chain now proposes writing the tally into the
appraisal itself.

## Script

**VO:** At one national retail and hospitality chain, a rostering app keeps a
fairness-credit tally of each worker's weekend shifts. [beat 0.9]

_Visual:_ beat 0 (hero): the paper's hero under the scrim, with the title block.

**VO:** At six in a rolling eight weeks, [beat 0.2] it stops offering them
weekend shifts. [beat 0.3] And nothing in its rules touches a worker's
appraisal. [beat 1.0]

_Visual:_ beat 1 (stat): 6 weekend shifts, on "six"; then from "And" beat 2
(statement): "Nothing in its rules touches the appraisal.", "touches the
appraisal" in gold.

**VO:** A paper from the School of Emergent Priorities asks whether it does
anyway. [beat 0.3] When a worker crosses that line, [beat 0.1] does their
supervisor describe them differently? [beat 0.9]

_Visual:_ beat 3 (figure): the paper's first page, whole; then from "When" beat
4 (statement): the question in type, "describe them differently" in gold.

**VO (lindiwe-achterberg):** A worker one shift either side of the line is much
the same worker. [beat 0.3] So we followed four hundred and thirty-eight casual
and part-time staff, [beat 0.1] at twenty-four outlets. [beat 0.9]

_Visual:_ beat 5 (people): Lindiwe Achterberg, large, with her title and school;
then from "So" beat 6 (stat): 438 staff, counting up, at 24 outlets over 18
months (the label carries the 18 months).

**VO:** The team searched each worker's next appraisal for words like flexible,
adaptable, and easy to roster around. [beat 0.9]

_Visual:_ beat 7 (statement): three of the paper's flexibility terms, "Easy to
roster around." in gold.

**VO:** Just under the threshold, fifty-eight per cent of appraisals used one.
[beat 0.3] Over it, only twenty-two. [beat 0.4] That's a fall of thirty-six
points, and it stayed down. [beat 1.3]

_Visual:_ beat 8 (figure): Figure 1, the share of appraisals using a flexibility
term either side of the threshold; then from "That's" beat 9 (stat): the
36-point fall, from 58% to 22%.

**VO (casimir-beng):** We also checked the things the threshold ought to move.
[beat 0.6] Rostered hours, shift swaps, logged incidents. [beat 0.2] None of
them move. [beat 0.3] Only the words do. [beat 0.9]

_Visual:_ beat 10 (people): Casimir Beng, large, with his title and school; then
from "Rostered" beat 11 (cards): hours, shift swaps and incidents, each as it is
said, none with a jump.

**VO:** As a check, three placebo cutoffs, where the app enforces nothing, show
no such jump. [beat 0.9]

_Visual:_ beat 12 (figure): Figure 2, the estimated jump at the real threshold
beside the three placebos.

**VO (anneke-tolan):** The chain has already seen an early version of our
results. [beat 0.7] It now proposes filling in each draft appraisal with a
flexibility rating, [beat 0.2] worked out from the same tally. [beat 0.9]

_Visual:_ beat 13 (people): Anneke Tolan, large, with her title and school; then
from "It" beat 14 (statement): the chain's proposal, "worked out from the tally"
in gold.

**VO (lindiwe-achterberg):** A threshold built to even out the weekend roster
has ended up deciding what a supervisor writes down, [beat 0.2] and the worker
never sees either number. [beat 1.0]

_Visual:_ beat 15 (quote, spoken): her words, the news post's pull quote, over
her portrait, lighting as she says them, then the close: the lockup.
