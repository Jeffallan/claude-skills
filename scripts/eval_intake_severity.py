"""Compare an intake run's severities with a gold set's, for every gold row the run's accuracy mapping matched.

Levels score Critical 4, High 3, Medium 2, Low 1. A run whose plugin had no Critical level is scored on its own
scale too: gold Critical against run High is a scale match, exact in the normalized score and one under in the
raw score. Agreement, error and kappa use the normalized score. The method, gold-cell markers and gates are in
evals/intake/SEVERITY.md.

Usage:
  python3 scripts/eval_intake_severity.py <gold.md> <mapping.json> <intake-findings.md>
      [--critical | --no-critical | --plugin <sha>] [--json] [--gate]
  python3 scripts/eval_intake_severity.py --pool <eval directory> [<eval directory> ...] [--json] [--gate]

--pool scores every run in each directory's eval.json that has an `accuracy` mapping, reading its tracker
from the run's bundle at `scored_at`, and adds pooled metrics with the calibration gates. Gates are advisory:
the exit code is 0 unless --gate is given and a gate fails (1). Bad input exits 2.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

import eval_dir
from eval_intake_accuracy import findings_table

LEVELS = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
NAMES = {v: k for k, v in LEVELS.items()}
LEVEL_RE = re.compile(r"\b(Critical|High|Medium|Low)\b")
ROW_RE = re.compile(r"Row:\s*(?:Critical|High|Medium|Low)\b[^;]*;\s*\S")
REPO_ROOT = Path(__file__).resolve().parent.parent

# (gate, threshold text, test) per gate set; None as the test means the gate is report-only
RUN_GATES: list[tuple[str, str, Any]] = [
    ("floor", "0", lambda m: m["floor"] == 0),
    ("two_plus", "0", lambda m: m["two_plus"] == 0),
    ("exact", ">= 80%", lambda m: m["exact"] >= 0.80),
    ("within_one", "100%", lambda m: m["within_one"] == 1.0),
    ("signed_error", "within 0.2 of zero", lambda m: abs(m["signed_error"]) <= 0.2),
    ("unexplained", "0", None),
    ("stated_row", "100%", None),
]
POOL_GATES: list[tuple[str, str, Any]] = [
    ("floor", "0", lambda m: m["floor"] == 0),
    ("two_plus", "<= 2%", lambda m: m["two_plus"] / m["n"] <= 0.02),
    ("exact", ">= 70%", lambda m: m["exact"] >= 0.70),
    ("within_one", ">= 95%", lambda m: m["within_one"] >= 0.95),
    ("signed_error", "within 0.15 of zero", lambda m: abs(m["signed_error"]) <= 0.15),
    ("over", "<= 15%", lambda m: m["over"] / m["n"] <= 0.15),
    ("under", "<= 15%", lambda m: m["under"] / m["n"] <= 0.15),
    ("kappa_linear", ">= 0.70", lambda m: m["kappa_linear"] is not None and m["kappa_linear"] >= 0.70),
    ("ac2_linear", ">= 0.70", lambda m: m["ac2_linear"] is not None and m["ac2_linear"] >= 0.70),
    ("recall", ">= 0.60 per level", lambda m: min(m["recall"].values()) >= 0.60),
    ("unexplained", "0", None),
    ("stated_row", "100%", None),
]


def tracker(text: str) -> dict[str, str]:
    """Each finding id in the run's tracker with the text of its `Severity:` line."""
    out = {}
    for section in re.split(r"^### ", text, flags=re.M)[1:]:
        fid = re.match(r"F-\d+", section)
        sev = re.search(r"^- \*\*Severity:\*\*\s*(.+)$", section, re.M)
        if fid and sev:
            out[fid.group(0)] = sev.group(1).strip()
    return out


def level(text: str) -> int:
    m = LEVEL_RE.search(text)
    if not m:
        raise ValueError(f"no severity level in {text!r}")
    return LEVELS[m.group(1)]


def run_id(value: str | None) -> str | None:
    """The run finding a mapping value names; None for a miss or a docs-only `(d)` match, which has no rating."""
    m = re.match(r"F-\d+", value or "")
    return m.group(0) if m else None


