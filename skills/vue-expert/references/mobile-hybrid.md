# Mobile & Hybrid Apps

> Reference for: Vue Expert
> Load when: Quasar, Capacitor, PWA, service worker, mobile, hybrid app, offline

---

## Quasar Framework

### Project Setup

```bash
# Create new Quasar project
npm init quasar

# Add Quasar to existing Vue project
npm install quasar @quasar/extras
npm install -D @quasar/vite-plugin
```

```typescript
// vite.config.ts - Quasar plugin setup
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { quasar, transformAssetUrls } from '@quasar/vite-plugin'

export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    quasar({
      sassVariables: 'src/quasar-variables.scss'
    })
  ]
})
```

### Quasar Configuration

```javascript
// quasar.config.js
export default configure((ctx) => ({
  // Build modes: spa, pwa, ssr, capacitor, electron, bex
  boot: ['axios', 'i18n'],

  css: ['app.scss'],

  extras: [
    'roboto-font',
    'material-icons'
  ],

  framework: {
    plugins: ['Notify', 'Dialog', 'Loading', 'LocalStorage'],
    config: {
      notify: { position: 'top-right' },
      loading: { spinnerColor: 'primary' }
    }
  },

  build: {
    target: { browser: ['es2022', 'firefox115', 'chrome115', 'safari14'] },
    vueRouterMode: 'history'
  }
}))
```

### Quasar Components with Composition API

```vue
<script setup lang="ts">
import { useQuasar } from 'quasar'

const $q = useQuasar()

function showNotification() {
  $q.notify({
    message: 'Action completed successfully',
    type: 'positive',
    position: 'top',
    timeout: 3000
  })
}

function showConfirmDialog() {
  $q.dialog({
    title: 'Confirm',
    message: 'Are you sure you want to proceed?',
    cancel: true,
    persistent: true
  }).onOk(() => {
    // User confirmed
  })
}

async function showLoading() {
  $q.loading.show({ message: 'Processing...' })
  await doAsyncWork()
  $q.loading.hide()
}
</script>
```

### Layout System

```vue
<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" @click="toggleLeftDrawer" />
        <q-toolbar-title>My App</q-toolbar-title>
        <q-btn flat round icon="person" />
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list>
        <q-item clickable v-ripple to="/dashboard">
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>Dashboard</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const leftDrawerOpen = ref(false)

function toggleLeftDrawer() {
  leftDrawerOpen.value = !leftDrawerOpen.value
}
</script>
```

### Platform Detection

```vue
<script setup lang="ts">
import { useQuasar } from 'quasar'

const $q = useQuasar()

// Platform detection
const isMobile = $q.platform.is.mobile
const isIOS = $q.platform.is.ios
const isAndroid = $q.platform.is.android
const isDesktop = $q.platform.is.desktop
const isCapacitor = $q.platform.is.capacitor

// Screen utilities
const isSmallScreen = $q.screen.lt.md
const screenWidth = $q.screen.width
</script>

<template>
  <div>
    <MobileNav v-if="isMobile" />
    <DesktopNav v-else />
  </div>
</template>
```

---

## Capacitor Integration

### Setup

```bash
# Add Capacitor to Quasar
quasar mode add capacitor

# Initialize Capacitor
cd src-capacitor
npx cap init "App Name" "com.example.app"

# Add platforms
npx cap add android
npx cap add ios

# Sync and run
npx cap sync
npx cap open android
```

### Capacitor Configuration

```typescript
// capacitor.config.ts
import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'com.example.myapp',
  appName: 'My App',
  webDir: 'dist/spa',
  server: {
    androidScheme: 'https',
    // For development
    url: 'http://192.168.1.100:9000',
    cleartext: true
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: false,
      showSpinner: true
    },
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert']
    }
  }
}

export default config
```

### Native Plugins with TypeScript

