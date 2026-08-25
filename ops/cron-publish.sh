#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="/home/ben/projects/slop-university"
WORKTREE_DIR="/home/ben/projects/slop-university-press"
PRESS_BRANCH="press"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_DIR}/publish-$(date +%Y-%m-%d).log"
PENDING_DIR="${PROJECT_DIR}/data/pending-uploads"

mkdir -p "$LOG_DIR" "${PROJECT_DIR}/data" "$PENDING_DIR"

# Keep two months of run logs; they grow without bound otherwise.
find "$LOG_DIR" -name 'publish-*.log' -mtime +60 -delete

log() { echo "$*" >> "$LOG_FILE"; }

# --- The run's outcome, reported to the JOURNAL and not only to logs/.
#
# Everything here says what it is doing in $LOG_FILE and nothing on stdout, so
# `systemctl status` and `journalctl -u slop-publish` could only ever show
# systemd's own "Finished" --- which is precisely what they showed for sixteen
# consecutive ticks over 2026-08-03/04 while the agent died one second in on an
# expired OAuth token and published nothing. A tolerated agent failure and a
# real publish were the same green unit, and the only tell was a run lasting
# seven seconds instead of twenty minutes.
#
# So every exit path names an outcome and the EXIT trap prints one greppable
# line to stdout. The trap is what makes that total: a `set -e` abort, a
# TimeoutStartSec kill, or a later code path that forgets to call result() all
# still land a line, and it reads "crashed" rather than nothing at all. That
# line is also what the alert carries --- unit-oncall (wired to this unit via
# OnFailure=) quotes the journal tail into the todo, so the todo says which
# failure this was without anyone opening the log.
RUN_RESULT="crashed"
RUN_DETAIL="wrapper exited without recording an outcome"
result() {
  RUN_RESULT="$1"
  RUN_DETAIL="${2:-}"
}
on_exit() {
  local code=$?
  rm -f "${AGENT_OUT:-}"
  local line="RESULT=${RUN_RESULT} exit=${code} detail=${RUN_DETAIL}"
  echo "$line"
  log "$line"
}
trap on_exit EXIT

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
# split as "the agent commits, the wrapper pushes". Note what that split does
# and does not buy. It is STRUCTURAL for the action: the agent has no path to
# send a post, because only this wrapper calls the poster. It is NOT isolation
# of the credential --- mise exports SLOPU_TOKEN (and every other secret in the
# untracked [env] block) into this shell, and the agent runs as a child, so it
# inherits them. Anything relying on the unattended, feed-reading agent not
# HOLDING a secret needs `env -u` on its invocation below; today nothing does.
# data/ is canonical HERE: the press worktree's data/ is a symlink to
# this checkout's, so a post the agent stages over there lands where this
# wrapper (and the lock, and the block file) already look.
#
# POSTED records whether this run actually sent one, because otherwise the
# outcome line libels a good run: a 2G tick does its whole job without
# committing anything (the post is a gitignored artefact), so judging the run
# by its commits alone reports "committed nothing" for a tick that worked.
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

# Manual kill switch: a human can halt the pipeline by creating this file.
# (The wrapper itself no longer writes it --- the old writer existed for agent
# violations interleaved with human commits on main, which the press worktree
# makes impossible: the agent never commits where a human works.)
if [ -f "${PROJECT_DIR}/data/publish-blocked" ]; then
  log "PIPELINE BLOCKED --- data/publish-blocked exists; a human must triage and remove it:"
  cat "${PROJECT_DIR}/data/publish-blocked" >> "$LOG_FILE"
  log "=== run refused at $(date -Iseconds) ==="
  result "blocked" "data/publish-blocked exists; a human must triage and remove it"
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
    result "config-error" "${WORKTREE_DIR} exists but is not a registered worktree"
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
#
# `env -u` strips the credentials the agent must never hold. The
# compose/publish split above is structural for the ACTION --- only this
# wrapper calls the poster and the uploader --- but it was never isolation of
# the CREDENTIAL: mise exports the whole untracked [env] block into this shell
# and the agent runs as a child, so it inherited SLOPU_TOKEN and the bucket
# keys and could have used them directly, bypassing the split entirely. That
# gap matters because the agent reads attacker-influenceable input every run:
# the RSS sources and the Bluesky search in 2A are open channels, and a live
# installation taking topic suggestions from the room widens them. Stripping
# the tokens turns "the agent has no code path to post" into "the agent has no
# credential to post with", which survives an injected agent that stops
# following the skill. REPLICATE_API_TOKEN deliberately stays: image generation
# genuinely needs it, so bound that one with a spend cap on the key instead.
PRESET="$("${PROJECT_DIR}/ops/select-preset.sh")"
# The rest of a 2A run's enumerable axes --- finding-shape, setting,
# topic-sentence frame, title form, and the lead author (with them, the
# school). Drawn out here for the same reason the preset is: the skill used to
# infer each one by sampling the published corpus, which converges (the sample's
# newest entries read as exemplars) and correlates concurrent slots (two runs
# reading one corpus infer one dominant value and steer to one alternative).
# See ops/draw-axes.py. Multi-line by design; it goes into the prompt verbatim.
AXES="$("${PROJECT_DIR}/ops/draw-axes.py" --root "$WORKTREE_DIR")"
PUBLISHED_AT="$(date -Iseconds)"
log "=== selected preset: ${PRESET}; publishedAt: ${PUBLISHED_AT} ==="
log "=== drawn axes ==="
printf '%s\n' "$AXES" >> "$LOG_FILE"

