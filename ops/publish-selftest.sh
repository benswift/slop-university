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
         ops/check-output-quality.py ops/check-recent-language.py ops/draw-axes.py \
         ops/encode-images.py ops/select-preset.sh ops/topic-claim.py \
         canon/axes.yml canon/burnt-shapes.yml skills/publish/SKILL.md \
         skills/from-preset/presets/*.md; do
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

# Exits clean having done nothing --- what an agent that stopped to ask the
# operator a question looks like from out here.
cat > "${FIXTURE}/agent-nothing" <<'AGENT'
#!/usr/bin/env bash
set -euo pipefail
echo "I have hit a contradiction and would like to ask you which way to go."
AGENT

# Stages a paired but visibly collapsed paper. This gets past the asset check,
# proving the page-flow gate has its own place in the wrapper.
cat > "${FIXTURE}/agent-sparse" <<'AGENT'
#!/usr/bin/env bash
set -euo pipefail
ID="slop-paper-sparse-$$"
STAGING="${SLOPU_PENDING_DIR:-$(git rev-parse --show-toplevel)/data/pending-uploads}"
cat > "/tmp/${ID}.typ" <<'TYP'
#set page(paper: "a4", margin: 1.4cm)
= A stranded final page
#for word in range(900) [substantive ]
#pagebreak()
Only one short paragraph made it onto this page.
TYP
mkdir -p "$STAGING" "${STAGING}/img/thumbs" "${STAGING}/img/heroes/outputs" "${STAGING}/img/og/outputs"
typst compile "/tmp/${ID}.typ" "${STAGING}/${ID}.pdf"
: > "${STAGING}/img/thumbs/${ID}-400.avif"
: > "${STAGING}/img/heroes/outputs/${ID}-800.avif"
: > "${STAGING}/img/og/outputs/${ID}.jpg"
cat > "website/src/content/outputs/${ID}.yml" <<YML
title: A stranded final page
authors: []
preset: paper
school: School of Continuous Improvement
date: 2026-08-26
doi: 10.5555/slop.sparse
summary: A fixture for the final-content-page quality gate.
topic: Test the quality gate
pages: 1
version: "1.0"
YML
git add "website/src/content/outputs/${ID}.yml"
git commit -qm "publish: sparse output fixture"
AGENT

chmod +x "${FIXTURE}"/agent-*

echo
echo "document quality helpers"
quality() { # quality <preset> <pdf>
  ( "${REPO}/ops/check-output-quality.py" --preset "$1" "$2" >/dev/null 2>&1 ); echo $?
}

# <name> <pages> <heading-or-empty>: a document whose PENULTIMATE page (the one
# a booklet is judged on) carries a short closing block reaching a bit under
# half the page, optionally under a section heading. At two pages the same block
# is the final page, which is what a paper is judged on.
fixture() {
  { echo '#set page(paper: "a4", margin: 1.4cm)'
    echo '#set text(size: 10pt)'
    echo '#for word in range(420) [substantive ]'
    echo '#pagebreak()'
    if [ -n "$3" ]; then echo "#text(size: 20pt)[$3]"; fi
    echo '#for word in range(12) [a closing line of ordinary prose ]'
    echo '#place(top + left, dy: 45%, [The last line of the closing block.])'
    if [ "$2" = 3 ]; then echo '#pagebreak()'; echo 'Back cover.'; fi
  } > "${FIXTURE}/${1}.typ"
  typst compile "${FIXTURE}/${1}.typ" "${FIXTURE}/${1}.pdf"
}

cat > "${FIXTURE}/dense.typ" <<'TYP'
#set page(paper: "a4", margin: 1cm)
#for word in range(130) [substantive ]
#place(top + left, dy: 72%, [A final substantive line near the foot of the content area.])
TYP
typst compile "${FIXTURE}/dense.typ" "${FIXTURE}/dense.pdf"
check "a substantially filled final page passes" 0 "$(quality paper "${FIXTURE}/dense.pdf")"

# The calibration that keeps the gate off the published corpus. A booklet page
# is one full-width column, so a heading-less half page is a visible hole; the
# same page under a closing section heading is an ordinary sign-off. A paper
# page is two columns and the measure only sees the deeper one, so references
# stopping part-way down the left column --- which every real paper does --- has
# to pass. Get either bar wrong and the gate rescues a quarter of the corpus.
fixture closing-spill 3 ""
fixture closing-section 3 "With thanks"
fixture part-column 2 ""
check "a booklet's heading-less half page is a spill, and fails" 1 \
  "$(quality strategy "${FIXTURE}/closing-spill.pdf")"
check "...but the same page under a closing heading passes" 0 \
  "$(quality strategy "${FIXTURE}/closing-section.pdf")"
check "a paper's part-column of references passes" 0 \
  "$(quality paper "${FIXTURE}/part-column.pdf")"
check "a poster format is out of scope, not a failure" 0 \
  "$(quality research-poster "${FIXTURE}/part-column.pdf")"

# The audit's whole value is telling a scaffold that has stopped rotating apart
# from the blueprint's own furniture. Four references: one label and sentence
# frame shared by two of them (a drifting scaffold), another shared by all four
# (the template speaking, and not this run's to rewrite).
language() { # language <name> <section-label>
  { echo "= $2"
    echo "This programme will continue to map ordinary conduct through a calibrated institutional lens."
    echo
    echo "= Office of Research Outputs"
    echo "The University publishes each instrument alongside the rule it is meant to inform."
  } > "${FIXTURE}/${1}.typ"
  typst compile "${FIXTURE}/${1}.typ" "${FIXTURE}/${1}.pdf"
}
language language "Capability pathways"
language language-a "Capability pathways"
language language-b "Capability pathways"
language language-c "Adjacent provisions"
language language-d "Distinct provisions"
LANGUAGE_REPORT="$("${REPO}/ops/check-recent-language.py" --preset paper \
  --reference "${FIXTURE}/language-a.pdf" --reference "${FIXTURE}/language-b.pdf" \
  --reference "${FIXTURE}/language-c.pdf" --reference "${FIXTURE}/language-d.pdf" \
  "${FIXTURE}/language.pdf")"
# under <heading> <needle>: is the needle listed beneath that report heading?
under() {
  awk -v head="$1" '$0 ~ head {inside=1; next} /^[^ ]/ {inside=0} inside' \
    <<< "$LANGUAGE_REPORT" | grep -q "$2" && echo yes || echo no
}
check "the corpus audit spots a repeated section label" yes \
  "$(grep -q 'Repeated non-fixed section labels' <<< "$LANGUAGE_REPORT" && echo yes || echo no)"
check "...naming the drifting label, not the standing one" yes \
  "$(under 'Repeated non-fixed' 'Capability pathways')"
check "...and files the template's own furniture separately" yes \
  "$(under 'Standing furniture' 'Office of Research Outputs')"
check "...which is not mistaken for a drifting scaffold" no \
  "$(under 'Repeated non-fixed' 'Office of Research Outputs')"
check "the corpus audit spots a repeated sentence frame" yes \
  "$(grep -q 'Repeated six-word sentence openings' <<< "$LANGUAGE_REPORT" && echo yes || echo no)"

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
log_has() { grep -q "$1" "${REPO}"/logs/publish-*.log && echo yes || echo no; }

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
gen 2 sparse > /dev/null
gen 3 good > /dev/null
check "a sparse final content page is rescued"      rescued-quality "$(land)"
check "...and the log names the collapsed final page" yes "$(log_has 'underfilled final content page')"
check "...and a quality failure does not block the queue" published "$(land)"

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
check "a serial tick rejects a sparse final page"   quality-failure "$(serial sparse)"
check "a tick that does nothing is a lost tick, not a success" no-op "$(serial nothing)"
check "...and exits non-zero, so it cannot clear the on-call todo" 6 \
  "$( ( cd "$REPO" && SLOPU_PROJECT_DIR="$REPO" SLOPU_PRESS_WORKTREE="${FIXTURE}/press" \
        SLOPU_AGENT_RUN="${FIXTURE}/agent-nothing" ./ops/cron-publish.sh >/dev/null 2>&1 ); echo $? )"
check "a generator that produces no candidate exits non-zero too" 6 \
  "$( ( cd "$REPO" && SLOPU_PROJECT_DIR="$REPO" \
        SLOPU_AGENT_RUN="${FIXTURE}/agent-nothing" ./ops/publish-generate.sh 1 >/dev/null 2>&1 ); echo $? )"

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

# Every preset the roll can actually produce, because the draw now READS the
# blueprint and a blueprint is a human document. marketing-poster's description
# has a colon inside a plain scalar; parsing the frontmatter rather than
# scanning it for one key made that preset's every tick a crash, at a tenth of
# all rolls. A per-preset smoke is the only check that sees that class of thing.
check "every preset in the registry draws" "" \
  "$( for b in "${REPO}"/skills/from-preset/presets/*.md; do
        name="$(basename "$b" .md)"
        [ "$name" = README ] && continue
        ( cd "$REPO" && ./ops/draw-axes.py --json --preset "$name" >/dev/null 2>&1 ) || echo "$name"
      done )"

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

# Verbatim off logs/publish-2026-08-24.log, where this sentence went unmatched
# twenty-four times in a row and each tick reported a failed generation.
printf "You've hit your weekly limit \xc2\xb7 resets Aug 25, 2am (Australia/Melbourne)\n" > "${CLS}/weekly.out"
: > "${CLS}/weekly.jsonl"
check "a Claude WEEKLY limit is out of credits" yes \
  "$(classify claude-sub "${CLS}/weekly.out" "${CLS}/weekly.jsonl" credits_exhausted)"
check "...and is hard exhaustion: it resets in a week, not an hour" yes \
  "$(classify claude-sub "${CLS}/weekly.out" "${CLS}/weekly.jsonl" credits_hard_exhausted)"

# The route fallback, which is what turns a dead Grok balance into a published
# output instead of a lost tick.
route() { # <starting profile> <field>
  (
    # Via the env var, not the variable: publish-lib.sh derives AGENT_PROFILE
    # (and the fallback that hangs off it) at source time, so a plain assignment
    # here would simply be overwritten by the default.
    PROJECT_DIR="$REPO_ROOT" LOG_FILE=/dev/null SLOPU_AGENT_PROFILE="$1"
    export SLOPU_AGENT_PROFILE
    shift
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

check "a dead Grok balance falls through to claude-sub" claude-sub "$(route grok-sub profile)"
check "...on that profile's own model, not the Grok pin" sonnet "$(route grok-sub model)"
check "...and each route is tried once, never looped" no "$(route grok-sub again)"
check "a spent Claude week falls through the other way" grok-sub "$(route claude-sub profile)"
check "...onto a Grok model, not a Claude one" grok-4.6 "$(route claude-sub model)"

echo
echo "fixture safety"
check "no bucket upload was attempted from the fixture" 0 \
  "$(grep -c 'uploading .* to the .*bucket' "${REPO}"/logs/publish-*.log || true)"
