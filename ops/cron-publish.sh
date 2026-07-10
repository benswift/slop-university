#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ben/projects/slop-university"
WORKTREE_DIR="/home/ben/projects/slop-university-press"
PRESS_BRANCH="press"
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
# agent's. data/ is canonical HERE: the press worktree's data/ is a symlink to
# this checkout's, so a post the agent stages over there lands where this
# wrapper (and the lock, and the block file) already look.
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

# Manual kill switch: a human can halt the pipeline by creating this file.
# (The wrapper itself no longer writes it --- the old writer existed for agent
# violations interleaved with human commits on main, which the press worktree
# makes impossible: the agent never commits where a human works.)
if [ -f "${PROJECT_DIR}/data/publish-blocked" ]; then
  log "PIPELINE BLOCKED --- data/publish-blocked exists; a human must triage and remove it:"
  cat "${PROJECT_DIR}/data/publish-blocked" >> "$LOG_FILE"
  log "=== run refused at $(date -Iseconds) ==="
  exit 1
fi

# --- The press worktree. The agent never works in the human checkout: it gets
# a persistent worktree on the `press` branch, reset to the newest published
# state before every run. Three things fall out of this: a tick never skips
# because a human is mid-edit here; the agent always generates against a
# COMMITTED, consistent state of the canon (never a half-edited roster); and
# the gitignored private surface (private/, CLAUDE.local.md, the top-level
# references/*.avif photos) simply does not exist over there --- braces on top
# of SLOPU_PUBLIC_ONLY's belt.
if ! git worktree list --porcelain | grep -qxF "worktree ${WORKTREE_DIR}"; then
  if [ -e "$WORKTREE_DIR" ]; then
    log "ERROR: ${WORKTREE_DIR} exists but is not a registered worktree; refusing to touch it"
    flush_pending_post
    exit 1
  fi
  git worktree add -B "$PRESS_BRANCH" "$WORKTREE_DIR" main >> "$LOG_FILE" 2>&1
  log "created press worktree at ${WORKTREE_DIR}"
fi

# mise refuses config files it hasn't been told to trust; idempotent.
for f in "${WORKTREE_DIR}/mise.toml" "${WORKTREE_DIR}/website/mise.toml"; do
  [ -f "$f" ] && /home/ben/.local/bin/mise trust "$f" >> "$LOG_FILE" 2>&1 || true
done

# --- Base selection: build on the newest published state. Normally one of
# main / origin/main contains the other (a prior run pushed but couldn't
# fast-forward a dirty local checkout, or the human committed locally and the
# push will carry it). Genuine divergence means a human rebase is due --- skip
# rather than guess.
git fetch origin >> "$LOG_FILE" 2>&1 || log "WARNING: git fetch failed; selecting base from local refs"
if git merge-base --is-ancestor main origin/main; then
  BASE_REF="$(git rev-parse origin/main)"
  BASE_NAME="origin/main"
elif git merge-base --is-ancestor origin/main main; then
  BASE_REF="$(git rev-parse main)"
  BASE_NAME="main"
else
  log "main and origin/main have DIVERGED; a human must reconcile (rebase). Skipping this tick."
  flush_pending_post
  log "=== run skipped at $(date -Iseconds) ==="
  exit 1
fi

# A previous run that committed but failed to push leaves press ahead of every
# base; preserve those commits before the reset below discards them. (There is
# no resume --- the skill's contract is one atomic run --- so a fresh tick
# regenerates rather than retrying a stale commit.)
if ! git merge-base --is-ancestor "$PRESS_BRANCH" "$BASE_REF"; then
  ts="$(date +%Y%m%d-%H%M%S)"
  if git branch "publish-rescue/${ts}" "$PRESS_BRANCH" >> "$LOG_FILE" 2>&1; then
    log "press had commits not reachable from ${BASE_NAME}; preserved on publish-rescue/${ts}"
  else
    log "WARNING: could not create rescue branch for stranded press commits"
  fi
