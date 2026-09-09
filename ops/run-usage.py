#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Measure what one publish tick cost in tokens, for whichever agent ran it.

Nothing logs this today: the pipeline picks its agent profile
(`ops/publish-lib.sh`) and pins its model, but nobody records what a tick
actually spent, so the tick rate can't be tuned against a subscription's weekly
allowance and a run-shrinking change can't be measured before/after.

Two profiles, two transcript formats, because the two subscriptions log
differently:

- `claude-sub`: `~/.claude/projects/<encoded worktree>/*.jsonl`, one line per
  message. Sum `message.usage` on every `message.role == "assistant"` line.
  Subagent transcripts live under a subdirectory of the same project dir
  (`<session>/subagents/*.jsonl`), so the glob is recursive.
- `grok-sub`: `~/.grok/sessions/<url-encoded worktree>/<session-id>/
  updates.jsonl`. Only the LAST `"usage":{...}` object in the file matters ---
  each `turn_completed` update carries the session's running total, so the
  last one IS the session total, not one turn's slice.

Usage:
  ops/run-usage.py --profile claude-sub --since 2026-09-10T07:30:00+10:00 \\
      --worktree /home/ben/projects/slop-university-press
  ops/run-usage.py --profile grok-sub --since ... --until ...
  ops/run-usage.py --weekly
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import urllib.parse
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
GROK_SESSIONS_DIR = Path.home() / ".grok" / "sessions"


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


def encode_grok_worktree(worktree: Path) -> str:
    """Percent-encoded, e.g. /home/ben/x -> %2Fhome%2Fben%2Fx."""
    return urllib.parse.quote(str(worktree), safe="")


def in_window(mtime: float, since: datetime, until: datetime) -> bool:
    ts = datetime.fromtimestamp(mtime, tz=timezone.utc)
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
                    if isinstance(msg_usage, dict):
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


@dataclass
class GrokUsage:
    calls: int = 0
    input_tokens: int = 0
    cached_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    sessions: int = 0


def last_usage_object(text: str) -> dict | None:
    """The final `"usage":{...}` in the file --- each `turn_completed` update
    carries the session's running total, so the last one supersedes every
    earlier one rather than adding to it."""
    marker = '"usage":{'
    idx = text.rfind(marker)
    if idx == -1:
        return None
    start = idx + len('"usage":')
    decoder = json.JSONDecoder()
    obj, _ = decoder.raw_decode(text, start)
    return obj


def collect_grok_usage(worktree: Path, since: datetime, until: datetime) -> GrokUsage:
    sessions_dir = GROK_SESSIONS_DIR / encode_grok_worktree(worktree)
    usage = GrokUsage()
    if not sessions_dir.is_dir():
        return usage

    for session_dir in sessions_dir.iterdir():
        if not session_dir.is_dir():
            continue
        try:
            mtime = session_dir.stat().st_mtime
        except OSError:
            continue
        if not in_window(mtime, since, until):
            continue

        updates_path = session_dir / "updates.jsonl"
        if not updates_path.is_file():
            continue

        last = last_usage_object(updates_path.read_text())
        if last is None:
            continue

        usage.sessions += 1
        usage.calls += last.get("modelCalls", 0) or 0
        usage.input_tokens += last.get("inputTokens", 0) or 0
        usage.cached_tokens += last.get("cachedReadTokens", 0) or 0
        usage.output_tokens += last.get("outputTokens", 0) or 0
        usage.cost_usd += (last.get("costUsdTicks", 0) or 0) / 1e10

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


def report_grok(usage: GrokUsage, label: str | None) -> tuple[str, dict]:
    line = (
        f"usage: grok-sub calls={usage.calls} "
        f"input={human(usage.input_tokens)} "
        f"cached={human(usage.cached_tokens)} "
        f"output={human(usage.output_tokens)} "
        f"cost=${usage.cost_usd:.2f}"
    )
    record = {
        "profile": "grok-sub",
        "label": label,
        "calls": usage.calls,
        "input_tokens": usage.input_tokens,
        "cached_tokens": usage.cached_tokens,
        "output_tokens": usage.output_tokens,
        "cost_usd": usage.cost_usd,
        "sessions": usage.sessions,
    }
    return line, record


def print_weekly(ledger_path: Path) -> int:
    if not ledger_path.is_file():
        print(f"usage: no ledger at {ledger_path}")
        return 0

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
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
            totals[profile]["cost_usd_ticks"] += int(record.get("cost_usd", 0) * 1e10)

    if not totals:
        print("usage: weekly totals: no ledger entries in the trailing 7 days")
        return 0

    for profile, counter in totals.items():
        cost_usd = counter["cost_usd_ticks"] / 1e10
        print(
            f"usage: weekly {profile} runs={runs[profile]} "
            f"calls={counter['calls']} "
            f"context_sent={human(counter['context_sent'])} "
            f"output={human(counter['output_tokens'])} "
            f"cost=${cost_usd:.2f}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["claude-sub", "grok-sub"])
    parser.add_argument("--since", type=parse_time)
    parser.add_argument("--until", type=parse_time)
    parser.add_argument(
        "--worktree",
        type=Path,
        default=Path("/home/ben/projects/slop-university-press"),
    )
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--label")
    parser.add_argument("--weekly", action="store_true")
    args = parser.parse_args()

    ledger_path = args.ledger or (repo_root() / "data" / "usage-ledger.jsonl")

    if args.weekly:
        return print_weekly(ledger_path)

    if not args.profile or not args.since:
        parser.error("--profile and --since are required unless --weekly is given")

    until = args.until or datetime.now().astimezone()
    since = args.since
    if since.tzinfo is None:
        since = since.astimezone()
    since = since.astimezone(timezone.utc)
    until = until.astimezone(timezone.utc)

    if args.profile == "claude-sub":
        usage = collect_claude_usage(args.worktree, since, until)
        if usage.calls == 0:
            print(f"usage: {args.profile} no transcripts found in window")
            return 0
        line, record = report_claude(usage, args.label)
    else:
        usage = collect_grok_usage(args.worktree, since, until)
        if usage.sessions == 0:
            print(f"usage: {args.profile} no transcripts found in window")
            return 0
        line, record = report_grok(usage, args.label)

    print(line)
    record["timestamp"] = datetime.now(timezone.utc).isoformat()
    record["worktree"] = str(args.worktree)
    append_ledger(ledger_path, record)
    return 0


if __name__ == "__main__":
    sys.exit(main())
