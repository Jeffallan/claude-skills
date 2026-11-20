# Deployment

`nuxt build` runs Vite for the app and Nitro for the server, and writes a self-contained `.output/` folder shaped by a deployment preset. The same code deploys to a Node server, a container, serverless functions, edge workers or static hosting; only the preset and the environment change.

## When to Use

- Shipping a Nuxt app to Node, Docker, Vercel, Netlify, Cloudflare or a static host
- Wiring environment variables and secrets for production
- Debugging a build that works locally but fails on the host

## When Not to Use

- Choosing per-route caching: `rendering.md`
- CI pipelines and infrastructure as code in general: `devops-engineer`

## Requirements (Nuxt 4.6)

- Node.js `^22.22.3`, `^24.15.0` or `>=26.0.0` for building and for Node presets
- Nitro 2 (`nitropack` 2.13.6 or later) bundled with Nuxt 4; Nuxt 5 will move to Nitro 3
- `nuxt build` for anything with a server; `nuxt generate` only for fully static output

## Presets

| Target | Preset | How it is selected |
| --- | --- | --- |
| Any Node host, VM, container | `node-server` | Default |
| Multi-core Node without PM2 | `node_cluster` | `NITRO_PRESET=node_cluster` |
| Vercel | `vercel` | Auto-detected on Vercel builds |
| Netlify | `netlify` | Auto-detected on Netlify builds |
| Cloudflare Workers | `cloudflare_module` | Set explicitly (recommended Cloudflare target) |
| Cloudflare Pages | `cloudflare_pages` | Auto-detected on Pages builds |
| Static host (no server) | `static` | `nuxt generate` |

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: { preset: 'cloudflare_module' },
})
```

The `NITRO_PRESET` variable sets it per build: `NITRO_PRESET=node-server npx nuxt build`. Check the preset list at nitro.build/deploy before naming another one.

## Node Server

```bash
npx nuxt build
NODE_ENV=production PORT=3000 node .output/server/index.mjs
```

- `.output/` contains its own `node_modules`; production needs only that folder
- `PORT`/`NITRO_PORT` and `HOST`/`NITRO_HOST` set the listener (defaults `3000`, `0.0.0.0`)
- Set `NODE_ENV=production`, or Vue Router warnings flood the logs
- Terminate TLS at a reverse proxy (nginx, Caddy, a load balancer); serve under a subpath with `NUXT_APP_BASE_URL`

PM2 cluster example:

```js
// ecosystem.config.cjs
module.exports = {
  apps: [{
    name: 'shop',
    script: './.output/server/index.mjs',
    exec_mode: 'cluster',
    instances: 'max',
    env: { NODE_ENV: 'production', PORT: '3000' },
  }],
}
```

## Docker

```dockerfile
# Dockerfile
FROM node:24-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npx nuxt build

FROM node:24-alpine
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY --from=build /app/.output ./.output
USER node
EXPOSE 3000
HEALTHCHECK CMD wget -qO- http://127.0.0.1:3000/api/health || exit 1
CMD ["node", ".output/server/index.mjs"]
```

```ts
// server/api/health.get.ts
import { defineEventHandler } from 'nuxt/server'

