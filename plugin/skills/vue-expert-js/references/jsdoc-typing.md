# JSDoc Typing for Vue

---

## Basic JSDoc with Vue

### Typing Refs

```vue
<script setup>
import { ref, computed } from 'vue'

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {boolean} [isActive] - Optional property
 */

/** @type {import('vue').Ref<User | null>} */
const user = ref(null)

/** @type {import('vue').Ref<User[]>} */
const users = ref([])

/** @type {import('vue').Ref<string>} */
const searchQuery = ref('')

/** @type {import('vue').Ref<number>} */
const count = ref(0)
</script>
```

### Typing Computed

```vue
<script setup>
import { ref, computed } from 'vue'

/** @type {import('vue').Ref<User | null>} */
const user = ref(null)

/** @type {import('vue').ComputedRef<string>} */
const userName = computed(() => user.value?.name ?? 'Anonymous')

/** @type {import('vue').ComputedRef<boolean>} */
const isLoggedIn = computed(() => user.value !== null)

/** @type {import('vue').ComputedRef<User[]>} */
const activeUsers = computed(() =>
  users.value.filter(u => u.isActive)
)
</script>
```

### Typing Reactive

```vue
<script setup>
import { reactive } from 'vue'

/**
 * @typedef {Object} FormState
 * @property {string} email
 * @property {string} password
 * @property {boolean} rememberMe
 * @property {string[]} errors
 */

/** @type {FormState} */
const form = reactive({
  email: '',
  password: '',
  rememberMe: false,
  errors: []
})
</script>
```

---

## Props with JSDoc

### Basic Props

```vue
<script setup>
/**
 * @typedef {Object} Props
 * @property {string} title - The card title
 * @property {string} [subtitle] - Optional subtitle
 * @property {number} [count=0] - Counter with default value
 * @property {boolean} [disabled=false] - Disabled state
 */

/** @type {Props} */
const props = defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  count: {
    type: Number,
    default: 0
  },
  disabled: {
    type: Boolean,
    default: false
  }
})
</script>
```

### Complex Props

```vue
<script setup>
/**
 * @typedef {Object} MenuItem
 * @property {string} id
 * @property {string} label
 * @property {string} [icon]
 * @property {MenuItem[]} [children]
 */

/**
 * @typedef {'primary' | 'secondary' | 'danger'} ButtonVariant
 */

/**
 * @typedef {Object} Props
 * @property {MenuItem[]} items - Menu items
 * @property {ButtonVariant} [variant='primary'] - Button style
 * @property {(item: MenuItem) => void} [onSelect] - Selection callback
 */

const props = defineProps({
  items: {
    type: Array,
    required: true,
    /** @param {MenuItem[]} value */
    validator: (value) => value.every(item => item.id && item.label)
  },
  variant: {
    type: String,
    default: 'primary',
    /** @param {string} value */
    validator: (value) => ['primary', 'secondary', 'danger'].includes(value)
  },
  onSelect: {
    type: Function,
    default: null
  }
})
</script>
```

---

## Emits with JSDoc

### Basic Emits

```vue
<script setup>
/**
 * @typedef {Object} Emits
 * @property {(value: string) => void} update - Emitted on value change
 * @property {(id: number) => void} delete - Emitted on delete
 * @property {() => void} close - Emitted on close
 */

const emit = defineEmits(['update', 'delete', 'close'])

/**
 * Handle input change
 * @param {string} value - The new value
 */
function handleChange(value) {
  emit('update', value)
}

/**
 * Handle delete action
 * @param {number} id - The item ID to delete
 */
function handleDelete(id) {
  emit('delete', id)
}

function handleClose() {
  emit('close')
}
</script>
```

### With Validation

```vue
<script setup>
const emit = defineEmits({
  /**
   * @param {string} value
   * @returns {boolean}
   */
  update: (value) => typeof value === 'string',

  /**
   * @param {{ id: number, reason: string }} payload
   * @returns {boolean}
   */
  delete: (payload) => typeof payload.id === 'number'
})
</script>
```

---

## Composables with JSDoc

### Basic Composable

```javascript
// composables/useCounter.js
import { ref, computed } from 'vue'

/**
 * @typedef {Object} UseCounterReturn
 * @property {import('vue').Ref<number>} count - Current count
 * @property {import('vue').ComputedRef<number>} doubled - Doubled value
 * @property {() => void} increment - Increment count
 * @property {() => void} decrement - Decrement count
 * @property {(value: number) => void} set - Set count to value
 */

/**
 * Counter composable with increment/decrement
 * @param {number} [initialValue=0] - Starting value
 * @returns {UseCounterReturn}
 */
export function useCounter(initialValue = 0) {
  /** @type {import('vue').Ref<number>} */
  const count = ref(initialValue)

  const doubled = computed(() => count.value * 2)

  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  /**
   * @param {number} value
   */
  function set(value) {
    count.value = value
  }

  return { count, doubled, increment, decrement, set }
}
```

### Async Composable

