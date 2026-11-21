"""`guard spec-status`: where every spec stands, read from each spec branch and the default branch."""

from __future__ import annotations

from collections.abc import Callable
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
from typing import Any

from ticket_guard import marker, plan, review, settings, specindex
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import git

NEXT = {
    "Triaged": "spec:create {s}",
    "Drafting": "spec:create {s}",
    "Planned": "launch the goal run spec:create printed",
    "In progress": "let the goal run finish, or relaunch it",
    "Ready for review": "spec:review {s}",
    "In review": "spec:review {s}: fix or decide the blocking rows",
    "Ready to complete": "spec:complete {s}",
    "PR open": "spec:complete {s}",
    "Completed": "none",
}


def default_branch(cwd: Path) -> str:
    remote = git(cwd, "symbolic-ref", "--short", "refs/remotes/origin/HEAD", check=False)
    if "/" in remote:
        return remote.split("/", 1)[1]
    return "main" if git(cwd, "branch", "--list", "main").strip() else git(cwd, "rev-parse", "--abbrev-ref", "HEAD")


def _show(cwd: Path, ref: str, rel: str) -> str | None:
    out = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=cwd, capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else None


def _folder(cwd: Path, ref: str, root: str, spec: str) -> str | None:
    """The spec's folder on `ref`: todo/ or completed/, or None."""
    for where in ("todo", "completed"):
        if git(cwd, "ls-tree", "--name-only", ref, f"{root}/{where}/{spec}", check=False).strip():
            return f"{root}/{where}/{spec}"
    return None


def _specs_in(cwd: Path, ref: str, folder: str) -> set[str]:
    """Spec folder names under `folder` on `ref`, discovery/ excluded."""
    if _show(cwd, ref, folder) is None:
        return set()
    return {
        n.rsplit("/", 1)[-1]
        for n in git(cwd, "ls-tree", "-d", "--name-only", f"{ref}:{folder}").split()
        if n != "discovery"
    }


def _gate_passes(cwd: Path, ref: str, folder: str, spec: str) -> bool:
    """Run the gate on a copy of the spec folder taken from `ref`; owner decisions come from the shared git dir."""
    data = subprocess.run(
        ["git", "archive", "--format=tar", ref, "--", folder], cwd=cwd, capture_output=True, check=True
    )
    with tempfile.TemporaryDirectory() as tmp:
        with tarfile.open(fileobj=BytesIO(data.stdout)) as tar:
            tar.extractall(tmp, filter="data")
        try:
            refusals, _ = review.gate(cwd, spec, Path(tmp) / folder)
        except review.GateError:
            return False
    return not refusals


def prs_enabled(cwd: Path) -> bool:
    """`status.pullRequests` when set; otherwise on for a GitHub code host (`codeHost.type`, else the origin URL)."""
    chosen = settings.get(cwd, "status.pullRequests")
    if chosen is not None:
        return bool(chosen)
    host = settings.get(cwd, "codeHost.type")
    if host is not None:
        return host == "github"
    return "github.com" in git(cwd, "remote", "get-url", "origin", check=False)


