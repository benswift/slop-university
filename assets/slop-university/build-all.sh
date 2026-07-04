#!/usr/bin/env bash
# Regenerate the four Slop University lockups from lockup-gen.typ, optimise with
# svgo (viewBox preserved), and install them into the slop-university-brand
# typst package in this repo (brand/slop-university-brand/<version>/logos/).
#
# secondary-horizontal = cover/masthead; primary-horizontal = back cover. Both
# use the same artwork (the lockup is a single horizontal mark); the two names
# exist because the brand package resolves them separately. black/white =
# wordmark ink (the crest stays gold in both). See NOTES.md.
set -euo pipefail
cd "$(dirname "$0")"

FONT_PATH="${PUBLIC_SANS_PATH:-$HOME/.local/share/fonts/PublicSans-static}"
LOGOS="${SLOP_BRAND_LOGOS:-../../brand/slop-university-brand/0.1.0/logos}"

for v in black white; do
  raw="/tmp/slop-lockup-$v.svg"
  mise exec -- typst compile lockup-gen.typ "$raw" --input "variant=$v" --font-path "$FONT_PATH"
  for stem in secondary-horizontal primary-horizontal; do
    out="slop-${stem}-gold-${v}.svg"
    npx -y svgo@latest -q --config svgo.config.mjs -i "$raw" -o "$LOGOS/$out"
    echo "  built $out"
  done
done
echo "done -> installed into $LOGOS"
