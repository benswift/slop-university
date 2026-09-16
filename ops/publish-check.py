#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Dead-man check: is the publish pipeline still landing anything?

Every other alert on this pipeline is a failure alert --- the wrappers exit
non-zero, `OnFailure=unit-oncall@` files a todo, and a phone buzzes. That
catches a pipeline that breaks. It cannot catch one that simply stops: a
disabled timer never fails, and neither does a generator whose every run is a
clean no-op. The split made this sharper, since the live path is now one
generator slot and one lander (slot 2 is deliberately off), so a single stopped
timer ends publishing with nothing anywhere reporting a problem.

Two questions, the same shape as `slop wake-check` in the salon:

* has either live timer been stopped longer than a pause takes? Stopping them
  is also how an edit is landed safely (CLAUDE.md says to, since the wrappers
  take effect at the next tick with no deploy step), so the question is how
  long, not whether.
* has anything actually landed recently? This is the end-to-end question, and
  the only one that survives a failure mode nobody predicted --- it is just as
  true of an exhausted subscription, a generator that no-ops every run, and a
  lander that rejects every candidate.

The limit below is set from the corpus rather than guessed: across 210 landings
in the six days to 2026-09-16 the median gap was 20 minutes, the 90th
percentile 1.6h and the longest 3.25h. Six hours is comfortably clear of the
worst observed gap while still catching a stall the same day.

Problems come back from `problems()` as printable lines, which is the whole of
the testable logic; the CLI prints them and exits non-zero so the oncall
pattern does the alerting.
"""

from __future__ import annotations

import argparse
import datetime as dt
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent

# The live path. Slot 2 and the superseded serial `slop-publish.timer` are
# deliberately not here: watching a timer that is meant to be off reports an
# outage every run, which is how a health check trains you to ignore it.
TIMERS = ("slop-publish-gen@1.timer", "slop-publish-land.timer")

MAX_AGE = 6 * 3600.0
# Long enough for the stop-edit-start cycle CLAUDE.md prescribes, short enough
# that a forgotten `start` is caught within a couple of the watchdog's hours.
GRACE = 3600.0


def format_age(seconds: float) -> str:
    if seconds < 90:
        return f"{int(seconds)}s"
    minutes = seconds / 60
    if minutes < 90:
        return f"{minutes:.0f}m"
    return f"{minutes / 60:.1f}h"


def problems(
    *,
    now: dt.datetime,
    newest_publish: dt.datetime | None,
    stopped_for: dict[str, float | None],
    max_age: float = MAX_AGE,
    grace: float = GRACE,
) -> list[str]:
    """Everything wrong right now, as printable lines. Empty means healthy.

    `stopped_for` maps a timer to the seconds it has been inactive, or None
    while it is armed.
    """
    found: list[str] = []

    for timer, stopped in stopped_for.items():
        if stopped is not None and stopped > grace:
            found.append(
                f"{timer} has been stopped for {format_age(stopped)}, past the "
                f"{format_age(grace)} a pause is given; nothing will fire until it is "
                f"started (`systemctl --user start {timer}`)"
            )

    if newest_publish is None:
        found.append("main carries no publish commit at all")
        return found

    age = (now - newest_publish).total_seconds()
    if age > max_age:
        found.append(
            f"nothing has landed for {format_age(age)}, past the {format_age(max_age)} "
            f"limit (newest publish on main: {newest_publish:%a %H:%M}). The generator "
            f"and lander journals say which half stopped: "
            f"`journalctl --user -u slop-publish-gen@1 -u slop-publish-land -n 50`"
        )

    return found


def timer_stopped_for(timer: str) -> float | None:
    """Seconds the timer has been inactive, or None while armed.

    Read off systemd's monotonic clock rather than a wall-clock timestamp, so a
    clock step cannot read as a day-long outage.
    """
    shown = _systemctl_show(timer, "ActiveState", "InactiveEnterTimestampMonotonic")
    if shown.get("ActiveState") == "active":
        return None
    try:
        since_boot = int(shown.get("InactiveEnterTimestampMonotonic", 0)) / 1_000_000
    except ValueError:
        since_boot = 0.0
    return max(0.0, time.monotonic() - since_boot)


def _systemctl_show(unit: str, *properties: str) -> dict[str, str]:
    args = ["systemctl", "--user", "show", unit]
    for prop in properties:
        args += ["-p", prop]
    out = subprocess.run(args, capture_output=True, text=True, check=False).stdout
    return dict(line.split("=", 1) for line in out.splitlines() if "=" in line)


def newest_publish(ref: str = "main") -> dt.datetime | None:
    """When the newest landed output was committed, or None if there is none.

    Local `main`, not `origin/main`: the lander commits and pushes in one step,
    so a commit here means generation reached the end of the pipeline, and a
    push that then failed already failed its own unit.
    """
    out = subprocess.run(
        [
            "git",
            "-C",
            str(PROJECT_DIR),
            "log",
            "-1",
            "--format=%cI",
            "--grep=^publish:",
            ref,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    stamp = out.stdout.strip()
    return dt.datetime.fromisoformat(stamp) if stamp else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-age",
        type=float,
        default=MAX_AGE / 3600,
        metavar="HOURS",
        help="how long without a landing counts as a stall (default: %(default)s)",
    )
    parser.add_argument(
        "--grace",
        type=float,
        default=GRACE / 3600,
        metavar="HOURS",
        help="how long a stopped timer reads as a pause (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    now = dt.datetime.now().astimezone()
    newest = newest_publish()
    found = problems(
        now=now,
        newest_publish=newest,
        stopped_for={timer: timer_stopped_for(timer) for timer in TIMERS},
        max_age=args.max_age * 3600,
        grace=args.grace * 3600,
    )
    if found:
        for problem in found:
            print(f"PUBLISH-CHECK: {problem}", file=sys.stderr)
        return 1

    # `problems()` reports a corpus with no landing at all, so reaching here
    # means there is one to date the healthy line from.
    assert newest is not None
    age = format_age((now - newest).total_seconds())
    print(f"ok: {', '.join(TIMERS)} armed, newest landing {age} old")
    return 0


if __name__ == "__main__":
    sys.exit(main())
