#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ben/projects/slop-university"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/publish-$(date +%Y-%m-%d).log"

mkdir -p "$LOG_DIR" "${PROJECT_DIR}/data"

# Keep two months of run logs; they grow without bound otherwise.
find "$LOG_DIR" -name 'publish-*.log' -mtime +60 -delete

log() { echo "$*" >> "$LOG_FILE"; }

# Serialize runs: Persistent=true catch-up ticks and a still-running previous
# tick must never overlap (an overlapped pair each sees the other's commits as
# its own and validation becomes meaningless). Non-blocking --- a tick that
# finds the lock held simply skips; the next hourly tick retries.
exec 9> "${PROJECT_DIR}/data/publish.lock"
if ! flock -n 9; then
  log "=== $(date -Iseconds): another publish run holds the lock; skipping ==="
  exit 0
fi

# mise activates tool shims into PATH (node, pnpm, typst, etc.) and exports
# the untracked env block (REPLICATE_API_TOKEN and friends).
eval "$(/home/ben/.local/bin/mise activate bash)"

cd "$PROJECT_DIR"

log "=== publish run started at $(date -Iseconds) ==="

# --- Publish the staged social post, if one is waiting. A staged post
# references already-live site content, so it is valid to send regardless of
# what this run goes on to do (including aborting) --- which is why the flush
# lives in a function called from every exit path, not only after a clean
# push. Posted only on success; a failure leaves the file staged for the next
# run to retry (the poster dedups, so a lost-response retry can't double-post).
# data/pending-post.json is a gitignored working-tree artefact, never
# committed: the agent COMPOSES it, this wrapper POSTS it --- the same trust
# split as "the agent commits, the wrapper pushes". The SLOPU_TOKEN credential
# lives only in this wrapper's mise env, never in the unattended, feed-reading
# agent's.
flush_pending_post() {
  if [ -f "${PROJECT_DIR}/data/pending-post.json" ]; then
    log "=== posting staged social update at $(date -Iseconds) ==="
    if uv run "${PROJECT_DIR}/ops/post-to-bluesky.py" >> "$LOG_FILE" 2>&1; then
      rm -f "${PROJECT_DIR}/data/pending-post.json"
      log "posted and cleared data/pending-post.json"
    else
      log "social post failed; leaving data/pending-post.json staged for retry"
    fi
  fi
}

# A previous run that found agent violations interleaved with human commits
# cannot safely reset --- it blocks the pipeline instead and a human clears it.
# While blocked: no agent run, no push, no post (the block means something on
# main is suspect; don't amplify it anywhere).
if [ -f "${PROJECT_DIR}/data/publish-blocked" ]; then
  log "PIPELINE BLOCKED --- data/publish-blocked exists; a human must triage and remove it:"
  cat "${PROJECT_DIR}/data/publish-blocked" >> "$LOG_FILE"
  log "=== run refused at $(date -Iseconds) ==="
  exit 1
fi

# Pre-flight: a dirty tree means a human is mid-work in this shared working
# tree (or a crashed run left residue). Skip the whole run --- the agent's own
# precondition would abort anyway, and skipping here means nothing is ever
# stashed or reset out from under an interactive session. A staged post is
# still flushed: it references live content and owes nothing to this tree.
if [ -n "$(git status --porcelain)" ]; then
  log "working tree dirty before run; skipping this tick (human work in progress?):"
  git status --porcelain >> "$LOG_FILE"
  flush_pending_post
  log "=== run skipped at $(date -Iseconds) ==="
  exit 0
fi

# Remember where main was immediately before the agent runs. Everything the
# agent commits sits in BASE_REF..HEAD; a human commit landing mid-run also
# lands in that range, which is why validation below distinguishes commits by
# author rather than judging the range wholesale.
BASE_REF="$(git rev-parse HEAD)"

