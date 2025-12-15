# State Management with Pinia

> Reference for: Vue Expert
> Load when: Pinia stores, actions, getters, state management

## Basic Store Setup

```typescript
// stores/counter.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

// Setup Stores (Composition API style) - RECOMMENDED
export const useCounterStore = defineStore('counter', () => {
  // State
  const count = ref(0)
  const name = ref('Counter')

  // Getters (computed)
  const doubleCount = computed(() => count.value * 2)
  const isEven = computed(() => count.value % 2 === 0)

  // Actions
  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  function reset() {
    count.value = 0
  }

  async function incrementAsync() {
    await new Promise(resolve => setTimeout(resolve, 1000))
    count.value++
  }

  return {
    // State
    count,
    name,
    // Getters
    doubleCount,
    isEven,
    // Actions
    increment,
    decrement,
    reset,
    incrementAsync
  }
})

// Usage in component
<script setup lang="ts">
import { useCounterStore } from '@/stores/counter'
import { storeToRefs } from 'pinia'

const counter = useCounterStore()

// Use storeToRefs to maintain reactivity when destructuring
const { count, doubleCount, isEven } = storeToRefs(counter)

// Actions can be destructured directly (they don't need refs)
const { increment, decrement } = counter
</script>

<template>
  <div>
    <p>Count: {{ count }}</p>
    <p>Double: {{ doubleCount }}</p>
    <p>Is Even: {{ isEven }}</p>
    <button @click="increment">+</button>
    <button @click="decrement">-</button>
  </div>
</template>
```

## Options Store (Alternative Style)

```typescript
// stores/user.ts
import { defineStore } from 'pinia'

interface User {
  id: number
  name: string
  email: string
}

interface UserState {
  user: User | null
  users: User[]
  loading: boolean
}

export const useUserStore = defineStore('user', {
  // State
  state: (): UserState => ({
    user: null,
    users: [],
    loading: false
  }),

  // Getters
  getters: {
    isLoggedIn: (state) => state.user !== null,
    userCount: (state) => state.users.length,

    // Getter with parameters
    getUserById: (state) => {
      return (userId: number) => state.users.find(u => u.id === userId)
    },

    // Getter accessing other getters
    activeUserCount(): number {
      return this.users.filter(u => u.isActive).length
    }
  },

  // Actions
  actions: {
    async fetchUsers() {
      this.loading = true
      try {
        const response = await fetch('/api/users')
        this.users = await response.json()
      } catch (error) {
        console.error('Failed to fetch users:', error)
      } finally {
        this.loading = false
      }
    },

    async login(email: string, password: string) {
      this.loading = true
      try {
        const response = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        })
        this.user = await response.json()
      } catch (error) {
        console.error('Login failed:', error)
        throw error
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.user = null
    },

    // Action calling another action
    async refreshUserData() {
      if (this.user) {
        await this.fetchUsers()
      }
    }
  }
})
```

## Store with TypeScript

```typescript
// stores/todos.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface Todo {
  id: number
  title: string
  completed: boolean
  createdAt: Date
}

type TodoFilter = 'all' | 'active' | 'completed'

export const useTodoStore = defineStore('todos', () => {
  // State
  const todos = ref<Todo[]>([])
  const filter = ref<TodoFilter>('all')
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const filteredTodos = computed(() => {
    switch (filter.value) {
      case 'active':
        return todos.value.filter(t => !t.completed)
      case 'completed':
        return todos.value.filter(t => t.completed)
      default:
        return todos.value
    }
  })

  const completedCount = computed(() =>
    todos.value.filter(t => t.completed).length
  )

  const activeCount = computed(() =>
    todos.value.filter(t => !t.completed).length
  )

  // Actions
  async function fetchTodos() {
    loading.value = true
    error.value = null
    try {
      const response = await fetch('/api/todos')
      if (!response.ok) throw new Error('Failed to fetch todos')
      todos.value = await response.json()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    } finally {
      loading.value = false
    }
  }

  function addTodo(title: string) {
    const newTodo: Todo = {
      id: Date.now(),
      title,
      completed: false,
      createdAt: new Date()
    }
    todos.value.push(newTodo)
  }

  function toggleTodo(id: number) {
    const todo = todos.value.find(t => t.id === id)
    if (todo) {
      todo.completed = !todo.completed
    }
  }

  function deleteTodo(id: number) {
    const index = todos.value.findIndex(t => t.id === id)
    if (index > -1) {
      todos.value.splice(index, 1)
    }
  }

  function setFilter(newFilter: TodoFilter) {
    filter.value = newFilter
  }

  function clearCompleted() {
    todos.value = todos.value.filter(t => !t.completed)
  }

  return {
    // State
    todos,
    filter,
    loading,
    error,
    // Getters
    filteredTodos,
    completedCount,
    activeCount,
    // Actions
    fetchTodos,
    addTodo,
    toggleTodo,
    deleteTodo,
    setFilter,
    clearCompleted
  }
})
```

