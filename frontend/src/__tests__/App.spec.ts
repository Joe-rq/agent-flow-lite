import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import App from '@/App.vue'

describe('App Chrome and Navigation', () => {
  let router: ReturnType<typeof createRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    // Clear auth-related localStorage to avoid state pollution
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')

    router = createRouter({
      history: createWebHistory(),
      routes: [
        {
          path: '/login',
          name: 'login',
          component: { template: '<div>Login</div>' },
          meta: { public: true, hideChrome: true },
        },
        {
          path: '/',
          name: 'home',
          component: { template: '<div>Home</div>' },
        },
      ],
    })
    pinia = createPinia()
    setActivePinia(pinia)
    await router.push('/login')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should NOT render header when user is not authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = null
    authStore.user = null

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const header = wrapper.find('.app-header')
    expect(header.exists()).toBe(false)
  })

  it('should NOT render sidebar when user is not authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = null
    authStore.user = null

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const sidebar = wrapper.find('.app-sidebar')
    expect(sidebar.exists()).toBe(false)
  })

  it('should render header when user is authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: '1', email: 'test@example.com', role: 'user' })

    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    await flushPromises()

    const header = wrapper.find('.app-header')
    expect(header.exists()).toBe(true)
  })

  it('should render sidebar when user is authenticated', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: '1', email: 'test@example.com', role: 'user' })

    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    await flushPromises()

    const sidebar = wrapper.find('.app-sidebar')
    expect(sidebar.exists()).toBe(true)
  })

  it('should redirect to /login immediately after clicking logout', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: '1', email: 'test@example.com', role: 'user' })

    await router.push('/')
    await router.isReady()

    vi.spyOn(axios, 'post').mockResolvedValueOnce({ data: {} })

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    await flushPromises()

    const logoutButton = wrapper.find('[data-testid="logout-button"]')
    await logoutButton.trigger('click')

    await flushPromises()
    await router.isReady()

    expect(router.currentRoute.value.path).toBe('/login')
  })
})
