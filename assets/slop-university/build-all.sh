#!/usr/bin/env bash
# Regenerate the two Slop University lockup SVGs from lockup-gen.typ and
# install them into the slop-university-brand typst package
# (brand/slop-university-brand/<version>/logos/) and the website's branding
# assets (website/src/assets/branding/) so the two can't drift.
#
# The lockup is a single horizontal mark used for masthead and back cover
# alike; black/white = wordmark ink (the crest stays gold in both). Typst's
# SVG export carries the viewBox the masthead placement depends on. See
# NOTES.md.
set -euo pipefail
cd "$(dirname "$0")"

FONT_PATH="${PUBLIC_SANS_PATH:-$HOME/.local/share/fonts/PublicSans-static}"
LOGOS="${SLOP_BRAND_LOGOS:-../../brand/slop-university-brand/0.1.0/logos}"
WEB_BRANDING="${SLOP_WEB_BRANDING:-../../website/src/assets/branding}"

for v in black white; do
  out="slop-horizontal-gold-${v}.svg"
  mise exec -- typst compile lockup-gen.typ "$LOGOS/$out" --input "variant=$v" --font-path "$FONT_PATH"
  cp "$LOGOS/$out" "$WEB_BRANDING/$out"
  echo "  built $out -> brand package + website"
done
echo "done"