```javascript
// composables/useFetch.js
import { ref, watchEffect, toValue } from 'vue'

/**
 * @template T
 * @typedef {Object} UseFetchReturn
 * @property {import('vue').Ref<T | null>} data - Fetched data
 * @property {import('vue').Ref<Error | null>} error - Error if any
 * @property {import('vue').Ref<boolean>} loading - Loading state
 * @property {() => Promise<void>} refresh - Refetch data
 */

/**
 * Composable for fetching data
 * @template T
 * @param {string | import('vue').Ref<string>} url - URL to fetch
 * @param {RequestInit} [options] - Fetch options
 * @returns {UseFetchReturn<T>}
 */
export function useFetch(url, options = {}) {
  /** @type {import('vue').Ref<T | null>} */
  const data = ref(null)

  /** @type {import('vue').Ref<Error | null>} */
  const error = ref(null)

  /** @type {import('vue').Ref<boolean>} */
  const loading = ref(false)

  async function refresh() {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(toValue(url), options)
      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`)
      }
      data.value = await response.json()
    } catch (e) {
      error.value = /** @type {Error} */ (e)
    } finally {
      loading.value = false
    }
  }

  watchEffect(() => {
    refresh()
  })

  return { data, error, loading, refresh }
}
```

### Composable with Options

```javascript
// composables/useLocalStorage.js
import { ref, watch } from 'vue'

/**
 * @template T
 * @typedef {Object} UseLocalStorageOptions
 * @property {(value: T) => string} [serialize] - Custom serializer
 * @property {(value: string) => T} [deserialize] - Custom deserializer
 */

/**
 * Reactive localStorage composable
 * @template T
 * @param {string} key - Storage key
 * @param {T} defaultValue - Default value if key not found
 * @param {UseLocalStorageOptions<T>} [options] - Options
 * @returns {import('vue').Ref<T>}
 */
export function useLocalStorage(key, defaultValue, options = {}) {
  const serialize = options.serialize ?? JSON.stringify
  const deserialize = options.deserialize ?? JSON.parse

  /** @type {import('vue').Ref<T>} */
  const data = ref(defaultValue)

  // Load from storage
  const stored = localStorage.getItem(key)
  if (stored) {
    try {
      data.value = deserialize(stored)
    } catch {
      data.value = defaultValue
    }
  }

  // Persist on change
  watch(data, (value) => {
    localStorage.setItem(key, serialize(value))
  }, { deep: true })

  return data
}
```

---

## Type Imports and Shared Types

### Shared Type Definitions

```javascript
// types.js - Shared type definitions
/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} name
 * @property {string} email
 * @property {UserRole} role
 */

/**
 * @typedef {'admin' | 'user' | 'guest'} UserRole
 */

/**
 * @typedef {Object} Post
 * @property {number} id
 * @property {string} title
 * @property {string} content
 * @property {User} author
 * @property {string} createdAt
 */

/**
 * @typedef {Object} PaginatedResponse
 * @template T
 * @property {T[]} data
 * @property {number} total
 * @property {number} page
 * @property {number} pageSize
 */

// Export empty object for IDE import support
export const Types = {}
```

### Importing Types

```vue
<script setup>
/** @typedef {import('./types.js').User} User */
/** @typedef {import('./types.js').Post} Post */

import { ref } from 'vue'

/** @type {import('vue').Ref<User | null>} */
const currentUser = ref(null)

/** @type {import('vue').Ref<Post[]>} */
const posts = ref([])
</script>
```

### Global Type Definitions

```javascript
// types/global.d.js (for IDE support)
/**
 * @typedef {Object} ApiResponse
 * @template T
 * @property {boolean} success
 * @property {T} [data]
 * @property {string} [error]
 */

/**
 * @typedef {Object} ValidationError
 * @property {string} field
 * @property {string} message
 */
```

---

## Pinia Stores with JSDoc

```javascript
// stores/user.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/** @typedef {import('../types.js').User} User */

/**
 * @typedef {Object} UserStoreState
 * @property {User | null} currentUser
 * @property {boolean} isLoading
 */

export const useUserStore = defineStore('user', () => {
  /** @type {import('vue').Ref<User | null>} */
  const currentUser = ref(null)

  /** @type {import('vue').Ref<boolean>} */
  const isLoading = ref(false)

  const isLoggedIn = computed(() => currentUser.value !== null)
  const userName = computed(() => currentUser.value?.name ?? 'Guest')

  /**
   * Login user
   * @param {string} email
   * @param {string} password
   * @returns {Promise<boolean>}
   */
  async function login(email, password) {
    isLoading.value = true
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      })
      const data = await response.json()
      currentUser.value = data.user
      return true
    } catch {
      return false
    } finally {
      isLoading.value = false
    }
  }

  function logout() {
    currentUser.value = null
  }

  return {
    currentUser,
    isLoading,
    isLoggedIn,
    userName,
    login,
    logout
  }
})
```

---

## Quick Reference

| Pattern | Syntax | Use Case |
|---------|--------|----------|
| `@typedef` | `@typedef {Object} Name` | Define object shapes |
| `@property` | `@property {type} name` | Object properties |
| `@type` | `@type {Type}` | Annotate variables |
| `@param` | `@param {type} name` | Function parameters |
| `@returns` | `@returns {type}` | Function return type |
| `@template` | `@template T` | Generic types |
| Optional | `{type} [name]` | Optional property |
| Default | `{type} [name=value]` | With default value |
| Union | `{type1 \| type2}` | Multiple types |
| Import | `import('./file').Type` | Import from file |
| Vue Ref | `import('vue').Ref<T>` | Typed ref |
| Vue Computed | `import('vue').ComputedRef<T>` | Typed computed |
