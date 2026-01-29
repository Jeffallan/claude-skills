# Component Architecture

---

## Props

```vue
<script setup>
/**
 * @typedef {Object} Props
 * @property {string} title - Required
 * @property {string} [subtitle] - Optional
 * @property {number} [count=0] - With default
 */

const props = defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: '' },
  count: { type: Number, default: 0 },
  // Complex types
  items: { type: Array, default: () => [] },
  user: { type: Object, required: true },
  // Validator
  size: {
    type: String,
    default: 'medium',
    validator: (v) => ['small', 'medium', 'large'].includes(v)
  }
})
</script>
```

---

## Emits

```vue
<script setup>
const emit = defineEmits(['update', 'delete', 'close'])

// With validation
const emit = defineEmits({
  /** @param {string} value */
  update: (value) => typeof value === 'string',
  /** @param {{ id: number }} payload */
  delete: (payload) => typeof payload?.id === 'number',
  close: null
})

// Usage
emit('update', 'new value')
emit('delete', { id: 1 })
</script>
```

---

## v-model

```vue
<!-- Single v-model -->
<script setup>
const props = defineProps({ modelValue: { type: String, required: true } })
const emit = defineEmits(['update:modelValue'])
</script>

<template>
  <input :value="modelValue" @input="emit('update:modelValue', $event.target.value)" />
</template>
```

```vue
<!-- Multiple v-models: v-model:firstName, v-model:lastName -->
<script setup>
defineProps({ firstName: String, lastName: String })
defineEmits(['update:firstName', 'update:lastName'])
</script>
```

---

## Slots

```vue
<!-- Card.vue -->
<template>
  <div class="card">
    <header v-if="$slots.header"><slot name="header" /></header>
    <div class="card-body"><slot /></div>
    <footer v-if="$slots.footer"><slot name="footer" /></footer>
  </div>
</template>
```

```vue
<!-- Scoped slot -->
<template>
  <ul>
    <li v-for="(item, index) in items" :key="item.id">
      <slot name="item" :item="item" :index="index">
        {{ item.name }}
      </slot>
    </li>
  </ul>
</template>

<!-- Usage -->
<DataList :items="users">
  <template #item="{ item, index }">
    {{ index + 1 }}. {{ item.name }}
  </template>
</DataList>
```

---

## Provide / Inject

```vue
<!-- Provider.vue -->
<script setup>
import { provide, ref, readonly } from 'vue'

const theme = ref('light')
provide('theme', readonly(theme))
provide('setTheme', (t) => { theme.value = t })
</script>
```

```vue
<!-- Consumer.vue -->
<script setup>
import { inject, ref } from 'vue'

const theme = inject('theme', ref('light'))
const setTheme = inject('setTheme', () => {})
</script>
```

```javascript
// Composable pattern
// composables/useTheme.js
import { ref, provide, inject, readonly, computed } from 'vue'

const ThemeSymbol = Symbol('theme')

export function provideTheme(initial = 'light') {
  const theme = ref(initial)
  const isDark = computed(() => theme.value === 'dark')
  const toggle = () => { theme.value = theme.value === 'light' ? 'dark' : 'light' }

  provide(ThemeSymbol, { theme: readonly(theme), isDark, toggle })
  return { theme, isDark, toggle }
}

export function useTheme() {
  const ctx = inject(ThemeSymbol)
  if (!ctx) throw new Error('useTheme requires ThemeProvider')
  return ctx
}
```

---

## Dynamic Components

```vue
<script setup>
import { shallowRef, markRaw } from 'vue'
import TabHome from './TabHome.vue'
import TabProfile from './TabProfile.vue'

const tabs = [
  { name: 'Home', component: markRaw(TabHome) },
  { name: 'Profile', component: markRaw(TabProfile) }
]

const currentTab = shallowRef(tabs[0].component)
</script>

<template>
  <button v-for="tab in tabs" :key="tab.name" @click="currentTab = tab.component">
    {{ tab.name }}
  </button>
  <KeepAlive>
    <component :is="currentTab" />
  </KeepAlive>
</template>
```

```javascript
// Async component
import { defineAsyncComponent } from 'vue'

const AsyncModal = defineAsyncComponent({
  loader: () => import('./Modal.vue'),
  delay: 200,
  timeout: 10000
})
```

---

## Quick Reference

| Feature | Syntax |
|---------|--------|
| Required prop | `{ type: String, required: true }` |
| Default prop | `{ type: Number, default: 0 }` |
| Array/Object default | `{ type: Array, default: () => [] }` |
| Emit event | `emit('eventName', payload)` |
| v-model | `modelValue` prop + `update:modelValue` emit |
| Named v-model | `v-model:name` → `name` prop + `update:name` emit |
| Default slot | `<slot />` |
| Named slot | `<slot name="header" />` → `#header` |
| Scoped slot | `<slot :item="item" />` → `#default="{ item }"` |
| Provide | `provide('key', value)` |
| Inject | `inject('key', defaultValue)` |
| Dynamic component | `<component :is="comp" />` |
