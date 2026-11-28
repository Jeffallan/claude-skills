# Assertion Patterns Reference

Common `expect()` patterns by UI element type. Use during the optimization pass to add meaningful assertions to trimmed recordings.

## URL / Navigation

```typescript
await expect(page).toHaveURL('/dashboard');
await expect(page).toHaveURL(/\/invoices\/\d+/);  // regex for dynamic IDs
await expect(page).not.toHaveURL('/login');        // confirm not redirected out
```

## Visibility

```typescript
await expect(page.getByText('Submission successful')).toBeVisible();
await expect(page.getByRole('alert')).toBeVisible();
await expect(page.getByTestId('loading-spinner')).toBeHidden();
await expect(page.getByRole('dialog')).not.toBeVisible();
```

## Form State

```typescript
await expect(page.getByLabel('Email')).toHaveValue('user@example.com');
await expect(page.getByRole('checkbox', { name: 'Remember me' })).toBeChecked();
await expect(page.getByRole('button', { name: 'Submit' })).toBeDisabled();
await expect(page.getByRole('button', { name: 'Submit' })).toBeEnabled();
```

## Text Content

```typescript
await expect(page.getByRole('heading')).toHaveText('Invoice Export');
await expect(page.getByRole('status')).toContainText('3 items');
await expect(page.locator('table')).toContainText('Q1 2024');
```

## Count / List

```typescript
await expect(page.getByRole('listitem')).toHaveCount(5);
await expect(page.locator('tr')).toHaveCount(11); // 10 rows + header
```

## Download

```typescript
const downloadPromise = page.waitForEvent('download');
await page.getByRole('button', { name: 'Download' }).click();
const download = await downloadPromise;
expect(download.suggestedFilename()).toMatch(/\.csv$/);
```

## Toast / Notification (transient)

```typescript
// Must catch before it disappears
const toast = page.getByRole('status');
await expect(toast).toBeVisible();
await expect(toast).toContainText('Saved');
```

## Table Cell

```typescript
const row = page.getByRole('row', { name: /Invoice #1042/ });
await expect(row.getByRole('cell', { name: 'Paid' })).toBeVisible();
```

## Locator Priority (Highest to Lowest)

Use these in order — stop at the first one that works cleanly:

1. `getByRole()` — most semantic, tied to ARIA
2. `getByLabel()` — for form fields
3. `getByPlaceholder()` — fallback for unlabeled inputs
4. `getByText()` — for non-interactive content
5. `getByTestId()` — when `data-testid` is available
6. `locator('css')` — last resort, flag for dev to add testid

Never use `nth-child`, positional, or deeply nested CSS selectors in optimized tests.

## Bug Repro: State Capture Snippets

### Console errors

```typescript
const errors: string[] = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
```

### Failed requests

```typescript
const failed: string[] = [];
page.on('requestfailed', r => failed.push(`${r.method()} ${r.url()}`));
```

### Element state at failure

```typescript
const state = await page.locator('#submit-btn').evaluate(el => ({
  disabled: (el as HTMLButtonElement).disabled,
  visible: (el as HTMLElement).offsetParent !== null,
  text: el.textContent?.trim(),
  ariaLabel: el.getAttribute('aria-label'),
}));
```

### Full diagnostic attach

```typescript
await test.info().attach('session-diagnostics', {
  body: JSON.stringify({ errors, failed, state, ts: new Date().toISOString() }, null, 2),
  contentType: 'application/json',
});
```
