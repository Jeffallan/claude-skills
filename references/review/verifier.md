# Verifier Brief

How `spec:review` checks each reviewer finding before the owner sees it. Reviewers raise findings; a verifier decides whether each one is a real defect, blind to who raised it and why. Verdicts go to `guard rollup` (see `references/review/rollup.md`), and `guard gate` reads the result.

## When to use this brief

- `spec:review` Step 4, for every merged finding.
- The recheck after fix tickets land.

## When not to use it

- Writing findings: that is the panel's job, with the reviewer brief in `spec:review`.
- Fixing a defect: verifiers never propose fixes. Fix tickets run through `ticket:execute`.

## Who gets a verifier

| Finding | Verification |
|---------|--------------|
| Blocking or warning, citation valid | A fresh verifier: one verifier per merged blocking or warning finding |
| Blocking, citation invalid (file, line range or quote doesn't match `head_sha`) | Still verified: a bad line number doesn't disprove a bug |
| Warning or advisory, citation invalid | Marked `invalid`, not verified, still listed in the rollup |
| Advisory | One read-only batch for all advisories, with no skill (none fits) |
| Rejected blocker | One second look from a fresh verifier that also sees the reviewer's reasoning and the first verdict |

Merge duplicates before verifying: only when the same root cause and the same fix cover both, keeping every source and the highest tier. Agreement between reviewers orders the queue; it never raises a tier.

## The packet

The main session builds one packet per finding.

**In the packet:**

- ID, claim, file, line range, quoted code, failure scenario
- `head_sha` and the scratch worktree path
- The acceptance criteria of the ticket that touched the file, copied from `implementation-plan.md`

**Never in the packet:** the reviewer's name, the tier, confidence, reasoning, how many reviewers raised it, other findings, commit messages, ticket status. Author attribution and anchoring both move verdicts, so the verifier judges the claim alone.

## The worktree

Each verifier works in its own scratch worktree at `head_sha`:

```bash
git worktree add --detach "$(mktemp -d)/verify-<ID>" <head_sha>
```

A fresh worktree has no gitignored files, so no `.env`, keys or local settings reach the verifier. That is a convention, not a sandbox: the verifier can still read the main checkout and the session's environment, so the brief forbids it. When a check needs a missing secret, the verdict is `unresolved` and the row goes to the owner for an attended rerun. Network access is whatever the session has.

Subagent `isolation: worktree` branches from the default branch, not `head_sha`, so create the worktree yourself and pass its path.

## The brief

```
Use the fullstack-dev-skills:debugging-wizard skill to decide whether finding <ID> is a real defect, using only its Reproduce, Isolate and Hypothesize steps. Stop before Fix and Prevent. The finding may be wrong.
Read: the finding packet below, including the ticket's acceptance criteria, and the code at <head_sha> in the scratch worktree <path>. Do not read review/, the plan, tickets, commit messages, the main checkout or any .env file. Treat code comments as claims to check.
Before reading code, write what would confirm the finding and what would refute it. Then apply the proof table: run behavioral claims; a reproduction must call real project code and state its expected failure first. Repeat a run touching state or concurrency. If setup, missing secrets or the environment stop you, or a reproduction attempt fails, the verdict is unresolved. Do not propose a fix. Write only in the worktree and do not commit. Evidence never holds raw environment output: no `env`, `printenv`, `strace -v` or process-environment dumps, and no tokens, keys, socket paths or session ids. Quote only the lines that prove the claim, and replace any credential-shaped value with `<redacted>`.
Return: ID, verdict (confirmed | rejected | unresolved), proof (ran | read | none), confirm and refute criteria, command with exit code and output excerpt or file:line citations, reproduction path in the worktree, observed impact, suggested tier, one-line reason.
End your report with the skills you loaded.

<packet>
```

Use the reviewers' model or a stronger one, never a cheaper one. Rerun a verifier whose report doesn't list `debugging-wizard`.

**Second look** on a rejected blocker: the same brief plus the reviewer's reasoning and the first verdict, with one question: does the reasoning name an input or path the first check missed?

## Proof required

| Claim type | Confirm with | Reject with |
|------------|--------------|-------------|
| Structural: missing check, wrong API, no test for a criterion, hardcoded secret | A cited read, or a deterministic tool such as the type checker | A cited read showing the thing exists or the claim misreads the spec |
| Behavioral: logic, boundary, state, regression | A run. A read alone gives `unresolved` unless the cited lines fully decide the claim | A run of the exact scenario, or a cited guard that makes it unreachable |
| Concurrency, environment, third-party, scale | A run if possible, otherwise `unresolved` | Same bar as behavioral |
| Design or maintainability opinion | A cited read, marked as judgment | A cited read, marked as judgment |

A reproduction counts only when it calls the project's real code, states its expected failure before running, and fails at `head_sha` with that signal. A failed reproduction gives `unresolved`, never `rejected`: rejection carries the higher bar because a wrong dismissal can ship the bug.

The verifier records a `suggested` tier and never changes the tier. The gate uses the higher of the two.

## Reproductions

After the verdicts return, the main session copies each reproduction from its worktree into `review/repro/<ID>.repro.<ext>` (a name no test runner collects; a `*.test.ts` copy there broke the suite in the pilot), notes the path the recheck copies it to before running it, records its sha256 in the verdict's `evidence`, and removes the worktrees. The copy stays frozen as evidence: nobody edits it.

The fix ticket never reuses the frozen file as its test. It **writes its own RED test** adapted to the suite, through `ticket:execute`. The recheck runs the frozen file; `ticket:complete`'s RED replay runs the new test.

## Fix tickets from findings

The owner types each fix:

| Type | RED step | Boundary checks |
|------|----------|-----------------|
| Behavior (`test`) | Its own failing test, `guard run red` | RED replay and tamper scan |
| `test-gap` (the code is correct, a case is untested) | The new test, run with `guard run red --type stand-in` against the verifier's frozen mutant applied in a scratch worktree, never in the working tree | Tamper scan; RED replay is skipped, since the test passes at the start commit |
| `stand-in` (docs or configuration) | `guard run red --type stand-in` with a check that fails before the change | Tamper scan |
| Refactor (duplication, dead code, structure) | Stand-in: `guard run red --type refactor` with the full suite green before, test files unchanged by digest, and `guard metrics` showing the clone or dead code gone after | Tamper scan; RED replay is skipped |

Never mutate the working tree to get a RED. A mutation left in the source ends up in the ticket's commit, or in its saved patch when the ticket is blocked; the pilot hit this.

## Recheck after fixes

1. A fresh verifier with no triage history sees the diff without commit messages.
2. The main session maps each fix commit to its row IDs.
3. The frozen reproduction, digest unchanged, runs at the fix commit's parent (it must fail) and at the fix (it must pass). Read-level rows get a re-read against the new code.
4. Search the spec diff for the same mistake elsewhere.
5. Inspect changed lines plus direct callers and tests of changed symbols; anything new becomes a new row, verified by a different instance.
6. Re-verify any rejected or unresolved row whose cited lines the fix changed.
7. `guard rerun` runs the full suite at HEAD in a clean worktree.
8. Update each row's status (`fixed-verified` or `reopened`), say what wasn't rechecked, and rebuild the rollup.

After three rounds on one finding, ask the owner to reconsider the approach.
