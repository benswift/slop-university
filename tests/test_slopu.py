#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Integration checks for the slopU dispatcher launcher."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPT = ROOT / "bin" / "slopu"


class SlopuTest(unittest.TestCase):
    def run_slopu(self, *args: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            capture = temp / "argv"
            stub = temp / "agent-run"
            stub.write_text(
                "#!/usr/bin/env zsh\n"
                'for arg in "$@"; do print -r -- "$arg"; done > "$CAPTURE"\n'
            )
            stub.chmod(0o755)
            env = {
                **os.environ,
                "AGENT_RUN_BIN": str(stub),
                "CAPTURE": str(capture),
            }
            env.pop("AGENT_PROFILE", None)
            env.pop("AGENT_MODEL", None)
            subprocess.run(
                [str(SCRIPT), *args],
                cwd=temp,
                env=env,
                check=True,
            )
            return capture.read_text().splitlines()

    def test_preset_preserves_claude_subscription_settings(self) -> None:
        args = self.run_slopu("from-preset", "strategy", "sovereign capability")

        self.assertEqual(
            args,
            [
                "--profile",
                "claude-sub",
                "--cwd",
                str(ROOT),
                "--claude-dangerously-skip-permissions",
                "--codex-sandbox",
                "danger-full-access",
                "--claude-effort",
                "max",
                (
                    "Read skills/from-preset/SKILL.md and execute its workflow "
                    "end-to-end. Argument: strategy sovereign capability (first "
                    "whitespace-separated word is the preset name; the rest is the "
                    "steering prompt)."
                ),
            ],
        )

    def test_publish_keeps_sonnet(self) -> None:
        args = self.run_slopu("publish")

        self.assertEqual(args[-3:-1], ["--model", "sonnet"])
        self.assertIn("skills/publish/SKILL.md", args[-1])
        self.assertNotIn("--claude-effort", args)

    def test_profile_and_model_can_be_switched_together(self) -> None:
        args = self.run_slopu(
            "--profile",
            "openrouter",
            "--model",
            "provider/model:free",
            "from-source",
            "brief.md",
        )

        self.assertEqual(args[0:2], ["--profile", "openrouter"])
        self.assertEqual(args[-3:-1], ["--model", "provider/model:free"])
        self.assertIn("skills/from-source/SKILL.md", args[-1])
        self.assertTrue(args[-1].endswith("Source: brief.md"))

    def test_alternative_publish_profile_keeps_its_model_default(self) -> None:
        args = self.run_slopu("--profile", "deepseek", "publish")

        self.assertIn("skills/publish/SKILL.md", args[-1])
        self.assertNotIn("--model", args)


if __name__ == "__main__":
    unittest.main()
