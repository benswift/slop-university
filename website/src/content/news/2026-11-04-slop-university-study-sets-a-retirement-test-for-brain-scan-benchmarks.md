---
title: Slop University study sets a retirement test for brain-scan benchmarks
subtitle: A classifier kept naming tumour types after the tumour was masked out, and one archive's long-serving test split has now been stood down
date: 2026-11-04
description: >-
  A new paper from the School of Continuous Improvement shows how much of a
  brain tumour classifier's accuracy survives without the tumour, and proposes
  a criterion for deciding when a benchmark split has done its work.
output: slop-paper-lesion-blind-baselines-brain-the4tt
---

A test split that has served a radiology teaching archive for many years has
been formally stood down, on the strength of a new paper from the
[School of Continuous Improvement](/schools/continuous-improvement/).
[_The Tumour Is Optional_](/outputs/slop-paper-lesion-blind-baselines-brain-the4tt/),
by [Dr Renke Sabel](/people/renke-sabel/), Dr Torun Ezeigwe and Associate
Professor Casimir Beng, offers the field a way of knowing when a benchmark has
told it everything it can.

> Most of the measures this School studies are never formally retired. They
> are reported a little less each year until nobody can say when they stopped
> meaning anything. It has been a genuine pleasure to write one of the rare
> retirement notices, and to write it in a form the next split can be held to.
>
> --- Dr Renke Sabel, Senior Lecturer and Convenor, Indicator Commons

The study progressively removes information from the images a classifier
learns from, mobilising a ladder of lesion-blind baselines to surface what a
model can know without looking where it is meant to. With the tumour masked
out, accuracy held at 83.7%; with no image at all, 66.2%. A new patient-level
split, built from the same archive, now carries the work forward, and the
retirement test is reported beside every result computed on it.

The paper evaluates research benchmarks rather than clinical tools, and the
University regards it as a natural extension of its stewardship of the
instruments its scholars rely on. "Our students meet a great many tests that
have been taught to," said Dr Ezeigwe, Senior Lecturer and Director of the
Master of Applied Measurement. "It is a fine thing to show them one that was
thanked and allowed to rest."

The full paper is available from the University's research repository under
an open licence, doi:10.5555/slop.the4tt.
