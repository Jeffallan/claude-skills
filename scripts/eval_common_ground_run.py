#!/usr/bin/env python3
"""Score one common-ground run's assumptions check against gold conflicts.

Reads the report table the command prints (`| ID | Verdict | Spec | Assumption | Source | Fix |`), saved
from the run, and checks recall of the gold conflicts, flags that match no gold conflict, and whether each
flag names the right spec. Gold unknowns and the files saved next to the report (git-files.txt, ground.index.json,
COMMON-GROUND.md) add checks that are skipped when absent. The gold set lives in a private eval directory
(evals/README.md).

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
from eval_workflow_run import cells, check, report, skip


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


def run_checks(report: str, gold: dict, run: Path) -> list[dict]:
    """Checks on gold unknowns and on the files the operator saves in the run folder; each is skipped when its gold
    key or file is absent."""
    out = []
    if "unknowns" in gold:
        bad = []
        for g in gold["unknowns"]:
            hit = [
                r
                for r in rows(report)
                if r.get("spec") == g["spec"]
                and re.search(g["match"], f"{r.get('assumption', '')} {r.get('source', '')}", re.I)
            ]
            if not hit or any(verdict(r) == "conflicts" for r in hit):
                bad.append(f"{g['match']}: {'conflicts' if hit else 'missing'}")
        n = len(gold["unknowns"])
        out.append(check("unknown-not-guessed", not bad, f"{n} gold unknowns not flagged" if not bad else str(bad)))
    else:
        out.append(skip("unknown-not-guessed", "no unknowns in gold"))
    files = run / "git-files.txt"
    if files.exists():
        touched = [
            p
            for p in (ln.strip() for ln in files.read_text(encoding="utf-8").splitlines())
            if p.startswith("docs/specs/") or p == "docs/current-state.json"
        ]
        out.append(
            check(
                "no-spec-edits", not touched, "no spec or current-state edits" if not touched else f"touched: {touched}"
            )
        )
    else:
        out.append(skip("no-spec-edits", "no git-files.txt in the run folder"))
    index = run / "ground.index.json"
    if index.exists():
        try:
            n = len(json.loads(index.read_text(encoding="utf-8"))["assumptions"])
            md = run / "COMMON-GROUND.md"
            ids = set(re.findall(r"^###\s+(A\d+)\b", md.read_text(encoding="utf-8"), re.M)) if md.exists() else set()
            ok, detail = n == len(ids), f"index has {n} assumptions, COMMON-GROUND.md has {len(ids)} ids"
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            ok, detail = False, f"ground.index.json is not a valid index: {e}"
        out.append(check("ground-file-valid", ok, detail))
    else:
        out.append(skip("ground-file-valid", "no ground.index.json in the run folder"))
    return out


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
    # An either entry passes as a conflicts row of its spec, or as a holds row of its spec that names the caveat
    full = lambda r: f"{text(r)} {r.get('fix', '')}"  # noqa: E731
    for g in gold.get("either", []):
        hits = [i for i, r in enumerate(flags) if re.search(g["match"], text(r), re.I)]
        matched.update(hits)
        wrong_spec += [
            f"{g['match']}: flagged on {flags[i]['spec']}, want {g['spec']}"
            for i in hits
            if flags[i].get("spec") != g["spec"]
        ]
        if not any(
            r.get("spec") == g["spec"]
            and re.search(g["match"], text(r), re.I)
            and (
                verdict(r) == "conflicts" or (verdict(r).startswith("holds") and re.search(g["caveat"], full(r), re.I))
            )
            for r in rows(report)
        ):
            missed.append(g["match"])
    false = [flags[i].get("id", "?") for i in range(len(flags)) if i not in matched]
    n = len(gold.get("conflicts", [])) + len(gold.get("either", []))
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
        text, gold = a.report.read_text(encoding="utf-8"), json.loads(a.gold.read_text())
        checks = score(text, gold) + run_checks(text, gold, a.report.parent)
    except (OSError, LookupError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return report("common-ground", checks)


if __name__ == "__main__":
    sys.exit(main())
