# Composables Patterns

---

## Basic Composable Structure

```javascript
// composables/useToggle.js
import { ref } from 'vue'

/**
 * @typedef {Object} UseToggleReturn
 * @property {import('vue').Ref<boolean>} value
 * @property {() => void} toggle
 */

/**
 * @param {boolean} [initialValue=false]
 * @returns {UseToggleReturn}
 */
export function useToggle(initialValue = false) {
  const value = ref(initialValue)
  const toggle = () => { value.value = !value.value }
  return { value, toggle }
}
```

---

## Ref vs Reactive

```javascript
import { ref, reactive, toRefs, toValue } from 'vue'

// Use ref for: primitives, reassignable values, composable returns
/** @type {import('vue').Ref<number>} */
const count = ref(0)

// Use reactive for: complex objects with nested properties
/** @type {{ email: string, password: string }} */
const form = reactive({ email: '', password: '' })

// Convert reactive to refs for destructuring
const { email, password } = toRefs(form)

// Unwrap ref or return plain value
/** @param {number | import('vue').Ref<number>} maybeRef */
function double(maybeRef) {
  return toValue(maybeRef) * 2
}
```

---

## Lifecycle Hooks

```javascript
// composables/useEventListener.js
import { onMounted, onUnmounted, toValue } from 'vue'

/**
 * @template {keyof WindowEventMap} K
 * @param {K} event
 * @param {(ev: WindowEventMap[K]) => void} handler
 * @param {EventTarget | import('vue').Ref<EventTarget>} [target=window]
 */
export function useEventListener(event, handler, target = window) {
  onMounted(() => toValue(target).addEventListener(event, handler))
  onUnmounted(() => toValue(target).removeEventListener(event, handler))
}
```

```javascript
// Lifecycle-aware async (prevents state updates after unmount)
import { ref, onUnmounted } from 'vue'

export function useAsyncState(fn) {
  const data = ref(null)
  const loading = ref(false)
  let isMounted = true

  onUnmounted(() => { isMounted = false })

  async function execute() {
    loading.value = true
    try {
      const result = await fn()
      if (isMounted) data.value = result
    } finally {
      if (isMounted) loading.value = false
    }
  }

  return { data, loading, execute }
}
```

---

## Shared State (Singleton)

```javascript
// composables/useNotifications.js
import { ref, readonly } from 'vue'

// Module-level state = singleton shared across all components
/** @type {import('vue').Ref<Array<{id: string, message: string}>>} */
const notifications = ref([])

export function useNotifications() {
  /** @param {string} message */
  function notify(message) {
    const id = Date.now().toString()
    notifications.value.push({ id, message })
    setTimeout(() => dismiss(id), 5000)
  }

  /** @param {string} id */
  function dismiss(id) {
    notifications.value = notifications.value.filter(n => n.id !== id)
  }

  return {
    notifications: readonly(notifications),
    notify,
    dismiss
  }
}
```

---

## Async with Cancellation

```javascript
// composables/useCancellableFetch.js
import { ref, onUnmounted } from 'vue'

export function useCancellableFetch() {
  const data = ref(null)
  const error = ref(null)
  const loading = ref(false)
  /** @type {AbortController | null} */
  let controller = null

  /** @param {string} url */
  async function execute(url) {
    controller?.abort()
    controller = new AbortController()
    loading.value = true
    error.value = null

    try {
      const res = await fetch(url, { signal: controller.signal })
      data.value = await res.json()
    } catch (e) {
      if (/** @type {Error} */ (e).name !== 'AbortError') {
        error.value = /** @type {Error} */ (e)
      }
    } finally {
      loading.value = false
    }
  }

  onUnmounted(() => controller?.abort())

  return { data, error, loading, execute }
}
```

---

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `ref()` | Primitives, values passed to/from composables |
| `reactive()` | Objects with nested reactivity |
| `toRefs()` | Destructure reactive while keeping reactivity |
| `toValue()` | Unwrap ref or return plain value |
| Module-level ref | Singleton shared state |
| Factory function | New instance per component |
| `onUnmounted` | Cleanup timers, listeners, abort controllers |
