#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Integration checks for the roster merge driver, through git itself."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
DRIVER = ROOT / "ops" / "merge-roster.py"

ROSTER = """\
# The roster.

researchers:
  - id: founder-one
    name: Founder One
    title: Professor
    bio: >-
      A founding professor.
    collisionChecked: "2026-07-04"

  - id: founder-two
    name: Founder Two
    title: Professor
    bio: >-
      Another founding professor.
    collisionChecked: "2026-07-04"
"""


# Candidates admitted on the same day share most of their lines, which is what
# a line-wise union merge folds together.
def candidate(name: str) -> str:
    return f"""\
  - id: {name}
    name: {name}
    title: Doctoral Candidate
    collisionChecked: "2026-10-05"
    supervisors: [founder-one, founder-two]
"""


class Repo:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.roster = path / "canon" / "roster.yml"
        self.roster.parent.mkdir()
        self.roster.write_text(ROSTER)
        (path / ".gitattributes").write_text("canon/roster.yml merge=roster\n")
        self.git("init", "-q", "-b", "main")
        self.git("config", "merge.roster.driver", f"{DRIVER} %O %A %B")
        self.commit("base")

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        identity = ["-c", "user.name=t", "-c", "user.email=t@example.invalid"]
        return subprocess.run(
            ["git", "-C", str(self.path), *identity, *args],
            capture_output=True,
            text=True,
            check=check,
        )

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def branch(self, name: str, text: str) -> None:
        self.git("checkout", "-q", "-b", name, "main")
        self.roster.write_text(text)
        self.commit(name)
        self.git("checkout", "-q", "main")


@pytest.fixture
def repo(tmp_path: Path) -> Repo:
    return Repo(tmp_path)


def test_concurrent_admissions_all_land_whole(repo: Repo) -> None:
    names = ["cand-a", "cand-b", "cand-c"]
    for name in names:
        repo.branch(name, ROSTER + candidate(name))
    repo.git("cherry-pick", *names)
    assert repo.roster.read_text() == ROSTER + "".join(map(candidate, names))


def test_the_same_candidate_twice_conflicts(repo: Repo) -> None:
    repo.branch("first", ROSTER + candidate("cand-a"))
    repo.branch("second", ROSTER + candidate("cand-a").replace("Doctoral", "Second"))
    repo.git("cherry-pick", "first")
    assert repo.git("cherry-pick", "second", check=False).returncode != 0


def test_an_edit_still_merges_as_text(repo: Repo) -> None:
    repo.branch("edit", ROSTER.replace("A founding professor.", "A revised bio."))
    repo.branch("admit", ROSTER + candidate("cand-a"))
    repo.git("cherry-pick", "admit", "edit")
    merged = repo.roster.read_text()
    assert "A revised bio." in merged
    assert merged.endswith(candidate("cand-a"))


def test_two_edits_to_one_bio_conflict(repo: Repo) -> None:
    repo.branch("one", ROSTER.replace("A founding professor.", "One."))
    repo.branch("two", ROSTER.replace("A founding professor.", "Two."))
    repo.git("cherry-pick", "one")
    assert repo.git("cherry-pick", "two", check=False).returncode != 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
