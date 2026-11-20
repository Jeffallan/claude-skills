"""`guard rollup` builds review/rollup.md from verifier verdicts; `guard gate` decides with no model."""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from ticket_guard import decisions, docs, evidence, plan, settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import read_jsonl

COLUMNS = (
    "ID",
    "Tier",
    "Suggested",
    "Sources",
    "Location",
    "Claim",
    "Verdict",
    "Proof",
    "Evidence",
    "Reason",
    "Tokens",
    "Minutes",
    "Status",
)
OWNER_STATUSES = ("wontfix", "rejection-accepted")
VERIFIER_STATUSES = ("open", "fixed-verified", "reopened")
FEEDBACK_OWNER_STATUSES = (*OWNER_STATUSES, "answered")
FINISHED = ("Done", "Already done")


class GateError(GuardError):
    """The gate cannot run at all (exit 2, fail closed)."""


def cost(transcript: Path) -> tuple[int, int]:
    """(tokens, minutes) from a subagent transcript: usage summed once per message id."""
    usage: dict[str, dict[str, Any]] = {}
    stamps: list[datetime] = []
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("timestamp"):
            stamps.append(datetime.fromisoformat(entry["timestamp"]))
        message = entry.get("message") or {}
        if entry.get("type") == "assistant" and message.get("usage"):
            usage[message.get("id") or f"line{len(usage)}"] = message["usage"]
    keys = (
        "input_tokens",
        "output_tokens",
        "cache_read_input_tokens",
        "cache_creation_input_tokens",
    )
    tokens = sum(int(u.get(k) or 0) for u in usage.values() for k in keys)
    minutes = round((max(stamps) - min(stamps)).total_seconds() / 60) if stamps else 0
    return tokens, minutes


def _transcript(finding: dict[str, Any], transcripts: list[Path]) -> Path | None:
    if finding.get("transcript"):
        return Path(finding["transcript"])
    if finding.get("agent_id"):
        for folder in transcripts:  # verifiers can span sessions, one folder each
            path = folder / f"agent-{finding['agent_id']}.jsonl"
            if path.is_file():
                return path
    return None


def _cell(value: Any) -> str:
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    text = str(value if value not in (None, "") else "-").replace("\n", " ")
    return text.replace("|", "\\|")


def load_verdicts(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8").strip()
    found = json.loads(text) if text.startswith("[") else [json.loads(x) for x in text.splitlines() if x.strip()]
    for index, finding in enumerate(found):
        if not isinstance(finding, dict) or not finding.get("id"):
            raise GuardError(f"verdict {index + 1} in {path} has no id")
    return found


def rollup(cwd: Path, spec: str, verdicts: Path, transcripts: list[Path] | None = None) -> Path:
    owner = decisions.latest(cwd, spec)
    rows = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
    counted: dict[Path, str] = {}  # one batch verifier covers several findings (GH9)
    for f in load_verdicts(verdicts):
        source = _transcript(f, transcripts or [])
        tokens, minutes = cost(source) if source and source.is_file() else (None, None)
        if tokens is not None and source.resolve() in counted:
            tokens = minutes = f"shared with {counted[source.resolve()]}"
        elif tokens is not None:
            counted[source.resolve()] = f["id"]
            tokens = f"{tokens:,}"
        status = f.get("status") if f.get("status") in VERIFIER_STATUSES else "open"
        if owner.get(f["id"]) in OWNER_STATUSES:
            status = owner[f["id"]]
        values = [
            f["id"],
            f.get("tier"),
            f.get("suggested"),
            f.get("sources"),
            f.get("location"),
            f.get("claim"),
            f.get("verdict"),
            f.get("proof"),
            f.get("evidence"),
            f.get("reason"),
            tokens,
            minutes,
            status,
        ]
        rows.append("| " + " | ".join(_cell(v) for v in values) + " |")
    path = settings.spec_dir(cwd, spec) / "review" / "rollup.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"# Review rollup: {spec}\n\nBuilt by `guard rollup` from the verifier verdicts. "
        "Owner statuses come from `guard decide`; edits here are not read by the gate.\n\n" + "\n".join(rows) + "\n",
        encoding="utf-8",
    )
    return path


def _rollup_rows(path: Path) -> list[dict[str, str]]:
    rows = [plan.cells(x) for x in path.read_text(encoding="utf-8").splitlines() if x.lstrip().startswith("|")]
    if not rows or rows[0][0] != "ID":
        raise GateError(f"the gate cannot read {path}: no table with an ID column")
    return [dict(zip(rows[0], r, strict=False)) for r in rows[2:]]