# Which agent publishes. The run goes through the dotfiles dispatcher rather
# than a hardcoded CLI, so switching the press from one agent to another is a
# profile name, not an edit to the invocation below. grok-sub runs Grok Build
# on the SuperGrok subscription; claude-sub is the previous behaviour.
AGENT_PROFILE="${SLOPU_AGENT_PROFILE:-grok-sub}"
AGENT_RUN="${SLOPU_AGENT_RUN:-/home/ben/.dotfiles/bin/agent-run}"

# --- The model the unattended run generates on, pinned here rather than
# inherited. With no --model the runner takes its own default --- for Claude
# that is ~/.claude/settings.json, i.e. the INTERACTIVE default, whatever was
# last chosen with /model. The press
# transcripts show the pipeline riding that setting through four silent
# changes (sonnet to late July, opus to 7 Aug, sonnet to the 12th, opus to the
# 17th, fable after), not one of them a decision about this pipeline. On
# 2026-08-20 that bit: the global default had moved to Fable, the account's
# Fable credits ran out at 01:24, and every tick for the next seven hours died
# three seconds in on "You're out of usage credits" while opus, sonnet and
# haiku all still answered. Pinning makes the hourly run's model a property of
# the pipeline; the env overrides ride out a bad limit day without an edit.
#
# Model names are per-agent, so the pin has to be too: pointing a Grok profile
# at "sonnet" would fail every tick identically.
case "$AGENT_PROFILE" in
  grok-*) DEFAULT_MODEL="grok-4.6"; DEFAULT_FALLBACK_MODEL="grok-4.5" ;;
  *)      DEFAULT_MODEL="sonnet";   DEFAULT_FALLBACK_MODEL="haiku" ;;
esac
AGENT_MODEL="${SLOPU_AGENT_MODEL:-$DEFAULT_MODEL}"
AGENT_FALLBACK_MODEL="${SLOPU_AGENT_FALLBACK_MODEL:-$DEFAULT_FALLBACK_MODEL}"

# Captured rather than appended straight to the log, because the classifiers
# below have to read what the agent said. It lands in the log either way; the
# EXIT trap removes the temp copy on every path, including the aborts.
AGENT_OUT="$(mktemp)"
AGENT_STATUS=0

# Where the Grok StopFailure hook records how each turn ended. Grok classifies
# its own API failures into six tokens and hands them to a hook, which is a
# far better signal than grepping the agent's prose for phrasings lifted out of
# the binary's strings. See ops/grok-stop-failure-hook.py (and note it does NOT
# cover auth --- that fails before a session exists, so no hook fires; the
# regex below is still the only detector for it).
#
# A gitignored file under data/, like the other handoff artefacts, and cleared
# at the top of every attempt so the fallback-model retry reads its OWN verdict
# rather than the first attempt's.
STOP_FAILURE_LOG="${PROJECT_DIR}/data/stop-failures.jsonl"

