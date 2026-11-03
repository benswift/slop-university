---
title: Continuous Improvement meters the energy behind every merged change
subtitle: A half-year study of one research software group's build machines, and what caching and test selection gave back
date: 2026-11-03
description: A paper from the School of Continuous Improvement follows the electricity of a research software group's build-and-test machines to the outlet, and finds most of it spent waiting or repeating work already done.
output: slop-paper-joules-per-merged-zoye1y
---

For twenty-six weeks, a meter sat on every outlet of the machines that build and test a research software group's code. What it recorded is now the subject of [_Joules per Merged Change_](/outputs/slop-paper-joules-per-merged-zoye1y/), a new paper by [Dr Thandiwe Solberg](/people/thandiwe-solberg/), Senior Lecturer and Convenor, Demo Quarter, and [Dr Marit Osayande](/people/marit-osayande/), Lecturer and Convenor, Living Dashboard, both of the [School of Continuous Improvement](/schools/continuous-improvement/).

> None of this would have been possible without fifty-eight people agreeing to carry on exactly as usual while we watched the power strip. We owe them a great deal, and they have been very gracious about the showcase weeks.
>
> --- Dr Thandiwe Solberg, Senior Lecturer and Convenor, Demo Quarter

The paper brings outlet metering, on-chip energy counters and the group's own pipeline records into a single account of where a development process spends its electricity, sorting every job into what was new and needed, what had been done before, what was overtaken by a later push and what was simply retried. Fewer than one joule in four, it finds, went to work that was both new and used. A second phase of established practice, from build caching to powering down idle machines, roughly halved the energy behind each merged change, though the faster feedback that followed invited a share of the saving back.

The work sits within the School's continuing attention to the systems an institution leaves running when no one is looking at them, and the University counts it among the School's most practical contributions to date.

"We set out to measure a machine room and came away knowing rather more about ourselves," said Dr Osayande.

The full paper is available from the University's research repository under an open licence, doi:10.5555/slop.zoye1y.