# Preserve, never destroy, on a validation abort. Only reached when every
# commit in BASE_REF..HEAD is agent-authored (mixed ranges block instead, and
# never touch main). The offending commits are rescued onto a local
# `publish-rescue/<ts>` branch and any uncommitted residue stashed before main
# is reset back to BASE_REF. Recover with `git branch --list 'publish-rescue/*'`
# and `git stash list`. Rescue branches are local-only (git push only pushes
# main) and left for manual cleanup.
rescue_and_abort() {
  local ts; ts="$(date +%Y%m%d-%H%M%S)"
  if [ "$(git rev-parse HEAD)" != "$BASE_REF" ]; then
    if git branch "publish-rescue/${ts}" HEAD >> "$LOG_FILE" 2>&1; then
      log "preserved commits ${BASE_REF}..HEAD on branch publish-rescue/${ts}"
    else
      log "WARNING: could not create rescue branch publish-rescue/${ts}"
    fi
  fi
  if [ -n "$(git status --porcelain)" ]; then
    if git stash push -u -m "publish-rescue ${ts}" >> "$LOG_FILE" 2>&1; then
      log "stashed uncommitted work as 'publish-rescue ${ts}' (see: git stash list)"
    else
      log "WARNING: could not stash uncommitted work"
    fi
  fi
  git reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1 || log "WARNING: reset to ${BASE_REF} failed"
  log "=== reset main to ${BASE_REF}; run aborted at $(date -Iseconds) ==="
  flush_pending_post
  exit 1
}

# The publish agent generates one output, stages it into website/, verifies
# the site builds, and commits --- it never pushes (that's this wrapper's job,
# after validation). A failed generation is tolerated: the push below still
# redeploys whatever previously passed validation.
#
# GIT_AUTHOR_* stamps every commit the agent makes with a distinct author, so
# validation below can tell agent commits from human commits landing in the
# same range. SLOPU_PUBLIC_ONLY tells the from-preset resolver to treat
# private/ preset overlays as unresolvable --- the unattended path can only
# ever run public slop presets.
GIT_AUTHOR_NAME="Slop University Press" \
GIT_AUTHOR_EMAIL="press@slop.university" \
SLOPU_PUBLIC_ONLY=1 \
/home/ben/.local/bin/claude \
  --dangerously-skip-permissions \
  -p "/publish" \
  >> "$LOG_FILE" 2>&1 || log "publish agent failed (continuing)"

log "=== publish agent finished at $(date -Iseconds) ==="

# --- Post-run residue. The tree was clean pre-flight, so any dirt now is this
# run's leftovers (a crashed generation) or a human who started editing
# mid-run. Stash only residue inside the agent's own content surface --- an
# uncommitted news post or outputs entry would otherwise leak into the next
# run's build and deadlock its clean-tree precondition --- and leave anything
# else in place with a warning (it's likelier a human's).
RESIDUE="$(git status --porcelain)"
if [ -n "$RESIDUE" ]; then
  log "post-run residue in working tree:"
  echo "$RESIDUE" >> "$LOG_FILE"
  AGENT_RESIDUE="$(echo "$RESIDUE" | awk '{print $2}' | grep -E '^(website/(src/content|src/assets|public/outputs)/|canon/)' || true)"
  if [ -n "$AGENT_RESIDUE" ]; then
    ts="$(date +%Y%m%d-%H%M%S)"
    # shellcheck disable=SC2086
    if git stash push -u -m "publish-residue ${ts}" -- $AGENT_RESIDUE >> "$LOG_FILE" 2>&1; then
      log "stashed agent residue as 'publish-residue ${ts}' (see: git stash list)"
    else
      log "WARNING: could not stash agent residue"
    fi
  fi
fi