```typescript
// composables/useCamera.ts
import { ref } from 'vue'
import { Camera, CameraResultType, CameraSource } from '@capacitor/camera'

export function useCamera() {
  const photo = ref<string | null>(null)
  const error = ref<string | null>(null)

  async function takePhoto() {
    try {
      const image = await Camera.getPhoto({
        resultType: CameraResultType.Uri,
        source: CameraSource.Camera,
        quality: 90
      })
      photo.value = image.webPath ?? null
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  async function pickFromGallery() {
    try {
      const image = await Camera.getPhoto({
        resultType: CameraResultType.Uri,
        source: CameraSource.Photos,
        quality: 90
      })
      photo.value = image.webPath ?? null
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  return { photo, error, takePhoto, pickFromGallery }
}
```

```typescript
// composables/useGeolocation.ts
import { ref, onMounted, onUnmounted } from 'vue'
import { Geolocation, Position } from '@capacitor/geolocation'

export function useGeolocation() {
  const position = ref<Position | null>(null)
  const error = ref<string | null>(null)
  let watchId: string | null = null

  async function getCurrentPosition() {
    try {
      position.value = await Geolocation.getCurrentPosition({
        enableHighAccuracy: true
      })
    } catch (e) {
      error.value = (e as Error).message
    }
  }

  async function watchPosition() {
    watchId = await Geolocation.watchPosition(
      { enableHighAccuracy: true },
      (pos, err) => {
        if (err) {
          error.value = err.message
        } else if (pos) {
          position.value = pos
        }
      }
    )
  }

  function stopWatching() {
    if (watchId) {
      Geolocation.clearWatch({ id: watchId })
      watchId = null
    }
  }

  onUnmounted(stopWatching)

  return { position, error, getCurrentPosition, watchPosition, stopWatching }
}
```

### Push Notifications

```typescript
// composables/usePushNotifications.ts
import { ref, onMounted } from 'vue'
import { PushNotifications, Token, PushNotificationSchema } from '@capacitor/push-notifications'
import { Capacitor } from '@capacitor/core'

export function usePushNotifications() {
  const token = ref<string | null>(null)
  const notifications = ref<PushNotificationSchema[]>([])

  async function register() {
    if (!Capacitor.isNativePlatform()) return

    const permission = await PushNotifications.requestPermissions()
    if (permission.receive !== 'granted') return

    await PushNotifications.register()
  }

  onMounted(() => {
    if (!Capacitor.isNativePlatform()) return

    PushNotifications.addListener('registration', (t: Token) => {
      token.value = t.value
    })

    PushNotifications.addListener('pushNotificationReceived', (notification) => {
      notifications.value.push(notification)
    })

    PushNotifications.addListener('pushNotificationActionPerformed', (action) => {
      // Handle notification tap
      console.log('Action:', action.actionId)
    })
  })

  return { token, notifications, register }
}
```

### App Lifecycle

```typescript
// composables/useAppLifecycle.ts
import { onMounted, onUnmounted } from 'vue'
import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'

export function useAppLifecycle() {
  onMounted(() => {
    if (!Capacitor.isNativePlatform()) return

    App.addListener('appStateChange', ({ isActive }) => {
      if (isActive) {
        // App came to foreground
        refreshData()
      } else {
        // App went to background
        saveState()
      }
    })

    App.addListener('backButton', ({ canGoBack }) => {
      if (!canGoBack) {
        App.exitApp()
      } else {
        window.history.back()
      }
    })
  })

  onUnmounted(() => {
    App.removeAllListeners()
  })
}
```

---

## PWA & Service Workers

### Workbox Configuration

```javascript
// quasar.config.js
export default configure((ctx) => ({
  pwa: {
    workboxMode: 'GenerateSW', // or 'InjectManifest'

    workboxOptions: {
      skipWaiting: true,
      clientsClaim: true,
      cleanupOutdatedCaches: true,

      // Cache strategies
      runtimeCaching: [
        {
          // Cache API responses
          urlPattern: /^https:\/\/api\./,
          handler: 'NetworkFirst',
          options: {
            cacheName: 'api-cache',
            networkTimeoutSeconds: 10,
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 60 * 60 * 24 // 24 hours
            }
          }
        },
        {
          // Cache images
          urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp)$/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'image-cache',
            expiration: {
              maxEntries: 50,
              maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
            }
          }
        },
        {
          // Cache fonts
          urlPattern: /\.(?:woff|woff2|ttf|eot)$/,
          handler: 'CacheFirst',
          options: {
            cacheName: 'font-cache',
            expiration: {
              maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
            }
          }
        }
      ]
    }
  }
}))
```

