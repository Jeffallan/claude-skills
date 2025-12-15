# Components

> Reference for: Vue Expert
> Load when: Props, emits, slots, provide/inject, teleport

## Props with TypeScript

```vue
<script setup lang="ts">
// Simple props
interface Props {
  title: string
  count?: number
  items: string[]
}

const props = defineProps<Props>()

// Props with defaults
const propsWithDefaults = withDefaults(defineProps<Props>(), {
  count: 0,
  items: () => []
})

// Runtime props (without TypeScript)
const runtimeProps = defineProps({
  title: {
    type: String,
    required: true
  },
  count: {
    type: Number,
    default: 0,
    validator: (value: number) => value >= 0
  },
  items: {
    type: Array as PropType<string[]>,
    default: () => []
  }
})

// Access props
console.log(props.title)
console.log(props.count)
</script>

<template>
  <div>
    <h1>{{ title }}</h1>
    <p>Count: {{ count }}</p>
  </div>
</template>
```

## Emits (Events)

```vue
<script setup lang="ts">
// TypeScript emits
interface Emits {
  (e: 'update', value: string): void
  (e: 'delete', id: number): void
  (e: 'submit', payload: { name: string; email: string }): void
}

const emit = defineEmits<Emits>()

// Emit events
function handleUpdate() {
  emit('update', 'new value')
}

function handleDelete(id: number) {
  emit('delete', id)
}

function handleSubmit() {
  emit('submit', { name: 'John', email: 'john@example.com' })
}

// Runtime emits with validation
const runtimeEmit = defineEmits({
  update: (value: string) => {
    return value.length > 0
  },
  delete: (id: number) => {
    return id > 0
  }
})
</script>

<template>
  <button @click="handleUpdate">Update</button>
  <button @click="handleDelete(123)">Delete</button>
</template>
```

## v-model (Two-way Binding)

```vue
<!-- Parent Component -->
<script setup lang="ts">
import { ref } from 'vue'
import CustomInput from './CustomInput.vue'

const searchQuery = ref('')
const filters = ref({ category: '', price: 0 })
</script>

<template>
  <!-- Single v-model -->
  <CustomInput v-model="searchQuery" />

  <!-- Multiple v-models -->
  <FilterPanel
    v-model:category="filters.category"
    v-model:price="filters.price"
  />
</template>

<!-- CustomInput.vue -->
<script setup lang="ts">
interface Props {
  modelValue: string
}

interface Emits {
  (e: 'update:modelValue', value: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}
</script>

<template>
  <input :value="modelValue" @input="handleInput" />
</template>

<!-- FilterPanel.vue with multiple v-models -->
<script setup lang="ts">
interface Props {
  category: string
  price: number
}

interface Emits {
  (e: 'update:category', value: string): void
  (e: 'update:price', value: number): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()
</script>

<template>
  <select
    :value="category"
    @change="emit('update:category', ($event.target as HTMLSelectElement).value)"
  >
    <option value="books">Books</option>
    <option value="electronics">Electronics</option>
  </select>
  <input
    type="number"
    :value="price"
    @input="emit('update:price', Number(($event.target as HTMLInputElement).value))"
  />
</template>
```

## Slots

```vue
<!-- Parent Component -->
<template>
  <Card>
    <template #header>
      <h2>Card Title</h2>
    </template>

    <template #default>
      <p>Main content goes here</p>
    </template>

    <template #footer="{ close }">
      <button @click="close">Close</button>
    </template>
  </Card>
</template>

<!-- Card.vue -->
<script setup lang="ts">
import { useSlots } from 'vue'

const slots = useSlots()

// Check if slot exists
const hasHeader = !!slots.header
const hasFooter = !!slots.footer

function close() {
  console.log('Closing card')
}
</script>

<template>
  <div class="card">
    <div v-if="hasHeader" class="card-header">
      <slot name="header"></slot>
    </div>

    <div class="card-body">
      <slot></slot> <!-- Default slot -->
    </div>

    <div v-if="hasFooter" class="card-footer">
      <slot name="footer" :close="close"></slot> <!-- Scoped slot -->
    </div>
  </div>
</template>
```

## Scoped Slots (Advanced)

