# Rollup and Gate

The row format `spec:review` and `spec:complete` use, the verdicts file `guard rollup` reads, how verifier cost is counted, and what `guard gate` requires before a spec can leave review.

## When to use this reference

- Building `review/rollup.md` from verifier verdicts.
- Writing `review/pr-feedback-<round>.md` in `spec:complete`.
- Explaining a gate refusal to the owner.

## When not to use it

- Editing statuses by hand. The rollup is generated, and owner statuses live in the decision log; markdown edits are never read by the gate.

## Row format

Every row in `review/rollup.md` and `review/pr-feedback-<round>.md` uses these thirteen columns:

| Column | Holds |
|--------|-------|
| ID | `F<n>` for review findings, `P<n>` for PR feedback |
| Tier | The reviewer's tier: blocking, warning or advisory |
| Suggested | The verifier's suggested tier; the gate uses the higher of Tier and Suggested |
| Sources | Every reviewer that raised it (merged duplicates keep all) |
| Location | `file:line` |
| Claim | One falsifiable defect; for PR feedback, linked to the thread |
| Verdict | `confirmed`, `rejected`, `unresolved` or `invalid` |
| Proof | `ran`, `read` or `none` |
| Evidence | Command and exit code, `review/repro/<ID>` with its sha256, or citations |
| Reason | One line |
| Tokens | The verifier's tokens: input, output, cache read and cache creation, counted once per message id |
| Minutes | First to last entry of the verifier's transcript |
| Status | See below |

## Status values

| Status | Set by | Meaning |
|--------|--------|---------|
| `open` | `guard rollup` | Not yet fixed or decided |
| `fixed-verified` | Recheck, in the verdicts file | The frozen reproduction fails at the fix's parent and passes at the fix |
| `reopened` | Recheck | The fix didn't hold |
| `wontfix` | `guard decide <ID> wontfix --spec <spec-name>` | Owner chose not to fix |
| `rejection-accepted` | `guard decide <ID> rejection-accepted --spec <spec-name>` | Owner agreed the finding is not a defect |
| `answered` | `guard decide <P-id> answered --spec <spec-name>` | PR feedback only: a question replied to with no code change |

Owner statuses come only from the decision log, `$(git rev-parse --git-dir)/ticket-guard/decisions.jsonl`, written by `guard decide` in an attended session after the owner's answer. Goal runs deny the command. The log is local to the clone.

## Verdicts file

The main session writes one JSON object per finding, one per line, to `review/verdicts.jsonl`:

| Key | Value |
|-----|-------|
| `id`, `tier`, `suggested`, `sources`, `location`, `claim` | From the merged finding and the verdict |
| `verdict`, `proof`, `evidence`, `reason` | From the verifier's report |
| `status` | `open`, or `fixed-verified` / `reopened` after a recheck |
| `agent_id` | The verifier subagent's ID, to find its transcript |
| `transcript` | Optional: a transcript path, used instead of `agent_id` |

<!-- example-verdicts:start -->
```jsonl
{"id": "F1", "tier": "blocking", "suggested": "blocking", "sources": ["code-reviewer", "test-master"], "location": "src/auth/session.ts:142", "claim": "Refresh races logout, leaving the session active", "verdict": "confirmed", "proof": "ran", "evidence": "review/repro/F1.test.ts sha256 3f2a..., exit 1 as predicted", "reason": "Stale token accepted after logout", "status": "open", "agent_id": "a1"}
{"id": "F2", "tier": "warning", "suggested": "advisory", "sources": ["security-reviewer"], "location": "api/users.py:88", "claim": "Unvalidated id reaches the query", "verdict": "rejected", "proof": "read", "evidence": "api/users.py:80 casts to int", "reason": "Scenario unreachable", "status": "open", "agent_id": "a2"}
{"id": "F3", "tier": "advisory", "suggested": "advisory", "sources": ["test-master"], "location": "tests/cart.test.ts:20", "claim": "Discount boundary untested at 100", "verdict": "unresolved", "proof": "none", "evidence": "fixture needs a missing secret", "reason": "Could not run", "status": "open", "agent_id": "a3"}
```
<!-- example-verdicts:end -->

`scripts/test-review-wiring.sh` runs this example through the runtime, so a format change breaks the test.

## Building the rollup

```bash
guard rollup <spec-name> \
  --verdicts <specsRoot>/todo/<spec-name>/review/verdicts.jsonl \
  --transcripts ~/.claude/projects/<project>/<session-id>/subagents/
```

`--transcripts` points at the folder holding each verifier's `agent-<agent_id>.jsonl`; Claude Code keeps subagent transcripts there. Tokens and Minutes stay empty for a verdict with no transcript. Every finding appears, including `invalid` and `rejected` ones, so the owner can overrule any of them. There is no budget cap; the cost columns are the record.

## The gate

```bash
guard gate <spec-name>
```

Exit 0 only when all of these hold:

- Every **blocking** rollup row (by the higher of Tier and Suggested) is `fixed-verified`, or logged `wontfix` or `rejection-accepted`. Warnings and advisories never block.
- Every row in every `review/pr-feedback-<round>.md` is `fixed-verified` or carries a logged `wontfix`, `rejection-accepted` or `answered`, whatever its tier.
- Every ticket in the Completion Status table is Done, Already done, or Blocked and accepted with `guard decide <ticket> accepted --spec <spec-name>`. Pending tickets fail it.
- Every row of `review/docs-waivers.md` has a ruling in the `## Waivers` table of `review/code-documenter.md`: `holds`, or `wrong` naming its finding. When the plan's notes record a waiver and `review/docs-waivers.md` is missing, the gate refuses and names `guard docs-waivers`.

`answered` closes a PR-feedback row, never a review finding. The gate also lists the Readiness table's Blocked tickets, which never entered the run. Exit 1 lists every refusal; exit 2 means the rollup or the plan is missing, and the gate fails closed.
