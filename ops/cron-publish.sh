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
  if [ ${#pdfs[@]} -eq 0 ]; then
    return
  fi

  rescue_dir="${PROJECT_DIR}/data/publish-rescue/${ts}"
  mkdir -p "$rescue_dir"
  mv "${pdfs[@]}" "$rescue_dir"/
  log "preserved ${#pdfs[@]} staged PDF(s) in ${rescue_dir}"
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
PUBLISHED_AT="$(date -Iseconds)"
log "=== selected preset: ${PRESET}; publishedAt: ${PUBLISHED_AT} ==="
# Captured rather than appended straight to the log, because the classifier
# below has to read what the agent said. It lands in the log either way; the
# EXIT trap removes the temp copy on every path, including the aborts.
AGENT_OUT="$(mktemp)"
AGENT_STATUS=0
(
  cd "$WORKTREE_DIR"
  GIT_AUTHOR_NAME="Slop University Press" \
  GIT_AUTHOR_EMAIL="press@slop.university" \
  SLOPU_PUBLIC_ONLY=1 \
  SLOPU_PUBLISHED_AT="$PUBLISHED_AT" \
  env -u SLOPU_TOKEN \
      -u SLOPU_S3_ACCESS_KEY_ID \
      -u SLOPU_S3_SECRET_ACCESS_KEY \
      -u SLOPU_S3_BUCKET \
      -u SLOPU_S3_ENDPOINT \
  /home/ben/.local/bin/claude \
    --dangerously-skip-permissions \
    -p "/publish. For a 2A output, the wrapper selected preset: ${PRESET}. You must use that preset; do not roll a preset yourself. Record publishedAt from SLOPU_PUBLISHED_AT in its output entry."
) > "$AGENT_OUT" 2>&1 || AGENT_STATUS=$?
cat "$AGENT_OUT" >> "$LOG_FILE"

log "=== publish agent finished at $(date -Iseconds) (status ${AGENT_STATUS}) ==="

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
if grep -qiE 'failed to authenticate|oauth.*(expired|refresh)|invalid api key|please run /login|not logged in' "$AGENT_OUT"; then
  log "AGENT AUTH FAILURE --- the unattended agent could not authenticate. No work was attempted."
  log "  Fix: run \`claude\` interactively as ben, complete /login, and let the next tick run."
  rescue_and_abort "failed-auth" "agent could not authenticate; a human must run: claude /login" 3
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
# Note the tick may only touch heroes UNDER outputs/ and news/ --- the
# hand-built index and homepage heroes elsewhere in src/assets/heroes are
# deliberately excluded. The denylist carves the one out-of-fiction page
# (colophon) back out of the otherwise-allowed pages/ dir.
ALLOWLIST_RE='^(website/src/content/(news|outputs|pages|grants)/|website/src/assets/(outputs/thumbs|heroes/(outputs|news))/|canon/(roster\.yml|schools\.yml|headshots/|heroes/))'
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
    rmdir -p --ignore-fail-on-non-empty "$stray_dir" 2>/dev/null || true
  fi
done

PENDING_PDFS=("$PENDING_DIR"/*.pdf)
shopt -u nullglob

# An empty staging dir is normal --- only a 2A run publishes an output; the
# canon and news actions stage nothing. What must never happen is a NEW outputs
# entry without its bytes, so check that pairing directly rather than inferring
# the action. A dark render is required exactly when the entry flags one.
MISSING_PDFS=""
for f in $(git diff --name-only --diff-filter=A "$BASE_REF" "$PRESS_BRANCH" -- 'website/src/content/outputs/*.yml'); do
  id="$(basename "$f" .yml)"
  [ -f "${PENDING_DIR}/${id}.pdf" ] || MISSING_PDFS="${MISSING_PDFS}  ${id}.pdf"$'\n'
  if git show "${PRESS_BRANCH}:${f}" | grep -qE '^pdfDark: *true'; then
    [ -f "${PENDING_DIR}/${id}-dark.pdf" ] || MISSING_PDFS="${MISSING_PDFS}  ${id}-dark.pdf"$'\n'
  fi
done

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
  result "published" "$(echo "$AGENT_SHAS" | wc -l) agent commit(s) validated and pushed; preset=${PRESET}"
elif [ "$AGENT_STATUS" -ne 0 ]; then
  result "failed-generation" "agent exited ${AGENT_STATUS} and published nothing; preset=${PRESET}; site redeployed unchanged"
  exit 4
elif [ "$POSTED" = "yes" ]; then
  # A 2G tick, and a complete one. It sits above 2A on the ladder, so the
  # rolled preset goes unused and the next tick draws again --- the absence of
  # a commit is the design, not a symptom.
  result "posted" "social post published; no commit, as a 2G tick stages a gitignored post; preset=${PRESET} unused"
else
  result "no-op" "agent exited cleanly, committed nothing and posted nothing; preset=${PRESET}"
fi