```vue
<!-- List Component with Scoped Slot -->
<script setup lang="ts" generic="T">
interface Props {
  items: T[]
}

const props = defineProps<Props>()
</script>

<template>
  <div class="list">
    <div v-for="(item, index) in items" :key="index">
      <slot :item="item" :index="index"></slot>
    </div>
  </div>
</template>

<!-- Usage -->
<template>
  <List :items="users">
    <template #default="{ item, index }">
      <div>{{ index }}: {{ item.name }}</div>
    </template>
  </List>
</template>
```

## Provide/Inject

```vue
<!-- Parent Component (Provider) -->
<script setup lang="ts">
import { provide, ref, readonly, InjectionKey } from 'vue'

// Type-safe injection key
interface UserData {
  name: string
  email: string
}

export const userKey = Symbol() as InjectionKey<UserData>

const user = ref<UserData>({
  name: 'John Doe',
  email: 'john@example.com'
})

function updateUser(newUser: UserData) {
  user.value = newUser
}

// Provide data
provide(userKey, readonly(user.value))
provide('updateUser', updateUser)
</script>

<!-- Child Component (Injector) -->
<script setup lang="ts">
import { inject } from 'vue'
import { userKey } from './Parent.vue'

// Inject with type safety
const user = inject(userKey)
const updateUser = inject<(user: UserData) => void>('updateUser')

// Inject with default value
const theme = inject('theme', 'light')

function handleUpdate() {
  if (updateUser) {
    updateUser({ name: 'Jane', email: 'jane@example.com' })
  }
}
</script>

<template>
  <div>
    <p>User: {{ user?.name }}</p>
    <p>Theme: {{ theme }}</p>
    <button @click="handleUpdate">Update User</button>
  </div>
</template>
```

## Teleport

```vue
<script setup lang="ts">
import { ref } from 'vue'

const showModal = ref(false)
</script>

<template>
  <button @click="showModal = true">Show Modal</button>

  <!-- Teleport to body -->
  <Teleport to="body">
    <div v-if="showModal" class="modal">
      <div class="modal-content">
        <h2>Modal Title</h2>
        <p>Modal content</p>
        <button @click="showModal = false">Close</button>
      </div>
    </div>
  </Teleport>

  <!-- Teleport to specific element -->
  <Teleport to="#modal-container">
    <div class="notification">Notification message</div>
  </Teleport>

  <!-- Conditional teleport -->
  <Teleport to="body" :disabled="!isMobile">
    <div>Only teleported on mobile</div>
  </Teleport>
</template>

<style scoped>
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 8px;
}
</style>
```

## Dynamic Components

```vue
<script setup lang="ts">
import { ref, shallowRef, Component } from 'vue'
import HomeView from './HomeView.vue'
import AboutView from './AboutView.vue'
import ContactView from './ContactView.vue'

// Use shallowRef for component references (performance)
const currentView = shallowRef<Component>(HomeView)

const components = {
  home: HomeView,
  about: AboutView,
  contact: ContactView
}

function switchView(view: keyof typeof components) {
  currentView.value = components[view]
}
</script>

<template>
  <button @click="switchView('home')">Home</button>
  <button @click="switchView('about')">About</button>
  <button @click="switchView('contact')">Contact</button>

  <!-- Dynamic component with KeepAlive -->
  <KeepAlive>
    <component :is="currentView" />
  </KeepAlive>
</template>
```

## Async Components

```vue
<script setup lang="ts">
import { defineAsyncComponent } from 'vue'

// Lazy load component
const HeavyComponent = defineAsyncComponent(() =>
  import('./HeavyComponent.vue')
)

// With loading and error states
const AdminPanel = defineAsyncComponent({
  loader: () => import('./AdminPanel.vue'),
  loadingComponent: () => import('./LoadingSpinner.vue'),
  errorComponent: () => import('./ErrorDisplay.vue'),
  delay: 200, // Delay before showing loading component
  timeout: 3000 // Timeout before showing error
})
</script>

<template>
  <Suspense>
    <template #default>
      <HeavyComponent />
    </template>
    <template #fallback>
      <div>Loading...</div>
    </template>
  </Suspense>
</template>
```

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `defineProps<T>()` | Type-safe props with TypeScript |
| `withDefaults()` | Props with default values |
| `defineEmits<T>()` | Type-safe event emitters |
| `v-model` | Two-way data binding |
| `<slot>` | Content distribution |
| Scoped slots | Pass data from child to parent |
| `provide/inject` | Dependency injection (avoid prop drilling) |
| `<Teleport>` | Render DOM outside component hierarchy |
| `<component :is>` | Dynamic component switching |
| `defineAsyncComponent()` | Lazy load components |
