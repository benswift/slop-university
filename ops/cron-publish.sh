#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ben/projects/slop-university"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/publish-$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR"

# Keep two months of run logs; they grow without bound otherwise.
find "$LOG_DIR" -name 'publish-*.log' -mtime +60 -delete

# mise activates tool shims into PATH (node, pnpm, typst, etc.) and exports
# the untracked env block (REPLICATE_API_TOKEN and friends).
eval "$(/home/ben/.local/bin/mise activate bash)"

cd "$PROJECT_DIR"

log() { echo "$*" >> "$LOG_FILE"; }

log "=== publish run started at $(date -Iseconds) ==="

# Remember where main was: the allowlist below validates exactly the commits
# this run produced, whether or not origin is reachable.
BASE_REF="$(git rev-parse HEAD)"

# The publish agent generates one output, stages it into website/, verifies
# the site builds, and commits — it never pushes (that's this wrapper's job,
# after validation). A failed generation is tolerated: the push below still
# redeploys whatever previously passed validation.
/home/ben/.local/bin/claude \
  --dangerously-skip-permissions \
  -p "/publish" \
  >> "$LOG_FILE" 2>&1 || log "publish agent failed (continuing)"

log "=== publish agent finished at $(date -Iseconds) ==="

# --- Validate: every file the agent's commits touched must fall inside the
# allowlist AND outside the denylist. This is the mechanical enforcement of
# website/CLAUDE.md's hard floors: workflows, CNAME, robots.txt, site-config,
# and doctrine files can never land via the unattended path, no matter what the
# agent was talked into. The allowlist covers the gap-driven tick's whole
# surface: research outputs (news + outputs + PDFs, plus each output's
# pipeline-optimised thumbnail and hero under src/assets/{outputs/thumbs,
# heroes/outputs}), grown pages, and the canon it edits (roster, schools,
# headshots, and canon/heroes for headshot-derived profile heroes). Note the
# tick may only touch heroes UNDER outputs/ --- the hand-built index and
# homepage heroes elsewhere in src/assets/heroes are deliberately excluded. The
# denylist carves the one out-of-fiction page (colophon) back out of the
# otherwise-allowed pages/ dir.
ALLOWLIST_RE='^(website/src/content/(news|outputs|pages)/|website/src/assets/(outputs/thumbs|heroes/outputs)/|website/public/outputs/pdf/|canon/(roster\.yml|schools\.yml|headshots/|heroes/)|data/pending-post\.json$)'
DENYLIST_RE='(^|/)colophon\.md$'

if [ -n "$(git status --porcelain)" ]; then
  log "VALIDATION FAILURE: dirty working tree after agent run:"
  git status --porcelain >> "$LOG_FILE"
  git reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1
  git clean -fd website/src/content website/src/assets website/public/outputs canon/headshots canon/heroes >> "$LOG_FILE" 2>&1
  log "=== reset to ${BASE_REF}; run aborted at $(date -Iseconds) ==="
  exit 1
fi

CHANGED="$(git diff --name-only "${BASE_REF}"..HEAD)"
if [ -n "$CHANGED" ]; then
  DENIED="$(echo "$CHANGED" | grep -E "$DENYLIST_RE" || true)"
  VIOLATIONS="$(echo "$CHANGED" | grep -Ev "$ALLOWLIST_RE" || true)"
  if [ -n "$DENIED" ] || [ -n "$VIOLATIONS" ]; then
    log "VALIDATION FAILURE: publish commit touches disallowed paths:"
    { echo "$DENIED"; echo "$VIOLATIONS"; } | grep -v '^$' >> "$LOG_FILE" || true
    git reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1
    log "=== reset to ${BASE_REF}; run aborted at $(date -Iseconds) ==="
    exit 1
  fi
  log "validated $(echo "$CHANGED" | wc -l) changed path(s) against allowlist"
else
  log "no new commits this run"
fi

# Push (the documented per-repo exception to the global manual-push rule,
# like the aps tracker's). Also redeploys prior validated work after a
# failed-generation run.
log "=== push at $(date -Iseconds) ==="
git push >> "$LOG_FILE" 2>&1 || log "push failed"

log "=== run finished at $(date -Iseconds) ==="
