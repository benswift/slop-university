#!/usr/bin/env bash
# A concurrent generator slot: produce ONE publish candidate and stop.
#
# Usage: ops/publish-generate.sh <slot>       (slot is a small integer, 1..N)
#
# The generator never touches origin, never uploads and never pushes. It runs
# the agent in its own worktree, keeps whatever the agent committed on a branch
# named for the run, leaves the run's PDFs and images in their own staging
# directory, writes one marker file, and exits. ops/publish-land.sh does
# everything after that, serially, one candidate at a time.
#
# Why the split. Ticks were serialised by a non-blocking flock, the timer was
# hourly and a run took ~20 minutes, so the timer could not buy throughput ---
# below ~30 minutes the extra ticks simply skipped. Concurrency was the only
# lever, and the blocker was semantic rather than mechanical: /publish is
# gap-driven, so two agents assessing the same base state identify the SAME gap
# and produce two files that merge perfectly and are semantically duplicates.
# Only 2A parallelises (distinct output ids, news slugs, thumbnails, heroes), so
# extra slots run 2A only and exactly one slot keeps the full gap ladder.
#
# The safety-critical section --- rebase, validate, upload, push --- is NOT made
# concurrent. That was the alternative design (N symmetric slots each pushing
# under a short lock) and it would have made the one part of the pipeline with
# real shared state N-way contended, and forced it to handle rebase conflicts
# the code has never had to. Here concurrency is confined to the part with no
# shared state at all.
#
# Slot 1 is the gardening slot: it runs the whole ladder (2B-2I), so bios,
# blurbs, pages, news, grants and the social post keep flowing. Slots 2+ are
# pinned to 2A. That asymmetry is deliberate --- the gardening rungs are gated
# on shared state (2G if socials are due, 2H if the newsroom is due, 2I picks
# "the researcher in no grant's grantees"), so two slots reading it choose the
# same gap, and no merge strategy catches a semantic duplicate.
set -euo pipefail

# Overridable ONLY so the pipeline can be exercised end-to-end against a
# throwaway clone; the unattended units never set it.
PROJECT_DIR="${SLOPU_PROJECT_DIR:-/home/ben/projects/slop-university}"
# shellcheck source=ops/publish-lib.sh
source "${PROJECT_DIR}/ops/publish-lib.sh"

SLOT="${1:?usage: publish-generate.sh <slot>}"
case "$SLOT" in
  ''|*[!0-9]*) echo "slot must be a positive integer" >&2; exit 2 ;;
esac

WORKTREE_DIR="${PROJECT_DIR}/../slop-university-gen-${SLOT}"
WORKTREE_DIR="$(cd "$(dirname "$WORKTREE_DIR")" && pwd)/$(basename "$WORKTREE_DIR")"
# Sortable, so the lander's "oldest first" is a plain filename sort, and unique
# per slot, so two slots starting in the same second cannot collide.
RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-slot${SLOT}"
CAND_BRANCH="press-gen-${RUN_ID}"
PENDING_DIR="${PENDING_ROOT}/${RUN_ID}"

mkdir -p "$LOG_DIR" "${PROJECT_DIR}/data" "$CANDIDATE_DIR" "$PENDING_DIR"
prune_logs
install_exit_trap

log "=== generator slot ${SLOT} started at $(date -Iseconds) (run ${RUN_ID}) ==="

# Serialise a slot against ITSELF only. Slots do not contend with each other ---
# that is the whole point --- but a slot whose previous run is still going must
# skip rather than start a second agent in the same worktree.
exec 9> "${PROJECT_DIR}/data/publish-gen-${SLOT}.lock"
if ! flock -n 9; then
  log "slot ${SLOT} is still busy with an earlier run; skipping"
  result "skipped-locked" "generator slot ${SLOT} is still running an earlier candidate"
  exit 0
fi

activate_mise
cd "$PROJECT_DIR"

if pipeline_blocked; then
  result "blocked" "data/publish-blocked exists; a human must triage and remove it"
  exit 1
fi

# --- Discard this run's work and leave nothing behind for the lander to find.
# Called on every failure path; a generator has no rescue branch because it has
# produced nothing a human would want. (A candidate that FAILS IN THE LANDER is
# a different matter and does get rescued --- it contains a finished output.)
discard_candidate() {
  rm -rf "$PENDING_DIR"
  rm -f "${CANDIDATE_DIR}/${RUN_ID}.json" "${CANDIDATE_DIR}/${RUN_ID}.json.tmp"
  if git show-ref --verify --quiet "refs/heads/${CAND_BRANCH}"; then
    git -C "$WORKTREE_DIR" checkout --detach --quiet 2>/dev/null || true
    git branch -D "$CAND_BRANCH" >> "$LOG_FILE" 2>&1 || log "WARNING: could not delete ${CAND_BRANCH}"
  fi
}