### Web App Manifest

```javascript
// quasar.config.js
export default configure((ctx) => ({
  pwa: {
    manifest: {
      name: 'My Progressive App',
      short_name: 'MyApp',
      description: 'A Progressive Web Application',
      display: 'standalone',
      orientation: 'portrait',
      background_color: '#ffffff',
      theme_color: '#1976D2',
      start_url: '/',
      icons: [
        {
          src: 'icons/icon-128x128.png',
          sizes: '128x128',
          type: 'image/png'
        },
        {
          src: 'icons/icon-512x512.png',
          sizes: '512x512',
          type: 'image/png'
        }
      ]
    }
  }
}))
```

### Install Prompt Handling

```typescript
// composables/usePWAInstall.ts
import { ref, onMounted } from 'vue'

interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

export function usePWAInstall() {
  const canInstall = ref(false)
  const isInstalled = ref(false)
  let deferredPrompt: BeforeInstallPromptEvent | null = null

  onMounted(() => {
    // Check if already installed
    isInstalled.value = window.matchMedia('(display-mode: standalone)').matches

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault()
      deferredPrompt = e as BeforeInstallPromptEvent
      canInstall.value = true
    })

    window.addEventListener('appinstalled', () => {
      isInstalled.value = true
      canInstall.value = false
      deferredPrompt = null
    })
  })

  async function install() {
    if (!deferredPrompt) return false

    await deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    deferredPrompt = null
    canInstall.value = false

    return outcome === 'accepted'
  }

  return { canInstall, isInstalled, install }
}
```

### PWA Update Flow

```typescript
// composables/usePWAUpdate.ts
import { ref, onMounted } from 'vue'
import { useQuasar } from 'quasar'

export function usePWAUpdate() {
  const $q = useQuasar()
  const needsUpdate = ref(false)
  let registration: ServiceWorkerRegistration | null = null

  onMounted(() => {
    if (!('serviceWorker' in navigator)) return

    navigator.serviceWorker.ready.then((reg) => {
      registration = reg

      reg.addEventListener('updatefound', () => {
        const newWorker = reg.installing
        if (!newWorker) return

        newWorker.addEventListener('statechange', () => {
          if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
            needsUpdate.value = true
            promptUpdate()
          }
        })
      })
    })
  })

  function promptUpdate() {
    $q.notify({
      message: 'A new version is available',
      timeout: 0,
      actions: [
        {
          label: 'Update',
          color: 'white',
          handler: updateApp
        },
        {
          label: 'Later',
          color: 'white'
        }
      ]
    })
  }

  function updateApp() {
    if (registration?.waiting) {
      registration.waiting.postMessage({ type: 'SKIP_WAITING' })
    }
    window.location.reload()
  }

  return { needsUpdate, updateApp }
}
```

### Offline Detection

```typescript
// composables/useOnlineStatus.ts
import { ref, onMounted, onUnmounted } from 'vue'

export function useOnlineStatus() {
  const isOnline = ref(navigator.onLine)

  function updateOnlineStatus() {
    isOnline.value = navigator.onLine
  }

  onMounted(() => {
    window.addEventListener('online', updateOnlineStatus)
    window.addEventListener('offline', updateOnlineStatus)
  })

  onUnmounted(() => {
    window.removeEventListener('online', updateOnlineStatus)
    window.removeEventListener('offline', updateOnlineStatus)
  })

  return { isOnline }
}
```

---

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `useQuasar()` | Access Quasar plugins ($q) |
| `$q.platform.is.*` | Platform detection |
| `$q.notify()` | Toast notifications |
| `$q.dialog()` | Modal dialogs |
| `@capacitor/camera` | Native camera access |
| `@capacitor/geolocation` | GPS location |
| `@capacitor/push-notifications` | Push notifications |
| `workboxMode: 'GenerateSW'` | Auto-generate service worker |
| `runtimeCaching` | Workbox cache strategies |
| `beforeinstallprompt` | PWA install prompt |
| `navigator.serviceWorker.ready` | Service worker lifecycle |
