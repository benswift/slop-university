#!/usr/bin/env bash
# shellcheck shell=bash
# shellcheck disable=SC2034  # this is a library: callers consume these globals
# Shared machinery for the publish pipeline. Sourced, never executed.
#
# Three entry points use this: ops/publish-generate.sh (a concurrent generator
# slot), ops/publish-land.sh (the single serial lander) and ops/land.sh (the
# hand lander). They differ in what they orchestrate, not in what the
# safety-critical steps mean --- so base selection, commit validation, the
# entry-to-asset pairing check, the upload-then-push guard and the
# agent-failure classifiers live here, in one copy, and every caller gets the
# same answer.
#
# These functions read and write the caller's globals rather than taking every
# input as a parameter; each documents the globals it expects and sets.

PROJECT_DIR="${PROJECT_DIR:-/home/ben/projects/slop-university}"
LOG_DIR="${PROJECT_DIR}/logs"

# The roster's merge driver (.gitattributes names it; ops/merge-roster.py says
# why it exists), defined in the environment so every git the pipeline runs has
# it without anything being written to a config file.
export GIT_CONFIG_COUNT=1
export GIT_CONFIG_KEY_0="merge.roster.driver"
export GIT_CONFIG_VALUE_0="${PROJECT_DIR}/ops/merge-roster.py %O %A %B"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/publish-$(date +%Y-%m-%d).log}"

# Where generated PDFs and images wait to be uploaded. Each run owns a
# subdirectory (data/pending-uploads/<run-id>/), so two slots staging at once
# cannot see each other's files.
PENDING_ROOT="${PROJECT_DIR}/data/pending-uploads"

# The generate/land handoff: one marker file per completed candidate, written
# last so its existence means "this candidate is whole". See publish-land.sh.
CANDIDATE_DIR="${PROJECT_DIR}/data/candidates"

log() { echo "$*" >> "$LOG_FILE"; }

# --- Is this a throwaway fixture rather than the real checkout?
#
# The pipeline can be exercised end-to-end against a scratch clone by setting
# SLOPU_PROJECT_DIR. Git is safe under that: a clone has its own origin, so a
# push can only reach the fixture's own bare repo. The BUCKETS are not --- the
# credentials come from the mise env block and address one global bucket, so an
# upload from a fixture would write junk objects into the live image tree. A
# fixture run does everything except touch shared external infrastructure.
IS_FIXTURE=0
[ -n "${SLOPU_PROJECT_DIR:-}" ] && [ "${SLOPU_PROJECT_DIR}" != "/home/ben/projects/slop-university" ] && IS_FIXTURE=1

# Returns 0 when the upload may proceed. Shouts rather than failing silently:
# a skipped upload in a fixture is correct, and a human reading the log must be
# able to see that the assets did not go anywhere.
bucket_upload_allowed() {
  if [ "$IS_FIXTURE" = 1 ]; then
    log "FIXTURE RUN (SLOPU_PROJECT_DIR=${SLOPU_PROJECT_DIR}): refusing to upload to the shared bucket."
    log "  The entry would 404 in production, which is exactly why this is not the real checkout."
    return 1
  fi
  return 0
}

# --- The staged social posts, one file per platform.
#
# The agent COMPOSES these gitignored working-tree files and the wrapper POSTS
# them --- the same trust split as "the agent commits, the wrapper pushes". A
# staged post references already-live site content, so it is valid to send
# whatever the run goes on to do, which is why each wrapper flushes from every
# exit path. One file per platform so each retries alone: a LinkedIn relay that
# is switched off must not hold back a Bluesky post, or double-post one. Each
# poster exits 0 on a sent or deduped post, and only then is its file removed.
#
# A retry only fixes a transient failure. A post the poster refuses on its
# content (over the cap, no text, malformed JSON) exits POSTER_REJECTED, and is
# moved to data/rejected-posts/ so the platform can stage its next post. Left in
# place it is refused every tick and holds the socials gate shut, while the runs
# report published. REJECTED_POSTS makes the run's outcome say so
# (publish_on_exit).
#
# Posting is shared external infrastructure, like the buckets, so a fixture
# never posts to Bluesky, and posts to LinkedIn only through the loopback stub
# named in SLOPU_SELFTEST_LINKEDIN_WEBHOOK. It is a separate variable because
# activate_mise re-exports the live webhook into every wrapper, fixture or not.
STAGED_POSTS=(
  "pending-post.json:post-to-bluesky.py"
  "pending-linkedin-post.json:post-to-linkedin.py"
)
POSTER_REJECTED=65
REJECTED_POSTS=""

# Returns 0 when any platform has a post staged.
staged_post_exists() {
  local pair
  for pair in "${STAGED_POSTS[@]}"; do
    [ -f "${PROJECT_DIR}/data/${pair%%:*}" ] && return 0
  done
  return 1
}

