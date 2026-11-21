"""Keep docs current: `related:` frontmatter, `path::symbol` citations, and which docs a diff affects."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path
import re
import subprocess
from typing import Any

from ticket_guard import evidence, files, plan, settings
from ticket_guard.errors import GuardError
from ticket_guard.gitutil import git, top

CITE = re.compile(r"`([\w./-]+)::([A-Za-z_][\w.]*)(?:\(\))?`")
HUNK = re.compile(r"^@@[^@]*@@(.*)$")


def frontmatter(text: str) -> dict[str, Any]:
    """The leading `---` block: `key: value` scalars, inline `[a, b]` lists and block `- item` lists."""
    lines = text.splitlines()
    if lines[:1] != ["---"] or "---" not in lines[1:]:
        return {}
    block = lines[1 : lines.index("---", 1)]
    out: dict[str, Any] = {}
    key = None
    for line in block:
        item = line.lstrip()
        if key and item.startswith("- "):
            out[key].append(item[2:].strip().strip("'\""))
            continue
        name, sep, rest = line.partition(":")
        if not sep or line[:1].isspace():
            continue
        key, rest = name.strip(), rest.split(" #")[0].strip()
        if rest.startswith("["):
            out[key] = [p.strip().strip("'\"") for p in rest.strip("[]").split(",") if p.strip()]
        elif rest:
            out[key] = rest.strip("'\"")
        else:
            out[key] = []
    return out


def related(text: str) -> list[str]:
    value = frontmatter(text).get("related", [])
    return value if isinstance(value, list) else [value]


def sources(text: str) -> list[str]:
    value = frontmatter(text).get("sources", [])
    return value if isinstance(value, list) else [value]


def citations(text: str) -> list[tuple[str, str]]:
    return [(m[1], m[2]) for m in CITE.finditer(text)]


def root(cwd: Path) -> str:
    return settings.get(cwd, "docsRoot") or "docs"


def all_docs(cwd: Path) -> dict[str, str]:
    """{path relative to the docs root: text} for every Markdown doc there, the specs root excluded."""
    base, specs = root(cwd).rstrip("/") + "/", settings.get(cwd, "specsRoot").rstrip("/") + "/"
    listed = git(cwd, "ls-files", "--cached", "--others", "--exclude-standard", "--", base).splitlines()
    repo = top(cwd)
    return {
        p[len(base) :]: (repo / p).read_text(encoding="utf-8")
        for p in sorted(listed)
        if p.endswith(".md") and not p.startswith(specs) and (repo / p).is_file()
    }


def _word(symbol: str) -> re.Pattern[str]:
    return re.compile(rf"\b{re.escape(symbol.split('.')[-1])}\b")


def check(cwd: Path) -> list[str]:
    """Missing or one-sided `related:` links and citations that no longer resolve."""
    repo, found = top(cwd), all_docs(cwd)
    problems = []
    for doc, text in found.items():
        for other in related(text):
            if other not in found:
                problems.append(f"{doc}: related doc {other} does not exist")
            elif doc not in related(found[other]):
                problems.append(f"{doc} lists {other} as related, but {other} does not list it back")
        verified = frontmatter(text).get("verified")
        if verified and not _is_commit(cwd, str(verified)):
            problems.append(f"{doc}: verified {verified} is not a commit")
        cited = citations(text)
        ignored = _ignored(cwd, sorted({path for path, _ in cited if (repo / path).is_file()}))
        for path, symbol in cited:
            target = repo / path
            if path in ignored:
                problems.append(
                    f"{doc}: cites {path}::{symbol}, but {path} is vendored or git-ignored; cite the project's own code"
                )
            elif not target.is_file():
                problems.append(f"{doc}: cites {path}::{symbol}, but {path} does not exist")
            elif not _word(symbol).search(target.read_text(encoding="utf-8", errors="replace")):
                problems.append(f"{doc}: cites {path}::{symbol}, but {symbol.split('.')[-1]} is not in {path}")
    return problems


def _ignored(cwd: Path, paths: list[str]) -> set[str]:
    """The paths git ignores: installed dependencies and other vendored code the project doesn't own."""
    if not paths:
        return set()
    out = subprocess.run(
        ["git", "check-ignore", "--no-index", "--stdin"],
        cwd=top(cwd),
        input="\n".join(paths),
        capture_output=True,
        text=True,
    ).stdout
    return set(out.split())


