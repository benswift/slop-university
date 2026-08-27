#!/usr/bin/env bash
# The serial lander: take ONE completed candidate and publish it.
#
# Usage: ops/publish-land.sh [--dry-run] [--sweep-only]
#
#   --dry-run     do everything except the bucket upload and the push. For
#                 running the split alongside the live serial pipeline: origin
#                 is never touched, so the two cannot race, and every step that
#                 could reject a candidate still runs.
#   --sweep-only  expire abandoned candidates and report stale ones; land
#                 nothing.
#
# This is ops/cron-publish.sh with the agent invocation replaced by "claim the
# oldest unclaimed candidate". Base selection, the allowlist/denylist/firewall
# validation, the entry-to-asset pairing checks, the remote-race guard, the
# bucket uploads and the push all survive unchanged --- they are the same
# functions, in ops/publish-lib.sh, that the serial pipeline calls.
#
# Exactly one of these runs at a time, under the same flock the serial pipeline
# used. That is the design's whole point: concurrency lives in the generators,
# which have no shared state, and the part with real shared state stays
# single-threaded. In particular the remote-race guard needs no replacement ---
# it exists to catch a HUMAN pushing during a long generation window, and under
# this split the lander is the only thing that pushes and it holds the lock
# across fetch, rebase, verify, upload and push. If origin/main moves inside
# that window it was a human, which is exactly the guard's premise.
set -euo pipefail

# Overridable ONLY so the pipeline can be exercised end-to-end against a
# throwaway clone; the unattended units never set it.
PROJECT_DIR="${SLOPU_PROJECT_DIR:-/home/ben/projects/slop-university}"
# shellcheck source=ops/publish-lib.sh
source "${PROJECT_DIR}/ops/publish-lib.sh"

WORKTREE_DIR="${SLOPU_PRESS_WORKTREE:-/home/ben/projects/slop-university-press}"
PRESS_BRANCH="press"

DRY_RUN=0
SWEEP_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --sweep-only) SWEEP_ONLY=1 ;;
    *) echo "unknown argument: $arg" >&2; exit 2 ;;
  esac
done

# A candidate still unclaimed this long after it was written means the lander is
# not keeping up (or is not running); a human should hear about it. Generation
# takes ~20 minutes and the lander runs every few, so an hour is far outside
# normal.
STALE_MINUTES="${SLOPU_CANDIDATE_STALE_MINUTES:-60}"
# A branch or staging directory with no marker file belongs to a generator that
# died mid-run. Well beyond the longest observed generation, so an in-flight run
# is never mistaken for an abandoned one.
ABANDON_MINUTES="${SLOPU_CANDIDATE_ABANDON_MINUTES:-180}"

mkdir -p "$LOG_DIR" "${PROJECT_DIR}/data" "$CANDIDATE_DIR" "$PENDING_ROOT"
prune_logs
install_exit_trap

log "=== lander started at $(date -Iseconds)$([ "$DRY_RUN" = 1 ] && echo ' (DRY RUN)') ==="

# One lander. Non-blocking --- a lander that finds the lock held simply skips;
# the next timer tick retries. Deliberately the SAME lock file the serial
# pipeline uses, so the two can never both be pushing during the parallel-run
# window.
exec 9> "${PROJECT_DIR}/data/publish.lock"
if ! flock -n 9; then
  log "another publish run holds the lock; skipping"
  result "skipped-locked" "another publish run holds the lock; the next tick retries"
  exit 0
fi

activate_mise
cd "$PROJECT_DIR"

# --- Publish the staged social post, if one is waiting.
#
# A staged post references already-live site content, so it is valid to send
# regardless of what this run goes on to do (including aborting) --- which is
# why the flush lives in a function called from every exit path, not only after
# a clean push. Posted only on success; a failure leaves the file staged for the
# next run to retry (the poster dedups, so a lost-response retry cannot
# double-post). data/pending-post.json is a gitignored working-tree artefact,
# never committed: the agent COMPOSES it, the wrapper POSTS it --- the same
# trust split as "the agent commits, the wrapper pushes".
POSTED="no"
flush_pending_post() {
  [ "$DRY_RUN" = 1 ] && { log "dry run: leaving any staged social post alone"; return 0; }
  if [ -f "${PROJECT_DIR}/data/pending-post.json" ]; then
    log "=== posting staged social update at $(date -Iseconds) ==="
    if uv run "${PROJECT_DIR}/ops/post-to-bluesky.py" >> "$LOG_FILE" 2>&1; then
      rm -f "${PROJECT_DIR}/data/pending-post.json"
      POSTED="yes"
      log "posted and cleared data/pending-post.json"
    else
      log "social post failed; leaving data/pending-post.json staged for retry"
    fi
  fi
}

