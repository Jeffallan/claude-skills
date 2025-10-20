---
name: Playwright Expert
description: Expert in Playwright end-to-end testing for web applications. Use when writing E2E tests, debugging Playwright tests, setting up test infrastructure, handling test flakiness, or when the user mentions Playwright, browser testing, E2E testing, or UI automation.
---

# Playwright Expert

A specialized skill for creating robust, maintainable end-to-end tests using Playwright. This skill helps you write reliable browser automation tests for modern web applications.

## Instructions

### Core Workflow

1. **Understand testing requirements**
   - Ask what needs to be tested (user flows, features, pages)
   - Identify the application framework (React, Vue, Angular, etc.)
   - Determine test scope (smoke tests, regression, full E2E suite)
   - Ask about existing test infrastructure

2. **Setup and configuration**
   - Verify Playwright installation
   - Configure playwright.config.ts appropriately
   - Set up test project structure
   - Configure browsers, viewports, base URLs
   - Set up CI/CD integration if needed

3. **Write maintainable tests**
   - Use Page Object Model (POM) pattern for complex apps
   - Implement proper selectors (prefer data-testid, role-based)
   - Add proper waits and assertions
   - Handle authentication and state management
   - Write reusable fixtures and helpers

4. **Debug and fix flaky tests**
   - Use Playwright's debugging tools
   - Identify race conditions and timing issues
   - Implement proper wait strategies
   - Add trace collection for failures

5. **Best practices**
   - Keep tests independent and isolated
   - Use meaningful test descriptions
   - Implement proper cleanup and teardown
   - Optimize test execution (parallel, sharding)

### Playwright Best Practices

#### Selector Strategy (Priority Order)
1. **User-facing attributes** (best):
   ```typescript
   await page.getByRole('button', { name: 'Submit' });
   await page.getByLabel('Email address');
   await page.getByPlaceholder('Enter email');
   await page.getByText('Welcome');
   ```

2. **Data-testid** (good for non-semantic elements):
   ```typescript
   await page.getByTestId('user-profile');
   ```

3. **CSS/XPath** (avoid if possible, brittle):
   ```typescript
   await page.locator('.submit-button');
   ```

#### Wait Strategies
```typescript
// Auto-waiting (preferred - built into Playwright)
await page.click('button'); // Automatically waits for element

// Explicit waits when needed
await page.waitForSelector('[data-testid="results"]');
await page.waitForResponse(resp => resp.url().includes('/api/data'));
await page.waitForLoadState('networkidle');

// Assertions with auto-retry
await expect(page.getByText('Success')).toBeVisible();
await expect(page).toHaveURL(/dashboard/);
```

#### Page Object Model Pattern
```typescript
// pages/LoginPage.ts
export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Log in' });
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
    await this.page.waitForURL(/dashboard/);
  }

  async goto() {
    await this.page.goto('/login');
  }
}

// test.spec.ts
test('user can login', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password');
  await expect(page.getByText('Welcome')).toBeVisible();
});
```

#### Fixtures for Reusability
```typescript
// fixtures.ts
import { test as base } from '@playwright/test';

type Fixtures = {
  authenticatedPage: Page;
};

export const test = base.extend<Fixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'password');
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/);

    await use(page);

    // Cleanup if needed
  },
});

// Usage
test('view profile', async ({ authenticatedPage }) => {
  await authenticatedPage.goto('/profile');
  // Test authenticated features
});
```

#### API Mocking and Interception
```typescript
// Mock API responses
await page.route('**/api/users', route => {
  route.fulfill({
    status: 200,
    body: JSON.stringify([
      { id: 1, name: 'John Doe' },
      { id: 2, name: 'Jane Smith' }
    ])
  });
});

// Intercept and modify requests
await page.route('**/api/config', route => {
  const response = await route.fetch();
  const json = await response.json();
  json.feature_flag_enabled = true;
  route.fulfill({ response, json });
});
```

#### Handling Authentication
```typescript
// Save auth state
test('save auth state', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'user@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');
  await page.waitForURL(/dashboard/);

  // Save storage state
  await page.context().storageState({ path: 'auth.json' });
});

// Reuse auth state in config
// playwright.config.ts
export default defineConfig({
  use: {
    storageState: 'auth.json',
  },
});
```

#### Screenshot and Video
```typescript
// Take screenshots
await page.screenshot({ path: 'screenshot.png', fullPage: true });

// Configure in playwright.config.ts
export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
});
```

### Debugging Flaky Tests

#### Common Causes and Solutions

1. **Race Conditions**
   ```typescript
   // Bad: Doesn't wait for API call
   await page.click('button');
   await expect(page.getByText('Success')).toBeVisible();

   // Good: Wait for API response
   await Promise.all([
     page.waitForResponse(resp => resp.url().includes('/api/submit')),
     page.click('button')
   ]);
   await expect(page.getByText('Success')).toBeVisible();
   ```

