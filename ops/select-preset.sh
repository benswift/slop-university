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
if   (( roll < 36 )); then echo research-poster
elif (( roll < 72 )); then echo paper
elif (( roll < 82 )); then echo marketing-poster
elif (( roll < 94 )); then echo brochure
elif (( roll < 97 )); then echo impact-report
else                       echo strategy
fi
