import json
import sys

from ticket_guard import docs, evidence, marker
from ticket_guard.__main__ import main

PYTEST = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]

API = "---\nrelated: [security/auth.md]\n---\n# API\n\n`add` lives in `src/app.py::add`.\n"
AUTH = "---\nrelated:\n  - architecture/api.md\n---\n# Auth\n\nNo code cited.\n"
OTHER = "# Other\n\nCites `src/app.py::mul`, which no ticket touches.\n"


def with_docs(git_repo):
    git_repo.write("src/app.py", "def add(a, b):\n    return a + b\n\n\ndef mul(a, b):\n    return a * b\n")
    git_repo.write("docs/architecture/api.md", API)
    git_repo.write("docs/security/auth.md", AUTH)
    git_repo.write("docs/other.md", OTHER)
    return git_repo.commit("docs")


# frontmatter and citations ----------------------------------------------------


def test_related_reads_inline_and_block_lists():
    assert docs.related(API) == ["security/auth.md"]
    assert docs.related(AUTH) == ["architecture/api.md"]
    assert docs.related("# no frontmatter\n") == []


def test_citations_name_path_and_symbol():
    assert docs.citations("see `a/b.py::Klass.meth()` and `c.ts::run`, not `x.py:12`") == [
        ("a/b.py", "Klass.meth"),
        ("c.ts", "run"),
    ]


# docs-check -------------------------------------------------------------------


def test_check_passes_consistent_docs(git_repo, capsys):
    with_docs(git_repo)
    assert main(["docs-check"]) == 0


def test_check_flags_one_sided_missing_related_and_broken_citations(git_repo, capsys):
    with_docs(git_repo)
    git_repo.write(
        "docs/security/auth.md", "---\nrelated: [gone.md]\n---\n# Auth\n\n`src/app.py::nope` `src/x.py::f`\n"
    )
    assert main(["docs-check"]) == 1
    err = capsys.readouterr().err
    assert "architecture/api.md lists security/auth.md as related, but security/auth.md does not list it back" in err
    assert "security/auth.md: related doc gone.md does not exist" in err
    assert "security/auth.md: cites src/app.py::nope, but nope is not in src/app.py" in err
    assert "security/auth.md: cites src/x.py::f, but src/x.py does not exist" in err


def test_check_skips_the_specs_root(git_repo, capsys):
    with_docs(git_repo)
    git_repo.write("docs/specs/todo/demo/overview.md", "`src/app.py::nope`\n")
    assert main(["docs-check"]) == 0


# docs-affected ----------------------------------------------------------------


def test_changed_symbol_flags_the_doc_citing_it_and_its_related_doc(git_repo, capsys):
    base = with_docs(git_repo)
    git_repo.write("src/app.py", "def add(a, b):\n    return b + a\n\n\ndef mul(a, b):\n    return a * b\n")
    got = docs.affected(git_repo.root, base)
    assert got == {"architecture/api.md": ["cites src/app.py::add"]}
    git_repo.write("docs/architecture/api.md", API + "\nUpdated.\n")
    got = docs.affected(git_repo.root, base)
    assert got["security/auth.md"] == ["related to architecture/api.md"]
    assert "other.md" not in got


