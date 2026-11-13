# Intake Findings Tracker

Every intake command records the bugs, drift and dead code it finds in one file, `docs/intake-findings.md`, instead of fixing them. This file defines that tracker, its finding ids and the rule that governs the tests built on it. The eval in `evals/intake/` reads the tracker and the tests with these rules.

## Characterize, don't fix

Intake records what the code does today. It never changes behavior, never fixes a bug mid-run, and never asserts a bug as correct.

- **Docs** describe current behavior neutrally. A doc that finds code contradicting its own intent (a type, a comment, another doc, a rule) records both and adds a finding.
- **Tests** pin current behavior. A known bug gets two tests:
  1. a passing **characterization test** that asserts what the code does now, and
  2. a sibling **intended-behavior test**, skipped or marked expected-fail, that asserts what the code should do.

  Write the intended-behavior test so any correct fix passes it: assert the observable outcome, never the names of classes or functions the fix may remove; cover every case the recommendation names (both ends of a range, the overnight case, the other role); and check the full effect (the record exists, not only the redirect). Ask "would this pass for the right fix, and fail for a wrong one?" before committing it. The characterization test pins the buggy behavior, never a correct case beside it.

  Both tests carry the finding id in their name (the hyphen may drop where names can't hold one, `F012`) or in a comment on the line above, for example `test_F012_owner_can_read_other_profiles_current` and `test_F012_owner_cannot_read_other_profiles_intended`. When the fix lands later, the characterization test fails, which is the signal to delete it and un-skip the sibling.
- **Docstrings** (`intake:document-codebase`) describe the code as it behaves. A docstring that would have to say "this is wrong" says what happens instead and names the finding id.

Use the test framework's own skip or expected-fail marker: `pytest.mark.xfail(strict=True, reason="F-012")`, `it.skip` or `it.failing` in Jest and Vitest, `test.fixme` in Playwright, `@Disabled("F-012")` in JUnit, `t.Skip("F-012")` in Go. A strict expected-fail is better than a skip where the framework has one, because it reports when the bug is fixed.

## File shape

```markdown
# Intake Findings

Issues found while running intake on <YYYY-MM-DD>, at <branch> <base-sha>. Found by reading code to
document and test it, not by a dedicated audit, so the list is a starting backlog. Findings are suspected
until triaged.

**Status values:** `open` (default), `ticketed: <ref>`, `accepted-risk`, `fixed`, `invalid`.

## Summary

| ID | Finding | Severity | Area | Status | Surfaced by |
|----|---------|----------|------|--------|-------------|
| F-001 | <one line> | High / Medium / Low | <area> | open | <command> |

## Open questions

| # | Command | Question | Draft decision |
|---|---------|----------|----------------|

## Findings

### F-001 <title>
- **Severity:** <High / Medium / Low> (<area>)
- **Status:** open
- **Location:** `<path>::<symbol>`
- **What:** <what the code does, in plain terms>
- **Impact:** <who or what it affects>
- **Recommendation:** <the fix, not applied>
- **Surfaced in:** <relative links to the docs that mention it>
- **Tests:** `<test path>::<test id>` for each test that characterizes it (the pytest node id, such as `tests/test_x.py::TestX::test_y`, or for a JS test its title as written: `tests/x.spec.js::F-001 hides profiles (current)`), or none: <why no test can express it>; evidence: `<command>`

## Test coverage

| ID | Characterization test | Intended-behavior test |
|----|-----------------------|------------------------|
```

## Finding ids

- Ids are `F-` plus a three-digit number, assigned in order and never reused: `F-001`, `F-002`. A finding later shown to be wrong keeps its id and gets `invalid`.
- The command that finds an issue appends it with the next free id, before it writes the doc or test that mentions it. "Append" means at the end of each section: the Summary row goes at the end of the Summary table, the finding at the end of Findings. The file keeps its section order.
- Docs, docstrings and tests cite the id, never a paraphrase, so `grep -rn "F-012"` finds every place a finding touches.
- An access-control finding from the matrix names its operation ids, the principal column and the invariant it breaks, one finding per root cause (`references/intake/access-control.md`, "Findings from the matrix").
- Cite code by symbol, never by line: `` `app/billing/services.py::round_minutes` ``, `` `app/models.py::Profile.save` `` for a method, the setting or key name for configuration, the path alone for a file with no symbol. `intake:document-codebase` and every later docstring move lines, so a line number goes stale inside the run. `<base-sha>` in the header is the commit the intake branch started from, the same one the checklist header names.

## Security detail in a committed tracker

The tracker is committed, and a High security finding with its tests is a working recipe against the deployed system until it's fixed. Before writing the first High security finding, check where the repo is visible (`gh repo view --json visibility`, the remote's host, or the owner's note in the checklist):

- **Private to the owner's team:** write it in full, as usual.
- **Public, or shared wider than the people who would fix it, or unknown:** write the Summary row and a Findings entry with severity, area, status, location and `Tests:` line, and put the reproduction detail (the exact requests, payloads and the steps) in `docs/intake-findings-restricted.md`, which the command adds to `.git/info/exclude` so it never gets committed. Record the choice in the item's checklist note and as an Open question, so the owner can move the detail back.

The tests still pin the behavior either way; their names say what they check, not how to exploit it.

## Who writes what

| Section | Written by |
|---------|-----------|
| Summary and Findings | Every intake command, appending |
| Open questions | A command in a goal run that makes a choice the owner could reasonably reverse (see `references/intake/rules.md`); routine scope confirmations stay in the checklist note |
| Test coverage, and each finding's `Tests:` line | The `intake:testing-*` commands, both in the same commit as the test |
| A finding's text after a test confirms or disproves it (drop "suspected", correct the claim, set `invalid`) | The testing command whose test settled it |
| `fixed` on a finding about the test code itself, repaired under "A red baseline" | `intake:testing-setup`, naming the repair commit |
| Status changes to `ticketed`, `accepted-risk`, `fixed` | The owner, at close-out |

## Every finding has evidence

A finding without evidence is not a finding. By the end of Phase 3, every finding that isn't `invalid` names its characterization test on its `Tests:` line (and its intended-behavior twin when it is a bug), in the same `path::name` form the Test coverage table uses. Each testing command takes the open findings in its area; `intake:testing-user-flows`, the last testing item, takes every finding still without a test, whatever its area.

Only a finding no test can express (dead code, a build or deploy setting, an end-of-life dependency version) goes without one. Its `Tests:` line then says why and names the command whose output proves the finding, for example: none: end-of-life version, nothing to run; evidence: `pip show django`. A finding that can't be proven either way is `invalid` or an Open question, never left open.

A `fixed` finding keeps its evidence too: the `Tests:` line names the intended-behavior test that now passes, or, when no test can express the fix (a repaired test factory, a build setting), says so and names the fixing commit as its evidence command: none: test code only; evidence: `git show <sha>`.

## Severity

| Severity | Use it for |
|----------|-----------|
| High | Data exposure, broken access control, data loss, a security control that is missing or bypassable |
| Medium | Incorrect behavior a user can hit, a non-atomic operation that can leave bad state, a hardening gap |
| Low | Drift between two sources of truth, dead code, type drift, inconsistency |

Severity is the finder's first guess; the owner adjusts it at close-out.

## Close-out

Intake is done when the docs, the test suite and the tracker agree. Every finding then has a status other than `open`: a ticket reference, an accepted-risk note with its reason, `fixed` or `invalid`. Close-out is attended; a goal run leaves findings `open` and lists them in its final report.

## Fixing a finding

Fixes come after intake, attended, one finding at a time:

1. Un-skip the intended-behavior test and watch it fail. A finding whose `Tests:` line says `none:` gets a new failing test first. When no test can express it (dead code to delete, a build-time warning), say so in the finding and name the command whose result proves the fix (a clean build log, a test run with the runner the fix restores).
2. Fix the code. Keep the suite deterministic: a fix that adds shared state (a rate limit, a cache) keys it so tests don't leak into each other.
3. Delete the characterization test and the comment block that cites the id above it, the whole block when it spans lines.
4. Set the status in both the Summary row and the finding's section, and point the `Tests:` line at the evidence for the fix ("Every finding has evidence").
5. Update every doc that cites the id (`grep -rn "F-012" docs/`): describe the fixed behavior and drop or annotate the citation.

## When not to use it

- A bug found outside intake goes to the tracker through the normal workflow, not into this file.
- A finding that needs a decision before the run can continue (the tests can't be written either way) is an Open question, not a finding.