# --- Validate: every file touched by an AGENT-authored commit must fall inside
# the allowlist AND outside the denylist, and its diff must be free of
# private-brand markers. This is the mechanical enforcement of
# website/CLAUDE.md's hard floors: workflows, CNAME, robots.txt, site-config,
# and doctrine files can never land via the unattended path, no matter what the
# agent was talked into. Human commits in the range are logged and passed
# through unjudged --- the allowlist gates the agent, not the human whose repo
# this is. The allowlist covers the gap-driven tick's whole surface: research
# outputs (news + outputs + PDFs, plus each output's pipeline-optimised
# thumbnail and hero under src/assets/{outputs/thumbs,heroes/outputs}), grant
# awards (content/grants/ --- but NOT canon/grants.yml: the tick awards from
# existing schemes only; adding a scheme is a human action), grown pages, and
# the canon it edits (roster, schools, headshots, and canon/heroes for
# headshot-derived profile heroes). Note the tick may only touch heroes
# UNDER outputs/ --- the hand-built index and homepage heroes elsewhere in
# src/assets/heroes are deliberately excluded. The denylist carves the one
# out-of-fiction page (colophon) back out of the otherwise-allowed pages/ dir.
ALLOWLIST_RE='^(website/src/content/(news|outputs|pages|grants)/|website/src/assets/(outputs/thumbs|heroes/outputs)/|website/public/outputs/pdf/|canon/(roster\.yml|schools\.yml|headshots/|heroes/))'
DENYLIST_RE='(^|/)colophon\.md$'
# The private-brand firewall: no agent commit may reference the ANU brand
# layer, the private preset overlay, or the non-redistributable top-level
# references/*.avif photos. (references/slop-style/ is fine and unmatched ---
# the pattern has no slash.) Belt to the SLOPU_PUBLIC_ONLY braces above.
FIREWALL_RE='anu-typst-template|@local/anu|private/anu|lockup: *"anu|references/[a-z0-9_-]+\.avif'

AGENT_EMAIL="press@slop.university"
AGENT_SHAS="$(git log --format='%H' --author="$AGENT_EMAIL" "${BASE_REF}..HEAD")"
HUMAN_SHAS="$(git log --format='%H' "${BASE_REF}..HEAD" | grep -vxF "$AGENT_SHAS" || true)"

if [ -n "$HUMAN_SHAS" ]; then
  log "NOTE: human commit(s) landed during this run; passed through unvalidated:"
  # shellcheck disable=SC2086  # sha list is deliberately word-split
  git log --format='  %h %s' --no-walk $HUMAN_SHAS >> "$LOG_FILE" 2>&1 || true
fi

VIOLATION_LOG=""
for sha in $AGENT_SHAS; do
  FILES="$(git show --name-only --format= "$sha")"
  DENIED="$(echo "$FILES" | grep -E "$DENYLIST_RE" || true)"
  OUTSIDE="$(echo "$FILES" | grep -Ev "$ALLOWLIST_RE" | grep -v '^$' || true)"
  LEAKED="$(git show "$sha" | grep -E "$FIREWALL_RE" || true)"
  if [ -n "$DENIED" ] || [ -n "$OUTSIDE" ] || [ -n "$LEAKED" ]; then
    DETAIL="$(printf '%s\n' "$DENIED" "$OUTSIDE" "$LEAKED" | grep -v '^$')"
    VIOLATION_LOG="${VIOLATION_LOG}
commit ${sha}:
${DETAIL}"
  fi
done

if [ -n "$VIOLATION_LOG" ]; then
  log "VALIDATION FAILURE: agent commit(s) violate the allowlist/denylist/firewall:"
  echo "$VIOLATION_LOG" >> "$LOG_FILE"
  if [ -z "$HUMAN_SHAS" ]; then
    rescue_and_abort
  else
    # Agent violations interleaved with human commits: resetting would destroy
    # the human's work and surgery is not this script's job. Block the
    # pipeline (no push, no future runs) until a human triages.
    {
      echo "blocked at $(date -Iseconds): agent commit(s) in ${BASE_REF}..$(git rev-parse HEAD)"
      echo "violate the allowlist/denylist/firewall but are interleaved with human"
      echo "commits, so the wrapper won't reset. Inspect, fix main, then delete"
      echo "this file to unblock."
      echo "$VIOLATION_LOG"
    } > "${PROJECT_DIR}/data/publish-blocked"
    log "CRITICAL: wrote data/publish-blocked; pipeline halted until a human clears it"
    log "=== run aborted (blocked) at $(date -Iseconds) ==="
    exit 1
  fi
fi

if [ -n "$AGENT_SHAS" ]; then
  log "validated $(echo "$AGENT_SHAS" | wc -l) agent commit(s) against allowlist + firewall"
else
  log "no agent commits this run"
fi

# Push (the documented per-repo exception to the global manual-push rule,
# like the aps tracker's). Also redeploys prior validated work after a
# failed-generation run.
log "=== push at $(date -Iseconds) ==="
git push >> "$LOG_FILE" 2>&1 || log "push failed"

flush_pending_post

log "=== run finished at $(date -Iseconds) ==="