def readiness_blocked(spec_dir: Path) -> list[str]:
    overview = spec_dir / "overview.md"
    if not overview.is_file():
        return []
    out = []
    for line in overview.read_text(encoding="utf-8").splitlines():
        row = plan.cells(line) if line.lstrip().startswith("|") else []
        if len(row) > 1 and row[1].startswith("Blocked"):
            out.append(" ".join(c for c in row if c and c != "-"))
    return out


def gate(cwd: Path, spec: str, spec_dir: Path | None = None) -> tuple[list[str], list[str]]:
    """(refusals, notes). No refusals means spec:complete may continue past its step 1.

    `spec_dir` defaults to the checked-out spec folder; `guard spec-status` passes a copy taken from a branch.
    """
    spec_dir = spec_dir or settings.spec_dir(cwd, spec)
    rollup_md, plan_md = (
        spec_dir / "review" / "rollup.md",
        spec_dir / "implementation-plan.md",
    )
    for need, what in (
        (rollup_md, "build it with `guard rollup`"),
        (plan_md, "the plan is needed"),
    ):
        if not need.is_file():
            raise GateError(f"the gate cannot run: {need} is absent ({what}); refusing")
    refusals = _refusals(spec_dir, decisions.latest(cwd, spec))
    exported = spec_dir / "review" / "decisions.jsonl"
    if refusals and exported.is_file() and _export_would_help(cwd, spec, spec_dir, exported, len(refusals)):
        refusals.append(
            f"{exported} holds owner decisions this clone lacks; "
            f"the owner runs `guard decisions import {spec}` (attended), then reruns the gate"
        )
    # A ticket with a marker_start entered a run, so its Blocked row is the run's, not Readiness's.
    entered = {t for t in evidence.tickets(cwd) if any(r["event"] == "marker_start" for r in evidence.records(cwd, t))}
    notes = [
        f"Blocked during a run: {t} ({cells[3] if len(cells) > 3 else ''})"
        for t, cells in plan.status_rows(plan_md).items()
        if t in entered and len(cells) > 1 and cells[1].startswith(plan.BLOCKED)
    ]
    notes += [
        f"Readiness-blocked, never entered the run: {r}"
        for r in readiness_blocked(spec_dir)
        if r.split()[0] not in entered
    ]
    return refusals, notes


def _export_would_help(cwd: Path, spec: str, spec_dir: Path, exported: Path, count: int) -> bool:
    """Only for the hint: the committed export is never trusted, so a broken one just gives no hint."""
    try:
        both = read_jsonl(decisions.path(cwd)) + read_jsonl(exported)
        return len(_refusals(spec_dir, decisions.latest(cwd, spec, both))) < count
    except (ValueError, KeyError, TypeError, AttributeError):
        return False


def _refusals(spec_dir: Path, owner: dict[str, str]) -> list[str]:
    rollup_md, plan_md = spec_dir / "review" / "rollup.md", spec_dir / "implementation-plan.md"
    refusals = []
    for row in _rollup_rows(rollup_md):
        tiers = {row.get("Tier", "").lower(), row.get("Suggested", "").lower()}
        if "blocking" not in tiers:
            continue
        status = row.get("Status", "").lower()
        logged = owner.get(row["ID"])
        if status == "fixed-verified" or logged in OWNER_STATUSES:
            continue
        refusals.append(f"{row['ID']}: blocking finding is {status or 'open'} ({row.get('Claim', '')})")
    # PR feedback rows use the rollup row format; every row counts, whatever its tier.
    for feedback in sorted((spec_dir / "review").glob("pr-feedback-*.md")):
        for row in _rollup_rows(feedback):
            if row.get("Status", "").lower() == "fixed-verified":
                continue
            if owner.get(row["ID"]) in FEEDBACK_OWNER_STATUSES:
                continue
            refusals.append(
                f"{row['ID']} ({feedback.name}): PR feedback is {row.get('Status') or 'open'} ({row.get('Claim', '')})"
            )
    for ticket, cells in plan.status_rows(plan_md).items():
        state = cells[1] if len(cells) > 1 else ""
        if state.startswith(plan.BLOCKED):
            if owner.get(ticket) != "accepted":
                refusals.append(
                    f"{ticket}: Blocked ({cells[3] if len(cells) > 3 else ''}); move it out or accept it with `guard decide {ticket} accepted`"
                )
        elif state not in FINISHED:
            refusals.append(f"{ticket}: {state or 'no status'}, not Done")
    refusals += docs.gate_refusals(spec_dir, plan_md.read_text(encoding="utf-8"))
    return refusals
