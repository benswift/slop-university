---
title: Slop University brings cluster-scale fairness to one 3D printer
subtitle:
  A twelve-week makerspace deployment lifts a fairness index into
  cluster-computing range, while the wait it distributes barely shrinks
description:
  A School of Continuous Improvement paper deploys a fair-share
  job-scheduling algorithm, adapted from forty-year-old multi-user computing
  practice, on a suburban community makerspace's single 3D printer, finding
  it redistributes queue wait across member types more than it reduces it
  overall.
date: 2026-08-25
output: slop-paper-fair-share-scheduling-for-ji65cu
---

For forty years, computing centres have used one trick to stop a heavy user
monopolising a shared machine: track what they have already had, and make
them wait longer for more. Slop University has now put that trick on a
single 3D printer in a suburban community makerspace, and reports today what
cluster-computing literature would have predicted, had anyone thought to ask
it about a hobby workshop.

A paper published by Associate Professor Casimir Beng and Dr Mirela Hanke
tracked a booking kiosk through a twelve-week term after its
first-come-first-served queue was replaced with an exponentially-decayed
fair-share formula, units changed but logic untouched from the multi-user
computing literature. A weekly fairness index climbed into the range
published cluster deployments report, while total time spent waiting barely
moved: first-time and casual members waited substantially less, and the
makerspace's small population of heavy batch users waited substantially
more --- exactly the kind of scrutiny the School of Continuous Improvement
expects any fairness mechanism it deploys to survive.

> A fairness index and the queue you actually stand in are not the same
> measurement, and we would rather publish both than let one stand in for
> the other.
>
> --- Associate Professor Casimir Beng, Lead of the Adaptive Metrics Lab

The scheduler's fourteen-day decay window lets a member's recent printer use
fade out gradually rather than resetting on a fixed cycle. Forty-seven
members across the site's full range of printing habits are covered by the
twelve-week study; a follow-up ablation across three priority-weight
settings found the weighting itself contributed little beyond the decay
mechanism.

"It's a shorter queue than anything we usually study, and that turned out
to be the point," said Dr Mirela Hanke, Postdoctoral Fellow and Deputy
Convenor of the Living Dashboard. "A formula built for thousands of users
still has to answer to the person standing in front of the printer."

The full paper is available from the University's research repository under
an open licence, doi:10.5555/slop.ji65cu.
