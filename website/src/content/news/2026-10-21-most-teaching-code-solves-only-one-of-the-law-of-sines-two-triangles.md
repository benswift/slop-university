---
title: Most teaching code solves only one of the law of sines' two triangles
subtitle: A test of 417 triangle solvers finds the ambiguous case named in the comments and dropped in the code
date: 2026-10-21
description: A research poster from the School of Continuous Improvement tests 417 triangle-solving functions from teaching repositories against an exact oracle, and finds most return one triangle where the geometry allows two.
output: slop-poster-the-second-triangle-iei4qn
---

The School of Continuous Improvement's long interest in what a system remembers to do has found its way into the geometry classroom. [_The Second Triangle_](/outputs/slop-poster-the-second-triangle-iei4qn/), a new research poster, asks whether the code written to teach the law of sines keeps the rule's best-known exception: that two sides and an angle not between them can describe two different triangles.

For the most part it does not. Of 417 functions examined, 254 compute one angle and stop, and 96 of those mention the second triangle in a comment on the way past.

> The second triangle has been in the textbook for a very long time. It seemed only fair to look for it in the code as well.
>
> --- [Mr Eskil Nwabueze](/people/eskil-nwabueze/), Doctoral Candidate, School of Continuous Improvement

The study, led by Mr Nwabueze with [Dr Mirela Hanke](/people/mirela-hanke/), Postdoctoral Fellow and Deputy Convenor of the Living Dashboard, and [Associate Professor Casimir Beng](/people/casimir-beng/), Lead of the Adaptive Metrics Lab, brings together corpus mining, strategy-level classification and large-scale automated testing to build a picture of how a familiar rule travels from the page into practice. Its most portable contribution is a five-case test fixture, released with the poster, which teaching repositories can adopt as they see fit.

Associate Professor Beng welcomed the fixture as "the sort of small, durable instrument the Lab has always preferred, because it costs so little to keep honest."

The poster takes its place in the University's continuing programme of work on the reliability of everyday measurement and calculation.

The full poster is available from the University's research repository under an open licence, doi:10.5555/slop.iei4qn.
