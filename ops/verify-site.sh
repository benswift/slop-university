#!/usr/bin/env bash
# Run the site verify chain (skills/publish/SKILL.md "3. Verify the site") as
# one quiet command.
#
# Why: running the six `pnpm` steps one at a time from an agent turn spends a
# turn and the full tool output per step --- six turns and a wall of Astro /
# oxlint / vitest noise for a chain that is almost always green. This runs the
# whole thing in one call, captures each step's output to a temp file, and
# prints one line per step: the last 60 lines only surface on the step that
# actually failed.
#
# What it deliberately does NOT do: `pnpm format` (repo-wide). The chain uses
# `format:content`, scoped to news/outputs/pages/grants --- see the skill for
# why that scope matters (it's exactly the publish wrapper's stage-by-name
# allowlist; `pnpm format` would touch files a run is forbidden to commit).
set -euo pipefail

REPO_ROOT="$(git -C "$(dirname "${BASH_SOURCE[0]}")" rev-parse --show-toplevel)"
WEBSITE_DIR="${REPO_ROOT}/website"
cd "$WEBSITE_DIR"

TOTAL_START=$SECONDS

run_step() {
  local label="$1"
  shift
  local out
  out="$(mktemp)"
  local start=$SECONDS
  if "$@" > "$out" 2>&1; then
    echo "ok  ${label} ($((SECONDS - start))s)"
    rm -f "$out"
  else
    local status=$?
    echo "FAIL ${label}"
    tail -n 60 "$out"
    if [[ "$label" == "typecheck" || "$label" == "build" ]] && grep -qi "content" "$out"; then
      echo "hint: if this looks like a stale content-layer cache, try: rm -rf node_modules/.astro .astro"
    fi
    rm -f "$out"
    exit "$status"
  fi
}

run_step "format:content" mise exec -- pnpm format:content
run_step "typecheck" mise exec -- pnpm typecheck
run_step "lint" mise exec -- pnpm lint
run_step "lint:css" mise exec -- pnpm run lint:css
run_step "test" mise exec -- pnpm test

# A concurrent generator slot sets this: the build is the expensive step and
# the lander runs the one authoritative build for every candidate it lands, so
# running it here too would put it on the parallel path N times over.
if [ -z "${SLOPU_SKIP_BUILD:-}" ]; then
  run_step "build" mise exec -- pnpm build
fi

echo "site verify: all green ($((SECONDS - TOTAL_START))s)"
