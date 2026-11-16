"""RED and GREEN wrappers: run the ticket's check, save the log, append the evidence record."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from ticket_guard import evidence, files, marker, settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import guard_dir, head, top

RED_TYPES = ("test", "stand-in", "refactor")
# Exit codes and output that mean the tests never ran: pytest 2 (interrupted), 4 (usage), 5 (none collected).
COLLECTION_EXITS = frozenset({2, 4, 5})
COLLECTION_ERROR = re.compile(
    r"error collecting|errors during collection|no tests ran|no tests found|"
    r"SyntaxError|Failed to load|Cannot find module",
    re.IGNORECASE,
)
# The runner never started: shell 126/127, `python -m <runner>` without it installed, or a shell
# "not found". A test's own import error prints the module quoted, so it still counts as RED.
RUNNER_EXITS = frozenset({126, 127})
RUNNER_MISSING = re.compile(r"(?m): No module named [\w.]+$|: command not found$|^sh: \d+: \S+: not found$")


def active(cwd: Path) -> dict[str, Any]:
    data = marker.read(cwd)
    if data is None:
        raise GuardError("no marker: run `guard marker start` first")
    return data


def execute(
    cwd: Path,
    ticket: str,
    phase: str,
    command: list[str],
    echo: bool = True,
    run_in: Path | None = None,
) -> dict[str, Any]:
    """Run `command` from the repo root (or `run_in`), save its log, return the run fields."""
    root = run_in or top(cwd)
    started = evidence.now()
    shell = len(command) == 1  # one argument is a shell string, as in workflow-config `verify`
    proc = subprocess.run(
        command[0] if shell else command,
        cwd=root,
        shell=shell,
        capture_output=True,
        text=True,
        check=False,
    )
    output = proc.stdout + proc.stderr
    log = guard_dir(cwd) / "logs" / f"{ticket}-{phase}-{started.replace(':', '')}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(output, encoding="utf-8")
    if echo:
        sys.stdout.write(output[-4000:])
    return {
        "phase": phase,
        "command": " ".join(command),
        "argv": command,
        "cwd": str(root),
        "exit_code": proc.returncode,
        "head_sha": head(root),
        "tree_hash": files.tree_hash(root),
        "log_path": str(log),
        "log_sha256": hashlib.sha256(output.encode()).hexdigest(),
        "started_at": started,
        "output": output,
    }


def latest(records: list[dict[str, Any]], phase: str, valid_only: bool = True) -> dict[str, Any] | None:
    for rec in reversed(records):
        if rec.get("event") == "run" and rec.get("phase") == phase and (not valid_only or rec.get("valid", True)):
            return rec
    return None


def red(cwd: Path, command: list[str], kind: str = "test") -> dict[str, Any]:
    data = active(cwd)
    ticket = data["ticket"]
    plan = (settings.spec_dir(cwd, data["spec"]) / "implementation-plan.md").relative_to(top(cwd))
    is_test = files.test_matcher(cwd)
    changed = [p for p in files.changed_since(cwd, data["start_sha"]) if p != plan.as_posix()]
    tests = [p for p in changed if is_test(p)]
    reason = None
    if kind == "test":
        others = [p for p in changed if not is_test(p)]
        if others:
            reason = f"non-test files changed before RED: {', '.join(others)}"
        elif not tests:
            reason = "no new or changed test files since the start SHA"
    elif kind == "refactor":
        tests = files.all_tests(cwd)
    run: dict[str, Any] = {}
    if reason is None:
        run = execute(cwd, ticket, "red", command)
        output = run.pop("output")
        if kind == "refactor":
            if run["exit_code"] != 0:
                reason = "a refactor ticket's stand-in needs the full suite passing before the change"
        elif run["exit_code"] == 0:
            reason = "the check passed; RED needs a failing test"
        elif run["exit_code"] in RUNNER_EXITS or RUNNER_MISSING.search(output):
            reason = "the test runner did not start (missing command or module), so nothing failed"
        elif kind == "test" and (run["exit_code"] in COLLECTION_EXITS or COLLECTION_ERROR.search(output)):
            reason = "the failure looks like a collection or import error, not a failing test"
    return evidence.append(
        cwd,
        ticket,
        "run",
        **({"phase": "red", "command": " ".join(command)} | run),
        red_type=kind,
        test_files=tests,
        test_files_digest=files.digest(cwd, tests),
        test_file_digests={rel: files.digest(cwd, [rel]) for rel in tests},
        valid=reason is None,
        reason=reason,
    )


def green(cwd: Path, command: list[str], source: str = "wrapper", echo: bool = True) -> dict[str, Any]:
    data = active(cwd)
    ticket = data["ticket"]
    recs = evidence.current(cwd, ticket)
    red_rec = latest(recs, "red")
    if red_rec is None:
        raise GuardError("no valid RED record for this ticket; record RED first")
    run = execute(cwd, ticket, "green", command, echo)
    run.pop("output")
    tests = red_rec["test_files"]
    digest = files.digest(cwd, tests)
    changed, amended = _changed_and_amended(cwd, data, recs, red_rec, digest)
    return evidence.append(
        cwd,
        ticket,
        "run",
        **run,
        source=source,
        test_files=tests,
        test_files_digest=digest,
        tests_changed=bool(changed - amended),
        amended_tests=sorted(changed & amended),
    )


def _changed_and_amended(
    cwd: Path, data: dict[str, Any], recs: list[dict[str, Any]], red_rec: dict[str, Any], digest: str
) -> tuple[set[str], set[str]]:
    """The frozen tests changed since RED, and those an owner-approved amendment after RED covers."""
    if digest == red_rec["test_files_digest"]:
        return set(), set()
    tests = red_rec["test_files"]
    after_red = recs[next(i for i, r in enumerate(recs) if r is red_rec) + 1 :]
    events = {"amendment_applied"}
    per_file = red_rec.get("test_file_digests")
    if per_file is None:
        # shortcut: RED from a build before per-file digests can't say which file changed, so an attended
        # amendment request counts and every frozen file is treated as changed; drop once those runs are done.
        changed = set(tests)
        if data["mode"] == "attended":
            events.add("amendment_requested")
    else:
        changed = {rel for rel in tests if files.digest(cwd, [rel]) != per_file.get(rel)}
    amended = {
        r["file"] for r in after_red if r["event"] in events and r.get("owner_ticket", data["ticket"]) == data["ticket"]
    }
    if per_file is None and amended & changed:
        return amended & changed, amended
    return changed, amended