export default defineEventHandler(() => ({ status: 'ok' }))
```

Pass secrets at run time (`docker run -e NUXT_APP_SECRET=... -e NUXT_DATABASE_URL=...`), never as build args: build args persist in image layers. One image then serves every environment.

## Environment Variables

| Variable | Read when | Example |
| --- | --- | --- |
| `NUXT_<KEY>` | Runtime, overrides `runtimeConfig.<key>` | `NUXT_DATABASE_URL` |
| `NUXT_PUBLIC_<KEY>` | Runtime, overrides `runtimeConfig.public.<key>` | `NUXT_PUBLIC_API_BASE` |
| `NUXT_APP_SECRET` | Runtime, root secret for sessions | 32+ random bytes |
| `NUXT_APP_BASE_URL` | Runtime, base path | `/shop/` |
| `NITRO_PRESET` | Build | `vercel` |
| `NITRO_PORT` / `PORT` | Runtime (Node) | `3000` |

Camel-case keys map to upper snake case: `runtimeConfig.stripeSecretKey` reads `NUXT_STRIPE_SECRET_KEY`. Only keys declared in `nuxt.config.ts` are overridden; an undeclared `NUXT_FOO` does nothing. `.env` is read by `nuxt dev`, `nuxt build` and `nuxt preview`, not by the production server: set variables in the host.

## Vercel

- Import the repo; the framework preset is detected and `nuxt build` runs
- Add `NUXT_*` variables per environment in project settings
- `isr` route rules map to Vercel's cache; `isr: true` lasts until the next deploy
- Edge rendering: `NITRO_PRESET=vercel-edge` (check that server dependencies avoid Node-only APIs)

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    '/blog/**': { isr: 3600 },
    '/account/**': { ssr: false },
  },
})
```

## Netlify

- Build command `npx nuxt build`, publish directory `dist` (set by the preset)
- `isr` and `swr` rules become Netlify durable cache rules
- Edge: `NITRO_PRESET=netlify-edge`

## Cloudflare Workers

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'cloudflare_module',
    cloudflare: { deployConfig: true, nodeCompat: true },
  },
})
```

```jsonc
// wrangler.jsonc (bindings)
{
  "name": "shop",
  "compatibility_date": "2026-10-01",
  "compatibility_flags": ["nodejs_compat"],
  "d1_databases": [{ "binding": "DB", "database_name": "shop", "database_id": "<id>" }]
}
```

```ts
// server/api/products/index.get.ts (h3 style: bindings come from Nitro's event context)
import { defineEventHandler } from 'h3'

export default defineEventHandler(async (event) => {
  const db = event.context.cloudflare.env.DB as D1Database
  const { results } = await db.prepare('SELECT id, name FROM products LIMIT 50').all()
  return results
})
```

```bash
npx nuxt build && npx wrangler deploy
```

- Workers have no file system and limited Node APIs; pick drivers that support Workers (D1, KV, R2, Hyperdrive for Postgres)
- Secrets: `npx wrangler secret put NUXT_APP_SECRET`
- In the Cloudflare dashboard, turn off Rocket Loader and Email Address Obfuscation; both rewrite HTML and break hydration
- On Nitro 3 (Nuxt 5) bindings move to `event.req.runtime.cloudflare.env`; keep binding access in one `server/utils` helper so the move is one edit

## Static Hosting

```bash
npx nuxt generate   # prerenders every crawlable route into .output/public
npx serve .output/public
```

- Produces `200.html` (SPA fallback) and `404.html`; configure the host to use them
- No server routes at runtime: `server/api` handlers run only during prerendering, and modules that need a server (nuxt-auth-utils) do not work
- Runtime config is frozen at build time; `NUXT_*` variables on the static host change nothing

## Pre-Deploy Checklist

- `npx nuxt typecheck` and tests pass
- `npx nuxt build` succeeds locally with the production preset
- `npx nuxt preview` serves the build; changed routes load with JavaScript disabled where SEO matters
- Every private `runtimeConfig` key and `NUXT_APP_SECRET` is set in the host
- `grep` of `.output/public` shows no secrets (`security.md`)
- Cache rules exclude user-specific routes

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| Works in dev, 500 in production | Missing `NUXT_*` variable; check server logs for `undefined` config |
| Config value never changes per environment | Key not declared in `runtimeConfig`, or a static build |
| `Cannot find module` on the server | Running from a copied `node_modules` instead of `.output/server` |
| Hydration errors only behind Cloudflare | Rocket Loader or email obfuscation |
| Users see each other's pages | `swr`/`isr`/`cache` on a personalized route |
| Sessions reset on every deploy | `NUXT_APP_SECRET` not set or differs per instance |
