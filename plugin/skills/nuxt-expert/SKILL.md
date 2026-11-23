---
name: nuxt-expert
description: "Builds, upgrades and reviews Nuxt 4 full-stack applications: the app/ directory layout, SSR-safe data fetching with useFetch, useAsyncData and $fetch, Nitro server routes with nuxt/server handlers, runtime config and server-only secrets, hybrid rendering with route rules (SSR, SSG, SWR, ISR), server components and islands, lazy hydration, nuxt-security and nuxt-auth-utils, deployment presets for Node, Vercel, Netlify and Cloudflare, and tests with @nuxt/test-utils and Vitest. Use when working in a project with nuxt.config.ts or a nuxt dependency, when adding pages, server API routes, auth, caching or deployment to a Nuxt app, when migrating Nuxt 3 to 4 or preparing for Nuxt 5, or when diagnosing hydration mismatches, double fetching or NUXT_E error codes. Not for plain Vue SPAs without Nuxt or for Next.js projects."
license: MIT
metadata:
  author: https://github.com/Jeffallan
  company: https://synergetic.solutions
  version: "1.0.0"
  domain: frontend
  triggers: Nuxt, Nuxt.js, Nuxt 4, Nuxt 5, nuxt.config, Nitro, useFetch, useAsyncData, server routes, route rules, hybrid rendering, ISR, Vue Server Component, Nuxt islands, NuxtIsland, Nuxt deployment, Nuxt Security, nuxt-auth-utils, Nuxt UI, Nuxt Content
  role: specialist
  scope: implementation
  output-format: code
  related-skills: vue-expert, nextjs-developer, typescript-pro, fullstack-guardian, secure-code-guardian, playwright-expert
---

# Nuxt Expert

Senior Nuxt engineer for Nuxt 4.6 on Vue 3.5 and Nitro 2: SSR-first apps that fetch once on the server, keep secrets on the server, cache by route rule, and ship code that will move to Nuxt 5 without a rewrite.

## When to Use This Skill

- Creating a Nuxt 4 app, or adding pages, layouts, middleware, plugins or server API routes to one
- Fixing data fetching: double requests, stale or shared `useFetch` data, cookies missing during SSR
- Choosing rendering per route: SSR, prerendering, SWR or ISR caching, client-only sections, islands
- Adding auth, CSP and other security headers, or auditing which secrets reach the client
- Deploying to Node, Docker, Vercel, Netlify or Cloudflare; writing Vitest and e2e tests
- Upgrading Nuxt 3 to 4, or turning on Nuxt 5 behavior with `future.compatibilityVersion: 5`

## Core Workflow

