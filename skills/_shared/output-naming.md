# Shared: output filename conventions

Cross-cutting naming rule for documents written to `output/`. The calling skill
supplies the **prefix** (e.g. `slop-strategy`, `source`) and the **source
string** from which the slug is derived (a steering prompt, or a source
document's title); this file defines how the slug and seed are produced and how
the output paths are assembled.

## Filename shape

```
output/<prefix>-<slug>-<seed>.typ
output/pdf/<group>/<prefix>-<slug>-<seed>.pdf   # final PDF, foldered by source
output/pdf/<group>/<prefix>-<slug>-<seed>-dark.pdf  # dark render, if the
                                           # preset declares a dark variant
output/<prefix>-<slug>-<seed>-images/      # if the run generates images
output/<prefix>-<slug>-<seed>-charts/      # if the run generates charts
```

The final PDF lands in a per-source subfolder of `output/pdf/` (create it if
absent) so the booklets and posters are easy to browse by what produced them;
the intermediate `.typ`, image folder, and chart folder stay flat in `output/`.
The `<group>` subfolder and its `<prefix>` are fixed per calling path:

| Path / preset     | `<group>` (pdf subfolder) | `<prefix>`      |
| ----------------- | ------------------------- | --------------- |
| `strategy`        | `strategy`                | `slop-strategy` |
| `impact-report`   | `impact-report`           | `slop-impact`   |
| `research-poster` | `research-poster`         | `slop-poster`   |
| `paper`           | `paper`                   | `slop-paper`    |
| `brochure`        | `brochure`                | `slop-brochure` |
| `from-source`     | `from-source`             | `source`        |

A preset blueprint may declare its own prefix and group inline; a
blueprint-declared value overrides this table.

## Slug derivation

Take the first three whitespace-split words of the source string; lowercase;
replace any non-alphanumeric character with `-`; collapse adjacent `-`; trim
trailing `-`. If the result exceeds 30 characters, drop the trailing word.

Examples:

| Source string                                     | Slug                             |
| ------------------------------------------------- | -------------------------------- |
| `french-australian partnerships`                  | `french-australian-partnerships` |
| `aversion to PowerPoint presentations`            | `aversion-to-powerpoint`         |
| `lean into sovereign capability`                  | `lean-into-sovereign-capability` |
| `rise to the AI moment`                           | `rise-to-the`                    |
| `Annual Report of the School of Cybernetics 2024` | `annual-report-of`               |

## Seed

A random 6-character lowercase alphanumeric (e.g. `k7p2qx`). Two runs from the
same source string on the same day get distinct seeds and don't collide on disk.

## Ephemeral on disk

Outputs are kept locally only --- the `.gitignore` excludes them. Don't commit
the `.typ`, the PDF, the image folder, or the chart folder, and don't tag the
run.
