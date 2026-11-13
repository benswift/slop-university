# Manual rungs

## 2T. Doctoral thesis (manual only --- never assessed)

The one rung no assessor returns and no timer fires: a human starts it with
`bin/slopu thesis`, in a generator slot named `thesis`, and the lander lands the
candidate like any other.

A run that dies at that limit leaves its drafting under `output/` and its
admission and site entries uncommitted in the slot's worktree, and the slot
refuses to run again until that work is finished or cleared. Finish it by hand,
in that worktree, once the window resets: branch
`press-gen-<new-run-id>-slot<slot>` off `main` carrying the uncommitted work,
whatever of steps 1-7 below is still owed (the blueprint's read-every-chapter
pass always is), staged into `data/pending-uploads/<new-run-id>/`, one commit
authored as the Press, then the candidate marker `ops/publish-generate.sh` would
have written. The lander does the rest.

The invocation line names the action `2T`, the preset `thesis`, the fiction the
wrapper drew --- the setting, the school, and a primary and an associate
supervisor from that school --- and, when the human steered the run, the topic.
Everything else is yours --- this is the run with creative licence, bounded only
by the blueprint's floors (`skills/from-preset/presets/thesis.md`): a thesis
that would pass examination, that is also a Slop University output in the true
sense.

In order:

1. **Admit the candidate** by the 2E procedure (name, collision check, headshot,
   person hero) with `title: Doctoral Candidate`, the drawn school, and
   `supervisors: [<primary id>, <associate id>]`. Their `bio` is a backstory in
   the roster's register --- where the thesis sits in the school's programme,
   what they did before --- and everything it says must agree with the thesis.
   Read the other candidates' bios first and open this one differently; a stock
   frame ("came to the University after nine years in...") shows by the second
   use. Admit them before composing, so the title page names a roster member,
   and write the roster entry in this step, beside the images: an interrupted
   run is finished from what is on disk.
2. **Compose the topic** to fit the drawn setting; dedup and claim it exactly as
   2A does (§2A, dedup and claim). A steered run is handed its topic on the
   invocation line instead --- take it as given, dedup and claim it the same
   way, and compose only what the drawn fiction still decides.
3. **Generate** with `skills/from-preset/SKILL.md` and the `thesis` blueprint.
   Its working method --- plan file first, references first, chapters to
   subagents, front matter last --- is the run's shape, and its floors are the
   only fixed structure. This run may take hours: the loop budgets in the
   operating rules apply per chapter, not per run, and the subagent rule applies
   with the model the blueprint names for each kind of work.
4. **Post-compile checks** as 2A, with the thesis substitutions the blueprint
   names (`ops/check-recent-language.py --preset thesis --self-reference-only`,
   since there are no prior theses to compare against; the page floor in
   `ops/check-output-quality.py --preset thesis`).
5. **Cite the canon.** The blueprint's floor (30-60 prior outputs, each
   characterised truly) replaces the per-preset table; run
   `ops/extract-citations.py --suggest` and take at least half from it.
6. **Mint the DOI, write the news post and the outputs entry, stage the assets**
   as 2A, with `preset: thesis`, `authors:` the candidate alone, `pages` from
   `pdfinfo`, no dark PDF. The news post announces the submission of the thesis
   for examination and names the supervisors. The thumbnail is the title page.
7. **Verify and commit** as below.

## 2V. Research explainer video (manual only --- never assessed)

A human runs `bin/slopu explainer` and the `video` slot starts. The invocation
line names the action `2V` and the output to explain, in `output`. The output
was drawn by `ops/pick-explainer.py` or named by the human, and its authors
already have voices. Make the video with `skills/video/SKILL.md` as an explainer
of that output. Nobody watches the run, so four things differ:

- `templated.py stage` stages into `$SLOPU_PENDING_DIR`, as every generator
  slot's assets do.
- Step 6 ends only on `video/_kit/review.py <id>` passing. Fix what it reports
  and run it again, at most three rounds. A video whose review still fails is
  not published: revert, leave the tree clean, and exit non-zero.
- Never run `ops/assign-voices.py`. A voice is canon, and canon is outside a
  video run's commit.
- Step 9 is the commit (§4), not a report. The candidate is held until a human
  has watched the staged drafts and approved it.

The run is exempt from §0.5's call count, because a video takes about 130 calls.
It is not exempt from the peak: delegate the render-and-review loop's reads.
