# Security: Secrets, Auth and Headers

A Nuxt app is a browser bundle and a server in one repository, so the main risks are a secret ending up in the bundle or payload, an API route that trusts the page's route middleware, and missing response headers. This reference covers the Nuxt-specific controls; general OWASP work belongs to `secure-code-guardian`.

## When to Use

- Adding login, sessions, roles or OAuth to a Nuxt app
- Deciding where an API key or database URL lives
- Adding CSP and other security headers, rate limits or request size limits
- Reviewing a Nuxt app for leaked secrets or unprotected routes

## When Not to Use

- Server handler mechanics: `server-routes.md`
- Infrastructure secrets management (Vault, cloud KMS): `devops-engineer`

## Secrets and Runtime Config

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    databaseUrl: '',          // NUXT_DATABASE_URL
    stripeSecretKey: '',      // NUXT_STRIPE_SECRET_KEY
    public: {
      stripePublishableKey: '', // NUXT_PUBLIC_STRIPE_PUBLISHABLE_KEY (safe to expose)
    },
  },
})
```

```ts
// server/api/checkout.post.ts
import { defineEventHandler, readValidatedBody, useRuntimeConfig } from 'nuxt/server'
import Stripe from 'stripe'
import { z } from 'zod'

const body = z.object({ priceId: z.string().startsWith('price_') })

export default defineEventHandler(async (event) => {
  const { priceId } = await readValidatedBody(event, body)
  const stripe = new Stripe(useRuntimeConfig().stripeSecretKey)
  const session = await stripe.checkout.sessions.create({
    mode: 'payment',
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: 'https://shop.example.com/thanks',
  })
  return { url: session.url }
})
```

Rules:

- Private keys live at the top level of `runtimeConfig` with empty defaults; values come from `NUXT_*` environment variables at runtime
- Never put a secret in `runtimeConfig.public`, `app.config.ts`, `NUXT_PUBLIC_*` or a literal in `nuxt.config.ts`: all of those reach the browser or the bundle
- Never read `process.env.X` in `app/` code; Vite inlines or drops it unpredictably
- Commit `.env.example` with placeholders; keep `.env` git-ignored
- Do not return secrets inside `useAsyncData` results: everything fetched during SSR is serialized into the page payload

Audit commands (run from the project root):

```bash
# Secrets in public config or app code
grep -rnE "public:\s*\{" nuxt.config.ts
grep -rnE "process\.env\." app/ --include='*.vue' --include='*.ts'
# Built client bundle must not contain server secrets
npx nuxt build && grep -rl "sk_live_\|postgres://" .output/public/ && echo "LEAK"
```

## The Application Secret (Nuxt 4.6+)

`runtimeConfig.appSecret`, set with `NUXT_APP_SECRET`, is the root secret Nuxt and modules derive purpose-specific keys from (`deriveSecret(purpose)`). Sessions in `nuxt/server` and nuxt-auth-utils seal cookies with it.

```bash
openssl rand -base64 32   # store as NUXT_APP_SECRET in the host's secret store
```

Development generates and persists one if missing. Builds never do: a production deploy without `NUXT_APP_SECRET` cannot seal sessions. Every instance behind a load balancer needs the same value; rotating it logs everyone out.

## Authentication with nuxt-auth-utils

nuxt-auth-utils 0.6 (requires Nuxt 4.6+) stores the session in a sealed, HTTP-only cookie and ships helpers for passwords, OAuth and WebAuthn. It needs a running server, so it does not work with `nuxt generate`.

```bash
npx nuxt module add auth-utils
```

```ts
// server/api/login.post.ts
import { createError, defineEventHandler, readValidatedBody } from 'nuxt/server'
import { z } from 'zod'
import { findUserByEmail } from '../utils/users'

const credentials = z.object({
  email: z.string().email().max(254),
  password: z.string().min(8).max(200),
})

export default defineEventHandler(async (event) => {
  const { email, password } = await readValidatedBody(event, credentials)
  const user = await findUserByEmail(email)
  // Same error for unknown email and wrong password
  if (!user || !(await verifyPassword(user.passwordHash, password))) {
    throw createError({ status: 401, statusText: 'Invalid credentials' })
  }
  await setUserSession(event, {
    user: { id: user.id, name: user.name, role: user.role },
    loggedInAt: Date.now(),
  })
  return { ok: true }
})
```

```ts
// shared/types/auth.d.ts: type the session
declare module '#auth-utils' {
  interface User {
    id: number
    name: string
    role: 'admin' | 'customer'
  }
}
export {}
```

```ts
// server/api/orders/index.get.ts
import { defineEventHandler } from 'nuxt/server'
import { listOrdersForUser } from '../../utils/orders'

