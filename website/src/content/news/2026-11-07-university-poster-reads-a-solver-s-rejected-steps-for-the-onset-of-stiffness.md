---
title: University poster reads a solver's rejected steps for the onset of stiffness
subtitle: Where the Steps Start Failing tests a step-size controller's own record as an early signal on a relaxation oscillator
description:
  A new research poster from the School of Emergent Priorities finds that the
  steps an explicit Runge–Kutta solver rejects mark where its problem turns
  stiff, closely under one controller and much more faintly under another.
output: slop-poster-reading-an-explicit-3akasp
date: 2026-11-07
publishedAt: "2026-11-07T03:02:18+11:00"
---

The [School of Emergent Priorities](/schools/emergent-priorities/) has long
asked how a change can be recognised before anyone formally declares it. Its
latest research poster,
[_Where the Steps Start Failing_](/outputs/slop-poster-reading-an-explicit-3akasp/),
puts that question to a numerical solver.

> We came to the solver's record the way we would come to any register,
> expecting it to know a little more than it had been asked to keep.
>
> --- Dr Fenna Okoro, Senior Lecturer and Convenor, Horizon Register

Led by [Dr Fenna Okoro](/people/fenna-okoro/) with
[Dr Petra Umbile](/people/petra-umbile/), Postdoctoral Fellow in the School,
the work turns a routine by-product of adaptive integration into an
instrument in its own right. Across five stiffness settings of a relaxation
oscillator, the team compared the solver's log of rejected steps with an
exact reference for the moment each slow stretch becomes stiff. Under the
simpler of two step-size controllers, the log flagged that moment within a
median of 4 to 14 attempted steps. Under a smoother controller, which rejects
far fewer steps, the same rule lagged by as many as 140 and at the stiffest
setting missed 39% of stretches altogether.

"Every good result leaves a further question behind it, and this one leaves
an especially welcome one," Dr Umbile said.

The poster extends the School's anticipatory agenda into the computational
sciences, a reach the University is pleased to see its foresight community
make on its own initiative. The full poster is available from the
University's research repository under an open licence,
doi:10.5555/slop.3akasp.
