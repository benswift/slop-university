#!/usr/bin/env bash
# Land a templated video: the mechanical half of publishing one.
#
# `bin/slopu video ...` makes the video and leaves it staged: its encodes and
# covers in data/pending-uploads/video-<slug>/, its entry in
# website/src/content/videos/<slug>.yml and its sources in video/<slug>/ and
# video/scripts/<slug>.md, all uncommitted (skills/video/SKILL.md). This script
# does everything after a human has watched the drafts: gate, commit, upload,
# push. It is ops/land.sh for a video, under the same lock and the same order:
# the bytes are served before the entry that names them ships.
#
# Usage: ops/land-video.sh <slug> [--dry-run]
#        ops/land-video.sh --list        # what is staged and landable
set -euo pipefail

PROJECT_DIR="${SLOPU_PROJECT_DIR:-/home/ben/projects/slop-university}"
# shellcheck source=ops/publish-lib.sh
source "${PROJECT_DIR}/ops/publish-lib.sh"

DRY_RUN=0
SLUG=""
LIST=0

while (($# > 0)); do
  case "$1" in
    --dry-run) DRY_RUN=1; shift ;;
    --list) LIST=1; shift ;;
    -h | --help)
      sed -n '2,13p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
      exit 0
      ;;
    -*)
      echo "land-video: unknown option: $1" >&2
      exit 2
      ;;
    *)
      [ -z "$SLUG" ] || { echo "land-video: one video at a time" >&2; exit 2; }
      SLUG="$1"
      shift
      ;;
  esac
done

cd "$PROJECT_DIR"

in_head() { git rev-parse --verify -q "HEAD:$1" > /dev/null 2>&1; }

list_landable() {
  local d slug
  shopt -s nullglob
  for d in "${PENDING_ROOT}"/video-*/; do
    slug="$(basename "$d")"; slug="${slug#video-}"
    [ -f "website/src/content/videos/${slug}.yml" ] || continue
    in_head "website/src/content/videos/${slug}.yml" && continue
    echo "$slug"
  done
  shopt -u nullglob
}

if [ "$LIST" = 1 ]; then
  list_landable
  exit 0
fi

if [ -z "$SLUG" ]; then
  echo "land-video: which video? staged and landable:" >&2
  list_landable >&2
  exit 2
fi

PENDING_DIR="${PENDING_ROOT}/video-${SLUG}"
ENTRY="website/src/content/videos/${SLUG}.yml"

mkdir -p "$LOG_DIR"
install_exit_trap
activate_mise
log "=== video lander started at $(date -Iseconds) for ${SLUG}$([ "$DRY_RUN" = 1 ] && echo ' (DRY RUN)') ==="

if [ ! -d "$PENDING_DIR" ] || [ ! -f "$ENTRY" ]; then
  result "no-staging" "nothing staged for ${SLUG}; run video/_kit/templated.py stage ${SLUG}"
  exit 2
fi
if in_head "$ENTRY"; then
  result "already-landed" "${SLUG} is already committed; nothing to land"
  exit 2
fi
if pipeline_blocked; then
  result "blocked" "data/publish-blocked exists; a human must clear it"
  exit 0
fi

# Every file the entry names is staged: an entry that ships ahead of its bytes
# is a dead video on the screens and the site.
MISSING=""
while read -r f; do
  [ -f "${PENDING_DIR}/${f}" ] || MISSING="${MISSING} ${f}"
done < <(grep -oE '[a-z0-9-]+-[0-9a-f]{10}\.(mp4|jpg)' "$ENTRY")
if [ -n "$MISSING" ]; then
  result "failed-pairing" "the entry names files not staged:${MISSING}"
  exit 1
fi

exec 9> "${PROJECT_DIR}/data/publish.lock"
if ! flock -n 9; then
  result "skipped-locked" "the autonomous lander holds data/publish.lock"
  exit 0
fi

unwind_commit() {
  git reset --soft HEAD~1 >> "$LOG_FILE" 2>&1 || log "WARNING: could not unwind the landing commit"
}

TITLE="$(sed -n 's/^title:[[:space:]]*//p' "$ENTRY" | head -1 | sed "s/^['\"]//; s/['\"]$//")"
KIND="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["kind"])' "video/${SLUG}/spec.json")"
git add "$ENTRY" "video/${SLUG}" "video/scripts/${SLUG}.md"
git commit -q -m "video: ${KIND} — ${TITLE}"
log "committed $(git rev-parse --short HEAD)"

if ! "${PROJECT_DIR}/ops/verify-site.sh" >> "$LOG_FILE" 2>&1; then
  unwind_commit
  result "failed-verify" "the site verify chain failed; nothing uploaded or pushed"
  exit 1
fi

if ! git fetch origin >> "$LOG_FILE" 2>&1 || ! git merge-base --is-ancestor origin/main HEAD; then
  unwind_commit
  result "remote-race" "origin/main moved or could not be fetched; pull and retry"
  exit 1
fi

shopt -s nullglob
FILES=("$PENDING_DIR"/*.mp4 "$PENDING_DIR"/*.jpg)
shopt -u nullglob

if [ "$DRY_RUN" = 1 ]; then
  unwind_commit
  result "dry-run-ok" "${SLUG} passed pairing and verify; would upload ${#FILES[@]} file(s) and push"
  exit 0
fi

if bucket_upload_allowed; then
  if ! "${PROJECT_DIR}/ops/bucket-sync.py" upload "${FILES[@]}" >> "$LOG_FILE" 2>&1; then
    unwind_commit
    result "failed-upload" "bucket upload failed; the video would not be served"
    exit 1
  fi
  log "uploaded ${#FILES[@]} file(s)"
fi

if ! git push origin HEAD:main >> "$LOG_FILE" 2>&1; then
  result "failed-push" "git push failed after the upload; commit and staging retained"
  exit 1
fi

rm -rf "$PENDING_DIR"
prune_logs
result "landed" "${SLUG} is live"
exit 0
