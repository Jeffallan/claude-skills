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
from eval_workflow_run import cells, check


def tables(text: str, need: set[str]) -> list[list[dict[str, str]]]:
    """Each table whose header has every column in `need` (lowercase), as rows keyed by lowercased header."""
    out: list[list[dict[str, str]]] = []
    head = None
    for ln in text.splitlines():
        if not ln.strip().startswith("|"):
            head = None
            continue
        row = cells(ln)
        if head is None:
            head = [c.lower() for c in row] if need <= {c.lower() for c in row} else []
            if head:
                out.append([])
        elif head and not all(re.fullmatch(r":?-+:?", c) for c in row):
            out[-1].append(dict(zip(head, row, strict=False)))
    return out


def rows(text: str) -> list[dict[str, str]]:
    """Rows of the last table whose header has Verdict and Spec: a run that prints the table again after an owner's
    answer reports its last one."""
    found = tables(text, {"verdict", "spec"})
    return found[-1] if found else []


def verdict(row: dict[str, str]) -> str:
    return row.get("verdict", "").strip("`* ").lower()


def score(report: str, gold: dict) -> list[dict]:
    flags = [r for r in rows(report) if verdict(r) == "conflicts"]
    holds = [r for r in rows(report) if verdict(r) == "holds"]
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
    not_held = [
        g["match"]
        for g in gold.get("holds", [])
        if not any(re.search(g["match"], text(r), re.I) and r.get("spec") == g["spec"] for r in holds)
    ]
    return [
        check(
            "conflict-recall",
            not missed,
            f"{n - len(missed)} of {n} gold conflicts flagged" if not missed else f"missed: {missed}",
        ),
        check("no-false-flags", not false, "every flag is a gold conflict" if not false else f"false flags: {false}"),
        check("right-spec", not wrong_spec, "every flag names its spec" if not wrong_spec else str(wrong_spec)),
        check(
            "holds-recognized",
            not not_held,
            f"{len(gold.get('holds', []))} gold holds reported as holding" if not not_held else f"not held: {not_held}",
        ),
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
