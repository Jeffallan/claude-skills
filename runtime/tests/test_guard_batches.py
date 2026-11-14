import json
import re
import stat
import sys

import pytest
from ticket_guard import plan
from ticket_guard.__main__ import main

# A stand-in for the claude binary. It logs its argv, and for a /goal prompt it marks the
# named tickets in the plan according to FAKE_MODE, then prints `--output-format json` output.
FAKE = r"""#!PYTHON
import json, os, re, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["FAKE_LOG"], "a") as log:
    log.write(json.dumps(args) + "\n")
prompt = args[args.index("-p") + 1]
mode = os.environ.get("FAKE_MODE", "ok")
result, code = "compacted", 0
if prompt.startswith("/goal"):
    tickets = re.search(r"tickets ([A-Z0-9, ]+?)\)", prompt).group(1).split(", ")
    plan = Path("docs/specs/todo/demo/implementation-plan.md")
    text = plan.read_text()
    for t in tickets:
        if mode == "stall":
            break
        status = "Blocked" if (mode == "block-t2" and t == "T2") else "Done"
        text = text.replace(f"| {t} | Pending | - | - |", f"| {t} | {status} | - | x |")
    plan.write_text(text)
    result = "BLOCKED: environment broken" if mode == "blocked" else "All done: evidence ..."
    code = 1 if mode == "exit1" else 0
print(json.dumps({"type": "result", "session_id": "S1", "result": result, "is_error": code != 0}))
sys.exit(code)
"""


