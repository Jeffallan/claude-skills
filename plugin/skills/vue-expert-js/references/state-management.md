# State Management

---

## Setup

```javascript
// main.js
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

createApp(App).use(createPinia()).mount('#app')
```

---

## Options Store Syntax

```javascript
// stores/counter.js
import { defineStore } from 'pinia'

export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0,
    name: 'Counter'
  }),

  getters: {
    doubleCount: (state) => state.count * 2,
    // Getter with parameter
    countPlusN: (state) => (n) => state.count + n
  },

  actions: {
    increment() {
      this.count++
    },
    /** @param {number} amount */
    incrementBy(amount) {
      this.count += amount
    }
  }
})
```

---

## Setup Store Syntax (Composition API)

```javascript
// stores/user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 */

export const useUserStore = defineStore('user', () => {
  // State
  /** @type {import('vue').Ref<User | null>} */
  const currentUser = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  // Getters
  const isLoggedIn = computed(() => currentUser.value !== null)
  const userName = computed(() => currentUser.value?.name ?? 'Guest')

  // Actions
  async function login(email, password) {
    isLoading.value = true
    error.value = null
    try {
      const res = await fetch('/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      })
      currentUser.value = (await res.json()).user
      return true
    } catch (e) {
      error.value = e.message
      return false
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    currentUser.value = null
  }

  return { currentUser, isLoading, error, isLoggedIn, userName, login, logout }
})
```

---

## Using Stores

```vue
<script setup>
import { useUserStore } from '@/stores/user'
import { storeToRefs } from 'pinia'

const userStore = useUserStore()

// Use storeToRefs for reactive state/getters
const { currentUser, isLoggedIn, isLoading } = storeToRefs(userStore)

// Actions can be destructured directly
const { login, logout } = userStore
</script>

<template>
  <div v-if="isLoading">Loading...</div>
  <div v-else-if="isLoggedIn">
    Welcome, {{ currentUser?.name }}
    <button @click="logout">Logout</button>
  </div>
</template>
```

---

## Store Composition

```javascript
// stores/cart.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useProductsStore } from './products'
import { useUserStore } from './user'

export const useCartStore = defineStore('cart', () => {
  const items = ref([]) // [{ productId, quantity }]

  // Access other stores
  const productsStore = useProductsStore()
  const userStore = useUserStore()

  const total = computed(() =>
    items.value.reduce((sum, item) => {
      const product = productsStore.items.find(p => p.id === item.productId)
      return sum + (product?.price ?? 0) * item.quantity
    }, 0)
  )

  function addItem(productId, quantity = 1) {
    const existing = items.value.find(i => i.productId === productId)
    if (existing) existing.quantity += quantity
    else items.value.push({ productId, quantity })
  }

  async function checkout() {
    if (!userStore.isLoggedIn) throw new Error('Must be logged in')
    await fetch('/api/checkout', {
      method: 'POST',
      body: JSON.stringify({ userId: userStore.currentUser.id, items: items.value })
    })
    items.value = []
  }

  return { items, total, addItem, checkout }
})
```

---

## Persistence

```javascript
// stores/settings.js
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'app-settings'

function loadFromStorage() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? {}
  } catch {
    return {}
  }
}

export const useSettingsStore = defineStore('settings', () => {
  const saved = loadFromStorage()

  const theme = ref(saved.theme ?? 'light')
  const language = ref(saved.language ?? 'en')

  watch([theme, language], () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({
      theme: theme.value,
      language: language.value
    }))
  })

  return { theme, language }
})
```

---

## Testing Stores

```javascript
// stores/__tests__/counter.test.js
import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCounterStore } from '../counter'

describe('Counter Store', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('increments count', () => {
    const store = useCounterStore()
    store.increment()
    expect(store.count).toBe(1)
  })

  it('computes double count', () => {
    const store = useCounterStore()
    store.count = 5
    expect(store.doubleCount).toBe(10)
  })
})
```

---

## Quick Reference

| Feature | Options Syntax | Setup Syntax |
|---------|---------------|--------------|
| State | `state: () => ({})` | `const x = ref()` |
| Getter | `getters: { x: (state) => }` | `const x = computed()` |
| Action | `actions: { fn() {} }` | `function fn() {}` |
| Use in component | `storeToRefs()` for state | Same |
| Reset state | `store.$reset()` | Manual reset function |
| Subscribe | `store.$subscribe((mutation, state) => {})` | Same |
| Other stores | Use in actions | Call at setup top level |
