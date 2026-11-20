"""`guard run-batches`: headless next-batch goal runs in one session, /compact between them (answer 87)."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from ticket_guard import plan, review, settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import top

# Writes-only deny set (answer 98), passed on every `claude -p` call. Provisional: the pilot
# confirms each pattern. Tracker MCP write tools differ per tracker, so they come from goal.deny.
DENY = (
    "AskUserQuestion",
    "Bash(git push:*)",
    "Bash(git tag:*)",
    # A goal run once dropped and squashed spec-branch commits (pilot F7); guard block resets
    # through its own subprocess, not the Bash tool.
    "Bash(git rebase:*)",
    "Bash(git reset:*)",
    "Bash(git commit --amend:*)",
    *(
        f"Bash(gh pr {verb}:*)"
        for verb in (
            "create",
            "merge",
            "comment",
            "review",
            "edit",
            "close",
            "reopen",
            "ready",
        )
    ),
    *(
        f"Bash(gh issue {verb}:*)"
        for verb in (
            "create",
            "edit",
            "close",
            "comment",
            "reopen",
            "delete",
            "transfer",
        )
    ),
    # Any method or field flag, attached or not (-XPOST, -ftitle=x; -f implies POST): GH5.
    # The space before the flag keeps a path such as repos/o/my-fork from matching.
    *(
        f"Bash(gh api {gap}{flag}*)"
        for flag in ("-X", "-f", "-F", "--method", "--field", "--raw-field", "--input")
        for gap in ("", "* ")
    ),
    # A goal run has no reason to change a Project; list, view, field-list and item-list read.
    *(
        f"Bash(gh project {verb}:*)"
        for verb in (
            "close",
            "copy",
            "create",
            "delete",
            "edit",
            "field-create",
            "field-delete",
            "item-add",
            "item-archive",
            "item-create",
            "item-delete",
            "item-edit",
            "link",
            "mark-template",
            "unlink",
        )
    ),
    "Bash(gh release:*)",
    "Bash(*guard.pyz* decide *)",
    "Bash(*ticket_guard* decide *)",
    "Bash(*runtime* decide *)",
    "Bash(*guard.pyz* decisions import*)",
    "Bash(*ticket_guard* decisions import*)",
    "Bash(*runtime* decisions import*)",
)
SETTLED = (*review.FINISHED, plan.BLOCKED)


def claude_args(cwd: Path) -> list[str]:
    """Flags for every `claude -p` call; the variadic tool lists go last."""
    mode = settings.get(cwd, "goal.permissionMode")
    extra = settings.get(cwd, "goal.extraArgs") or []
    if not isinstance(mode, str):
        raise GuardError("goal.permissionMode must be a string")
    if not isinstance(extra, list) or not all(isinstance(a, str) for a in extra):
        raise GuardError("goal.extraArgs must be a list of strings")
    rules = [*DENY, *(settings.get(cwd, "goal.deny") or [])]
    allow = settings.get(cwd, "goal.allow") or []
    return (
        ["--permission-mode", mode, *extra]
        + [arg for rule in rules for arg in ("--disallowedTools", rule)]
        + [arg for rule in allow for arg in ("--allowedTools", rule)]
    )


def kickoff(goal_prompt: str, tickets: list[str]) -> str:
    """The next-batch kickoff (wording provisional; section 8 leaves it open)."""
    return (
        f"/goal Every condition in <done_when> in {goal_prompt} holds for the next batch "
        f"(tickets {', '.join(tickets)}), each Done or Blocked with its reason, and your latest message "
        "shows the evidence, or your latest message starts with BLOCKED: and names a spec-wide stop from <stops> "
        "in that file. Do only these tickets, in Execution Order, update the Completion Status table, "
        "then stop. Read that file first, and again after any compaction."
    )


def _settled(state: str) -> bool:
    return state.startswith(SETTLED)


def _state(plan_file: Path) -> dict[str, str]:
    return {t: (row[1] if len(row) > 1 else "") for t, row in plan.status_rows(plan_file).items()}


def _claude(cwd: Path, argv: list[str]) -> dict[str, Any]:
    proc = subprocess.run(argv, cwd=top(cwd), capture_output=True, text=True, check=False)
    try:
        data = json.loads(proc.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise GuardError(
            f"could not read claude's final message (exit {proc.returncode}): {proc.stderr.strip()[-500:]}"
        ) from exc
    return data if isinstance(data, dict) else {}


def report(plan_file: Path) -> str:
    state = _state(plan_file)
    groups: dict[str, list[str]] = {"Blocked": [], "Done": [], "Not done": []}
    for ticket, status in state.items():
        key = "Blocked" if status.startswith(plan.BLOCKED) else "Done" if _settled(status) else "Not done"
        note = plan.status_rows(plan_file)[ticket][3:4]
        groups[key].append(f"- {ticket}: {status}" + (f" ({note[0]})" if key == "Blocked" and note else ""))
    return "\n".join(f"{k}:\n" + "\n".join(v) for k, v in groups.items() if v)


def run_batches(cwd: Path, spec: str, batch_size: int | None = None, claude: str = "claude") -> int:
    spec_dir = settings.spec_dir(cwd, spec)
    plan_file, goal_file = (
        spec_dir / "implementation-plan.md",
        spec_dir / "goal-prompt.md",
    )
    for need in (plan_file, goal_file):
        if not need.is_file():
            raise GuardError(f"run-batches needs {need}")
    size = batch_size or int(settings.get(cwd, "goal.batchSize"))
    goal_rel = goal_file.relative_to(top(cwd)).as_posix()
    deny, session = claude_args(cwd), None
    while True:
        state = _state(plan_file)
        remaining = [t for t in plan.execution_order(plan_file) if not _settled(state.get(t, ""))]
        if not remaining:
            print("every ticket is Done or Blocked\n" + report(plan_file))
            if plan.commit(cwd, spec):
                print(f"committed the plan's Blocked rows: docs({spec}): record Blocked rows in the plan")
            return 0
        if session is not None:
            _claude(
                cwd,
                [
                    claude,
                    "-p",
                    "/compact",
                    "--output-format",
                    "json",
                    "--resume",
                    session,
                    *deny,
                ],
            )
        batch = remaining[:size]
        print(f"batch: {', '.join(batch)}", flush=True)
        print(
            "running: a headless Claude session is working on this batch. "
            "Nothing prints until it ends, which can take a while.",
            flush=True,
        )
        resume = ["--resume", session] if session else []
        data = _claude(
            cwd,
            [
                claude,
                "-p",
                kickoff(goal_rel, batch),
                "--output-format",
                "json",
                *resume,
                *deny,
            ],
        )
        session = session or data.get("session_id")
        message = str(data.get("result") or "").strip()
        # Judge the final message, never the exit status: a -p goal run can report success with
        # the goal unmet after the Stop-hook block cap (answer 63).
        if message.startswith("BLOCKED:"):
            print(f"run stopped:\n{message}\n" + report(plan_file), file=sys.stderr)
            return 1
        after = _state(plan_file)
        if not any(_settled(after.get(t, "")) for t in batch):
            print(
                "no ticket in the batch reached Done or Blocked; stopping. Final message:\n" + message,
                file=sys.stderr,
            )
            return 1
        if session is None:
            raise GuardError("claude returned no session_id; cannot resume the same session")
