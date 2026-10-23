#!/usr/bin/env bash
# A concurrent generator slot: produce ONE publish candidate and stop.
#
# Usage: ops/publish-generate.sh <slot>       (slot is a small integer, 1..N,
#                                              or `thesis`, or `thesis<N>`)
#
# The generator never touches origin, never uploads and never pushes. It runs
# the agent in its own worktree, keeps whatever the agent committed on a branch
# named for the run, leaves the run's PDFs and images in their own staging
# directory, writes one marker file, and exits. ops/publish-land.sh does
# everything after that, serially, one candidate at a time.
#
# Concurrency is confined to generation, the part with no shared state; the
# safety-critical section --- rebase, validate, upload, push --- stays serial
# in the lander. /publish is gap-driven, so two agents assessing the same state
# identify the SAME gap and produce semantic duplicates that merge perfectly.
# Only 2A parallelises (distinct output ids, news slugs, thumbnails, heroes).
#
# Slot 1 is the gardening slot: it runs the whole ladder (2B-2I), so bios,
# blurbs, pages, news, grants and the social post keep flowing. Slots 2+ are
# pinned to 2A. That asymmetry is deliberate --- the gardening rungs are gated
# on shared state (2G if socials are due, 2H if the newsroom is due, 2I picks the
# researcher whose funding lags their output), so two slots reading it choose the
# same gap, and no merge strategy catches a semantic duplicate.
#
# The `thesis` slot is the one rung with no timer: a human runs it (bin/slopu
# thesis) to spend a token budget on a doctoral thesis, action 2T. It is a
# generator like the others --- its own worktree, branch and staging dir, a
# candidate the lander lands --- with two differences: its inputs are the
# thesis fiction rather than an assessed rung, and it has no fallback model,
# because a run that exists to spend a budget either has it or does not.
#
# `thesis<N>` (thesis2, thesis3, ...) are further thesis slots, identical but for
# their own worktree and lock, so several theses can be written at once
# (bin/slopu --slot <N> thesis). Every thesis admits its candidate to
# canon/roster.yml, so concurrent ones conflict in the lander: the first lands
# and the rest are rescued, to be rebased by hand and re-queued with a candidate
# marker.
set -euo pipefail

# Overridable ONLY so the pipeline can be exercised end-to-end against a
# throwaway clone; the unattended units never set it.
PROJECT_DIR="${SLOPU_PROJECT_DIR:-/home/ben/projects/slop-university}"
# shellcheck source=ops/publish-lib.sh
source "${PROJECT_DIR}/ops/publish-lib.sh"

SLOT="${1:?usage: publish-generate.sh <slot>}"
THESIS=0
case "$SLOT" in
  thesis) THESIS=1 ;;
  thesis*[!0-9]*) echo "a thesis slot is 'thesis' or 'thesis<N>'" >&2; exit 2 ;;
  thesis*) THESIS=1 ;;
  ''|*[!0-9]*) echo "slot must be a positive integer, 'thesis' or 'thesis<N>'" >&2; exit 2 ;;
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
take_lock "${PROJECT_DIR}/data/publish-gen-${SLOT}.lock" \
  "slot ${SLOT} is still busy with an earlier run; skipping" \
  "generator slot ${SLOT} is still running an earlier candidate" || exit 0

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

# A thesis run that died at the session limit leaves its candidate's admission
# (roster entry, headshot, person hero) and its site entries uncommitted in the
# worktree, beside an hour of drafting under output/. The reset below would
# erase all of it but output/, so a thesis slot refuses to start over unfinished
# work: a human finishes it by hand (skills/publish/SKILL.md §2T) or clears it.
if [ "$THESIS" = 1 ] && [ -n "$(git -C "$WORKTREE_DIR" status --porcelain)" ]; then
  log "slot ${SLOT} holds an unfinished thesis in ${WORKTREE_DIR}; not resetting it:"
  git -C "$WORKTREE_DIR" status --short >> "$LOG_FILE" 2>&1
  rmdir "$PENDING_DIR" 2>/dev/null || true
  result "unfinished-thesis" "${WORKTREE_DIR} has uncommitted work from an earlier thesis run; finish or clear it before running slot ${SLOT} again"
  exit 1
fi

reset_worktree "$WORKTREE_DIR" "$CAND_BRANCH" "$BASE_REF"

if ! worktree_install "$WORKTREE_DIR"; then
  log "pnpm install failed in ${WORKTREE_DIR}; aborting"
  discard_candidate
  result "failed-setup" "pnpm install failed in generator slot ${SLOT}"
  exit 1
fi

if [ "$SLOT" = "1" ]; then
  draw_run_inputs "$WORKTREE_DIR"
elif [ "$THESIS" = 1 ]; then
  draw_run_inputs "$WORKTREE_DIR" thesis
else
  draw_run_inputs "$WORKTREE_DIR" 2a-only
fi