fi

# Reset the worktree to base and clear crash residue. clean is deliberately
# not -x: gitignored state (output/ scratch, .typst-cache/, website's
# node_modules, the data symlink) survives; only untracked non-ignored files
# --- a crashed run's half-staged content --- are removed.
git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1
git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1

# The data/ handoff symlink (see flush_pending_post above). After the clean so
# a mistaken removal is always repaired.
if [ ! -e "${WORKTREE_DIR}/data" ]; then
  ln -s "${PROJECT_DIR}/data" "${WORKTREE_DIR}/data"
fi

# The site verify (typecheck/lint/test/build) needs node_modules in THIS
# worktree; pnpm's shared store makes this hardlinks, not a second download.
if ! (cd "${WORKTREE_DIR}/website" && pnpm install --frozen-lockfile) >> "$LOG_FILE" 2>&1; then
  log "pnpm install failed in press worktree; aborting run"
  flush_pending_post
  exit 1
fi

# Preserve, never destroy, on a validation abort. main is never touched ---
# the offending commits exist only on press, so rescue is a branch pointer
# plus a worktree reset.
rescue_and_abort() {
  local ts; ts="$(date +%Y%m%d-%H%M%S)"
  if [ "$(git rev-parse "$PRESS_BRANCH")" != "$BASE_REF" ]; then
    if git branch "publish-rescue/${ts}" "$PRESS_BRANCH" >> "$LOG_FILE" 2>&1; then
      log "preserved commits ${BASE_REF}..${PRESS_BRANCH} on branch publish-rescue/${ts}"
    else
      log "WARNING: could not create rescue branch publish-rescue/${ts}"
    fi
  fi
  git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1 || log "WARNING: reset press to ${BASE_REF} failed"
  log "=== reset press to ${BASE_REF}; run aborted at $(date -Iseconds) ==="
  flush_pending_post
  exit 1
}

# The publish agent generates one output, stages it into website/, verifies
# the site builds, and commits --- it never pushes (that's this wrapper's job,
# after validation). A failed generation is tolerated: the push below still
# redeploys whatever previously passed validation.
#
# GIT_AUTHOR_* stamps every commit the agent makes with a distinct author, so
# validation below can prove every commit on press is the agent's. SLOPU_PUBLIC_ONLY
# tells the from-preset resolver to treat private/ preset overlays as
# unresolvable --- the unattended path can only ever run public slop presets
# (and in the worktree private/ doesn't exist to begin with).
(
  cd "$WORKTREE_DIR"
  GIT_AUTHOR_NAME="Slop University Press" \
  GIT_AUTHOR_EMAIL="press@slop.university" \
  SLOPU_PUBLIC_ONLY=1 \
  /home/ben/.local/bin/claude \
    --dangerously-skip-permissions \
    -p "/publish"
) >> "$LOG_FILE" 2>&1 || log "publish agent failed (continuing)"

log "=== publish agent finished at $(date -Iseconds) ==="

# --- Post-run residue in the worktree is a crashed generation's leftovers;
# nothing human lives there, so it needs no stash --- the next run's
# reset+clean clears it. Log it for the record.
RESIDUE="$(git -C "$WORKTREE_DIR" status --porcelain)"
if [ -n "$RESIDUE" ]; then
  log "post-run residue in press worktree (next run's reset/clean clears it):"
  echo "$RESIDUE" >> "$LOG_FILE"
fi