def score_run(
    gold_text: str, mapping: dict[str, Any], findings_text: str, critical: bool
) -> tuple[list[dict[str, Any]], list[str]]:
    """One record per matched gold row the run is scored on (given rows and the run's own rows left out), and the
    gold ids matched only in the run's docs."""
    gold = findings_table(gold_text)
    sev = tracker(findings_text)
    given = set(mapping.get("given", []))
    matches, docs_only = [], []
    for gid, value in mapping.get("found", {}).items():
        if not value or gid in given or gid not in gold:
            continue
        row = gold[gid]
        if row.get("Source") and row["Source"] == mapping.get("run"):
            continue
        rid = run_id(value)
        if rid is None:
            docs_only.append(gid)
            continue
        if rid not in sev:
            raise ValueError(f"mapped run finding {value!r} for {gid} has no Severity line in the tracker")
        line = sev[rid]
        run = level(line)
        cell = row.get("Severity", "")
        listed = [LEVELS[x] for x in LEVEL_RE.findall(cell)]
        if not listed:
            raise ValueError(f"gold row {gid} has no severity level")
        contested = "contested" in cell
        g = min(listed, key=lambda x: abs(run - x)) if contested else listed[0]
        g_norm = 3 if g == 4 and not critical else g
        rec = {
            "run_id": rid,
            "gold_id": gid,
            "area": row.get("Area", ""),
            "run": NAMES[run],
            "gold": NAMES[g],
            "raw_error": run - g,
            "error": run - g_norm,
            "gold_norm": g_norm,
            "run_norm": run,
            "stated_row": bool(ROW_RE.search(line)),
            "class": None,
        }
        if rec["raw_error"]:
            if not rec["error"]:
                rec["class"] = "scale"
            elif contested:
                rec["class"] = "contested"
            elif "floor" in cell and rec["error"] < 0:
                rec["class"] = "floor"
            elif not rec["stated_row"]:
                rec["class"] = "unexplained"
            else:
                rec["class"] = "misapplied"
        matches.append(rec)
    return matches, docs_only


def agreement(pairs: list[tuple[int, int]], quadratic: bool = False) -> tuple[float | None, float | None]:
    """Weighted Cohen's kappa and Gwet's AC2 over (gold, run) levels on the fixed four-level scale."""
    q, n = len(LEVELS), len(pairs)
    cats = range(1, q + 1)

    def w(i: int, j: int) -> float:
        d = abs(i - j) / (q - 1)
        return 1 - d * d if quadratic else 1 - d

    g = {k: sum(1 for a, _ in pairs if a == k) / n for k in cats}
    r = {k: sum(1 for _, b in pairs if b == k) / n for k in cats}
    po = sum(w(a, b) for a, b in pairs) / n
    pe_k = sum(w(i, j) * g[i] * r[j] for i in cats for j in cats)
    tw = sum(w(i, j) for i in cats for j in cats)
    pe_g = tw / (q * (q - 1)) * sum(((g[k] + r[k]) / 2) * (1 - (g[k] + r[k]) / 2) for k in cats)
    kappa = (po - pe_k) / (1 - pe_k) if pe_k < 1 else None
    ac2 = (po - pe_g) / (1 - pe_g) if pe_g < 1 else None
    return kappa, ac2


def rnd(x: float | None) -> float | None:
    return None if x is None else round(x, 3)


