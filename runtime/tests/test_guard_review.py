import json
import stat
import sys

from ticket_guard import metrics, review
from ticket_guard.__main__ import main

REVIEW = "docs/specs/todo/demo/review"


def transcript(path, messages):
    """Write a subagent transcript: (message id, usage, timestamp) per assistant entry."""
    lines = [{"type": "user", "timestamp": "2026-11-09T10:00:00.000Z", "message": {}}]
    for mid, usage, ts in messages:
        lines.append(
            {
                "type": "assistant",
                "timestamp": ts,
                "message": {"id": mid, "usage": usage},
            }
        )
    path.write_text("\n".join(json.dumps(x) for x in lines) + "\n")


U = {
    "input_tokens": 10,
    "output_tokens": 90,
    "cache_read_input_tokens": 300_000,
    "cache_creation_input_tokens": 1_900,
}

FINDINGS = [
    {
        "id": "F3",
        "tier": "blocking",
        "suggested": "blocking",
        "sources": ["code-reviewer", "test-master"],
        "location": "src/app.py:1",
        "claim": "Races logout",
        "verdict": "confirmed",
        "proof": "ran",
        "evidence": "review/repro/F3.test.py, exit 1",
        "reason": "Stale token",
        "agent_id": "abc",
        "status": "open",
    },
    {
        "id": "F7",
        "tier": "warning",
        "suggested": "blocking",
        "sources": "security-reviewer",
        "location": "api.py:8",
        "claim": "Unvalidated id",
        "verdict": "rejected",
        "proof": "read",
        "evidence": "api.py:80",
        "reason": "Unreachable",
        "status": "wontfix",
    },
    {
        "id": "F9",
        "tier": "advisory",
        "suggested": "advisory",
        "sources": "test-master",
        "location": "t.py:2",
        "claim": "Untested | edge",
        "verdict": "unresolved",
        "proof": "none",
        "evidence": "-",
        "reason": "Could not run",
        "status": "open",
    },
]


def rollup(git_repo, capsys, findings=FINDINGS, extra=()):
    tdir = git_repo.root.parent / "subagents"
    tdir.mkdir(exist_ok=True)
    transcript(
        tdir / "agent-abc.jsonl",
        [
            ("m1", U, "2026-11-09T10:01:00.000Z"),
            ("m1", U, "2026-11-09T10:01:00.500Z"),  # one message split in two entries
            ("m2", U, "2026-11-09T10:06:10.000Z"),
        ],
    )
    verdicts = git_repo.root.parent / "verdicts.json"
    verdicts.write_text(json.dumps(findings))
    code = main(
        [
            "rollup",
            "demo",
            "--verdicts",
            str(verdicts),
            "--transcripts",
            str(tdir),
            *extra,
        ]
    )
    capsys.readouterr()
    return code


def table(git_repo):
    from ticket_guard.plan import cells

    lines = (git_repo.root / REVIEW / "rollup.md").read_text().splitlines()
    rows = [cells(x) for x in lines if x.startswith("|")]
    header = rows[0]
    return {r[0]: dict(zip(header, r, strict=True)) for r in rows[2:]}


# rollup ---------------------------------------------------------------------------


def test_rollup_lists_every_finding_with_cost_from_the_transcript(git_repo, capsys):
    assert rollup(git_repo, capsys) == 0
    rows = table(git_repo)
    assert list(rows) == ["F3", "F7", "F9"]
    f3 = rows["F3"]
    assert f3["Sources"] == "code-reviewer, test-master"
    assert f3["Tokens"] == "604,000"  # 2 messages x 302,000, the split entry counted once
    assert f3["Minutes"] == "6"  # 10:00:00 brief to 10:06:10 last reply
    assert rows["F9"]["Tokens"] == "-"
    assert rows["F9"]["Claim"] == "Untested \\| edge"


def test_rollup_counts_a_shared_verifier_once(git_repo, capsys):
    batch = [dict(FINDINGS[2], id=f"A{n}", agent_id="abc", tier="advisory") for n in (1, 2, 3)]
    assert rollup(git_repo, capsys, findings=batch) == 0
    rows = table(git_repo)
    assert (rows["A1"]["Tokens"], rows["A1"]["Minutes"]) == ("604,000", "6")
    for other in ("A2", "A3"):
        assert rows[other]["Tokens"] == rows[other]["Minutes"] == "shared with A1"


