import json
import tarfile

from ticket_guard import evidence, marker, plan
from ticket_guard.__main__ import main


def rows(git_repo):
    return plan.status_rows(git_repo.root / "docs/specs/todo/demo/implementation-plan.md")


def test_block_saves_work_restores_start_and_clears_marker(git_repo, capsys):
    git_repo.write(
        "docs/specs/todo/demo/implementation-plan.md",
        git_repo.root.joinpath("docs/specs/todo/demo/implementation-plan.md")
        .read_text()
        .replace("| T3 | Pending | - | - |", "| T3 | Blocked | - | earlier block |"),
    )
    start = marker.start(git_repo.root, "demo", "T1", "goal")["start_sha"]
    git_repo.write("src/app.py", "def add(a, b):\n    return 0\n")
    git_repo.write("src/new.py", "NEW = 1\n")
    git_repo.write("tests/test_new.py", "def test_new():\n    assert False\n")

    assert main(["block", "T1", "contradicts the spec"]) == 0

    blocked = git_repo.guard / "blocked"
    patch = (blocked / "T1.patch").read_text()
    assert "return 0" in patch and "implementation-plan" not in patch
    with tarfile.open(blocked / "T1-untracked.tar.gz") as tar:
        assert sorted(tar.getnames()) == ["src/new.py", "tests/test_new.py"]
    assert git_repo.head() == start
    assert git_repo.git("status", "--porcelain") == ("M docs/specs/todo/demo/implementation-plan.md")
    assert "return a + b" in (git_repo.root / "src/app.py").read_text()
    assert not (git_repo.root / "src/new.py").exists()
    assert rows(git_repo)["T1"] == ["T1", "Blocked", "-", "contradicts the spec"]
    assert rows(git_repo)["T3"][1:] == ["Blocked", "-", "earlier block"]
    assert marker.read(git_repo.root) is None
    events = [r["event"] for r in evidence.records(git_repo.root, "T1")]
    assert events[-2:] == ["blocked", "marker_clear"]

    # the saved work re-applies cleanly
    git_repo.git("apply", str(blocked / "T1.patch"))
    assert "return 0" in (git_repo.root / "src/app.py").read_text()


def test_block_refuses_when_head_moved_past_start(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("x.txt", "x")
    git_repo.commit("unexpected")
    assert main(["block", "T1", "why"]) == 1
    assert "HEAD has moved past the start SHA" in capsys.readouterr().err
    assert marker.read(git_repo.root) is not None
    assert (git_repo.root / "x.txt").exists()
    assert rows(git_repo)["T1"][1] == "Pending"


def test_block_a_dependent_writes_only_the_row(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("src/app.py", "wip\n")
    assert main(["block", "T2", "depends on T1"]) == 0
    assert rows(git_repo)["T2"][1:] == ["Blocked", "-", "depends on T1"]
    assert marker.read(git_repo.root)["ticket"] == "T1"
    assert (git_repo.root / "src/app.py").read_text() == "wip\n"
    assert evidence.records(git_repo.root, "T2")[-1]["event"] == "blocked"


def test_block_without_marker_finds_the_plan(git_repo, capsys):
    assert main(["block", "T3", "needs a decision"]) == 0
    assert rows(git_repo)["T3"][1] == "Blocked"
    assert main(["block", "T9", "x"]) == 1
    assert "T9" in capsys.readouterr().err


def test_block_escapes_pipes_in_the_reason(git_repo):
    assert main(["block", "T3", "a | b"]) == 0
    assert rows(git_repo)["T3"][3] == "a \\| b"


def test_decide_appends_to_the_log(git_repo, capsys, monkeypatch):
    monkeypatch.setenv("CLAUDE_SESSION_ID", "sess-9")
    assert main(["decide", "F3", "wontfix", "--spec", "demo"]) == 0
    assert main(["decide", "T2", "accepted"]) == 0
    lines = (git_repo.guard / "decisions.jsonl").read_text().splitlines()
    first = json.loads(lines[0])
    assert (first["row"], first["status"], first["session_id"], first["spec"]) == (
        "F3",
        "wontfix",
        "sess-9",
        "demo",
    )
    assert first["at"]
    from ticket_guard import decisions

    assert decisions.latest(git_repo.root, "demo") == {
        "F3": "wontfix",
        "T2": "accepted",
    }


def test_decide_rejects_unknown_status_and_goal_mode(git_repo, capsys):
    assert main(["decide", "F3", "fixed-verified"]) == 1
    assert "wontfix" in capsys.readouterr().err
    marker.start(git_repo.root, "demo", "T1", "goal")
    assert main(["decide", "F3", "wontfix"]) == 1
    assert "attended" in capsys.readouterr().err
    assert not (git_repo.guard / "decisions.jsonl").exists()


def test_block_with_a_lost_marker_saves_and_restores_from_evidence(git_repo, capsys):
    start = marker.start(git_repo.root, "demo", "T1", "goal")["start_sha"]
    git_repo.write("src/app.py", "def add(a, b):\n    return 0\n")
    git_repo.write("src/new.py", "NEW = 1\n")
    marker.path(git_repo.root).unlink()  # lost mid-ticket, no logged clear

    assert main(["block", "T1", "marker lost"]) == 0

    blocked = git_repo.guard / "blocked"
    assert "return 0" in (blocked / "T1.patch").read_text()
    with tarfile.open(blocked / "T1-untracked.tar.gz") as tar:
        assert tar.getnames() == ["src/new.py"]
    assert git_repo.head() == start
    assert "return a + b" in (git_repo.root / "src/app.py").read_text()
    assert not (git_repo.root / "src/new.py").exists()
    assert rows(git_repo)["T1"][1:] == ["Blocked", "-", "marker lost"]
    recs = evidence.records(git_repo.root, "T1")
    assert [r["event"] for r in recs[-2:]] == ["blocked", "marker_clear"]
    assert recs[-1]["lost"] is True


def test_block_with_start_and_no_evidence(git_repo, capsys):
    start = git_repo.head()
    git_repo.write("src/app.py", "wip\n")
    assert main(["block", "T3", "why", "--start", start]) == 0
    assert "return a + b" in (git_repo.root / "src/app.py").read_text()
    assert (git_repo.guard / "blocked/T3.patch").read_text().count("wip") == 1


def test_block_with_a_lost_marker_refuses_when_head_moved(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    marker.path(git_repo.root).unlink()
    git_repo.write("x.txt", "x")
    git_repo.commit("unexpected")
    assert main(["block", "T1", "why"]) == 1
    assert "HEAD has moved past the start SHA" in capsys.readouterr().err
    assert (git_repo.root / "x.txt").exists()
    assert rows(git_repo)["T1"][1] == "Pending"


def test_block_start_refuses_while_another_ticket_holds_the_marker(git_repo, capsys):
    start = marker.start(git_repo.root, "demo", "T1", "goal")["start_sha"]
    git_repo.write("src/app.py", "wip\n")
    assert main(["block", "T2", "why", "--start", start]) == 1
    assert "T1" in capsys.readouterr().err
    assert (git_repo.root / "src/app.py").read_text() == "wip\n"