run_agent() {
  local model="$1"
  AGENT_STATUS=0
  rm -f "$STOP_FAILURE_LOG"
  log "=== publish agent starting at $(date -Iseconds) (profile ${AGENT_PROFILE}, model ${model}) ==="
  (
    cd "$WORKTREE_DIR"
    GIT_AUTHOR_NAME="Slop University Press" \
    GIT_AUTHOR_EMAIL="press@slop.university" \
    SLOPU_PUBLIC_ONLY=1 \
    SLOPU_PUBLISHED_AT="$PUBLISHED_AT" \
    SLOPU_STOP_FAILURE_LOG="$STOP_FAILURE_LOG" \
    env -u SLOPU_TOKEN \
        -u SLOPU_S3_ACCESS_KEY_ID \
        -u SLOPU_S3_SECRET_ACCESS_KEY \
        -u SLOPU_S3_BUCKET \
        -u SLOPU_S3_ENDPOINT \
        -u SLOPU_IMG_BUCKET \
        -u SLOPU_IMG_ACCESS_KEY_ID \
        -u SLOPU_IMG_SECRET_ACCESS_KEY \
        -u SLOPU_IMG_ADMIN_ACCESS_KEY_ID \
        -u SLOPU_IMG_ADMIN_SECRET_ACCESS_KEY \
    "$AGENT_RUN" \
      --profile "$AGENT_PROFILE" \
      --model "$model" \
      --bypass-permissions \
      "/publish. For a 2A output, the wrapper selected preset: ${PRESET}. You must use that preset; do not roll a preset yourself. The wrapper also drew this run's axes; for a 2A output, compose the topic to FIT them, and do not infer, count or override any of them:
${AXES}
Record publishedAt from SLOPU_PUBLISHED_AT in its output entry."
  ) > "$AGENT_OUT" 2>&1 || AGENT_STATUS=$?
  cat "$AGENT_OUT" >> "$LOG_FILE"
  log "=== publish agent finished at $(date -Iseconds) (status ${AGENT_STATUS}) ==="
  # Verbatim, so the first real rate-limit carries its own evidence into the
  # log rather than only its classification.
  if [ -s "$STOP_FAILURE_LOG" ]; then
    log "grok turn-end records:"
    cat "$STOP_FAILURE_LOG" >> "$LOG_FILE"
  fi
}
run_agent "$AGENT_MODEL"

# A dead credential is not a failed generation, and the difference is the whole
# reason this check exists. A failed generation is transient --- a typst error,
# a flaky model call --- and the next tick genuinely may succeed, so tolerating
# it is right. An expired OAuth token is the opposite: the agent burned nothing
# and did nothing, and every later tick dies identically until a human runs
# /login. Treating the two alike is what lost sixteen consecutive ticks behind
# a green unit on 2026-08-03/04. So this one stops the run and fails the unit.
#
# It deliberately does NOT write data/publish-blocked. That file is sticky by
# design and needs a human to clear it, whereas an expired credential un-breaks
# itself the moment the human logs in --- blocking would turn a one-step fix
# into two, and the failed unit already carries the alert.
#
# Each agent says this its own way. Grok's two signatures were captured by
# running it with no credential ("Not signed in.") and with a mangled
# auth.json ("Unauthorized (401) ... Invalid or expired credentials"); the
# Claude patterns are the originals, still live whenever the profile is a
# Claude one.
if grep -qiE 'failed to authenticate|oauth.*(expired|refresh)|invalid api key|please run /login|not logged in|not signed in|invalid or expired credentials|unauthorized \(401\)' "$AGENT_OUT"; then
  case "$AGENT_PROFILE" in
    grok-*) RELOGIN="grok login --device-auth (on weddle, redeeming the code in a browser elsewhere)" ;;
    *)      RELOGIN="claude /login" ;;
  esac
  log "AGENT AUTH FAILURE --- the unattended agent could not authenticate. No work was attempted."
  log "  Fix: run: ${RELOGIN}, then let the next tick run."
  rescue_and_abort "failed-auth" "agent could not authenticate; a human must run: ${RELOGIN}" 3
fi

# Out of usage credits is a third thing again --- not a dead credential (the
# login is fine) and not a failed generation (nothing was attempted). It is the
# account's limit for ONE model, which is exactly why the CLI's own advice is
# "switch to another model", so the tick's best move is to do that once rather
# than forfeit the hour. Only when the agent produced nothing, though: a
# mid-run exhaustion leaves half a publish on press, and regenerating over the
# top of that is how two outputs end up claiming one DOI. Anything already
# staged --- a commit on press, a PDF in the handoff directory --- sends this
# straight to the abort below, where rescue_and_abort preserves it.

