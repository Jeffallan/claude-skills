# Bug Repro Diagnostics Reference

Diagnostic injection patterns for converting codegen recordings into bug reproduction tests with full environment and state capture.

## When to Use Bug Repro Flow

Use bug repro (not happy path) when:
- A nontechnical user reported "the app broke" and you have their recorded session
- The goal is a reproducible failing test, not feature coverage
- You need to capture browser state, console errors, and network failures at the point of failure

## Diagnostic Injection Workflow

### Step 1: Add Comment Header

```typescript
/**
 * BUG REPRODUCTION TEST
 * Reported: 2024-03-15
 * Symptom: Export button does nothing after selecting date range
 * Browser: captured at runtime (see diagnosticReport)
 * Steps to reproduce: trimmed from user session recording
 * Expected: CSV download starts
 * Actual: Button click has no effect, no error shown
 */
```

### Step 2: Inject Environment Capture (before marker URL line)

```typescript
// Capture environment at session start
const browserName = page.context().browser()?.browserType().name();
const viewport = page.viewportSize();
const userAgent = await page.evaluate(() => navigator.userAgent);
```

### Step 3: Set Up Console Error Listener

```typescript
const consoleErrors: string[] = [];
page.on('console', msg => {
  if (msg.type() === 'error') consoleErrors.push(msg.text());
});

// Also catch uncaught exceptions
const pageErrors: string[] = [];
page.on('pageerror', err => pageErrors.push(err.message));
```

### Step 4: Set Up Network Failure Capture

```typescript
const failedRequests: { method: string; url: string; error: string }[] = [];
page.on('requestfailed', req => {
  failedRequests.push({
    method: req.method(),
    url: req.url(),
    error: req.failure()?.errorText ?? 'unknown',
  });
});

// Also capture non-2xx responses
const badResponses: { status: number; url: string }[] = [];
page.on('response', res => {
  if (res.status() >= 400) {
    badResponses.push({ status: res.status(), url: res.url() });
  }
});
```

### Step 5: Element State Snapshot at Failure Point

Insert this immediately before the action that the user reported as failing:

```typescript
const elementSnapshot = await page.locator('[data-testid="submit-btn"]').evaluate(el => ({
  disabled: (el as HTMLButtonElement).disabled,
  visible: (el as HTMLElement).offsetParent !== null,
  text: el.textContent,
  classes: el.className,
  ariaLabel: el.getAttribute('aria-label'),
  boundingBox: el.getBoundingClientRect().toJSON(),
}));
```

### Step 6: Attach Diagnostic Report

At the end of the test, attach all captured data to the test results:

```typescript
await test.info().attach('diagnostic-report', {
  body: JSON.stringify({
    browser: browserName,
    viewport,
    userAgent,
    consoleErrors,
    pageErrors,
    failedRequests,
    badResponses,
    elementSnapshot,
    timestamp: new Date().toISOString(),
  }, null, 2),
  contentType: 'application/json',
});
```

## Complete Example: Raw Recording to Bug Repro Test

**Input:** Raw codegen recording of a user who reported "export button doesn't work"

**Output:**
```typescript
import { test, expect } from '@playwright/test';

/**
 * BUG REPRODUCTION TEST
 * Reported: 2024-03-15
 * Symptom: Export button does nothing after selecting date range
 * Expected: CSV download starts
 * Actual: Button click has no effect
 */
test('invoice-export-bug-repro @bug-repro', async ({ authenticatedPage: page }) => {
  // -- Diagnostic setup --
  const browserName = page.context().browser()?.browserType().name();
  const viewport = page.viewportSize();
  const userAgent = await page.evaluate(() => navigator.userAgent);

  const consoleErrors: string[] = [];
  page.on('console', msg => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });
  const failedRequests: string[] = [];
  page.on('requestfailed', req => failedRequests.push(req.url()));

  // -- Trimmed user actions (from marker URL) --
  await page.goto('/invoices/export');
  await page.getByLabel('Date Range').fill('last-30-days');
  await page.getByLabel('Format').selectOption('CSV');

  // -- Element state before reported failure --
  const btnState = await page.getByRole('button', { name: 'Download' }).evaluate(el => ({
    disabled: (el as HTMLButtonElement).disabled,
    visible: (el as HTMLElement).offsetParent !== null,
  }));

  await page.getByRole('button', { name: 'Download' }).click();

  // -- Attach diagnostics --
  await test.info().attach('diagnostic-report', {
    body: JSON.stringify({
      browser: browserName, viewport, userAgent,
      consoleErrors, failedRequests, btnState,
      timestamp: new Date().toISOString(),
    }, null, 2),
    contentType: 'application/json',
  });
});
```

## Quick Reference: Diagnostic Capture Methods

| What | API | Notes |
|------|-----|-------|
| Console errors | `page.on('console', ...)` | Filter by `msg.type() === 'error'` |
| Uncaught exceptions | `page.on('pageerror', ...)` | Catches unhandled throws |
| Failed requests | `page.on('requestfailed', ...)` | DNS, CORS, timeout failures |
| Bad responses | `page.on('response', ...)` | Filter `status >= 400` |
| Element state | `locator.evaluate(...)` | disabled, visible, text, classes |
| Screenshot | `page.screenshot()` | Use `testInfo.attach()` for report |
| Browser info | `browser().browserType().name()` | Via context |
| Viewport | `page.viewportSize()` | Width/height object |
| User agent | `page.evaluate(() => navigator.userAgent)` | Full UA string |
