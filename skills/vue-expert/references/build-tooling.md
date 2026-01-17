# Build Tooling & Vite

> Reference for: Vue Expert
> Load when: Vite config, build optimization, sourcemaps, bundling, tree shaking, chunk splitting

---

## Vite Configuration for Vue

### Basic Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@components': fileURLToPath(new URL('./src/components', import.meta.url)),
      '@composables': fileURLToPath(new URL('./src/composables', import.meta.url)),
      '@stores': fileURLToPath(new URL('./src/stores', import.meta.url))
    }
  }
})
```

### Essential Plugins

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import VueDevTools from 'vite-plugin-vue-devtools'
import Components from 'unplugin-vue-components/vite'
import AutoImport from 'unplugin-auto-import/vite'
import { QuasarResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),

    // Vue DevTools integration
    VueDevTools(),

    // Auto-import components
    Components({
      dirs: ['src/components'],
      resolvers: [QuasarResolver()],
      dts: 'src/components.d.ts'
    }),

    // Auto-import Vue APIs
    AutoImport({
      imports: ['vue', 'vue-router', 'pinia'],
      dts: 'src/auto-imports.d.ts',
      dirs: ['src/composables'],
      vueTemplate: true
    })
  ]
})
```

### Environment Variables

```typescript
// .env
VITE_API_URL=https://api.example.com
VITE_APP_TITLE=My App

// .env.development
VITE_API_URL=http://localhost:3000

// .env.production
VITE_API_URL=https://api.production.com
```

```typescript
// Usage in code
const apiUrl = import.meta.env.VITE_API_URL
const isDev = import.meta.env.DEV
const isProd = import.meta.env.PROD
const mode = import.meta.env.MODE

// Type declarations (env.d.ts)
/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}
```

```typescript
// vite.config.ts - Define global constants
export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version),
    __BUILD_TIME__: JSON.stringify(new Date().toISOString())
  }
})
```

### Dev Server Proxy

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:3000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/ws': {
        target: 'ws://localhost:3000',
        ws: true
      }
    }
  }
})
```

---

## Sourcemaps Configuration

### Development Sourcemaps

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // Full sourcemaps for development
    sourcemap: true
  }
})
```

### Production Sourcemaps

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // Options: true | 'inline' | 'hidden' | false
    sourcemap: process.env.NODE_ENV === 'production' ? 'hidden' : true
  }
})
```

| Mode | Value | Use Case |
|------|-------|----------|
| Full | `true` | Development, staging |
| Hidden | `'hidden'` | Production with error tracking |
| Inline | `'inline'` | Single-file debugging |
| None | `false` | Production without debugging |

### VS Code Debugging

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "chrome",
      "request": "launch",
      "name": "Debug Vue App",
      "url": "http://localhost:5173",
      "webRoot": "${workspaceFolder}/src",
      "sourceMapPathOverrides": {
        "webpack:///./src/*": "${webRoot}/*"
      }
    }
  ]
}
```

### Sentry Error Tracking

```typescript
// vite.config.ts
import { sentryVitePlugin } from '@sentry/vite-plugin'

export default defineConfig({
  build: {
    sourcemap: true
  },
  plugins: [
    sentryVitePlugin({
      org: 'your-org',
      project: 'your-project',
      authToken: process.env.SENTRY_AUTH_TOKEN,
      sourcemaps: {
        assets: './dist/**',
        filesToDeleteAfterUpload: './dist/**/*.map'
      }
    })
  ]
})
```

---

## Build Optimization

### Tree Shaking Best Practices

```typescript
// Good: Named imports enable tree shaking
import { ref, computed, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { format, parseISO } from 'date-fns'

// Bad: Namespace imports include everything
import * as Vue from 'vue'
import * as dateFns from 'date-fns'
```

```typescript
// Ensure package.json has sideEffects for proper tree shaking
{
  "sideEffects": [
    "*.css",
    "*.scss",
    "*.vue"
  ]
}
```

### Code Splitting & Lazy Loading