# Two detectors, and which one speaks depends on what the run actually had
# available.
#
# The hook is authoritative when it ran: grok classified the failure itself and
# said so in a field, so there is nothing to pattern-match. The regex survives
# for the two cases the hook cannot serve --- a Claude profile (claude-sub has
# no such hook) and a Grok run where the hook did not load at all.
#
# That second case is why the hook also records a SessionEnd heartbeat. An
# absent StopFailure line means "no API error" if the hook was live and "I have
# no detector" if it was not, and those must not read alike; the heartbeat is
# what separates them. A silent fallback would be the same bug as the sixteen
# green ticks that published nothing, one layer down, so it also shouts.
hook_was_live() { [ -s "$STOP_FAILURE_LOG" ]; }

hook_saw_rate_limit() {
  # Matching a field this script's sibling writes, not prose xAI can reword ---
  # the contract is between ops/grok-stop-failure-hook.py and this line.
  # Capacity errors (503/529) also classify as rate_limit, which is why the
  # hook records errorDetails verbatim: the retry below is the right response
  # to both, and the log is what will eventually let the two be told apart.
  grep -qE '"error": *"rate_limit"' "$STOP_FAILURE_LOG" 2>/dev/null
}

credits_exhausted_by_regex() {
  # "usage limit reached" happens to be common to both agents; the rest of
  # Grok's phrasings ("out of credits", "usage balance exhausted", "over your
  # spending limit") come from the strings in the grok binary itself.
  grep -qiE "out of usage credits|usage limit reached|exceeded your [a-z ]*(usage|rate) limit|out of credits|usage balance exhausted|spending limit" "$AGENT_OUT"
}

credits_exhausted() {
  case "$AGENT_PROFILE" in
    grok-*)
      if hook_was_live; then
        hook_saw_rate_limit
      else
        log "WARNING: the Grok StopFailure hook left no record (not even a SessionEnd heartbeat)."
        log "  Falling back to stdout matching. Check that ~/.grok/hooks/slopu-stop-failure.json"
        log "  resolves to ops/grok-hooks/slopu-stop-failure.json and that the script is executable."
        credits_exhausted_by_regex
      fi
      ;;
    *) credits_exhausted_by_regex ;;
  esac
}
if credits_exhausted; then
  log "AGENT OUT OF CREDITS on model ${AGENT_MODEL}."
  if [ "$(git rev-parse "$PRESS_BRANCH")" = "$BASE_REF" ] && [ -z "$(ls -A "$PENDING_DIR" 2>/dev/null)" ]; then
    log "  nothing was generated; retrying this tick on the fallback model ${AGENT_FALLBACK_MODEL}"
    git -C "$WORKTREE_DIR" clean -fd >> "$LOG_FILE" 2>&1
    run_agent "$AGENT_FALLBACK_MODEL"
  else
    log "  the run had already staged work; not retrying (see the abort below)"
  fi
fi
# Re-read, because a retry overwrote $AGENT_OUT: this now asks whether the
# FALLBACK also refused. Both models out is a real stop --- the account has
# nothing left to generate with, every later tick dies identically, and the
# failed unit is what puts that in front of a human. Like the auth check it
# does not write data/publish-blocked: a limit window un-breaks itself, and
# blocking would turn a wait into a two-step fix.
if credits_exhausted; then
  log "AGENT OUT OF CREDITS --- ${AGENT_MODEL} and the fallback ${AGENT_FALLBACK_MODEL} both refused; no output was generated."
  log "  Fix: wait for the usage window to reset, or point SLOPU_AGENT_MODEL at a model that still has credits."
  rescue_and_abort "out-of-credits" "no usage credits for ${AGENT_MODEL} or fallback ${AGENT_FALLBACK_MODEL}; wait for the reset or set SLOPU_AGENT_MODEL" 5
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