## Accessing Other Stores

```typescript
// stores/cart.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useUserStore } from './user'
import { useProductStore } from './product'

interface CartItem {
  productId: number
  quantity: number
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])

  const userStore = useUserStore()
  const productStore = useProductStore()

  const total = computed(() => {
    return items.value.reduce((sum, item) => {
      const product = productStore.getProductById(item.productId)
      return sum + (product?.price || 0) * item.quantity
    }, 0)
  })

  function addItem(productId: number, quantity = 1) {
    const existingItem = items.value.find(i => i.productId === productId)
    if (existingItem) {
      existingItem.quantity += quantity
    } else {
      items.value.push({ productId, quantity })
    }
  }

  async function checkout() {
    if (!userStore.isLoggedIn) {
      throw new Error('User must be logged in to checkout')
    }

    // Checkout logic
    const order = {
      userId: userStore.user?.id,
      items: items.value,
      total: total.value
    }

    // Make API call
    await fetch('/api/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order)
    })

    items.value = []
  }

  return { items, total, addItem, checkout }
})
```

## Store Plugins

```typescript
// plugins/pinia-logger.ts
import { PiniaPluginContext } from 'pinia'

export function piniaLogger({ store }: PiniaPluginContext) {
  store.$subscribe((mutation, state) => {
    console.log(`[${store.$id}]:`, mutation.type, mutation.payload)
    console.log('New state:', state)
  })
}

// main.ts
import { createPinia } from 'pinia'
import { piniaLogger } from './plugins/pinia-logger'

const pinia = createPinia()
pinia.use(piniaLogger)

app.use(pinia)
```

## Persistence Plugin

```typescript
// Install: npm install pinia-plugin-persistedstate

// main.ts
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)

// stores/settings.ts
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<'light' | 'dark'>('light')
  const language = ref('en')

  function setTheme(newTheme: 'light' | 'dark') {
    theme.value = newTheme
  }

  return { theme, language, setTheme }
}, {
  persist: true // Auto-persist to localStorage
})

// Advanced persistence
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)

  return { token, user }
}, {
  persist: {
    key: 'auth-storage',
    storage: sessionStorage,
    paths: ['token'] // Only persist token, not user
  }
})
```

## Store Testing

```typescript
// stores/__tests__/counter.spec.ts
import { setActivePinia, createPinia } from 'pinia'
import { describe, it, expect, beforeEach } from 'vitest'
import { useCounterStore } from '../counter'

describe('Counter Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('increments count', () => {
    const counter = useCounterStore()
    expect(counter.count).toBe(0)
    counter.increment()
    expect(counter.count).toBe(1)
  })

  it('doubles count', () => {
    const counter = useCounterStore()
    counter.count = 5
    expect(counter.doubleCount).toBe(10)
  })

  it('resets count', () => {
    const counter = useCounterStore()
    counter.count = 10
    counter.reset()
    expect(counter.count).toBe(0)
  })
})
```

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| Setup stores | Composition API style (recommended) |
| Options stores | Traditional Vuex-like syntax |
| `storeToRefs()` | Maintain reactivity when destructuring |
| `store.$subscribe()` | Watch for state changes |
| `store.$patch()` | Batch state updates |
| `store.$reset()` | Reset state to initial |
| Plugins | Add global functionality (logger, persistence) |
| Accessing stores | Use other stores in actions |
| Testing | Use `setActivePinia()` for isolated tests |
