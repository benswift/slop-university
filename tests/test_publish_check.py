#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest", "typer"]
# ///
"""Unit checks for the publish pipeline's dead-man check.

`problems()` is pure by design so the interesting cases can be asserted here
rather than by stopping a live timer and waiting an hour.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SPEC = importlib.util.spec_from_file_location(
    "publish_check", ROOT / "ops" / "publish-check.py"
)
assert SPEC and SPEC.loader
publish_check = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(publish_check)

NOW = dt.datetime(2026, 9, 16, 12, 0, tzinfo=dt.UTC)
ARMED = {"slop-publish-gen@1.timer": None, "slop-publish-land.timer": None}


def ago(**kwargs: float) -> dt.datetime:
    return NOW - dt.timedelta(**kwargs)


def found(**overrides) -> list[str]:
    kwargs = {
        "now": NOW,
        "newest_publish": ago(minutes=20),
        "stopped_for": ARMED,
    }
    kwargs.update(overrides)
    return publish_check.problems(**kwargs)


def test_healthy_pipeline_is_silent():
    assert found() == []


def test_a_landing_inside_the_limit_passes():
    assert found(newest_publish=ago(hours=5, minutes=55)) == []


def test_a_stalled_pipeline_is_reported():
    result = found(newest_publish=ago(hours=7))
    assert len(result) == 1
    assert "nothing has landed for 7.0h" in result[0]


def test_a_stopped_timer_past_grace_is_reported():
    result = found(
        stopped_for={
            "slop-publish-gen@1.timer": 2 * 3600,
            "slop-publish-land.timer": None,
        }
    )
    assert len(result) == 1
    assert "slop-publish-gen@1.timer has been stopped for 2.0h" in result[0]
    assert "systemctl --user start" in result[0]


def test_a_brief_pause_is_not_an_outage():
    # The stop-edit-start cycle CLAUDE.md prescribes must not page.
    assert (
        found(
            stopped_for={
                "slop-publish-gen@1.timer": 15 * 60,
                "slop-publish-land.timer": 15 * 60,
            }
        )
        == []
    )


def test_both_timers_stopped_are_reported_separately():
    result = found(
        stopped_for={
            "slop-publish-gen@1.timer": 2 * 3600,
            "slop-publish-land.timer": 2 * 3600,
        }
    )
    assert len(result) == 2


def test_a_stopped_timer_is_caught_before_the_stall_shows():
    # The point of watching the timers at all: a stop is visible within the
    # hour, where the freshness limit would not notice for six.
    result = found(
        newest_publish=ago(minutes=20),
        stopped_for={
            "slop-publish-gen@1.timer": 90 * 60,
            "slop-publish-land.timer": None,
        },
    )
    assert len(result) == 1


def test_an_empty_corpus_is_reported_once():
    assert found(newest_publish=None) == ["main carries no publish commit at all"]


def test_an_empty_corpus_still_reports_a_stopped_timer():
    result = found(
        newest_publish=None,
        stopped_for={
            "slop-publish-gen@1.timer": 2 * 3600,
            "slop-publish-land.timer": None,
        },
    )
    assert len(result) == 2


@pytest.mark.parametrize(
    ("seconds", "expected"), [(45, "45s"), (30 * 60, "30m"), (6 * 3600, "6.0h")]
)
def test_format_age_reads_naturally_at_each_scale(seconds, expected):
    assert publish_check.format_age(seconds) == expected


def test_newest_publish_reads_this_checkout():
    # Not a fixture: the corpus is the thing being measured, and a wrong
    # ref or a wrong --grep would return None here rather than a date.
    newest = publish_check.newest_publish()
    assert newest is not None
    assert newest.tzinfo is not None


def test_an_unknown_timer_reads_as_stopped_not_armed():
    # Fail closed: a renamed unit must not read as healthy.
    assert publish_check.timer_stopped_for("slop-does-not-exist.timer") is not None


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