def _is_commit(cwd: Path, rev: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "-q", f"{rev}^{{commit}}"], cwd=cwd, capture_output=True
        ).returncode
        == 0
    )


def _diff_text(diff: str) -> str:
    """The added, removed and hunk-header text of a `-U0` diff."""
    out = []
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        hunk = HUNK.match(line)
        if hunk:
            out.append(hunk[1])
        elif line[:1] in "+-":
            out.append(line[1:])
    return "\n".join(out)


def _changed_lines(cwd: Path, base: str, path: str) -> str:
    """The added, removed and hunk-header text of `path`'s diff against `base` (all of it when untracked)."""
    tracked = git(cwd, "ls-files", "--", path).strip()
    if not tracked and not git(cwd, "ls-tree", "--name-only", base, "--", path).strip():
        target = top(cwd) / path
        return target.read_text(encoding="utf-8", errors="replace") if target.is_file() else ""
    return _diff_text(git(cwd, "diff", "-U0", "--no-renames", base, "--", path))


def _code_reasons(text: str, changed: set[str], lines_of, exists, new: set[str] | None = None) -> list[str]:
    """Why a doc is affected: a cited symbol the changed files touch, or a `sources:` glob a file matches.

    `new` limits the glob match to added files (the per-ticket check: an edit to an existing file is covered
    by the citations, so broad globs don't flag a doc on every ticket); None matches every changed file (drift).
    """
    out = []
    for path, symbol in citations(text):
        if path in changed and (not exists(path) or _word(symbol).search(lines_of(path))):
            out.append(f"cites {path}::{symbol}")
    for glob in sources(text):
        out.extend(f"matches sources {glob}: {f}" for f in sorted(changed if new is None else new) if fnmatch(f, glob))
    return out


def affected(cwd: Path, base: str) -> dict[str, list[str]]:
    """{doc: reasons}: docs citing a symbol the diff touches, and the `related:` docs of each changed doc."""
    found, changed = all_docs(cwd), set(files.changed_since(cwd, base))
    prefix = root(cwd).rstrip("/") + "/"
    diffs: dict[str, str] = {}
    out: dict[str, list[str]] = {}
    code = {f for f in changed if not f.startswith(prefix)}
    added = set(git(cwd, "diff", "--name-only", "--no-renames", "--diff-filter=A", base).split())
    added |= set(git(cwd, "ls-files", "--others", "--exclude-standard").split())
    new = {f for f in code if f in added}

    def lines_of(path: str) -> str:
        return diffs.setdefault(path, _changed_lines(cwd, base, path))

    for doc, text in found.items():
        reasons = _code_reasons(text, code, lines_of, lambda path: (top(cwd) / path).is_file(), new)
        if reasons:
            out.setdefault(doc, []).extend(reasons)
    for doc in sorted(d for d in found if prefix + d in changed):
        for other in related(found[doc]):
            if other in found:
                out.setdefault(other, []).append(f"related to {doc}")
    return {doc: sorted(set(reasons)) for doc, reasons in sorted(out.items())}