# --- Base: the newest state this machine knows is published.
#
# Deliberately a LOCAL ref. The generator must not fetch (it is one of N and
# origin is the lander's business), and it does not need to: the lander rebases
# every candidate onto the current origin/main before it lands, so the base here
# only has to be recent, not current. The lander fast-forwards local main after
# each push, so it is.
BASE_REF="$(git rev-parse main)"
log "basing on local main ${BASE_REF}"

if ! ensure_worktree "$WORKTREE_DIR" "$CAND_BRANCH" "$BASE_REF"; then
  result "config-error" "${WORKTREE_DIR} exists but is not a registered worktree"
  exit 1
fi

# Fresh branch per run, off the chosen base. -B rather than a new worktree each
# time: the worktree is persistent so node_modules, the typst cache and the
# pnpm store survive between runs, which is most of why a generator can be
# cheap. clean is deliberately not -x --- gitignored state survives; only a
# crashed run's untracked residue goes.
git -C "$WORKTREE_DIR" checkout -B "$CAND_BRANCH" "$BASE_REF" >> "$LOG_FILE" 2>&1
git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1
git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1
link_data_dir "$WORKTREE_DIR"

if ! worktree_install "$WORKTREE_DIR"; then
  log "pnpm install failed in ${WORKTREE_DIR}; aborting"
  discard_candidate
  result "failed-setup" "pnpm install failed in generator slot ${SLOT}"
  exit 1
fi

draw_run_inputs "$WORKTREE_DIR"

# Slot 1 gardens; the rest are pinned to 2A. See the header.
if [ "$SLOT" = "1" ]; then
  compose_agent_prompt ""
else
  compose_agent_prompt "This is a 2A-only generator slot: take rung 2A (a new research output) regardless of what the ladder in phase 1 would otherwise choose, and do not take any of 2B-2I. If 2A itself cannot proceed, do nothing and exit."
fi

# shellcheck disable=SC2034  # consumed by run_agent/publish_on_exit in publish-lib.sh
AGENT_OUT="$(mktemp)"
# Per-slot, so a slot's credit verdict is read from its OWN turn records rather
# than a sibling's. The EXIT trap clears AGENT_OUT.
# shellcheck disable=SC2034  # consumed by run_agent/hook_was_live in publish-lib.sh
STOP_FAILURE_LOG="${PROJECT_DIR}/data/stop-failures-gen-${SLOT}.jsonl"

# What the agent must do differently in a generator slot:
#   SLOPU_PENDING_DIR --- stage into this run's own directory, so two slots
#     staging at the same moment cannot see or clobber each other's assets.
#   SLOPU_SKIP_BUILD --- run every site check EXCEPT `pnpm build`. The build is
#     ~2 minutes cold and the lander runs the one authoritative build anyway;
#     keeping it here would put it on the parallel path N times over and force
#     the generator worktrees to stay warm. The cheap checks (format:content,
#     typecheck, lint, lint:css, test --- about 9 seconds) stay, so only a build
#     failure with all of those green can reach the lander, which is rare.
export SLOPU_PENDING_DIR="$PENDING_DIR"
export SLOPU_SKIP_BUILD=1

run_agent "$WORKTREE_DIR" "$AGENT_MODEL"

if agent_auth_failed; then
  RELOGIN="$(relogin_hint)"
  log "AGENT AUTH FAILURE --- the unattended agent could not authenticate. No work was attempted."
  log "  Fix: run: ${RELOGIN}, then let the next run go."
  discard_candidate
  result "failed-auth" "agent could not authenticate; a human must run: ${RELOGIN}"
  exit 3
fi

# Only retry on the fallback model when the run produced NOTHING. A mid-run
# exhaustion leaves half a candidate on the branch, and regenerating over the
# top of that is how two outputs end up claiming one DOI.
if credits_exhausted; then
  log "AGENT OUT OF CREDITS on model ${AGENT_MODEL}."
  if [ "$(git -C "$WORKTREE_DIR" rev-parse HEAD)" = "$BASE_REF" ] && ! staged_anything "$PENDING_DIR"; then
    git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1
    # Order matters: the hard-exhaustion test reads the attempt's output, and
    # the switch it guards overwrites the profile that test would classify by.
    if credits_hard_exhausted && switch_to_fallback_profile; then
      log "  the whole account balance is gone, so another model billed to it would refuse too;"
      log "  retrying on the fallback profile ${AGENT_PROFILE} (model ${AGENT_MODEL})"
      run_agent "$WORKTREE_DIR" "$AGENT_MODEL"
    else
      log "  nothing was generated; retrying on the fallback model ${AGENT_FALLBACK_MODEL}"
      run_agent "$WORKTREE_DIR" "$AGENT_FALLBACK_MODEL"
    fi
  else
    log "  the run had already staged work; not retrying"
  fi
