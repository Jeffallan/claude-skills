# Debugging & Flaky Tests

> Reference for: Playwright Expert
> Load when: Debugging tests, fixing flaky tests

## Debugging Tools

```typescript
// Pause execution and open inspector
await page.pause();

// Enable step-by-step mode
PWDEBUG=1 npx playwright test

// Slow motion
test.use({ launchOptions: { slowMo: 500 } });

// Headed mode
npx playwright test --headed
```

## Trace Viewer

```bash
# View trace from failed test
npx playwright show-trace trace.zip

# Generate trace always
test.use({ trace: 'on' });

# View in UI mode
npx playwright test --ui
```

## Common Flaky Test Causes

### 1. Race Conditions

```typescript
// ❌ Bad: Element may not exist yet
await page.click('.submit-btn');

// ✅ Good: Auto-waiting built in
await page.getByRole('button', { name: 'Submit' }).click();
```

### 2. Animation/Transitions

```typescript
// ❌ Bad: Click during animation
await page.click('.menu-item');

// ✅ Good: Wait for stable state
await page.getByRole('menuitem').click();
await expect(page.getByRole('menu')).toBeVisible();
```

### 3. Network Timing

```typescript
// ❌ Bad: Assumes data loaded
await page.goto('/dashboard');
expect(await page.textContent('.user-name')).toBe('John');

// ✅ Good: Wait for network
await page.goto('/dashboard');
await page.waitForResponse('**/api/user');
await expect(page.getByTestId('user-name')).toHaveText('John');
```

### 4. Test Isolation

```typescript
// ❌ Bad: Tests share state
test('test 1', async () => { /* creates user */ });
test('test 2', async () => { /* assumes user exists */ });

// ✅ Good: Each test is independent
test.beforeEach(async ({ page }) => {
  await page.request.post('/api/test/reset');
});
```

## Proper Waiting

```typescript
// Wait for element state
await expect(page.getByText('Success')).toBeVisible();
await expect(page.getByRole('button')).toBeEnabled();
await expect(page.getByRole('dialog')).toBeHidden();

// Wait for navigation
await page.waitForURL(/dashboard/);

// Wait for response
await page.waitForResponse(r => r.url().includes('/api/data'));

// Wait for load state
await page.waitForLoadState('networkidle');

// AVOID arbitrary waits
await page.waitForTimeout(3000); // ❌ BAD
```

## Retry Strategies

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,

  // Retry only specific tests
  expect: {
    timeout: 10000, // Increase assertion timeout
  },
});

// Per-test retry
test('flaky test', async ({ page }) => {
  test.info().annotations.push({ type: 'issue', description: 'Known flaky' });
  // ...
});
```

## Debugging Output

```typescript
// Console output
test('debug test', async ({ page }) => {
  page.on('console', msg => console.log(msg.text()));
  page.on('pageerror', err => console.log(err.message));
});

// Screenshot on step
await page.screenshot({ path: 'debug.png' });
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `PWDEBUG=1` | Enable inspector |
| `--headed` | Show browser |
| `--ui` | UI mode |
| `page.pause()` | Pause execution |
| `show-trace` | View trace file |

| Fix | Flaky Cause |
|-----|-------------|
| Auto-wait locators | Race conditions |
| `waitForResponse` | Network timing |
| Test isolation | Shared state |
| Increase timeout | Slow operations |