if pipeline_blocked; then
  result "blocked" "data/publish-blocked exists; a human must triage and remove it"
  exit 1
fi

# --- Sweeper: abandoned candidates out, stale ones reported.
#
# A crashed generator leaves an unclaimed branch and a staging directory rather
# than a stranded slot --- that is the design --- but something has to expire
# them or the repo accumulates dead refs and the disk fills with dead PDFs.
STALE_REPORT=""

# How long ago a run STARTED, from its id.
#
# The id is the generator's UTC start time, which is the only honest clock here.
# A branch's commit time is not: a generator that died before its agent
# committed leaves a branch pointing at whatever base it checked out, whose
# commit is as old as the last landing --- so a just-abandoned candidate would
# read as hours old, or a genuinely stale one as brand new. A directory's mtime
# is no better once anything touches it.
candidate_age_minutes() {
  local run_id="$1" stamp epoch
  # 20260825T180614Z-slot2 -> 2026-08-25T18:06:14Z
  stamp="${run_id%%-slot*}"
  stamp="${stamp:0:4}-${stamp:4:2}-${stamp:6:2}T${stamp:9:2}:${stamp:11:2}:${stamp:13:2}Z"
  if ! epoch="$(date -d "$stamp" +%s 2>/dev/null)"; then
    # An id this function cannot read is not evidence of staleness; say "new"
    # so the sweeper leaves it for a human rather than deleting it.
    echo 0
    return
  fi
  echo $(( ( $(date +%s) - epoch ) / 60 ))
}