# --- Validate: every file touched by an AGENT-authored commit must fall inside
# the allowlist AND outside the denylist, and its diff must be free of
# private-brand markers. This is the mechanical enforcement of
# website/CLAUDE.md's hard floors: workflows, CNAME, robots.txt, site-config,
# and doctrine files can never land via the unattended path, no matter what the
# agent was talked into. The allowlist covers the gap-driven tick's whole
# surface: research outputs (news + outputs, plus each output's
# pipeline-optimised thumbnail and hero under
# src/assets/{outputs/thumbs,heroes/outputs}), grant awards (content/grants/
# --- but NOT canon/grants.yml: the tick awards from existing schemes only;
# adding a scheme is a human action), the heroes of the news posts that
# announce no output (grant awards and institutional notices, under
# src/assets/heroes/news/), grown pages, and the canon it edits (roster,
# schools, headshots, and canon/heroes for headshot-derived profile heroes).
# canon/burnt-shapes.yml is deliberately NOT here any more: it was the ledger
# the 2A dedup appended to, and since the finding-shape became a draw
# (ops/draw-axes.py) it is a static exclusion list the wrapper reads and no run
# writes. That removed 2A's only shared-file write.
# Note the tick may only touch heroes UNDER outputs/ and news/ --- the
# hand-built index and homepage heroes elsewhere in src/assets/heroes are
# deliberately excluded. The denylist carves the one out-of-fiction page
# (colophon) back out of the otherwise-allowed pages/ dir, and likewise the
# Vice-Chancellor: canon/leadership.yml is already outside the allowlist, but
# his portrait and profile hero sit INSIDE the allowlisted canon/headshots/ and
# canon/heroes/ trees, and they are the one likeness in the project worked from
# a real person's photographs. The tick never regenerates them.
ALLOWLIST_RE='^(website/src/content/(news|outputs|pages|grants)/|canon/(roster\.yml|schools\.yml|headshots/|heroes/))'
DENYLIST_RE='(^|/)colophon\.md$|^canon/leadership\.yml$|(^|/)ben-swift\.(jpg|avif)$'
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
  rescue_and_abort "validation-failure" "non-agent commit(s) on press"
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
  rescue_and_abort "validation-failure" "agent commit(s) outside the allowlist, in the denylist, or tripping the private-brand firewall"
fi

if [ -n "$AGENT_SHAS" ]; then
  log "validated $(echo "$AGENT_SHAS" | wc -l) agent commit(s) against allowlist + firewall"
else
  log "no agent commits this run"
fi

