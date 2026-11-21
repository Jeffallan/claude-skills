#!/usr/bin/env python3
"""Score one common-ground run's assumptions check against gold conflicts.

Reads the report table the command prints (`| ID | Verdict | Spec | Assumption | Source | Fix |`), saved
from the run, and checks recall of the gold conflicts, flags that match no gold conflict, and whether each
flag names the right spec. The gold set lives in a private eval directory (evals/README.md).

Usage: eval_common_ground_run.py (--eval <dir> --run <name> | --report <report.md> --gold <gold.json>)
Exit codes: 0 = every check passed, 1 = a check failed, 2 = bad input
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

import eval_dir
from eval_workflow_run import check


def rows(text: str) -> list[dict[str, str]]:
    """Rows of every table whose header has Verdict and Spec, keyed by lowercased header."""
    out, head = [], None
    for ln in text.splitlines():
        if not ln.strip().startswith("|"):
            head = None
            continue
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if head is None:
            head = [c.lower() for c in cells] if {"verdict", "spec"} <= {c.lower() for c in cells} else []
        elif head and not all(re.fullmatch(r":?-+:?", c) for c in cells):
            out.append(dict(zip(head, cells, strict=False)))
    return out


def score(report: str, gold: dict) -> list[dict]:
    flags = [r for r in rows(report) if r.get("verdict", "").strip("`").lower() == "conflicts"]
    text = lambda r: f"{r.get('assumption', '')} {r.get('source', '')}"  # noqa: E731
    missed, wrong_spec, matched = [], [], set()
    for g in gold.get("conflicts", []):
        hits = [i for i, r in enumerate(flags) if re.search(g["match"], text(r), re.I)]
        if not hits:
            missed.append(g["match"])
        matched.update(hits)
        wrong_spec += [
            f"{g['match']}: flagged on {flags[i]['spec']}, want {g['spec']}"
            for i in hits
            if flags[i].get("spec") != g["spec"]
        ]
    false = [flags[i].get("id", "?") for i in range(len(flags)) if i not in matched]
    n = len(gold.get("conflicts", []))
    return [
        check(
            "conflict-recall",
            not missed,
            f"{n - len(missed)} of {n} gold conflicts flagged" if not missed else f"missed: {missed}",
        ),
        check("no-false-flags", not false, "every flag is a gold conflict" if not false else f"false flags: {false}"),
        check("right-spec", not wrong_spec, "every flag names its spec" if not wrong_spec else str(wrong_spec)),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one common-ground assumptions check against gold conflicts.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--report", type=Path, help="the command's saved report")
    ap.add_argument("--gold", type=Path)
    a = ap.parse_args()
    try:
        if a.eval:
            data, run = eval_dir.run(a.eval, a.run)
            a.report = a.report or (eval_dir.path(a.eval, run["report"]) if run.get("report") else None)
            a.gold = a.gold or (eval_dir.path(a.eval, data["gold"]) if data.get("gold") else None)
        if not (a.report and a.gold):
            ap.error("give --report and --gold, or --eval and --run with both in eval.json")
        checks = score(a.report.read_text(encoding="utf-8"), json.loads(a.gold.read_text()))
    except (OSError, LookupError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    s = sum(c["pass"] for c in checks)
    print(json.dumps({"eval": "common-ground", "score": s, "total": len(checks), "checks": checks}, indent=2))
    return 0 if s == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