def statuses(cwd: Path, base: str, recs: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Each affected doc as updated (changed in the diff), checked (a `docs_checked` record) or pending."""
    changed = set(files.changed_since(cwd, base))
    prefix = root(cwd).rstrip("/") + "/"
    checked = {r["doc"]: r["reason"] for r in recs or [] if r["event"] == "docs_checked"}
    rows = []
    for doc, reasons in affected(cwd, base).items():
        if prefix + doc in changed:
            status = "updated"
        elif doc in checked:
            status = "checked"
        else:
            status = "pending"
        row = {"doc": doc, "reasons": reasons, "status": status}
        if status == "checked":
            row["reason"] = checked[doc]
        rows.append(row)
    return rows


def mark_checked(cwd: Path, ticket: str, doc: str, reason: str, mode: str) -> dict[str, Any]:
    """Record a waiver. Allowed in goal mode: spec:review's docs reviewer must rule on each one (`waivers`)."""
    if doc not in all_docs(cwd):
        raise GuardError(f"{doc} is not a doc under {root(cwd)}/")
    if not reason.strip():
        raise GuardError("give the reason the doc needs no change")
    return evidence.append(cwd, ticket, "docs_checked", doc=doc, reason=reason.strip().replace(")", "]"), mode=mode)


def summary_part(rows: list[dict[str, Any]]) -> tuple[str | None, list[str]]:
    """(notes text, missing lines) for `guard summary`; (None, []) when no doc is affected."""
    if not rows:
        return None, []
    missing = [
        f"docs: {r['doc']} not updated or checked ({'; '.join(r['reasons'])})" for r in rows if r["status"] == "pending"
    ]
    done = [r["doc"] for r in rows if r["status"] == "updated"]
    checked = [f"{r['doc']} ({r['reason']})" for r in rows if r["status"] == "checked"]
    text = "docs: " + "; ".join(
        p
        for p in (f"updated {', '.join(done)}" if done else "", f"checked {', '.join(checked)}" if checked else "")
        if p
    )
    return (text if done or checked else None), missing


SMALL_WORDS = 3  # a doc update this small may be cosmetic: the docs reviewer rules on it like a waiver
WAIVER = re.compile(r"([\w./-]+\.md) \(([^)]*)\)")


def plan_waivers(plan_text: str) -> list[tuple[str, str, str]]:
    """(ticket, doc, reason) for each `checked` doc in the Completion Status notes `guard summary` wrote."""
    out = []
    for ticket, cells in plan.status_rows_text(plan_text).items():
        notes = cells[3] if len(cells) > 3 else ""
        for part in notes.split(";"):
            part = part.strip().removeprefix("docs:").strip()
            if part.startswith("checked "):
                out.extend((ticket, doc, reason) for doc, reason in WAIVER.findall(part))
    return out


def small_updates(cwd: Path, base: str) -> list[tuple[str, int]]:
    """(doc, words changed) for each doc the diff changes by SMALL_WORDS words or fewer."""
    prefix = root(cwd).rstrip("/") + "/"
    changed = set(files.changed_since(cwd, base))
    out = []
    for doc in all_docs(cwd):
        if prefix + doc not in changed or not git(cwd, "ls-tree", "--name-only", base, "--", prefix + doc).strip():
            continue
        diff = git(cwd, "diff", "--word-diff=porcelain", base, "--", prefix + doc).splitlines()
        words = sum(len(line[1:].split()) for line in diff if line[:1] in "+-" and not line.startswith(("+++", "---")))
        if words <= SMALL_WORDS:
            out.append((doc, words))
    return out


def write_waivers(cwd: Path, spec: str, base: str) -> Path:
    """review/docs-waivers.md: every waiver and small doc update, each needing a ruling from the docs reviewer."""
    folder = settings.spec_dir(cwd, spec)
    rows = [
        (t, d, "checked, no change", r)
        for t, d, r in plan_waivers((folder / "implementation-plan.md").read_text(encoding="utf-8"))
    ]
    rows += [("-", d, f"small update ({n} words)", "-") for d, n in small_updates(cwd, base)]
    lines = [
        "# Docs waivers",
        "",
        "The docs reviewer rules on each row in its own file, in a `## Waivers` table: `| W<n> | holds | - |`, or",
        "`| W<n> | wrong | <finding id> |` with that finding raised as blocking. `guard gate` refuses until every row has a ruling.",
        "",
        "| ID | Ticket | Doc | Kind | Reason |",
        "|----|--------|-----|------|--------|",
        *(f"| W{i} | {t} | {d} | {k} | {r} |" for i, (t, d, k, r) in enumerate(rows, 1)),
    ]
    path = folder / "review" / "docs-waivers.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _table_rows(text: str) -> list[list[str]]:
    return [plan.cells(line) for line in text.splitlines() if re.match(r"\|\s*W\d+\s*\|", line)]


def gate_refusals(spec_dir: Path, plan_text: str) -> list[str]:
    """Refusals for waivers the docs reviewer hasn't ruled on (option b: the run may waive, the reviewer decides)."""
    listing = spec_dir / "review" / "docs-waivers.md"
    if not listing.is_file():
        return (
            [f"docs waivers in the plan were never reviewed: run `guard docs-waivers {spec_dir.name}` in spec:review"]
            if plan_waivers(plan_text)
            else []
        )
    reviewer = spec_dir / "review" / "code-documenter.md"
    section = reviewer.read_text(encoding="utf-8").split("## Waivers", 1) if reviewer.is_file() else []
    rulings = {r[0]: r for r in _table_rows(section[1])} if len(section) > 1 else {}
    out = []
    for row in _table_rows(listing.read_text(encoding="utf-8")):
        wid, doc = row[0], row[2] if len(row) > 2 else ""
        ruled = rulings.get(wid)
        verdict = ruled[1].lower() if ruled and len(ruled) > 1 else ""
        if verdict == "holds":
            continue
        if verdict == "wrong":
            if not re.fullmatch(r"[A-Z]+-?\d+", ruled[2] if len(ruled) > 2 else ""):
                out.append(f"{wid}: ruled wrong but names no finding ({doc})")
            continue
        out.append(f"{wid}: docs waiver ({doc}) has no ruling in review/code-documenter.md")
    return out


def drift(cwd: Path) -> list[dict[str, Any]]:
    """Docs with a `verified:` commit that code changed since, outside the commits that also updated the doc.

    A commit that changes the doc counts as its update (the ticket workflow edits code and docs together); one
    without an `Intake:` or `Ticket:` trailer is a hand edit, reported so a rerun keeps it.
    """
    prefix = root(cwd).rstrip("/") + "/"
    rows = []
    for doc, text in all_docs(cwd).items():
        fm = frontmatter(text)
        verified = fm.get("verified")
        if not verified:
            continue
        if not _is_commit(cwd, str(verified)):
            rows.append(
                {
                    "doc": doc,
                    "command": fm.get("command"),
                    "verified": verified,
                    "reasons": [f"verified {verified} is not a commit"],
                }
            )
            continue
        reasons: list[str] = []
        for sha in git(cwd, "rev-list", "--reverse", "--no-merges", f"{verified}..HEAD").split():
            files = set(git(cwd, "show", "--name-only", "--format=", "--no-renames", sha).split())
            if prefix + doc in files:
                # A line match, not git's trailer parser: Claude Code's Co-Authored-By paragraph, added after
                # a blank line, makes git stop reading an earlier Ticket: line as a trailer.
                body = git(cwd, "log", "-1", "--format=%B", sha)
                marked = re.search(r"^(Intake|Ticket): \S", body, re.M)
                if not marked and "edited outside the workflow since its audit" not in reasons:
                    reasons.append("edited outside the workflow since its audit")
                continue
            code = {f for f in files if not f.startswith(prefix)}

            def lines_of(path: str, sha: str = sha) -> str:
                return _diff_text(git(cwd, "show", "-U0", "--format=", "--no-renames", sha, "--", path))

            def exists(path: str, sha: str = sha) -> bool:
                return bool(git(cwd, "ls-tree", "--name-only", sha, "--", path).strip())

            reasons += [r for r in _code_reasons(text, code, lines_of, exists) if r not in reasons]
        if reasons:
            rows.append({"doc": doc, "command": fm.get("command"), "verified": verified, "reasons": reasons})
    return rows
