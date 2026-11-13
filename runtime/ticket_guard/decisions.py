"""Owner decisions: `<git-dir>/ticket-guard/decisions.jsonl`, the only source of owner-only statuses."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from ticket_guard import evidence, marker
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import append_jsonl, guard_dir, read_jsonl

# answered: a PR-feedback question replied to with no code change (answer 83).
STATUSES = ("wontfix", "rejection-accepted", "accepted", "answered")
# No session id is exported to Bash (R6 proposal), so take it from the caller, then the environment.
SESSION_ENV = ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID")


def path(cwd: Path) -> Path:
    return guard_dir(cwd) / "decisions.jsonl"


def decide(
    cwd: Path,
    row: str,
    status: str,
    spec: str | None = None,
    session: str | None = None,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise GuardError(f"status must be one of: {', '.join(STATUSES)}")
    data = marker.read(cwd)
    if data is not None and data["mode"] == "goal":
        raise GuardError("guard decide is attended only; a goal run is active (marker mode goal)")
    session = session or next((os.environ[k] for k in SESSION_ENV if os.environ.get(k)), None)
    if session is None and data is not None:
        session = data.get("session_id") or None
    record = {
        "row": row,
        "status": status,
        "spec": spec or (data or {}).get("spec"),
        "session_id": session or "unknown",
        "at": evidence.now(),
    }
    append_jsonl(path(cwd), record)
    return record


def latest(cwd: Path, spec: str) -> dict[str, str]:
    """Row -> its most recent status, for this spec (records without a spec apply to every spec)."""
    out: dict[str, str] = {}
    for rec in read_jsonl(path(cwd)):
        if rec.get("spec") in (None, spec):
            out[rec["row"]] = rec["status"]
    return out
