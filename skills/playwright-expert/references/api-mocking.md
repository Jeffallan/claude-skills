# API Mocking

> Reference for: Playwright Expert
> Load when: Mocking API responses, route interception

## Basic Route Mocking

```typescript
test('displays mocked user data', async ({ page }) => {
  await page.route('**/api/users', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
      ]),
    })
  );

  await page.goto('/users');
  await expect(page.getByText('Alice')).toBeVisible();
  await expect(page.getByText('Bob')).toBeVisible();
});
```

## Mock Error Responses

```typescript
test('handles API error gracefully', async ({ page }) => {
  await page.route('**/api/users', route =>
    route.fulfill({
      status: 500,
      body: JSON.stringify({ error: 'Server error' }),
    })
  );

  await page.goto('/users');
  await expect(page.getByText('Failed to load users')).toBeVisible();
});
```

## Conditional Mocking

```typescript
test('mock specific requests', async ({ page }) => {
  await page.route('**/api/**', route => {
    const url = route.request().url();

    if (url.includes('/api/users')) {
      return route.fulfill({
        status: 200,
        json: [{ id: 1, name: 'Mocked User' }],
      });
    }

    // Let other requests through
    return route.continue();
  });
});
```

## Modify Responses

```typescript
test('modify API response', async ({ page }) => {
  await page.route('**/api/products', async route => {
    // Get real response
    const response = await route.fetch();
    const json = await response.json();

    // Modify it
    json.products = json.products.map(p => ({
      ...p,
      price: p.price * 0.9, // 10% discount
    }));

    // Return modified response
    await route.fulfill({ json });
  });
});
```

## Wait for Response

```typescript
test('waits for API response', async ({ page }) => {
  const responsePromise = page.waitForResponse('**/api/users');

  await page.getByRole('button', { name: 'Load Users' }).click();

  const response = await responsePromise;
  expect(response.status()).toBe(200);
});
```

## Mock Network Conditions

```typescript
test('slow network', async ({ page }) => {
  await page.route('**/api/**', async route => {
    await new Promise(resolve => setTimeout(resolve, 3000));
    await route.continue();
  });

  await page.goto('/dashboard');
  await expect(page.getByText('Loading...')).toBeVisible();
});
```

## HAR File Mocking

```typescript
// Record responses
await page.routeFromHAR('mocks/api.har', {
  url: '**/api/**',
  update: true, // Record new responses
});

// Playback recorded responses
await page.routeFromHAR('mocks/api.har', {
  url: '**/api/**',
  update: false,
});
```

## Quick Reference

| Method | Purpose |
|--------|---------|
| `route.fulfill()` | Return mock response |
| `route.continue()` | Pass to real server |
| `route.fetch()` | Get real response |
| `route.abort()` | Block request |
| `waitForResponse()` | Wait for API call |
| `routeFromHAR()` | Use recorded responses |

| Pattern | Use Case |
|---------|----------|
| Mock all | Isolated testing |
| Mock errors | Error handling |
| Modify response | Test edge cases |
| Network delay | Loading states |