export default defineEventHandler(async (event) => {
  const { user } = await requireUserSession(event) // 401 when logged out
  return listOrdersForUser(user.id)               // scoped to the owner
})
```

```vue
<!-- app/pages/login.vue -->
<script setup lang="ts">
const { fetch: refreshSession } = useUserSession()
const form = reactive({ email: '', password: '' })
const errorMessage = ref('')

async function submit() {
  errorMessage.value = ''
  try {
    await $fetch('/api/login', { method: 'POST', body: form })
    await refreshSession()
    await navigateTo('/account')
  }
  catch {
    errorMessage.value = 'Email or password is incorrect.'
  }
}
</script>

<template>
  <form @submit.prevent="submit">
    <label>Email <input v-model="form.email" type="email" autocomplete="email" required></label>
    <label>Password <input v-model="form.password" type="password" autocomplete="current-password" required></label>
    <p v-if="errorMessage" role="alert">{{ errorMessage }}</p>
    <button type="submit">Sign in</button>
  </form>
</template>
```

OAuth handlers follow `defineOAuth<Provider>EventHandler({ onSuccess, onError })`, for example `defineOAuthGitHubEventHandler`, with client IDs and secrets from `NUXT_OAUTH_<PROVIDER>_*` variables. Inside `onSuccess`, import helpers such as `sendRedirect` from `nuxt/server`.

Store only identifiers and display data in the session: the cookie size limit is about 4 KB, and the data is sealed but travels with every request.

## Defense in Depth for Routes

| Layer | Purpose | Enough on its own? |
| --- | --- | --- |
| Route middleware (`app/middleware`) | Redirects logged-out users in the UI | No: runs in the browser too |
| `routeRules` (`ssr: false`, `redirect`) | Rendering and URL behavior | No: not a security boundary |
| Server middleware | Attach the user to `event.context` | No: handlers still check roles |
| Handler checks (`requireUserSession`, ownership filter) | Enforce access per resource | Yes |

Every handler that reads or changes user data calls `requireUserSession` and filters by owner or role.

## Security Headers with nuxt-security

```bash
npx nuxt module add security
```

nuxt-security 2.x enables by default: a nonce-based CSP with `'strict-dynamic'`, HSTS, `X-Content-Type-Options`, `X-Frame-Options: SAMEORIGIN`, a referrer policy, Subresource Integrity for bundled scripts, a rate limiter (150 requests per 5 minutes per IP, in-memory), a request size limiter (2 MB body, 8 MB upload), an XSS validator for query and body, and removal of `X-Powered-By` and console loggers in production. CSRF is off by default.

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['nuxt-security'],
  security: {
    headers: {
      contentSecurityPolicy: {
        'img-src': ["'self'", 'data:', 'https://images.example-cdn.com'],
        'connect-src': ["'self'", 'https://api.stripe.com'],
      },
    },
    rateLimiter: {
      tokensPerInterval: 300,
      interval: 60_000,
      driver: { name: 'redis' }, // share limits across instances
    },
  },
  routeRules: {
    '/api/login': {
      security: { rateLimiter: { tokensPerInterval: 5, interval: 60_000 } },
    },
    '/embed/**': {
      security: { headers: { xFrameOptions: false, contentSecurityPolicy: { 'frame-ancestors': ['*'] } } },
    },
  },
})
```

- Configure security headers through `security`, including per-route `routeRules[path].security`; a raw `headers` rule for the same header is overridden
- Nonces only work for server-rendered responses. Prerendered pages use hashes (`ssg.hashScripts`); ISR/SWR cached HTML replays one nonce to many users, so check the module's strict CSP guide before combining CSP nonces with caching
- The in-memory rate limiter is per process. Use a shared driver behind a load balancer, or the platform's rate limiting
- Enable `csrf: true` (nuxt-csurf) when cookie sessions accept form posts from other origins; same-site `lax` cookies already block most cross-site POSTs

## Island and Rendering Pitfalls

- Island props travel in the URL: never pass tokens, emails or other personal data as props to a `.server.vue` component
- Validate and clamp island props; map string props to components through an allowlist, never `<component :is="prop">`
- `v-html` only with sanitized HTML (DOMPurify on the client, `isomorphic-dompurify` or a Markdown pipeline with sanitize on the server)
- Production error pages show only `createError` messages since 4.6.4; still avoid putting stack traces or SQL in `statusText`

## Dependency and Version Hygiene

- Stay on the latest 4.6.x patch: 4.6.4 fixed eight Nuxt and three Nitro advisories (November 2026)
- Nuxt 3 is end-of-life since July 31, 2026 and receives no security fixes
- Run `npx nuxt upgrade --dedupe` so Nitro, h3 and unjs packages update together
- Dev servers behind a tunnel need `devServer.allowedHosts`; never expose `nuxt dev` publicly
