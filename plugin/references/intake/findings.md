# Intake Findings Tracker

Every intake procedure records the bugs, drift and dead code it finds in one file, `docs/intake-findings.md`, instead of fixing them. This file defines that tracker, its finding ids and the rule that governs the tests built on it. The eval in `evals/intake/` reads the tracker and the tests with these rules.

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
| F-001 | <one line> | Critical / High / Medium / Low | <area> | open | <command> |

## Open questions

| # | Command | Question | Draft decision |
|---|---------|----------|----------------|

## Findings

### F-001 <title>
- **Severity:** <Critical / High / Medium / Low> (<area>). Row: <row>; <adjustment, or no adjustment>
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

## Security detail stays out of git

The tracker and the tests are committed, and a pushed repo can be cloned, forked, mirrored or leaked well beyond the people who would fix it. Until the fix ships, a security finding's reproduction detail is a working recipe against the deployed system. It never goes in a committed file, at any severity, in any repo, private ones included.

A **security finding** is one someone could use against the app or its users: every finding from the access matrix, `intake:testing-authorization` or `intake:testing-owasp`, and any other finding about authentication, authorization, sessions or tokens, input handling (injection, unsafe deserialization, file paths, redirects), secrets, or one account reaching another account's data.

**Reproduction detail** is anything that lets a reader carry out the attack without working it out from the code:

- the exact requests: method, route with real ids, headers, cookies, query strings and bodies
- payloads and inputs crafted to trigger it
- credentials, tokens, session ids or keys used or obtained, test ones included
- step-by-step exploitation: the account set-up, the order of calls, the timing
- commands or scripts that run the attack (a `curl` line, a scanner invocation)

For a security finding:

- **The committed tracker entry** keeps the Summary row and a Findings entry with the id, `Severity:` (area), `Status:`, `Location:` (`path::symbol`), `What:` and `Impact:` in plain terms, `Recommendation:`, `Surfaced in:` and `Tests:`. `What:` says what is missing or wrong and who can reach what ("the invoice export checks the session but not the invoice's account"), never how to send it. It ends with `Reproduction: restricted file.`
- **`docs/intake-findings-restricted.md`** holds the reproduction detail, one `### F-0xx <title>` section per finding. Whoever appends the finding to the tracker writes its section here, in the same step; in the parallel testing batch the agents report it under `Tracker edits:` and the `intake` command writes it. Before the file is first written, add `docs/intake-findings-restricted.md` to `.git/info/exclude`; the `intake` command confirms `git check-ignore -q docs/intake-findings-restricted.md` succeeds before every commit that follows.
- **Docs** that cite the finding (`docs/security/*.md`, the access matrix) give the id and the plain-terms `What:`, never the detail.
- **Tests** stay committed: they pin the behavior and the fix needs them. Their names and comments say what they check (`test_F012_member_cannot_read_other_accounts_invoices_intended`), never how to exploit it, and they read their inputs from fixtures rather than spelling out a payload in a comment. They are the exposure that remains: a reader who studies the tests can still work out the attack, so the restricted file narrows the exposure and does not remove it.
- **The item's checklist note** says the restricted file exists and which ids it holds, so the owner knows to keep it. Git does not carry it: a fresh clone, another machine or a deleted working tree loses it, so keep a copy somewhere safe until the findings are fixed.

The rule has no exception for the owner to reverse, so it needs no Open question. Findings that are not security findings keep their detail in the tracker, as usual.

## Who writes what

| Section | Written by |
|---------|-----------|
| Summary and Findings | Every intake procedure, appending |
| Open questions | A command in a goal run that makes a choice the owner could reasonably reverse (see `references/intake/rules.md`); routine scope confirmations stay in the checklist note |
| Test coverage, and each finding's `Tests:` line | The `intake:testing-*` commands, both in the same commit as the test |
| A finding's text after a test confirms or disproves it (drop "suspected", correct the claim, set `invalid`) | The testing command whose test settled it |
| A finding's `Severity:` line after later evidence changes its reach | The procedure that holds the evidence, in the same commit (`references/intake/severity.md`, "Re-rating"), with a `Re-rated:` entry in its checklist note; the parallel testing commands report it as a tracker edit |
| `fixed` on a finding about the test code itself, repaired under "A red baseline" | `intake:testing-setup`, naming the repair commit |
| Status changes to `ticketed`, `accepted-risk`, `fixed` | The owner, at close-out |

`intake:testing-features`, `intake:testing-authorization` and `intake:testing-owasp` write at the same time, so their agents never edit the tracker. Each reports its new findings under provisional ids and its other tracker changes, and the `intake` command writes their tracker edits: it assigns the real ids in checklist order and appends each item's entries in that item's commit.

## Every finding has evidence

A finding without evidence is not a finding. By the end of Phase 3, every finding that isn't `invalid` names its characterization test on its `Tests:` line (and its intended-behavior twin when it is a bug), in the same `path::name` form the Test coverage table uses. Each testing command takes the open findings in its area; `intake:testing-user-flows`, the last testing item, takes every finding still without a test, whatever its area.

Only a finding no test can express (dead code, a build or deploy setting, an end-of-life dependency version) goes without one. Its `Tests:` line then says why and names the command whose output proves the finding, for example: none: end-of-life version, nothing to run; evidence: `pip show django`. A finding that can't be proven either way is `invalid` or an Open question, never left open.

A `fixed` finding keeps its evidence too: the `Tests:` line names the intended-behavior test that now passes, or, when no test can express the fix (a repaired test factory, a build setting), says so and names the fixing commit as its evidence command: none: test code only; evidence: `git show <sha>`.

## Severity

Every finding has a severity: Critical, High, Medium or Low. Read `references/intake/severity.md` before you write or change a `Severity:` line. It holds the levels, the data classes, the closed list of adjustments, the floors, the over-rating guards, the re-rate rule and the anchors. The `Severity:` line names the table row the rating comes from and any adjustment. A later procedure whose evidence changes a finding's reach re-rates it in the same commit; the owner can still adjust any rating at close-out.

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
