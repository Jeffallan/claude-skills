# Vue SSR Without Nuxt

Server-side rendering with Vue's own APIs (`createSSRApp`, `renderToString`) and a Node server you control. For Nuxt projects (`nuxt.config.ts`, `useFetch`, server routes, route rules, islands, Nuxt 4 upgrades), use the `nuxt-expert` skill instead: Nuxt handles payload transfer, hydration and rendering modes for you.

## When to Use

- An existing Vite + Vue app needs SSR and adopting Nuxt is not an option
- Embedding server-rendered Vue in another Node server (Fastify, Express)
- Understanding or fixing hydration mismatches in any Vue SSR setup

## When Not to Use

- Any Nuxt project: `nuxt-expert`
- Static marketing sites: prerender with Nuxt or VitePress rather than hand-rolled SSR

## Custom SSR with Fastify

For custom Vue 3 SSR without Nuxt, using Fastify as the server:

```typescript
// server.ts
import Fastify from 'fastify'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import App from './App.vue'

const fastify = Fastify({ logger: true })

fastify.get('*', async (request, reply) => {
  const app = createSSRApp(App)

  // Server-side data fetching
  const initialState = await fetchInitialData(request.url)

  const html = await renderToString(app)

  reply.type('text/html').send(`
    <!DOCTYPE html>
    <html>
      <head>
        <title>Vue SSR</title>
        <script>window.__INITIAL_STATE__ = ${JSON.stringify(initialState).replace(/</g, '\\u003c')}</script>
      </head>
      <body>
        <div id="app">${html}</div>
        <script type="module" src="/src/entry-client.ts"></script>
      </body>
    </html>
  `)
})

fastify.listen({ port: 3000 })
```

```typescript
// entry-client.ts
import { createApp } from 'vue'
import App from './App.vue'

const app = createApp(App)

// Hydrate with server state
if (window.__INITIAL_STATE__) {
  app.provide('initialState', window.__INITIAL_STATE__)
}

app.mount('#app')
```

```typescript
// vite.config.ts for SSR
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  build: {
    ssr: true,
    rollupOptions: {
      input: {
        server: './server.ts',
        client: './src/entry-client.ts'
      }
    }
  }
})
```


Escape `<` in serialized state (or use `devalue`) so a `</script>` inside data cannot break out of the tag.

## Hydration Patterns

### Hydration Mismatch Prevention

```vue
<script setup lang="ts">
import { onMounted, ref, useId } from 'vue'

// Values that differ between server and client render only after mount
const currentTime = ref<string | null>(null)
const windowWidth = ref<number | null>(null)
const inputId = useId() // stable across server and client (Vue 3.5+)

onMounted(() => {
  currentTime.value = new Date().toLocaleTimeString()
  windowWidth.value = window.innerWidth
})
</script>

<template>
  <div>
    <span v-if="currentTime">{{ currentTime }}</span>
    <span v-else>--:--:--</span>
    <span v-if="windowWidth !== null">Width: {{ windowWidth }}px</span>
    <label :for="inputId">Search</label>
    <input :id="inputId" type="search">
  </div>
</template>
```

Common causes: `Date.now()` or `Math.random()` in templates, locale or time zone formatting, `window` checks during setup, and invalid HTML nesting that the browser rewrites before hydration.

### Lazy Hydration (Vue 3.5+)

```ts
import { defineAsyncComponent, hydrateOnIdle, hydrateOnVisible } from 'vue'

// Server-renders normally; hydrates only when scrolled into view
const ReviewsList = defineAsyncComponent({
  loader: () => import('./components/ReviewsList.vue'),
  hydrate: hydrateOnVisible(),
})

// Hydrates when the browser is idle
const Newsletter = defineAsyncComponent({
  loader: () => import('./components/Newsletter.vue'),
  hydrate: hydrateOnIdle(),
})
```

Vue also provides `hydrateOnInteraction` and `hydrateOnMediaQuery`. Keep above-the-fold content on normal hydration. In Nuxt the same strategies are template props (`<LazyReviewsList hydrate-on-visible />`); see `nuxt-expert`.

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `createSSRApp()` | App instance for SSR and hydration |
| `renderToString()` | Render the app to HTML on the server |
| `useId()` | IDs that match on server and client |
| `onMounted()` | Client-only values without mismatches |
| `defineAsyncComponent({ hydrate })` | Lazy hydration strategies |
| Nuxt projects | Use the `nuxt-expert` skill |
