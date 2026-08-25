#!/usr/bin/python3
"""Record how a Grok turn ended, for the publish wrapper to classify.

The wrapper used to learn "the account is out of credits" by grepping the
agent's stdout for phrasings lifted out of the grok binary's own strings. That
works until xAI rewords one. Grok classifies the failure itself and hands the
classification to a StopFailure hook as one of six tokens (rate_limit,
authentication_failed, invalid_request, server_error, max_output_tokens,
unknown), so the wrapper can read the verdict instead of inferring it.

Two events are registered, and the second matters as much as the first:

    StopFailure --- a turn ended on an API error. The payload we care about.
    SessionEnd  --- fires on every session, successful or not. A heartbeat.

The heartbeat is here because the failure mode of a hook is SILENCE. A hook
that never loaded and a run that never failed both leave no StopFailure line,
and without the heartbeat the wrapper cannot tell "nothing went wrong" from "my
detector is not installed" --- precisely the class of bug this wrapper's history
is full of (sixteen green ticks that published nothing). With it, an empty log
AND no heartbeat is a loud, greppable condition.

Note what this hook cannot see. A dead credential fails before a session
exists: `grok -p` with no auth prints "Not signed in." and exits 1 having fired
no hook at all (verified 2026-08-25 against an isolated GROK_HOME). So auth
detection stays on the wrapper's regex; only the credit/limit path moves here.

Installed globally (symlinked into ~/.grok/hooks/) rather than as a project
hook, because project hooks under <repo>/.grok/ require folder-trust and are
SILENTLY SKIPPED without it --- an unattended pipeline must not depend on a
trust decision nobody is present to make. Global means it fires for every Grok
session on this machine, so it writes nothing unless SLOPU_STOP_FAILURE_LOG
names a destination; the publish wrapper is the only thing that sets it.

Interpreter is /usr/bin/python3 by absolute path --- not `uv run --script` like
the other ops scripts, and not a bare `python3`. This runs as a grandchild of
the wrapper via grok's `sh -c`, and both uv and mise's shims depend on PATH
surviving that chain. Stdlib only, system interpreter, no such dependency.

Passive hook: stdout is ignored and the exit code cannot block anything, so
every path exits 0. A detector that failed a run it was only meant to observe
would be worse than no detector.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys


def main() -> int:
    log = os.environ.get("SLOPU_STOP_FAILURE_LOG", "")
    if not log:
        return 0

    event = os.environ.get("GROK_HOOK_EVENT", "unknown")
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    record = {
        "event": event,
        "sessionId": payload.get("sessionId"),
        "timestamp": payload.get("timestamp"),
    }
    if event == "stop_failure":
        record["error"] = payload.get("error") or "unknown"
        # Verbatim, clipped by grok at 1000 chars. This is the field that tells
        # a transient capacity blip (503/529, which grok ALSO classifies as
        # rate_limit) apart from a genuinely exhausted subscription. Nobody
        # knows the exact wording yet, so record it rather than pattern-match
        # it --- the first real occurrence is the evidence for making that
        # split on something better than a guess.
        record["errorDetails"] = payload.get("errorDetails")
        record["lastAssistantMessage"] = payload.get("lastAssistantMessage")
        record["subagentType"] = payload.get("subagentType")

    path = pathlib.Path(log)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as fh:
        fh.write(json.dumps(record) + "\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # never fail the run we are only observing
        print(f"slopu stop-failure hook: {exc}", file=sys.stderr)
        sys.exit(0)
