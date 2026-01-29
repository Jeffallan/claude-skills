# Testing Patterns

---

## Setup

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./vitest.setup.js']
  }
})
```

```javascript
// vitest.setup.js
import { config } from '@vue/test-utils'
import { vi } from 'vitest'

vi.stubGlobal('fetch', vi.fn())

config.global.stubs = {
  'router-link': { template: '<a><slot /></a>' }
}
```

---

## Component Testing Basics

```javascript
// Button.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import Button from './Button.vue'

describe('Button', () => {
  it('renders slot content', () => {
    const wrapper = mount(Button, { slots: { default: 'Click me' } })
    expect(wrapper.text()).toBe('Click me')
  })

  it('applies variant class', () => {
    const wrapper = mount(Button, { props: { variant: 'danger' } })
    expect(wrapper.classes()).toContain('btn--danger')
  })

  it('emits click event', async () => {
    const wrapper = mount(Button)
    await wrapper.trigger('click')
    expect(wrapper.emitted('click')).toHaveLength(1)
  })

  it('is disabled when prop is true', () => {
    const wrapper = mount(Button, { props: { disabled: true } })
    expect(wrapper.attributes('disabled')).toBeDefined()
  })
})
```

---

## Testing v-model

```javascript
// TextInput.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import TextInput from './TextInput.vue'

describe('TextInput', () => {
  it('emits update:modelValue on input', async () => {
    const wrapper = mount(TextInput, { props: { modelValue: '' } })
    await wrapper.find('input').setValue('new value')
    expect(wrapper.emitted('update:modelValue')).toEqual([['new value']])
  })
})
```

---

## Testing Async

```javascript
// UserList.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import UserList from './UserList.vue'

describe('UserList', () => {
  beforeEach(() => vi.resetAllMocks())

  it('renders users after fetch', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ id: 1, name: 'Alice' }])
    })

    const wrapper = mount(UserList)
    await flushPromises()

    expect(wrapper.text()).toContain('Alice')
  })

  it('shows error on failure', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))

    const wrapper = mount(UserList)
    await flushPromises()

    expect(wrapper.find('[data-test="error"]').exists()).toBe(true)
  })
})
```

---

## Mocking Composables

```javascript
// Header.test.js
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref, computed } from 'vue'
import Header from './Header.vue'
import * as useAuthModule from '@/composables/useAuth'

describe('Header', () => {
  it('shows login button when logged out', () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: ref(null),
      isLoggedIn: computed(() => false),
      login: vi.fn(),
      logout: vi.fn()
    })

    const wrapper = mount(Header)
    expect(wrapper.find('[data-test="login-btn"]').exists()).toBe(true)
  })

  it('shows user menu when logged in', () => {
    vi.spyOn(useAuthModule, 'useAuth').mockReturnValue({
      user: ref({ id: 1, name: 'John' }),
      isLoggedIn: computed(() => true),
      login: vi.fn(),
      logout: vi.fn()
    })

    const wrapper = mount(Header)
    expect(wrapper.find('[data-test="user-menu"]').exists()).toBe(true)
  })
})
```

---

## Testing with Pinia

```javascript
// CartSummary.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import CartSummary from './CartSummary.vue'
import { useCartStore } from '@/stores/cart'

describe('CartSummary', () => {
  it('displays cart total', () => {
    const wrapper = mount(CartSummary, {
      global: {
        plugins: [createTestingPinia({
          initialState: {
            cart: { items: [{ productId: 1, quantity: 2, price: 100 }] }
          }
        })]
      }
    })

    expect(wrapper.text()).toContain('$200')
  })

  it('calls checkout action', async () => {
    const wrapper = mount(CartSummary, {
      global: { plugins: [createTestingPinia()] }
    })

    await wrapper.find('[data-test="checkout-btn"]').trigger('click')
    expect(useCartStore().checkout).toHaveBeenCalled()
  })
})
```

---

## Testing Provide/Inject

```javascript
// ChildComponent.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import ChildComponent from './ChildComponent.vue'

describe('ChildComponent', () => {
  it('uses injected theme', () => {
    const wrapper = mount(ChildComponent, {
      global: { provide: { theme: ref('dark') } }
    })
    expect(wrapper.classes()).toContain('theme-dark')
  })
})
```

---

## Quick Reference

| Task | Code |
|------|------|
| Mount | `mount(Component, { props, slots, global })` |
| Find | `wrapper.find('[data-test="x"]')` |
| Trigger | `await wrapper.trigger('click')` |
| Check emitted | `wrapper.emitted('event')` |
| Set input | `await wrapper.find('input').setValue('x')` |
| Wait async | `await flushPromises()` |
| Mock composable | `vi.spyOn(module, 'fn').mockReturnValue()` |
| Mock fetch | `global.fetch = vi.fn().mockResolvedValue()` |
| Test Pinia | `createTestingPinia({ initialState })` |
| Provide | `global: { provide: { key: value } }` |
| Stub component | `global: { stubs: { Comp: true } }` |