sweep_candidates() {
  local marker run_id branch dir age_min landed

  shopt -s nullglob
  for branch in $(git for-each-ref --format='%(refname:short)' 'refs/heads/press-gen-*'); do
    run_id="${branch#press-gen-}"

    # Already landed. Compared by PATCH ID, not by containment: the lander
    # cherry-picks a candidate onto the current base, so the commit that shipped
    # has a different sha from the one on this branch and no ancestry test can
    # see the two are the same work. `git cherry` marks a commit "-" when an
    # equivalent patch is already upstream, so a branch with commits and no "+"
    # line has landed in full.
    #
    # This is the normal cleanup path. The lander cannot delete the branch at
    # push time, because the generator worktree that produced it still has it
    # checked out and keeps it until that slot's next run. A branch with no
    # commits at all produces no output here and falls through to the age check
    # below --- it may belong to a generator that is mid-run right now.
    landed="$(git cherry origin/main "$branch" 2>/dev/null || true)"
    if [ -n "$landed" ] && ! printf '%s\n' "$landed" | grep -q '^+'; then
      if git branch -D "$branch" >> "$LOG_FILE" 2>&1; then
        log "sweeper: removed landed branch ${branch}"
        rm -rf "${PENDING_ROOT:?}/${run_id}"
      else
        log "sweeper: landed branch ${branch} is still checked out somewhere; retrying next sweep"
      fi
      continue
    fi

    # Marker-less leftovers: a generator that died between creating its branch
    # and writing its marker. Old enough that no in-flight run is caught by this.
    [ -f "${CANDIDATE_DIR}/${run_id}.json" ] && continue
    [ -f "${CANDIDATE_DIR}/${run_id}.claimed" ] && continue
    age_min="$(candidate_age_minutes "$run_id")"
    if [ "$age_min" -ge "$ABANDON_MINUTES" ]; then
      log "sweeper: expiring abandoned candidate ${run_id} (branch ${age_min}m old, no marker)"
      git branch -D "$branch" >> "$LOG_FILE" 2>&1 || log "WARNING: could not delete ${branch}"
      rm -rf "${PENDING_ROOT:?}/${run_id}"
    fi
  done

  for dir in "${PENDING_ROOT}"/*/; do
    run_id="$(basename "$dir")"
    [ -f "${CANDIDATE_DIR}/${run_id}.json" ] && continue
    [ -f "${CANDIDATE_DIR}/${run_id}.claimed" ] && continue
    git show-ref --verify --quiet "refs/heads/press-gen-${run_id}" && continue
    age_min="$(candidate_age_minutes "$run_id")"
    if [ "$age_min" -ge "$ABANDON_MINUTES" ]; then
      log "sweeper: expiring orphaned staging dir ${run_id} (${age_min}m old, no branch, no marker)"
      rm -rf "$dir"
    fi
  done

  # Stale but INTACT candidates are the opposite problem: nothing is wrong with
  # them, the lander is simply not draining the queue. That reaches a human,
  # because a queue that only grows is how a live installation quietly stops
  # publishing while every unit stays green.
  for marker in "${CANDIDATE_DIR}"/*.json; do
    run_id="$(basename "$marker" .json)"
    age_min="$(candidate_age_minutes "$run_id")"
    if [ "$age_min" -ge "$STALE_MINUTES" ]; then
      STALE_REPORT="${STALE_REPORT}${run_id} (${age_min}m) "
    fi
  done
  shopt -u nullglob

  if [ -n "$STALE_REPORT" ]; then
    log "SWEEPER: candidate(s) unclaimed past ${STALE_MINUTES}m --- the lander is behind: ${STALE_REPORT}"
  fi
}
sweep_candidates

if [ "$SWEEP_ONLY" = 1 ]; then
  flush_pending_post
  if [ -n "$STALE_REPORT" ]; then
    result "stale-queue" "candidate(s) unclaimed past ${STALE_MINUTES}m: ${STALE_REPORT}"
    exit 6
  fi
  result "swept" "sweep complete; nothing stale"
  exit 0
fi

# --- Claim the oldest unclaimed candidate. Run ids are sortable timestamps, so
# oldest-first is a filename sort. The claim is a rename, which is atomic ---
# though only one lander runs at a time, so this is belt to the flock's braces.
shopt -s nullglob
MARKERS=("${CANDIDATE_DIR}"/*.json)
shopt -u nullglob
if [ ${#MARKERS[@]} -eq 0 ]; then
  log "no candidates waiting"
  flush_pending_post
  if [ "$POSTED" = "yes" ]; then
    result "posted" "social post published; no candidate was waiting"
    exit 0
  fi
  result "idle" "no candidates waiting to land"
  exit 0
fi

MARKER="${MARKERS[0]}"
RUN_ID="$(basename "$MARKER" .json)"
CLAIM="${CANDIDATE_DIR}/${RUN_ID}.claimed"
mv "$MARKER" "$CLAIM"
CAND_BRANCH="$(sed -n 's/.*"branch": *"\([^"]*\)".*/\1/p' "$CLAIM")"
CAND_BASE="$(sed -n 's/.*"base": *"\([^"]*\)".*/\1/p' "$CLAIM")"
CAND_PRESET="$(sed -n 's/.*"preset": *"\([^"]*\)".*/\1/p' "$CLAIM")"
PENDING_DIR="${PENDING_ROOT}/${RUN_ID}"
log "=== claimed candidate ${RUN_ID} (branch ${CAND_BRANCH}, base ${CAND_BASE:0:12}, preset ${CAND_PRESET}) ==="

if ! git show-ref --verify --quiet "refs/heads/${CAND_BRANCH}"; then
  log "claimed candidate's branch ${CAND_BRANCH} does not exist; discarding the marker"
  rm -f "$CLAIM"
  flush_pending_post
  result "candidate-missing" "candidate ${RUN_ID} had no branch ${CAND_BRANCH}"
  exit 1
fi

# --- Rescue a candidate rather than lose it, and never block the queue on one.
#
# A candidate contains a finished output: twenty minutes of generation, a typst
# compile, generated imagery and a Replicate spend. When the lander cannot take
# it, the answer is to set it aside for a human and move on to the next one ---
# not to discard it, and not to stop landing. Its assets move with it, so an
# unrelated later run can never upload bytes belonging to a rescued entry.
rescue_candidate() {
  local reason="$1" ts rescue_dir
  ts="$(date +%Y%m%d-%H%M%S)"
  if git branch -m "$CAND_BRANCH" "publish-rescue/${ts}-${RUN_ID}" >> "$LOG_FILE" 2>&1; then
    log "preserved candidate ${RUN_ID} on publish-rescue/${ts}-${RUN_ID} (${reason})"
  else
    log "WARNING: could not rename ${CAND_BRANCH} to a rescue branch"
  fi
  rescue_dir="${PROJECT_DIR}/data/publish-rescue/${ts}-${RUN_ID}"
  if [ -d "$PENDING_DIR" ]; then
    mkdir -p "$(dirname "$rescue_dir")"
    mv "$PENDING_DIR" "$rescue_dir"
    log "preserved its staged assets in ${rescue_dir}"
  fi
  mv "$CLAIM" "${CANDIDATE_DIR}/${RUN_ID}.rescued"
  git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1 || log "WARNING: reset press to ${BASE_REF} failed"
}

# --- Base: the newest published state. Same selection the serial pipeline used.
if ! select_base; then
  log "Skipping this run; the claimed candidate goes back on the queue."
  mv "$CLAIM" "${CANDIDATE_DIR}/${RUN_ID}.json"
  flush_pending_post
  # Its own exit code, because this is the one failure a human fixes with a
  # rebase rather than by looking at the pipeline. It ran for two days in
  # August 2026 and every tick in that window was lost.
  result "skipped-diverged" "main and origin/main have diverged; a human must rebase"
  exit 2
fi
log "landing onto ${BASE_NAME} ${BASE_REF}"

if ! ensure_worktree "$WORKTREE_DIR" "$PRESS_BRANCH" "$BASE_REF"; then
  mv "$CLAIM" "${CANDIDATE_DIR}/${RUN_ID}.json"
  result "config-error" "${WORKTREE_DIR} exists but is not a registered worktree"
  exit 1
fi

# --- Rebase the candidate onto the current base.
#
# The generator based on whatever local main held when it started, which may be
# several landings ago. Replaying its commits onto the current base is what
# makes that safe. Candidates touch disjoint files by construction (distinct
# output ids, news slugs, thumbnails and heroes; no shared-file writes since the
# finding-shape ledger became a static draw pool), so a conflict here means an
# assumption has broken --- rescue it and take the next one rather than guess.
git -C "$WORKTREE_DIR" checkout -B "$PRESS_BRANCH" "$BASE_REF" >> "$LOG_FILE" 2>&1
git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1
git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1
link_data_dir "$WORKTREE_DIR"

if ! git -C "$WORKTREE_DIR" cherry-pick "${CAND_BASE}..${CAND_BRANCH}" >> "$LOG_FILE" 2>&1; then
  log "REBASE CONFLICT replaying ${CAND_BRANCH} onto ${BASE_REF}"
  git -C "$WORKTREE_DIR" cherry-pick --abort >> "$LOG_FILE" 2>&1 || true
  rescue_candidate "rebase conflict"
  flush_pending_post
  result "rescued-conflict" "candidate ${RUN_ID} conflicted on rebase; rescued, queue continues"
  exit 7
fi
log "replayed $(git -C "$WORKTREE_DIR" rev-list --count "${BASE_REF}..HEAD") commit(s) onto ${BASE_REF}"

# --- Cheap gates first, expensive ones after.
#
# Validation and the pairing check cost seconds; the build costs minutes. Order
# matters for more than wall-clock: a candidate that touches a forbidden path and
# also happens to break the build must be reported as a VALIDATION failure, not
# as a red build. The two abort identically but call for completely different
# human responses, and the outcome line is what reaches the todo.

if ! validate_commits "$BASE_REF" "$PRESS_BRANCH"; then
  rescue_candidate "$VALIDATION_ERROR"
  flush_pending_post
  result "validation-failure" "candidate ${RUN_ID}: ${VALIDATION_ERROR}"
  exit 1
fi

# Assets the agent staged against the wrong cwd, folded back into THIS
# candidate's dir. Scoped to the press worktree, which only this candidate
# occupies.
rescue_stray_staging "$PENDING_DIR" "$WORKTREE_DIR"

if ! check_pairing "$BASE_REF" "$PRESS_BRANCH" "$PENDING_DIR"; then
  if [ -n "$MISSING_IMGS" ]; then
    log "VALIDATION FAILURE: new entry with images missing from ${PENDING_DIR}/img:"
    printf '%s' "$MISSING_IMGS" >> "$LOG_FILE"
  fi
  if [ -n "$MISSING_PDFS" ]; then
    log "VALIDATION FAILURE: new outputs entry with no PDF staged in ${PENDING_DIR}:"
    printf '%s' "$MISSING_PDFS" >> "$LOG_FILE"
    # Say WHERE it went, not just that it is absent. The first version of this
    # check reported only the missing name, and the PDFs turned out to be
    # landing in website/data/pending-uploads/ --- the agent had resolved a
    # relative path against website/. That cost a hunt through the worktree to
    # work out; this turns the same failure into one line of log.
    STRAYS="$(find "$WORKTREE_DIR" -name '*.pdf' -newermt '-3 hours' \
      -not -path "${WORKTREE_DIR}/output/pdf/*" -not -path "${PENDING_ROOT}/*" 2>/dev/null | head -20)"
    if [ -n "$STRAYS" ]; then
      log "  ...but these recent PDFs exist elsewhere in the worktree (mislanded staging path?):"
      printf '%s\n' "$STRAYS" >> "$LOG_FILE"
    fi
  fi
  rescue_candidate "entry with no staged assets"
  flush_pending_post
  result "rescued-pairing" "candidate ${RUN_ID} has an entry with no staged PDF or images; rescued, queue continues"
  exit 9
fi

if ! check_output_quality "$BASE_REF" "$PRESS_BRANCH" "$PENDING_DIR"; then
  rescue_candidate "$QUALITY_ERROR"
  flush_pending_post
  result "rescued-quality" "candidate ${RUN_ID}: ${QUALITY_ERROR}; rescued, queue continues"
  exit 10
fi

if ! worktree_install "$WORKTREE_DIR"; then
  log "pnpm install failed in the press worktree; putting the candidate back"
  mv "$CLAIM" "${CANDIDATE_DIR}/${RUN_ID}.json"
  flush_pending_post
  result "failed-setup" "pnpm install failed in the press worktree"
  exit 1
fi

# --- The one authoritative build.
#
# Generators skip it: it is the expensive step (~2 minutes cold) and running it
# on the parallel path N times over would also force the generator worktrees to
# stay warm. They still run format:content, typecheck, lint, lint:css and test
# (~9 seconds), so only a build failure with all of those green reaches here.
#
# The cost of moving it is real and worth naming: in the serial pipeline the
# agent fixed its own red build inside the run, and the lander has no model to
# do that. So a build failure is not a pipeline stop --- the candidate is
# rescued for a human and the lander takes the next one.
log "=== authoritative build at $(date -Iseconds) ==="
if ! (cd "${WORKTREE_DIR}/website" && pnpm build) >> "$LOG_FILE" 2>&1; then
  log "BUILD FAILED for candidate ${RUN_ID}; rescuing it and moving on"
  rescue_candidate "build failure"
  flush_pending_post
  result "rescued-build" "candidate ${RUN_ID} failed the authoritative build; rescued, queue continues"
  exit 8
fi

# --- Upload BEFORE the push, and only after a fresh fetch proves the remote tip
# is still contained in the candidate.
#
# Ordering is the whole point. The push is what makes the outputs entry live,
# and the entry's PDF URL is derived from its id --- so an entry that shipped
# before its bytes did would be a live 404. Keep the local copies until the push
# succeeds. If the remote moves during the short upload window, preserve the
# commit and the assets together for human recovery rather than throwing the
# commit away and leaving untraceable bucket objects.
log "=== pre-upload remote race check at $(date -Iseconds) ==="
if ! git fetch origin >> "$LOG_FILE" 2>&1; then
  log "REMOTE RACE GUARD: fetch failed; refusing to upload or push"
  rescue_candidate "pre-upload fetch failed"
  flush_pending_post
  result "failed-fetch" "pre-upload fetch of origin failed; refused to upload or push"
  exit 1
fi
if ! git merge-base --is-ancestor origin/main "$PRESS_BRANCH"; then
  log "REMOTE RACE GUARD: origin/main advanced outside press during landing; refusing to upload or push"
  rescue_candidate "origin/main advanced during landing"
  flush_pending_post
  result "remote-race" "origin/main advanced outside press during landing"
  exit 1
fi

shopt -s nullglob
PENDING_PDFS=("$PENDING_DIR"/*.pdf)
shopt -u nullglob

if [ "$DRY_RUN" = 1 ]; then
  log "=== DRY RUN: would upload ${#PENDING_PDFS[@]} PDF(s)$([ -d "${PENDING_DIR}/img" ] && echo ' plus the image tree') and push ${PRESS_BRANCH}:main ==="
  log "leaving candidate ${RUN_ID} intact for a human to inspect; nothing was sent"
  mv "$CLAIM" "${CANDIDATE_DIR}/${RUN_ID}.dryrun"
  git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1
  log "=== dry run finished at $(date -Iseconds) ==="
  result "dry-run-ok" "candidate ${RUN_ID} passed rebase, build, validation and pairing; not uploaded or pushed"
  exit 0
fi

if [ ${#PENDING_PDFS[@]} -gt 0 ] && bucket_upload_allowed; then
  log "=== uploading ${#PENDING_PDFS[@]} PDF(s) to the bucket at $(date -Iseconds) ==="
  if "${PROJECT_DIR}/ops/bucket-sync.py" upload "${PENDING_PDFS[@]}" >> "$LOG_FILE" 2>&1; then
    log "uploaded PDFs; retaining local copies until the git push succeeds"
  else
    log "BUCKET UPLOAD FAILED --- refusing to push an entry whose PDF is not served"
    rescue_candidate "bucket upload failed"
    flush_pending_post
    result "failed-upload" "bucket upload failed; the entry's PDF would not be served"
    exit 1
  fi
else
  log "no PDFs staged for this candidate"
fi

if [ -d "${PENDING_DIR}/img" ] && bucket_upload_allowed; then
  log "=== uploading the staged image tree to the img bucket at $(date -Iseconds) ==="
  if "${PROJECT_DIR}/ops/bucket-sync.py" upload --target img "${PENDING_DIR}/img" >> "$LOG_FILE" 2>&1; then
    log "uploaded images; retaining local copies until the git push succeeds"
  else
    log "IMG BUCKET UPLOAD FAILED --- refusing to push an entry whose images are not served"
    rescue_candidate "img bucket upload failed"
    flush_pending_post
    result "failed-upload" "img bucket upload failed; the entry's images would not be served"
    exit 1
  fi
else
  log "no images staged for this candidate"
fi

# Push press to main on origin (the documented per-repo exception to the global
# manual-push rule). Then fast-forward the human checkout's main when git allows
# it --- which is also what keeps the generators' local base recent. A dirty
# checkout that cannot take the update just stays behind origin until the human
# pulls; the lander bases on origin/main regardless.
log "=== push at $(date -Iseconds) ==="
if git push origin "${PRESS_BRANCH}:main" >> "$LOG_FILE" 2>&1; then
  rm -rf "$PENDING_DIR"
  rm -f "$CLAIM"
  # Best-effort: the generator worktree that produced this branch still has it
  # checked out until that slot's next run, and git rightly refuses to delete it
  # from under a worktree. The sweeper collects it on containment instead.
  git branch -D "$CAND_BRANCH" >> "$LOG_FILE" 2>&1 \
    || log "landed branch ${CAND_BRANCH} is still checked out in its generator worktree; the sweeper will remove it"
  log "push succeeded; cleared candidate ${RUN_ID}'s staging dir and marker"
  if git merge --ff-only "$PRESS_BRANCH" >> "$LOG_FILE" 2>&1; then
    log "fast-forwarded local main to press"
  else
    log "NOTE: local main not fast-forwarded (dirty or diverged checkout); pull when convenient"
  fi
else
  log "push failed after the remote race check; preserving the candidate and its assets"
  rescue_candidate "push failed"
  flush_pending_post
  result "failed-push" "git push failed after the remote race check"
  exit 1
fi

flush_pending_post

log "=== lander finished at $(date -Iseconds) ==="
result "published" "landed candidate ${RUN_ID}: $(git log --format='%s' -1 "$PRESS_BRANCH")"
