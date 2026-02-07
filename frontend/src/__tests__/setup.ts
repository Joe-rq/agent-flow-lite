import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'

// Simple smoke test to verify Vitest setup
describe('Vitest Setup', () => {
  it('should run tests successfully', () => {
    expect(true).toBe(true)
  })

  it('should handle async operations', async () => {
    const result = await Promise.resolve(42)
    expect(result).toBe(42)
  })
})

// Helper to create test router
export function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/', component: { template: '<div>Home</div>' } },
      { path: '/workflow', component: { template: '<div>Workflow</div>' } },
      { path: '/knowledge', component: { template: '<div>Knowledge</div>' } },
      { path: '/chat', component: { template: '<div>Chat</div>' } }
    ]
  })
}

// Helper to mount component with required plugins
export function mountWithPlugins(component: unknown, options: Record<string, unknown> = {}) {
  const router = createTestRouter()
  const pinia = createPinia()

  return mount(component, {
    global: {
      plugins: [router, pinia]
    },
    ...options
  })
}
