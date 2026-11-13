"""Read and edit the Completion Status and Execution Order tables of an implementation plan."""

from __future__ import annotations

from pathlib import Path
import re

from ticket_guard import settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import git, git_dir, top

CELL_SPLIT = re.compile(r"(?<!\\)\|")
DONE, BLOCKED = "Done", "Blocked"


def cells(line: str) -> list[str]:
    return [c.strip() for c in CELL_SPLIT.split(line.strip().strip("|"))]


def _table(lines: list[str], heading: str) -> list[int]:
    """Line indexes of the data rows of the first table under `## <heading>`."""
    found, rows, seen_table = False, [], False
    for index, line in enumerate(lines):
        if line.startswith("## "):
            if found:
                break
            found = line[3:].strip().lower() == heading.lower()
            continue
        if not found:
            continue
        if line.lstrip().startswith("|"):
            seen_table = True
            rows.append(index)
        elif seen_table:
            break
    return rows[2:]  # header and separator


def status_rows(path: Path) -> dict[str, list[str]]:
    return status_rows_text(path.read_text(encoding="utf-8"))


def status_rows_text(text: str) -> dict[str, list[str]]:
    lines = text.splitlines()
    return {cells(lines[i])[0]: cells(lines[i]) for i in _table(lines, "Completion Status")}


def execution_order(path: Path) -> list[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    order = [cells(lines[i])[1] for i in _table(lines, "Execution Order")]
    return order or list(status_rows(path))


def set_status(path: Path, ticket: str, status: str, notes: str, date: str = "-") -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for index in _table(lines, "Completion Status"):
        row = cells(lines[index])
        if row[0] == ticket:
            row[1:4] = [status, date, notes.replace("|", "\\|")]
            lines[index] = "| " + " | ".join(row) + " |"
            path.write_text(
                "\n".join(lines) + ("\n" if text.endswith("\n") else ""),
                encoding="utf-8",
            )
            return
    raise GuardError(f"ticket {ticket} has no row in the Completion Status table of {path}")


def plan_path(cwd: Path, spec: str) -> Path:
    return settings.spec_dir(cwd, spec) / "implementation-plan.md"


def find_spec(cwd: Path, ticket: str) -> str:
    """The one spec under todo/ whose plan lists `ticket`."""
    todo = top(cwd) / settings.get(cwd, "specsRoot") / "todo"
    hits = [p.parent.name for p in sorted(todo.glob("*/implementation-plan.md")) if ticket in status_rows(p)]
    if len(hits) != 1:
        where = ", ".join(hits) if hits else "no plan under " + str(todo)
        raise GuardError(f"cannot tell which spec ticket {ticket} belongs to ({where}); pass --spec")
    return hits[0]


def commit(cwd: Path, spec: str) -> bool:
    """Commit Blocked rows that guard block left uncommitted. Only the plan may be dirty."""
    found = git_dir(cwd)
    if found and (found / "ticket-guard" / "marker.json").is_file():
        raise GuardError("a ticket is in progress (marker exists); finish or block it first")
    rel = plan_path(cwd, spec).relative_to(top(cwd)).as_posix()
    lines = git(cwd, "status", "--porcelain", "--untracked-files=all").splitlines()
    others = [line for line in lines if line[3:] != rel]
    if others:
        raise GuardError("only the plan may be uncommitted; also changed:\n" + "\n".join(others))
    if not lines:
        return False
    git(
        cwd,
        "commit",
        "-q",
        "-m",
        f"docs({spec}): record Blocked rows in the plan",
        "--",
        rel,
    )
    return True
