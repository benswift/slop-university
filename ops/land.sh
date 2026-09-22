#!/usr/bin/env bash
# Land a hand-steered document: the mechanical half of publishing one.
#
# `bin/slopu from-preset --land` generates the artefact AND writes its site
# entry, news post and staged assets (skills/from-preset/SKILL.md step 9). This
# script does everything after that: gate, commit, upload, push. It is the hand
# path's equivalent of ops/publish-land.sh, minus the candidate queue --- there
# is no marker to claim and no worktree to rebase, because a hand run works in
# the checkout and the human has already looked at the PDF.
#
# The split is the same one the autonomous pipeline uses, and for the same
# reason: the thing that writes to the buckets and pushes to a live site has no
# model in it. Everything here is derivable from the staged files and the entry.
#
# Usage: ops/land.sh <run-id> [--dry-run]
#        ops/land.sh --list        # what is staged and landable
set -euo pipefail

PROJECT_DIR="${SLOPU_PROJECT_DIR:-/home/ben/projects/slop-university}"
# shellcheck source=ops/publish-lib.sh
source "${PROJECT_DIR}/ops/publish-lib.sh"

DRY_RUN=0
RUN_ID=""
LIST=0

while (($# > 0)); do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --list) LIST=1; shift ;;
    -h | --help)
      sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    -*)
      echo "land: unknown option: $1" >&2
      exit 2
      ;;
    *)
      [ -z "$RUN_ID" ] || { echo "land: one run id at a time" >&2; exit 2; }
      RUN_ID="$1"
      shift
      ;;
  esac
done

cd "$PROJECT_DIR"

# Committed, as opposed to merely staged. A failed or rehearsed landing leaves
# its files in the index (`git reset --soft`), so `git ls-files` would call
# them published and refuse the retry --- HEAD is the only honest answer.
in_head() { git rev-parse --verify -q "HEAD:$1" > /dev/null 2>&1; }

