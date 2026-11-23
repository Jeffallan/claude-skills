"""`guard block`: save the ticket's work, restore the start SHA, write the Blocked row (and an Open question), clear the marker."""

from __future__ import annotations

import contextlib
from pathlib import Path
import tarfile
from typing import Any

from ticket_guard import evidence, marker, plan
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import git, guard_dir, head, top


def _save_and_restore(cwd: Path, ticket: str, start_sha: str, plan_file: Path) -> dict[str, Any]:
    root = top(cwd)
    rel_plan = plan_file.relative_to(root).as_posix()
    out = guard_dir(cwd) / "blocked"
    out.mkdir(parents=True, exist_ok=True)
    patch = out / f"{ticket}.patch"
    diff = git(cwd, "diff", "--binary", start_sha, "--", ".", f":(exclude){rel_plan}")
    patch.write_text(diff + "\n" if diff else "", encoding="utf-8")
    untracked = [p for p in git(cwd, "ls-files", "--others", "--exclude-standard").splitlines() if p]
    tarball = None
    if untracked:
        tarball = out / f"{ticket}-untracked.tar.gz"
        with tarfile.open(tarball, "w:gz") as tar:
            for rel in untracked:
                tar.add(root / rel, arcname=rel)
    plan_text = plan_file.read_text(encoding="utf-8") if plan_file.is_file() else None
    git(cwd, "reset", "-q", "--hard", start_sha)
    for rel in untracked:
        (root / rel).unlink(missing_ok=True)
    if plan_text is not None:
        plan_file.write_text(plan_text, encoding="utf-8")
    return {
        "patch": str(patch),
        "untracked": str(tarball) if tarball else None,
        "files": untracked,
    }


def _lost_start(cwd: Path, ticket: str) -> str | None:
    """The start SHA of a marker lost mid-ticket: the last marker_* event is not a clear."""
    recs = [r for r in evidence.records(cwd, ticket) if r["event"].startswith("marker_")]
    if not recs or recs[-1]["event"] == "marker_clear":
        return None
    starts = [r for r in recs if r["event"] == "marker_start"]
    return starts[-1].get("start_sha") if starts else None


def block(
    cwd: Path,
    ticket: str,
    reason: str,
    spec: str | None = None,
    start: str | None = None,
    question: str | None = None,
) -> dict[str, Any]:
    data = marker.read(cwd)
    own = data is not None and data["ticket"] == ticket
    if own:
        start = data["start_sha"]
    elif start and data is not None:
        raise GuardError(f"ticket {data['ticket']} holds the marker; --start would restore over its work")
    elif data is None:
        start = start or _lost_start(cwd, ticket)
    if start and head(cwd) != git(cwd, "rev-parse", start):
        raise GuardError(
            f"HEAD has moved past the start SHA {start[:12]} of ticket {ticket}; "
            "nothing was changed. A ticket commits only in ticket:complete, so check `git log` by hand."
        )
    spec = spec or (data["spec"] if own else None) or plan.find_spec(cwd, ticket)
    plan_file = plan.plan_path(cwd, spec)
    if ticket not in plan.status_rows(plan_file):
        raise GuardError(f"ticket {ticket} has no row in the Completion Status table of {plan_file}")
    if question:
        plan.questions_table(plan_file)  # refuse before anything changes
    saved = _save_and_restore(cwd, ticket, start, plan_file) if start else {}
    plan.set_status(plan_file, ticket, plan.BLOCKED, reason)
    if question:
        plan.add_question(plan_file, ticket, question, data["mode"] if data else "attended")
    record = evidence.append(cwd, ticket, "blocked", reason=reason, spec=spec, **saved)
    if own:
        marker.clear(cwd)
    elif saved:
        evidence.append(cwd, ticket, "marker_clear", lost=True)
    committed = False
    if marker.read(cwd) is None:  # with a marker the row would land in that ticket's commit
        with contextlib.suppress(GuardError):  # other files dirty: leave the row for `guard commit-plan`
            committed = plan.commit(cwd, spec)
    return record | {"committed": committed}
