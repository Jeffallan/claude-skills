import json

from ticket_guard import marker, specstatus
from ticket_guard.__main__ import main

OVERVIEW = "# {name}\n\n**Spec:** {name}\n**After:** {after}\n**Status:** {status}\n\n## Readiness\n"
ROLLUP = "# Review rollup\n\n| ID | Tier | Suggested | Status | Claim |\n|----|------|-----------|--------|-------|\n| F1 | {tier} | {tier} | open | x |\n"


def plan(statuses):
    rows = "\n".join(f"| T{i} | {s} | - | - |" for i, s in enumerate(statuses, 1))
    return (
        f"# Plan\n\n## Completion Status\n\n| Ticket | Status | Completed Date | Notes |\n|---|---|---|---|\n{rows}\n"
    )


def on_branch(repo, name, files, completed=False):
    """Commit a spec's files on spec/<name>, then return to main."""
    repo.git("switch", "-q", "-c", f"spec/{name}")
    folder = "completed" if completed else "todo"
    for rel, text in files.items():
        repo.write(f"docs/specs/{folder}/{name}/{rel}", text)
    repo.commit(f"spec {name}")
    repo.git("switch", "-q", "main")


def rows(repo, **kw):
    kw.setdefault("pr_lookup", lambda branch: None)
    return {r["spec"]: r for r in specstatus.collect(repo.root, **kw)}


def test_states_follow_the_files_on_each_spec_branch(git_repo):
    git_repo.git("branch", "spec/triaged")
    on_branch(
        git_repo,
        "draft",
        {"overview.md": OVERVIEW.format(name="draft", after="none", status="Draft, waiting for owner approval")},
    )
    on_branch(
        git_repo,
        "busy",
        {
            "overview.md": OVERVIEW.format(name="busy", after="draft", status="Approved 2026-11-12"),
            "implementation-plan.md": plan(["Done", "Pending", "Blocked: decision"]),
        },
    )
    on_branch(git_repo, "built", {"implementation-plan.md": plan(["Done", "Done"])})
    on_branch(
        git_repo,
        "review",
        {"implementation-plan.md": plan(["Done"]), "review/rollup.md": ROLLUP.format(tier="blocking")},
    )
    on_branch(
        git_repo,
        "ready",
        {"implementation-plan.md": plan(["Done"]), "review/rollup.md": ROLLUP.format(tier="advisory")},
    )
    got = rows(git_repo)
    assert got["triaged"]["state"] == "Triaged" and got["triaged"]["next"] == "spec:create triaged"
    assert got["draft"]["state"] == "Drafting"
    assert got["demo"]["state"] == "Planned"  # only on main: the plan with every ticket Pending
    assert got["busy"]["state"] == "In progress"
    assert (got["busy"]["done"], got["busy"]["blocked"], got["busy"]["pending"]) == (1, 1, 1)
    assert got["busy"]["after"] == ["draft"]
    assert got["built"]["state"] == "Ready for review" and got["built"]["next"] == "spec:review built"
    assert got["review"]["state"] == "In review"
    assert got["ready"]["state"] == "Ready to complete" and got["ready"]["next"] == "spec:complete ready"


def test_a_spec_only_on_the_current_branch_is_listed_as_unbranched(git_repo, capsys, monkeypatch):
    git_repo.git("switch", "-q", "-c", "feat/units")
    git_repo.write("docs/specs/todo/units/overview.md", OVERVIEW.format(name="units", after="none", status="Approved"))
    git_repo.write("docs/specs/todo/units/implementation-plan.md", plan(["Done", "Pending"]))
    git_repo.commit("units spec, no spec branch")
    got = rows(git_repo)
    units = got["units"]
    assert units["state"] == "Unbranched (on feat/units)"
    assert units["branch"] is None and units["pr"] is None
    assert (units["done"], units["blocked"], units["pending"]) == (1, 0, 1)
    assert "spec/units" in units["next"]
    assert got["demo"]["state"] == "Planned"  # normal specs keep their state
    monkeypatch.setattr(specstatus, "gh_pr", lambda cwd, branch: None)
    assert main(["spec-status"]) == 0
    assert "| units | Unbranched (on feat/units) | 1 / 0 / 1 |" in capsys.readouterr().out


def test_the_marker_names_the_live_ticket(git_repo):
    marker.start(git_repo.root, "demo", "T2", "goal")
    assert rows(git_repo)["demo"]["ticket"] == "T2"


def github(repo, **extra):
    repo.write(".claude/workflow-config.json", json.dumps({"codeHost": {"type": "github"}, **extra}))
    repo.commit("config")


def test_pr_state_and_completed_specs(git_repo):
    github(git_repo)
    on_branch(git_repo, "shipping", {"implementation-plan.md": plan(["Done"])}, completed=True)
    git_repo.write("docs/specs/completed/old/implementation-plan.md", plan(["Done"]))
    git_repo.commit("old spec merged")
    prs = {"spec/shipping": {"number": 7, "state": "OPEN"}}
    got = rows(git_repo, pr_lookup=prs.get)
    assert got["shipping"]["state"] == "PR open" and got["shipping"]["pr"] == "#7 open"
    assert "old" not in got
    assert rows(git_repo, include_completed=True)["old"]["state"] == "Completed"


def test_cli_prints_a_table_and_json(git_repo, capsys, monkeypatch):
    monkeypatch.setattr(specstatus, "gh_pr", lambda cwd, branch: None)
    assert main(["spec-status"]) == 0
    out = capsys.readouterr().out
    assert "| demo | Planned | 0 / 0 / 3 | - | - | - | launch the goal run spec:create printed |" in out
    assert main(["spec-status", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["spec"] == "demo"


def spy():
    calls = []

    def lookup(branch):
        calls.append(branch)
        return {"number": 1, "state": "OPEN"}

    return calls, lookup


def test_no_pr_lookup_without_github(git_repo):
    git_repo.write(".claude/workflow-config.json", json.dumps({"codeHost": {"type": "none"}}))
    git_repo.commit("config")
    on_branch(git_repo, "built", {"implementation-plan.md": plan(["Done"])})
    calls, lookup = spy()
    got = rows(git_repo, pr_lookup=lookup)
    assert calls == [] and got["built"]["pr"] is None and got["built"]["state"] == "Ready for review"


def test_pr_lookup_can_be_turned_off(git_repo):
    github(git_repo, status={"pullRequests": False})
    on_branch(git_repo, "built", {"implementation-plan.md": plan(["Done"])})
    calls, lookup = spy()
    rows(git_repo, pr_lookup=lookup)
    assert calls == []


def test_a_failed_pr_lookup_marks_the_column_unknown(git_repo):
    github(git_repo)
    on_branch(git_repo, "built", {"implementation-plan.md": plan(["Done"])})

    def broken(branch):
        raise specstatus.GuardError("gh is not signed in")

    got = rows(git_repo, pr_lookup=broken)
    assert got["built"]["pr"] == "unknown" and got["built"]["state"] == "Ready for review"
