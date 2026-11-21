# Testing with @nuxt/test-utils and Vitest

`@nuxt/test-utils` (4.x) runs tests inside a Nuxt environment, so auto-imports, plugins, `useFetch` and `#components` work as they do in the app. Split tests into three Vitest projects: plain unit tests in Node, component and composable tests in the Nuxt environment, and end-to-end tests against a built server.

## When to Use

- Setting up tests in a Nuxt project
- Testing components that use auto-imported composables or `useFetch`
- Mocking Nuxt composables, components or API endpoints
- Testing server routes and full pages end to end

## When Not to Use

- Large browser test suites, visual regression, page objects: `playwright-expert`
- Test strategy across a whole organization: `test-master`

## Setup

```bash
npm i -D @nuxt/test-utils vitest @vue/test-utils happy-dom playwright-core
```

```ts
// nuxt.config.ts: enables the test utils module (dev only)
export default defineNuxtConfig({
  modules: ['@nuxt/test-utils/module'],
})
```

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config'
import { defineVitestProject } from '@nuxt/test-utils/config'

export default defineConfig({
  test: {
    projects: [
      {
        test: {
          name: 'unit',
          include: ['test/unit/**/*.{test,spec}.ts'],
          environment: 'node',
        },
      },
      await defineVitestProject({
        test: {
          name: 'nuxt',
          include: ['test/nuxt/**/*.{test,spec}.ts'],
          environment: 'nuxt',
        },
      }),
      {
        test: {
          name: 'e2e',
          include: ['test/e2e/**/*.{test,spec}.ts'],
          environment: 'node',
        },
      },
    ],
  },
})
```

```json
// package.json scripts
{
  "scripts": {
    "test": "vitest run",
    "test:unit": "vitest run --project unit",
    "test:nuxt": "vitest run --project nuxt",
    "test:e2e": "vitest run --project e2e"
  }
}
```

Keep pure logic (schemas, formatters in `shared/utils`) in the `unit` project: it starts fastest. Use the `nuxt` project only when the code needs Nuxt.

## Unit Tests

```ts
// test/unit/schemas.test.ts
import { describe, expect, it } from 'vitest'
import { productInput } from '../../shared/utils/schemas'

describe('productInput', () => {
  it('rejects a negative price', () => {
    const result = productInput.safeParse({ name: 'Mug', priceCents: -1 })
    expect(result.success).toBe(false)
  })

  it('defaults the description', () => {
    expect(productInput.parse({ name: 'Mug', priceCents: 900 }).description).toBe('')
  })
})
```

## Component Tests in the Nuxt Environment

```ts
// test/nuxt/ProductCard.test.ts
import { describe, expect, it } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import { ProductCard } from '#components'

describe('ProductCard', () => {
  it('renders the formatted price', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: { id: 1, name: 'Mug', description: '', priceCents: 1299 } },
    })
    expect(wrapper.text()).toContain('$12.99')
  })
})
```

`mountSuspended` wraps the component in the Nuxt app with `<Suspense>`, so top-level `await useFetch` resolves before assertions. Use `renderSuspended` with `@testing-library/vue` for role-based queries.

Mount a page at a route:

```ts
// test/nuxt/product-page.test.ts
import { expect, it } from 'vitest'
import { mountSuspended, registerEndpoint } from '@nuxt/test-utils/runtime'
import App from '~/app.vue'

registerEndpoint('/api/products/7', () => ({
  id: 7, name: 'Teapot', description: 'Ceramic', priceCents: 3500,
}))

