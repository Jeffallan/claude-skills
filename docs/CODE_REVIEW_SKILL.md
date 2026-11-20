Code Reviewer is the code review skill in Claude Skills. Point it at a pull request, a branch diff or a set of files, and it reviews them the way a senior engineer would: bugs, security holes, slow queries, missing tests. You get back a report sorted by severity that ends in a verdict. It runs in Claude Code and in any agent that supports the [Agent Skills specification](https://agentskills.io/specification).

## What the code review skill checks

| Area | What it looks for |
|------|-------------------|
| Intent | Sums up what the change is for in one sentence before reviewing, and asks the author when it can't |
| Design | Whether the change follows existing patterns and whether each new abstraction is justified |
| Logic | Edge cases, null handling, race conditions, missing guard clauses |
| Security | SQL injection, XSS, insecure deserialization, hardcoded secrets, with the OWASP Top 10 as the baseline |
| Performance | N+1 queries, memory leaks, work that should be cached |
| Tests | Coverage of edge cases, and tests that check behavior instead of implementation details |
| Readability | Magic numbers and unclear names, while leaving style to your linter |
| Spec compliance | Whether the change does what was asked, with nothing missing and nothing extra |

The skill only reads and searches files. It reports problems and suggests fixes with code examples; it never edits your code.

## How to install the code review skill in Claude Code

Add the marketplace and install the plugin from inside Claude Code:

```bash
/plugin marketplace add jeffallan/claude-skills
/plugin install fullstack-dev-skills@fullstack-dev-skills
```

Restart Claude Code when prompted. The plugin carries every skill in the collection, and Claude loads Code Reviewer only when a request calls for a review.

To install the code review skill on its own, copy its folder into your personal skills directory:

```bash
git clone https://github.com/jeffallan/claude-skills.git
cp -r claude-skills/skills/code-reviewer ~/.claude/skills/
```

For Cursor, Codex CLI, Gemini CLI and other agents, see [Getting Started](https://jeffallan.github.io/claude-skills/getting-started/).

## How to start a review

Ask for a review in plain words. Any of these will load the skill:

- "Review this PR"
- "Review the changes on this branch for bugs and security issues"
- "Do a code quality audit of `src/billing/`"
- "Check this diff for N+1 queries"

## Example code review report

Each review follows the same layout, from a summary through to a verdict. A shortened report for a small API change looks like this:

```markdown
# Code Review: Add order export endpoint

## Summary
Adds a CSV export for a customer's orders. The endpoint works, but it has
an injection risk and a query per order. Request changes.

## Critical Issues (Must Fix)
### 1. orders/export.ts:42 Security: SQL injection
- Current: customer ID interpolated into the query string
- Suggested: parameterized query, `db.query('... WHERE customer_id = $1', [id])`
- Impact: any caller can read other customers' orders

## Major Issues (Should Fix)
### 1. orders/export.ts:58 Performance: N+1 query
- Current: line items fetched inside the order loop
- Suggested: load line items for all orders in one query
- Impact: one extra query per order on every export

## Minor Issues (Nice to Have)
### 1. orders/export.ts:12 Naming: `d` holds the export date
- Suggested: `exportDate`

## Positive Feedback
- Streaming the CSV keeps memory flat for large exports

## Questions for Author
- Should exports over 10,000 rows be paginated or queued?

**Verdict**: Request Changes
```

## Skills that go deeper than a general review

Code Reviewer covers correctness, performance, maintainability and tests in a single pass. For a narrower, deeper look, pair it with:

- [Security Reviewer](https://jeffallan.github.io/claude-skills/skills/security/security-reviewer/) for a full security audit, secrets scanning and compliance checks
- [Test Master](https://jeffallan.github.io/claude-skills/skills/quality/test-master/) to write the tests a review finds missing
- [Architecture Designer](https://jeffallan.github.io/claude-skills/skills/api-architecture/architecture-designer/) for design-level review and architecture decision records

The skill's full workflow, constraints and reference files follow below.
