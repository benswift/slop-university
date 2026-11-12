---
title: Slop University study finds the first caller decides what a function means
subtitle: Fourteen years of one codebase show developers following the first reading of an unclear docstring, not the docstring itself
date: 2026-11-12
description: A new paper from the School of Settled Matters and the School of Continuous Improvement traces how the earliest uses of an ambiguously documented function fix its meaning for every developer who comes after.
output: slop-paper-how-the-earliest-smz0ou
---

For fourteen years, the developers of one freight-invoicing system have been reading each other's code to find out what its documentation meant. [_Precedent at the Call Site_](/outputs/slop-paper-how-the-earliest-smz0ou/), a new paper by [Associate Professor Anselm Threlkeld](/people/anselm-threlkeld/) and [Dr Odalys Penhallow](/people/odalys-penhallow/) of the [School of Settled Matters](/schools/settled-matters/) with [Dr Mirela Hanke](/people/mirela-hanke/) of the [School of Continuous Improvement](/schools/continuous-improvement/), follows what they found.

> I spent nine years telling the profession which judgment was the one to follow. It has been a quiet education to learn that programmers ask the same question of each other, and mostly take the first answer they are given.
>
> --- Dr Odalys Penhallow, Senior Lecturer, School of Settled Matters

The paper brings the School's long practice of reading statutes after their drafters have gone to the everyday craft of software documentation. It frames each call to an unclear function as an act of interpretation, and positions the developer's test suite as the place where an interpretation becomes binding. Across 287 functions and more than three thousand call sites, later callers took the first caller's reading four times in five, and no clarifying revision ever reversed a reading once a test had fixed it.

The School regards the work as a natural extension of a reading list that until now stopped at the statute book. Associate Professor Threlkeld said he expected "a lively correspondence from anyone who has ever written a docstring and then gone on holiday."

The full paper is available from the University's research repository under an open licence, doi:10.5555/slop.smz0ou.
