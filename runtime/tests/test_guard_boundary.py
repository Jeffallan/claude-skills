import json
import sys

import pytest
from ticket_guard import boundary, evidence, marker
from ticket_guard.__main__ import main

PYTEST = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
SUB_TEST = "def test_sub():\n    from src.app import sub\n    assert sub(3, 1) == 2\n"
SUB_CODE = "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n"


def finished_ticket(git_repo, capsys, mode="goal"):
    """T1 with RED and GREEN recorded and the work uncommitted, as ticket:complete sees it."""
    marker.start(git_repo.root, "demo", "T1", mode)
    git_repo.write("tests/test_sub.py", SUB_TEST)
    assert main(["run", "red", "--", *PYTEST, "tests/test_sub.py"]) == 0
    git_repo.write("src/app.py", SUB_CODE)
    assert main(["run", "green", "--", *PYTEST]) == 0
    capsys.readouterr()


def last(git_repo, event):
    return [r for r in evidence.records(git_repo.root, "T1") if r["event"] == event][-1]


# clean re-run ---------------------------------------------------------------------


def test_rerun_runs_the_candidate_in_a_clean_worktree(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    (git_repo.root / "stray.txt").write_text("ignored? no, untracked", encoding="utf-8")
    assert main(["rerun", "--", *PYTEST]) == 0
    rec = last(git_repo, "boundary")
    assert (rec["check"], rec["exit_code"], rec["passed"]) == ("rerun", 0, True)
    assert rec["cwd"] != str(git_repo.root)
    assert git_repo.git("worktree", "list").count("\n") == 0  # temp worktree removed


def test_rerun_fails_when_the_candidate_fails(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    git_repo.write("src/app.py", "def add(a, b):\n    return a + b\n")
    assert main(["rerun", "--", *PYTEST]) == 1
    assert last(git_repo, "boundary")["passed"] is False


def test_rerun_uses_verify_from_config_then_green(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    assert main(["rerun"]) == 0
    assert last(git_repo, "boundary")["command"].endswith("no:cacheprovider")
    git_repo.write(
        ".claude/workflow-config.json",
        json.dumps({"verify": [f"{sys.executable} -c 'raise SystemExit(3)'"]}),
    )
    assert main(["rerun"]) == 1


def setup_config(git_repo, tmp_path, setup_exit=0):
    """A setup command that records where it ran, and a verify command that needs it."""
    seen = tmp_path / "setup-ran"
    setup = (
        f"{sys.executable} -c \"import os; open('ready', 'w');"
        f" open({str(seen)!r}, 'a').write(os.getcwd() + '\\n');"
        f' raise SystemExit({setup_exit})"'
    )
    verify = f"{sys.executable} -c \"import os; raise SystemExit(0 if os.path.exists('ready') else 3)\""
    git_repo.write(
        ".claude/workflow-config.json",
        json.dumps({"setup": [setup], "verify": [verify]}),
    )
    return seen


def test_rerun_runs_setup_in_the_worktree_before_verify(git_repo, capsys, tmp_path):
    finished_ticket(git_repo, capsys)
    seen = setup_config(git_repo, tmp_path)
    assert main(["rerun"]) == 0
    rec = last(git_repo, "boundary")
    assert rec["passed"] is True
    assert seen.read_text().strip() == rec["cwd"] != str(git_repo.root)


def test_rerun_fails_when_setup_fails(git_repo, capsys, tmp_path):
    finished_ticket(git_repo, capsys)
    setup_config(git_repo, tmp_path, setup_exit=4)
    assert main(["rerun"]) == 1
    rec = last(git_repo, "boundary")
    assert (rec["passed"], rec["exit_code"]) == (False, 4)
    assert rec["reason"].startswith("setup command failed")


def test_setup_must_be_a_list_of_strings(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    git_repo.write(".claude/workflow-config.json", json.dumps({"setup": "npm ci"}))
    assert main(["rerun", "--", *PYTEST]) != 0
    assert "setup must be a list of shell strings" in capsys.readouterr().err


# RED replay -----------------------------------------------------------------------


def test_red_replay_fails_new_tests_against_the_start_sha(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    assert main(["red-replay"]) == 0
    rec = last(git_repo, "boundary")
    assert (rec["check"], rec["passed"]) == ("red-replay", True)
    assert rec["exit_code"] != 0
    assert rec["head_sha"] == marker.read(git_repo.root)["start_sha"]


def test_red_replay_fails_when_the_test_passes_on_the_base(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("tests/test_add2.py", "def test_x():\n    assert False\n")
    main(["run", "red", "--", *PYTEST, "tests/test_add2.py"])
    git_repo.write("tests/test_add2.py", "def test_x():\n    assert True\n")
    assert main(["red-replay"]) == 1
    assert "passed against the start SHA" in capsys.readouterr().err


def test_red_replay_runs_setup_on_the_start_sha(git_repo, capsys, tmp_path):
    finished_ticket(git_repo, capsys)
    seen = setup_config(git_repo, tmp_path)
    assert main(["red-replay"]) == 0
    rec = last(git_repo, "boundary")
    assert seen.read_text().strip() == rec["cwd"]
    assert rec["head_sha"] == marker.read(git_repo.root)["start_sha"]


def test_red_replay_fails_when_setup_fails(git_repo, capsys, tmp_path):
    finished_ticket(git_repo, capsys)
    setup_config(git_repo, tmp_path, setup_exit=4)
    assert main(["red-replay"]) == 1
    rec = last(git_repo, "boundary")
    assert rec["passed"] is False
    assert rec["reason"].startswith("setup command failed")


def test_red_replay_is_skipped_for_refactor_tickets(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    assert main(["run", "red", "--type", "refactor", "--", *PYTEST]) == 0
    assert main(["red-replay"]) == 0
    assert last(git_repo, "boundary")["skipped"] == "refactor ticket (answer 102)"


# tamper scan ----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("setup", "kind"),
    [
        (lambda r: (r.root / "tests/test_app.py").unlink(), "deleted-test"),
        (
            lambda r: r.write(
                "tests/test_app.py",
                "import pytest\n\n\n@pytest.mark.skip\ndef test_add():\n    assert 1\n",
            ),
            "skip-added",
        ),
        (
            lambda r: r.write("tests/test_it.js", "it.only('x', () => expect(1))\n"),
            "skip-added",
        ),
        (
            lambda r: r.write("tests/test_none.py", "def test_none():\n    x = 1\n"),
            "no-assertion",
        ),
        (
            lambda r: r.write(
                "tests/test_mock.py",
                "def test_m(mocker):\n    m = mocker.Mock()\n    m()\n    m.assert_called_once()\n",
            ),
            "mock-only",
        ),
    ],
)
def test_tamper_scan_flags(git_repo, capsys, setup, kind):
    marker.start(git_repo.root, "demo", "T1", "goal")
    setup(git_repo)
    assert main(["tamper-scan"]) == 1
    flags = last(git_repo, "tamper_scan")["flags"]
    assert [f["kind"] for f in flags] == [kind]
    assert flags[0]["id"] == "TS1"


def test_tamper_scan_flags_a_js_test_case_without_assertion(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("tests/test_case.test.js", "test('adds', () => { add(1, 2) })\n")
    assert main(["tamper-scan"]) == 1
    assert [f["kind"] for f in last(git_repo, "tamper_scan")["flags"]] == ["no-assertion"]


def test_tamper_scan_skips_a_test_helper_with_no_test_cases(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("tests/register.ts", "export async function register(app) {\n  return app.post('/x')\n}\n")
    assert main(["tamper-scan"]) == 0
    assert last(git_repo, "tamper_scan")["flags"] == []


def test_tamper_scan_flags_changed_snapshots_not_new_ones(git_repo, capsys):
    git_repo.write("tests/__snapshots__/a.snap", "old\n")
    git_repo.commit("snap")
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("tests/__snapshots__/a.snap", "new\n")
    git_repo.write("tests/__snapshots__/b.snap", "added\n")
    assert main(["tamper-scan"]) == 1
    flags = last(git_repo, "tamper_scan")["flags"]
    assert [(f["kind"], f["file"]) for f in flags] == [("snapshot-changed", "tests/__snapshots__/a.snap")]


def test_tamper_scan_passes_clean_work_and_reasoned_flags(git_repo, capsys):
    finished_ticket(git_repo, capsys, mode="attended")
    assert main(["tamper-scan"]) == 0
    git_repo.write("tests/test_none.py", "def test_none():\n    x = 1\n")
    assert main(["tamper-scan", "--reason", "TS1=smoke test, import only"]) == 0
    assert last(git_repo, "tamper_scan")["flags"][0]["reason"] == "smoke test, import only"


# summary --------------------------------------------------------------------------


def test_summary_after_every_check(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    for cmd in (["rerun"], ["red-replay"], ["tamper-scan"]):
        assert main([*cmd]) == 0
    capsys.readouterr()
    assert main(["summary"]) == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("RED `")
    for part in (
        "exit 1",
        "GREEN `",
        "exit 0",
        "tests sha256 ",
        "clean re-run exit 0",
        "RED replay exit 1",
        "tamper scan: no flags",
    ):
        assert part in out


def test_summary_tests_digest_follows_the_documented_recipe(git_repo, capsys):
    import hashlib
    import re

    finished_ticket(git_repo, capsys)
    for cmd in (["rerun"], ["red-replay"], ["tamper-scan"]):
        main([*cmd])
    capsys.readouterr()
    main(["summary"])
    shown = re.search(r"tests sha256 (\w+) \((\d+) files\)", capsys.readouterr().out)
    # The recipe in `guard summary --help`: the RED test files sorted by repo path, each
    # fed as path, NUL, raw sha256 of its bytes; the first 12 hex characters are shown.
    h = hashlib.sha256()
    for rel in ["tests/test_sub.py"]:
        content = (git_repo.root / rel).read_bytes()
        h.update(rel.encode() + b"\0" + hashlib.sha256(content).digest())
    assert shown.groups() == (h.hexdigest()[:12], "1")
    with pytest.raises(SystemExit):
        main(["summary", "--help"])
    helptext = " ".join(capsys.readouterr().out.split())
    assert "sorted by repo path" in helptext and "NUL" in helptext


def test_summary_fails_on_missing_evidence(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    assert main(["summary"]) == 1
    err = capsys.readouterr().err
    for part in ("RED", "GREEN", "clean re-run", "RED replay", "tamper scan"):
        assert part in err


def test_summary_fails_on_a_lost_marker_unless_accepted_attended(git_repo, capsys):
    finished_ticket(git_repo, capsys, mode="attended")
    for cmd in (["rerun"], ["red-replay"], ["tamper-scan"]):
        main([*cmd])
    marker.path(git_repo.root).unlink()
    capsys.readouterr()
    assert main(["summary", "--ticket", "T1"]) == 1
    assert "marker lost" in capsys.readouterr().err
    assert main(["summary", "--ticket", "T1", "--accept-lost-marker"]) == 0


def test_lost_marker_cannot_be_accepted_in_goal_mode(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    for cmd in (["rerun"], ["red-replay"], ["tamper-scan"]):
        main([*cmd])
    marker.path(git_repo.root).unlink()
    assert main(["summary", "--ticket", "T1", "--accept-lost-marker"]) == 1
    assert "guard block" in capsys.readouterr().err


def test_boundary_ticket_and_start_come_from_evidence_without_marker(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    start = marker.read(git_repo.root)["start_sha"]
    marker.path(git_repo.root).unlink()
    assert boundary.context(git_repo.root, "T1")["start_sha"] == start


def test_tamper_scan_refuses_reasons_in_goal_mode(git_repo, capsys):
    finished_ticket(git_repo, capsys)
    git_repo.write("tests/test_none.py", "def test_none():\n    x = 1\n")
    assert main(["tamper-scan", "--reason", "TS1=fine"]) == 1
    assert "guard block" in capsys.readouterr().err
    assert last(git_repo, "tamper_scan")["flags"][0]["reason"] is None
