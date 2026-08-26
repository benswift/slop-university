#!/usr/bin/env bash
# The serial publish pipeline: one process generates one action and lands it.
#
# This is the original single-threaded tick, and it remains the live pipeline.
# It shares every safety-critical step with the concurrent split
# (ops/publish-generate.sh + ops/publish-land.sh) through ops/publish-lib.sh ---
# base selection, commit validation, the entry-to-asset pairing check, the
# agent-failure classifiers. One copy, so the two paths cannot drift on the
# question of what may be committed and what must ship with it.
#
# The difference is orchestration, not policy: here one process holds the lock
# from generation through push, which is simple and correct and caps throughput
# at one output per run. See ops/publish-generate.sh for why that cap needed
# lifting and what the split does about it.
set -euo pipefail

# Overridable ONLY so the pipeline can be exercised end-to-end against a
# throwaway clone; the unattended units never set it.
PROJECT_DIR="${SLOPU_PROJECT_DIR:-/home/ben/projects/slop-university}"
# shellcheck source=ops/publish-lib.sh
source "${PROJECT_DIR}/ops/publish-lib.sh"

WORKTREE_DIR="${SLOPU_PRESS_WORKTREE:-/home/ben/projects/slop-university-press}"
PRESS_BRANCH="press"
# The serial pipeline stages at the root of the handoff tree; only the
# concurrent generators need a directory per run.
PENDING_DIR="$PENDING_ROOT"

mkdir -p "$LOG_DIR" "${PROJECT_DIR}/data" "$PENDING_DIR"
prune_logs
install_exit_trap

# Serialize runs: Persistent=true catch-up ticks and a still-running previous
# tick must never overlap (an overlapped pair each sees the other's commits as
# its own and validation becomes meaningless). Non-blocking --- a tick that
# finds the lock held simply skips; the next hourly tick retries.
exec 9> "${PROJECT_DIR}/data/publish.lock"
if ! flock -n 9; then
  log "=== $(date -Iseconds): another publish run holds the lock; skipping ==="
  # Not a failed run and not a lost tick: the holder is still working. Reported
  # as its own outcome so a pile of these reads as one long run rather than as
  # a pipeline that has stopped doing anything.
  result "skipped-locked" "another publish run holds the lock; the next tick retries"
  exit 0
fi

activate_mise
cd "$PROJECT_DIR"

log "=== publish run started at $(date -Iseconds) ==="

