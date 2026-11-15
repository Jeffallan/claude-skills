"""Hook entry points for the companion skill. With no marker, or a marker this session
did not claim, every hook prints nothing and exits 0."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ticket_guard import evidence, marker, runs, settings
from ticket_guard.gitutil import top

EDIT_TOOLS = {
    "Write": "file_path",
    "Edit": "file_path",
    "MultiEdit": "file_path",
    "NotebookEdit": "notebook_path",
}
CLEAR = "guard marker clear"


def project_dir(payload: dict[str, Any]) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or os.getcwd())


def _rel(cwd: Path, file_path: str) -> str | None:
    path = Path(file_path)
    if not path.is_absolute():
        path = Path(cwd) / path
    try:
        return path.resolve().relative_to(top(cwd).resolve()).as_posix()
    except ValueError:
        return None


def _decision(kind: str, reason: str) -> str:
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": kind,
                "permissionDecisionReason": reason,
            }
        }
    )


def _frozen_by(cwd: Path, ticket: str, rel: str) -> str | None:
    """The ticket whose latest valid RED froze `rel`: the current ticket first, then any other with evidence."""
    for owner in [ticket, *(t for t in evidence.tickets(cwd) if t != ticket)]:
        red = runs.latest(evidence.current(cwd, owner), "red")
        if red is not None and rel in red["test_files"]:
            return owner
    return None


def _edit_target(payload: dict[str, Any]) -> tuple[Path, dict[str, Any], str] | None:
    """(project dir, claimed marker, repo-relative path) for an edit-tool call this session enforces."""
    cwd = project_dir(payload)
    data = marker.for_hook(cwd, payload.get("session_id", ""))
    key = EDIT_TOOLS.get(payload.get("tool_name", ""))
    if data is None or key is None:
        return None
    rel = _rel(cwd, (payload.get("tool_input") or {}).get(key, ""))
    return None if rel is None else (cwd, data, rel)


def post_tool_use(payload: dict[str, Any]) -> str | None:
    """A write to a frozen file ran, so the owner approved the ask: record it as an applied amendment."""
    target = _edit_target(payload)
    if target is None:
        return None
    cwd, data, rel = target
    ticket = data["ticket"]
    owner = _frozen_by(cwd, ticket, rel)
    if owner is None:
        return None
    tool = payload.get("tool_name")
    evidence.append(cwd, ticket, "amendment_applied", file=rel, tool=tool, owner_ticket=owner)
    if owner != ticket:
        evidence.append(cwd, owner, "amendment_applied", file=rel, tool=tool, from_ticket=ticket)
    return None


def pre_tool_use(payload: dict[str, Any]) -> str | None:
    target = _edit_target(payload)
    if target is None:
        return None
    cwd, data, rel = target
    ticket, goal = data["ticket"], data["mode"] == "goal"
    tickets_dir = settings.get(cwd, "text.ticketsDir")  # provisional key (answer 98)
    if goal and tickets_dir and (rel + "/").startswith(tickets_dir.rstrip("/") + "/"):
        return _decision(
            "deny",
            f"goal mode: text tickets under {tickets_dir} are written only by spec:complete "
            f"(ticket {ticket}). Add proposed changes to the plan's Proposed tracker changes.",
        )
    owner = _frozen_by(cwd, ticket, rel)
    if owner is None:
        return None
    where = f"marker {marker.path(cwd)}; if it is stale, clear it with `{CLEAR}`"
    if owner != ticket:
        if goal:
            return _decision(
                "deny",
                f"{rel} is frozen after RED for earlier ticket {owner}. Never weaken a test to get a pass; "
                f"if it contradicts the spec, block ticket {ticket} with `guard block`. ({where})",
            )
        tool = payload.get("tool_name")
        evidence.append(cwd, ticket, "amendment_requested", file=rel, tool=tool, owner_ticket=owner)
        evidence.append(cwd, owner, "amendment_requested", file=rel, tool=tool, from_ticket=ticket)
        return _decision(
            "ask",
            f"{rel} is frozen after RED for earlier ticket {owner}. Approve only as a deliberate test amendment. ({where})",
        )
    if goal:
        return _decision(
            "deny",
            f"{rel} is frozen after RED for ticket {ticket}. Never weaken a test to get a pass; "
            f"if the test contradicts the spec, block the ticket with `guard block`. ({where})",
        )
    evidence.append(cwd, ticket, "amendment_requested", file=rel, tool=payload.get("tool_name"))
    return _decision(
        "ask",
        f"{rel} is frozen after RED for ticket {ticket}. Approve only as a deliberate test amendment. ({where})",
    )


def next_step(cwd: Path, data: dict[str, Any]) -> str:
    ticket = data["ticket"]
    recs = evidence.current(cwd, ticket)
    green = runs.latest(recs, "green", valid_only=False)
    if runs.latest(recs, "red") is None:
        return "write the failing tests, then record RED with `guard run red -- <test command>`"
    if green is None or green["exit_code"] != 0 or green.get("tests_changed"):
        return "implement until the tests pass, then record GREEN with `guard run green -- <command>`"
    return f"run ticket:complete {ticket}"


def session_start(payload: dict[str, Any]) -> str | None:
    if payload.get("source") != "compact":
        return None
    cwd = project_dir(payload)
    data = marker.for_hook(cwd, payload.get("session_id", ""))
    if data is None:
        return None
    spec_dir = settings.spec_dir(cwd, data["spec"]).relative_to(top(cwd)).as_posix()
    return (
        f"ticket-guard: ticket {data['ticket']} of spec {data['spec']} is in progress in "
        f"{data['mode']} mode on branch {data['branch']} (start SHA {data['start_sha'][:12]}).\n"
        f"Next step: {next_step(cwd, data)}.\n"
        f"Re-read {spec_dir}/goal-prompt.md and rebuild state from the Completion Status "
        f"table and `git log`, never from memory."
    )


def _rerun_command(cwd: Path, ticket: str) -> list[str] | None:
    recs = evidence.current(cwd, ticket)
    if runs.latest(recs, "red") is None:
        return None
    last = runs.latest(recs, "green", valid_only=False) or runs.latest(recs, "red")
    return last.get("argv") or [last["command"]]


def stop(payload: dict[str, Any]) -> str | None:
    """Goal mode: re-run GREEN and block while it fails, up to guard.greenFailLimit times.

    Ignores stop_hook_active on purpose: inside /goal it is true on nearly every stop
    (answer 84). A final message starting with BLOCKED: always passes.
    """
    cwd = project_dir(payload)
    data = marker.for_hook(cwd, payload.get("session_id", ""))
    if data is None:
        return None
    ticket = data["ticket"]
    message = (payload.get("last_assistant_message") or "").lstrip()
    if message.startswith("BLOCKED:"):
        first = message.splitlines()[0][:500]
        marker.update(cwd, blocked_at=evidence.now(), blocked_stop=first)
        evidence.append(cwd, ticket, "blocked_stop", message=first)
        return None
    if data["mode"] != "goal":
        return None
    command = _rerun_command(cwd, ticket)
    if command is None:
        return None
    rec = runs.green(cwd, command, source="stop-hook", echo=False)
    if rec["exit_code"] == 0 and not rec["tests_changed"]:
        marker.update(cwd, green_failures=0, green_failed_at=None)
        return None
    count = data.get("green_failures", 0) + 1
    limit = int(settings.get(cwd, "guard.greenFailLimit"))
    if count > limit:
        fields: dict[str, Any] = {"green_failures": count}
        if not data.get("green_failed_at"):
            fields["green_failed_at"] = evidence.now()
            evidence.append(cwd, ticket, "green_failure", count=count, command=rec["command"])
        marker.update(cwd, **fields)
        return None
    marker.update(cwd, green_failures=count)
    problem = (
        "the ticket's test files changed since RED (they are frozen)"
        if rec["tests_changed"]
        else f"`{rec['command']}` exits {rec['exit_code']}"
    )
    log_tail = Path(rec["log_path"]).read_text(encoding="utf-8")[-1500:]
    reason = (
        f"ticket-guard: GREEN is failing for ticket {ticket} ({count} of {limit}): {problem}. "
        f"Fix the implementation, not the tests, until it passes. If you can't, run "
        f'`guard block {ticket} "<reason>"` and continue with the next ticket.\n'
        f"Log {rec['log_path']}, last lines:\n{log_tail}"
    )
    return json.dumps({"decision": "block", "reason": reason})
