---
title: Earth scientists teach a type checker where the water is
subtitle: A new type system treats a groundwater level as a position measured from somewhere, and declines to add two of them together
date: 2026-10-12
description: A research poster from the School of Underlying Conditions sets out a type system for water-level arithmetic and reports what it refused across an archive of 318 processing scripts.
output: slop-poster-datum-indexed-affine-types-j0mpxo
---

Slop University's earth scientists have written a type system. _Depth Is Not a
Number: Datum-indexed affine types for water-level arithmetic_ is a research
poster by Dr Vigdis Emenike, Senior Lecturer, and Dr Brynjar Obiora, Senior
Research Fellow, both of the School of Underlying Conditions, with Eivind
Onwuka, Doctoral Candidate in the School of Continuous Improvement.

The poster starts from a habit of programming languages that check units: they
will stop a program adding metres to seconds, and will let it add metres to
metres. For a depth read down a pipe, the authors propose, the second freedom is
the costly one. Their system records where each level was measured from and
carries that through every calculation that follows.

> We set out to teach a machine the difference between a place and a distance,
> and discovered how long we had been leaving that to whoever happened to be
> in the room. Both arrangements have had their successes.
>
> --- Dr Vigdis Emenike, Senior Lecturer, School of Underlying Conditions

The team brought the checker to bear on 318 scripts from the archive of a
regional monitoring network, describing the data only at the point each file is
opened and allowing the rules to settle the rest. It refused 61 calculations.
Twenty-three were averages that had arrived at the right answer by a route the
rules could not follow, and the rules were widened to admit them; four were
plain confusions of feet and metres.

The University holds that a school should be at liberty to follow a problem
into whichever discipline is currently keeping it, and to come back with
something. Dr Obiora said the work "leaves the School on firmer terms with the
word down".

The full poster is available from the University's research repository under an
open licence, doi:10.5555/slop.j0mpxo.
