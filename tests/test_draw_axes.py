#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Integration checks for the axes drawer."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

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


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    (tmp_path / "canon").mkdir()
    (tmp_path / "canon" / "roster.yml").write_text(ROSTER)
    # The attribution counts read this collection; an empty one is a
    # corpus with nothing published yet, which weights every school
    # and every researcher equally.
    (tmp_path / "website" / "src" / "content" / "outputs").mkdir(parents=True)
    return tmp_path


def draw(root: Path, *flags: str) -> dict:
    result = subprocess.run(
        [str(SCRIPT), *flags, "--json", "--root", str(root)],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


@pytest.fixture
def thesis_draws(fake_root: Path) -> list[dict]:
    return [draw(fake_root, "--thesis") for _ in range(12)]


def test_a_student_never_supervises(thesis_draws: list[dict]) -> None:
    for fiction in thesis_draws:
        assert fiction["primary_supervisor"] not in STUDENTS
        assert fiction["associate_supervisor"] not in STUDENTS


def test_a_school_with_no_eligible_supervisor_is_never_drawn(
    thesis_draws: list[dict],
) -> None:
    for fiction in thesis_draws:
        assert fiction["school"] == "School of Present Supervisors"


def test_a_run_is_given_a_subject_a_tradition_and_a_lead(fake_root: Path) -> None:
    subjects = {
        line.split("\t")[0]: line.split("\t")[3]
        for line in (ROOT / "canon" / "subjects.tsv").read_text().splitlines()
    }
    traditions = set()
    for _ in range(24):
        drawn = draw(fake_root)
        # A clinical-looking fabrication is the one harmful kind.
        assert subjects[drawn["subject"]] != "Health Sciences"
        assert drawn["lead_author"]
        traditions.add(drawn["tradition"])
    # Mostly the subject's own field, sometimes an outsider's reading:
    # 24 draws that are all one or all the other mean the share broke.
    assert "native" in traditions
    assert len(traditions) > 1


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
