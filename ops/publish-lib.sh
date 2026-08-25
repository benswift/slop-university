#!/usr/bin/env bash
# shellcheck shell=bash
# shellcheck disable=SC2034  # this is a library: callers consume these globals
# Shared machinery for the publish pipeline. Sourced, never executed.
#
# Three entry points use this: ops/cron-publish.sh (the serial pipeline, one
# process doing generate-then-land), ops/publish-generate.sh (a concurrent
# generator slot) and ops/publish-land.sh (the single serial lander). They
# differ in what they orchestrate, not in what the safety-critical steps mean
# --- so base selection, commit validation, the entry-to-asset pairing check
# and the agent-failure classifiers live here, in one copy, and every caller
# gets the same answer.
#
# Style note: these functions read and write the caller's globals rather than
# taking every input as a parameter. That is how the original single script was
# written and it keeps the call sites readable; each function documents the
# globals it expects and the ones it sets.

PROJECT_DIR="${PROJECT_DIR:-/home/ben/projects/slop-university}"
LOG_DIR="${PROJECT_DIR}/logs"
LOG_FILE="${LOG_FILE:-${LOG_DIR}/publish-$(date +%Y-%m-%d).log}"

# Where generated PDFs and images wait for the lander to upload them. Under the
# split each generation run owns a SUBDIRECTORY of this (data/pending-uploads/
# <run-id>/), so two slots staging at once cannot see each other's files. The
# serial pipeline still stages at the root, which is why the pairing check
# takes the directory as an argument rather than assuming one.
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
# upload from a fixture writes junk objects into the live image tree. That
# happened once, on 2026-08-26, during the very refactor that added this guard.
#
# So: a fixture run does everything except touch shared external
# infrastructure.
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

# --- The run's outcome, reported to the JOURNAL and not only to logs/.
#
# Everything here says what it is doing in $LOG_FILE and nothing on stdout, so
# `systemctl status` and `journalctl` could only ever show systemd's own
# "Finished" --- which is precisely what they showed for sixteen consecutive
# ticks over 2026-08-03/04 while the agent died one second in on an expired
# OAuth token and published nothing. A tolerated agent failure and a real
# publish were the same green unit, and the only tell was a run lasting seven
# seconds instead of twenty minutes.
#
# So every exit path names an outcome and the EXIT trap prints one greppable
# line to stdout. The trap is what makes that total: a `set -e` abort, a
# TimeoutStartSec kill, or a later code path that forgets to call result() all
# still land a line, and it reads "crashed" rather than nothing at all. That
# line is also what the alert carries --- unit-oncall (wired via OnFailure=)
# quotes the journal tail into the todo, so the todo says which failure this
# was without anyone opening the log.
RUN_RESULT="crashed"
RUN_DETAIL="wrapper exited without recording an outcome"
result() {
  RUN_RESULT="$1"
  RUN_DETAIL="${2:-}"
}

# Callers may define on_exit_cleanup() to add their own teardown; it runs first.
publish_on_exit() {
  local code=$?
  if declare -F on_exit_cleanup > /dev/null; then on_exit_cleanup || true; fi
  rm -f "${AGENT_OUT:-}"
  local line="RESULT=${RUN_RESULT} exit=${code} detail=${RUN_DETAIL}"
  echo "$line"
  log "$line"
}

install_exit_trap() { trap publish_on_exit EXIT; }

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
# canon/burnt-shapes.yml and canon/axes.yml are deliberately absent: since the
# finding-shape became a draw (ops/draw-axes.py) they are static doctrine the
# wrapper reads and no run writes. That removed 2A's only shared-file write,
# which is what makes concurrent 2A slots touch genuinely disjoint files.
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
AGENT_EMAIL="press@slop.university"

# Validate every commit in <base>..<branch>. Sets AGENT_SHAS (the agent's own
# commits, for the caller's outcome line) and VALIDATION_ERROR (empty when
# clean). Returns 1 when anything failed, so a caller can `if ! validate...`.
#
# Nothing but the agent ever commits on a publish branch --- a foreign-authored
# commit there is itself a violation (unlike the old shared-checkout design,
# where human commits landing mid-run were expected and passed through).
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
    [ -f "${pending}/${id}.pdf" ] || MISSING_PDFS="${MISSING_PDFS}  ${id}.pdf"$'\n'
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