2. **Animation/Transition Issues**
   ```typescript
   // Disable animations in test mode
   // playwright.config.ts
   use: {
     actionTimeout: 10000,
     navigationTimeout: 30000,
   }

   // Or add CSS to disable animations
   await page.addStyleTag({
     content: '* { animation: none !important; transition: none !important; }'
   });
   ```

3. **Non-deterministic Selectors**
   ```typescript
   // Bad: Order-dependent
   await page.locator('.user-card').first().click();

   // Good: Specific identifier
   await page.getByTestId('user-card-123').click();
   ```

4. **Timing Issues**
   ```typescript
   // Use Playwright's auto-waiting instead of manual delays
   // Bad
   await page.click('button');
   await page.waitForTimeout(3000); // Arbitrary delay

   // Good
   await page.click('button');
   await page.waitForSelector('[data-testid="result"]');
   // or
   await expect(page.getByTestId('result')).toBeVisible();
   ```

### Debug Tools

```typescript
// Debug mode
await page.pause(); // Opens Playwright Inspector

// Slow down execution
test.use({ launchOptions: { slowMo: 100 } });

// Enable verbose logging
DEBUG=pw:api npx playwright test

// Trace viewer (after test runs with trace: 'on')
npx playwright show-trace trace.zip
```

### Configuration Best Practices

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'test-results.xml' }]
  ],

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### CI/CD Integration

```yaml
# GitHub Actions example
name: Playwright Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Install dependencies
        run: npm ci
      - name: Install Playwright Browsers
        run: npx playwright install --with-deps
      - name: Run Playwright tests
        run: npx playwright test
      - uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

## Critical Rules

### Always Do
- Use auto-waiting features (don't add arbitrary timeouts)
- Prefer user-facing selectors (getByRole, getByLabel, etc.)
- Keep tests independent (no shared state between tests)
- Use Page Object Model for complex applications
- Add proper assertions (use expect with auto-retry)
- Enable traces and screenshots for debugging
- Run tests in parallel when possible
- Use fixtures for common setup

### Never Do
- Never use `waitForTimeout()` unless absolutely necessary
- Never rely on brittle CSS selectors (prefer data-testid or semantic selectors)
- Never share state between tests
- Never ignore flaky tests (fix them!)
- Never commit `.auth.json` or sensitive data
- Never use `first()`, `last()`, `nth()` without good reason (non-deterministic)

## Knowledge Base

- **Playwright API**: Expert in all Playwright APIs and features
- **Browser Automation**: Deep understanding of browser automation challenges
- **Test Patterns**: Page Object Model, fixtures, custom matchers
- **Debugging**: Proficient in debugging flaky tests and race conditions
- **CI/CD**: Experience integrating Playwright with various CI systems
- **Performance**: Understanding test optimization and parallelization

## Integration with Other Skills

- **Works with**: Test Master (overall testing strategy), React Expert (testing React apps)
- **Complements**: Frontend framework skills for framework-specific testing approaches

## Examples

### Example 1: E2E Test for User Registration

```typescript
import { test, expect } from '@playwright/test';

test.describe('User Registration', () => {
  test('successful registration flow', async ({ page }) => {
    await page.goto('/register');

    // Fill form
    await page.getByLabel('Email').fill('newuser@example.com');
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByLabel('Confirm Password').fill('SecurePass123!');
    await page.getByLabel(/I agree to the terms/).check();

    // Submit and wait for navigation
    await page.getByRole('button', { name: 'Sign Up' }).click();

    // Verify success
    await expect(page).toHaveURL(/dashboard/);
    await expect(page.getByText('Welcome')).toBeVisible();
  });

  test('validates email format', async ({ page }) => {
    await page.goto('/register');

    await page.getByLabel('Email').fill('invalid-email');
    await page.getByLabel('Password').fill('SecurePass123!');
    await page.getByRole('button', { name: 'Sign Up' }).click();

    await expect(page.getByText('Please enter a valid email')).toBeVisible();
    await expect(page).toHaveURL(/register/);
  });
});
```

### Example 2: Testing with API Mocking

```typescript
test('displays user list from API', async ({ page }) => {
  // Mock the API response
  await page.route('**/api/users', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        users: [
          { id: 1, name: 'Alice', email: 'alice@example.com' },
          { id: 2, name: 'Bob', email: 'bob@example.com' }
        ]
      })
    });
  });

  await page.goto('/users');

  // Verify mocked data is displayed
  await expect(page.getByText('Alice')).toBeVisible();
  await expect(page.getByText('Bob')).toBeVisible();
});
```

## Best Practices Summary

1. **Selector Priority**: Role > Label > Placeholder > Test ID > CSS/XPath
2. **Waiting**: Use auto-waiting, avoid `waitForTimeout()`
3. **Independence**: Each test should run in isolation
4. **Patterns**: Use Page Object Model for maintainability
5. **Debugging**: Enable traces, screenshots, and videos on failure
6. **Performance**: Run tests in parallel, use sharding for large suites
7. **Stability**: Fix flaky tests immediately, don't retry indefinitely
8. **Assertions**: Use Playwright's expect with built-in retry logic
9. **Authentication**: Save and reuse auth state
10. **CI/CD**: Integrate early, run on every commit
