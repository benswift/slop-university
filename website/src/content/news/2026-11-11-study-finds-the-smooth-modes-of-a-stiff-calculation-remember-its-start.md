---
title: Study finds the smooth parts of a stiff calculation remember how it began
subtitle: Starting values for multistep integrators, followed step by step through stiff and slowly varying modes
date: 2026-11-11
description: A new research poster from the School of Settled Matters traces the error a multistep solver takes on in its first few steps, and finds it is carried to the end in the slowly varying parts of the solution while the stiff parts forget it.
output: slop-poster-start-up-error-in-rih5k3
---

The [School of Settled Matters](/schools/settled-matters/), whose scholars study
how an open question comes to be treated as closed, has turned its attention to
numerical analysis.
[_The Smooth Modes Remember_](/outputs/slop-poster-start-up-error-in-rih5k3/), a
new research poster led by
[Dr Odalys Penhallow](/people/odalys-penhallow/), Senior Lecturer in the School,
with [Eskil Nwabueze](/people/eskil-nwabueze/), Doctoral Candidate in the
[School of Continuous Improvement](/schools/continuous-improvement/), and
[Dr Clemency Tredinnick](/people/clemency-tredinnick/), Lecturer in the School,
asks what becomes of the few values a solver must compute before its main
formula can begin.

> We set out to study the beginning of a calculation and found ourselves
> spending most of our time at its end. I suspect that is how these things
> usually go.
>
> --- Dr Odalys Penhallow, Senior Lecturer, School of Settled Matters

Working across a wide spectrum of stiffness, the team set five ways of
starting a calculation side by side and followed what each one leaves behind.
The answer divides cleanly: in the slowly varying parts of a solution the error
made at the start is never revisited, and can cost a fourth-order method two
orders of accuracy, while in the fast-decaying parts it is gone within ten
steps. The poster places the School's habits of close reading in direct
conversation with the University's computational capability.

"Colleagues in three Schools lent us their patience and their whiteboards," said
Dr Tredinnick, "and the poster carries a little of each of them."

The University is pleased to see its newest School find a home among the
equations, and expects the conversation to continue.

The full poster is available from the University's research repository under an
open licence, doi:10.5555/slop.rih5k3.
