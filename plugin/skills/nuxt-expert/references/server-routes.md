# Server Routes with Nitro and nuxt/server

Everything under `server/` runs only on the server, built by Nitro. Since Nuxt 4.6, `nuxt/server` exports a portable set of handler utilities typed against a web-standard `RequestEvent` (`event.req` is a `Request`, `event.res.headers` is `Headers`). Code written against it runs unchanged on Nuxt 5 (Nitro 3, h3 2).

## When to Use

- Adding JSON endpoints under `server/api/`, or feeds and webhooks under `server/routes/`
- Validating request bodies, queries and params
- Server middleware (auth context, logging), server plugins, cached handlers
- Sessions without a separate auth module

## When Not to Use

- Calling the endpoint from a page: `data-fetching.md`
- Login flows with OAuth providers: `security.md` (nuxt-auth-utils)
- Per-route CDN caching: `rendering.md`

## File Conventions

| File | Route | Methods |
| --- | --- | --- |
| `server/api/products/index.get.ts` | `/api/products` | GET |
| `server/api/products/index.post.ts` | `/api/products` | POST |
| `server/api/products/[id].get.ts` | `/api/products/:id` | GET |
| `server/api/files/[...path].ts` | `/api/files/*` | all |
| `server/routes/sitemap.xml.ts` | `/sitemap.xml` | all |
| `server/middleware/10.context.ts` | every request, ordered by prefix | all |

Method suffixes keep one handler per method and return 405 for the others.

## Handlers with nuxt/server

```ts
// server/api/products/index.get.ts
import { defineEventHandler, getValidatedQuery } from 'nuxt/server'
import { z } from 'zod'
import { listProducts } from '../../utils/products'

const query = z.object({
  page: z.coerce.number().int().min(1).default(1),
  q: z.string().max(100).optional(),
})

export default defineEventHandler(async (event) => {
  const { page, q } = await getValidatedQuery(event, query)
  return listProducts({ page, perPage: 20, search: q })
})
```

```ts
// server/api/products/index.post.ts
import { defineEventHandler, readValidatedBody } from 'nuxt/server'
import { productInput } from '#shared/utils/schemas'
import { requireAdmin } from '../../utils/auth'
import { createProduct } from '../../utils/products'

export default defineEventHandler(async (event) => {
  await requireAdmin(event)
  const input = await readValidatedBody(event, productInput) // 400 on invalid input
  const product = await createProduct(input)
  event.res.status = 201
  return product
})
```

`readValidatedBody` and `getValidatedQuery` accept any Standard Schema library (Zod, Valibot, ArkType) or a function. Return plain objects or arrays: Nitro serializes them as JSON. Since 4.6, handlers that validate their input give typed bodies to `$fetch` callers when `experimental.routeTypedFetch` is on (default in Nuxt 5).

## Errors

```ts
// server/api/products/[id].get.ts
import { createError, defineEventHandler, getRouterParam } from 'nuxt/server'
import { findProduct } from '../../utils/products'

export default defineEventHandler(async (event) => {
  const id = Number(getRouterParam(event, 'id'))
  if (!Number.isInteger(id) || id < 1) {
    throw createError({ status: 400, statusText: 'Invalid product id' })
  }
  const product = await findProduct(id)
  if (!product) {
    throw createError({ status: 404, statusText: 'Product not found' })
  }
  return product
})
```

- Use `status` and `statusText`; `statusCode`/`statusMessage` are deprecated
- Put safe, user-facing details in `data`; never the raw exception. Since 4.6.4, production error responses only carry message and data from errors created with `createError`; other thrown errors are reduced to a generic 500
- Log the real error on the server before throwing the generic one

## Request and Response Helpers

| Need | nuxt/server (4.6+) | h3 v1 equivalent (older code) |
| --- | --- | --- |
| Query | `getQuery(event)`, `getValidatedQuery` | same names |
| JSON body | `readBody(event)`, `readValidatedBody` | same names |
| Form data / files | `await event.req.formData()` | `readMultipartFormData(event)` |
| Raw body | `await event.req.text()` / `.arrayBuffer()` | `readRawBody(event)` |
| Route param | `getRouterParam(event, 'id', { decode: true })` | `getRouterParam(event, 'id')` (decoded) |
| Method | `event.req.method` | `getMethod(event)` |
| Request header | `event.req.headers.get('x-id')` | `getHeader(event, 'x-id')` |
| Response header | `event.res.headers.set('cache-control', 'no-store')` | `setResponseHeader(...)` |
| Status | `event.res.status = 201` | `setResponseStatus(event, 201)` |
| Redirect | `return sendRedirect(event, '/login', 302)` | `await sendRedirect(...)` |
| Call own API | `serverFetch(event, '/api/x')` | `event.$fetch('/api/x')` |
| Client IP | `getRequestIP(event, { xForwardedFor: true })` | same |
| CORS | `const r = handleCors(event, opts); if (r) return r` | `handleCors(event, opts)` |