def test_docs_affected_prints_status_per_doc(git_repo, capsys):
    base = with_docs(git_repo)
    git_repo.write("src/app.py", "def add(a, b):\n    return b + a\n\n\ndef mul(a, b):\n    return a * b\n")
    assert main(["docs-affected", "--base", base, "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows == [{"doc": "architecture/api.md", "reasons": ["cites src/app.py::add"], "status": "pending"}]


# ticket boundary --------------------------------------------------------------


def ticket_with_code_change(git_repo, capsys):
    with_docs(git_repo)
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("tests/test_add2.py", "from src.app import add\n\n\ndef test_add2():\n    assert add(2, 2) == 4\n")
    assert main(["run", "red", "--", *PYTEST, "tests/test_add2.py"]) in (0, 1)
    git_repo.write("src/app.py", "def add(a, b):\n    return b + a\n\n\ndef mul(a, b):\n    return a * b\n")
    capsys.readouterr()


def test_summary_lists_affected_docs_still_pending(git_repo, capsys):
    ticket_with_code_change(git_repo, capsys)
    main(["summary"])
    err = capsys.readouterr().err
    assert "docs: architecture/api.md not updated or checked (cites src/app.py::add)" in err


def test_docs_checked_clears_a_doc_with_its_reason(git_repo, capsys):
    ticket_with_code_change(git_repo, capsys)
    assert main(["docs-checked", "architecture/api.md", "--reason", "argument order is not documented"]) == 0
    main(["summary"])
    assert "architecture/api.md not updated" not in capsys.readouterr().err
    assert main(["docs-affected", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert rows[0]["status"] == "checked" and rows[0]["reason"] == "argument order is not documented"


def test_docs_checked_refuses_an_unknown_doc_or_empty_reason(git_repo, capsys):
    ticket_with_code_change(git_repo, capsys)
    assert main(["docs-checked", "nope.md", "--reason", "x"]) == 1
    assert main(["docs-checked", "architecture/api.md", "--reason", " "]) == 1


def test_updating_the_doc_then_requires_its_related_doc(git_repo, capsys):
    ticket_with_code_change(git_repo, capsys)
    git_repo.write("docs/architecture/api.md", API + "\nArguments swap.\n")
    main(["summary"])
    err = capsys.readouterr().err
    assert "architecture/api.md not updated" not in err
    assert "docs: security/auth.md not updated or checked (related to architecture/api.md)" in err


def test_summary_without_docs_root_reports_none_affected(git_repo, capsys):
    marker.start(git_repo.root, "demo", "T1", "goal")
    git_repo.write("src/app.py", "def add(a, b):\n    return b + a\n")
    main(["summary"])
    out, err = capsys.readouterr()
    assert "docs:" not in err


# option (b): every waiver and small doc update needs the docs reviewer's ruling ---------------

from test_guard_review import FINDINGS, done_plan, rollup  # noqa: E402

REVIEW = "docs/specs/todo/demo/review"
WAIVED = "docs: checked security/auth.md (no auth change), architecture/api.md (names unchanged)"


def reviewed_spec(git_repo, capsys, t2_note=WAIVED):
    base = with_docs(git_repo)
    done_plan(git_repo, t2_note=t2_note)
    rollup(git_repo, capsys, [dict(f, status="fixed-verified") for f in FINDINGS])
    return base


def ruling(git_repo, rows):
    git_repo.write(
        f"{REVIEW}/code-documenter.md",
        "# code-documenter\n\n## Waivers\n\n| ID | Ruling | Finding |\n|---|---|---|\n" + rows,
    )


def test_docs_checked_records_the_run_mode(git_repo, capsys):
    ticket_with_code_change(git_repo, capsys)
    main(["docs-checked", "architecture/api.md", "--reason", "x"])
    rec = [r for r in evidence.records(git_repo.root, "T1") if r["event"] == "docs_checked"][-1]
    assert rec["mode"] == "goal"


def test_docs_waivers_lists_plan_waivers_and_small_doc_updates(git_repo, capsys):
    base = reviewed_spec(git_repo, capsys)
    git_repo.write("docs/other.md", OTHER.replace("which no ticket", "which no single ticket"))
    assert main(["docs-waivers", "demo", "--base", base]) == 0
    text = (git_repo.root / REVIEW / "docs-waivers.md").read_text()
    assert "| W1 | T2 | security/auth.md | checked, no change | no auth change |" in text
    assert "| W2 | T2 | architecture/api.md | checked, no change | names unchanged |" in text
    assert "| W3 | - | other.md | small update (1 words) | - |" in text


def test_gate_refuses_waivers_without_a_ruling(git_repo, capsys):
    base = reviewed_spec(git_repo, capsys)
    assert main(["docs-waivers", "demo", "--base", base]) == 0
    ruling(git_repo, "| W1 | holds | - |\n")
    capsys.readouterr()
    assert main(["gate", "demo"]) == 1
    err = capsys.readouterr().err
    assert "W2: docs waiver (architecture/api.md) has no ruling" in err and "W1:" not in err


def test_gate_refuses_a_wrong_ruling_without_its_finding(git_repo, capsys):
    base = reviewed_spec(git_repo, capsys)
    main(["docs-waivers", "demo", "--base", base])
    ruling(git_repo, "| W1 | holds | - |\n| W2 | wrong | - |\n")
    capsys.readouterr()
    assert main(["gate", "demo"]) == 1
    assert "W2: ruled wrong but names no finding" in capsys.readouterr().err
    ruling(git_repo, "| W1 | holds | - |\n| W2 | wrong | F3 |\n")
    assert main(["gate", "demo"]) == 0


def test_gate_refuses_plan_waivers_when_docs_waivers_was_never_run(git_repo, capsys):
    reviewed_spec(git_repo, capsys)
    capsys.readouterr()
    assert main(["gate", "demo"]) == 1
    assert "guard docs-waivers demo" in capsys.readouterr().err


def test_gate_ignores_docs_when_no_ticket_waived(git_repo, capsys):
    reviewed_spec(git_repo, capsys, t2_note="ok")
    assert main(["gate", "demo"]) == 0
