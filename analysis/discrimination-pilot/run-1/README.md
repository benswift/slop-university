# Run 1 --- the 54-item pilot (1 August 2026)

Everything the first run produced, moved here intact when TASK-006 rebuilt the
real corpus at roughly ten times the size. The report in `../README.md`
describes this run and cites these files; the paths there are the ones below.

Nothing here is superseded in the sense of being wrong. It is superseded in the
sense of being small: 54 excerpts from 32 source documents, against a stimulus
set now drawn from 139 real documents across 25 countries.

**These results cannot be pooled with the new run.** The stimuli differ, the
extraction pipeline differs (ligature repair and orthography normalisation were
added, both of which change the text judges see), and the redaction gazetteer
differs. More mechanically, item ids in this run are *positional* --- `E001`,
`E002` assigned after a shuffle --- while the new run derives them from excerpt
content, so an id means a different thing on each side of the boundary. That is
exactly the confusion the new scheme exists to prevent, and moving these files
out of the working directories is the other half of preventing it.

```
stimuli/stimuli.json       the 54 sampled stimuli with truth labels
stimuli/stimuli.txt        same, human-readable
stimuli/key.json           compact item -> truth/condition/source key
stimuli/pool_leak_spans.json  every span the LLM leak detector flagged
results/judgements-*.json  raw judgements, 8 judges across both passes of run 1
results/memorisation.json  the recall probe
results/analysis.txt       full analysis output
```