# Did THIS run stage any assets? Root-level PDFs plus the root img tree.
#
# Deliberately NOT "is the directory non-empty". While the concurrent split runs
# alongside the serial pipeline, data/pending-uploads/ also holds one
# subdirectory per generator candidate --- so `ls -A` on the serial pipeline's
# staging root answers yes even when the serial run staged nothing, and the
# out-of-credits fallback retry (which is gated on "the run produced nothing")
# would be skipped every time a sibling had work in flight.
staged_anything() {
  local dir="$1"
  local -a pdfs
  shopt -s nullglob
  pdfs=("$dir"/*.pdf)
  shopt -u nullglob
  [ ${#pdfs[@]} -gt 0 ] || [ -d "${dir}/img" ]
}

# --- Rescue a mislanded staging dir before looking for its contents.
#
# The agent resolves the staging path against whatever its cwd is, and it runs
# the site checks from website/ --- which put three ticks' PDFs in
# website/data/pending-uploads/ and threw away three complete generation runs.
# The skill says to cd to the root, but a discarded run costs a full generation
# (typst, imagery, a Replicate spend) and an hour, whereas moving a file costs
# nothing. So: accept it, move it, and shout --- being strict here buys nothing
# and loses real work. The WARNING is the point; if it appears in the log the
# instruction has drifted again.
#
# Args: <destination-pending-dir> <search-root>...
rescue_stray_staging() {
  local dest="$1"; shift
  local root stray_dir strays
  mkdir -p "$dest"
  shopt -s nullglob
  for root in "$@"; do
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
        cp -an "${stray_dir}/img/." "${dest}/img/" >> "$LOG_FILE" 2>&1 \
          && rm -rf "${stray_dir}/img" \
          || log "WARNING: could not merge strays out of ${stray_dir}/img"
      fi
      rmdir -p --ignore-fail-on-non-empty "$stray_dir" 2>/dev/null || true
    done
  done
  shopt -u nullglob
}

# --- The publish agent.
#
# It generates one action's worth of work, stages assets, and COMMITS --- it
# never pushes and never uploads. That trust boundary is the pipeline's spine:
# the agent composes, the wrapper publishes.

# Which agent publishes. The run goes through the dotfiles dispatcher rather
# than a hardcoded CLI, so switching the press from one agent to another is a
# profile name, not an edit to the invocation. grok-sub runs Grok Build on the
# SuperGrok subscription; claude-sub is the previous behaviour.
AGENT_PROFILE="${SLOPU_AGENT_PROFILE:-grok-sub}"
AGENT_RUN="${SLOPU_AGENT_RUN:-/home/ben/.dotfiles/bin/agent-run}"

# --- The model the unattended run generates on, pinned here rather than
# inherited. With no --model the runner takes its own default --- for Claude
# that is ~/.claude/settings.json, i.e. the INTERACTIVE default, whatever was
# last chosen with /model. The press transcripts show the pipeline riding that
# setting through four silent changes (sonnet to late July, opus to 7 Aug,
# sonnet to the 12th, opus to the 17th, fable after), not one of them a
# decision about this pipeline. On 2026-08-20 that bit: the global default had
# moved to Fable, the account's Fable credits ran out at 01:24, and every tick
# for the next seven hours died three seconds in on "You're out of usage
# credits" while opus, sonnet and haiku all still answered. Pinning makes the
# run's model a property of the pipeline; the env overrides ride out a bad
# limit day without an edit.
#
# Model names are per-agent, so the pin has to be too: pointing a Grok profile
# at "sonnet" would fail every tick identically.
case "$AGENT_PROFILE" in
  grok-*) DEFAULT_MODEL="grok-4.6"; DEFAULT_FALLBACK_MODEL="grok-4.5" ;;
  *)      DEFAULT_MODEL="sonnet";   DEFAULT_FALLBACK_MODEL="haiku" ;;
esac
AGENT_MODEL="${SLOPU_AGENT_MODEL:-$DEFAULT_MODEL}"
AGENT_FALLBACK_MODEL="${SLOPU_AGENT_FALLBACK_MODEL:-$DEFAULT_FALLBACK_MODEL}"

# Draw this run's inputs. The preset and the enumerable 2A axes are chosen with
# OS randomness OUTSIDE the model (ops/select-preset.sh, ops/draw-axes.py) so a
# run receives one unambiguous selection instead of inferring it from the
# corpus --- inference converged on its own tail, and it correlates concurrent
# slots, which is precisely what a second generator must not do.
#
# Args: <worktree-dir> (the corpus the attribution draw reads). Sets PRESET,
# AXES and PUBLISHED_AT.
draw_run_inputs() {
  local worktree="$1"
  PRESET="$("${PROJECT_DIR}/ops/select-preset.sh")"
  AXES="$("${PROJECT_DIR}/ops/draw-axes.py" --root "$worktree")"
  PUBLISHED_AT="$(date -Iseconds)"
  log "=== selected preset: ${PRESET}; publishedAt: ${PUBLISHED_AT} ==="
  log "=== drawn axes ==="
  printf '%s\n' "$AXES" >> "$LOG_FILE"
}

# Build the /publish prompt from the drawn inputs. Sets AGENT_PROMPT.
#
# EXTRA_INSTRUCTIONS lets a generator slot narrow the ladder to 2A without a
# second copy of the prompt: concurrent slots must not garden, because the
# gardening rungs are gated on shared state and two slots reading it choose the
# same gap (two bios for one thin researcher, two rewrites of the About page).
compose_agent_prompt() {
  local extra="${1:-}"
  AGENT_PROMPT="/publish. For a 2A output, the wrapper selected preset: ${PRESET}. You must use that preset; do not roll a preset yourself. The wrapper also drew this run's axes; for a 2A output, compose the topic to FIT them, and do not infer, count or override any of them:
${AXES}
Record publishedAt from SLOPU_PUBLISHED_AT in its output entry."
  [ -n "$extra" ] && AGENT_PROMPT="${AGENT_PROMPT}
${extra}"
  return 0
}

# Run the agent in <worktree> on <model>. Sets AGENT_STATUS; the transcript
# lands in $AGENT_OUT and is appended to the log.
#
# Expects the caller to have set AGENT_OUT, STOP_FAILURE_LOG, AGENT_PROMPT,
# PUBLISHED_AT, and any of SLOPU_PENDING_DIR / SLOPU_SKIP_BUILD it wants passed
# through.
#
# GIT_AUTHOR_* stamps every commit with a distinct author, so validation can
# prove every commit on the branch is the agent's. SLOPU_PUBLIC_ONLY tells the
# from-preset resolver to treat private/ preset overlays as unresolvable --- the
# unattended path can only ever run public slop presets (and in a worktree
# private/ does not exist to begin with).
#
# `env -u` strips the credentials the agent must never hold. The compose/publish
# split is structural for the ACTION --- only the wrapper calls the poster and
# the uploader --- but it was never isolation of the CREDENTIAL: mise exports
# the whole untracked [env] block into this shell and the agent runs as a child,
# so it inherited SLOPU_TOKEN and the bucket keys and could have used them
# directly, bypassing the split entirely. That gap matters because the agent
# reads attacker-influenceable input every run: the RSS sources and the Bluesky
# search in 2A are open channels, and a live installation taking topic
# suggestions from the room widens them. Stripping the tokens turns "the agent
# has no code path to post" into "the agent has no credential to post with",
# which survives an injected agent that stops following the skill.
# REPLICATE_API_TOKEN deliberately stays: image generation genuinely needs it,
# so bound that one with a spend cap on the key instead.
run_agent() {
  local worktree="$1" model="$2"
  AGENT_STATUS=0
  rm -f "$STOP_FAILURE_LOG"
  log "=== publish agent starting at $(date -Iseconds) (profile ${AGENT_PROFILE}, model ${model}) ==="
  (
    cd "$worktree"
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
      "$AGENT_PROMPT"
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

# A dead credential is not a failed generation, and the difference is the whole
# reason this check exists. A failed generation is transient --- a typst error,
# a flaky model call --- and the next run genuinely may succeed, so tolerating
# it is right. An expired OAuth token is the opposite: the agent burned nothing
# and did nothing, and every later run dies identically until a human runs
# /login. Treating the two alike is what lost sixteen consecutive ticks behind a
# green unit on 2026-08-03/04.
#
# Each agent says this its own way. Grok's two signatures were captured by
# running it with no credential ("Not signed in.") and with a mangled auth.json
# ("Unauthorized (401) ... Invalid or expired credentials"); the Claude patterns
# are the originals, still live whenever the profile is a Claude one.
agent_auth_failed() {
  grep -qiE 'failed to authenticate|oauth.*(expired|refresh)|invalid api key|please run /login|not logged in|not signed in|invalid or expired credentials|unauthorized \(401\)' "$AGENT_OUT"
}

relogin_hint() {
  case "$AGENT_PROFILE" in
    grok-*) echo "grok login --device-auth (on weddle, redeeming the code in a browser elsewhere)" ;;
    *)      echo "claude /login" ;;
  esac
}

# Out of usage credits is a third thing again --- not a dead credential (the
# login is fine) and not a failed generation (nothing was attempted). It is the
# account's limit for ONE model, which is exactly why the CLI's own advice is
# "switch to another model", so the run's best move is to do that once rather
# than forfeit the slot.
#
# Two detectors, and which one speaks depends on what the run actually had
# available. The hook is authoritative when it ran: grok classified the failure
# itself and said so in a field, so there is nothing to pattern-match. The regex
# survives for the two cases the hook cannot serve --- a Claude profile
# (claude-sub has no such hook) and a Grok run where the hook did not load.
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
  # Capacity errors (503/529) also classify as rate_limit, which is why the hook
  # records errorDetails verbatim: the retry is the right response to both, and
  # the log is what will eventually let the two be told apart.
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