def gh_pr(cwd: Path, branch: str) -> dict[str, Any] | None:
    """The newest PR for `branch` from the code host, or None when there is none."""
    out = subprocess.run(
        ["gh", "pr", "list", "--head", branch, "--state", "all", "--json", "number,state", "--limit", "1"],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise GuardError(f"gh could not list PRs for {branch}: {out.stderr.strip() or out.returncode}")
    prs = json.loads(out.stdout or "[]")
    return prs[0] if prs else None


def collect(
    cwd: Path,
    include_completed: bool = False,
    pr_lookup: Callable[[str], dict[str, Any] | None] | None = None,
) -> list[dict[str, Any]]:
    root = settings.get(cwd, "specsRoot")
    main = default_branch(cwd)
    lookup = (pr_lookup or (lambda branch: gh_pr(cwd, branch))) if prs_enabled(cwd) else None
    names = {
        b.removeprefix("spec/")
        for b in git(cwd, "for-each-ref", "--format=%(refname:short)", "refs/heads/spec/").split()
    }
    for where in ("todo", "completed"):
        names |= _specs_in(cwd, main, f"{root}/{where}")
    # a spec committed on the current branch with no spec/<name> branch and not on the default branch
    current = git(cwd, "rev-parse", "--abbrev-ref", "HEAD")
    local = _specs_in(cwd, "HEAD", f"{root}/todo") - names
    live = marker.read(cwd) or {}
    out = []
    for spec in sorted(names | local):
        branch = f"spec/{spec}"
        has_branch = bool(git(cwd, "branch", "--list", branch).strip())
        ref = "HEAD" if spec in local else branch if has_branch else main
        folder = _folder(cwd, ref, root, spec)
        merged = (_folder(cwd, main, root, spec) or "").split("/")[-2:-1] == ["completed"]
        row = {
            "spec": spec,
            "branch": branch if has_branch else None,
            "done": 0,
            "blocked": 0,
            "pending": 0,
            "after": [],
            "ticket": live.get("ticket") if live.get("spec") == spec else None,
            "pr": None,
        }
        overview = _show(cwd, ref, f"{folder}/overview.md") if folder else None
        plan_text = _show(cwd, ref, f"{folder}/implementation-plan.md") if folder else None
        if overview:
            row["after"] = specindex._headers(overview).get("After", [])
        if plan_text:
            states = [cells[1] if len(cells) > 1 else "" for cells in plan.status_rows_text(plan_text).values()]
            row["done"] = sum(s in review.FINISHED for s in states)
            row["blocked"] = sum(s.startswith(plan.BLOCKED) for s in states)
            row["pending"] = len(states) - row["done"] - row["blocked"]
        if spec in local:  # only where it lives: no tracker state without a spec branch
            row["state"] = f"Unbranched (on {current})"
            row["next"] = f"no spec/{spec} branch: put it on one (spec:triage), or merge it into {main}"
            out.append(row)
            continue
        if merged and not has_branch:
            state = "Completed"
        elif not folder or not (overview or plan_text):
            state = "Triaged"
        elif not plan_text:
            state = "Drafting"
        elif row["done"] + row["blocked"] == 0:
            state = "Planned"
        elif row["pending"]:
            state = "In progress"
        elif _show(cwd, ref, f"{folder}/review/rollup.md") is None:
            state = "Ready for review"
        else:
            state = "Ready to complete" if _gate_passes(cwd, ref, folder, spec) else "In review"
        if lookup and has_branch and state not in ("Triaged", "Drafting"):
            try:
                pr = lookup(branch)
            except GuardError as exc:  # the PR column degrades; the rest of the status still stands
                print(f"warning: {exc}", file=sys.stderr)
                row["pr"], pr = "unknown", None
            if pr:
                row["pr"] = f"#{pr['number']} {pr['state'].lower()}"
                if pr["state"] == "OPEN":
                    state = "PR open"
                elif pr["state"] == "MERGED":
                    state = "Completed"
        if state == "Completed" and not include_completed:
            continue
        row["state"] = state
        row["next"] = NEXT[state].format(s=spec)
        out.append(row)
    return out


def render(rows: list[dict[str, Any]], hidden: int) -> str:
    lines = [
        "| Spec | State | Done / Blocked / Pending | After | Live ticket | PR | Next |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        counts = f"{r['done']} / {r['blocked']} / {r['pending']}"
        lines.append(
            f"| {r['spec']} | {r['state']} | {counts} | {', '.join(r['after']) or '-'} | {r['ticket'] or '-'} | {r['pr'] or '-'} | {r['next']} |"
        )
    if hidden:
        lines.append(f"\n{hidden} completed spec(s) hidden; `--all` shows them.")
    return "\n".join(lines)