# --- Validate: every file touched by an AGENT-authored commit must fall inside
# the allowlist AND outside the denylist, and its diff must be free of
# private-brand markers. This is the mechanical enforcement of
# website/CLAUDE.md's hard floors: workflows, CNAME, robots.txt, site-config,
# and doctrine files can never land via the unattended path, no matter what the
# agent was talked into. The allowlist covers the gap-driven tick's whole
# surface: research outputs (news + outputs + PDFs, plus each output's
# pipeline-optimised thumbnail and hero under
# src/assets/{outputs/thumbs,heroes/outputs}), grant awards (content/grants/
# --- but NOT canon/grants.yml: the tick awards from existing schemes only;
# adding a scheme is a human action), the heroes of the news posts that
# announce no output (grant awards and institutional notices, under
# src/assets/heroes/news/), grown pages, and the canon it edits (roster,
# schools, headshots, and canon/heroes for headshot-derived profile heroes).
# Note the tick may only touch heroes UNDER outputs/ and news/ --- the
# hand-built index and homepage heroes elsewhere in src/assets/heroes are
# deliberately excluded. The denylist carves the one out-of-fiction page
# (colophon) back out of the otherwise-allowed pages/ dir.
ALLOWLIST_RE='^(website/src/content/(news|outputs|pages|grants)/|website/src/assets/(outputs/thumbs|heroes/(outputs|news))/|website/public/outputs/pdf/|canon/(roster\.yml|schools\.yml|headshots/|heroes/))'
DENYLIST_RE='(^|/)colophon\.md$'
# The private-brand firewall: no agent commit may reference the ANU brand
# layer, the private preset overlay, or the non-redistributable top-level
# references/*.avif photos. (references/slop-style/ is fine and unmatched ---
# the pattern has no slash.) Belt to the SLOPU_PUBLIC_ONLY braces above.
FIREWALL_RE='anu-typst-template|@local/anu|private/anu|lockup: *"anu|references/[a-z0-9_-]+\.avif'

AGENT_EMAIL="press@slop.university"
AGENT_SHAS="$(git log --format='%H' --author="$AGENT_EMAIL" "${BASE_REF}..${PRESS_BRANCH}")"
if [ -n "$AGENT_SHAS" ]; then
  FOREIGN_SHAS="$(git log --format='%H' "${BASE_REF}..${PRESS_BRANCH}" | grep -vxF "$AGENT_SHAS" || true)"
else
  FOREIGN_SHAS="$(git log --format='%H' "${BASE_REF}..${PRESS_BRANCH}")"
fi

# Nothing but the agent ever commits on press --- a foreign-authored commit
# there is itself a violation (unlike the old shared-checkout design, where
# human commits landing mid-run were expected and passed through).
if [ -n "$FOREIGN_SHAS" ]; then
  log "VALIDATION FAILURE: non-agent commit(s) on press:"
  # shellcheck disable=SC2086  # sha list is deliberately word-split
  git log --format='  %h %an %s' --no-walk $FOREIGN_SHAS >> "$LOG_FILE" 2>&1 || true
  rescue_and_abort
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
  rescue_and_abort
fi

if [ -n "$AGENT_SHAS" ]; then
  log "validated $(echo "$AGENT_SHAS" | wc -l) agent commit(s) against allowlist + firewall"
else
  log "no agent commits this run"
fi

# Push press to main on origin (the documented per-repo exception to the
# global manual-push rule, like the aps tracker's). When base was local main,
# any unpushed human commits ride along --- same semantics as the old
# shared-checkout push. Also redeploys prior validated work after a
# failed-generation run. Then fast-forward the human checkout's main when git
# allows it; a dirty checkout that can't take the update just stays behind
# origin until the human pulls (the next run bases on origin/main regardless).
log "=== push at $(date -Iseconds) ==="
if git push origin "${PRESS_BRANCH}:main" >> "$LOG_FILE" 2>&1; then
  if git merge --ff-only "$PRESS_BRANCH" >> "$LOG_FILE" 2>&1; then
    log "fast-forwarded local main to press"
  else
    log "NOTE: local main not fast-forwarded (dirty or diverged checkout); pull when convenient"
  fi
else
  log "push failed; commits stay on press (the next run rescues them onto publish-rescue/*)"
fi

flush_pending_post

log "=== run finished at $(date -Iseconds) ==="
