---
title: Slop University builds a consensus layer for the supermarket price tag
subtitle: >-
  Gossip propagation and a staged canary rollout cut the delay before every
  shelf tag agrees with the register, though not by moving the typical case
description: >-
  A School of Emergent Priorities paper deploys a gossip-based consensus
  protocol across a 40-store electronic shelf label network and finds it
  shrinks the slowest price-tag delays without much changing the ordinary
  ones.
date: 2026-08-27
output: slop-paper-the-electronic-shelf-label-xtg0au
---

A supermarket shelf tag has always been a courtesy copy of the real price,
not the record the register actually charges. A paper published today by the
School of Emergent Priorities gives that courtesy copy a consensus protocol
of its own, borrowed wholesale from systems built to keep far larger things
in agreement.

Dr Lindiwe Achterberg led the work with Professor Verity Marris, School of
Emergent Priorities, and Dr Osei Vandermeer, Research Fellow and Convenor of
the Review Cadence Observatory, School of Continuous Improvement. The team
layered a gossip-based relay protocol and a staged canary release over a
40-store electronic shelf label network's existing broadcast, so a price
change spreads tag-to-tag as well as down from the centre. Across eighteen
weeks, the slowest tags caught up dramatically faster; the typical tag,
already fast, barely noticed the difference.

> Most of a shelf's tags were never the problem. The system exists for the
> handful that were always going to be last, and would otherwise have stayed
> last for a very long time.
>
> --- Dr Lindiwe Achterberg, Lecturer

"We built the canary stage to catch conflicts before they spread," said Dr
Vandermeer, "and the deployment obliged by proving it does exactly that, and
nothing else." The team is treating the gap between what the canary was
built to speed up and what it actually protects as its own small finding,
and plans to carry the framing into the estate's next fleet-scale
instrumentation round.

The full paper is available from the University's research repository under
an open licence, doi:10.5555/slop.xtg0au.
