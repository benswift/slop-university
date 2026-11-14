#!/usr/bin/env bash
# Pick a 2A artefact preset from the press mix. This runs outside the model so
# a publish run receives one unambiguous, genuinely random selection.
set -euo pipefail

# /dev/urandom gives us an OS-supplied random value. Reject the small tail above
# the largest multiple of 100 so modulo mapping does not favour any bucket.
while :; do
  value="$(LC_ALL=C od -An -N2 -tu2 /dev/urandom | tr -d '[:space:]')"
  if [ "$value" -lt 65500 ]; then
    roll=$((value % 100))
    break
  fi
done

# Shares mirror the target-share table in skills/publish/SKILL.md (rung 2A).
if   (( roll < 32 )); then preset=research-poster
elif (( roll < 64 )); then preset=paper
elif (( roll < 73 )); then preset=marketing-poster
elif (( roll < 84 )); then preset=brochure
elif (( roll < 87 )); then preset=impact-report
elif (( roll < 90 )); then preset=strategy
elif (( roll < 93 )); then preset=consultation-paper
elif (( roll < 97 )); then preset=submission
else                       preset=questions-on-notice
fi

# A submission answers a published consultation paper; with none in the
# ledger, draw the paper it would have answered instead.
outputs="${SLOPU_OUTPUTS_DIR:-$(cd "$(dirname "$0")/.." && pwd)/website/src/content/outputs}"
if [ "$preset" = submission ] \
  && ! grep -qlx 'preset: consultation-paper' "$outputs"/*.yml 2>/dev/null; then
  preset=consultation-paper
fi
echo "$preset"
