#!/usr/bin/env python3
"""Score one `spec:current` run and the `spec:diff` that follows it against a gold set.

`spec:current` commits the folded system description and the compiled `docs/current-state.json`; it is scored on
the repo after it. `spec:diff` prints a read-only plan; it is scored on its saved report and on the tree staying the
same around it. Each part scores only when its inputs are given. The gold set lives in a private eval directory
(evals/README.md); its format is in evals/spec-current-diff/EVAL.md.

Usage: eval_spec_current_diff_run.py (--eval <dir> --run <name> | --gold <gold.json> [--repo <repo>] [--start <sha>]
       [--diff-report <report.md>] [--diff-before <file> --diff-after <file>])
Exit codes: 0 = every check passed, 1 = a check failed, 2 = bad input
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

from eval_common_ground_run import tables
import eval_dir
from eval_workflow_run import check, git

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runtime"))
from ticket_guard import currentstate

DESCRIPTION = "docs/system-description.md"
STATE = "docs/current-state.json"


def same_sha(a: str, b: str) -> bool:
    return bool(a and b) and (a.startswith(b) or b.startswith(a))


def norm(path: str) -> str:
    return path.strip("` ").removeprefix("./")


def commits_check(repo: Path, start: str, want: dict[str, dict[str, Any]]) -> dict:
    """Each gold commit has one commit since the start: its subject, its trailer, and only its files."""
    log = git(repo, "log", "--format=%H%x00%s%x00%B%x01", f"{start}..HEAD")
    found = [c.strip("\n").split("\x00") for c in log.split("\x01") if c.strip()]
    bad = []
    for name, w in want.items():
        hits = [
            (sha, subject)
            for sha, subject, body in found
            if re.search(w["subject"], subject, re.I) and (not w.get("trailer") or w["trailer"] in body.splitlines())
        ]
        if not hits:
            bad.append(
                f"{name}: no commit with subject /{w['subject']}/"
                + (f" and `{w['trailer']}`" if w.get("trailer") else "")
            )
            continue
        files = set(git(repo, "show", "--name-only", "--format=", hits[-1][0]).split())
        if w.get("files_only") and not files <= set(w["files_only"]):
            bad.append(f"{name}: `{hits[-1][1]}` also touches {sorted(files - set(w['files_only']))}")
    return check("current-commits", not bad, f"{len(want)} commits as gold" if not bad else str(bad))


def last_updated(text: str) -> str:
    m = currentstate.LAST_UPDATED.search(text)
    return m.group(2) if m else ""


def history_specs(text: str) -> list[str]:
    m = re.search(r"^## Change history\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    found = tables(m.group(1), {"spec"}) if m else []
    return [r.get("spec", "").strip("` ") for t in found for r in t]


def current_checks(repo: Path, start: str | None, gold: dict[str, Any]) -> list[dict]:
    """The commits, the folded description and the compiled state against gold."""
    out = []
    if start and gold.get("commits"):
        out.append(commits_check(repo, start, gold["commits"]))
    sd = (repo / DESCRIPTION).read_text(encoding="utf-8")
    d = gold.get("description", {})
    verified = re.search(r"^verified:\s*(\S+)", sd, re.M)
    probs = []
    if (spec := d.get("change_history_row", {}).get("spec")) and spec not in history_specs(sd):
        probs.append(f"no Change history row for {spec}")
    if not last_updated(sd) or same_sha(last_updated(sd), d.get("last_updated_not", "")):
        probs.append(f"Last updated is still {last_updated(sd) or 'missing'}")
    if d.get("verified_not") and (not verified or same_sha(verified.group(1), d["verified_not"])):
        probs.append(f"verified: is still {verified.group(1) if verified else 'missing'}")
    out.append(
        check("description-folded", not probs, "the description is folded and re-verified" if not probs else str(probs))
    )

    data = json.loads((repo / STATE).read_text(encoding="utf-8"))
    cs = gold.get("current_state", {})
    probs = currentstate.validate(data)
    data = data if isinstance(data, dict) else {}
    built = str((data.get("built_at") or {}).get("system_description", ""))
    if same_sha(built, cs.get("built_at_system_description_not", "")) or not same_sha(built, last_updated(sd)):
        probs.append(f"built from {built or 'nothing'}, the description was last updated at {last_updated(sd) or '?'}")
    out.append(check("state-fresh", not probs, f"built from {built}" if not probs else str(probs)))

    comps = [c for c in data.get("components") or [] if isinstance(c, dict)]
    g = cs.get("components", {})
    probs = []
    if (rng := g.get("count")) and not rng[0] <= len(comps) <= rng[1]:
        probs.append(f"{len(comps)} components, want {rng[0]} to {rng[1]}")
    text = lambda c: f"{c.get('name', '')} {c.get('does', '')}"  # noqa: E731
    required = set()
    for r in g.get("required", []):
        hits = [i for i, c in enumerate(comps) if re.search(r["match"], text(c), re.I)]
        required.update(hits)
        if not hits:
            probs.append(f"no component matches /{r['match']}/")
        probs += [
            f"{comps[i]['name']}: {comps[i].get('status')}, want {r['status']}"
            for i in hits
            if comps[i].get("status") not in r["status"]
        ]
    for i, c in enumerate(comps):
        if c.get("status") == "planned" and i not in required:
            if g.get("planned_allowed") and not re.search(g["planned_allowed"], text(c), re.I):
                probs.append(f"{c.get('name')}: planned, not one gold allows")
        elif i not in required and g.get("others") and c.get("status") != g["others"]:
            probs.append(f"{c.get('name')}: {c.get('status')}, want {g['others']}")
    for f in g.get("forbidden", []):
        probs += [
            f"{c.get('name')}: does /{f['does_not']}/"
            for c in comps
            if re.search(f["match"], text(c), re.I) and re.search(f["does_not"], c.get("does", ""), re.I)
        ]
    out.append(check("components", not probs, f"{len(comps)} components as gold" if not probs else str(probs)))

    ids = {str(f.get("id", "")) for f in data.get("findings") or [] if isinstance(f, dict)}
    want = set(cs.get("findings", {}).get("ids", []))
    out.append(
        check(
            "findings",
            ids == want,
            f"{len(ids)} open findings as gold"
            if ids == want
            else f"missing: {sorted(want - ids)}; extra: {sorted(ids - want)}",
        )
    )
    docs = {norm(d.get("doc", "")) for d in data.get("drift") or [] if isinstance(d, dict)}
    dg = cs.get("drift", {})
    want_docs = {norm(x) for x in dg.get("docs", [])}
    absent = docs & {norm(x) for x in dg.get("absent", [])}
    ok = docs == want_docs and not absent
    out.append(
        check(
            "drift",
            ok,
            f"{len(docs)} drifted docs as gold"
            if ok
            else f"missing: {sorted(want_docs - docs)}; extra: {sorted(docs - want_docs)}; must not drift: {sorted(absent)}",
        )
    )
    return out


def spec_sections(report: str) -> dict[str, str]:
    """The body of each `### <name>` section of the report, by name."""
    parts = re.split(r"^### ", report, flags=re.M)[1:]
    return {p.split("\n", 1)[0].strip().strip("`"): p.split("\n", 1)[1] if "\n" in p else "" for p in parts}


def diff_checks(report: str, gold: dict[str, Any]) -> list[dict]:
    """The report covers every spec under the banner, lists the gold assumptions, overlaps and changes."""
    secs = spec_sections(report)
    flat = " ".join(report.split()).lower()
    probs = [f"no ### {s} section" for s in gold.get("specs", []) if s not in secs]
    if gold.get("banner") and " ".join(gold["banner"].split()).lower() not in flat:
        probs.append(f"no banner '{gold['banner']}'")
    out = [
        check(
            "diff-coverage",
            not probs,
            f"{len(gold.get('specs', []))} specs, banner present" if not probs else str(probs),
        )
    ]

    # every table under ### Assumptions (a run may write one per spec); with no such heading, the report's last table
    cols = {"spec", "kind", "assumption", "checked against"}
    if "Assumptions" in secs:
        rows = [r for t in tables(secs["Assumptions"], cols) for r in t]
    else:
        found = tables(report, cols)
        rows = found[-1] if found else []
    missed = []
    for g in gold.get("assumptions", []):
        ok = any(
            r.get("spec", "").strip("` ") == g["spec"]
            and re.search(g["match"], f"{r.get('assumption', '')} {r.get('quoted from', '')}", re.I)
            and re.search(g.get("kind", ""), r.get("kind", ""), re.I)
            and re.search(g.get("checked_against", ""), r.get("checked against", ""), re.I)
            for r in rows
        )
        if not ok:
            missed.append(f"{g['spec']}: /{g['match']}/")
    n = len(gold.get("assumptions", []))
    out.append(
        check(
            "diff-assumptions", not missed, f"{n} of {n} gold assumptions listed" if not missed else f"missed: {missed}"
        )
    )

    overlaps = [" | ".join(r.values()) for t in tables(secs.get("Overlaps", ""), {"specs"}) for r in t]
    missed = [
        f"{o['specs']}: /{o['match']}/"
        for o in gold.get("overlaps", [])
        if not any(all(s in row for s in o["specs"]) and re.search(o["match"], row, re.I) for row in overlaps)
    ]
    out.append(check("diff-overlaps", not missed, "every gold overlap listed" if not missed else f"missed: {missed}"))

    probs = []
    for spec in set(gold.get("changes", {})) | set(gold.get("not_changed", {})):
        body = " ".join(" | ".join(r.values()) for t in tables(secs.get(spec, ""), set()) for r in t)
        probs += [f"{spec}: no /{p}/" for p in gold.get("changes", {}).get(spec, []) if not re.search(p, body, re.I)]
        probs += [f"{spec}: has /{p}/" for p in gold.get("not_changed", {}).get(spec, []) if re.search(p, body, re.I)]
    out.append(check("diff-changes", not probs, "every spec's changes as gold" if not probs else str(probs)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one spec:current run and its spec:diff against a gold set.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--repo", type=Path, help="the clone after spec:current")
    ap.add_argument("--start", help="the commit the run started from (default: the gold's fixture_start)")
    ap.add_argument("--diff-report", type=Path, help="spec:diff's saved report")
    ap.add_argument("--diff-before", type=Path, help="HEAD and git status before spec:diff")
    ap.add_argument("--diff-after", type=Path, help="HEAD and git status after spec:diff")
    ap.add_argument("--gold", type=Path)
    a = ap.parse_args()
    try:
        if a.eval:
            data, run = eval_dir.run(a.eval, a.run)
            for key in ("repo", "diff_report", "diff_before", "diff_after"):
                if not getattr(a, key) and run.get(key):
                    setattr(a, key, eval_dir.path(a.eval, run[key]))
            a.start = a.start or run.get("start") or data.get("fixture_start")
            a.gold = a.gold or (eval_dir.path(a.eval, data["gold"]) if data.get("gold") else None)
        if not (a.gold and (a.repo or a.diff_report or a.diff_after)):
            ap.error(
                "give --gold and at least --repo, --diff-report or --diff-before/--diff-after, or --eval and --run"
            )
        gold = json.loads(a.gold.read_text())
        checks = []
        if a.repo:
            checks += current_checks(a.repo, a.start or gold.get("fixture_start"), gold.get("spec_current", {}))
        if a.diff_report:
            checks += diff_checks(a.diff_report.read_text(encoding="utf-8"), gold.get("spec_diff", {}))
        if a.diff_before and a.diff_after and gold.get("spec_diff", {}).get("writes_nothing", True):
            same = a.diff_before.read_text(encoding="utf-8") == a.diff_after.read_text(encoding="utf-8")
            checks.append(
                check(
                    "diff-read-only",
                    same,
                    "HEAD and status unchanged" if same else "spec:diff changed HEAD or the tree",
                )
            )
    except (OSError, LookupError, KeyError, ValueError, subprocess.CalledProcessError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    s = sum(c["pass"] for c in checks)
    print(json.dumps({"eval": "spec-current-diff", "score": s, "total": len(checks), "checks": checks}, indent=2))
    return 0 if s == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
