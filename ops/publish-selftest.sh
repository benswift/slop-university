#!/usr/bin/env bash
# End-to-end self-test for the publish pipeline, against a throwaway clone.
#
# Usage: ops/publish-selftest.sh [--keep]
#
# Builds a fixture (a bare "origin" plus a working clone carrying the CURRENT
# working-tree state of ops/, canon/ and the publish skill), stands a fake agent
# in for the model, and drives every path that decides whether work ships:
# generate, claim, rebase, validate, pair, build, rescue, sweep, push.
#
# Why this exists. The pipeline is unattended, it pushes to a live site, and
# ops/cron-publish.sh takes effect at the NEXT TICK with no deploy step --- so a
# mistake here is live within the hour and nobody is watching. Testing it by
# hand found three real bugs in one sitting (a sibling generator's staging dir
# defeating the out-of-credits retry, the lander reporting a forbidden-path
# violation as a red build because the expensive gate ran first, and a sweeper
# that dated candidates from a commit timestamp that says nothing about when the
# run started). Those are exactly the bugs that never show up until they eat a
# night of ticks.
#
# The fixture is safe by construction: a clone has its own origin, so a push
# reaches only the fixture's bare repo, and publish-lib.sh's fixture guard
# refuses every bucket upload (the buckets are global; git is not).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE="$(mktemp -d -t slopu-selftest-XXXXXX)"
KEEP=0
[ "${1:-}" = "--keep" ] && KEEP=1

PASS=0
FAIL=0
cleanup() {
  if [ "$KEEP" = 1 ]; then
    echo "fixture kept at ${FIXTURE}"
  else
    # The fixture registers worktrees in its own clone only, so a plain rm is
    # enough; nothing points back at the real checkout.
    rm -rf "$FIXTURE"
  fi
  echo
  echo "passed: ${PASS}  failed: ${FAIL}"
  [ "$FAIL" -eq 0 ]
}
trap cleanup EXIT

check() {
  local label="$1" expected="$2" actual="$3"
  if [ "$expected" = "$actual" ]; then
    printf '  ok   %s\n' "$label"
    PASS=$((PASS + 1))
  else
    printf '  FAIL %s\n       expected: %s\n       actual:   %s\n' "$label" "$expected" "$actual"
    FAIL=$((FAIL + 1))
  fi
}

# The RESULT= line is the pipeline's own contract with systemd and the on-call
# todo, so asserting on its token is asserting on the thing that actually
# reaches a human.
outcome() { sed -n 's/^RESULT=\([a-z-]*\) .*/\1/p' | tail -1; }

echo "building fixture in ${FIXTURE}"
git -C "$REPO_ROOT" clone --quiet --bare . "${FIXTURE}/origin.git"
git clone --quiet "${FIXTURE}/origin.git" "${FIXTURE}/repo"
REPO="${FIXTURE}/repo"
git -C "$REPO" config user.email ben@benswift.me
git -C "$REPO" config user.name "Ben Swift"

# Carry the working tree's current version of everything under test, so the
# self-test checks what is about to be committed rather than what already was.
for f in ops/publish-lib.sh ops/publish-generate.sh ops/publish-land.sh ops/cron-publish.sh \
         ops/draw-axes.py ops/encode-images.py ops/select-preset.sh ops/topic-claim.py \
         canon/axes.yml canon/burnt-shapes.yml skills/publish/SKILL.md \
         skills/from-preset/presets/impact-report.md; do
  mkdir -p "$(dirname "${REPO}/${f}")"
  cp "${REPO_ROOT}/${f}" "${REPO}/${f}"