def test_rollup_takes_owner_statuses_only_from_decisions(git_repo, capsys):
    rollup(git_repo, capsys)
    assert table(git_repo)["F7"]["Status"] == "open"
    main(["decide", "F7", "wontfix", "--spec", "demo"])
    rollup(git_repo, capsys)
    assert table(git_repo)["F7"]["Status"] == "wontfix"


def test_rollup_rejects_findings_without_an_id(git_repo, capsys):
    verdicts = git_repo.root.parent / "v.json"
    verdicts.write_text(json.dumps([{"tier": "blocking"}]))
    assert main(["rollup", "demo", "--verdicts", str(verdicts)]) == 1


# gate -----------------------------------------------------------------------------


def done_plan(git_repo, t2="Done", t2_note="-"):
    path = git_repo.root / "docs/specs/todo/demo/implementation-plan.md"
    text = path.read_text()
    text = text.replace("| T1 | Pending | - | - |", "| T1 | Done | 2026-11-10 | ok |")
    text = text.replace("| T2 | Pending | - | - |", f"| T2 | {t2} | - | {t2_note} |")
    text = text.replace("| T3 | Pending | - | - |", "| T3 | Done | 2026-11-10 | ok |")
    path.write_text(text)


def gate(capsys):
    code = main(["gate", "demo"])
    out = capsys.readouterr()
    return code, out.out + out.err


def test_gate_refuses_open_blocking_rows(git_repo, capsys):
    done_plan(git_repo)
    rollup(git_repo, capsys)
    code, out = gate(capsys)
    assert code == 1
    assert "F3" in out and "F7" in out and "F9" not in out


def test_gate_passes_fixed_verified_and_logged_owner_statuses(git_repo, capsys):
    done_plan(git_repo)
    findings = [dict(FINDINGS[0], status="fixed-verified"), FINDINGS[1], FINDINGS[2]]
    rollup(git_repo, capsys, findings)
    main(["decide", "F7", "rejection-accepted", "--spec", "demo"])
    capsys.readouterr()
    code, out = gate(capsys)
    assert code == 0, out


def test_gate_ignores_owner_statuses_edited_into_the_markdown(git_repo, capsys):
    done_plan(git_repo)
    rollup(git_repo, capsys, [dict(FINDINGS[0], status="fixed-verified")])
    path = git_repo.root / REVIEW / "rollup.md"
    path.write_text(path.read_text().replace("fixed-verified", "wontfix"))
    code, out = gate(capsys)
    assert code == 1 and "F3" in out


def test_gate_refuses_blocked_tickets_until_accepted(git_repo, capsys):
    done_plan(git_repo, t2="Blocked", t2_note="needs a decision")
    rollup(git_repo, capsys, [dict(FINDINGS[0], status="fixed-verified")])
    code, out = gate(capsys)
    assert code == 1 and "T2" in out
    main(["decide", "T2", "accepted", "--spec", "demo"])
    assert gate(capsys)[0] == 0


def test_gate_refuses_unfinished_tickets(git_repo, capsys):
    rollup(git_repo, capsys, [dict(FINDINGS[0], status="fixed-verified")])
    code, out = gate(capsys)
    assert code == 1 and "T1" in out and "Pending" in out


def test_gate_fails_closed_without_a_rollup(git_repo, capsys):
    done_plan(git_repo)
    code, out = gate(capsys)
    assert code == 2 and "rollup" in out


def test_gate_lists_readiness_blocked_tickets(git_repo, capsys):
    done_plan(git_repo)
    rollup(git_repo, capsys, [dict(FINDINGS[0], status="fixed-verified")])
    git_repo.write(
        "docs/specs/todo/demo/overview.md",
        "# Demo\n\n**Spec:** demo\n\n## Readiness\n\n| Ticket | Readiness | Note |\n"
        "|---|---|---|\n| T1 | Ready | - |\n| T8 | Blocked: question | Which DB? |\n",
    )
    code, out = gate(capsys)
    assert code == 0 and "T8" in out and "Which DB?" in out


# metrics --------------------------------------------------------------------------


