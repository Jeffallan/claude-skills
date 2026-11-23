"""Re-score every baseline intake run with the current scorer and gold set, so runs compare on one check set.

Each run is rebuilt from its saved git bundle; reflogs, transcripts and accuracy mappings come from the
results folder. `suite_green` stands in for a live test run when the run's services are gone. A rebuilt run has
no installed dependencies, so eval.json's optional `setup` commands (a run may override them) run in it first.

It writes the score table into the eval directory's baseline.md, in place of the table it wrote last, and keeps
the prose around it; `--print` prints the table instead.

Usage: python3 scripts/eval_intake_baseline.py [--print] <eval directory holding eval.json>
"""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import eval_dir

HERE = Path(__file__).resolve().parent


def score(run: dict, base: Path, work: Path, gold: Path, setup: list[str]) -> dict:
    repo = work / run["run"].replace(" ", "-")
    bundle = eval_dir.path(base, run["bundle"])
    subprocess.run(["git", "clone", "-q", "-b", run["branch"], str(bundle), str(repo)], check=True)
    for cmd in run.get("setup", setup):
        r = subprocess.run(cmd, shell=True, cwd=repo, capture_output=True, text=True)
        if r.returncode:
            tail = (r.stdout + r.stderr).strip().splitlines()[-1:] or [""]
            raise SystemExit(f"{run['run']}: setup `{cmd}` exit {r.returncode}: {tail[0][:160]}")
    cmd = [
        sys.executable,
        str(HERE / "eval_intake_run.py"),
        "--eval",
        str(base),
        "--run",
        run["run"],
        "--repo",
        str(repo),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 2:
        raise SystemExit(f"{run['run']}: {proc.stderr.strip()}")
    proc_out = json.loads(proc.stdout)
    if not run.get("accuracy"):  # mapped by hand against the gold set, so a new run has none at first
        return {"run": run["run"], "plugin": run["plugin"], "procedure": proc_out, "accuracy": None}
    acc = subprocess.run(
        [sys.executable, str(HERE / "eval_intake_accuracy.py"), str(gold), str(eval_dir.path(base, run["accuracy"]))],
        capture_output=True,
        text=True,
        check=True,
    )
    return {"run": run["run"], "plugin": run["plugin"], "procedure": proc_out, "accuracy": json.loads(acc.stdout)}


# The block the baseline writes: its `Checks v.., gold v..` line, then the table under it
BLOCK = re.compile(r"^Checks v\S+, gold v.*\n(?:\n)*(?:\|.*(?:\n|$))*", re.M)


def write(path: Path, block: str, project: str) -> None:
    """Put the block in baseline.md in place of the last one written, keeping the prose around it."""
    text = path.read_text(encoding="utf-8") if path.exists() else f"# Intake eval baseline: {project}\n\n"
    found = list(BLOCK.finditer(text))
    if found:
        m = found[-1]
        text = text[: m.start()] + block + text[m.end() :]
    else:
        text = text.rstrip("\n") + "\n\n" + block if text.strip() else block
    path.write_text(text, encoding="utf-8")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Re-score every intake run of an eval directory into its baseline.md.")
    ap.add_argument("eval", type=Path, help="eval directory holding eval.json")
    ap.add_argument("--print", action="store_true", help="print the table instead of writing baseline.md")
    a = ap.parse_args(argv)
    base = a.eval
    manifest = eval_dir.manifest(base)
    gold = eval_dir.path(base, manifest["gold"])
    with tempfile.TemporaryDirectory() as tmp:
        results = [score(r, base, Path(tmp), gold, manifest.get("setup", [])) for r in manifest["runs"]]
    mapped = next((r["accuracy"] for r in results if r["accuracy"]), None)
    gold_v = mapped["gold_version"] if mapped else "unknown (no run mapped)"
    lines = [
        f"Checks v{results[0]['procedure']['checks_version']}, gold v{gold_v}",
        "",
        "| Run | Plugin | Procedure | Failed checks | Optional | Accuracy |",
        "|-----|--------|-----------|---------------|----------|----------|",
    ]
    for r in results:
        p, a_ = r["procedure"], r["accuracy"]
        failed = ", ".join(f"`{c['id']}`" for c in p["checks"] if not c["pass"]) or "none"
        opt = ", ".join(f"`{c['id']}` {'pass' if c['pass'] else 'fail'}" for c in p["optional"]) or "none exercised"
        acc = f"{a_['found']} of {a_['total']}" if a_ else "not mapped"
        lines.append(f"| {r['run']} | `{r['plugin']}` | {p['score']}/{p['total']} | {failed} | {opt} | {acc} |")
    block = "\n".join(lines) + "\n"
    if a.print:
        print(block, end="")
        return 0
    out = base / "baseline.md"
    write(out, block, manifest.get("project", base.name))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
