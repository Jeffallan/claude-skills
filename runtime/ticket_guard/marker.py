"""The ticket-guard marker at `<git-dir>/ticket-guard/marker.json` (R6 proposal, answers 46 to 52 and 100)."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from ticket_guard import evidence, settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import (
    branch,
    git,
    git_dir,
    guard_dir,
    head,
    top,
    write_json,
)

VERSION = 1
MODES = ("attended", "goal")


def path(cwd: Path) -> Path:
    return guard_dir(cwd) / "marker.json"


def read(cwd: Path) -> dict[str, Any] | None:
    found = git_dir(cwd)
    if found is None:
        return None
    file = found / "ticket-guard" / "marker.json"
    try:
        return json.loads(file.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None


def update(cwd: Path, **fields: Any) -> dict[str, Any]:
    data = read(cwd)
    if data is None:
        raise GuardError("no marker")
    data.update(fields)
    write_json(path(cwd), data)
    return data


def _dirty(cwd: Path, spec: str) -> list[str]:
    # The plan's Completion Status may hold uncommitted Blocked rows from guard block
    # (a ticket commits only in ticket:complete), so it never counts as dirty.
    plan = (settings.spec_dir(cwd, spec) / "implementation-plan.md").relative_to(top(cwd))
    lines = git(cwd, "status", "--porcelain", "--untracked-files=all").splitlines()
    return [line for line in lines if line[3:] != plan.as_posix()]


def start(cwd: Path, spec: str, ticket: str, mode: str) -> dict[str, Any]:
    """Write the marker for a clean start, or resume the same ticket on the same branch."""
    if mode not in MODES:
        raise GuardError(f"mode must be one of: {', '.join(MODES)}")
    current = read(cwd)
    if current is not None:
        if current["ticket"] == ticket and current["branch"] == branch(cwd):
            data = update(cwd, session_id="", claimed_at=None, mode=mode)
            evidence.append(cwd, ticket, "marker_resume", mode=mode)
            return data
        raise GuardError(
            f"a marker exists for ticket {current['ticket']} on branch {current['branch']} "
            f"(started {current['started_at']}); finish or block it, or clear it with "
            f"`guard marker clear`: {path(cwd)}"
        )
    dirty = _dirty(cwd, spec)
    if dirty:
        raise GuardError("working tree is not clean; commit or stash first:\n" + "\n".join(dirty))
    data = {
        "version": VERSION,
        "mode": mode,
        "spec": spec,
        "ticket": ticket,
        "branch": branch(cwd),
        "clean_start": True,
        "start_sha": head(cwd),
        "started_at": evidence.now(),
        "session_id": "",
        "claimed_at": None,
        "blocked_at": None,
        "blocked_stop": None,
        "green_failures": 0,
        "green_failed_at": None,
    }
    write_json(path(cwd), data)
    evidence.append(cwd, ticket, "marker_start", mode=mode, start_sha=data["start_sha"])
    return data


def claim(cwd: Path, session_id: str) -> dict[str, Any]:
    data = update(
        cwd,
        session_id=session_id,
        claimed_at=evidence.now(),
        blocked_at=None,
        blocked_stop=None,
    )
    evidence.append(cwd, data["ticket"], "marker_claim", session_id=session_id)
    return data


def for_hook(cwd: Path, session_id: str) -> dict[str, Any] | None:
    """The marker if this hook call should enforce it; None means stand down (exit 0).

    Claims an unclaimed marker for the calling session. Never deletes a marker.
    """
    data = read(cwd)
    if data is None or data.get("branch") != branch(cwd):
        return None
    if not data.get("session_id"):
        return claim(cwd, session_id)
    return data if data["session_id"] == session_id else None


def clear(cwd: Path) -> dict[str, Any] | None:
    data = read(cwd)
    if data is None:
        return None
    evidence.append(cwd, data["ticket"], "marker_clear")
    path(cwd).unlink()
    return data


def age_warning(cwd: Path, data: dict[str, Any]) -> str | None:
    if data.get("blocked_at"):
        return None
    hours = float(settings.get(cwd, "guard.markerWarnHours"))
    started = datetime.fromisoformat(data["started_at"])
    age = (datetime.now(UTC) - started).total_seconds() / 3600
    if age <= hours:
        return None
    return f"warning: the marker for ticket {data['ticket']} is older than {hours:g} hours ({age:.0f} h): {path(cwd)}"
