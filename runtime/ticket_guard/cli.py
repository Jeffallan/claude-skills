"""`guard ...` subcommands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from ticket_guard import (
    batches,
    block,
    boundary,
    decisions,
    docs,
    evidence,
    hooks,
    marker,
    metrics,
    plan,
    review,
    runs,
    specindex,
    specstatus,
)
from ticket_guard.errors import GuardError, NotARepo

EXIT_OK, EXIT_REFUSED, EXIT_USAGE = 0, 1, 2


def add_parser(sub: argparse._SubParsersAction) -> None:
    guard = sub.add_parser("guard", help="workflow runtime: marker, hooks, evidence, review")
    gsub = guard.add_subparsers(dest="guard_command", required=True)

    mk = gsub.add_parser("marker", help="start, show or clear the ticket marker")
    msub = mk.add_subparsers(dest="marker_command", required=True)
    start = msub.add_parser("start", help="clean-tree check, then write the marker")
    start.add_argument("spec")
    start.add_argument("ticket")
    start.add_argument("--mode", choices=marker.MODES, default="attended")
    start.set_defaults(func=cmd_marker_start)
    msub.add_parser("status", help="print the marker").set_defaults(func=cmd_marker_status)
    msub.add_parser("clear", help="remove the marker").set_defaults(func=cmd_marker_clear)

    run = gsub.add_parser("run", help="run a check and record RED or GREEN evidence")
    rsub = run.add_subparsers(dest="run_command", required=True)
    red = rsub.add_parser("red", help="record a failing run of the ticket's new tests")
    red.add_argument("--type", choices=runs.RED_TYPES, default="test", dest="red_type")
    red.add_argument("cmd", nargs=argparse.REMAINDER)
    red.set_defaults(func=cmd_run_red)
    green = rsub.add_parser("green", help="record a run after the implementation")
    green.add_argument("cmd", nargs=argparse.REMAINDER)
    green.set_defaults(func=cmd_run_green)

    blk = gsub.add_parser("block", help="save the ticket's work, restore, write the Blocked row")
    blk.add_argument("ticket")
    blk.add_argument("reason")
    blk.add_argument("--spec", help="default: the marker's spec, else the plan listing the ticket")
    blk.add_argument(
        "--start",
        help="with no marker: save and restore to this SHA (default: the evidence's marker_start when the marker was lost)",
    )
    blk.set_defaults(func=cmd_block)
    dec = gsub.add_parser("decide", help="record an owner decision (attended only)")
    dec.add_argument("row", help="finding or ticket ID, such as F3 or T2")
    dec.add_argument("status", help=", ".join(decisions.STATUSES))
    dec.add_argument("--spec")
    dec.add_argument("--session", help="session id (default: $CLAUDE_SESSION_ID, then the marker)")
    dec.set_defaults(func=cmd_decide)

    rr = gsub.add_parser("rerun", help="run the checks on the uncommitted work in a clean worktree")
    who = rr.add_mutually_exclusive_group()
    who.add_argument("--ticket")
    who.add_argument("--spec", help="spec-level recheck at HEAD: no marker needed")
    rr.add_argument("cmd", nargs=argparse.REMAINDER)
    rr.set_defaults(func=cmd_rerun)
    rp = gsub.add_parser("red-replay", help="the new tests must fail against the start SHA")
    rp.add_argument("--ticket")
    rp.set_defaults(func=cmd_red_replay)
    ts = gsub.add_parser(
        "tamper-scan",
        help="flag deleted tests, skips, snapshot changes, assertion-free tests",
    )
    ts.add_argument("--ticket")
    ts.add_argument("--reason", action="append", default=[], metavar="ID=TEXT")
    ts.set_defaults(func=cmd_tamper_scan)
    sm = gsub.add_parser(
        "summary",
        help="evidence summary for the Completion Status notes",
        description=(
            "Prints the evidence summary for the Completion Status notes. "
            "`tests sha256 X (N files)` is the first 12 hex characters of a sha256 "
            "over the RED test files, sorted by repo path: for each file, its path, "
            "a NUL byte, then the raw 32-byte sha256 of its content (a deleted file "
            "hashes as the bytes `<deleted>`). It is not the hash of any one file."
        ),
    )
    sm.add_argument("--ticket")
    sm.add_argument("--accept-lost-marker", action="store_true")
    sm.set_defaults(func=cmd_summary)

    mt = gsub.add_parser("metrics", help="write review/metrics.md for the spec diff")
    mt.add_argument("spec")
    mt.add_argument("--base", help="default: merge base with origin/HEAD, main or master")
    mt.set_defaults(func=cmd_metrics)
    ro = gsub.add_parser("rollup", help="write review/rollup.md from verifier verdicts")
    ro.add_argument("spec")
    ro.add_argument("--verdicts", type=Path, required=True, help="JSON list or JSONL of findings")
    ro.add_argument(
        "--transcripts",
        type=Path,
        help="folder of agent-<id>.jsonl subagent transcripts",
    )
    ro.set_defaults(func=cmd_rollup)
    gt = gsub.add_parser("gate", help="refuse while a blocking row or a Blocked ticket is open")
    gt.add_argument("spec")
    gt.set_defaults(func=cmd_gate)

    da = gsub.add_parser(
        "docs-affected", help="docs the diff affects: citing a changed symbol, or related to a changed doc"
    )
    da.add_argument("--base", help="default: the ticket's start SHA")
    da.add_argument("--ticket")
    da.add_argument("--json", action="store_true", help="print JSON rows instead of lines")
    da.set_defaults(func=cmd_docs_affected)
    dk = gsub.add_parser("docs-checked", help="record that an affected doc needs no change, with the reason")
    dk.add_argument("doc", help="path under the docs root, as docs-affected prints it")
    dk.add_argument("--reason", required=True)
    dk.add_argument("--ticket")
    dk.set_defaults(func=cmd_docs_checked)
    dw = gsub.add_parser("docs-waivers", help="write review/docs-waivers.md: waivers and small doc updates to rule on")
    dw.add_argument("spec")
    dw.add_argument("--base", help="default: merge base with origin/HEAD, main or master")
    dw.set_defaults(func=cmd_docs_waivers)
    dd = gsub.add_parser(
        "docs-drift", help="docs whose code changed since their verified: commit, outside the workflow"
    )
    dd.add_argument("--json", action="store_true", help="print JSON rows instead of lines")
    dd.set_defaults(func=cmd_docs_drift)
    dc = gsub.add_parser("docs-check", help="one-sided or missing related: links, citations that no longer resolve")
    dc.set_defaults(func=cmd_docs_check)

    ss = gsub.add_parser("spec-status", help="where every spec stands, read from each spec branch")
    ss.add_argument("--all", action="store_true", help="include completed specs")
    ss.add_argument("--json", action="store_true", help="print JSON rows instead of a table")
    ss.set_defaults(func=cmd_spec_status)
    si = gsub.add_parser("spec-index", help="write <specsRoot>/INDEX.md from the overviews")
    si.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 if stale or a name link is broken",
    )
    si.set_defaults(func=cmd_spec_index)

    rb = gsub.add_parser(
        "run-batches",
        help="headless next-batch goal runs until every ticket is Done or Blocked",
    )
    rb.add_argument("spec")
    rb.add_argument("--batch-size", type=int, help="default: goal.batchSize, else 3")
    rb.add_argument("--claude", default="claude", help="the claude binary")
    rb.set_defaults(func=cmd_run_batches)

    cp = gsub.add_parser("commit-plan", help="commit Blocked rows guard block left in the plan")
    cp.add_argument("spec")
    cp.set_defaults(func=cmd_commit_plan)

    hook = gsub.add_parser("hook", help="hook entry points (JSON on stdin)")
    hsub = hook.add_subparsers(dest="hook_command", required=True)
    for name, func in HOOKS.items():
        hsub.add_parser(name).set_defaults(func=cmd_hook, hook=func)


HOOKS = {
    "pre-tool-use": hooks.pre_tool_use,
    "post-tool-use": hooks.post_tool_use,
    "session-start": hooks.session_start,
    "stop": hooks.stop,
}


def _print(data: object) -> None:
    print(json.dumps(data, indent=2))


def cmd_marker_start(args) -> int:
    data = marker.start(Path.cwd(), args.spec, args.ticket, args.mode)
    warning = marker.age_warning(Path.cwd(), data)
    if warning:
        print(warning, file=sys.stderr)
    _print(data)
    return EXIT_OK


def cmd_marker_status(args) -> int:
    marker.path(Path.cwd())  # raises NotARepo outside a repo
    data = marker.read(Path.cwd())
    if data is None:
        print("no marker", file=sys.stderr)
        return EXIT_REFUSED
    warning = marker.age_warning(Path.cwd(), data)
    if warning:
        print(warning, file=sys.stderr)
    _print(data)
    return EXIT_OK


def cmd_marker_clear(args) -> int:
    data = marker.clear(Path.cwd())
    print(f"cleared marker for {data['ticket']}" if data else "no marker")
    return EXIT_OK


def _command(args) -> list[str]:
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    if not cmd:
        raise GuardError("give the command after --")
    return cmd


def cmd_run_red(args) -> int:
    rec = runs.red(Path.cwd(), _command(args), args.red_type)
    if not rec["valid"]:
        print(f"RED not recorded as valid: {rec['reason']}", file=sys.stderr)
        return EXIT_REFUSED
    print(f"RED recorded for {', '.join(rec['test_files']) or rec['command']}")
    return EXIT_OK


def cmd_run_green(args) -> int:
    rec = runs.green(Path.cwd(), _command(args))
    if rec["tests_changed"]:
        print("the ticket's test files changed since RED", file=sys.stderr)
        return EXIT_REFUSED
    return EXIT_OK if rec["exit_code"] == 0 else EXIT_REFUSED


def cmd_block(args) -> int:
    rec = block.block(Path.cwd(), args.ticket, args.reason, args.spec, args.start)
    print(f"{args.ticket} Blocked in {rec['spec']}: {args.reason}")
    if rec["committed"]:
        print(f"committed the Blocked row: docs({rec['spec']}): record Blocked rows in the plan")
    else:
        print(f"the Blocked row is uncommitted; once no ticket is in progress, run `guard commit-plan {rec['spec']}`")
    if rec.get("patch"):
        print(f"saved: {rec['patch']}" + (f", {rec['untracked']}" if rec["untracked"] else ""))
    return EXIT_OK


def cmd_decide(args) -> int:
    rec = decisions.decide(Path.cwd(), args.row, args.status, args.spec, args.session)
    print(f"recorded {rec['row']}: {rec['status']} ({decisions.path(Path.cwd())})")
    return EXIT_OK


def cmd_rerun(args) -> int:
    cmd = args.cmd[1:] if args.cmd[:1] == ["--"] else args.cmd
    rec = boundary.rerun(Path.cwd(), cmd or None, args.ticket, args.spec)
    print(f"clean re-run: `{rec['command']}` exit {rec['exit_code']}")
    return EXIT_OK if rec["passed"] else EXIT_REFUSED


def cmd_red_replay(args) -> int:
    rec = boundary.red_replay(Path.cwd(), args.ticket)
    if rec.get("skipped"):
        print(f"RED replay skipped: {rec['skipped']}")
    elif rec["passed"]:
        print(f"RED replay: `{rec['command']}` exit {rec['exit_code']} at the start SHA")
    else:
        print(f"RED replay failed: {rec['reason']}", file=sys.stderr)
    return EXIT_OK if rec["passed"] else EXIT_REFUSED


def cmd_tamper_scan(args) -> int:
    reasons = dict(r.split("=", 1) for r in args.reason if "=" in r)
    rec = boundary.tamper_scan(Path.cwd(), reasons, args.ticket)
    for flag in rec["flags"]:
        where = flag["file"] + (f":{flag['line']}" if flag.get("line") else "")
        print(f"{flag['id']} {flag['kind']} {where}: {flag['detail']} | reason: {flag['reason'] or 'missing'}")
    if not rec["passed"] and rec["mode"] == "goal":
        print(
            "goal mode takes no --reason: block the ticket with `guard block`",
            file=sys.stderr,
        )
    elif not rec["passed"]:
        print("give each flag a one-line reason with --reason ID=TEXT", file=sys.stderr)
    return EXIT_OK if rec["passed"] else EXIT_REFUSED


def cmd_summary(args) -> int:
    line, missing = boundary.summary(Path.cwd(), args.ticket, args.accept_lost_marker)
    if missing:
        print(
            "missing evidence:\n" + "\n".join(f"- {m}" for m in missing),
            file=sys.stderr,
        )
        return EXIT_REFUSED
    print(line)
    return EXIT_OK


def cmd_metrics(args) -> int:
    print(f"wrote {metrics.report(Path.cwd(), args.spec, args.base)}")
    return EXIT_OK


def cmd_rollup(args) -> int:
    print(f"wrote {review.rollup(Path.cwd(), args.spec, args.verdicts, args.transcripts)}")
    return EXIT_OK


def cmd_gate(args) -> int:
    try:
        refusals, notes = review.gate(Path.cwd(), args.spec)
    except review.GateError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE
    for note in notes:
        print(note)
    if refusals:
        print("gate refused:\n" + "\n".join(f"- {r}" for r in refusals), file=sys.stderr)
        return EXIT_REFUSED
    print(f"gate passed for {args.spec}")
    return EXIT_OK


def cmd_docs_affected(args) -> int:
    cwd = Path.cwd()
    if args.base:
        rows = docs.statuses(cwd, args.base)
    else:
        ctx = boundary.context(cwd, args.ticket)
        rows = docs.statuses(cwd, ctx["start_sha"], evidence.current(cwd, ctx["ticket"]))
    if args.json:
        _print(rows)
    else:
        for r in rows:
            print(f"{r['status']:8} {r['doc']}: {'; '.join(r['reasons'])}")
        if not rows:
            print("no doc affected")
    return EXIT_OK


def cmd_docs_checked(args) -> int:
    ctx = boundary.context(Path.cwd(), args.ticket)
    docs.mark_checked(Path.cwd(), ctx["ticket"], args.doc, args.reason, ctx["mode"])
    print(f"recorded {args.doc} as checked, no change")
    return EXIT_OK


def cmd_docs_waivers(args) -> int:
    base = args.base or metrics.default_base(Path.cwd())
    print(f"wrote {docs.write_waivers(Path.cwd(), args.spec, base)}")
    return EXIT_OK


def cmd_docs_drift(args) -> int:
    rows = docs.drift(Path.cwd())
    if args.json:
        _print(rows)
    else:
        for r in rows:
            print(f"{r['doc']} ({r['command'] or 'no command'}, verified {r['verified']}): {'; '.join(r['reasons'])}")
        if not rows:
            print("no drift since each doc's verified commit")
    return EXIT_OK


def cmd_docs_check(args) -> int:
    problems = docs.check(Path.cwd())
    for problem in problems:
        print(problem, file=sys.stderr)
    if not problems:
        print("docs consistent")
    return EXIT_REFUSED if problems else EXIT_OK


def cmd_spec_status(args) -> int:
    cwd = Path.cwd()
    every = specstatus.collect(cwd, include_completed=True)
    rows = every if args.all else [r for r in every if r["state"] != "Completed"]
    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        print(specstatus.render(rows, len(every) - len(rows)))
    return EXIT_OK


def cmd_spec_index(args) -> int:
    path, errors, warnings = specindex.build(Path.cwd(), args.check)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if not args.check:
        print(f"wrote {path}")
    return EXIT_REFUSED if errors else EXIT_OK


def cmd_run_batches(args) -> int:
    return batches.run_batches(Path.cwd(), args.spec, args.batch_size, args.claude)


def cmd_commit_plan(args) -> int:
    done = plan.commit(Path.cwd(), args.spec)
    print("committed the plan" if done else "nothing to commit: the plan is clean")
    return EXIT_OK


def cmd_hook(args) -> int:
    """Hooks never fail the session: bad input or an internal error prints to stderr, exit 0."""
    try:
        payload = json.load(sys.stdin)
        out = args.hook(payload) if isinstance(payload, dict) else None
    except Exception as exc:
        print(f"ticket-guard hook error: {exc}", file=sys.stderr)
        return EXIT_OK
    if out:
        print(out)
    return EXIT_OK


def run(args) -> int:
    try:
        return args.func(args)
    except NotARepo as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE
    except GuardError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_REFUSED