def metrics(matches: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(matches)
    if not n:
        return {"n": 0}
    errs = [m["error"] for m in matches]
    pairs = [(m["gold_norm"], m["run_norm"]) for m in matches]
    k_lin, ac2 = agreement(pairs)
    k_quad, _ = agreement(pairs, quadratic=True)
    confusion = {gn: {rn: 0 for rn in LEVELS} for gn in LEVELS}
    for m in matches:
        confusion[m["gold"]][m["run"]] += 1
    recall = {}
    for lv in sorted({m["gold_norm"] for m in matches}, reverse=True):
        rows = [m for m in matches if m["gold_norm"] == lv]
        recall[NAMES[lv]] = rnd(sum(1 for m in rows if m["error"] == 0) / len(rows))
    return {
        "n": n,
        "exact_raw": rnd(sum(1 for m in matches if m["raw_error"] == 0) / n),
        "exact": rnd(errs.count(0) / n),
        "within_one": rnd(sum(1 for e in errs if abs(e) <= 1) / n),
        "signed_error": rnd(sum(errs) / n),
        "over": sum(1 for e in errs if e > 0),
        "under": sum(1 for e in errs if e < 0),
        "two_plus": sum(1 for e in errs if abs(e) >= 2),
        "floor": sum(1 for m in matches if m["class"] == "floor"),
        "unexplained": sum(1 for m in matches if m["class"] == "unexplained"),
        "stated_row": [sum(1 for m in matches if m["stated_row"]), n],
        "kappa_linear": rnd(k_lin),
        "kappa_quadratic": rnd(k_quad),
        "ac2_linear": rnd(ac2),
        "recall": recall,
        "confusion": confusion,
    }


def gates(m: dict[str, Any], table: list[tuple[str, str, Any]]) -> list[dict[str, Any]]:
    out = []
    for name, threshold, test in table:
        if test is None:
            result = "report-only"
        elif not m["n"]:
            result = "n/a"
        else:
            result = "pass" if test(m) else "fail"
        out.append({"gate": name, "threshold": threshold, "value": m.get(name), "result": result})
    return out


def plugin_has_critical(sha: str, repo: Path) -> bool | None:
    """Whether the plugin at `sha` (a suffix such as `-noskills` dropped) rates Critical; None when unknown."""
    r = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "grep",
            "-q",
            "-w",
            "Critical",
            sha.split("-")[0],
            "--",
            "*references/intake/findings.md",
        ],
        capture_output=True,
    )
    return {0: True, 1: False}.get(r.returncode)


def run_scale(entry: dict[str, Any], repo: Path) -> dict[str, Any]:
    if "critical" in entry:
        return {"critical": bool(entry["critical"]), "source": "eval.json"}
    plugin = entry.get("plugin")
    if not plugin:
        return {"critical": False, "source": "assumed (no plugin recorded)"}
    found = plugin_has_critical(plugin, repo)
    if found is None:
        return {"critical": False, "source": f"assumed (plugin {plugin} unknown)"}
    return {"critical": found, "source": f"plugin {plugin}"}


def report(gold_text: str, mapping: dict[str, Any], findings_text: str, scale: dict[str, Any]) -> dict[str, Any]:
    matches, docs_only = score_run(gold_text, mapping, findings_text, scale["critical"])
    m = metrics(matches)
    mapped = {run_id(v) for v in mapping.get("found", {}).values()}
    extras: dict[str, int] = {}
    for rid, line in tracker(findings_text).items():
        if rid not in mapped:
            name = NAMES[level(line)]
            extras[name] = extras.get(name, 0) + 1
    misses = [{k: x[k] for k in ("run_id", "gold_id", "run", "gold", "area", "class")} for x in matches if x["class"]]
    return {
        "scale": scale,
        **m,
        "gates": gates(m, RUN_GATES),
        "misses": misses,
        "extras": extras,
        "docs_only": docs_only,
        "matches": matches,
    }


def tracker_from_bundle(base: Path, entry: dict[str, Any]) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        bundle = eval_dir.path(base, entry["bundle"])
        subprocess.run(["git", "clone", "-q", "--bare", str(bundle), tmp], check=True, capture_output=True)
        rev = entry.get("scored_at") or entry["branch"]
        return subprocess.run(
            ["git", "-C", tmp, "show", f"{rev}:docs/intake-findings.md"], check=True, capture_output=True, text=True
        ).stdout


PCT = {"exact_raw", "exact", "within_one"}
ROWS = [
    ("Matched findings", "n"),
    ("Exact, raw", "exact_raw"),
    ("Exact, normalized", "exact"),
    ("Within one", "within_one"),
    ("Mean signed error", "signed_error"),
    ("Over-rated", "over"),
    ("Under-rated", "under"),
    ("Misses of two or more", "two_plus"),
    ("Floor misses", "floor"),
    ("Unexplained misses", "unexplained"),
    ("Severity lines naming a row", "stated_row"),
    ("Linear-weighted kappa", "kappa_linear"),
    ("Quadratic-weighted kappa", "kappa_quadratic"),
    ("Gwet's AC2, linear", "ac2_linear"),
    ("Recall per level", "recall"),
]


