# Rendering: Route Rules, Islands and Hydration

Nuxt server-renders every route by default (universal rendering). Route rules change that per path: prerender at build time, cache with SWR or ISR, or skip SSR. Server components (islands) and lazy hydration cut the JavaScript a page ships.

## When to Use

- Choosing SSR, SSG, SWR, ISR or client-only rendering for a section of the site
- Shipping less JavaScript: server components, `hydrate-*` props, `noScripts`
- Fixing hydration mismatch warnings
- Page titles, meta tags and Open Graph data

## When Not to Use

- API response caching inside a handler: `server-routes.md`
- Host-specific deploy settings: `deployment.md`

## Route Rules (Hybrid Rendering)

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    '/': { prerender: true },                         // HTML built at build time
    '/blog/**': { isr: 3600 },                        // CDN cache, regenerate hourly (Vercel, Netlify)
    '/products/**': { swr: 600 },                     // server cache, serve stale while refreshing
    '/account/**': { ssr: false },                    // client-only SPA section
    '/docs/**': { prerender: true, noScripts: true }, // static HTML, no Nuxt JS
    '/api/public/**': { cors: true, headers: { 'cache-control': 's-maxage=60' } },
    '/old-shop/**': { redirect: { to: '/products/**', statusCode: 301 } },
    '/admin/**': { appLayout: 'admin', appMiddleware: ['auth'] },
  },
})
```

| Rule | What happens | Good for |
| --- | --- | --- |
| `prerender: true` | Rendered once at build; served as static file | Marketing, docs, legal pages |
| `swr: seconds` | Nitro caches the response; serves stale, refreshes in background | Catalog pages, listings |
| `isr: seconds \| true` | Like `swr`, cached at the CDN (Vercel, Netlify only); `true` keeps until next deploy | High-traffic content |
| `ssr: false` | Server sends an empty shell; the browser renders | Dashboards behind login |
| `noScripts: true` | No Nuxt JS or resource hints | Content with no interactivity |
| `cache: { maxAge }` | Nitro cache with full options | Fine-grained cache control |
| `redirect`, `proxy` | Handled before your app, often by the host | URL moves, API proxying |
| `headers` | Adds response headers | Cache-Control, CORS tweaks |

Rules:

- Pages behind login must not use `swr`, `isr` or `cache`: they are keyed by URL. Since 4.6.4 Nuxt refuses to cache responses that set cookies or send `Cache-Control: private`, but do not rely on that as the guard
- Route rules are not a security boundary. `redirect` and `proxy` run before server middleware and may be applied by the host. Authorization stays in handlers
- `nuxt generate` builds a fully static site and ignores server-dependent rules. Use `nuxt build` with `prerender` rules for hybrid output
- Prerendered and ISR/SWR pages emit `_payload.json`, so client navigation to them skips the API

Discover dynamic routes to prerender:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: { prerender: { crawlLinks: true, routes: ['/sitemap.xml'] } },
})
```

## Rendering Modes at a Glance

| Need | Choose |
| --- | --- |
| SEO, personalized per request | Default SSR |
| SEO, same for everyone, changes rarely | `prerender` |
| SEO, same for everyone, changes often | `swr` or `isr` |
| No SEO, logged-in app | `ssr: false` for that section |
| Whole app static, no server | `nuxt generate` (with `ssr: true` for prerendered HTML) |
| Global SPA | `ssr: false` in config (loses SSR everywhere; prefer per-route) |

## SSR Streaming (Experimental, 4.5+)

```ts
export default defineNuxtConfig({
  experimental: { ssrStreaming: true },
  routeRules: { '/checkout/**': { streaming: false } },
})
```

Streaming sends the head immediately and the body as Vue renders, which improves time to first byte. Status codes, headers and cookies set after rendering starts cannot reach the client. Routes with `redirect`, `cache`, `swr`, `isr`, `noScripts` or `ssr: false` fall back to buffered rendering, and crawlers get buffered HTML. Turn it off for routes that set status or cookies in page code.

## Server Components and Islands

A `.server.vue` component renders only on the server. Its HTML is embedded in the page and none of its JavaScript (or its dependencies, such as a Markdown parser) reaches the browser. Islands are still marked experimental; `experimental.componentIslands` defaults to `'auto'` and turns on when the project has one.

```vue
<!-- app/components/ProductSpecs.server.vue -->
<script setup lang="ts">
import { renderMarkdown } from '~/utils/markdown' // stays on the server

const props = defineProps<{ productId: number }>()
const { data: specs } = await useFetch(`/api/products/${props.productId}/specs`)
const html = specs.value ? await renderMarkdown(specs.value.markdown) : ''
</script>

<template>
  <section class="specs" v-html="html" />
</template>
```