```typescript
// Route-based code splitting
const routes = [
  {
    path: '/dashboard',
    component: () => import('./views/Dashboard.vue')
  },
  {
    path: '/settings',
    component: () => import('./views/Settings.vue')
  }
]

// Component-level lazy loading
const HeavyChart = defineAsyncComponent(() =>
  import('./components/HeavyChart.vue')
)

// With loading/error states
const AsyncModal = defineAsyncComponent({
  loader: () => import('./components/Modal.vue'),
  loadingComponent: LoadingSpinner,
  errorComponent: ErrorDisplay,
  delay: 200,
  timeout: 10000
})
```

### Manual Chunks Configuration

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunk for core dependencies
          'vendor': ['vue', 'vue-router', 'pinia'],

          // UI framework chunk
          'ui': ['quasar', '@quasar/extras'],

          // Utility libraries
          'utils': ['lodash-es', 'date-fns', 'axios']
        }
      }
    }
  }
})
```

```typescript
// Dynamic chunking by package
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Split each package into its own chunk
            const packageName = id.split('node_modules/')[1].split('/')[0]
            return `vendor-${packageName}`
          }
        }
      }
    }
  }
})
```

### Chunk Size Optimization

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // Warn if chunk exceeds 500KB
    chunkSizeWarningLimit: 500,

    rollupOptions: {
      output: {
        // Ensure CSS is extracted
        assetFileNames: 'assets/[name]-[hash][extname]',
        chunkFileNames: 'js/[name]-[hash].js',
        entryFileNames: 'js/[name]-[hash].js'
      }
    }
  }
})
```

### Compression Plugins

```typescript
// vite.config.ts
import viteCompression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    // Gzip compression
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 1024
    }),

    // Brotli compression (better ratio)
    viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 1024
    })
  ]
})
```

### Image Optimization

```typescript
// vite.config.ts
import viteImagemin from 'vite-plugin-imagemin'

export default defineConfig({
  plugins: [
    viteImagemin({
      gifsicle: { optimizationLevel: 3 },
      optipng: { optimizationLevel: 7 },
      mozjpeg: { quality: 80 },
      svgo: {
        plugins: [
          { name: 'removeViewBox', active: false },
          { name: 'removeEmptyAttrs', active: true }
        ]
      },
      webp: { quality: 80 }
    })
  ]
})
```

---

## Performance Analysis

### Bundle Analyzer

```typescript
// vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    visualizer({
      filename: 'stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
      template: 'treemap' // or 'sunburst', 'network'
    })
  ]
})
```

```bash
# Generate analysis report
npm run build
# Opens stats.html automatically
```

### Build Performance

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    // Faster builds with esbuild minification
    minify: 'esbuild',

    // Target modern browsers only
    target: 'esnext',

    // Disable CSS code splitting for faster builds
    cssCodeSplit: false
  },

  // Optimize dependency pre-bundling
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios'],
    exclude: ['your-local-package']
  }
})
```

### Web Vitals Monitoring

```typescript
// src/utils/vitals.ts
import { onCLS, onFID, onLCP, onFCP, onTTFB } from 'web-vitals'

type VitalMetric = {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
}

function sendToAnalytics(metric: VitalMetric) {
  // Send to your analytics endpoint
  console.log(metric)
}

export function initVitals() {
  onCLS(sendToAnalytics)
  onFID(sendToAnalytics)
  onLCP(sendToAnalytics)
  onFCP(sendToAnalytics)
  onTTFB(sendToAnalytics)
}
```

```typescript
// main.ts
import { initVitals } from './utils/vitals'

if (import.meta.env.PROD) {
  initVitals()
}
```

---

## Quick Reference

| Pattern | Use Case |
|---------|----------|
| `@vitejs/plugin-vue` | Vue 3 SFC support |
| `unplugin-vue-components` | Auto-import components |
| `unplugin-auto-import` | Auto-import Vue APIs |
| `manualChunks` | Vendor code splitting |
| `sourcemap: 'hidden'` | Production error tracking |
| `vite-plugin-compression` | Gzip/Brotli compression |
| `rollup-plugin-visualizer` | Bundle size analysis |
| `import.meta.env.VITE_*` | Environment variables |
| `defineAsyncComponent` | Component lazy loading |
| `web-vitals` | Core Web Vitals monitoring |