# --- What is landable: a staged directory whose entry is written but not yet
# committed. Both halves have to be true, so this is also the answer to "did
# the generation run actually do step 9".
list_landable() {
  local d id
  shopt -s nullglob
  for d in "${PENDING_ROOT}"/*/; do
    id="$(basename "$d")"
    [ -f "website/src/content/outputs/${id}.yml" ] || continue
    in_head "website/src/content/outputs/${id}.yml" && continue
    echo "$id"
  done
  shopt -u nullglob
}

if [ "$LIST" = 1 ]; then
  list_landable
  exit 0
fi

if [ -z "$RUN_ID" ]; then
  echo "land: which run? staged and landable:" >&2
  list_landable >&2
  exit 2
fi

PENDING_DIR="${PENDING_ROOT}/${RUN_ID}"
ENTRY="website/src/content/outputs/${RUN_ID}.yml"

mkdir -p "$LOG_DIR"
install_exit_trap
activate_mise
log "=== hand lander started at $(date -Iseconds) for ${RUN_ID}$([ "$DRY_RUN" = 1 ] && echo ' (DRY RUN)') ==="

# --- Preflight, before the lock: a missing input is the human's typo, not a
# reason to make the autonomous lander wait behind us.
if [ ! -d "$PENDING_DIR" ]; then
  log "no staging directory at ${PENDING_DIR}"
  result "no-staging" "nothing staged for ${RUN_ID}; was the run generated with --land?"
  exit 2
fi
if [ ! -f "$ENTRY" ]; then
  log "no outputs entry at ${ENTRY}"
  result "no-entry" "${RUN_ID} has no outputs entry; was the run generated with --land?"
  exit 2
fi
if in_head "$ENTRY"; then
  log "${ENTRY} is already committed"
  result "already-landed" "${RUN_ID} is already committed; nothing to land"
  exit 2
fi

if pipeline_blocked; then
  result "blocked" "data/publish-blocked exists; a human must clear it"
  exit 0
fi

# --- The lock the autonomous lander takes, held across the whole critical
# section. Without it a hand landing races ops/publish-land.sh at exactly the
# two steps that matter: the bucket upload and the push to main.
exec 9> "${PROJECT_DIR}/data/publish.lock"
if ! flock -n 9; then
  log "another publish run holds the lock; try again once it finishes"
  result "skipped-locked" "the autonomous lander holds data/publish.lock"
  exit 0
fi

# --- The news posts this landing carries.
#
# Two ways a post belongs to this run, mirroring what check_pairing looks for:
# one that announces the output names it in `output:`, and one that stands on
# its own (an institutional notice) has its own hero staged under its id. Only
# uncommitted files are considered, so an unrelated draft is never swept in.
news_files() {
  local f id
  shopt -s nullglob
  for f in website/src/content/news/*.md website/src/content/news/*.mdx; do
    in_head "$f" && continue
    id="$(basename "$f")"; id="${id%.*}"
    if grep -qE "^output:[[:space:]]*${RUN_ID}[[:space:]]*$" "$f" \
      || compgen -G "${PENDING_DIR}/img/heroes/news/${id}-*.avif" > /dev/null; then
      echo "$f"
    fi
  done
  shopt -u nullglob
}

mapfile -t NEWS < <(news_files)
log "landing ${ENTRY}$([ ${#NEWS[@]} -gt 0 ] && printf ' plus %d news post(s)' "${#NEWS[@]}")"

# --- Citations are harvested, never hand-copied: the .typ is the only place
# the canon's citation edges exist, and output/ is gitignored and disposable.
if ! "${PROJECT_DIR}/ops/extract-citations.py" --id "$RUN_ID" --write >> "$LOG_FILE" 2>&1; then
  log "WARNING: citation harvest failed for ${RUN_ID}; landing without cites:"
fi

# --- Commit, then gate. check_pairing and check_output_quality both diff a
# base against a branch, so the commit has to exist before they can run. An
# unwind puts the tree back exactly as the human left it, files still staged.
unwind_commit() {
  git reset --soft HEAD~1 >> "$LOG_FILE" 2>&1 || log "WARNING: could not unwind the landing commit"
}

TITLE="$(python3 - "$ENTRY" <<'PY'
import re, sys

text = open(sys.argv[1]).read()
value = re.search(r"^title:[ \t]*(.*)$", text, re.M).group(1).strip()
if value in (">", ">-", "|", "|-", ""):
    # A folded scalar: the value is the indented block that follows.
    lines, started = [], False
    for line in text.splitlines():
        if re.match(r"^title:", line):
            started = True
            continue
        if started:
            if re.match(r"^\s+\S", line):
                lines.append(line.strip())
            else:
                break
    value = " ".join(lines)
print(value)
PY
)"
PRESET="$(sed -n 's/^preset:[[:space:]]*//p' "$ENTRY" | head -1)"
DOI="$(sed -n 's/^doi:[[:space:]]*//p' "$ENTRY" | head -1)"

git add "$ENTRY" "${NEWS[@]}"
git commit -q -m "publish: ${PRESET} — ${TITLE} (${DOI})"
log "committed $(git rev-parse --short HEAD)"

if ! check_pairing HEAD~1 HEAD "$PENDING_DIR"; then
  log "PAIRING FAILURE --- staged assets do not cover the entry:"
  printf '%s%s\n' "$MISSING_PDFS" "$MISSING_IMGS" >> "$LOG_FILE"
  unwind_commit
  result "failed-pairing" "assets missing for ${RUN_ID}; nothing uploaded or pushed"
  exit 1
fi

if ! check_output_quality HEAD~1 HEAD "$PENDING_DIR"; then
  unwind_commit
  result "failed-quality" "${QUALITY_ERROR}"
  exit 1
fi

if ! "${PROJECT_DIR}/ops/verify-site.sh" >> "$LOG_FILE" 2>&1; then
  log "SITE VERIFY FAILED --- see the chain output above"
  unwind_commit
  result "failed-verify" "the site verify chain failed; nothing uploaded or pushed"
  exit 1
fi

# --- Upload before push, and only once a fresh fetch proves the remote tip is
# still contained in HEAD. An entry that shipped before its bytes did is a live
# 404, and the id is what derives the URL, so the order is not negotiable.
if ! git fetch origin >> "$LOG_FILE" 2>&1; then
  log "REMOTE RACE GUARD: fetch failed; refusing to upload or push"
  unwind_commit
  result "failed-fetch" "pre-upload fetch of origin failed"
  exit 1
fi
if ! git merge-base --is-ancestor origin/main HEAD; then
  log "REMOTE RACE GUARD: origin/main advanced during landing; refusing to upload or push"
  unwind_commit
  result "remote-race" "origin/main advanced during landing; pull and retry"
  exit 1
fi

shopt -s nullglob
PENDING_PDFS=("$PENDING_DIR"/*.pdf)
shopt -u nullglob

if [ "$DRY_RUN" = 1 ]; then
  log "=== DRY RUN: would upload ${#PENDING_PDFS[@]} PDF(s)$([ -d "${PENDING_DIR}/img" ] && echo ' plus the image tree') and push HEAD to main ==="
  log "unwinding the landing commit; the entry and news post are staged as the human left them"
  unwind_commit
  result "dry-run-ok" "${RUN_ID} passed pairing, quality and verify; not uploaded or pushed"
  exit 0
fi

if [ ${#PENDING_PDFS[@]} -gt 0 ] && bucket_upload_allowed; then
  if "${PROJECT_DIR}/ops/bucket-sync.py" upload "${PENDING_PDFS[@]}" >> "$LOG_FILE" 2>&1; then
    log "uploaded ${#PENDING_PDFS[@]} PDF(s); retaining local copies until the push succeeds"
  else
    log "BUCKET UPLOAD FAILED --- refusing to push an entry whose PDF is not served"
    unwind_commit
    result "failed-upload" "bucket upload failed; the entry's PDF would not be served"
    exit 1
  fi
else
  log "no PDFs staged for ${RUN_ID}"
fi

if [ -d "${PENDING_DIR}/img" ] && bucket_upload_allowed; then
  if "${PROJECT_DIR}/ops/bucket-sync.py" upload --target img "${PENDING_DIR}/img" >> "$LOG_FILE" 2>&1; then
    log "uploaded images; retaining local copies until the push succeeds"
  else
    log "IMG BUCKET UPLOAD FAILED --- refusing to push an entry whose images are not served"
    unwind_commit
    result "failed-upload" "img bucket upload failed; the entry's images would not be served"
    exit 1
  fi
else
  log "no images staged for ${RUN_ID}"
fi

log "=== push at $(date -Iseconds) ==="
if ! git push origin HEAD:main >> "$LOG_FILE" 2>&1; then
  # The assets are already served, which is harmless on its own --- an object
  # nothing links to. Keep the commit and the staging dir so a retry is just
  # this script again after a pull.
  log "PUSH FAILED --- the commit and staging dir are kept; pull and re-run"
  result "failed-push" "git push failed after the upload; commit and staging retained"
  exit 1
fi

rm -rf "$PENDING_DIR"
log "push succeeded; cleared ${RUN_ID}'s staging dir"
flush_staged_posts
prune_logs
result "landed" "${RUN_ID} (${DOI}) is live"
exit 0
