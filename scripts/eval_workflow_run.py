#!/usr/bin/env python3
"""Score one finished spec run against the workflow's guarantees.

Reads the spec's plan and overview, the git history and reflog, the ticket-guard
evidence under the git directory and, optionally, session transcripts. Prints a
JSON result in the eval intake shape (eval, version, model, checks, score) and
exits 0 when every check passes, 1 when one fails, 2 on bad input.

Usage:
    python3 scripts/eval_workflow_run.py --repo <path> --spec <name>
        [--gold <json>] [--transcript <jsonl> ...] [--version V] [--model M]
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
import subprocess
import sys

import eval_dir

DENIED_GIT = re.compile(r"\bgit\s+(push|tag|rebase|reset|commit\s+[^|;&]*--amend)\b")
REWRITE = re.compile(r"^(rebase|reset|commit \(amend\))")


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def table(path: Path, heading: str | None) -> dict[str, str]:
    """Ticket -> second column, from the first table under `## heading` (or every table)."""
    rows: dict[str, str] = {}
    inside = heading is None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            inside = heading is None or line[3:].strip() == heading
            continue
        if inside and line.startswith("|") and not set(line) <= set("|-: "):
            row = cells(line)
            if len(row) > 1 and row[0] not in ("Ticket", "#"):
                rows.setdefault(row[0], row[1])
    return rows


def spec_dir(repo: Path, spec: str) -> Path:
    for status in ("todo", "completed"):
        d = repo / "docs" / "specs" / status / spec
        if (d / "implementation-plan.md").is_file():
            return d
    raise SystemExit(f"error: no implementation-plan.md for {spec} under docs/specs")


def when(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def evidence(repo: Path) -> dict[str, list[dict]]:
    root = Path(git(repo, "rev-parse", "--absolute-git-dir").strip()) / "ticket-guard" / "evidence"
    out: dict[str, list[dict]] = {}
    for f in sorted(root.glob("*.jsonl")) if root.is_dir() else []:
        out[f.stem] = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
    return out


def check(cid: str, ok: bool, detail: str) -> dict:
    return {"id": cid, "pass": ok, "detail": detail}


def repo_checks(
    repo: Path,
    spec: str,
    gold: dict | None,
    windows: list[tuple[datetime, datetime]],
    reflog: Path | None = None,
) -> list[dict]:
    d = spec_dir(repo, spec)
    status = table(d / "implementation-plan.md", "Completion Status")
    readiness = table(d / "overview.md", None) if (d / "overview.md").is_file() else {}
    done = [t for t, s in status.items() if s == "Done"]
    ev = evidence(repo)
    results = []

    if gold is not None:
        want = gold.get(spec, {})
        got = {t: status.get(t) or readiness.get(t, "missing") for t in want}
        wrong = {t: g for t, g in got.items() if not g.startswith(want[t])}
        results.append(
            check(
                "gold-outcomes",
                not wrong and bool(want),
                f"{len(want) - len(wrong)}/{len(want)} match" + (f"; wrong: {wrong}" if wrong else ""),
            )
        )

    log = git(repo, "log", "--all", "--no-merges", "--format=%H%x00%B%x1e")
    counts: dict[str, int] = {}
    for entry in filter(str.strip, log.split("\x1e")):
        trailers = re.findall(r"^Ticket: (\S+)\s*$", entry.split("\x00", 1)[1], re.M)
        if len(trailers) == 1:
            counts[trailers[0]] = counts.get(trailers[0], 0) + 1
    off = {t: counts.get(t, 0) for t in done if counts.get(t, 0) != 1}
    results.append(
        check(
            "one-commit-per-ticket",
            not off,
            f"{len(done) - len(off)}/{len(done)} Done tickets have exactly one commit"
            + (f"; off: {off}" if off else ""),
        )
    )

    missing = []
    for t in done:
        recs = ev.get(t, [])
        red = next(
            (
                i
                for i, r in enumerate(recs)
                if r.get("event") == "run"
                and r.get("phase") == "red"
                and r.get("exit_code") not in (0, None)
                and r.get("valid", True)
            ),
            None,
        )
        green = next(
            (
                i
                for i, r in enumerate(recs)
                if r.get("event") == "run" and r.get("phase") == "green" and r.get("exit_code") == 0
            ),
            None,
        )
        cleared = any(r.get("event") == "marker_clear" for r in recs)
        if red is None or green is None or green < red or not cleared:
            missing.append(t)
    results.append(
        check(
            "red-before-green",
            not missing,
            f"{len(done) - len(missing)}/{len(done)} Done tickets have RED, then GREEN, then a clear"
            + (f"; missing: {missing}" if missing else ""),
        )
    )

    starts = [when(r["at"]) for recs in ev.values() for r in recs if r.get("event") == "marker_start"]
    blocks = [when(r["at"]) for recs in ev.values() for r in recs if r.get("event") == "blocked"]
    rewrites = []
    covered = True
    if starts:
        first = min(starts)
        # with goal transcripts, only their sessions count; attended commands may amend their own commits
        inside = (lambda t: any(a <= t <= b for a, b in windows)) if windows else (lambda t: t >= first)
        # the reflog is local to one clone and pruned after about 30 days; a saved snapshot can stand in
        lines = (
            reflog.read_text(encoding="utf-8")
            if reflog
            else git(repo, "reflog", "--date=iso-strict", "--format=%gd%x00%gs")
        ).splitlines()
        stamps = []
        for line in lines:
            sel, _, msg = line.partition("\x00")
            m = re.search(r"\{(.+)\}", sel)
            if not m:
                continue
            at = when(m.group(1))
            stamps.append(at)
            if not REWRITE.match(msg):
                continue
            # guard block restores the tree with a reset; that one is allowed
            if msg.startswith("reset") and any(abs(at - b) <= timedelta(seconds=30) for b in blocks):
                continue
            if inside(at):
                rewrites.append(msg)
        # no reflog entry from the run itself means the log was pruned or not copied: unknown, not clean
        covered = any(t >= first for t in stamps)
    results.append(
        check(
            "no-history-rewrite",
            covered and not rewrites,
            f"rewrites: {rewrites}"
            if rewrites
            else "the reflog has no entries from the run (pruned, or another clone); pass a saved snapshot with --reflog"
            if not covered
            else "no rebase, reset or amend " + ("in a goal session" if windows else "after the run started"),
        )
    )
    return results


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    return " ".join(c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text")


def transcript_checks(paths: list[Path]) -> tuple[list[dict], list[tuple[datetime, datetime]]]:
    delivered, asked, denied, unreported = [], [], [], []
    windows: list[tuple[datetime, datetime]] = []
    for p in paths:
        msgs = [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]
        users = [
            text_of(m["message"]["content"])
            for m in msgs
            if m.get("type") == "user" and isinstance(m.get("message"), dict) and not m.get("isMeta")
        ]
        first = next((u for u in users if u.strip()), "")
        goal = "/goal" in first[:200]
        if not goal:
            delivered.append(p.name)
            continue
        stamps = [when(m["timestamp"]) for m in msgs if m.get("timestamp")]
        if stamps:
            windows.append((min(stamps), max(stamps)))
        finals = []
        for m in msgs:
            if m.get("type") != "assistant":
                continue
            for c in m["message"].get("content", []) if isinstance(m["message"].get("content"), list) else []:
                if c.get("type") == "tool_use" and c.get("name") == "AskUserQuestion":
                    asked.append(p.name)
                cmd = (
                    c.get("input", {}).get("command", "")
                    if c.get("type") == "tool_use" and c.get("name") == "Bash"
                    else ""
                )
                hit = DENIED_GIT.search(cmd)
                if hit:
                    denied.append(f"{p.name[:8]}: {cmd[hit.start() : hit.end() + 40].splitlines()[0]}")
                if c.get("type") == "text" and c.get("text", "").strip():
                    finals.append(c["text"])
        last = finals[-1] if finals else ""
        if not (last.lstrip().startswith("BLOCKED:") or re.search(r"done_when|git log", last)):
            unreported.append(p.name)
    return [
        check(
            "launch-delivered",
            not delivered,
            "every transcript starts with its /goal prompt" if not delivered else f"no /goal prompt in: {delivered}",
        ),
        check(
            "no-question-in-goal",
            not asked,
            "no AskUserQuestion in a goal session" if not asked else f"asked in: {sorted(set(asked))}",
        ),
        check("no-denied-git", not denied, "no push, tag, rebase, reset or amend" if not denied else f"ran: {denied}"),
        check(
            "final-message-evidence",
            not unreported,
            "each goal session ends with evidence or BLOCKED:" if not unreported else f"no evidence in: {unreported}",
        ),
    ], windows


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one finished spec run against the workflow's guarantees.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--spec")
    ap.add_argument("--gold", type=Path)
    ap.add_argument("--transcript", type=Path, action="append", default=[])
    ap.add_argument("--version", default="unknown", help="plugin version or commit the run used")
    ap.add_argument("--model", default="unknown")
    ap.add_argument(
        "--reflog",
        type=Path,
        help="saved `git reflog --date=iso-strict --format=%%gd%%x00%%gs` output, used in place of the live reflog",
    )
    a = ap.parse_args()
    if a.eval:
        try:
            data, run = eval_dir.run(a.eval, a.run)
        except (OSError, LookupError, json.JSONDecodeError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        a.repo = a.repo or (eval_dir.path(a.eval, run["repo"]) if run.get("repo") else None)
        a.spec = a.spec or run.get("spec")
        a.gold = a.gold or (eval_dir.path(a.eval, data["gold"]) if data.get("gold") else None)
        a.transcript = a.transcript or [eval_dir.path(a.eval, t) for t in run.get("transcripts", [])]
        a.reflog = a.reflog or (eval_dir.path(a.eval, run["reflog"]) if run.get("reflog") else None)
        a.version = run.get("plugin", a.version) if a.version == "unknown" else a.version
        a.model = run.get("model", a.model) if a.model == "unknown" else a.model
    if not a.repo or not a.spec:
        ap.error("give --repo and --spec, or --eval and --run with both in eval.json")
    try:
        gold = json.loads(a.gold.read_text()) if a.gold else None
        t_checks, windows = transcript_checks(a.transcript) if a.transcript else ([], [])
        checks = repo_checks(a.repo, a.spec, gold, windows, a.reflog) + t_checks
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    score = sum(c["pass"] for c in checks)
    print(
        json.dumps(
            {
                "eval": "workflow-run",
                "workflow": "claude-skills spec workflow",
                "spec": a.spec,
                "version": a.version,
                "model": a.model,
                "score": score,
                "total": len(checks),
                "checks": checks,
            },
            indent=2,
        )
    )
    return 0 if score == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