done
chmod +x "${REPO}"/ops/*.sh "${REPO}"/ops/*.py
git -C "$REPO" add -A
git -C "$REPO" commit -qm "selftest: carry the working tree into the fixture"
git -C "$REPO" push -q origin main

# --- Stand-ins for the model. Each writes only its own new files, which is the
# property that makes concurrent 2A slots safe in the first place.
cat > "${FIXTURE}/agent-good" <<'AGENT'
#!/usr/bin/env bash
set -euo pipefail
SLUG="probe-$$"
STAGING="${SLOPU_PENDING_DIR:-$(git rev-parse --show-toplevel)/data/pending-uploads}"
cat > "website/src/content/news/2026-08-26-${SLUG}.md" <<MD
---
title: "Probe ${SLUG}"
date: 2026-08-26
summary: a disjoint-file candidate standing in for a real publish action
hero:
  width: 2752
  height: 1536
---

Body text.
MD
git add "website/src/content/news/2026-08-26-${SLUG}.md"
git commit -qm "publish: news — ${SLUG}"
mkdir -p "${STAGING}/img/heroes/news" "${STAGING}/img/og/news"
: > "${STAGING}/img/heroes/news/2026-08-26-${SLUG}-800.avif"
: > "${STAGING}/img/og/news/2026-08-26-${SLUG}.jpg"
AGENT

# Commits a news post but stages no hero: the pairing invariant's whole point.
cat > "${FIXTURE}/agent-noassets" <<'AGENT'
#!/usr/bin/env bash
set -euo pipefail
SLUG="bare-$$"
cat > "website/src/content/news/2026-08-26-${SLUG}.md" <<MD
---
title: "Bare ${SLUG}"
date: 2026-08-26
summary: a news post whose hero was never staged
hero:
  width: 2752
  height: 1536
---

Body text.
MD
git add "website/src/content/news/2026-08-26-${SLUG}.md"
git commit -qm "publish: news — ${SLUG}"
AGENT

# Touches a path the allowlist forbids AND breaks the build, so the outcome
# token proves which gate spoke first.
cat > "${FIXTURE}/agent-forbidden" <<'AGENT'
#!/usr/bin/env bash
set -euo pipefail
echo "# tampered" >> website/astro.config.mjs
git add website/astro.config.mjs
git commit -qm "publish: news — innocuous subject"
AGENT

chmod +x "${FIXTURE}"/agent-*

gen() { # gen <slot> <agent>
  ( cd "$REPO" && SLOPU_PROJECT_DIR="$REPO" SLOPU_AGENT_RUN="${FIXTURE}/agent-$2" \
      ./ops/publish-generate.sh "$1" 2>&1 ) | outcome
}
land() { # land [args...]
  ( cd "$REPO" && SLOPU_PROJECT_DIR="$REPO" SLOPU_PRESS_WORKTREE="${FIXTURE}/press" \
      ./ops/publish-land.sh "$@" 2>&1 ) | outcome
}
serial() {
  ( cd "$REPO" && SLOPU_PROJECT_DIR="$REPO" SLOPU_PRESS_WORKTREE="${FIXTURE}/press" \
      SLOPU_AGENT_RUN="${FIXTURE}/agent-$1" ./ops/cron-publish.sh 2>&1 ) | outcome
}

echo
echo "generate + land"
check "a generator produces a candidate"            candidate    "$(gen 2 good)"
check "the lander lands it"                         published    "$(land)"
check "an empty queue is idle, not an error"        idle         "$(land)"

echo
echo "concurrency"
gen 2 good > /dev/null; gen 3 good > /dev/null
check "two disjoint candidates: first lands"        published    "$(land)"
check "two disjoint candidates: second lands"       published    "$(land)"

echo
echo "the queue never blocks"
gen 2 forbidden > /dev/null
gen 3 good > /dev/null
check "a forbidden path is a VALIDATION failure"    validation-failure "$(land)"
check "...and the good candidate behind it lands"   published    "$(land)"
gen 2 noassets > /dev/null
gen 3 good > /dev/null
check "an entry with no staged assets is rescued"   rescued-pairing "$(land)"
check "...and the queue keeps moving"               published    "$(land)"

echo
echo "sweeper"
git -C "$REPO" branch press-gen-20260101T000000Z-slot9 main
mkdir -p "${REPO}/data/pending-uploads/20260101T000000Z-slot9"
land --sweep-only > /dev/null
check "an abandoned candidate is expired" "" \
  "$(git -C "$REPO" branch --list 'press-gen-20260101T000000Z-slot9' | tr -d ' +*')"
gen 2 good > /dev/null
check "a fresh candidate is NOT swept" "press-gen" \
  "$(git -C "$REPO" for-each-ref --format='%(refname:short)' 'refs/heads/press-gen-*' | head -1 | cut -d- -f1-2)"
check "an overdue queue reaches a human" stale-queue \
  "$( ( cd "$REPO" && SLOPU_PROJECT_DIR="$REPO" SLOPU_PRESS_WORKTREE="${FIXTURE}/press" \
        SLOPU_CANDIDATE_STALE_MINUTES=0 ./ops/publish-land.sh --sweep-only 2>&1 ) | outcome )"
land > /dev/null

echo
echo "dry run"
gen 2 good > /dev/null
check "a dry run passes every gate and ships nothing" dry-run-ok "$(land --dry-run)"
BEFORE="$(git -C "$REPO" rev-parse origin/main)"
check "...and origin did not move" "$BEFORE" "$(git -C "$REPO" fetch -q origin && git -C "$REPO" rev-parse origin/main)"
rm -f "${REPO}"/data/candidates/*.dryrun

echo
echo "the serial pipeline (ops/cron-publish.sh) still works"
check "a full serial tick publishes"                published    "$(serial good)"
check "a serial tick rejects an unstaged entry"     validation-failure "$(serial noassets)"

# --- The author draw against the preset it is drawing for. impact-report is
# the School of Continuous Improvement's report about itself; a lead from
# anywhere else is a contradiction the agent can only stop and ask about.
echo
echo "preset-constrained attribution"
draw_school() { # <preset-args...>
  ( cd "$REPO" && ./ops/draw-axes.py --json "$@" ) \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["school"])'
}
SCHOOLS="$(for _ in 1 2 3 4 5 6 7 8; do draw_school --preset impact-report; done | sort -u)"
check "impact-report always leads from its own school" "School of Continuous Improvement" "$SCHOOLS"
check "a preset that fixes no school still draws freely" ok \
  "$( [ "$(for _ in 1 2 3 4 5 6 7 8; do draw_school --preset paper; done | sort -u | wc -l)" -gt 1 ] && echo ok || echo "only one school in 8 draws" )"
check "a misspelt preset fails loudly rather than drawing unconstrained" 1 \
  "$( ( cd "$REPO" && ./ops/draw-axes.py --json --preset no-such-preset >/dev/null 2>&1 ); echo $? )"

# --- The credit/limit classifiers, against captured evidence rather than a
# live account. This is the one part of the wrapper whose failure mode is
# silent: a misclassified limit reports as a failed generation, the retry that
# would have rescued the tick never fires, and the pipeline keeps ticking
# green-ish while publishing nothing. That is exactly what happened on
# 2026-08-26 --- the fixtures below are the real records off that outage.
echo
echo "credit classifiers"

# Runs one predicate against a pair of fixture files, in a subshell so
# publish-lib.sh's globals never leak into this harness. Echoes yes/no.
classify() { # <profile> <agent-out fixture> <stop-failure fixture> <predicate>
  (
    set +e
    PROJECT_DIR="$REPO_ROOT" LOG_FILE=/dev/null
    # shellcheck source=ops/publish-lib.sh
    source "${REPO_ROOT}/ops/publish-lib.sh"
    AGENT_PROFILE="$1" AGENT_OUT="$2" STOP_FAILURE_LOG="$3"
    if "$4"; then echo yes; else echo no; fi
  )
}

CLS="${FIXTURE}/classifiers"
mkdir -p "$CLS"

# Verbatim from logs/publish-2026-08-26.log. Note the hook's own verdict:
# "invalid_request", not "rate_limit" --- xAI classifies a dead balance as a
# malformed request, which is why the hook cannot be the only detector.
cat > "${CLS}/402.out" <<'EOF'
Internal error: {
  "message": "API error (status 402 Payment Required): Grok Build usage balance exhausted",
  "http_status": 402
}
EOF
cat > "${CLS}/402.jsonl" <<'EOF'
{"event": "stop_failure", "sessionId": "01a03dbc", "error": "invalid_request", "errorDetails": "API error (status 402 Payment Required): Grok Build usage balance exhausted"}
{"event": "session_end", "sessionId": "01a03dbc"}
EOF

printf 'Error: overloaded\n' > "${CLS}/429.out"
printf '%s\n' '{"event": "stop_failure", "error": "rate_limit", "errorDetails": "API error (status 529): Overloaded"}' > "${CLS}/429.jsonl"

printf 'error: expected semicolon\ntypst compile failed\n' > "${CLS}/typst.out"
printf '%s\n' '{"event": "session_end", "sessionId": "x"}' > "${CLS}/typst.jsonl"

printf "You're out of usage credits\n" > "${CLS}/claude.out"
: > "${CLS}/claude.jsonl"

check "a Grok 402 is out of credits, not a failed generation" yes \
  "$(classify grok-sub "${CLS}/402.out" "${CLS}/402.jsonl" credits_exhausted)"
check "...and is HARD exhaustion, so a model retry is futile" yes \
  "$(classify grok-sub "${CLS}/402.out" "${CLS}/402.jsonl" credits_hard_exhausted)"
check "...and is not mistaken for a dead credential" no \
  "$(classify grok-sub "${CLS}/402.out" "${CLS}/402.jsonl" agent_auth_failed)"
check "a capacity rate limit is retryable, not hard exhaustion" no \
  "$(classify grok-sub "${CLS}/429.out" "${CLS}/429.jsonl" credits_hard_exhausted)"
check "...but still counts as out of credits" yes \
  "$(classify grok-sub "${CLS}/429.out" "${CLS}/429.jsonl" credits_exhausted)"
check "a typst error is neither" no \
  "$(classify grok-sub "${CLS}/typst.out" "${CLS}/typst.jsonl" credits_exhausted)"
check "a Claude exhaustion still reads off the regex" yes \
  "$(classify claude-sub "${CLS}/claude.out" "${CLS}/claude.jsonl" credits_exhausted)"

# The route fallback, which is what turns a dead Grok balance into a published
# output instead of a lost tick.
route() { # <field>
  (
    PROJECT_DIR="$REPO_ROOT" LOG_FILE=/dev/null AGENT_PROFILE=grok-sub
    # shellcheck source=ops/publish-lib.sh
    source "${REPO_ROOT}/ops/publish-lib.sh"
    if switch_to_fallback_profile; then
      case "$1" in
        profile)  echo "$AGENT_PROFILE" ;;
        model)    echo "$AGENT_MODEL" ;;
        again)    if switch_to_fallback_profile; then echo yes; else echo no; fi ;;
      esac
    else
      echo no-fallback
    fi
  )
}

check "a dead Grok balance falls through to claude-sub" claude-sub "$(route profile)"
check "...on that profile's own model, not the Grok pin" sonnet "$(route model)"
check "...and each route is tried once, never looped" no "$(route again)"

echo
echo "fixture safety"
check "no bucket upload was attempted from the fixture" 0 \
  "$(grep -c 'uploading .* to the .*bucket' "${REPO}"/logs/publish-*.log || true)"
