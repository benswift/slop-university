#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Unit checks for the publish pipeline's dead-man check.

`problems()` is pure by design so the interesting cases can be asserted here
rather than by stopping a live timer and waiting an hour.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import unittest
from pathlib import Path

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


class ProblemsTest(unittest.TestCase):
    def found(self, **overrides) -> list[str]:
        kwargs = {
            "now": NOW,
            "newest_publish": ago(minutes=20),
            "stopped_for": ARMED,
        }
        kwargs.update(overrides)
        return publish_check.problems(**kwargs)

    def test_healthy_pipeline_is_silent(self):
        self.assertEqual([], self.found())

    def test_a_landing_inside_the_limit_passes(self):
        self.assertEqual([], self.found(newest_publish=ago(hours=5, minutes=55)))

    def test_a_stalled_pipeline_is_reported(self):
        found = self.found(newest_publish=ago(hours=7))
        self.assertEqual(1, len(found))
        self.assertIn("nothing has landed for 7.0h", found[0])

    def test_a_stopped_timer_past_grace_is_reported(self):
        found = self.found(
            stopped_for={
                "slop-publish-gen@1.timer": 2 * 3600,
                "slop-publish-land.timer": None,
            }
        )
        self.assertEqual(1, len(found))
        self.assertIn("slop-publish-gen@1.timer has been stopped for 2.0h", found[0])
        self.assertIn("systemctl --user start", found[0])

    def test_a_brief_pause_is_not_an_outage(self):
        # The stop-edit-start cycle CLAUDE.md prescribes must not page.
        self.assertEqual(
            [],
            self.found(
                stopped_for={
                    "slop-publish-gen@1.timer": 15 * 60,
                    "slop-publish-land.timer": 15 * 60,
                }
            ),
        )

    def test_both_timers_stopped_are_reported_separately(self):
        found = self.found(
            stopped_for={
                "slop-publish-gen@1.timer": 2 * 3600,
                "slop-publish-land.timer": 2 * 3600,
            }
        )
        self.assertEqual(2, len(found))

    def test_a_stopped_timer_is_caught_before_the_stall_shows(self):
        # The point of watching the timers at all: a stop is visible within the
        # hour, where the freshness limit would not notice for six.
        found = self.found(
            newest_publish=ago(minutes=20),
            stopped_for={
                "slop-publish-gen@1.timer": 90 * 60,
                "slop-publish-land.timer": None,
            },
        )
        self.assertEqual(1, len(found))

    def test_an_empty_corpus_is_reported_once(self):
        found = self.found(newest_publish=None)
        self.assertEqual(["main carries no publish commit at all"], found)

    def test_an_empty_corpus_still_reports_a_stopped_timer(self):
        found = self.found(
            newest_publish=None,
            stopped_for={
                "slop-publish-gen@1.timer": 2 * 3600,
                "slop-publish-land.timer": None,
            },
        )
        self.assertEqual(2, len(found))


class FormatAgeTest(unittest.TestCase):
    def test_reads_naturally_at_each_scale(self):
        self.assertEqual("45s", publish_check.format_age(45))
        self.assertEqual("30m", publish_check.format_age(30 * 60))
        self.assertEqual("6.0h", publish_check.format_age(6 * 3600))


class LiveReadTest(unittest.TestCase):
    def test_newest_publish_reads_this_checkout(self):
        # Not a fixture: the corpus is the thing being measured, and a wrong
        # ref or a wrong --grep would return None here rather than a date.
        newest = publish_check.newest_publish()
        self.assertIsNotNone(newest)
        self.assertIsNotNone(newest.tzinfo)

    def test_an_unknown_timer_reads_as_stopped_not_armed(self):
        # Fail closed: a renamed unit must not read as healthy.
        self.assertIsNotNone(
            publish_check.timer_stopped_for("slop-does-not-exist.timer")
        )


if __name__ == "__main__":
    unittest.main()