# --- Publish the staged social post, if one is waiting. A staged post
# references already-live site content, so it is valid to send regardless of
# what this run goes on to do (including aborting) --- which is why the flush
# lives in a function called from every exit path, not only after a clean push.
# Posted only on success; a failure leaves the file staged for the next run to
# retry (the poster dedups, so a lost-response retry can't double-post).
# data/pending-post.json is a gitignored working-tree artefact, never committed:
# the agent COMPOSES it, this wrapper POSTS it --- the same trust split as "the
# agent commits, the wrapper pushes". Note what that split does and does not
# buy. It is STRUCTURAL for the action: the agent has no path to send a post,
# because only this wrapper calls the poster. It is NOT isolation of the
# credential --- see run_agent's `env -u` list in publish-lib.sh, which is where
# that half is done.
#
# POSTED records whether this run actually sent one, because otherwise the
# outcome line libels a good run: a 2G tick does its whole job without
# committing anything (the post is a gitignored artefact), so judging the run by
# its commits alone reports "committed nothing" for a tick that worked.
POSTED="no"
flush_pending_post() {
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
  log "=== run refused at $(date -Iseconds) ==="
  result "blocked" "data/publish-blocked exists; a human must triage and remove it"
  exit 1
fi

if ! ensure_worktree "$WORKTREE_DIR" "$PRESS_BRANCH" main; then
  flush_pending_post
  result "config-error" "${WORKTREE_DIR} exists but is not a registered worktree"
  exit 1
fi

if ! select_base; then
  log "Skipping this tick."
  flush_pending_post
  log "=== run skipped at $(date -Iseconds) ==="
  # Its own exit code, because this is the one failure a human fixes with a
  # rebase rather than by looking at the pipeline. It ran for two days in
  # August 2026 and every tick in that window was lost.
  result "skipped-diverged" "main and origin/main have diverged; a human must rebase"
  exit 2
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

# Reset the worktree to base and clear crash residue. clean is deliberately not
# -x: gitignored state (output/ scratch, .typst-cache/, website's node_modules,
# the data symlink) survives; only untracked non-ignored files --- a crashed
# run's half-staged content --- are removed.
git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1
git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1
link_data_dir "$WORKTREE_DIR"

if ! worktree_install "$WORKTREE_DIR"; then
  log "pnpm install failed in press worktree; aborting run"
  flush_pending_post
  result "failed-setup" "pnpm install failed in the press worktree"
  exit 1
fi

# Preserve, never destroy, on an abort after generation. main is never touched
# --- the candidate commits exist only on press, so rescue is a branch pointer
# plus a worktree reset. PDFs move with the rescue instead of remaining in the
# live handoff directory for an unrelated later tick to upload.
quarantine_pending_pdfs() {
  local ts="$1" rescue_dir
  local -a pdfs
  shopt -s nullglob
  pdfs=("$PENDING_DIR"/*.pdf)
  shopt -u nullglob
  rescue_dir="${PROJECT_DIR}/data/publish-rescue/${ts}"
  if [ ${#pdfs[@]} -gt 0 ]; then
    mkdir -p "$rescue_dir"
    mv "${pdfs[@]}" "$rescue_dir"/
    log "preserved ${#pdfs[@]} staged PDF(s) in ${rescue_dir}"
  fi
  if [ -d "${PENDING_DIR}/img" ]; then
    mkdir -p "$rescue_dir"
    mv "${PENDING_DIR}/img" "$rescue_dir"/img
    log "preserved the staged image tree in ${rescue_dir}/img"
  fi
}

# Args: <outcome-token> <detail> [exit-code]. Every abort names itself, so the
# journal line (and the todo built from it) distinguishes a firewall violation
# from a lost push from a dead credential --- they abort identically here but
# call for completely different human responses.
rescue_and_abort() {
  result "$1" "$2"
  local ts; ts="$(date +%Y%m%d-%H%M%S)"
  if [ "$(git rev-parse "$PRESS_BRANCH")" != "$BASE_REF" ]; then
    if git branch "publish-rescue/${ts}" "$PRESS_BRANCH" >> "$LOG_FILE" 2>&1; then
      log "preserved commits ${BASE_REF}..${PRESS_BRANCH} on branch publish-rescue/${ts}"
    else
      log "WARNING: could not create rescue branch publish-rescue/${ts}"
    fi
  fi
  quarantine_pending_pdfs "$ts"
  git -C "$WORKTREE_DIR" reset --hard "$BASE_REF" >> "$LOG_FILE" 2>&1 || log "WARNING: reset press to ${BASE_REF} failed"
  log "=== reset press to ${BASE_REF}; run aborted at $(date -Iseconds) ==="
  flush_pending_post
  exit "${3:-1}"
}

# The publish agent generates one output, stages it into website/, verifies the
# site builds, and commits --- it never pushes (that's this wrapper's job, after
# validation). A failed generation is tolerated: the push below still redeploys
# whatever previously passed validation.
draw_run_inputs "$WORKTREE_DIR"
compose_agent_prompt ""

# Captured rather than appended straight to the log, because the classifiers
# below have to read what the agent said. It lands in the log either way; the
# EXIT trap removes the temp copy on every path, including the aborts.
# shellcheck disable=SC2034  # consumed by run_agent/publish_on_exit in publish-lib.sh
AGENT_OUT="$(mktemp)"
# Where the Grok StopFailure hook records how each turn ended. Grok classifies
# its own API failures into six tokens and hands them to a hook, which is a far
# better signal than grepping the agent's prose for phrasings lifted out of the
# binary's strings. See ops/grok-stop-failure-hook.py (and note it does NOT
# cover auth --- that fails before a session exists, so no hook fires; the regex
# is still the only detector for it).
#
# A gitignored file under data/, like the other handoff artefacts, and cleared
# at the top of every attempt so the fallback-model retry reads its OWN verdict
# rather than the first attempt's.
# shellcheck disable=SC2034  # consumed by run_agent/hook_was_live in publish-lib.sh
STOP_FAILURE_LOG="${PROJECT_DIR}/data/stop-failures.jsonl"

run_agent "$WORKTREE_DIR" "$AGENT_MODEL"

# A dead credential is not a failed generation. It deliberately does NOT write
# data/publish-blocked: that file is sticky by design and needs a human to clear
# it, whereas an expired credential un-breaks itself the moment the human logs
# in --- blocking would turn a one-step fix into two, and the failed unit
# already carries the alert.
if agent_auth_failed; then
  RELOGIN="$(relogin_hint)"
  log "AGENT AUTH FAILURE --- the unattended agent could not authenticate. No work was attempted."
  log "  Fix: run: ${RELOGIN}, then let the next tick run."
  rescue_and_abort "failed-auth" "agent could not authenticate; a human must run: ${RELOGIN}" 3
fi

# Out of credits is a third thing again. Only when the agent produced nothing,
# though: a mid-run exhaustion leaves half a publish on press, and regenerating
# over the top of that is how two outputs end up claiming one DOI. Anything
# already staged --- a commit on press, a PDF in the handoff directory --- sends
# this straight to the abort below, where rescue_and_abort preserves it.
if credits_exhausted; then
  log "AGENT OUT OF CREDITS on model ${AGENT_MODEL}."
  if [ "$(git rev-parse "$PRESS_BRANCH")" = "$BASE_REF" ] && ! staged_anything "$PENDING_DIR"; then
    git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1
    # Order matters: the hard-exhaustion test reads the attempt's output, and
    # the switch it guards overwrites the profile that test would classify by.
    if credits_hard_exhausted && switch_to_fallback_profile; then
      log "  the whole account balance is gone, so another model billed to it would refuse too;"
      log "  retrying this tick on the fallback profile ${AGENT_PROFILE} (model ${AGENT_MODEL})"
      run_agent "$WORKTREE_DIR" "$AGENT_MODEL"
    else
      log "  nothing was generated; retrying this tick on the fallback model ${AGENT_FALLBACK_MODEL}"
      run_agent "$WORKTREE_DIR" "$AGENT_FALLBACK_MODEL"
    fi
  else
    log "  the run had already staged work; not retrying (see the abort below)"
  fi
fi
# Re-read, because a retry overwrote $AGENT_OUT: this now asks whether the
# FALLBACK also refused. Both models out is a real stop --- the account has
# nothing left to generate with, every later tick dies identically, and the
# failed unit is what puts that in front of a human. Like the auth check it does
# not write data/publish-blocked: a limit window un-breaks itself, and blocking
# would turn a wait into a two-step fix.
if credits_exhausted; then
  log "AGENT OUT OF CREDITS --- the retry on ${AGENT_PROFILE}/${AGENT_MODEL} refused too; no output was generated."
  log "  Fix: wait for the usage window to reset, or point SLOPU_AGENT_PROFILE / SLOPU_AGENT_MODEL"
  log "  at a route that still has credits."
  rescue_and_abort "out-of-credits" "no usage credits on ${AGENT_PROFILE}/${AGENT_MODEL} or its fallback; wait for the reset or set SLOPU_AGENT_PROFILE" 5
fi

if [ "$AGENT_STATUS" -ne 0 ]; then
  log "publish agent failed with status ${AGENT_STATUS} (continuing --- the push below still redeploys the last validated state)"
fi

# --- Post-run residue in the worktree is a crashed generation's leftovers;
# nothing human lives there, so it needs no stash --- the next run's
# reset+clean clears it. Log it for the record.
RESIDUE="$(git -C "$WORKTREE_DIR" status --porcelain)"
if [ -n "$RESIDUE" ]; then
  log "post-run residue in press worktree (next run's reset/clean clears it):"
  echo "$RESIDUE" >> "$LOG_FILE"
fi

if ! validate_commits "$BASE_REF" "$PRESS_BRANCH"; then
  rescue_and_abort "validation-failure" "$VALIDATION_ERROR"
fi

# --- Upload this tick's PDFs to the bucket, BEFORE the push. Output PDFs are
# served from pdf.slop.university, not from the Pages artifact (they were its
# largest and only unbounded category, and being committed they grew .git at the
# same rate --- see website/src/lib/pdfs.ts). The agent stages them into
# gitignored data/pending-uploads/ and never uploads: same trust split as the
# social post, the agent composes and the wrapper publishes.
rescue_stray_staging "$PENDING_DIR" "$WORKTREE_DIR" "$PROJECT_DIR"

shopt -s nullglob
PENDING_PDFS=("$PENDING_DIR"/*.pdf)
shopt -u nullglob

if ! check_pairing "$BASE_REF" "$PRESS_BRANCH" "$PENDING_DIR"; then
  if [ -n "$MISSING_IMGS" ]; then
    log "VALIDATION FAILURE: new entry with images missing from ${PENDING_DIR}/img:"
    printf '%s' "$MISSING_IMGS" >> "$LOG_FILE"
    rescue_and_abort "validation-failure" "new entry with no images staged in data/pending-uploads/img/"
  fi
  log "VALIDATION FAILURE: new outputs entry with no PDF staged in ${PENDING_DIR}:"
  printf '%s' "$MISSING_PDFS" >> "$LOG_FILE"
  # Say WHERE it went, not just that it is absent. The first version of this
  # check reported only the missing name, and the PDFs turned out to be landing
  # in website/data/pending-uploads/ --- the agent had resolved a relative path
  # against website/. That cost a hunt through the worktree to work out; this
  # turns the same failure into one line of log.
  STRAYS="$(find "$WORKTREE_DIR" -name '*.pdf' -newermt '-3 hours' \
    -not -path "${WORKTREE_DIR}/output/pdf/*" -not -path "${PENDING_DIR}/*" 2>/dev/null | head -20)"
  if [ -n "$STRAYS" ]; then
    log "  ...but these recent PDFs exist elsewhere in the worktree (mislanded staging path?):"
    printf '%s\n' "$STRAYS" >> "$LOG_FILE"
  fi
  rescue_and_abort "validation-failure" "new outputs entry with no PDF staged in data/pending-uploads/"
fi

# Generation can take twenty minutes or more. A human push during that window
# used to be noticed only after the PDFs had been uploaded, producing an orphan
# object and a rescue branch. Refresh the remote immediately before the upload
# and require its current main tip to be contained in press. A fetch failure is
# also a stop: without a current remote view this guard cannot make its claim.
log "=== pre-upload remote race check at $(date -Iseconds) ==="
if ! git fetch origin >> "$LOG_FILE" 2>&1; then
  log "REMOTE RACE GUARD: fetch failed; refusing to upload or push"
  rescue_and_abort "failed-fetch" "pre-upload fetch of origin failed; refused to upload or push"
fi
if ! git merge-base --is-ancestor origin/main "$PRESS_BRANCH"; then
  log "REMOTE RACE GUARD: origin/main advanced outside press during generation; refusing to upload or push"
  rescue_and_abort "remote-race" "origin/main advanced outside press during generation"
fi

if [ ${#PENDING_PDFS[@]} -gt 0 ] && bucket_upload_allowed; then
  log "=== uploading ${#PENDING_PDFS[@]} PDF(s) to the bucket at $(date -Iseconds) ==="
  if "${PROJECT_DIR}/ops/bucket-sync.py" upload "${PENDING_PDFS[@]}" >> "$LOG_FILE" 2>&1; then
    log "uploaded PDFs; retaining local copies until the git push succeeds"
  else
    log "BUCKET UPLOAD FAILED --- refusing to push an entry whose PDF is not served"
    rescue_and_abort "failed-upload" "bucket upload failed; the entry's PDF would not be served"
  fi
else
  log "no PDFs staged for upload this run"
fi

if [ -d "${PENDING_DIR}/img" ] && bucket_upload_allowed; then
  log "=== uploading the staged image tree to the img bucket at $(date -Iseconds) ==="
  if "${PROJECT_DIR}/ops/bucket-sync.py" upload --target img "${PENDING_DIR}/img" >> "$LOG_FILE" 2>&1; then
    log "uploaded images; retaining local copies until the git push succeeds"
  else
    log "IMG BUCKET UPLOAD FAILED --- refusing to push an entry whose images are not served"
    rescue_and_abort "failed-upload" "img bucket upload failed; the entry's images would not be served"
  fi
else
  log "no images staged for upload this run"
fi

# Push press to main on origin (the documented per-repo exception to the global
# manual-push rule, like the aps tracker's). When base was local main, any
# unpushed human commits ride along --- same semantics as the old
# shared-checkout push. Also redeploys prior validated work after a
# failed-generation run. Then fast-forward the human checkout's main when git
# allows it; a dirty checkout that can't take the update just stays behind
# origin until the human pulls (the next run bases on origin/main regardless).
log "=== push at $(date -Iseconds) ==="
if git push origin "${PRESS_BRANCH}:main" >> "$LOG_FILE" 2>&1; then
  if [ ${#PENDING_PDFS[@]} -gt 0 ]; then
    rm -f "${PENDING_PDFS[@]}"
    log "push succeeded; cleared uploaded PDFs from data/pending-uploads/"
  fi
  if [ -d "${PENDING_DIR}/img" ]; then
    rm -rf "${PENDING_DIR}/img"
    log "push succeeded; cleared uploaded images from data/pending-uploads/img/"
  fi
  if git merge --ff-only "$PRESS_BRANCH" >> "$LOG_FILE" 2>&1; then
    log "fast-forwarded local main to press"
  else
    log "NOTE: local main not fast-forwarded (dirty or diverged checkout); pull when convenient"
  fi
else
  log "push failed after the remote race check; preserving the commit and its PDF copies"
  rescue_and_abort "failed-push" "git push failed after the remote race check"
fi

flush_pending_post

log "=== run finished at $(date -Iseconds) ==="

# Name what the tick actually achieved. A run that pushed nothing new because
# the agent fell over is not the same event as a clean publish, and until this
# existed the two were indistinguishable from `systemctl status`. A lost tick
# exits non-zero even though the push itself succeeded: the push only redeployed
# the previous state, and "the pipeline produced nothing this hour" is exactly
# the thing that needs to reach a human. If a single transient generation
# failure turns out to page too eagerly, this is the line to soften ---
# unit-oncall already dedups, so a one-off files one todo and the next
# successful tick clears it.
if [ -n "$AGENT_SHAS" ]; then
  # Report the commit subject, not the rolled preset. The preset is an INPUT,
  # and most rungs of the ladder never use it --- the tick that first published
  # under this line committed a grant award while the line read "preset=
  # brochure", which reads as a brochure nobody generated. The agent's own
  # subject is the only description guaranteed to match what landed.
  result "published" "$(echo "$AGENT_SHAS" | wc -l) agent commit(s) pushed: $(git log --format='%s' -1 "$(echo "$AGENT_SHAS" | head -1)")"
elif [ "$AGENT_STATUS" -ne 0 ]; then
  result "failed-generation" "agent exited ${AGENT_STATUS} and published nothing; rolled preset=${PRESET}; site redeployed unchanged"
  exit 4
elif [ "$POSTED" = "yes" ]; then
  # A 2G tick, and a complete one. It sits above 2A on the ladder, so the rolled
  # preset goes unused and the next tick draws again --- the absence of a commit
  # is the design, not a symptom.
  result "posted" "social post published; no commit, as a 2G tick stages a gitignored post; preset=${PRESET} unused"
else
  # A clean exit having done nothing is a LOST TICK, and it exits non-zero so it
  # reaches a human like one. The skill's own ladder says why: rung 5 ("nothing
  # is due") is "rare now that 2A is uncapped --- reachable only when the
  # generation itself aborts", so in practice this branch means the run gave up
  # somewhere and said so to nobody. On 2026-08-26 it meant the agent had hit a
  # contradiction in its instructions and stopped to ask the operator which way
  # to go; unattended, the question went to a log file.
  #
  # Exiting zero here was the dangerous part. systemd fires OnSuccess= on a zero
  # exit, which CLEARS any standing on-call todo --- so a pipeline stuck in this
  # state would not merely stay quiet, it would actively tidy away the alert
  # from the failure that preceded it. That is the sixteen-green-ticks bug with
  # a fresh coat of paint, and the unit's own comments were written about it.
  #
  # Deliberately NOT pattern-matched on "did the agent ask a question": there
  # are many ways to do nothing and only one thing worth reporting about all of
  # them, which is that the tick published nothing.
  result "no-op" "agent exited cleanly but committed nothing and posted nothing (a lost tick); preset=${PRESET}"
  exit 6
fi
