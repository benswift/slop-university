---
title: Slop University pilots a timer that reclaims empty study rooms
subtitle:
  A grace-window release agent lifts study-room use in three buildings, and
  quietly evicts a small, predictable slice of latecomers
description:
  A new paper from the School of Continuous Improvement pilots a
  timeout-release agent for booked-but-empty study rooms, and finds its
  near-miss eviction rate tracks an unrevisited installation setting more
  closely than any deliberate design choice.
date: 2026-07-11
output: slop-paper-a-lightweight-release-dzfu3a
---

A booked study room with nobody in it is, to the room, indistinguishable
from an empty one. Three teaching buildings spent a term acting on that
distinction anyway, continuing the School of Continuous Improvement's
habit of turning a quiet inefficiency into a measured one.

Associate Professor Casimir Beng and Dr Joost Nwosu fitted the three
buildings' study-room panels with a release agent, cancelling any booking
with no check-in or motion signal within a grace window, against three
matched buildings left on the University's ordinary rules. Room use crept
upward where the agent ran and stayed flat where it didn't; a follow-up
check against access logs found a smaller, steadier population of
near-misses --- bookers who arrived only minutes after their room went
back to the waitlist.

> A control system is only as good as the number nobody remembers
> choosing. We built the release rule; somebody else, years before us,
> built the number that decides who it lets through.
>
> --- Associate Professor Casimir Beng, Lead, Adaptive Metrics Lab

That number mattered more than the pilot's design did. Two buildings run
the panel's factory-set eight-minute window; the third runs fifteen, set
by an installer years ago and never revisited. The shorter window
recovers marginally more room time each week and produces markedly more
near-misses; dropping the motion sensor from the release decision changed
almost nothing about either.

"Every deployed threshold is a decision someone made once and never
revisited," said Dr Nwosu, Postdoctoral Fellow in the School of Continuous
Improvement. "We'd rather this raise that question for every timer on
campus than settle it for the one we studied."

The University has not decided whether every building should adopt the
rule. For now, the pilot's own numbers --- eight-minute default included
--- are what it stands behind.

The full paper is available from the University's research repository
under an open licence, doi:10.5555/slop.dzfu3a.
