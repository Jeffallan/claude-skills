# Unattended Rules

How the workflow commands behave when nobody is there to answer: inside a `/goal` run, in a headless `claude -p` session, or in any session where `AskUserQuestion` is unavailable. Goal runs launch with `AskUserQuestion` and every write denied for that session (`references/specs/launch.md`), so these rules and the deny set back each other up.

## Two kinds of command

| Kind | Commands | Under a goal |
|------|----------|--------------|
| Ticket commands | `ticket:execute`, `ticket:complete` | Run under the unattended rules below |
| Attended-only commands | `discovery:approve`, `spec:triage`, `spec:create`, the owner triage in `spec:review`, `spec:complete`, the config wizard | Write nothing and end with `BLOCKED:` |

`discovery:create` and `discovery:synthesize` write only local files; without `AskUserQuestion` they skip interviews and record open questions instead.

## The attended-only guard

Each attended-only command checks this before its first write:

> When a goal is active or `AskUserQuestion` is unavailable, write nothing. Print what the command would have done as a read-only proposal, then end the turn with `BLOCKED: <command> needs the owner`, followed by `git status --short`.

"Write" covers files, commits, branches, tracker calls and PR calls. A goal is active when the session was started with `/goal`, or the goal prompt is running the command. Nothing about this guard is checked by a hook; the launch-scoped denies stop the writes even when the guard is missed.

## Ticket commands under unattended rules

The ticket commands take their mode from the caller: the goal prompt's per-ticket loop says "under its unattended rules", and the marker records `--mode goal`. Under these rules:

- **Never call `AskUserQuestion`,** and never wait for an answer. Skip every attended checkpoint (approach confirmation, commit message review).
- **No tracker writes,** attended or not. Neither ticket command calls any adapter write operation, and neither moves a ticket's status. Commits reference the ticket with a neutral `Ticket: <id>` trailer, never a Linear issue ID or a Jira `#transition` token.
- **RED first.** The failing test and its RED record come before any implementation edit.
- **Never rewrite history.** No `git rebase`, `git reset`, `git commit --amend` or squash, even to tidy the commit count. A ticket found wrong after its commit stays committed: report it as a deviation, add it to Open questions, and let `spec:review` handle it. Goal launches deny these commands.
- **Subagents only read** and return text. Every edit happens in the main session, where the companion skill's hooks apply.
- **Frozen scope.** Never work a new issue found during the ticket. Append it to the plan's Proposed tracker changes (title, plain-language example, file references, duplicate check against open tickets) and carry on with the ticket.
- **Questions are collected, never defaulted.** When the ticket or a skill needs an answer the run can't get, block the ticket with `guard block <ticket> "question: <question>" --question "<question>"`, which writes the Blocked row and the plan's Open questions row in one commit.

## Blocking a ticket

A ticket that can't be finished is blocked through the runtime, never by hand:

```bash
guard block <ticket> "<reason>"
```

On the marker's ticket it saves the diff against the start SHA to `$(git rev-parse --git-dir)/ticket-guard/blocked/<ticket>.patch`, new untracked files to a tarball beside it, restores the tree to the start SHA, writes the Blocked row with the reason and clears the marker. Nothing that predates the ticket is touched, and the work can be re-applied later. It works without a marker too: it takes the start SHA from the ticket's evidence record, or from `--start <sha>`, so a ticket whose marker was lost is saved and restored the same way. It refuses when HEAD has moved past the start SHA; a ticket commits only in `ticket:complete`, so that means something else committed, which is a spec-wide stop.

Block a ticket when:

- Its steps would have to change, or an acceptance criterion contradicts the spec.
- Access or a prerequisite is missing, or a needed action is denied.
- Three attempts at the same problem have failed.
- A skill or the ticket needs an answer nobody can give (`Blocked: question`).
- `ticket:complete`'s tamper scan flags something, the evidence summary is incomplete, or the marker disappeared without a logged clear.

Then mark every ticket that depends on it:

```bash
guard block <dependent> "depends on <blocked ticket>"
```

and continue with the next ticket that doesn't depend on a blocked one. A run where only blocked tickets remain finishes normally: its final report lists the blocked tickets and the open questions first.

## `BLOCKED:` is for spec-wide stops

End the turn with `BLOCKED: <stop>`, what is needed, and `git status --short` only for a stop the goal prompt lists in `<stops>`, or one that makes every remaining ticket pointless: the environment won't build or run tests, the sources contradict each other on something every ticket depends on, `guard block` refuses. A single stuck ticket is never a `BLOCKED:` stop.

## Owner-only actions

Some flags and commands record owner decisions. A run under unattended rules never uses them:

- `guard decide` (denied in goal launches).
- `guard tamper-scan --reason ID=TEXT`: in goal mode the runtime ignores `--reason`, so a flagged ticket goes through `guard block`.
- `guard summary --accept-lost-marker`: attended only, after the owner accepts.

## Attended runs

Attended, the ticket commands keep their checkpoints: confirm the approach before writing tests, ask before any deviation, show the commit message before committing, and let the owner decide on tamper flags and lost markers. The rules on tracker writes, RED first, frozen scope and read-only subagents are the same in both modes.
