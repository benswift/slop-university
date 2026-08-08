#!/usr/bin/env bash
# Build the two composite plates for the NeurIPS 2026 Creative AI paper
# (research-papers/slop-university-neurips-2026/figures/): the wall of census
# papers and the roster band. Requires poppler-utils (pdftoppm) and
# imagemagick (montage, convert), plus local checkouts holding the output
# PDFs (output/ is gitignored, so the PDFs exist only where they were
# generated: this repo and the ../slop-university-press worktree).
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
PRESS="$REPO/../slop-university-press"
OUT="${1:-$REPO/analysis/paper-figures/out}"
TILES="$OUT/wall-tiles"
mkdir -p "$TILES"

# The paper's census is the ledger at commit 44525e3 (2026-08-01 10:23 AEST,
# 496 outputs / 199 papers). Recover that exact paper list from git rather
# than filtering by date: papers kept landing hourly through 1 August.
CENSUS_COMMIT=44525e3329a185b7ca3bd583718f7eee79e69aa6

cd "$REPO"
git grep -l "preset: paper" "$CENSUS_COMMIT" -- website/src/content/outputs |
  while read -r f; do
    git show "$f" | python3 -c "
import sys, yaml
d = yaml.safe_load(sys.stdin)
print(str(d['date']), d['doi'].split('.')[-1])
"
  done | sort > "$OUT/census-papers.txt"
echo "census papers: $(wc -l < "$OUT/census-papers.txt")"

# One tile per paper: page 1 at 40 dpi, in publication order.
i=0
while read -r _date slug; do
  pdf=$(find "$PRESS/output/pdf/paper" "$REPO/output/pdf/paper" \
    -name "*${slug}*.pdf" 2>/dev/null | head -1)
  [ -n "$pdf" ] || { echo "MISSING: $slug" >&2; exit 1; }
  printf -v n "%03d" "$i"
  pdftoppm -png -f 1 -l 1 -r 40 -singlefile "$pdf" "$TILES/tile-$n"
  i=$((i + 1))
done < "$OUT/census-papers.txt"

# 20x10 grid; 199 is prime, so the last cell stays empty (the caption's
# "filled by lunchtime" joke refers to the 200th paper, published ~2h after
# the census read).
montage "$TILES"/tile-*.png -tile 20x10 -geometry 150x+2+2 \
  -background white "$OUT/plate-wall-16bit.png"
convert "$OUT/plate-wall-16bit.png" -depth 8 -quality 90 "$OUT/plate-wall.jpg"

# Roster band: all canon headshots, 13x2, fictional researchers in
# alphabetical order with the Vice-Chancellor (the one real person) last.
cd "$REPO/canon/headshots"
montage $(ls ./*.jpg | grep -v ben-swift; echo ben-swift.jpg) \
  -tile 13x2 -geometry 200x200+2+2 -background white \
  "$OUT/plate-roster-16bit.png"
convert "$OUT/plate-roster-16bit.png" -depth 8 -quality 92 "$OUT/plate-roster.jpg"

rm -f "$OUT/plate-wall-16bit.png" "$OUT/plate-roster-16bit.png"
echo "plates written to $OUT; copy plate-wall.jpg and plate-roster.jpg into"
echo "research-papers/slop-university-neurips-2026/figures/"