fi
# Re-read, because a retry overwrote $AGENT_OUT: this asks whether the FALLBACK
# also refused. Both models out is a real stop --- the account has nothing left
# to generate with and every later run dies identically, so the failed unit is
# what puts it in front of a human. Like the auth check it does not write
# data/publish-blocked: a limit window un-breaks itself, and blocking would turn
# a wait into a two-step fix.
#
# This is also the signal that says whether N slots have overrun the plan. It
# has never fired at one run an hour; if it starts firing after a slot is added,
# that is the ceiling talking, and data/stop-failures-gen-*.jsonl carries xAI's
# own classification plus errorDetails verbatim.
if credits_exhausted; then
  log "AGENT OUT OF CREDITS --- the retry on ${AGENT_PROFILE}/${AGENT_MODEL} refused too."
  log "  Fix: wait for the usage window to reset, or point SLOPU_AGENT_PROFILE / SLOPU_AGENT_MODEL"
  log "  at a route that still has credits."
  log "  If this began after adding a slot, the subscription is the ceiling: reduce slots."
  discard_candidate
  result "out-of-credits" "no usage credits on ${AGENT_PROFILE}/${AGENT_MODEL} or its fallback in slot ${SLOT}"
  exit 5
fi

if [ "$AGENT_STATUS" -ne 0 ]; then
  log "publish agent failed with status ${AGENT_STATUS}"
fi

# Assets the agent resolved against the wrong cwd, folded back into this run's
# staging dir. Only this slot's worktree is searched: a stray under another
# slot's tree belongs to that run, and stealing it would pair one candidate's
# entry with another's bytes.
rescue_stray_staging "$PENDING_DIR" "$WORKTREE_DIR"

RESIDUE="$(git -C "$WORKTREE_DIR" status --porcelain)"
if [ -n "$RESIDUE" ]; then
  log "post-run residue in ${WORKTREE_DIR} (next run's reset/clean clears it):"
  echo "$RESIDUE" >> "$LOG_FILE"
fi

HEAD_SHA="$(git -C "$WORKTREE_DIR" rev-parse HEAD)"
if [ "$HEAD_SHA" = "$BASE_REF" ]; then
  # No commit is a legitimate outcome: a 2G tick posts without committing, and
  # "nothing is due" is a real rung. Neither leaves a candidate to land.
  if [ -f "${PROJECT_DIR}/data/pending-post.json" ]; then
    log "no commit, but a social post is staged for the lander to flush"
    discard_candidate
    result "staged-post" "agent staged a social post; no candidate to land"
    exit 0
  fi
  log "agent committed nothing; no candidate produced"
  discard_candidate
  if [ "$AGENT_STATUS" -ne 0 ]; then
    result "failed-generation" "agent exited ${AGENT_STATUS} and committed nothing in slot ${SLOT}; rolled preset=${PRESET}"
    exit 4
  fi
  # Non-zero for the same reason as the serial pipeline's no-op: a generator
  # that exits clean having produced no candidate has lost its slot, and a zero
  # exit would fire OnSuccess= and clear the standing on-call todo on its way
  # out. See ops/cron-publish.sh for the long version.
  result "no-op" "agent exited cleanly but committed nothing in slot ${SLOT} (a lost slot); preset=${PRESET}"
  exit 6
fi

# --- Hand off. The marker is written LAST and atomically, so its existence is
# the signal that this candidate is whole: branch created, commits made, assets
# staged. A generator killed at any earlier point leaves a branch and a staging
# dir with no marker, which the lander's sweeper expires rather than lands.
cat > "${CANDIDATE_DIR}/${RUN_ID}.json.tmp" <<JSON
{
  "run_id": "${RUN_ID}",
  "slot": ${SLOT},
  "branch": "${CAND_BRANCH}",
  "base": "${BASE_REF}",
  "head": "${HEAD_SHA}",
  "preset": "${PRESET}",
  "pending_dir": "${PENDING_DIR}",
  "created_at": "$(date -Iseconds)"
}
JSON
mv "${CANDIDATE_DIR}/${RUN_ID}.json.tmp" "${CANDIDATE_DIR}/${RUN_ID}.json"

# Let go of the branch. The commits stay --- a branch ref is independent of any
# worktree's HEAD --- but git refuses to delete a branch that some worktree has
# checked out, and this slot has no further use for it. Detaching here is what
# lets the lander delete the branch the moment it lands, rather than leaving a
# ref behind until this slot happens to start its next run. The next run does
# `checkout -B` anyway, so a detached HEAD in between costs nothing.
git -C "$WORKTREE_DIR" checkout --detach --quiet 2>/dev/null \
  || log "NOTE: could not detach ${WORKTREE_DIR} from ${CAND_BRANCH}; the sweeper will collect the ref"

log "=== candidate ${RUN_ID} ready at $(date -Iseconds) ==="
result "candidate" "slot ${SLOT} produced candidate ${RUN_ID}: $(git -C "$WORKTREE_DIR" log --format='%s' -1)"