# Sets POSTED=yes when any platform posted.
flush_staged_posts() {
  local pair staged poster status quarantined
  local -a fixture_env
  for pair in "${STAGED_POSTS[@]}"; do
    staged="${pair%%:*}"
    poster="${pair##*:}"
    [ -f "${PROJECT_DIR}/data/${staged}" ] || continue
    fixture_env=()
    if [ "$IS_FIXTURE" = 1 ]; then
      if [ "$poster" != post-to-linkedin.py ] ||
          [[ "${SLOPU_SELFTEST_LINKEDIN_WEBHOOK:-}" != http://127.0.0.1:* ]]; then
        log "FIXTURE RUN: refusing to run ${poster} against a live account; data/${staged} stays staged"
        continue
      fi
      fixture_env=(SLOPU_LINKEDIN_WEBHOOK="$SLOPU_SELFTEST_LINKEDIN_WEBHOOK" SLOPU_LINKEDIN_WEBHOOK_KEY=selftest)
    fi
    log "=== posting data/${staged} at $(date -Iseconds) ==="
    status=0
    env "${fixture_env[@]}" uv run "${PROJECT_DIR}/ops/${poster}" "${PROJECT_DIR}/data/${staged}" >> "$LOG_FILE" 2>&1 || status=$?
    if [ "$status" = 0 ]; then
      rm -f "${PROJECT_DIR}/data/${staged}"
      POSTED="yes"
      log "posted and cleared data/${staged}"
    elif [ "$status" = "$POSTER_REJECTED" ]; then
      quarantined="data/rejected-posts/$(date +%Y%m%d-%H%M%S)-${staged}"
      mkdir -p "${PROJECT_DIR}/data/rejected-posts"
      mv "${PROJECT_DIR}/data/${staged}" "${PROJECT_DIR}/${quarantined}"
      REJECTED_POSTS="${REJECTED_POSTS:+${REJECTED_POSTS}, }${quarantined}"
      log "${poster} can never accept data/${staged}; moved it to ${quarantined}"
    else
      log "${poster} failed; leaving data/${staged} staged for retry"
    fi
  done
}

# --- The ATproto records (ops/sync-atproto.py says what they are and why the
# run is capped). Called after the push and the posts, so the post it refers to
# usually exists already. Fail-open: a failed sync never fails a landing, and
# the next landing's reconcile repairs it. $1 is the checkout that was pushed,
# which is the truth the records follow --- never a human checkout that may be
# behind or on another branch. A fixture never syncs: the account is live.
sync_atproto() {
  if [ "$IS_FIXTURE" = 1 ]; then
    log "FIXTURE RUN: refusing to sync ATproto records to the live account"
    return 0
  fi
  log "=== ATproto sync at $(date -Iseconds) ==="
  timeout 600 uv run "${PROJECT_DIR}/ops/sync-atproto.py" --root "$1" --limit 100 >> "$LOG_FILE" 2>&1 \
    || log "ATproto sync failed; the next landing repairs it"
}

# --- The run's outcome, reported to the JOURNAL and not only to logs/.
#
# Everything here logs to $LOG_FILE and nothing to stdout, so without this
# `systemctl status` would show only systemd's own "Finished", and a tolerated
# agent failure would look exactly like a real publish. Every exit path names an
# outcome, and the EXIT trap prints one greppable line to stdout. The trap is
# what makes that total: a `set -e` abort, a TimeoutStartSec kill, or a code
# path that forgets to call result() still lands a line, reading "crashed".
# unit-oncall (wired via OnFailure=) quotes that line into the todo.
RUN_RESULT="crashed"
RUN_DETAIL="wrapper exited without recording an outcome"
result() {
  RUN_RESULT="$1"
  RUN_DETAIL="${2:-}"
}

# Callers may define on_exit_cleanup() to add their own teardown; it runs first.
#
# A rejected post outranks a successful outcome and exits POSTER_REJECTED, since
# the run's own work is fine and only a human can fix the copy. A failed run
# keeps its own outcome and carries the rejection in its detail.
publish_on_exit() {
  local code=$?
  if declare -F on_exit_cleanup > /dev/null; then on_exit_cleanup || true; fi
  rm -f "${AGENT_OUT:-}"
  if [ -n "$REJECTED_POSTS" ]; then
    if [ "$code" = 0 ]; then
      RUN_DETAIL="unpostable social post quarantined in ${REJECTED_POSTS}; the run was ${RUN_RESULT}: ${RUN_DETAIL}"
      RUN_RESULT="rejected-post"
      code=$POSTER_REJECTED
    else
      RUN_DETAIL="${RUN_DETAIL}; also quarantined an unpostable social post in ${REJECTED_POSTS}"
    fi
  fi
  local line="RESULT=${RUN_RESULT} exit=${code} detail=${RUN_DETAIL}"
  echo "$line"
  log "$line"
  exit "$code"
}

install_exit_trap() { trap publish_on_exit EXIT; }

# Take <lockfile> non-blocking on fd 9, held for the rest of the process.
# Returns 1, having logged <message> and recorded a skipped-locked outcome with
# <detail>, when another run holds it.
take_lock() {
  exec 9> "$1"
  flock -n 9 && return 0
  log "$2"
  result "skipped-locked" "$3"
  return 1
}

# mise activates tool shims into PATH (node, pnpm, typst, etc.) and exports the
# untracked env block (REPLICATE_API_TOKEN and friends).
activate_mise() { eval "$(/home/ben/.local/bin/mise activate bash)"; }

# Keep two months of run logs; they grow without bound otherwise.
prune_logs() { find "$LOG_DIR" -name 'publish-*.log' -mtime +60 -delete; }

# Manual kill switch: a human halts the whole pipeline --- every generator and
# the lander --- by creating this file. Returns 0 when blocked.
pipeline_blocked() {
  [ -f "${PROJECT_DIR}/data/publish-blocked" ] || return 1
  log "PIPELINE BLOCKED --- data/publish-blocked exists; a human must triage and remove it:"
  cat "${PROJECT_DIR}/data/publish-blocked" >> "$LOG_FILE"
  return 0
}

# mise refuses config files it hasn't been told to trust; idempotent.
trust_mise_configs() {
  local dir="$1" f
  for f in "${dir}/mise.toml" "${dir}/website/mise.toml"; do
    [ -f "$f" ] && /home/ben/.local/bin/mise trust "$f" >> "$LOG_FILE" 2>&1 || true
  done
}

# --- A publish worktree. The agent never works in the human checkout: it gets
# a persistent worktree, reset to a committed state before every run. Three
# things fall out of this: a run never skips because a human is mid-edit in the
# checkout; the agent always generates against a COMMITTED, consistent state of
# the canon (never a half-edited roster); and the gitignored private surface
# (private/, CLAUDE.local.md, the top-level references/*.avif photos) simply
# does not exist over there --- braces on top of SLOPU_PUBLIC_ONLY's belt.
#
# Args: <worktree-dir> <branch> <base-committish>. Returns 1 if the path exists
# but is not a registered worktree --- refusing to touch it is the point.
ensure_worktree() {
  local dir="$1" branch="$2" base="$3"
  if ! git worktree list --porcelain | grep -qxF "worktree ${dir}"; then
    if [ -e "$dir" ]; then
      log "ERROR: ${dir} exists but is not a registered worktree; refusing to touch it"
      return 1
    fi
    git worktree add -B "$branch" "$dir" "$base" >> "$LOG_FILE" 2>&1
    log "created publish worktree at ${dir} on ${branch}"
  fi
  trust_mise_configs "$dir"
}

# Put <worktree-dir> on a fresh <branch> at <base>, discarding whatever a
# crashed run left. Persistent rather than recreated, so node_modules, the typst
# cache and the pnpm store survive between runs. -f so neither local changes
# nor untracked files in the way can make the checkout refuse. clean is
# deliberately not -x --- gitignored state survives; only untracked residue
# goes.
reset_worktree() {
  local dir="$1" branch="$2" base="$3"
  git -C "$dir" checkout -f -B "$branch" "$base" >> "$LOG_FILE" 2>&1
  git -C "$dir" clean -fd >> "$LOG_FILE" 2>&1
  link_data_dir "$dir"
}

# The data/ handoff symlink. data/ is canonical in the MAIN checkout --- every
# worktree's data/ points at it --- so the topic-claim lock, the staged social
# post and the pending-uploads tree are one set of files no matter which
# worktree wrote them. That shared view is what lets concurrent slots claim
# topics against each other. After any clean, so a mistaken removal is
# always repaired.
link_data_dir() {
  local dir="$1"
  [ -e "${dir}/data" ] || ln -s "${PROJECT_DIR}/data" "${dir}/data"
}

# The site checks need node_modules in THIS worktree; pnpm's shared store makes
# that hardlinks, not a second download. Returns non-zero on failure.
worktree_install() {
  local dir="$1"
  (cd "${dir}/website" && pnpm install --frozen-lockfile) >> "$LOG_FILE" 2>&1
}

# --- Base selection: build on the newest published state. Normally one of
# main / origin/main contains the other (a prior run pushed but couldn't
# fast-forward a dirty local checkout, or the human committed locally and the
# push will carry it). Genuine divergence means a human rebase is due --- the
# caller skips rather than guesses.
#
# Sets BASE_REF and BASE_NAME. Returns 1 on divergence. Fetches, so only the
# lander calls it: a generator never touches origin.
select_base() {
  git fetch origin >> "$LOG_FILE" 2>&1 || log "WARNING: git fetch failed; selecting base from local refs"
  if git merge-base --is-ancestor main origin/main; then
    BASE_REF="$(git rev-parse origin/main)"
    BASE_NAME="origin/main"
  elif git merge-base --is-ancestor origin/main main; then
    BASE_REF="$(git rev-parse main)"
    BASE_NAME="main"
  else
    log "main and origin/main have DIVERGED; a human must reconcile (rebase)."
    return 1
  fi
}

# --- Who may commit, and what they may touch.
#
# This is the mechanical enforcement of website/CLAUDE.md's hard floors:
# workflows, CNAME, robots.txt, site-config and doctrine files can never land
# via the unattended path, no matter what the agent was talked into. The
# allowlist covers the gap-driven tick's whole surface: research outputs (news +
# outputs), grant awards (content/grants/ --- but NOT canon/grants.yml: the tick
# awards from existing schemes only; adding a scheme is a human action), grown
# pages, and the canon it edits (roster, schools, headshots, and canon/heroes
# for headshot-derived profile heroes).
#
# The draw pools (canon/axes.yml, canon/subjects.tsv, canon/burnt-shapes.yml)
# are deliberately absent: they are static doctrine the wrapper reads
# (ops/draw-axes.py) and no run writes, which is what makes concurrent 2A slots
# touch genuinely disjoint files.
#
# The denylist carves the one out-of-fiction page (colophon) back out of the
# otherwise-allowed pages/ dir, and likewise the Vice-Chancellor:
# canon/leadership.yml is already outside the allowlist, but his portrait and
# profile hero sit INSIDE the allowlisted canon/headshots/ and canon/heroes/
# trees, and they are the one likeness in the project worked from a real
# person's photographs. The tick never regenerates them.
ALLOWLIST_RE='^(website/src/content/(news|outputs|pages|grants)/|canon/(roster\.yml|schools\.yml|headshots/|heroes/))'
DENYLIST_RE='(^|/)colophon\.md$|^canon/leadership\.yml$|(^|/)ben-swift\.(jpg|avif)$'
# The private-brand firewall: no agent commit may reference the ANU brand
# layer, the private preset overlay, or the non-redistributable top-level
# references/*.avif photos. (references/slop-style/ is fine and unmatched ---
# the pattern has no slash.) Belt to SLOPU_PUBLIC_ONLY's braces.
FIREWALL_RE='anu-typst-template|@local/anu|private/anu|lockup: *"anu|references/[a-z0-9_-]+\.avif'
AGENT_NAME="Slop University Press"
AGENT_EMAIL="press@slop.university"

# Validate every commit in <base>..<branch>. Sets AGENT_SHAS (the agent's own
# commits, for the caller's outcome line) and VALIDATION_ERROR (empty when
# clean). Returns 1 when anything failed, so a caller can `if ! validate...`.
#
# Nothing but the agent ever commits on a publish branch, so a foreign-authored
# commit there is itself a violation.
validate_commits() {
  local base="$1" branch="$2" sha files denied outside leaked detail foreign
  VALIDATION_ERROR=""
  AGENT_SHAS="$(git log --format='%H' --author="$AGENT_EMAIL" "${base}..${branch}")"
  if [ -n "$AGENT_SHAS" ]; then
    foreign="$(git log --format='%H' "${base}..${branch}" | grep -vxF "$AGENT_SHAS" || true)"
  else
    foreign="$(git log --format='%H' "${base}..${branch}")"
  fi

  if [ -n "$foreign" ]; then
    log "VALIDATION FAILURE: non-agent commit(s) in ${base}..${branch}:"
    # shellcheck disable=SC2086  # sha list is deliberately word-split
    git log --format='  %h %an %s' --no-walk $foreign >> "$LOG_FILE" 2>&1 || true
    VALIDATION_ERROR="non-agent commit(s) on the publish branch"
    return 1
  fi

  local violations=""
  for sha in $AGENT_SHAS; do
    files="$(git show --name-only --format= "$sha")"
    denied="$(echo "$files" | grep -E "$DENYLIST_RE" || true)"
    outside="$(echo "$files" | grep -Ev "$ALLOWLIST_RE" | grep -v '^$' || true)"
    leaked="$(git show "$sha" | grep -E "$FIREWALL_RE" || true)"
    if [ -n "$denied" ] || [ -n "$outside" ] || [ -n "$leaked" ]; then
      detail="$(printf '%s\n' "$denied" "$outside" "$leaked" | grep -v '^$')"
      violations="${violations}
commit ${sha}:
${detail}"
    fi
  done

  if [ -n "$violations" ]; then
    log "VALIDATION FAILURE: agent commit(s) violate the allowlist/denylist/firewall:"
    echo "$violations" >> "$LOG_FILE"
    VALIDATION_ERROR="agent commit(s) outside the allowlist, in the denylist, or tripping the private-brand firewall"
    return 1
  fi

  if [ -n "$AGENT_SHAS" ]; then
    log "validated $(echo "$AGENT_SHAS" | wc -l) agent commit(s) against allowlist + firewall"
  else
    log "no agent commits in ${base}..${branch}"
  fi
}

# --- Every new entry must ship with its bytes.
#
# An empty staging dir is normal --- only a 2A run publishes an output; some
# actions stage nothing. What must never happen is a NEW entry without its
# assets, so check the pairing directly rather than inferring the action. A dark
# render is required exactly when the entry flags one. For images the check is
# category presence (>=1 rung per family + the og card), not rung-exactness ---
# the encoder owns the rung list; this owns the pairing invariant.
#
# Args: <base> <branch> <pending-dir>. Sets MISSING_PDFS and MISSING_IMGS.
# Returns 1 if either is non-empty.
check_pairing() {
  local base="$1" branch="$2" pending="$3" f id
  MISSING_PDFS=""
  MISSING_IMGS=""

  for f in $(git diff --name-only --diff-filter=A "$base" "$branch" -- 'website/src/content/outputs/*.yml'); do
    id="$(basename "$f" .yml)"
    if git show "${branch}:${f}" | grep -qE '^preset: *video-'; then
      # A video output has no PDF: its encodes and covers, which its videos
      # entry names, stand in for one.
      for v in $(git show "${branch}:website/src/content/videos/${id}.yml" 2>/dev/null | grep -oE '[a-z0-9-]+-[0-9a-f]{10}\.(mp4|jpg)' || echo "videos/${id}.yml"); do
        [ -f "${pending}/${v}" ] || MISSING_PDFS="${MISSING_PDFS}  ${v}"$'\n'
      done
    else
      [ -f "${pending}/${id}.pdf" ] || MISSING_PDFS="${MISSING_PDFS}  ${id}.pdf"$'\n'
    fi
    if git show "${branch}:${f}" | grep -qE '^pdfDark: *true'; then
      [ -f "${pending}/${id}-dark.pdf" ] || MISSING_PDFS="${MISSING_PDFS}  ${id}-dark.pdf"$'\n'
    fi
    compgen -G "${pending}/img/thumbs/${id}-*.avif" > /dev/null \
      || MISSING_IMGS="${MISSING_IMGS}  img/thumbs/${id}-*.avif"$'\n'
    compgen -G "${pending}/img/heroes/outputs/${id}-*.avif" > /dev/null \
      || MISSING_IMGS="${MISSING_IMGS}  img/heroes/outputs/${id}-*.avif"$'\n'
    [ -f "${pending}/img/og/outputs/${id}.jpg" ] \
      || MISSING_IMGS="${MISSING_IMGS}  img/og/outputs/${id}.jpg"$'\n'
  done

  # A new news post that announces no output carries its own hero (2H/2I); one
  # that announces an output inherits that output's, staged above.
  for f in $(git diff --name-only --diff-filter=A "$base" "$branch" -- 'website/src/content/news/*.md' 'website/src/content/news/*.mdx'); do
    id="$(basename "$f")"; id="${id%.*}"
    if ! git show "${branch}:${f}" | grep -qE '^output:'; then
      compgen -G "${pending}/img/heroes/news/${id}-*.avif" > /dev/null \
        || MISSING_IMGS="${MISSING_IMGS}  img/heroes/news/${id}-*.avif"$'\n'
      [ -f "${pending}/img/og/news/${id}.jpg" ] \
        || MISSING_IMGS="${MISSING_IMGS}  img/og/news/${id}.jpg"$'\n'
    fi
  done

  [ -z "$MISSING_PDFS" ] && [ -z "$MISSING_IMGS" ]
}

# Reject the characteristic booklet/paper failure where the last paragraph or
# reference block spills onto a mostly empty content page. The page checker
# knows which page is content for each preset; posters retain their stricter
# one-page preset checks. Pairing runs first, so every path passed here exists.
#
# Args: <base> <branch> <pending-dir>. Sets QUALITY_ERROR.
check_output_quality() {
  local base="$1" branch="$2" pending="$3" f id preset detail
  QUALITY_ERROR=""

  for f in $(git diff --name-only --diff-filter=A "$base" "$branch" -- 'website/src/content/outputs/*.yml'); do
    id="$(basename "$f" .yml)"
    preset="$(git show "${branch}:${f}" | sed -n 's/^preset:[[:space:]]*//p' | head -1)"
    # a video's gate is its run's own review; it has no pages to check
    [[ "$preset" == video-* ]] && continue
    if ! detail="$("${PROJECT_DIR}/ops/check-output-quality.py" --preset "$preset" "${pending}/${id}.pdf" 2>&1)"; then
      log "QUALITY FAILURE for ${id}:"
      printf '%s\n' "$detail" >> "$LOG_FILE"
      QUALITY_ERROR="${id} has an orphaned or substantially underfilled final content page"
      return 1
    fi
    log "${detail}"
  done
  return 0
}

# Did the run stage any assets into <pending-dir>?
staged_anything() {
  local dir="$1"
  [ -n "$(ls -A "$dir" 2>/dev/null)" ]
}

# --- Rescue a mislanded staging dir before looking for its contents.
#
# The agent resolves the staging path against whatever its cwd is, and it runs
# the site checks from website/, so a relative path lands its PDFs in
# website/data/pending-uploads/. A discarded run costs a full generation and an
# hour, whereas moving a file costs nothing, so accept it, move it, and shout:
# if the WARNING appears in the log, the skill's instruction has drifted.
#
# Args: <destination-pending-dir> <worktree-dir>.
rescue_stray_staging() {
  local dest="$1" root="$2"
  local stray_dir strays
  mkdir -p "$dest"
  shopt -s nullglob
  for stray_dir in "${root}"/*/data/pending-uploads "${root}"/*/data/pending-uploads/*/; do
    [ -d "$stray_dir" ] || continue
    [ "${stray_dir%/}" = "${dest%/}" ] && continue
    strays=("$stray_dir"/*.pdf)
    if [ ${#strays[@]} -gt 0 ]; then
      log "WARNING: ${#strays[@]} PDF(s) staged in the WRONG dir (${stray_dir}); moving to ${dest}"
      mv -n "${strays[@]}" "$dest"/ >> "$LOG_FILE" 2>&1 || log "WARNING: could not move strays out of ${stray_dir}"
    fi
    if [ -d "${stray_dir}/img" ]; then
      log "WARNING: staged image tree in the WRONG dir (${stray_dir}/img); merging into ${dest}/img"
      mkdir -p "${dest}/img"
      if cp -an "${stray_dir}/img/." "${dest}/img/" >> "$LOG_FILE" 2>&1; then
        rm -rf "${stray_dir}/img"
      else
        log "WARNING: could not merge strays out of ${stray_dir}/img"
      fi
    fi
    rmdir -p --ignore-fail-on-non-empty "$stray_dir" 2>/dev/null || true
  done
  shopt -u nullglob
}

# --- Upload before push, and only once a fresh fetch proves the remote tip is
# still contained in what is about to be pushed.
#
# The push is what makes an entry live, and the entry's asset URLs derive from
# its id, so an entry that shipped before its bytes would be a live 404. Each
# caller keeps its local copies until the push succeeds.
#
# Args: <ref>. On failure records the outcome with result() and returns 1; the
# caller unwinds and exits 1.
guard_remote_race() {
  log "=== pre-upload remote race check at $(date -Iseconds) ==="
  if ! git fetch origin >> "$LOG_FILE" 2>&1; then
    log "REMOTE RACE GUARD: fetch failed; refusing to upload or push"
    result "failed-fetch" "pre-upload fetch of origin failed; refused to upload or push"
    return 1
  fi
  if ! git merge-base --is-ancestor origin/main "$1"; then
    log "REMOTE RACE GUARD: origin/main advanced during landing; refusing to upload or push"
    result "remote-race" "origin/main advanced during landing; pull and retry"
    return 1
  fi
}

# The files in <pending-dir> bound for the PDF bucket: the PDFs, or a video
# output's encodes and covers. Sets STAGED_FILES.
collect_staged_files() {
  shopt -s nullglob
  STAGED_FILES=("$1"/*.pdf "$1"/*.mp4 "$1"/*.jpg)
  shopt -u nullglob
}

# Upload STAGED_FILES to the PDF bucket and <pending-dir>/img to the img
# bucket. On failure records the outcome with result() and returns 1; the
# caller unwinds and exits 1.
upload_staged_assets() {
  local pending="$1"
  if [ ${#STAGED_FILES[@]} -gt 0 ] && bucket_upload_allowed; then
    log "=== uploading ${#STAGED_FILES[@]} file(s) to the bucket at $(date -Iseconds) ==="
    if ! "${PROJECT_DIR}/ops/bucket-sync.py" upload "${STAGED_FILES[@]}" >> "$LOG_FILE" 2>&1; then
      log "BUCKET UPLOAD FAILED --- refusing to push an entry whose PDF is not served"
      result "failed-upload" "bucket upload failed; the entry's PDF would not be served"
      return 1
    fi
    log "uploaded ${#STAGED_FILES[@]} file(s); retaining local copies until the push succeeds"
  else
    log "no PDFs staged"
  fi

  if [ -d "${pending}/img" ] && bucket_upload_allowed; then
    log "=== uploading the staged image tree to the img bucket at $(date -Iseconds) ==="
    if ! "${PROJECT_DIR}/ops/bucket-sync.py" upload --target img "${pending}/img" >> "$LOG_FILE" 2>&1; then
      log "IMG BUCKET UPLOAD FAILED --- refusing to push an entry whose images are not served"
      result "failed-upload" "img bucket upload failed; the entry's images would not be served"
      return 1
    fi
    log "uploaded images; retaining local copies until the push succeeds"
  else
    log "no images staged"
  fi
}

# --- The publish agent.
#
# It generates one action's worth of work, stages assets, and COMMITS --- it
# never pushes and never uploads. That trust boundary is the pipeline's spine:
# the agent composes, the wrapper publishes.

# Which agent publishes. The run goes through the dotfiles dispatcher rather
# than a hardcoded CLI, so switching the press from one agent to another is a
# profile name, not an edit to the invocation. claude-sub is the Claude
# subscription.
AGENT_PROFILE="${SLOPU_AGENT_PROFILE:-claude-sub}"
AGENT_RUN="${SLOPU_AGENT_RUN:-/home/ben/.dotfiles/bin/agent-run}"

# --- The model, pinned here rather than inherited. With no --model the runner
# takes its own default --- for Claude that is ~/.claude/settings.json, the
# INTERACTIVE default, whatever was last chosen with /model --- so an
# unrelated /model change (or that model's credits running out) would silently
# move or stop the press. The env overrides ride out a bad limit day without
# an edit.
#
# The brief (skills/from-preset/genre.md) leaves the piece to the model's
# judgement, so the model is where the quality comes from.
AGENT_MODEL="${SLOPU_AGENT_MODEL:-opus}"
AGENT_FALLBACK_MODEL="${SLOPU_AGENT_FALLBACK_MODEL:-sonnet}"

# --- Reasoning effort, pinned for the same reason the model is. Effort is the
# cheapest lever on a run's token bill, so it is a property of the pipeline,
# tunable per route without an edit. Only the Claude runner takes the flag.
AGENT_EFFORT="${SLOPU_AGENT_EFFORT:-high}"

# Draw this run's inputs. The rung (ops/assess-ladder.py), the preset
# (ops/select-preset.sh) and a 2A run's givens (ops/draw-axes.py: subject,
# tradition, lead author) are all chosen OUTSIDE the model, so a run receives
# one unambiguous selection instead of choosing. A model anchors on whatever
# the prompt names and converges on its favourites, and it correlates
# concurrent slots, which is precisely what a second generator must not do.
#
# Args: <worktree-dir> (the corpus the draws read) [<mode>], where mode is
# "2a-only" (slots 2+: the assessor returns 2A unread) or "thesis" (rung 2T,
# never assessed). Sets ACTION, ACTION_REASON, ACTION_PARAMS, PRESET, AXES and
# PUBLISHED_AT.
draw_run_inputs() {
  local worktree="$1" mode="${2:-}"
  if [ "$mode" = "thesis" ]; then
    # The rung is fixed by the human who started the run, the preset is the
    # thesis's own, and the only inputs drawn are the fiction (setting, school,
    # supervisors).
    ACTION="2T"
    ACTION_REASON="a doctoral thesis, run by hand; never assessed and never timed"
    ACTION_PARAMS="{}"
    PRESET="thesis"
    AXES="$("${PROJECT_DIR}/ops/draw-axes.py" --root "$worktree" --thesis)"
    PUBLISHED_AT="$(date -Iseconds)"
    log "=== assessed action: ${ACTION} --- ${ACTION_REASON} ==="
    log "=== selected preset: ${PRESET}; publishedAt: ${PUBLISHED_AT} ==="
    log "=== drawn fiction ==="
    printf '%s\n' "$AXES" >> "$LOG_FILE"
    return 0
  fi
  local assess_args=(--root "$worktree" --json)
  [ "$mode" = "2a-only" ] && assess_args+=(--only-2a)
  [ -n "${SLOPU_ASSESS_NO_NETWORK:-}" ] && assess_args+=(--no-network)
  ACTION_JSON="$("${PROJECT_DIR}/ops/assess-ladder.py" "${assess_args[@]}")"
  ACTION="$(printf '%s' "$ACTION_JSON" | jq -r .rung)"
  ACTION_REASON="$(printf '%s' "$ACTION_JSON" | jq -r .reason)"
  ACTION_PARAMS="$(printf '%s' "$ACTION_JSON" | jq -c .params)"
  PRESET="$("${PROJECT_DIR}/ops/select-preset.sh")"
  # Preset first, then the axes drawn FOR it: a preset that fixes its school
  # (impact-report) must not be handed a lead author from another one.
  AXES="$("${PROJECT_DIR}/ops/draw-axes.py" --root "$worktree" --preset "$PRESET")"
  PUBLISHED_AT="$(date -Iseconds)"
  log "=== assessed action: ${ACTION} --- ${ACTION_REASON} ==="
  log "action params: ${ACTION_PARAMS}"
  log "=== selected preset: ${PRESET}; publishedAt: ${PUBLISHED_AT} ==="
  log "=== drawn axes ==="
  printf '%s\n' "$AXES" >> "$LOG_FILE"
}

# Build the /publish prompt from the assessed action and the drawn inputs.
# Sets AGENT_PROMPT.
#
# The action comes first and by name, so the run never re-reads the ledger to
# decide what to do. The preset and axes are only sent on a 2A or 2T run: on
# any other rung they are noise that pulled the model back toward 2A.
compose_agent_prompt() {
  local extra="${1:-}"
  AGENT_PROMPT="/publish. This run's action is ${ACTION} --- assessed by ops/assess-ladder.py from the live ledger (${ACTION_REASON}). Take that action and no other; do not re-assess the ladder or read the corpus to second-guess it. Action parameters: ${ACTION_PARAMS}
Record publishedAt from SLOPU_PUBLISHED_AT in any outputs entry, and in any news post that announces no output."
  if [ "$ACTION" = "2A" ] || [ "$ACTION" = "2T" ]; then
    AGENT_PROMPT="${AGENT_PROMPT}
The wrapper selected preset: ${PRESET}. You must use that preset; do not roll a preset yourself. The wrapper also drew what this run is given; take each as given, and do not infer, count or override any of them:
${AXES}"
  fi
  # A run started to spend a budget that resets at a known time (the thesis)
  # has to finish before it; the agent is the only party that can pace itself.
  if [ -n "${SLOPU_DEADLINE:-}" ]; then
    AGENT_PROMPT="${AGENT_PROMPT}
Hard deadline: this run must have committed by ${SLOPU_DEADLINE} (local time; the token budget it spends resets then). Plan the work backwards from that time, check the clock (\`date\`) between phases, and scale the document toward the lower end of its range rather than run past it. A run that has not committed by the deadline publishes nothing."
  fi
  [ -n "$extra" ] && AGENT_PROMPT="${AGENT_PROMPT}
${extra}"
  return 0
}

# Run the agent in <worktree> on <model>. Sets AGENT_STATUS; the transcript
# lands in $AGENT_OUT and is appended to the log.
#
# Expects the caller to have set AGENT_OUT, AGENT_PROMPT,
# PUBLISHED_AT, and any of SLOPU_PENDING_DIR / SLOPU_SKIP_BUILD it wants passed
# through.
#
# GIT_AUTHOR_* stamps every commit with a distinct author, so validation can
# prove every commit on the branch is the agent's. SLOPU_PUBLIC_ONLY tells the
# from-preset resolver to treat private/ preset overlays as unresolvable --- the
# unattended path can only ever run public slop presets (and in a worktree
# private/ does not exist to begin with).
#
# `env -u` strips the credentials the agent must never hold. mise exports the
# whole untracked [env] block into this shell and the agent runs as a child, so
# without this it would inherit the posting and bucket keys and could bypass
# the compose/publish split directly. That matters because the agent reads
# attacker-influenceable input every run (the RSS sources and the Bluesky search
# in 2A): stripping the tokens turns "the agent has no code path to post" into
# "the agent has no credential to post with". REPLICATE_API_TOKEN deliberately
# stays: image generation genuinely needs it, so that key carries a spend cap.
run_agent() {
  local worktree="$1" model="$2"
  local started
  started="$(date -Iseconds)"
  # The effort pin is a Claude option and agent-run REJECTS it on any other
  # runner (exit 2, nothing attempted) rather than ignoring it; any other
  # runner takes its own default.
  local -a effort_args=()
  local effort_note="runner default"
  case "$AGENT_PROFILE" in
    claude-*) effort_args=(--claude-effort "$AGENT_EFFORT"); effort_note="$AGENT_EFFORT" ;;
  esac
  AGENT_STATUS=0
  log "=== publish agent starting at ${started} (profile ${AGENT_PROFILE}, model ${model}, effort ${effort_note}) ==="
  (
    cd "$worktree"
    GIT_AUTHOR_NAME="$AGENT_NAME" \
    GIT_AUTHOR_EMAIL="$AGENT_EMAIL" \
    SLOPU_PUBLIC_ONLY=1 \
    SLOPU_PUBLISHED_AT="$PUBLISHED_AT" \
    env -u SLOPU_TOKEN \
        -u SLOPU_LINKEDIN_WEBHOOK \
        -u SLOPU_LINKEDIN_WEBHOOK_KEY \
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
      "${effort_args[@]}" \
      --bypass-permissions \
      "$AGENT_PROMPT"
  ) > "$AGENT_OUT" 2>&1 || AGENT_STATUS=$?
  cat "$AGENT_OUT" >> "$LOG_FILE"
  log "=== publish agent finished at $(date -Iseconds) (status ${AGENT_STATUS}) ==="
  # What the run cost, from the runner's own transcript: the meter the tick
  # rate is tuned against. Best effort --- a metering failure must never fail a
  # tick.
  "${PROJECT_DIR}/ops/run-usage.py" --profile "$AGENT_PROFILE" --since "$started" \
    --worktree "$worktree" --label "${ACTION:-?}/${PRESET:-?}" >> "$LOG_FILE" 2>&1 \
    || log "usage: metering failed (non-fatal)"
}

# A dead credential is not a failed generation. A failed generation is
# transient --- a typst error, a flaky model call --- and the next run may
# succeed, so tolerating it is right. An expired OAuth token is the opposite:
# every later run dies identically until a human logs in again, so it must
# fail loudly.
agent_auth_failed() {
  grep -qiE 'failed to authenticate|oauth.*(expired|refresh)|invalid api key|please run /login|not logged in' "$AGENT_OUT"
}

# Out of usage credits is a third thing again --- not a dead credential (the
# login is fine) and not a failed generation (nothing was attempted). It is
# usually the limit for ONE model, so the run's best move is to retry once on
# another model rather than forfeit the slot. "hit your <period> limit" is the
# subscription's wording, with the period left open because the list of
# billing windows is theirs to change.
credits_exhausted() {
  grep -qiE "out of usage credits|usage limit reached|(exceeded|hit) your [a-z ]*limit" "$AGENT_OUT"
}

# The whole subscription is out, as opposed to one model's window being shut: a
# weekly/daily/monthly limit binds every model, so a model retry is futile.
credits_hard_exhausted() {
  grep -qiE 'hit your [a-z ]*(weekly|daily|monthly) limit' "$AGENT_OUT" 2>/dev/null
}
