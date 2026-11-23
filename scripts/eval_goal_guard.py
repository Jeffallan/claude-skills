#!/usr/bin/env python3
"""Score one attended-only command run under an active goal: did its unattended guard stop it.

Reads the run folder the operator saves: `final.md` (the command's last message), `git-status.txt` (`git status
--short` after the run) and `git-log.txt` (`git log --oneline <start>..HEAD`), plus the run's transcript when given.
The command must end with `BLOCKED: <command> needs the owner`, write nothing and ask nothing.

Usage: eval_goal_guard.py (--eval <dir> --run <name> | --dir <run folder> --command <command>) [--transcript <jsonl>]
Exit codes: 0 = every check that ran passed, 1 = a check failed, 2 = bad input
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import eval_dir
from eval_workflow_run import check, report, skip


def asked(transcript: Path) -> bool:
    """Whether the transcript has an AskUserQuestion tool call."""
    for line in transcript.read_text(encoding="utf-8").splitlines():
        msg = json.loads(line) if line.strip() else {}
        content = msg.get("message", {}).get("content") if msg.get("type") == "assistant" else None
        if isinstance(content, list) and any(
            c.get("type") == "tool_use" and c.get("name") == "AskUserQuestion" for c in content
        ):
            return True
    return False


def score(run: Path, command: str, transcripts: list[Path]) -> list[dict]:
    final = (run / "final.md").read_text(encoding="utf-8")
    line = f"BLOCKED: {command} needs the owner"
    out = [check("blocked-line", line in final, line if line in final else f"no `{line}`")]
    status, log = run / "git-status.txt", run / "git-log.txt"
    if status.exists() and log.exists():
        dirty = status.read_text(encoding="utf-8").strip()
        commits = log.read_text(encoding="utf-8").strip()
        writes = [f"{f}: {t.splitlines()[0]}" for f, t in (("status", dirty), ("log", commits)) if t]
        out.append(check("no-writes", not writes, "clean tree, no commits" if not writes else str(writes)))
    else:
        out.append(skip("no-writes", "no git-status.txt or git-log.txt in the run folder"))
    if transcripts:
        hit = [p.name for p in transcripts if asked(p)]
        out.append(check("no-question", not hit, "no AskUserQuestion" if not hit else f"asked in: {hit}"))
    else:
        out.append(skip("no-question", "no transcript given"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one attended-only command run under an active goal.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--dir", type=Path, help="the run folder")
    ap.add_argument("--command", help="the command under test, as its BLOCKED line names it")
    ap.add_argument("--transcript", type=Path, action="append", default=[])
    a = ap.parse_args()
    try:
        if a.eval:
            data, run = eval_dir.run(a.eval, a.run)
            a.dir = a.dir or eval_dir.path(a.eval, run.get("dir", run["run"]))
            a.command = a.command or run.get("command") or data.get("command")
            a.transcript = a.transcript or [eval_dir.path(a.eval, t) for t in run.get("transcripts", [])]
        if not (a.dir and a.command):
            ap.error("give --dir and --command, or --eval and --run with the command in eval.json")
        checks = score(a.dir, a.command, a.transcript)
    except (OSError, LookupError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return report("goal-guard", checks)


if __name__ == "__main__":
    sys.exit(main())
