"""The per-ticket evidence record: `<git-dir>/ticket-guard/evidence/<ticket>.jsonl`, written only by the runtime."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ticket_guard.gitutil import append_jsonl, guard_dir, read_jsonl


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def path(cwd: Path, ticket: str) -> Path:
    return guard_dir(cwd) / "evidence" / f"{ticket}.jsonl"


def append(cwd: Path, ticket: str, event: str, /, **fields: Any) -> dict[str, Any]:
    record = {"event": event, "at": now(), **fields}
    append_jsonl(path(cwd, ticket), record)
    return record


def tickets(cwd: Path) -> list[str]:
    """Every ticket with an evidence record in this repo."""
    return sorted(p.stem for p in (guard_dir(cwd) / "evidence").glob("*.jsonl"))


def records(cwd: Path, ticket: str) -> list[dict[str, Any]]:
    return read_jsonl(path(cwd, ticket))


def current(cwd: Path, ticket: str) -> list[dict[str, Any]]:
    """The records of the ticket's latest attempt: from its last `marker_start` on.

    The file stays append-only for audit; a rerun after `guard block` is judged only by its own records.
    """
    recs = records(cwd, ticket)
    starts = [i for i, r in enumerate(recs) if r["event"] == "marker_start"]
    return recs[starts[-1] :] if starts else recs
