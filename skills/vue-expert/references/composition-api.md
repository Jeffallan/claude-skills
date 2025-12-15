# Composition API

> Reference for: Vue Expert
> Load when: Using ref, reactive, computed, watch, lifecycle hooks

## Script Setup Syntax

```vue
<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'

// Automatic component registration - no need to register in components option
import UserCard from './UserCard.vue'

// Props with TypeScript
interface Props {
  userId: number
  optional?: string
}
const props = withDefaults(defineProps<Props>(), {
  optional: 'default value'
})

// Emits with TypeScript
interface Emits {
  (e: 'update', value: string): void
  (e: 'delete', id: number): void
}
const emit = defineEmits<Emits>()

// Reactive state
const count = ref(0)
const user = reactive({
  name: 'John',
  age: 30
})

// Computed
const doubled = computed(() => count.value * 2)

// Methods
function increment() {
  count.value++
  emit('update', count.value.toString())
}

// Lifecycle
onMounted(() => {
  console.log('Component mounted')
})
</script>
```

## Ref vs Reactive

```typescript
import { ref, reactive, toRefs } from 'vue'

// Use ref() for primitives
const count = ref(0)
const message = ref('hello')
const isActive = ref(true)

// Access/modify with .value
count.value++
console.log(message.value)

// Use reactive() for objects
const state = reactive({
  count: 0,
  user: {
    name: 'John',
    email: 'john@example.com'
  }
})

// No .value needed for reactive
state.count++
state.user.name = 'Jane'

// Convert reactive to refs for destructuring
const { count: refCount, user } = toRefs(state)
// Now refCount.value works
```

## Computed Properties

```typescript
import { ref, computed } from 'vue'

const firstName = ref('John')
const lastName = ref('Doe')

// Read-only computed
const fullName = computed(() => {
  return `${firstName.value} ${lastName.value}`
})

// Writable computed
const fullNameWritable = computed({
  get() {
    return `${firstName.value} ${lastName.value}`
  },
  set(value: string) {
    const [first, last] = value.split(' ')
    firstName.value = first
    lastName.value = last
  }
})

// Computed with complex logic (cached until dependencies change)
const filteredItems = computed(() => {
  return items.value.filter(item =>
    item.name.toLowerCase().includes(searchQuery.value.toLowerCase())
  )
})
```

## Watchers

```typescript
import { ref, watch, watchEffect } from 'vue'

const count = ref(0)
const user = ref({ name: 'John', age: 30 })

// Watch single source
watch(count, (newValue, oldValue) => {
  console.log(`Count changed from ${oldValue} to ${newValue}`)
})

// Watch multiple sources
watch([count, user], ([newCount, newUser], [oldCount, oldUser]) => {
  console.log('Count or user changed')
})

// Watch with options
watch(
  () => user.value.name, // Getter function
  (newName) => {
    console.log(`Name changed to ${newName}`)
  },
  {
    immediate: true, // Run immediately
    deep: true // Deep watch for objects
  }
)

// watchEffect - automatically tracks dependencies
watchEffect(() => {
  console.log(`Count is ${count.value}`)
  // Automatically re-runs when count changes
})

// Cleanup and stop watching
const stop = watchEffect((onCleanup) => {
  const timer = setInterval(() => console.log('tick'), 1000)

  onCleanup(() => {
    clearInterval(timer)
  })
})

// Stop watching when needed
stop()
```

## Lifecycle Hooks

```typescript
import {
  onBeforeMount,
  onMounted,
  onBeforeUpdate,
  onUpdated,
  onBeforeUnmount,
  onUnmounted,
  onErrorCaptured
} from 'vue'

// Before component is mounted
onBeforeMount(() => {
  console.log('Before mount')
})

// After component is mounted (DOM is ready)
onMounted(() => {
  console.log('Mounted - DOM is ready')
  // Fetch data, setup event listeners, etc.
})

// Before component updates
onBeforeUpdate(() => {
  console.log('Before update')
})

// After component updates
onUpdated(() => {
  console.log('Updated')
})

// Before component is unmounted
onBeforeUnmount(() => {
  console.log('Before unmount - cleanup here')
})

// After component is unmounted
onUnmounted(() => {
  console.log('Unmounted')
  // Cleanup: remove event listeners, cancel timers, etc.
})

// Error handling
onErrorCaptured((err, instance, info) => {
  console.error('Error captured:', err, info)
  return false // Prevent error from propagating
})
```

## Composables Pattern

```typescript
// composables/useCounter.ts
import { ref, computed } from 'vue'

export function useCounter(initialValue = 0) {
  const count = ref(initialValue)
  const doubled = computed(() => count.value * 2)

  function increment() {
    count.value++
  }

  function decrement() {
    count.value--
  }

  function reset() {
    count.value = initialValue
  }

  return {
    count,
    doubled,
    increment,
    decrement,
    reset
  }
}

// Usage in component
<script setup lang="ts">
import { useCounter } from './composables/useCounter'

const { count, doubled, increment, decrement } = useCounter(10)
</script>
```

## Advanced Composable with Cleanup

```typescript
// composables/useEventListener.ts
import { onMounted, onUnmounted } from 'vue'

export function useEventListener(
  target: EventTarget,
  event: string,
  handler: EventListener
) {
  onMounted(() => {
    target.addEventListener(event, handler)
  })

  onUnmounted(() => {
    target.removeEventListener(event, handler)
  })
}

// Usage
<script setup lang="ts">
import { useEventListener } from './composables/useEventListener'

function handleClick(e: MouseEvent) {
  console.log('Clicked at:', e.clientX, e.clientY)
}

useEventListener(window, 'click', handleClick)
</script>
```

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `ref()` | Primitives (string, number, boolean) |
| `reactive()` | Objects and arrays |
| `computed()` | Derived state (cached) |
| `watch()` | Side effects on specific changes |
| `watchEffect()` | Auto-tracked side effects |
| `onMounted()` | DOM-dependent operations |
| `onUnmounted()` | Cleanup (timers, listeners) |
| Composables | Reusable stateful logic |