def fake_tool(bin_dir, name, output, code=0):
    path = bin_dir / name
    path.write_text(f"#!{sys.executable}\nprint({output!r})\nraise SystemExit({code})\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    return str(path)


def test_metrics_runs_installed_tools_and_notes_missing_ones(git_repo, capsys, monkeypatch, tmp_path):
    base = git_repo.head()
    git_repo.write("src/app.py", "def add(a, b):\n    return a + b\n\n\ndef unused():\n    pass\n")
    git_repo.write("web/a.ts", "export const x = 1\n")
    git_repo.commit("work")
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    tools = {
        "vulture": fake_tool(bin_dir, "vulture", "src/app.py:5: unused function 'unused'", 3),
        "lizard": fake_tool(bin_dir, "lizard", "NLOC CCN\n2 1 add@1-2@src/app.py"),
    }
    monkeypatch.setattr(metrics.shutil, "which", lambda name: tools.get(name))
    assert main(["metrics", "demo", "--base", base]) == 0
    text = (git_repo.root / REVIEW / "metrics.md").read_text()
    assert "unused function 'unused'" in text
    assert "add@1-2@src/app.py" in text
    assert "jscpd: not installed" in text and "knip: not installed" in text
    assert "src/app.py" in text and "web/a.ts" in text


def test_metrics_with_no_tools_still_writes_the_file(git_repo, capsys, monkeypatch):
    base = git_repo.head()
    git_repo.write("src/app.py", "def add(a, b):\n    return a + b + 0\n")
    git_repo.write("web/a.ts", "export const x = 1\n")
    git_repo.commit("work")
    monkeypatch.setattr(metrics.shutil, "which", lambda name: None)
    assert main(["metrics", "demo", "--base", base]) == 0
    text = (git_repo.root / REVIEW / "metrics.md").read_text()
    assert text.count("not installed") == 4


def test_metrics_skips_tools_for_languages_the_diff_lacks(git_repo, capsys, monkeypatch):
    base = git_repo.head()
    git_repo.write("web/a.ts", "export const x = 1\n")
    git_repo.commit("ts only")
    monkeypatch.setattr(metrics.shutil, "which", lambda name: None)
    assert main(["metrics", "demo", "--base", base]) == 0
    text = (git_repo.root / REVIEW / "metrics.md").read_text()
    assert "vulture: no changed files it reads" in text and "vulture: not installed" not in text
    assert "knip: not installed" in text


def pr_feedback(git_repo, status, row_id="P1"):
    header = "| " + " | ".join(review.COLUMNS) + " |\n|" + "---|" * len(review.COLUMNS)
    row = f"| {row_id} | advisory | advisory | reviewer | a.py:1 | Rename x | - | - | link | - | - | - | {status} |"
    git_repo.write(f"{REVIEW}/pr-feedback-1.md", f"# PR feedback, round 1\n\n{header}\n{row}\n")


def test_gate_refuses_pr_feedback_rows_not_fixed_verified(git_repo, capsys):
    done_plan(git_repo)
    rollup(git_repo, capsys, [dict(FINDINGS[0], status="fixed-verified")])
    pr_feedback(git_repo, "open")
    code, out = gate(capsys)
    assert code == 1 and "P1" in out and "pr-feedback-1.md" in out
    pr_feedback(git_repo, "fixed-verified")
    assert gate(capsys)[0] == 0


def test_gate_accepts_logged_owner_status_on_pr_feedback(git_repo, capsys):
    done_plan(git_repo)
    rollup(git_repo, capsys, [dict(FINDINGS[0], status="fixed-verified")])
    pr_feedback(git_repo, "wontfix")
    assert gate(capsys)[0] == 1  # markdown alone is not trusted
    main(["decide", "P1", "wontfix", "--spec", "demo"])
    assert gate(capsys)[0] == 0


def test_answered_closes_pr_feedback_questions_but_not_review_findings(git_repo, capsys):
    done_plan(git_repo)
    rollup(git_repo, capsys, [FINDINGS[0]])
    pr_feedback(git_repo, "open", row_id="P2")
    main(["decide", "P2", "answered", "--spec", "demo"])
    main(["decide", "F3", "answered", "--spec", "demo"])
    capsys.readouterr()
    code, out = gate(capsys)
    assert code == 1 and "F3" in out and "P2" not in out
