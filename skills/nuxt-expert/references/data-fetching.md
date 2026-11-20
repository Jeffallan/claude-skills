# Data Fetching and State

Nuxt renders a page on the server, serializes what it fetched into the payload, and hydrates the browser from it. `useFetch` and `useAsyncData` do that transfer; `$fetch` does not. Picking the wrong one is the most common cause of double requests and hydration mismatches.

## When to Use

- Loading data a page or component needs to render
- Refetching on parameter change, polling, conditional fetching
- Sharing fetched data or state between components
- Calling an API from a form submit or button
- Forwarding cookies to an API during SSR

## When Not to Use

- Writing the API handler itself: `server-routes.md`
- Caching whole pages at the CDN: `rendering.md`

## Choosing the Tool

| Situation | Use |
| --- | --- |
| Data needed to render, from a URL | `useFetch(url, options)` |
| Data needed to render, from an SDK, CMS client or several calls | `useAsyncData(key, handler)` |
| User action: submit, delete, click | `$fetch` inside the handler |
| Same defaults (base URL, headers) across many calls | `createUseFetch` / `createUseAsyncData` |
| One-time side effect on first render (store init, analytics) | `callOnce` |
| Cross-component SSR-safe state | `useState` or a Pinia store |

```vue
<script setup lang="ts">
// Renders on the server, reused in the browser from the payload
const { data: products, status, error, refresh } = await useFetch('/api/products')

// User action: plain $fetch, then refresh what changed
async function remove(id: number) {
  await $fetch(`/api/products/${id}`, { method: 'DELETE' })
  await refresh()
}
</script>
```

Calling `$fetch('/api/products')` at the top of `<script setup>` runs once on the server and again in the browser during hydration, with nothing passed between them.

## Return Values in Nuxt 4

```ts
const { data, error, status, refresh, execute, clear } = await useFetch<Product[]>('/api/products')
// data:   ShallowRef<Product[] | undefined>   undefined until loaded (was null in Nuxt 3)
// error:  ShallowRef<NuxtError | undefined>
// status: Ref<'idle' | 'pending' | 'success' | 'error'>
```

`data` is a `shallowRef`. Replace it rather than mutating nested fields:

```ts
// No re-render: nested mutation on a shallowRef
data.value?.push(newProduct)

// Re-renders
data.value = [...(data.value ?? []), newProduct]

// Or opt this call into deep reactivity
const { data: cart } = await useFetch('/api/cart', { deep: true })
```

## Keys and Sharing

`useFetch` builds its key from the URL, options and call site. `useAsyncData` takes the key as its first argument. Calls with the same key share one `data`, `error` and `status`.

```ts
// app/composables/useProduct.ts
export function useProduct(id: MaybeRefOrGetter<number>) {
  return useAsyncData(
    () => `product-${toValue(id)}`, // reactive key: changes trigger a refetch
    (_nuxtApp, { signal }) => $fetch<Product>(`/api/products/${toValue(id)}`, { signal }),
  )
}
```

Rules:

- Give an explicit key in every composable, so two components share the cache on purpose
- Calls sharing a key must agree on `deep`, `transform`, `pick`, `getCachedData` and `default`; Nuxt warns in development otherwise
- Data under a key is purged when its last consumer unmounts
- `useNuxtData('product-1')` reads cached data without fetching (optimistic updates)
- `refreshNuxtData('product-1')` and `clearNuxtData('product-1')` refresh or drop it globally

## Reactive Parameters

```vue
<script setup lang="ts">
const page = ref(1)
const search = ref('')

const { data } = await useFetch('/api/products', {
  query: { page, q: search },            // refs in query are watched automatically
  enabled: () => search.value.length !== 1, // Nuxt 4.5+: block fetches while false
  dedupe: 'cancel',                      // a new request aborts the previous one
})
</script>
```

Use a getter URL when a path segment changes:

```ts
const route = useRoute()
const { data } = await useFetch(() => `/api/products/${route.params.id}`)
```

## Options Reference