def markdown(title: str, r: dict[str, Any]) -> str:
    if not r["n"]:
        return f"## {title}\n\nNo matched findings.\n"
    by_gate = {g["gate"]: g for g in r["gates"]}
    out = [f"## {title}", ""]
    if "scale" in r:
        out += [
            f"Critical on the run's scale: {'yes' if r['scale']['critical'] else 'no'} ({r['scale']['source']})",
            "",
        ]
    out += ["| Metric | Value | Gate | Result |", "|--------|-------|------|--------|"]
    for label, key in ROWS:
        v = r[key]
        if key in PCT:
            v = f"{v * 100:.1f}%"
        elif key == "stated_row":
            v = f"{v[0]} of {v[1]}"
        elif key == "recall":
            v = ", ".join(f"{k} {x}" for k, x in v.items())
        g = by_gate.get(key)
        out.append(f"| {label} | {v} | {g['threshold'] if g else ''} | {g['result'] if g else ''} |")
    if r.get("misses"):
        out += [
            "",
            "| Run id | Gold id | Run | Gold | Area | Class |",
            "|--------|---------|-----|------|------|-------|",
        ]
        out += [
            f"| {x['run_id']} | {x['gold_id']} | {x['run']} | {x['gold']} | {x['area']} | {x['class']} |"
            for x in r["misses"]
        ]
    if r.get("extras"):
        out += ["", "Unmatched run findings: " + ", ".join(f"{k} {v}" for k, v in r["extras"].items())]
    if r.get("docs_only"):
        out += ["", "Matched in docs only, no rating: " + ", ".join(r["docs_only"])]
    return "\n".join(out) + "\n"


def failed(results: list[dict[str, Any]]) -> bool:
    return any(g["result"] == "fail" for r in results for g in r["gates"])


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help="gold.md mapping.json intake-findings.md")
    ap.add_argument("--pool", nargs="+", type=Path, metavar="EVAL_DIR")
    scale = ap.add_mutually_exclusive_group()
    scale.add_argument("--critical", dest="critical", action="store_true", default=None)
    scale.add_argument("--no-critical", dest="critical", action="store_false")
    scale.add_argument("--plugin", help="plugin commit the run used; its findings.md says whether Critical existed")
    ap.add_argument("--plugin-repo", type=Path, default=REPO_ROOT, help="claude-skills clone holding --plugin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true", help="exit 1 when a gate fails")
    args = ap.parse_args(argv)
    try:
        if args.pool:
            runs, everything = [], []
            for base in args.pool:
                manifest = eval_dir.manifest(base)
                gold_text = eval_dir.path(base, manifest["gold"]).read_text(encoding="utf-8")
                for entry in manifest["runs"]:
                    if not entry.get("accuracy"):
                        continue
                    mapping = json.loads(eval_dir.path(base, entry["accuracy"]).read_text(encoding="utf-8"))
                    r = report(gold_text, mapping, tracker_from_bundle(base, entry), run_scale(entry, args.plugin_repo))
                    runs.append({"eval": str(base), "run": entry["run"], **r})
                    everything += r["matches"]
            pooled = metrics(everything)
            pooled["gates"] = gates(pooled, POOL_GATES)
            if args.json:
                print(json.dumps({"runs": runs, "pooled": pooled}))
            else:
                print("\n".join(markdown(f"{r['eval']}: {r['run']}", r) for r in runs))
                print(markdown(f"Pooled ({len(runs)} runs)", pooled))
            return 1 if args.gate and failed([*runs, pooled]) else 0
        if len(args.files) != 3:
            ap.error("give gold.md, mapping.json and intake-findings.md, or --pool")
        gold, mapping, findings = (Path(f).read_text(encoding="utf-8") for f in args.files)
        if args.critical is not None:
            sc = {"critical": args.critical, "source": "flag"}
        else:
            sc = run_scale({"plugin": args.plugin} if args.plugin else {}, args.plugin_repo)
        r = report(gold, json.loads(mapping), findings, sc)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        print(f"bad input: {e}", file=sys.stderr)
        return 2
    print(json.dumps(r) if args.json else markdown(Path(args.files[1]).name, r))
    return 1 if args.gate and failed([r]) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
