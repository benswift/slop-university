---
title: University paper finds a tester's first-fail log safer than its reputation
subtitle: A continue-on-fail audit of one sensor chip's wafer-sort program finds a quarter of its test time in tests the log could not rank
date: 2026-11-07
description: A School of Underlying Conditions paper shows what a stop-on-first-fail test log can safely say about retiring tests from a mature mixed-signal program, and audits 401,520 die to find where it falls silent.
output: slop-paper-what-a-stop-on-first-fail-1sjrag
---

Which tests can a production line stop running, and what does its own record
allow it to conclude? A new paper from the
[School of Underlying Conditions](/schools/underlying-conditions/) takes up that
question for a mixed-signal sensor-interface chip whose wafer-sort program has
grown, over nine years, to 1,146 tests.

The work extends the School's standing interest in what a single record is
asked to say. Here the record is the tester's stop-on-first-fail log, which
credits each failing die to the first test it fails and nothing after. The
paper establishes that this log is a sound gate for retirement decisions,
then aligns it with a full continue-on-fail audit of seven production lots to
surface where the log's caution outruns the evidence, concentrated in the long
analog tests that account for much of the line's tester time.

> The School has always been drawn to the records people stop reading once they
> have decided what those records say. This paper read one to the end, and we
> are glad to have the result on the shelf beside our own.
>
> --- Dr Vigdis Emenike, Senior Lecturer, School of Underlying Conditions

The paper sits comfortably within the University's wider effort to treat
measurement infrastructure as a subject of scholarship in its own right, and
the School regards it as a natural step from the borefield to the cleanroom.

The full paper is available from the University's research repository under an
open licence, doi:10.5555/slop.1sjrag.
