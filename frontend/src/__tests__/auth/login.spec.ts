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

    await authStore.login('test@example.com', 'password123')

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'test@example.com',
      password: 'password123',
    })
    expect(authStore.token).toBe('test-token-123')
    expect(authStore.user).toEqual({ id: '1', email: 'test@example.com', role: 'user' })
    expect(localStorage.getItem('auth_token')).toBe('test-token-123')
  })

  it('should register successfully and store token', async () => {
    const authStore = useAuthStore()
    const mockResponse = {
      data: {
        token: 'new-token-456',
        user: { id: '2', email: 'new@example.com', role: 'user' },
      },
    }
    vi.mocked(axios.post).mockResolvedValueOnce(mockResponse)

    await authStore.register('new@example.com', 'password123')

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/register', {
      email: 'new@example.com',
      password: 'password123',
    })
    expect(authStore.token).toBe('new-token-456')
    expect(authStore.user).toEqual({ id: '2', email: 'new@example.com', role: 'user' })
    expect(localStorage.getItem('auth_token')).toBe('new-token-456')
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

  it('should init from localStorage and revalidate user', async () => {
    localStorage.setItem('auth_token', 'stored-token')
    const authStore = useAuthStore()

    // Mock /me to return user data
    vi.mocked(axios.get).mockResolvedValueOnce({
      data: { id: 1, email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' }
    })

    const result = await authStore.init()

    expect(result).toBe(true)
    expect(authStore.token).toBe('stored-token')
    expect(authStore.user).not.toBeNull()
    expect(authStore.isAuthenticated).toBe(true)
  })

  it('should return false from init when no token in localStorage', async () => {
    const authStore = useAuthStore()
    const result = await authStore.init()

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

  it('should set isHydrating to true during init /me call', async () => {
    localStorage.setItem('auth_token', 'stored-token')
    const authStore = useAuthStore()

    let resolveMe: (value: unknown) => void
    const mePromise = new Promise((resolve) => { resolveMe = resolve })
    vi.mocked(axios.get).mockReturnValueOnce(mePromise as Promise<unknown>)

    const initPromise = authStore.init()

    // During the /me call, isHydrating should be true
    expect(authStore.isHydrating).toBe(true)

    resolveMe!({
      data: { id: 1, email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' }
    })
    await initPromise

    // After /me completes, isHydrating should be false
    expect(authStore.isHydrating).toBe(false)
  })

  it('should set isHydrating to false even when /me fails', async () => {
    localStorage.setItem('auth_token', 'stored-token')
    const authStore = useAuthStore()

    vi.mocked(axios.get).mockRejectedValueOnce(new Error('Network Error'))

    await authStore.init()

    expect(authStore.isHydrating).toBe(false)
  })
})

describe('Refresh-Logout Bug (RED PHASE)', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.clearAllMocks()
  })

  it('init with cached token should restore both token and user for isAuthenticated=true', async () => {
    localStorage.setItem('auth_token', 'cached-token')

    const authStore = useAuthStore()

    vi.mocked(axios.get).mockResolvedValueOnce({
      data: { id: 1, email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' }
    })

    await authStore.init()

    expect(authStore.token).toBe('cached-token')
    expect(authStore.user).not.toBeNull()
    expect(authStore.isAuthenticated).toBe(true)
  })

  it('refresh with valid token but missing user should trigger revalidation via /api/v1/auth/me', async () => {
    localStorage.setItem('auth_token', 'valid-token')

    const authStore = useAuthStore()

    const mockMeResponse = {
      data: { id: '1', email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' },
    }
    vi.mocked(axios.get).mockResolvedValueOnce(mockMeResponse)

    const result = await authStore.init()

    expect(result).toBe(true)
    expect(authStore.token).toBe('valid-token')
    expect(axios.get).toHaveBeenCalledWith('/api/v1/auth/me')
    expect(authStore.user).not.toBeNull()
    expect(authStore.isAuthenticated).toBe(true)
  })

  it('401 from /me should clear auth state and redirect to /login', async () => {
    localStorage.setItem('auth_token', 'expired-token')

    const authStore = useAuthStore()

    const mock401Error = {
      response: { status: 401 },
    }
    vi.mocked(axios.get).mockRejectedValueOnce(mock401Error)

    await authStore.init()

    expect(authStore.token).toBeNull()
    expect(authStore.user).toBeNull()
    expect(localStorage.getItem('auth_token')).toBeNull()
  })

  it('network failure during /me should gracefully handle without breaking', async () => {
    localStorage.setItem('auth_token', 'valid-token')

    const authStore = useAuthStore()

    vi.mocked(axios.get).mockRejectedValueOnce(new Error('Network Error'))

    await authStore.init()

    expect(axios.get).toHaveBeenCalledWith('/api/v1/auth/me')
  })

  it('isAuthenticated should be false when token exists but user is null', () => {
    localStorage.setItem('auth_token', 'some-token')
    const authStore = useAuthStore()

    authStore.init()

    expect(authStore.token).not.toBeNull()
    expect(authStore.user).toBeNull()
    expect(authStore.isAuthenticated).toBe(false)
  })

  it('should call /api/v1/auth/me to restore user after init', async () => {
    localStorage.setItem('auth_token', 'cached-token')

    vi.mocked(axios.get).mockResolvedValueOnce({
      data: { id: 1, email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' }
    })

    const authStore = useAuthStore()
    await authStore.init()

    expect(axios.get).toHaveBeenCalledWith('/api/v1/auth/me')
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

  it('should display email and password inputs', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })
    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.find('input[type="password"]')
    expect(emailInput.exists()).toBe(true)
    expect(passwordInput.exists()).toBe(true)
    expect(emailInput.attributes('placeholder')).toBe('请输入邮箱地址')
    expect(passwordInput.attributes('placeholder')).toBe('请输入密码')
  })

  it('should display login button', () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })
    const button = wrapper.find('button')
    expect(button.text()).toContain('登录')
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

  it('should show error for empty password', async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const emailInput = wrapper.find('input[type="email"]')
    await emailInput.setValue('test@example.com')

    const button = wrapper.find('button')
    await button.trigger('click')

    expect(wrapper.text()).toContain('请输入密码')
  })

  it('should call login API with valid email and password', async () => {
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

    const emailInput = wrapper.find('input[type="email"]')
    await emailInput.setValue('test@example.com')

    const passwordInput = wrapper.find('input[type="password"]')
    await passwordInput.setValue('password123')

    const button = wrapper.find('button')
    await button.trigger('click')

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/login', {
      email: 'test@example.com',
      password: 'password123',
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

    const emailInput = wrapper.find('input[type="email"]')
    await emailInput.setValue('test@example.com')

    const passwordInput = wrapper.find('input[type="password"]')
    await passwordInput.setValue('password123')

    const button = wrapper.find('button')
    await button.trigger('click')

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(pushSpy).toHaveBeenCalledWith('/')
  })

  it('should show error message on login failure', async () => {
    vi.mocked(axios.post).mockRejectedValueOnce({
      response: { data: { detail: 'Invalid email or password' } },
    })

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    const emailInput = wrapper.find('input[type="email"]')
    await emailInput.setValue('test@example.com')

    const passwordInput = wrapper.find('input[type="password"]')
    await passwordInput.setValue('wrongpassword')

    const button = wrapper.find('button')
    await button.trigger('click')

    await new Promise((resolve) => setTimeout(resolve, 0))

    expect(wrapper.text()).toContain('Invalid email or password')
  })

  it('should toggle between login and register mode', async () => {
    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    // Initially in login mode
    expect(wrapper.text()).toContain('没有账号？')
    expect(wrapper.text()).toContain('去注册')

    // Toggle to register mode
    const toggleLink = wrapper.find('.toggle-link')
    await toggleLink.trigger('click')

    expect(wrapper.text()).toContain('已有账号？')
    expect(wrapper.text()).toContain('去登录')

    // Should show confirm password field in register mode
    const passwordInputs = wrapper.findAll('input[type="password"]')
    expect(passwordInputs.length).toBe(2)
  })

  it('should call register API in register mode', async () => {
    const mockResponse = {
      data: {
        token: 'new-token',
        user: { id: '2', email: 'new@example.com', role: 'user' },
      },
    }
    vi.mocked(axios.post).mockResolvedValueOnce(mockResponse)

    const wrapper = mount(LoginView, {
      global: {
        plugins: [router, pinia],
      },
    })

    // Toggle to register mode
    const toggleLink = wrapper.find('.toggle-link')
    await toggleLink.trigger('click')

    const emailInput = wrapper.find('input[type="email"]')
    await emailInput.setValue('new@example.com')

    const passwordInputs = wrapper.findAll('input[type="password"]')
    await passwordInputs[0].setValue('password123')
    await passwordInputs[1].setValue('password123')

    const button = wrapper.find('button')
    await button.trigger('click')

    expect(axios.post).toHaveBeenCalledWith('/api/v1/auth/register', {
      email: 'new@example.com',
      password: 'password123',
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
    // Set up authenticated state
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: 1, email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' })

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
    // Set up authenticated state
    const authStore = useAuthStore()
    authStore.token = 'test-token'
    authStore.setUser({ id: 1, email: 'test@example.com', role: 'user', is_active: true, created_at: '2024-01-01' })

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