it('renders a product page', async () => {
  const wrapper = await mountSuspended(App, { route: '/products/7' })
  expect(wrapper.find('h1').text()).toBe('Teapot')
})
```

## Mocking

`registerEndpoint` answers `$fetch` and `useFetch` calls inside the Nuxt environment:

```ts
registerEndpoint('/api/cart', {
  method: 'POST',
  handler: () => ({ items: 1 }),
})
```

`mockNuxtImport` replaces an auto-import. Call it at the top level of the file; it is hoisted. Use `vi.hoisted` to change the mock per test:

```ts
// test/nuxt/AccountMenu.test.ts
import { describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'
import { mockNuxtImport, mountSuspended } from '@nuxt/test-utils/runtime'
import { AccountMenu } from '#components'

const { sessionMock } = vi.hoisted(() => ({
  sessionMock: vi.fn(() => ({
    loggedIn: ref(false),
    user: ref<null | { name: string }>(null),
    clear: vi.fn(),
  })),
}))

mockNuxtImport('useUserSession', () => sessionMock)

describe('AccountMenu', () => {
  it('shows sign in when logged out', async () => {
    const wrapper = await mountSuspended(AccountMenu)
    expect(wrapper.text()).toContain('Sign in')
  })

  it('greets a logged-in user', async () => {
    sessionMock.mockReturnValueOnce({
      loggedIn: ref(true),
      user: ref({ name: 'Ada' }),
      clear: vi.fn(),
    })
    const wrapper = await mountSuspended(AccountMenu)
    expect(wrapper.text()).toContain('Ada')
  })
})
```

`mockComponent('HeavyChart', { template: '<div>chart</div>' })` swaps a component by name or path.

## End-to-End Tests

```ts
// test/e2e/products.test.ts
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { $fetch, createPage, fetch, setup, url } from '@nuxt/test-utils/e2e'

describe('products', async () => {
  await setup({
    rootDir: fileURLToPath(new URL('../..', import.meta.url)),
    browser: true, // needs playwright-core and a browser: `npx playwright install chromium`
  })

  it('server-renders the product list', async () => {
    const html = await $fetch<string>('/products')
    expect(html).toContain('<h1>Products</h1>')
  })

  it('rejects invalid ids', async () => {
    const res = await fetch('/api/products/abc')
    expect(res.status).toBe(400)
  })

  it('adds to cart after hydration', async () => {
    const page = await createPage()
    await page.goto(url('/products/1'), { waitUntil: 'hydration' })
    await page.getByRole('button', { name: 'Add to cart' }).click()
    await expect.poll(() => page.getByTestId('cart-count').textContent()).toBe('1')
  })
})
```

`setup` builds the app and starts a server once per file, which is slow; group related assertions into one file. Set the environment the server needs (`NUXT_APP_SECRET`, a test database URL) before `setup`, through `env` in the project config or the CI job.

Testing auth flows end to end: log in through the real `/api/login` handler with a seeded user, then reuse the page's cookies. Do not mock the session in e2e tests.

## Testing Server Handlers

Prefer e2e `fetch` against the running server for handlers: it exercises validation, middleware and serialization together. Extract business logic into `server/utils` functions that take plain arguments and test those in the `unit` project.

```ts
// server/utils/pricing.ts
export function applyDiscount(priceCents: number, percent: number): number {
  if (percent < 0 || percent > 100) throw new RangeError('percent out of range')
  return Math.round(priceCents * (1 - percent / 100))
}
```

```ts
// test/unit/pricing.test.ts
import { expect, it } from 'vitest'
import { applyDiscount } from '../../server/utils/pricing'

it('rounds to whole cents', () => {
  expect(applyDiscount(999, 15)).toBe(849)
})

it('rejects invalid percentages', () => {
  expect(() => applyDiscount(999, 120)).toThrow(RangeError)
})
```

## CI

```yaml
# .github/workflows/test.yml (excerpt)
- run: npm ci
- run: npx nuxt prepare           # generates .nuxt types and tsconfigs
- run: npx nuxt typecheck
- run: npx playwright install --with-deps chromium
- run: npm test
```

## Common Mistakes

| Symptom | Fix |
| --- | --- |
| `useFetch is not defined` | Test is in the `node` project; move it to `test/nuxt/` |
| Assertions run before data loads | `mount` instead of `mountSuspended` |
| Real network calls from component tests | `registerEndpoint` for every API the component hits |
| Mock not applied | `mockNuxtImport` inside a test body; move it to the top level |
| e2e suite takes minutes | One `setup` per file; fewer, larger files |
| Types missing in CI | Run `nuxt prepare` before `vitest` and `typecheck` |
