# Nuxt 3

> Reference for: Vue Expert
> Load when: Nuxt 3, SSR, file-based routing, useFetch, server routes

## Project Structure

```
my-nuxt-app/
├── app.vue              # Root component (optional)
├── nuxt.config.ts       # Nuxt configuration
├── package.json
├── tsconfig.json
├── .output/             # Build output
├── assets/              # Uncompiled assets (CSS, images)
├── public/              # Static files (served at root)
├── components/          # Auto-imported components
│   ├── AppHeader.vue
│   └── base/
│       └── Button.vue   # Used as <BaseButton>
├── composables/         # Auto-imported composables
│   └── useAuth.ts
├── layouts/             # Layout components
│   ├── default.vue
│   └── admin.vue
├── middleware/          # Route middleware
│   └── auth.ts
├── pages/               # File-based routing
│   ├── index.vue        # /
│   ├── about.vue        # /about
│   ├── users/
│   │   ├── index.vue    # /users
│   │   └── [id].vue     # /users/:id
│   └── [...slug].vue    # Catch-all route
├── plugins/             # Plugins
│   └── api.ts
├── server/              # Server API routes
│   ├── api/
│   │   └── users.ts     # /api/users
│   └── middleware/
│       └── log.ts
└── stores/              # Pinia stores
    └── user.ts
```

## File-based Routing

```vue
<!-- pages/index.vue -->
<script setup lang="ts">
definePageMeta({
  title: 'Home',
  layout: 'default'
})
</script>

<template>
  <div>
    <h1>Home Page</h1>
  </div>
</template>

<!-- pages/about.vue -->
<template>
  <div>About Page</div>
</template>

<!-- pages/users/[id].vue - Dynamic route -->
<script setup lang="ts">
const route = useRoute()
const userId = computed(() => route.params.id)

const { data: user } = await useFetch(`/api/users/${userId.value}`)
</script>

<template>
  <div>
    <h1>User: {{ user?.name }}</h1>
  </div>
</template>

<!-- pages/blog/[...slug].vue - Catch-all route -->
<script setup lang="ts">
const route = useRoute()
const slug = route.params.slug // ['2024', '12', 'my-post']
</script>

<template>
  <div>Blog post: {{ slug }}</div>
</template>
```

## Layouts

```vue
<!-- layouts/default.vue -->
<template>
  <div>
    <header>
      <nav>Navigation</nav>
    </header>
    <main>
      <slot /> <!-- Page content goes here -->
    </main>
    <footer>Footer</footer>
  </div>
</template>

<!-- layouts/admin.vue -->
<script setup lang="ts">
definePageMeta({
  middleware: 'auth' // Protect with middleware
})
</script>

<template>
  <div class="admin-layout">
    <aside>Admin Sidebar</aside>
    <main>
      <slot />
    </main>
  </div>
</template>

<!-- pages/admin/dashboard.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'admin'
})
</script>

<template>
  <div>Admin Dashboard</div>
</template>
```

## Data Fetching

```vue
<script setup lang="ts">
interface User {
  id: number
  name: string
  email: string
}

// useFetch - SSR-safe, auto-imports
const { data: users, pending, error, refresh } = await useFetch<User[]>('/api/users')

// With options
const { data } = await useFetch('/api/users', {
  method: 'POST',
  body: { name: 'John' },
  headers: {
    'Authorization': 'Bearer token'
  },
  query: { page: 1, limit: 10 },
  // Transform response
  transform: (data) => data.map(u => ({ ...u, fullName: u.firstName + ' ' + u.lastName })),
  // Pick specific keys
  pick: ['id', 'name'],
  // Watch for changes
  watch: [page, limit]
})

// useAsyncData - More control
const { data: user } = await useAsyncData(
  'user-123', // Unique key for caching
  async () => {
    const response = await fetch('/api/users/123')
    return response.json()
  },
  {
    server: true, // Fetch on server
    lazy: false, // Don't block navigation
    default: () => null // Default value while loading
  }
)

// useLazyFetch - Non-blocking
const { data: posts } = await useLazyFetch('/api/posts')

// useLazyAsyncData - Non-blocking with custom fetcher
const { data: comments } = await useLazyAsyncData('comments', () =>
  $fetch('/api/comments')
)

// Manual refresh
function handleRefresh() {
  refresh() // Re-fetch data
}
</script>

<template>
  <div>
    <div v-if="pending">Loading...</div>
    <div v-else-if="error">Error: {{ error.message }}</div>
    <div v-else>
      <div v-for="user in users" :key="user.id">
        {{ user.name }}
      </div>
      <button @click="handleRefresh">Refresh</button>
    </div>
  </div>
</template>
```

## Server API Routes