# --- Upload this tick's PDFs to the bucket, BEFORE the push. Output PDFs are
# served from pdf.slop.university, not from the Pages artifact (they were its
# largest and only unbounded category, and being committed they grew .git at the
# same rate --- see website/src/lib/pdfs.ts). The agent stages them into
# gitignored data/pending-uploads/ and never uploads: same trust split as the
# social post, the agent composes and the wrapper publishes.
#
# Ordering is the whole point. The push is what makes the outputs entry live,
# and the entry's PDF URL is derived from its id --- so an entry that shipped
# before its bytes did would be a live 404. Upload first, but only after a fresh
# fetch proves the remote tip is still contained in the candidate commit. Keep
# the local PDF copies until the push succeeds. If the remote moves during the
# short upload window, preserve the commit and PDFs together for human recovery
# rather than throwing the commit away and leaving untraceable bucket objects.
# Rescue a mislanded staging dir before looking. The agent resolves the staging
# path against whatever its cwd is, and it runs the site checks from website/ ---
# which put three ticks' PDFs in website/data/pending-uploads/ and threw away
# three complete generation runs. The skill now says to cd to the root, but a
# discarded run costs a full generation (typst, imagery, a Replicate spend) and
# an hour, whereas moving a file costs nothing. So: accept it, move it, and shout
# --- being strict here buys nothing and loses real work. The WARNING is the
# point; if it appears in the log the instruction has drifted again.
shopt -s nullglob
for stray_dir in "${WORKTREE_DIR}"/*/data/pending-uploads "${PROJECT_DIR}"/*/data/pending-uploads; do
  strays=("$stray_dir"/*.pdf)
  if [ ${#strays[@]} -gt 0 ]; then
    log "WARNING: ${#strays[@]} PDF(s) staged in the WRONG dir (${stray_dir}); moving to ${PENDING_DIR}"
    mv -n "${strays[@]}" "$PENDING_DIR"/ >> "$LOG_FILE" 2>&1 || log "WARNING: could not move strays out of ${stray_dir}"
  fi
  # The image tree mislands the same way the PDFs used to (relative staging
  # path resolved against the wrong cwd); fold it into the real staging dir
  # without clobbering anything already there.
  if [ -d "${stray_dir}/img" ]; then
    log "WARNING: staged image tree in the WRONG dir (${stray_dir}/img); merging into ${PENDING_DIR}/img"
    mkdir -p "${PENDING_DIR}/img"
    cp -an "${stray_dir}/img/." "${PENDING_DIR}/img/" >> "$LOG_FILE" 2>&1 \
      && rm -rf "${stray_dir}/img" \
      || log "WARNING: could not merge strays out of ${stray_dir}/img"
  fi
  rmdir -p --ignore-fail-on-non-empty "$stray_dir" 2>/dev/null || true
done

PENDING_PDFS=("$PENDING_DIR"/*.pdf)
shopt -u nullglob

# An empty staging dir is normal --- only a 2A run publishes an output; some
# actions stage nothing. What must never happen is a NEW entry without its
# bytes, so check the pairing directly rather than inferring the action. A dark
# render is required exactly when the entry flags one. For images the check is
# category presence (>=1 rung per family + the og card), not rung-exactness ---
# the encoder owns the rung list; the wrapper owns the pairing invariant.
MISSING_PDFS=""
MISSING_IMGS=""
for f in $(git diff --name-only --diff-filter=A "$BASE_REF" "$PRESS_BRANCH" -- 'website/src/content/outputs/*.yml'); do
  id="$(basename "$f" .yml)"
  [ -f "${PENDING_DIR}/${id}.pdf" ] || MISSING_PDFS="${MISSING_PDFS}  ${id}.pdf"$'\n'
  if git show "${PRESS_BRANCH}:${f}" | grep -qE '^pdfDark: *true'; then
    [ -f "${PENDING_DIR}/${id}-dark.pdf" ] || MISSING_PDFS="${MISSING_PDFS}  ${id}-dark.pdf"$'\n'
  fi
  compgen -G "${PENDING_DIR}/img/thumbs/${id}-*.avif" > /dev/null \
    || MISSING_IMGS="${MISSING_IMGS}  img/thumbs/${id}-*.avif"$'\n'
  compgen -G "${PENDING_DIR}/img/heroes/outputs/${id}-*.avif" > /dev/null \
    || MISSING_IMGS="${MISSING_IMGS}  img/heroes/outputs/${id}-*.avif"$'\n'
  [ -f "${PENDING_DIR}/img/og/outputs/${id}.jpg" ] \
    || MISSING_IMGS="${MISSING_IMGS}  img/og/outputs/${id}.jpg"$'\n'
done

# A new news post that announces no output carries its own hero (2H/2I); one
# that announces an output inherits that output's, staged above.
for f in $(git diff --name-only --diff-filter=A "$BASE_REF" "$PRESS_BRANCH" -- 'website/src/content/news/*.md' 'website/src/content/news/*.mdx'); do
  id="$(basename "$f")"; id="${id%.*}"
  if ! git show "${PRESS_BRANCH}:${f}" | grep -qE '^output:'; then
    compgen -G "${PENDING_DIR}/img/heroes/news/${id}-*.avif" > /dev/null \
      || MISSING_IMGS="${MISSING_IMGS}  img/heroes/news/${id}-*.avif"$'\n'
    [ -f "${PENDING_DIR}/img/og/news/${id}.jpg" ] \
      || MISSING_IMGS="${MISSING_IMGS}  img/og/news/${id}.jpg"$'\n'
  fi
done

if [ -n "$MISSING_IMGS" ]; then
  log "VALIDATION FAILURE: new entry with images missing from ${PENDING_DIR}/img:"
  printf '%s' "$MISSING_IMGS" >> "$LOG_FILE"
  rescue_and_abort "validation-failure" "new entry with no images staged in data/pending-uploads/img/"
fi

if [ -n "$MISSING_PDFS" ]; then
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

if [ ${#PENDING_PDFS[@]} -gt 0 ]; then
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

if [ -d "${PENDING_DIR}/img" ]; then
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

# Push press to main on origin (the documented per-repo exception to the
# global manual-push rule, like the aps tracker's). When base was local main,
# any unpushed human commits ride along --- same semantics as the old
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
# exits non-zero even though the push itself succeeded: the push only
# redeployed the previous state, and "the pipeline produced nothing this hour"
# is exactly the thing that needs to reach a human. If a single transient
# generation failure turns out to page too eagerly, this is the line to soften
# --- unit-oncall already dedups, so a one-off files one todo and the next
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
  # A 2G tick, and a complete one. It sits above 2A on the ladder, so the
  # rolled preset goes unused and the next tick draws again --- the absence of
  # a commit is the design, not a symptom.
  result "posted" "social post published; no commit, as a 2G tick stages a gitignored post; preset=${PRESET} unused"
else
  result "no-op" "agent exited cleanly, committed nothing and posted nothing; preset=${PRESET}"
fi
