#!/usr/bin/env python3
"""Score one discovery run (`discovery:create`, then `discovery:approve`) against a gold set.

Reads the topic folder (`discovery.md`, and `synthesis.md` when research ran) and prints a JSON result:
whether each gold item got its route, each gold blocking decision was raised, and each gold ticket was
created. The gold set lives in a private eval directory (evals/README.md).

Usage: eval_discovery_run.py (--eval <dir> --run <name> | --repo <repo> --topic <topic> --gold <gold.json>)
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


def table(text: str, heading: str) -> list[dict[str, str]]:
    """Rows of the first table under `## <heading>`, keyed by lowercased header."""
    m = re.search(rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    lines = [ln.strip() for ln in (m.group(1) if m else "").splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return []
    cells = [[c.strip() for c in ln.strip("|").split("|")] for ln in lines]
    head = [h.lower() for h in cells[0]]
    return [dict(zip(head, row, strict=False)) for row in cells[2:]]


def topic_dir(repo: Path, topic: str) -> Path:
    cfg = repo / ".claude/workflow-config.json"
    root = json.loads(cfg.read_text()).get("specsRoot", "docs/specs") if cfg.exists() else "docs/specs"
    for state in ("todo", "completed"):
        d = repo / root / state / "discovery" / topic
        if d.is_dir():
            return d
    raise OSError(f"no discovery topic {topic} under {root}/todo or {root}/completed")


def created_ids(text: str) -> set[str]:
    """Proposed tickets the topic records as created: `discovery:approve` writes "Created as <ID>" next to the ticket,
    on a line that names it (its table row, or `Created as ENG-1: P1`) or under its `### P<n>:` heading."""
    out = {p for line in text.splitlines() if "Created as" in line for p in re.findall(r"\bP\d+\b", line)}
    for m in re.finditer(r"^###\s+(P\d+)\b(.*?)(?=^##|\Z)", text, re.M | re.S):
        if "Created as" in m.group(2):
            out.add(m.group(1))
    return out


def score(folder: Path, gold: dict) -> list[dict]:
    texts = [
        (folder / f).read_text(encoding="utf-8") for f in ("discovery.md", "synthesis.md") if (folder / f).exists()
    ]
    items = table(texts[0], "Features") if texts else []
    wrong = []
    for pattern, route in gold.get("routes", {}).items():
        hit = [r for r in items if re.search(pattern, r.get("item", ""), re.I)]
        if not hit or hit[0].get("route", "").lower() != route.lower():
            wrong.append(f"{pattern}: {hit[0].get('route') if hit else 'missing'}, want {route}")
    decisions = [r.get("decision", "") for t in texts for r in table(t, "Blocking decisions")]
    missed = [p for p in gold.get("decisions", []) if not any(re.search(p, d, re.I) for d in decisions)]
    tickets = {r.get("#", ""): r.get("title", "") for t in texts for r in table(t, "Proposed tickets")}
    created = {p for t in texts for p in created_ids(t)}
    created_titles = [tickets.get(p, "") for p in created]
    not_created = [p for p in gold.get("tickets", []) if not any(re.search(p, t, re.I) for t in created_titles)]
    return [
        check("routing", not wrong, f"{len(gold.get('routes', {}))} items routed as gold" if not wrong else str(wrong)),
        check("blocking-decisions", not missed, "every gold decision raised" if not missed else f"missing: {missed}"),
        check(
            "approved-tickets",
            not not_created,
            "every gold ticket created" if not not_created else f"not created: {not_created}",
        ),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Score one discovery run against a gold set.")
    ap.add_argument("--eval", type=Path, help="eval directory: every input below defaults to its eval.json")
    ap.add_argument("--run", help="the run's name in eval.json")
    ap.add_argument("--repo", type=Path)
    ap.add_argument("--topic")
    ap.add_argument("--gold", type=Path)
    a = ap.parse_args()
    try:
        if a.eval:
            data, run = eval_dir.run(a.eval, a.run)
            a.repo = a.repo or (eval_dir.path(a.eval, run["repo"]) if run.get("repo") else None)
            a.gold = a.gold or (eval_dir.path(a.eval, data["gold"]) if data.get("gold") else None)
            a.topic = a.topic or run.get("topic")
        if not (a.repo and a.gold):
            ap.error("give --repo and --gold, or --eval and --run with both in eval.json")
        gold = json.loads(a.gold.read_text())
        checks = score(topic_dir(a.repo, a.topic or gold["topic"]), gold)
    except (OSError, LookupError, KeyError, json.JSONDecodeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    score_ = sum(c["pass"] for c in checks)
    print(json.dumps({"eval": "discovery", "score": score_, "total": len(checks), "checks": checks}, indent=2))
    return 0 if score_ == len(checks) else 1


if __name__ == "__main__":
    sys.exit(main())