```typescript
// server/api/users.get.ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const page = Number(query.page) || 1
  const limit = Number(query.limit) || 10

  // Fetch from database
  const users = await prisma.user.findMany({
    skip: (page - 1) * limit,
    take: limit
  })

  return users
})

// server/api/users/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id')

  const user = await prisma.user.findUnique({
    where: { id: Number(id) }
  })

  if (!user) {
    throw createError({
      statusCode: 404,
      message: 'User not found'
    })
  }

  return user
})

// server/api/users.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event)

  // Validate
  if (!body.email || !body.name) {
    throw createError({
      statusCode: 400,
      message: 'Email and name are required'
    })
  }

  const user = await prisma.user.create({
    data: {
      email: body.email,
      name: body.name
    }
  })

  return user
})

// server/api/auth/login.post.ts
export default defineEventHandler(async (event) => {
  const { email, password } = await readBody(event)

  // Verify credentials
  const user = await verifyCredentials(email, password)

  if (!user) {
    throw createError({
      statusCode: 401,
      message: 'Invalid credentials'
    })
  }

  // Set session cookie
  setCookie(event, 'session', user.sessionToken, {
    httpOnly: true,
    secure: true,
    sameSite: 'strict',
    maxAge: 60 * 60 * 24 * 7 // 7 days
  })

  return { success: true, user }
})
```

## Middleware

```typescript
// middleware/auth.ts - Route middleware
export default defineNuxtRouteMiddleware((to, from) => {
  const { isLoggedIn } = useAuthStore()

  if (!isLoggedIn) {
    return navigateTo('/login')
  }
})

// middleware/logger.global.ts - Global middleware
export default defineNuxtRouteMiddleware((to, from) => {
  console.log(`Navigating from ${from.path} to ${to.path}`)
})

// server/middleware/log.ts - Server middleware
export default defineEventHandler((event) => {
  console.log(`[${event.method}] ${event.path}`)
})
```

## Composables

```typescript
// composables/useAuth.ts - Auto-imported
export const useAuth = () => {
  const user = useState<User | null>('user', () => null)
  const isLoggedIn = computed(() => user.value !== null)

  async function login(email: string, password: string) {
    const { data, error } = await useFetch('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    })

    if (data.value) {
      user.value = data.value.user
    }

    return { data, error }
  }

  async function logout() {
    await useFetch('/api/auth/logout', { method: 'POST' })
    user.value = null
    navigateTo('/login')
  }

  async function fetchUser() {
    const { data } = await useFetch('/api/auth/me')
    user.value = data.value
  }

  return {
    user,
    isLoggedIn,
    login,
    logout,
    fetchUser
  }
}

// Usage in component (auto-imported)
<script setup lang="ts">
const { user, isLoggedIn, login, logout } = useAuth()
</script>
```

## Plugins

```typescript
// plugins/api.ts
export default defineNuxtPlugin((nuxtApp) => {
  const api = $fetch.create({
    baseURL: '/api',
    onRequest({ options }) {
      // Add auth token
      const token = useCookie('token')
      if (token.value) {
        options.headers = options.headers || {}
        options.headers.Authorization = `Bearer ${token.value}`
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        navigateTo('/login')
      }
    }
  })

  return {
    provide: {
      api
    }
  }
})

// Usage in component
<script setup lang="ts">
const { $api } = useNuxtApp()
const users = await $api('/users')
</script>
```

## Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  devtools: { enabled: true },

  modules: [
    '@pinia/nuxt',
    '@nuxtjs/tailwindcss',
    '@vueuse/nuxt'
  ],

  runtimeConfig: {
    // Server-only (never exposed to client)
    apiSecret: process.env.API_SECRET,

    // Exposed to client
    public: {
      apiBase: process.env.API_BASE || '/api'
    }
  },

  app: {
    head: {
      title: 'My App',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'My amazing site' }
      ],
      link: [
        { rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }
      ]
    }
  },

  css: ['~/assets/css/main.css'],

  typescript: {
    strict: true,
    typeCheck: true
  },

  nitro: {
    preset: 'vercel' // or 'node-server', 'cloudflare', etc.
  }
})
```

## SEO and Meta Tags

```vue
<script setup lang="ts">
const route = useRoute()
const title = computed(() => `User ${route.params.id}`)

useHead({
  title,
  meta: [
    { name: 'description', content: 'User profile page' },
    { property: 'og:title', content: title },
    { property: 'og:description', content: 'User profile' }
  ]
})

// Or use useSeoMeta
useSeoMeta({
  title: 'My Page',
  ogTitle: 'My Page',
  description: 'Page description',
  ogDescription: 'Page description',
  ogImage: 'https://example.com/image.png'
})
</script>
```

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `useFetch()` | Fetch data (SSR-safe) |
| `useAsyncData()` | Custom async operations |
| `useLazyFetch()` | Non-blocking fetch |
| `useState()` | Shared state across components |
| `useRoute()` | Access route params/query |
| `useRouter()` | Navigate programmatically |
| `navigateTo()` | Navigate to route |
| `definePageMeta()` | Page-level metadata |
| `useHead()` | Dynamic meta tags |
| Server routes | `/server/api/*.ts` |
| Auto-imports | Components, composables, utils |
