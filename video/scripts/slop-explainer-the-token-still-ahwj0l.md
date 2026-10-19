# The Token Still Passes, Explained

The research explainer of `slop-paper-an-open-plan-office-s-h5jlqp` (doi
10.5555/slop.h5jlqp), by Verity Marris and Anneke Tolan of the School of
Emergent Priorities and Casimir Beng of the School of Continuous Improvement.
Every number is the paper's; the closing line is Beng's quote in the paper's
news post.

The three charts are the paper's own figures, each rendered alone from its PDF
into `assets/figures/` (`fetch` skips `file` references), so they stay sharp in
the 4K push-ins. Before `check`, from `video/<id>/`, with the PDF at
`assets/pdf/slop-paper-an-open-plan-office-s-h5jlqp.pdf`:

    pdftoppm -png -singlefile -r 1400 -f 3 -l 3 -x 6852 -y 1375 -W 3229 -H 1629 <pdf> assets/figures/fig1
    pdftoppm -png -singlefile -r 1400 -f 3 -l 3 -x 6088 -y 6474 -W 4144 -H 1899 <pdf> assets/figures/fig2
    pdftoppm -png -singlefile -r 1400 -f 4 -l 4 -x 2118 -y 2341 -W 3692 -H 1588 <pdf> assets/figures/fig3

Figure 1 is cropped to its plot: the paper's team labels overprint each other.

## Key idea

Four years after a workshop gave an office's stand-ups a speaking token, a
stopwatch audit of 342 stand-ups across twelve teams finds the floor no more
equal the longer a team has passed it, while the teams rate it fair and most can
no longer say what it was for.

## Script

**VO:** Four years ago, a workshop recommended a speaking token for an office's
daily stand-ups. [beat 0.4] Only the person holding it may speak, [beat 0.2] and
they decide who speaks next. [beat 0.9]

_Visual:_ beat 0 (hero): the output's hero under the scrim, with the title
block.

**VO:** The idea spread across the floor. [beat 0.3] Twelve teams now pass the
token, some for a year and some for four. [beat 0.3] None has gone back to check
whether it works. [beat 0.9]

_Visual:_ beat 1 (quote): the paper's own sentence on the twelve teams and the
check none has made (page 1, introduction), building over the hero as the title
block clears.

**VO:** A new paper asks a narrow question. [beat 0.3] Does the floor get more
equal, the longer a team holds the token? [beat 0.9]

_Visual:_ beat 2 (statement): the question in type, "the longer a team holds the
token" in gold.

**VO (anneke-tolan):** For six weeks, we timed every stand-up with a stopwatch,
[beat 0.2] each person's turns, to the nearest second. [beat 0.3] Three hundred
and forty-two of them. [beat 1.8]

_Visual:_ beat 3 (people): Anneke Tolan, large, with her title and school; then
from "Three" beat 4 (stat): 342 stand-ups, counting up.

**VO:** Teams four years in were not measurably more equal than teams in their
first. [beat 0.4] At one year or four, a long tail of turns still takes over
thirty per cent of the floor. [beat 0.9]

_Visual:_ beat 5 (figure): Figure 2, each person's share of a stand-up by tenure
band, pushing in on the long right tails on "tail".

**VO:** So who does the talking? [beat 0.1] Role and tenure alone already
predict it. [beat 0.3] Knowing who holds the token adds almost nothing. [beat
0.5]

_Visual:_ beat 6 (figure): Figure 3, the variance explained with and without
token order, pushing in on the bars on "Knowing".

**VO:** Yet in eleven of the twelve teams, people rate it fairer than the
stopwatch finds it. [beat 0.4] Team L has held the token longest. [beat 0.2] It
rates itself the fairest of all twelve, [beat 0.2] and on the stopwatch, it's
the second least equal. [beat 0.9]

_Visual:_ beat 7 (figure): Figure 1, each team's felt fairness against its
measured equality; then from "rates" beat 8 (stats): Team L's 0.95 and, on
"second", its 0.44.

**VO (verity-marris):** In the final week, we asked the teams what the token was
for, in their own words. [beat 0.3] Only fourteen of the forty-seven who
answered could tell us. [beat 0.4] The commonest other answer was that it keeps
the meeting on time. [beat 0.9]

_Visual:_ beat 9 (people): Verity Marris, large, with her title and school; from
"Only" beat 10 (stat): 14, counting up; from "commonest" beat 11 (statement):
"It keeps the meeting on time.", "on time" in gold.

**VO:** The token still passes. [beat 0.3] The floor does not appear to move
with it. [beat 1.0]

_Visual:_ beat 12 (quote, spoken): the paper's closing sentence over its hero,
lighting as it is read.

**VO (casimir-beng):** The token was never wrong to introduce. [beat 0.3] What's
missing is anyone coming back to check on it, four years on, the way you'd check
a scale. [beat 1.0]

_Visual:_ beat 13 (quote, spoken): his words over his portrait, lighting as he
says them, then the close: the lockup.
