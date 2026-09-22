#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Integration checks for the axes drawer's thesis fiction."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "ops" / "draw-axes.py"

# Two schools, one of them staffed entirely by doctoral candidates. A drawer
# that filters the supervisor pools can never name a candidate and can never
# draw Absent, which has nobody eligible to supervise in it.
ROSTER = """\
researchers:
  - id: eligible-one
    name: Eligible One
    title: Lecturer
    school: School of Present Supervisors
  - id: eligible-two
    name: Eligible Two
    title: Postdoctoral Fellow
    school: School of Present Supervisors
  - id: student-one
    name: Student One
    title: Doctoral Candidate
    school: School of Present Supervisors
  - id: student-two
    name: Student Two
    title: Doctoral Candidate
    school: School of Absent Supervisors
  - id: student-three
    name: Student Three
    title: Doctoral Candidate
    school: School of Absent Supervisors
"""

STUDENTS = {"student-one", "student-two", "student-three"}


class ThesisFictionTest(unittest.TestCase):
    def draw(self, times: int) -> list[dict]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "canon").mkdir()
            (root / "canon" / "roster.yml").write_text(ROSTER)
            # The attribution counts read this collection; an empty one is a
            # corpus with nothing published yet, which weights every school
            # and every researcher equally.
            (root / "website" / "src" / "content" / "outputs").mkdir(parents=True)
            draws = []
            for _ in range(times):
                result = subprocess.run(
                    [str(SCRIPT), "--thesis", "--json", "--root", str(root)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                draws.append(json.loads(result.stdout))
            return draws

    def test_a_student_never_supervises(self) -> None:
        for fiction in self.draw(12):
            self.assertNotIn(fiction["primary_supervisor"], STUDENTS)
            self.assertNotIn(fiction["associate_supervisor"], STUDENTS)

    def test_a_school_with_no_eligible_supervisor_is_never_drawn(self) -> None:
        for fiction in self.draw(12):
            self.assertEqual(fiction["school"], "School of Present Supervisors")


if __name__ == "__main__":
    unittest.main()
