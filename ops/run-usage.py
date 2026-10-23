#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["typer"]
# ///
"""Measure what one publish tick cost in tokens, for whichever agent ran it.

Nothing logs this today: the pipeline picks its agent profile
(`ops/publish-lib.sh`) and pins its model, but nobody records what a tick
actually spent, so the tick rate can't be tuned against a subscription's weekly
allowance and a run-shrinking change can't be measured before/after.

The `claude-sub` transcripts are `~/.claude/projects/<encoded worktree>/*.jsonl`,
one line per CONTENT BLOCK, not one per message: an assistant turn of thinking
plus two tool calls is three lines, each repeating that turn's whole
`message.usage`. So sum usage once per `message.id` and count tool_use blocks
per line. Subagent transcripts live under a subdirectory of the same project
dir (`<session>/subagents/*.jsonl`), so the glob is recursive.

Usage:
  ops/run-usage.py --profile claude-sub --since 2026-09-10T07:30:00+10:00 \\
      --worktree /home/ben/projects/slop-university-press
  ops/run-usage.py --weekly
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def repo_root() -> Path:
    """The checkout this script lives in --- never the worktree being measured,
    which is a separate directory the ledger must survive independently of."""
    out = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=Path(__file__).resolve().parent,
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(out.stdout.strip())


def parse_time(text: str) -> datetime:
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.astimezone()
    return dt


def encode_claude_worktree(worktree: Path) -> str:
    """`/a/b/c` -> `-a-b-c`, the scheme `~/.claude/projects/` uses."""
    return str(worktree).replace("/", "-")


def in_window(mtime: float, since: datetime, until: datetime) -> bool:
    ts = datetime.fromtimestamp(mtime, tz=UTC)
    return since <= ts <= until


@dataclass
class ClaudeUsage:
    calls: int = 0
    input_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    output_tokens: int = 0
    peak_context: int = 0
    images: int = 0
    tools: Counter = field(default_factory=Counter)

    @property
    def context_sent(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_creation_tokens


def collect_claude_usage(
    worktree: Path, since: datetime, until: datetime
) -> ClaudeUsage:
    project_dir = CLAUDE_PROJECTS_DIR / encode_claude_worktree(worktree)
    usage = ClaudeUsage()
    if not project_dir.is_dir():
        return usage

    # One API call's usage, counted once, however many lines the transcript
    # spreads that call's content over. Across the project dir rather than per
    # file: an id identifies the API response, so a line repeating one already
    # seen in a sibling transcript is the same tokens either way.
    counted_calls: set[str] = set()

    for path in project_dir.rglob("*.jsonl"):
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if not in_window(mtime, since, until):
            continue

        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                message = obj.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")

                if message.get("role") == "assistant":
                    msg_usage = message.get("usage")
                    # An id-less line cannot be proved a repeat, so it counts:
                    # under-reporting a tick's cost is the worse failure.
                    message_id = message.get("id")
                    repeat = isinstance(message_id, str) and message_id in counted_calls
                    if isinstance(message_id, str):
                        counted_calls.add(message_id)
                    if isinstance(msg_usage, dict) and not repeat:
                        usage.calls += 1
                        input_tokens = msg_usage.get("input_tokens", 0) or 0
                        cache_read = msg_usage.get("cache_read_input_tokens", 0) or 0
                        cache_creation = (
                            msg_usage.get("cache_creation_input_tokens", 0) or 0
                        )
                        output_tokens = msg_usage.get("output_tokens", 0) or 0
                        usage.input_tokens += input_tokens
                        usage.cache_read_tokens += cache_read
                        usage.cache_creation_tokens += cache_creation
                        usage.output_tokens += output_tokens
                        call_context = input_tokens + cache_read + cache_creation
                        usage.peak_context = max(usage.peak_context, call_context)
                    # Not guarded by `repeat`: every line of a message holds
                    # its own block, so the second line of a two-tool turn is
                    # the second tool, not a duplicate of the first.
                    if isinstance(content, list):
                        for block in content:
                            if (
                                isinstance(block, dict)
                                and block.get("type") == "tool_use"
                            ):
                                usage.tools[block.get("name", "unknown")] += 1

                elif message.get("role") == "user" and isinstance(content, list):
                    for block in content:
                        if not (
                            isinstance(block, dict)
                            and block.get("type") == "tool_result"
                        ):
                            continue
                        result_content = block.get("content")
                        if isinstance(result_content, list):
                            for item in result_content:
                                if (
                                    isinstance(item, dict)
                                    and item.get("type") == "image"
                                ):
                                    usage.images += 1

    return usage


def human(n: int) -> str:
    """Compact magnitude suffix: 358214 -> 358k, 52123456 -> 52.1M."""
    n_abs = abs(n)
    if n_abs >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n_abs >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def append_ledger(ledger_path: Path, record: dict) -> None:
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


def report_claude(usage: ClaudeUsage, label: str | None) -> tuple[str, dict]:
    tools_str = ",".join(f"{name}:{count}" for name, count in usage.tools.most_common())
    line = (
        f"usage: claude-sub calls={usage.calls} "
        f"context_sent={human(usage.context_sent)} "
        f"new_context={human(usage.input_tokens + usage.cache_creation_tokens)} "
        f"output={human(usage.output_tokens)} "
        f"peak_context={human(usage.peak_context)} "
        f"images={usage.images} "
        f"tools={{{tools_str}}}"
    )
    record = {
        "profile": "claude-sub",
        "label": label,
        "calls": usage.calls,
        "input_tokens": usage.input_tokens,
        "cache_read_tokens": usage.cache_read_tokens,
        "cache_creation_tokens": usage.cache_creation_tokens,
        "output_tokens": usage.output_tokens,
        "context_sent": usage.context_sent,
        "peak_context": usage.peak_context,
        "images": usage.images,
        "tools": dict(usage.tools),
    }
    return line, record


def print_weekly(ledger_path: Path) -> int:
    if not ledger_path.is_file():
        print(f"usage: no ledger at {ledger_path}")
        return 0

    cutoff = datetime.now(UTC) - timedelta(days=7)
    totals: dict[str, Counter] = {}
    runs: Counter = Counter()

    with ledger_path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            ts = datetime.fromisoformat(record["timestamp"])
            if ts < cutoff:
                continue
            profile = record["profile"]
            totals.setdefault(profile, Counter())
            runs[profile] += 1
            totals[profile]["calls"] += record.get("calls", 0)
            totals[profile]["context_sent"] += record.get(
                "context_sent", record.get("input_tokens", 0)
            )
            totals[profile]["output_tokens"] += record.get("output_tokens", 0)

    if not totals:
        print("usage: weekly totals: no ledger entries in the trailing 7 days")
        return 0

    for profile, counter in totals.items():
        print(
            f"usage: weekly {profile} runs={runs[profile]} "
            f"calls={counter['calls']} "
            f"context_sent={human(counter['context_sent'])} "
            f"output={human(counter['output_tokens'])}"
        )
    return 0


app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


class Profile(StrEnum):
    claude_sub = "claude-sub"


@app.command(help=__doc__)
def main(
    profile: Annotated[Profile | None, typer.Option("--profile")] = None,
    since: Annotated[
        datetime | None, typer.Option("--since", parser=parse_time)
    ] = None,
    until: Annotated[
        datetime | None, typer.Option("--until", parser=parse_time)
    ] = None,
    worktree: Annotated[Path, typer.Option("--worktree")] = Path(
        "/home/ben/projects/slop-university-press"
    ),
    ledger: Annotated[Path | None, typer.Option("--ledger")] = None,
    label: Annotated[str | None, typer.Option("--label")] = None,
    weekly: Annotated[bool, typer.Option("--weekly")] = False,
) -> None:
    ledger_path = ledger or (repo_root() / "data" / "usage-ledger.jsonl")

    if weekly:
        raise typer.Exit(print_weekly(ledger_path))

    if not profile or not since:
        print(
            "error: --profile and --since are required unless --weekly is given",
            file=sys.stderr,
        )
        raise typer.Exit(2)

    until = until or datetime.now().astimezone()
    if since.tzinfo is None:
        since = since.astimezone()
    since = since.astimezone(UTC)
    until = until.astimezone(UTC)

    usage = collect_claude_usage(worktree, since, until)
    if usage.calls == 0:
        print(f"usage: {profile} no transcripts found in window")
        return
    line, record = report_claude(usage, label)

    print(line)
    record["timestamp"] = datetime.now(UTC).isoformat()
    record["worktree"] = str(worktree)
    append_ledger(ledger_path, record)


if __name__ == "__main__":
    app()
