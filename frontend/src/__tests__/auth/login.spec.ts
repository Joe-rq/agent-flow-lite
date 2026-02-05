import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import LoginView from '@/views/LoginView.vue'
import App from '@/App.vue'
import axios from 'axios'

vi.mock('axios', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn().mockResolvedValue({ data: [] }),
    delete: vi.fn().mockResolvedValue({ status: 200 }),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  },
}))

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/login', component: LoginView, meta: { public: true, hideChrome: true } },
      { path: '/', component: { template: '<div>Home</div>' } },
    ],
  })
}

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should initialize with null token and user', () => {
    const authStore = useAuthStore()
    expect(authStore.token).toBeNull()
    expect(authStore.user).toBeNull()
    expect(authStore.isAuthenticated).toBe(false)
  })

  it('should set isAuthenticated to true when both token and user exist', () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: '1', email: 'test@example.com', role: 'user' })
    expect(authStore.isAuthenticated).toBe(true)
  })

  it('should login successfully and store token', async () => {
    const authStore = useAuthStore()
    const mockResponse = {
      data: {
        token: 'test-token-123',
        user: { id: '1', email: 'test@example.com', role: 'user' },
      },
    }
    vi.mocked(axios.post).mockResolvedValueOnce(mockResponse)

    await authStore.login('test@example.com')

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'test@example.com',
    })
    expect(authStore.token).toBe('test-token-123')
    expect(authStore.user).toEqual({ id: '1', email: 'test@example.com', role: 'user' })
    expect(localStorage.getItem('auth_token')).toBe('test-token-123')
  })

  it('should logout successfully and clear state', async () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: '1', email: 'test@example.com', role: 'user' })
    localStorage.setItem('auth_token', 'test-token')

    vi.mocked(axios.post).mockResolvedValueOnce({ data: {} })

    await authStore.logout()

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/logout')
    expect(authStore.token).toBeNull()
    expect(authStore.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('should init from localStorage', () => {
    localStorage.setItem('auth_token', 'stored-token')
    const authStore = useAuthStore()

    const result = authStore.init()

    expect(result).toBe(true)
    expect(authStore.token).toBe('stored-token')
  })

  it('should return false from init when no token in localStorage', () => {
    const authStore = useAuthStore()
    const result = authStore.init()

    expect(result).toBe(false)
    expect(authStore.token).toBeNull()
  })

  it('should clear auth state', () => {
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: '1', email: 'test@example.com', role: 'user' })
    localStorage.setItem('auth_token', 'test-token')

    authStore.clearAuth()

    expect(authStore.token).toBeNull()
    expect(authStore.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })
})

describe('LoginView', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
    localStorage.clear()
    vi.clearAllMocks()
    await router.push('/login')
    await router.isReady()
  })

  it('should mount component successfully', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display login title', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })
    expect(wrapper.text()).toContain('Agent Flow')
    expect(wrapper.text()).toContain('智能体编排平台')
  })

  it('should display email input', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })
    const input = wrapper.find('input[type="email"]')
    expect(input.exists()).toBe(true)
    expect(input.attributes('placeholder')).toBe('请输入邮箱地址')
  })

  it('should display login button', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })
    expect(wrapper.text()).toContain('登录')
  })

  it('should show error for empty email', async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const button = wrapper.find('button')
    await button.trigger('click')

    expect(wrapper.text()).toContain('请输入邮箱地址')
  })

  it('should show error for invalid email format', async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const input = wrapper.find('input[type="email"]')
    await input.setValue('invalid-email')

    const button = wrapper.find('button')
    await button.trigger('click')

    expect(wrapper.text()).toContain('请输入有效的邮箱地址')
  })

  it('should call login API with valid email', async () => {
    const mockResponse = {
      data: {
        token: 'test-token',
        user: { id: '1', email: 'test@example.com', role: 'user' },
      },
    }
    vi.mocked(axios.post).mockResolvedValueOnce(mockResponse)

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const input = wrapper.find('input[type="email"]')
    await input.setValue('test@example.com')

    const button = wrapper.find('button')
    await button.trigger('click')

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'test@example.com',
    })
  })

  it('should redirect to home after successful login', async () => {
    const mockResponse = {
      data: {
        token: 'test-token',
        user: { id: '1', email: 'test@example.com', role: 'user' },
      },
    }
    vi.mocked(axios.post).mockResolvedValueOnce(mockResponse)

    const pushSpy = vi.spyOn(router, 'push')

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const input = wrapper.find('input[type="email"]')
    await input.setValue('test@example.com')

    const button = wrapper.find('button')
    await button.trigger('click')

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(pushSpy).toHaveBeenCalledWith('/')
  })

  it('should show error message on login failure', async () => {
    vi.mocked(axios.post).mockRejectedValueOnce({
      response: { data: { detail: '用户不存在' } },
    })

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const input = wrapper.find('input[type="email"]')
    await input.setValue('test@example.com')

    const button = wrapper.find('button')
    await button.trigger('click')

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('用户不存在')
  })

  it('should display register CTA button', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })
    expect(wrapper.text()).toContain('注册')
  })

  it('should call login API when register CTA is clicked with valid email', async () => {
    const mockResponse = {
      data: {
        token: 'test-token',
        user: { id: '1', email: 'newuser@example.com', role: 'user' },
      },
    }
    vi.mocked(axios.post).mockResolvedValueOnce(mockResponse)

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const input = wrapper.find('input[type="email"]')
    await input.setValue('newuser@example.com')

    const buttons = wrapper.findAll('button')
    const registerButton = buttons.find((btn) => btn.text().includes('注册'))
    expect(registerButton).toBeDefined()
    await registerButton!.trigger('click')

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'newuser@example.com',
    })
  })
})

describe('App Chrome Hiding on Login', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('should hide header on /login route', async () => {
    await router.push('/login')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const header = wrapper.find('.app-header')
    expect(header.exists()).toBe(false)
  })

  it('should hide sidebar on /login route', async () => {
    await router.push('/login')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const sidebar = wrapper.find('.app-sidebar')
    expect(sidebar.exists()).toBe(false)
  })

  it('should show header on non-login routes', async () => {
    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const header = wrapper.find('.app-header')
    expect(header.exists()).toBe(true)
  })

  it('should show sidebar on non-login routes', async () => {
    await router.push('/')
    await router.isReady()

    const wrapper = mount(App, {
      global: {
        plugins: [router, pinia],
      },
    })

    const sidebar = wrapper.find('.app-sidebar')
    expect(sidebar.exists()).toBe(true)
  })
})
