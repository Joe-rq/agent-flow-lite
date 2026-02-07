import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['src/**/*.{test,spec}.{js,ts,jsx,tsx}'],
    exclude: ['src/__tests__/login-verification.spec.ts', 'node_modules/', 'e2e/'],
    // Resource constraints to prevent OOM
    pool: 'forks',
    poolOptions: {
      forks: {
        maxForks: 2,
        minForks: 1
      }
    },
    maxConcurrency: 5,
    isolate: false,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules/', 'src/__tests__/setup.ts']
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  }
})