| Option | Effect |
| --- | --- |
| `lazy: true` | Do not block client navigation; render a loading state from `status` |
| `server: false` | Fetch only in the browser; `data` is `undefined` during SSR and hydration |
| `immediate: false` | Wait for `execute()` |
| `watch: [ref]` / `watch: false` | Extra refetch triggers / disable automatic watching |
| `pick: ['id', 'name']` | Keep only these fields in the payload |
| `transform: (raw) => ...` | Reshape before storing (and before serializing) |
| `default: () => []` | Value instead of `undefined`; restored on `clear()` |
| `getCachedData(key, nuxtApp, ctx)` | Return cached data to skip the request; `ctx.cause` says why it ran |
| `dedupe: 'cancel' \| 'defer'` | Cancel the running request, or reuse it |
| `enabled` | Reactive gate (4.5+) |
| `serialize: false` | Keep data out of the payload (4.6+); for components that never hydrate |

`pick` and `transform` shrink the payload; they do not reduce what the server fetched. Shape the response in the API handler when the upstream data is large.

## Loading and Error States

```vue
<script setup lang="ts">
const { data: orders, status, error, refresh } = await useLazyFetch('/api/orders', {
  default: () => [] as Order[],
})
</script>

<template>
  <p v-if="status === 'pending'">Loading orders…</p>
  <div v-else-if="error" role="alert">
    <p>Could not load orders ({{ error.status }}).</p>
    <button type="button" @click="refresh()">Retry</button>
  </div>
  <OrderTable v-else :orders="orders" />
</template>
```

For a missing record, throw a fatal error so the error page renders with the right status code:

```ts
const { data: product } = await useFetch(() => `/api/products/${route.params.id}`)
if (!product.value) {
  throw createError({ status: 404, statusText: 'Product not found', fatal: true })
}
```

## Custom Fetch Composables

```ts
// app/composables/useApiFetch.ts
export const useApiFetch = createUseFetch((options) => {
  const config = useRuntimeConfig()
  return {
    ...options,
    baseURL: options.baseURL ?? config.public.apiBase,
    onResponseError({ response }) {
      if (response.status === 401) void navigateTo('/login')
    },
  }
})
```

```vue
<script setup lang="ts">
const { data: invoices } = await useApiFetch('/invoices')
</script>
```

`createUseFetch` (4.4+) instances keep SSR key handling. In 4.6, `addons` (`defineUseFetchAddon`) add reusable behavior such as refresh-on-focus or polling. Prefer this over wrapping `useFetch` in a hand-written function, which loses automatic keys.

## Cookies and Headers During SSR

`useFetch` with a relative URL forwards the incoming request's cookies to your own API on the server. `$fetch` does not. When a handler or composable must call your API with the user's cookies during SSR:

```ts
// Inside setup or a plugin
const requestFetch = useRequestFetch()
const { data } = await useAsyncData('me', () => requestFetch('/api/me'))
```

Do not forward `host`, `content-length` or `x-forwarded-*` headers to a third-party API. Send third-party calls from a server route that adds its own credentials (`server-routes.md`).

## State

```ts
// app/composables/useCart.ts
export const useCartCount = () => useState<number>('cart-count', () => 0)
```

`useState` is serialized into the payload and shared across components for the request. Never declare `ref()` at module scope in a composable: on the server that one ref is shared by every user's request.

Pinia (`@pinia/nuxt`) for larger state:

```ts
// app/stores/user.ts
export const useUserStore = defineStore('user', () => {
  const profile = ref<UserProfile | null>(null)
  async function load() {
    profile.value = await $fetch<UserProfile>('/api/me')
  }
  return { profile, load }
})
```

```vue
<script setup lang="ts">
const store = useUserStore()
// Runs once on the server, skipped during hydration
await callOnce('user-profile', () => store.load())
</script>
```

Do not call store actions inside `useAsyncData`: its handler must be a pure fetch that returns the data. Use `callOnce` for side effects, or return the data from `useAsyncData` and assign it.

## Common Mistakes

| Symptom | Cause | Fix |
| --- | --- | --- |
| Request in both server and browser logs | `$fetch` in setup | `useFetch` / `useAsyncData` |
| Data shows on first load, blank after navigation | `lazy` with no loading branch | Render from `status` |
| Two components overwrite each other's data | Same key, different options | Unique keys per shape |
| Template does not update after a push | `shallowRef` | Replace the array, or `deep: true` |
| `null` checks never pass | Nuxt 4 default is `undefined` | `!data.value` |
| API sees no session during SSR | `$fetch` without cookies | `useFetch` or `useRequestFetch()` |
| Hydration mismatch with dates or random IDs | Values differ server vs client | `useId()`, format on server, or `<ClientOnly>` |