def fake_claude(tmp_path, monkeypatch, mode="ok"):
    path = tmp_path / "claude"
    path.write_text(FAKE.replace("PYTHON", sys.executable))
    path.chmod(path.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "calls.jsonl"
    monkeypatch.setenv("FAKE_LOG", str(log))
    monkeypatch.setenv("FAKE_MODE", mode)
    return str(path), log


def calls(log):
    return [json.loads(x) for x in log.read_text().splitlines()]


def goal_prompt(git_repo):
    git_repo.write("docs/specs/todo/demo/goal-prompt.md", "<done_when>...</done_when>\n")
    git_repo.commit("goal prompt")  # spec:create commits it in a real spec


def statuses(git_repo):
    rows = plan.status_rows(git_repo.root / "docs/specs/todo/demo/implementation-plan.md")
    return {t: r[1] for t, r in rows.items()}


def test_runs_batches_in_one_session_with_compact_between(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--batch-size", "2", "--claude", claude]) == 0
    seen = calls(log)
    prompts = [c[c.index("-p") + 1] for c in seen]
    assert prompts[0].startswith("/goal ") and "tickets T1, T2)" in prompts[0]
    assert prompts[1] == "/compact"
    assert "tickets T3)" in prompts[2]
    assert len(seen) == 3  # no compact after the last batch
    assert "--resume" not in seen[0]
    for c in seen[1:]:
        assert c[c.index("--resume") + 1] == "S1"
    assert statuses(git_repo) == {"T1": "Done", "T2": "Done", "T3": "Done"}
    assert "every ticket is Done or Blocked" in capsys.readouterr().out


def test_every_call_carries_the_write_deny_set(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    git_repo.write(
        ".claude/workflow-config.json",
        json.dumps({"goal": {"batchSize": 3, "deny": ["mcp__jira__createIssue"]}}),
    )
    git_repo.commit("config")
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    for c in calls(log):
        denied = [c[i + 1] for i, a in enumerate(c) if a == "--disallowedTools"]
        for rule in (
            "AskUserQuestion",
            "Bash(git push:*)",
            "Bash(gh pr merge:*)",
            "Bash(gh issue close:*)",
            *(f"Bash(gh pr {v}:*)" for v in ("close", "reopen", "ready")),
            *(f"Bash(gh issue {v}:*)" for v in ("reopen", "delete", "transfer")),
            *(f"Bash(gh api {gap}{flag}*)" for flag in ("-X", "-f", "-F", "--method", "--field") for gap in ("", "* ")),
            "Bash(gh api * --raw-field*)",
            "Bash(gh api * --input*)",
            *(f"Bash(gh project {v}:*)" for v in ("item-add", "item-create", "edit", "unlink")),
            "Bash(gh release:*)",
            "Bash(*guard.pyz* decide *)",
            "Bash(*ticket_guard* decide *)",
            "Bash(*runtime* decide *)",
            "Bash(git rebase:*)",
            "Bash(git reset:*)",
            "Bash(git commit --amend:*)",
            "mcp__jira__createIssue",
        ):
            assert rule in denied
        assert "Bash(gh api * -X POST *)" not in denied
    assert "tickets T1, T2, T3)" in calls(log)[0][calls(log)[0].index("-p") + 1]


def allowed(call):
    return [call[i + 1] for i, a in enumerate(call) if a == "--allowedTools"]


def test_every_call_allows_the_ticket_guard_skill(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    for c in calls(log):
        assert allowed(c) == ["Skill(fullstack-dev-skills:ticket-guard)"]


def test_goal_allow_replaces_the_default_rule(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    git_repo.write(
        ".claude/workflow-config.json",
        json.dumps({"goal": {"allow": ["Skill(my-plugin:ticket-guard)", "Bash(make test)"]}}),
    )
    git_repo.commit("config")
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    for c in calls(log):
        assert allowed(c) == ["Skill(my-plugin:ticket-guard)", "Bash(make test)"]


def test_every_call_runs_in_auto_permission_mode(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--batch-size", "2", "--claude", claude]) == 0
    seen = calls(log)
    assert len(seen) == 3  # goal, /compact, goal
    for c in seen:
        assert c[c.index("--permission-mode") + 1] == "auto"


def test_permission_mode_and_extra_args_come_from_config(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    git_repo.write(
        ".claude/workflow-config.json",
        json.dumps(
            {
                "goal": {
                    "batchSize": 2,
                    "permissionMode": "acceptEdits",
                    "extraArgs": ["--plugin-dir", "/tmp/build"],
                }
            }
        ),
    )
    git_repo.commit("config")
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    for c in calls(log):
        assert c[0] == "-p"  # the prompt stays right after -p, ahead of variadic flags
        assert c[c.index("--permission-mode") + 1] == "acceptEdits"
        assert c[c.index("--plugin-dir") + 1] == "/tmp/build"


def test_bad_extra_args_are_refused_before_any_call(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    git_repo.write(
        ".claude/workflow-config.json",
        json.dumps({"goal": {"extraArgs": "--plugin-dir x"}}),
    )
    git_repo.commit("config")
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--claude", claude]) == 1
    assert "goal.extraArgs" in capsys.readouterr().err
    assert not log.exists()


def test_blocked_final_message_stops_the_runner(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, log = fake_claude(tmp_path, monkeypatch, "blocked")
    assert main(["run-batches", "demo", "--batch-size", "1", "--claude", claude]) == 1
    assert len(calls(log)) == 1
    assert "BLOCKED: environment broken" in capsys.readouterr().err


def test_exit_status_is_never_the_judge(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, _ = fake_claude(tmp_path, monkeypatch, "exit1")
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    assert set(statuses(git_repo).values()) == {"Done"}


def test_no_progress_stops_instead_of_looping(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, log = fake_claude(tmp_path, monkeypatch, "stall")
    assert main(["run-batches", "demo", "--claude", claude]) == 1
    assert len(calls(log)) == 1
    assert "no ticket in the batch reached Done or Blocked" in capsys.readouterr().err


def test_blocked_tickets_finish_the_run_and_lead_the_report(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, _ = fake_claude(tmp_path, monkeypatch, "block-t2")
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    out = capsys.readouterr().out
    assert re.search(r"Blocked:\n- T2", out)
    assert out.index("Blocked:\n") < out.index("Done:\n")


def test_nothing_left_runs_nothing(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    for t in ("T1", "T2", "T3"):
        plan.set_status(
            git_repo.root / "docs/specs/todo/demo/implementation-plan.md",
            t,
            "Done",
            "x",
        )
    claude, log = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    assert not log.exists()


def test_needs_the_goal_prompt(git_repo, capsys, tmp_path, monkeypatch):
    claude, _ = fake_claude(tmp_path, monkeypatch)
    assert main(["run-batches", "demo", "--claude", claude]) == 1
    assert "goal-prompt.md" in capsys.readouterr().err


def test_blocked_rows_left_uncommitted_are_committed_at_the_end(git_repo, capsys, tmp_path, monkeypatch):
    goal_prompt(git_repo)
    claude, _ = fake_claude(tmp_path, monkeypatch, "block-t2")
    assert main(["run-batches", "demo", "--claude", claude]) == 0
    assert git_repo.git("status", "--porcelain") == ""
    assert git_repo.git("log", "-1", "--format=%s") == "docs(demo): record Blocked rows in the plan"


def test_commit_plan_refuses_other_changes_and_skips_a_clean_plan(git_repo, capsys):
    assert main(["commit-plan", "demo"]) == 0
    assert "nothing to commit" in capsys.readouterr().out
    plan.set_status(
        git_repo.root / "docs/specs/todo/demo/implementation-plan.md",
        "T2",
        "Blocked",
        "x",
    )
    git_repo.write("src/app.py", "changed\n")
    assert main(["commit-plan", "demo"]) == 1
    assert "src/app.py" in capsys.readouterr().err
    git_repo.git("checkout", "--", "src/app.py")
    before = git_repo.head()
    assert main(["commit-plan", "demo"]) == 0
    assert git_repo.head() != before and git_repo.git("status", "--porcelain") == ""


def denied_by(rules, command):
    """Claude Code's Bash rule match: `:*` is a prefix match, `*` matches any text."""
    from fnmatch import fnmatchcase

    pats = [r[5:-1].replace(":*", "*") for r in rules if r.startswith("Bash(")]
    return any(fnmatchcase(command, p) for p in pats)


@pytest.mark.parametrize(
    "command",
    [
        "gh api repos/o/r/issues -ftitle=x",
        "gh api repos/o/r/issues -Fbody=@f",
        "gh api -f title=x repos/o/r/issues",
        "gh api -Fbody=@f repos/o/r/issues",
        "gh api repos/o/r/issues -f title=x",
        "gh api -XPOST repos/o/r/issues",
        "gh api repos/o/r/issues -X POST",
        "gh api repos/o/r/issues --method=POST",
        "gh api repos/o/r/issues --field title=x",
        "gh api repos/o/r/issues --raw-field title=x",
        "gh api repos/o/r/issues --input body.json",
        *(
            f"gh project {verb} 1 --owner o"
            for verb in (
                "close",
                "copy",
                "create",
                "delete",
                "edit",
                "field-create",
                "field-delete",
                "item-add",
                "item-archive",
                "item-create",
                "item-delete",
                "item-edit",
                "link",
                "mark-template",
                "unlink",
            )
        ),
    ],
)
def test_deny_set_blocks_gh_writes(command):
    from ticket_guard.batches import DENY

    assert denied_by(DENY, command)


@pytest.mark.parametrize(
    "command",
    [
        "gh api repos/o/my-fork/issues",
        "gh api repos/o/r-Xtra/pulls",
        "gh api repos/o/r/issues --jq .[].title",
        "gh project view 1 --owner o",
        "gh project item-list 1 --owner o",
        "gh project field-list 1 --owner o",
        "gh project list --owner o",
    ],
)
def test_deny_set_allows_gh_reads(command):
    from ticket_guard.batches import DENY

    assert not denied_by(DENY, command)


@pytest.mark.parametrize(
    "command",
    [
        'python3 "/plugins/fullstack-dev-skills/runtime/guard.pyz" decide F1 wontfix --spec demo',
        "PYTHONPATH=runtime python3 -m ticket_guard decide F1 wontfix",
        "python3 runtime decide F1 wontfix",
        "cd /plugin && python3 ./runtime decide T2 accepted",
    ],
)
def test_deny_set_blocks_every_way_to_call_decide(command):
    from ticket_guard.batches import DENY

    assert denied_by(DENY, command)


def test_kickoff_reserves_blocked_for_spec_wide_stops():
    """A ticket-level stop ends the batch normally; only a spec-wide stop earns BLOCKED:."""
    from ticket_guard.batches import kickoff

    text = kickoff("docs/specs/todo/demo/goal-prompt.md", ["T1", "T2"])
    assert "each Done or Blocked with its reason" in text
    assert "names a spec-wide stop from <stops>" in text
