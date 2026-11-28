---
name: playwright-recording-processor
description: "Transforms raw Playwright codegen recordings into production-ready E2E tests through trimming, classification, and assertion injection. Use when processing codegen session recordings, trimming recorded browser sessions to a marker URL, classifying recordings as happy-path or bug-repro flows, or injecting diagnostic capture into reproduction tests. Invoke to convert a raw codegen recording into a maintainable test file or to build a bug reproduction test with console/network/state diagnostics."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.0.0"
  domain: quality
  triggers: codegen, recording, trim, marker URL, bug repro, diagnostic capture, session recording, Playwright codegen, recording processing, test generation
  role: specialist
  scope: implementation
  output-format: code
  related-skills: playwright-expert, test-master
---

# Playwright Recording Processor

Recording processing specialist that converts raw Playwright codegen output into structured, maintainable E2E tests.

## Core Workflow

1. **Trim** — Run `trim-recording.ts` to cut the raw recording at the marker URL
2. **Classify** — Determine flow type: happy path (feature coverage) or bug reproduction (diagnostic capture)
3. **Swap fixtures** — Replace raw `page` references with project-specific custom fixtures
4. **Harden** — Replace brittle selectors with role-based locators (cross-ref `playwright-expert`)
5. **Assert** — Inject assertions appropriate to flow type: state verification (happy path) or diagnostic capture (bug repro)

## Quick-Start Example

Transform raw recorded actions into an assertion-rich test using the auth fixture:

```typescript
// ❌ Raw recording (untrimmed with manual auth and missing assertions)
await page.goto('https://app.example.com/login');
await page.getByLabel('Email').fill('user@example.com');
await page.getByRole('button', { name: 'Sign in' }).click();
await page.goto('https://app.example.com/invoices/export');
await page.getByRole('button', { name: 'Download' }).click();

// ✅ Processed test (trimmed to marker URL, auth fixture swapped, assertions added)
test('Invoice Export @happy-path', async ({ authenticatedPage: page }) => {
  await page.goto('/invoices/export');
  await expect(page.getByRole('heading', { name: 'Export' })).toBeVisible();
  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toMatch(/\.csv$/);
});
```

## Inputs Required

1. Raw recording file — the `.spec.ts` output from `npx playwright codegen`
2. Marker URL — the path where the feature under test begins (e.g. `/invoices/export`)
3. Flow type — happy path or bug reproduction
4. Auth fixture name — the existing fixture that handles authenticated sessions
5. Output target — `e2e/` or `integration/` depending on scope

If any of these are missing, ask before proceeding.

## Flow Classification

### Happy Path Flow
Use when:
- Testing a new feature for the first time
- Adding coverage for a release
- Tester followed a structured checklist

Output: A clean spec with the full user journey from marker URL to completion, using the existing auth fixture, with assertions added at key checkpoints.

### Bug Reproduction Flow
Use when:
- A nontechnical user reported "the app broke"
- You need to capture what they actually did, in what state, on what browser
- The goal is a reproducible failing test to anchor a fix

Output: A spec with full diagnostic metadata injected — browser, viewport, console errors, network failures, element states at time of failure — plus a structured comment block at the top summarizing the reported issue.

## Reference Guide

Load detailed guidance based on context:

| Topic | Reference | Load When |
|-------|-----------|-----------|
| Assertion Patterns | `references/assertion-patterns.md` | Adding assertions by UI element type |
| Trim Recording | `references/trim-recording.md` | Trimming raw codegen output, marker URL |
| Bug Repro Diagnostics | `references/bug-repro-diagnostics.md` | Diagnostic injection, console/network/state capture |

### Cross-References (from `playwright-expert`, not duplicated)
- For locator hardening patterns, see `playwright-expert` (`selectors-locators.md`)
- For Page Object Model and fixture patterns, see `playwright-expert` (`page-object-model.md`)
- For debugging flaky processed tests, see `playwright-expert` (`debugging-flaky.md`)

## Constraints

### MUST DO
- Always trim to marker URL before processing
- Classify every recording before adding assertions
- Use role-based selectors from `playwright-expert` patterns when hardening
- Attach diagnostic reports to test results for bug repro flows
- Keep trimmed recordings as source-of-truth comments in generated tests

### MUST NOT DO
- Process untrimmed recordings (noise from manual navigation pollutes tests)
- Mix happy-path assertions with diagnostic capture in a single test
- Duplicate locator/POM patterns already covered by `playwright-expert`
- Use `waitForTimeout()` in generated tests (use proper waits)
- Generate tests without assertion injection (bare action-only tests are not useful)

## Output File Placement
- `e2e/`: Full journeys crossing multiple pages or system boundaries
- `integration/`: Scoped to feature area; bug repros usually land here
- `recordings/`: Archive only — raw files are never run directly

## Checklist Before Handing Off
- [ ] Trimmed to marker URL — no auth or pre-feature navigation
- [ ] Auth fixture swapped in correctly
- [ ] All locators are semantic (role, label, text) not positional
- [ ] At least one assertion per logical section (happy path)
- [ ] Diagnostic collection injected (bug repro)
- [ ] Dynamic values parameterized or noted for follow-up
- [ ] Tagged correctly (`@happy-path` or `@bug-repro`)
- [ ] Placed in correct output directory
- [ ] Raw recording archived untouched in `/recordings`

Maintained by [@jeffallan](https://github.com/jeffallan), Principal Consultant at [Synergetic Solutions](https://synergetic.solutions)

[Documentation](https://jeffallan.github.io/claude-skills/skills/quality/playwright-recording-processor/)
