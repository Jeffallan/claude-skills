"""Owner decisions: `<git-dir>/ticket-guard/decisions.jsonl`, the only source of owner-only statuses.

`export` copies a spec's records to `<spec>/review/decisions.jsonl` for git history; the gate never reads
that copy. `import` (attended only) is how the owner brings them into another clone's store.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ticket_guard import evidence, marker, settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import append_jsonl, guard_dir, read_jsonl

# answered: a PR-feedback question replied to with no code change (answer 83).
# revoke: withdraws the row's earlier decision; it is appended like any record, so the history stays.
REVOKE = "revoke"
STATUSES = ("wontfix", "rejection-accepted", "accepted", "answered", REVOKE)
# No session id is exported to Bash (R6 proposal), so take it from the caller, then the environment.
SESSION_ENV = ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID")


def path(cwd: Path) -> Path:
    return guard_dir(cwd) / "decisions.jsonl"


def committed(cwd: Path, spec: str) -> Path:
    return settings.spec_dir(cwd, spec) / "review" / "decisions.jsonl"


def _refuse_goal(cwd: Path, command: str) -> dict[str, Any] | None:
    data = marker.read(cwd)
    if data is not None and data["mode"] == "goal":
        raise GuardError(f"{command} is attended only; a goal run is active (marker mode goal)")
    return data


def decide(
    cwd: Path,
    row: str,
    status: str,
    spec: str | None = None,
    session: str | None = None,
) -> dict[str, Any]:
    if status not in STATUSES:
        raise GuardError(f"status must be one of: {', '.join(STATUSES)}")
    data = _refuse_goal(cwd, "guard decide")
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


def for_spec(records: list[dict[str, Any]], spec: str) -> list[dict[str, Any]]:
    """The records that apply to this spec (records without a spec apply to every spec), oldest first.

    Sorted by `at` (stable for ties) so an imported older record never overrides a newer local one.
    """
    return sorted((r for r in records if r.get("spec") in (None, spec)), key=lambda r: r.get("at", ""))


def latest(cwd: Path, spec: str, records: list[dict[str, Any]] | None = None) -> dict[str, str]:
    """Row -> its most recent status for this spec, from the local store unless `records` is given.

    A row whose most recent record is a revoke has no owner decision, so it is left out.
    """
    rows = {r["row"]: r["status"] for r in for_spec(read_jsonl(path(cwd)) if records is None else records, spec)}
    return {row: status for row, status in rows.items() if status != REVOKE}


def export(cwd: Path, spec: str) -> tuple[Path, int]:
    """Overwrite `<spec>/review/decisions.jsonl` with every local record the gate reads for this spec."""
    records = for_spec(read_jsonl(path(cwd)), spec)
    out = committed(cwd, spec)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in records), encoding="utf-8")
    return out, len(records)


def _key(rec: dict[str, Any]) -> tuple[Any, ...]:
    return rec.get("row"), rec.get("status"), rec.get("spec"), rec.get("at")


def import_(cwd: Path, spec: str) -> list[dict[str, Any]]:
    """Append each committed record the local store lacks; attended only, like `decide`."""
    _refuse_goal(cwd, "guard decisions import")
    source = committed(cwd, spec)
    if not source.is_file():
        raise GuardError(f"no exported decisions at {source}")
    incoming = read_jsonl(source)
    for rec in incoming:  # check every record before appending any
        if rec.get("status") not in STATUSES or not rec.get("row"):
            raise GuardError(f"{source} holds a record that is not an owner decision: {rec}")
    have = {_key(r) for r in read_jsonl(path(cwd))}
    added = []
    for rec in incoming:
        if _key(rec) in have:
            continue
        rec = {**rec, "imported_from": str(source)}
        append_jsonl(path(cwd), rec)
        have.add(_key(rec))
        added.append(rec)
    return added
