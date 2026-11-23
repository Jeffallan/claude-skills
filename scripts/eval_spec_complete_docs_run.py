#!/usr/bin/env python3
"""Score the docs duties of one `spec:complete` run against a gold set.

Step 2 of `spec:complete` folds the spec into `docs/system-description.md` (the section changes and a Change history
row) and runs docs:verify, which writes `review/docs-verify.md`: `| Doc | Claim | Verdict | Evidence |`, verdicts
`holds`, `stale` or `unknown`, a stale row later marked `fixed` or `declined`. This scorer reads the description
before and after the run and the saved docs:verify table. The gold set lives in a private eval directory
(evals/README.md); its format is in evals/spec-complete-docs/EVAL.md.

Usage: eval_spec_complete_docs_run.py (--eval <dir> --run <name> | --before <md> --after <md> --verify <md>
       --gold <gold.json>)
Exit codes: 0 = every check passed, 1 = a check failed, 2 = bad input
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

from eval_common_ground_run import tables, verdict
import eval_dir
from eval_workflow_run import check

# A flagged row: stale, or stale and then fixed or declined by the owner
FLAGGED = re.compile(r"stale|fixed|declined")


def section(text: str, g: dict[str, Any]) -> str | None:
    """The body of the `## ` section the gold entry names: its heading regex, else its number."""
    for part in re.split(r"^## ", text, flags=re.M)[1:]:
        head, _, body = part.partition("\n")
        if (g.get("heading") and re.search(g["heading"], head, re.I)) or re.match(
            rf"{re.escape(g['section'])}\b", head
        ):
            return body
    return None


def description_checks(before: str, after: str, gold: dict[str, Any]) -> list[dict]:
    """Must-change sections lose their stale sentences and carry the new facts; must-not-change sections stay."""
    changed_bad, unchanged_bad, notes = [], [], []
    for g in gold.get("sections", []):
        old, new = section(before, g), section(after, g)
        if g["must_change"] is True or g["must_change"] == "optional":
            body = new or ""
            miss = [f"still /{p}/" for p in g.get("stale", []) if re.search(p, body, re.I)]
            miss += [f"no /{p}/" for p in g.get("expect", []) if not re.search(p, body, re.I)]
            if g["must_change"] is True and miss:
                changed_bad.append(f"section {g['section']}: {', '.join(miss)}")
            elif g["must_change"] == "optional":
                notes.append(f"optional section {g['section']} {'unchanged' if miss else 'changed'}")
        elif g["must_change"] is False and " ".join((old or "").split()) != " ".join((new or "").split()):
            unchanged_bad.append(f"section {g['section']}")
    history = section(after, {"section": "Change history", "heading": "^Change history"}) or ""
    rows = [
        r
        for t in tables(history, {"spec"})
        for r in t
        if r.get("spec", "").strip("` ") == gold.get("change_history_row", {}).get("spec")
    ]
    want = gold.get("change_history_row", {}).get("sections_include", [])
    cell = next((r.get("sections changed", "") for r in rows), "")
    hist_ok = bool(rows) and all(re.search(p, cell, re.I) for p in want)
    hist = f"row: {cell}" if rows else f"no Change history row for {gold.get('change_history_row', {}).get('spec')}"
    return [
        check(
            "sd-changed",
            not changed_bad,
            "; ".join(["every must-change section changed", *notes])
            if not changed_bad
            else "; ".join(changed_bad + notes),
        ),
        check(
            "sd-unchanged",
            not unchanged_bad,
            "must-not-change sections unchanged" if not unchanged_bad else f"changed: {unchanged_bad}",
        ),
        check("change-history", hist_ok, hist if hist_ok else f"{hist}; want {want}"),
    ]


def verify_checks(report: str, gold: dict[str, Any]) -> list[dict]:
    """Every required stale claim is flagged on its doc, and no true claim is."""
    # every table: a run may split the file into Stale, Holds and Unknown tables
    rows = [r for t in tables(report, {"doc", "claim"}) for r in t]
    # without a Verdict column (an earlier proposed shape) every row is a flag
    flags = [r for r in rows if "verdict" not in r or FLAGGED.search(verdict(r))]
    excluded = tuple(gold.get("excluded_docs", []))
    flags = [r for r in flags if not r.get("doc", "").strip("` ").removeprefix("./").startswith(excluded)]

    def hit(g: dict[str, Any], r: dict[str, str]) -> bool:
        doc = r.get("doc", "").strip("` ").removeprefix("./")
        return doc.startswith(g["doc"].removeprefix("./")) and bool(re.search(g["match"], r.get("claim", ""), re.I))

    missed, notes = [], []
    for g in gold.get("stale_claims", []):
        if not any(hit(g, r) for r in flags):
            (missed if g.get("required", True) else notes).append(g.get("id", g["match"]))
    false = [g.get("id", g["match"]) for g in gold.get("not_stale", []) if any(hit(g, r) for r in flags)]
    note = "".join(f"; optional {i} not flagged" for i in notes)
    return [
        check(
            "verify-recall",
            not missed,
            f"every required stale claim flagged{note}" if not missed else f"missed: {missed}{note}",
        ),
        check(
            "verify-false-flags", not false, "no true claim flagged" if not false else f"flagged true claims: {false}"
        ),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one spec:complete run's docs duties against a gold set.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--before", type=Path, help="docs/system-description.md before the run")
    ap.add_argument("--after", type=Path, help="docs/system-description.md at the completion commit")
    ap.add_argument("--verify", type=Path, help="the docs:verify table, review/docs-verify.md")
    ap.add_argument("--gold", type=Path)
    a = ap.parse_args()
    try:
        if a.eval:
            data, run = eval_dir.run(a.eval, a.run)
            for key in ("before", "after", "verify"):
                if not getattr(a, key) and run.get(key):
                    setattr(a, key, eval_dir.path(a.eval, run[key]))
            a.gold = a.gold or (eval_dir.path(a.eval, data["gold"]) if data.get("gold") else None)
        if not (a.before and a.after and a.verify and a.gold):
            ap.error("give --before, --after, --verify and --gold, or --eval and --run with them in eval.json")
        gold = json.loads(a.gold.read_text())
        checks = description_checks(
            a.before.read_text(encoding="utf-8"),
            a.after.read_text(encoding="utf-8"),
            {**gold["system_description"], "spec": gold["spec"]},
        ) + verify_checks(a.verify.read_text(encoding="utf-8"), gold["docs_verify"])
    except (OSError, LookupError, KeyError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    s = sum(c["pass"] for c in checks)
    print(json.dumps({"eval": "spec-complete-docs", "score": s, "total": len(checks), "checks": checks}, indent=2))
    return 0 if s == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