# Slot 1 gardens; the thesis slot writes a thesis; the rest are pinned to 2A.
# See the header.
#
# A thesis run may be steered: `bin/slopu thesis "<topic>"` sets SLOPU_STEER and
# the topic arrives named on the invocation line, exactly as the preset and the
# axes do. It replaces the topic the run would compose, never the drawn fiction
# --- a steered thesis still sits in the setting and school the wrapper drew, so
# the corpus does not acquire a run whose every choice a human made.
STEER=""
if [ "$THESIS" = 1 ] && [ -n "${SLOPU_STEER:-}" ]; then
  STEER="This run's topic was steered by the human who started it: ${SLOPU_STEER}
Take that as the topic instead of composing one (§2T step 2); dedup and claim it as usual. The drawn fiction above still stands: site the work in the drawn setting, and compose the title, the studies and the findings to satisfy both."
fi
compose_agent_prompt "$STEER"

# shellcheck disable=SC2034  # consumed by run_agent/publish_on_exit in publish-lib.sh
AGENT_OUT="$(mktemp)"

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
  log "AGENT AUTH FAILURE --- the unattended agent could not authenticate. No work was attempted."
  log "  Fix: run: claude /login, then let the next run go."
  discard_candidate
  result "failed-auth" "agent could not authenticate; a human must run: claude /login"
  exit 3
fi

# Only retry on the fallback model when the run produced NOTHING. A mid-run
# exhaustion leaves half a candidate on the branch, and regenerating over the
# top of that is how two outputs end up claiming one DOI.
if credits_exhausted; then
  log "AGENT OUT OF CREDITS on model ${AGENT_MODEL}."
  if [ "$THESIS" = 1 ]; then
    log "  a thesis run has no fallback: it spends the budget it was given or stops"
  elif [ "$(git -C "$WORKTREE_DIR" rev-parse HEAD)" = "$BASE_REF" ] && ! staged_anything "$PENDING_DIR"; then
    git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1
    if credits_hard_exhausted; then
      log "  the whole subscription is out, so another model billed to it would refuse too; not retrying"
    else
      log "  nothing was generated; retrying on the fallback model ${AGENT_FALLBACK_MODEL}"
      run_agent "$WORKTREE_DIR" "$AGENT_FALLBACK_MODEL"
    fi
  else
    log "  the run had already staged work; not retrying"
  fi
fi
# Re-read, because a retry overwrote $AGENT_OUT: this asks whether the FALLBACK
# also refused (or there was no retry worth making). Both out is a real stop --- every later run dies identically, so
# the failed unit is what puts it in front of a human. Like the auth check it
# does not write data/publish-blocked: a limit window un-breaks itself. If this
# starts firing after a slot is added, the subscription is the ceiling.
if credits_exhausted; then
  log "AGENT OUT OF CREDITS --- nothing left to try on ${AGENT_PROFILE}."
  log "  Fix: wait for the usage window to reset, or point SLOPU_AGENT_PROFILE / SLOPU_AGENT_MODEL"
  log "  at a route that still has credits."
  log "  If this began after adding a slot, the subscription is the ceiling: reduce slots."
  if [ "$(git -C "$WORKTREE_DIR" rev-parse HEAD)" != "$BASE_REF" ]; then
    # The limit arrived after the agent had committed (or the transcript merely
    # quotes the limit wording): that is a candidate, not nothing. The marker
    # path below hands it to the lander, which validates it like any other; a
    # half-finished one fails pairing there and is rescued, never deleted.
    log "  the run had already committed; keeping the candidate for the lander"
  else
    discard_candidate
    result "out-of-credits" "no usage credits on ${AGENT_PROFILE}/${AGENT_MODEL} or its fallback model in slot ${SLOT}"
    exit 5
  fi
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
  if staged_post_exists; then
    log "no commit, but a social post is staged for the lander to flush"
    discard_candidate
    result "staged-post" "agent staged a social post; no candidate to land"
    exit 0
  fi
  log "agent committed nothing; no candidate produced"
  discard_candidate
  if [ "$AGENT_STATUS" -ne 0 ]; then
    result "failed-generation" "agent exited ${AGENT_STATUS} and committed nothing in slot ${SLOT}; action=${ACTION} preset=${PRESET}"
    exit 4
  fi
  # Non-zero: a generator that exits clean having produced no candidate has
  # lost its slot (an agent that stopped to ask a question looks like this), and
  # a zero exit would fire OnSuccess= and clear the standing on-call todo.
  result "no-op" "agent exited cleanly but committed nothing in slot ${SLOT} (a lost slot); action=${ACTION} preset=${PRESET}"
  exit 6
fi

# --- Hand off. The marker is written LAST and atomically, so its existence is
# the signal that this candidate is whole: branch created, commits made, assets
# staged. A generator killed at any earlier point leaves a branch and a staging
# dir with no marker, which the lander's sweeper expires rather than lands.
jq -n --arg run_id "$RUN_ID" --arg slot "$SLOT" --arg branch "$CAND_BRANCH" \
  --arg base "$BASE_REF" --arg head "$HEAD_SHA" --arg preset "$PRESET" \
  --arg pending_dir "$PENDING_DIR" --arg created_at "$(date -Iseconds)" \
  '$ARGS.named' > "${CANDIDATE_DIR}/${RUN_ID}.json.tmp"
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