On Nuxt 4 the auto-imported `defineEventHandler`, `getQuery` and `readBody` are still h3 v1's. Import from `nuxt/server` explicitly. A `nuxt/server` helper that receives an h3 event fails with `NUXT_E8012`: keep each file on one API. When a feature is missing from `nuxt/server` (for example `defineCachedEventHandler` or `useStorage`), write that file in h3 and Nitro style with explicit imports from `h3` and `nitropack/runtime`.

## Server Utilities

```ts
// server/utils/db.ts
import { drizzle } from 'drizzle-orm/node-postgres'
import { useRuntimeConfig } from 'nuxt/server'

let db: ReturnType<typeof drizzle> | undefined

export function useDb() {
  db ??= drizzle(useRuntimeConfig().databaseUrl) // one pool per server process
  return db
}
```

```ts
// server/utils/auth.ts
import { createError, type RequestEvent } from 'nuxt/server'

export async function requireAdmin(event: RequestEvent) {
  const { user } = await requireUserSession(event) // nuxt-auth-utils
  if (user.role !== 'admin') {
    throw createError({ status: 403, statusText: 'Forbidden' })
  }
  return user
}
```

Module-level singletons are fine for connection pools and clients. Never keep per-user data at module scope: one server process serves every user.

## Server Middleware

```ts
// server/middleware/10.request-id.ts
import { defineEventHandler } from 'nuxt/server'

export default defineEventHandler((event) => {
  const id = event.req.headers.get('x-request-id') ?? crypto.randomUUID()
  event.context.requestId = id
  event.res.headers.set('x-request-id', id)
  // return nothing: the request continues to the route handler
})
```

```ts
// server/types/context.d.ts
declare module '@nuxt/schema' {
  interface NuxtRequestContext {
    requestId: string
  }
}
export {}
```

Server middleware runs for every request, including assets in development. Keep it cheap and return nothing unless you mean to end the request.

## Sessions Without a Module

```ts
// server/api/visits.post.ts
import { defineEventHandler, useSession } from 'nuxt/server'

export default defineEventHandler(async (event) => {
  const session = await useSession<{ visits?: number }>(event)
  await session.update(data => ({ visits: (data.visits ?? 0) + 1 }))
  return { visits: session.data.visits }
})
```

The session is sealed into the `nuxt-session` cookie with a key derived from `runtimeConfig.appSecret` (`NUXT_APP_SECRET`). For login, roles and OAuth, use nuxt-auth-utils (`security.md`).

## Cached Handlers and Storage (Nitro)

```ts
// server/api/rates.get.ts
import { defineCachedEventHandler } from 'nitropack/runtime'

export default defineCachedEventHandler(async () => {
  const res = await fetch('https://api.example.com/rates')
  if (!res.ok) throw new Error(`Upstream ${res.status}`)
  return res.json() as Promise<Record<string, number>>
}, {
  maxAge: 60 * 10, // seconds
  swr: true,       // serve stale while refreshing in the background
  name: 'rates',
})
```

```ts
// nuxt.config.ts: storage driver for cache and useStorage
export default defineNuxtConfig({
  nitro: {
    storage: {
      cache: { driver: 'redis', url: process.env.REDIS_URL },
    },
  },
})
```

Never cache a handler whose response depends on the user (cookies, auth headers) unless the cache key includes the user. Since 4.6.4 the `cache`, `swr` and `isr` route rules skip responses that set cookies or send `Cache-Control: private`, but `defineCachedEventHandler` keys are your responsibility (`getKey`).

## Server Plugins and Tasks

```ts
// server/plugins/shutdown.ts
import { defineNitroPlugin } from 'nitropack/runtime'

export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook('close', async () => {
    await closeDbPool()
  })
})
```

Nitro tasks (`experimental.tasks`) and `scheduledTasks` cover cron jobs on Node and Cloudflare. Serverless presets stop work when the response ends, so use the platform's queue or cron for long jobs.

## Typed $fetch

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  experimental: { routeTypedFetch: true, strictRouteTypes: true },
})
```

With these flags, `$fetch('/api/products', { method: 'post', body })` checks `body` against the handler's schema, and a call to a path with no handler fails type-checking. Hand-written `ServerRoutes` augmentations need rewriting when you turn the flag on.

## Common Mistakes

- Returning a database row with password hashes or internal fields: map to a DTO
- `readBody` without validation: always use a schema
- Calling your own API with `$fetch` from a server route: call the function in `server/utils` directly, or `serverFetch(event, path)` to keep the request context
- Long work after the response on serverless presets: hand it to a queue or the platform's `waitUntil`; do not leave a floating promise