```vue
<!-- app/pages/products/[id].vue -->
<template>
  <ProductSpecs :product-id="Number($route.params.id)" />
</template>
```

`renderMarkdown` must sanitize its output before `v-html` (`security.md`).

Interactive children inside an island need `selectiveClient`:

```ts
export default defineNuxtConfig({
  experimental: { componentIslands: { selectiveClient: true } },
})
```

```vue
<!-- inside a .server.vue component -->
<AddToCartButton nuxt-client :product-id="productId" />
```

Constraints:

| Constraint | Consequence |
| --- | --- |
| Props are sent as GET query parameters | JSON-serializable only, size-limited, visible in logs and CDN caches; treat as untrusted |
| Island renders in an isolated Vue app | No shared `useState`, Pinia or provide/inject with the page; pass data as props |
| `useRoute()` inside reflects the island request | Pass route data as props |
| Route middleware does not run for islands | Auth checks belong in the API the island calls |
| Client navigation fetches each island | A round trip per island; use `lazy` with a `#fallback` slot, or keep islands few |
| Single root element required | HTML comments count as elements |
| `nuxt-client` only on local SFCs | Wrap built-ins such as `<NuxtLink>` in your own component |

Islands suit content pages reached by full page loads. A component that updates often in the browser should stay a normal component.

## Lazy Hydration

Any auto-imported component with the `Lazy` prefix accepts one hydration strategy:

```vue
<template>
  <HeroBanner />                                        <!-- above the fold: hydrate now -->
  <LazyReviewsList hydrate-on-visible />
  <LazyChatWidget hydrate-on-interaction="click" />
  <LazyMobileMenu hydrate-on-media-query="(max-width: 768px)" />
  <LazyNewsletter :hydrate-after="3000" />
  <LazyRecommendations hydrate-on-idle />
  <LazyFooterLinks hydrate-never />
</template>
```

The props must be written in the template (no `v-bind` spread), and any prop change hydrates the component at once. Do not delay hydration of above-the-fold or interactive-at-load content.

## Client-Only Code

```vue
<template>
  <ClientOnly>
    <MapView :center="center" />
    <template #fallback>
      <div class="map-skeleton" aria-busy="true">Loading map…</div>
    </template>
  </ClientOnly>
</template>
```

Naming the file `MapView.client.vue` has the same effect. Inside a client-only component, wait one `nextTick()` in `onMounted` before measuring the DOM.

## Hydration Mismatches

| Cause | Fix |
| --- | --- |
| `Date.now()`, `Math.random()` in templates | Compute on the server and pass through `useState`, or render in `onMounted` |
| Locale or time zone formatting | Fix the locale and time zone (`Intl.DateTimeFormat('en-US', { timeZone: 'UTC' })`) or format client-side |
| `window`/`localStorage` checks during setup | `onMounted`, `<ClientOnly>` or `import.meta.client` guards |
| Generated IDs | `useId()` |
| Invalid HTML nesting (`<div>` in `<p>`) | Fix the markup; the browser rewrites it before hydration |
| Browser extensions or CDN script injection | Disable Cloudflare Rocket Loader and email obfuscation (`deployment.md`) |

## SEO and Head

```vue
<script setup lang="ts">
const { data: post } = await useFetch(() => `/api/posts/${useRoute().params.slug}`)

useSeoMeta({
  title: () => post.value?.title,
  description: () => post.value?.excerpt,
  ogTitle: () => post.value?.title,
  ogImage: () => post.value?.coverUrl,
  twitterCard: 'summary_large_image',
})
</script>
```

```ts
// nuxt.config.ts: site-wide defaults
export default defineNuxtConfig({
  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      titleTemplate: '%s · Acme',
    },
  },
})
```

Use getters in `useSeoMeta` so values update after fetching. `useServerSeoMeta` stops being auto-imported under the Nuxt 5 flag; `useSeoMeta` covers both cases.

## Performance Checklist

- Prerender or cache every route that does not depend on the user
- Move heavy, static rendering (Markdown, syntax highlighting) into `.server.vue` components
- Add `hydrate-on-visible` to below-the-fold interactive components
- Use `<NuxtImg>` with explicit `width`/`height` and `loading="lazy"` below the fold
- Watch the payload size warning (100 kB, 4.6+); trim with `pick` or server-side DTOs
- `experimental.early404` (4.6+) answers unknown paths without booting the Vue app