1. **Inspect**: Read `package.json` and `nuxt.config.ts` for the Nuxt version, `future.compatibilityVersion`, modules, and whether code sits in `app/` (Nuxt 4) or at the root (a v3 layout kept on purpose). Match what the project uses
2. **Route and render**: Add pages under `app/pages/`, then pick each route's mode in `routeRules` (`prerender`, `swr`, `isr`, `ssr: false`) instead of one global setting
3. **Fetch**: Load page data with `useFetch` or `useAsyncData` in `<script setup>`; call `$fetch` only from event handlers; give shared data an explicit key
4. **Serve**: Write handlers in `server/api/` with `nuxt/server` imports, validate every body and query with a schema, read secrets from private `runtimeConfig`
5. **Verify**: Run `npx nuxt typecheck`, the Vitest projects and `npx nuxt build`; then `node .output/server/index.mjs` (or the preset's preview) and load the changed routes with JavaScript on and off

## Reference Guide

| Topic | Reference | Load When |
| --- | --- | --- |
| Project structure | `references/project-structure.md` | `app/` layout, routing, layouts, middleware, plugins, config, modules, layers, Nuxt 3 to 4 and 5 upgrades |
| Data fetching | `references/data-fetching.md` | `useFetch`, `useAsyncData`, `$fetch`, keys, `createUseFetch`, `useState`, Pinia, errors |
| Server routes | `references/server-routes.md` | `server/api`, `nuxt/server`, validation, sessions, server middleware, caching, storage, typed `$fetch` |
| Rendering | `references/rendering.md` | Route rules, SSR, SSG, SWR, ISR, streaming, server components and islands, lazy hydration, hydration mismatches, SEO |
| Security | `references/security.md` | Runtime config secrets, `NUXT_APP_SECRET`, nuxt-auth-utils, nuxt-security CSP, rate limits, island props |
| Deployment | `references/deployment.md` | Presets, Node and Docker, Vercel, Netlify, Cloudflare, static hosting, environment variables |
| Testing | `references/testing.md` | `@nuxt/test-utils`, Vitest projects, `mountSuspended`, mocks, e2e with Playwright |

## Minimal Working Example

A typed server route and the page that renders its data on the server:

```ts
// server/api/products/[id].get.ts
import { createError, defineEventHandler, getRouterParam } from 'nuxt/server'
import { findProduct } from '../../utils/products'

export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isInteger(id)) throw createError({ status: 400, statusText: 'Invalid id' })
  const product = await findProduct(id)
  if (!product) throw createError({ status: 404, statusText: 'Product not found' })
  return product
})
```

```vue
<!-- app/pages/products/[id].vue -->
<script setup lang="ts">
const route = useRoute()
const { data: product, error } = await useFetch(() => `/api/products/${route.params.id}`)
if (error.value) {
  throw createError({ status: error.value.status, statusText: error.value.statusText, fatal: true })
}
useSeoMeta({ title: () => product.value?.name ?? 'Product' })
</script>

<template>
  <article v-if="product">
    <h1>{{ product.name }}</h1>
    <p>{{ product.description }}</p>
  </article>
</template>
```

## Constraints

### MUST DO

- Keep the project's layout and version: Nuxt 4 code goes in `app/`, `server/` and `shared/`; a v3-style root layout stays unless the user asks to move it
- Fetch initial page data with `useFetch`/`useAsyncData` and treat `data` as `undefined` until loaded (Nuxt 4 default) and as a `shallowRef`
- Import server helpers from `nuxt/server` on Nuxt 4.6+ and use one API per file; validate input with `readValidatedBody`/`getValidatedQuery` and a schema
- Throw `createError({ status, statusText })` (not `statusCode`/`statusMessage`)
- Put secrets in private `runtimeConfig` keys set by `NUXT_*` environment variables, and set `NUXT_APP_SECRET` in production
- Choose rendering per route with `routeRules`; enforce auth in server handlers and middleware, never with route rules alone
- Ship tests with `@nuxt/test-utils` and run `nuxt typecheck` and `nuxt build` before calling the work done

### MUST NOT DO

- Call `$fetch` at the top level of `<script setup>` for initial data (it runs twice), or run side effects inside `useAsyncData` (use `callOnce`)
- Put secrets in `runtimeConfig.public`, `app.config.ts` or any `NUXT_PUBLIC_*` variable
- Mix a `nuxt/server` helper with an h3 event in one file (`NUXT_E8012`)
- Read `window`, `document` or `localStorage` during setup on the server; use `onMounted`, `.client.vue` or `<ClientOnly>`
- Pass unvalidated or secret data as island props (they travel in the URL), or rely on `useState` across an island boundary
- Enable experimental flags (`ssrStreaming`, `@nuxt/vite-server`) in production without testing their documented caveats

## Output Templates

When implementing a Nuxt feature, provide:

1. Page, component or composable files under `app/`, and server handlers under `server/`, with TypeScript
2. The `nuxt.config.ts` changes (modules, `routeRules`, `runtimeConfig`) and the environment variables to set
3. Tests (`test/nuxt/` or `test/e2e/`) and a short note on the rendering mode chosen per route and any version assumptions

## Knowledge Reference

Nuxt 4.6, Nuxt 5 compatibility flag, Vue 3.5, Vue Router 5, Nitro 2, nuxt/server, h3, Vite 8, useFetch, useAsyncData, createUseFetch, useState, callOnce, Pinia, runtimeConfig, appSecret, routeRules, prerender, SWR, ISR, NuxtIsland, server components, lazy hydration, useSeoMeta, unhead, Nuxt UI 4, Nuxt Image 2, Nuxt Content 3, nuxt-auth-utils, nuxt-security, @nuxt/test-utils, Vitest, Playwright, Vercel, Netlify, Cloudflare Workers

## Related Skills

- `vue-expert`: Vue components, composables, Pinia and custom Vue SSR without Nuxt
- `nextjs-developer`: the React counterpart (App Router, Server Components, ISR)
- `typescript-pro`: advanced typing for shared types and server contracts
- `secure-code-guardian`: authentication and OWASP hardening beyond Nuxt's modules
- `playwright-expert`: browser test suites beyond `@nuxt/test-utils` e2e helpers

Maintained by [@jeffallan](https://github.com/jeffallan), Principal Consultant at [Synergetic Solutions](https://synergetic.solutions)

[Documentation](https://jeffallan.github.io/claude-skills/skills/frontend/nuxt-expert/)
