#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pytest"]
# ///
"""Integration checks for the slopU dispatcher launcher."""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "bin" / "slopu"


@pytest.fixture
def run_slopu(tmp_path: Path) -> Callable[..., list[str]]:
    def run(*args: str) -> list[str]:
        capture = tmp_path / "argv"
        stub = tmp_path / "agent-run"
        stub.write_text(
            "#!/usr/bin/env zsh\n"
            'for arg in "$@"; do print -r -- "$arg"; done > "$CAPTURE"\n'
        )
        stub.chmod(0o755)
        env: dict[str, str] = {
            **os.environ,
            "AGENT_RUN_BIN": str(stub),
            "CAPTURE": str(capture),
        }
        env.pop("AGENT_PROFILE", None)
        env.pop("AGENT_MODEL", None)
        subprocess.run([str(SCRIPT), *args], cwd=tmp_path, env=env, check=True)
        return capture.read_text().splitlines()

    return run


def test_preset_preserves_claude_subscription_settings(run_slopu) -> None:
    args = run_slopu("from-preset", "strategy", "sovereign capability")

    assert args == [
        "--profile",
        "claude-sub",
        "--cwd",
        str(ROOT),
        "--bypass-permissions",
        "--claude-effort",
        "max",
        (
            "Read skills/from-preset/SKILL.md and execute its workflow "
            "end-to-end. Argument: strategy sovereign capability (first "
            "whitespace-separated word is the preset name; the rest is the "
            "steering prompt)."
        ),
    ]


def test_publish_keeps_sonnet(run_slopu) -> None:
    args = run_slopu("publish")

    assert args[-3:-1] == ["--model", "sonnet"]
    assert "skills/publish/SKILL.md" in args[-1]
    assert "--claude-effort" not in args


def test_profile_and_model_can_be_switched_together(run_slopu) -> None:
    args = run_slopu(
        "--profile",
        "openrouter",
        "--model",
        "provider/model:free",
        "from-source",
        "brief.md",
    )

    assert args[0:2] == ["--profile", "openrouter"]
    assert args[-3:-1] == ["--model", "provider/model:free"]
    assert "skills/from-source/SKILL.md" in args[-1]
    assert args[-1].endswith("Source: brief.md")


def test_alternative_publish_profile_keeps_its_model_default(run_slopu) -> None:
    args = run_slopu("--profile", "deepseek", "publish")

    assert "skills/publish/SKILL.md" in args[-1]
    assert "--model" not in args


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
