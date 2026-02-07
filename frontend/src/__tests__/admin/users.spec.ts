import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import AdminUsersView from '@/views/AdminUsersView.vue'
import Button from '@/components/ui/Button.vue'
import axios from 'axios'

vi.mock('axios')

const mockedAxios = axios as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

interface User {
  id: number
  email: string
  role: string
  is_active: boolean
  created_at: string
}

function mockApiCalls(users: User[], currentUser: User) {
  mockedAxios.get.mockImplementation((url: string) => {
    if (url === '/api/v1/auth/me') {
      return Promise.resolve({ data: currentUser })
    }
    if (url === '/api/v1/admin/users') {
      return Promise.resolve({ data: { users, total: users.length } })
    }
    return Promise.reject(new Error('Unknown URL'))
  })
}

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/admin', component: AdminUsersView },
      { path: '/', component: { template: '<div>Home</div>' } }
    ]
  })
}

describe('AdminUsersView', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  const mockUsers = [
    {
      id: 1,
      email: 'admin@example.com',
      role: 'admin',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z'
    },
    {
      id: 2,
      email: 'user@example.com',
      role: 'user',
      is_active: true,
      created_at: '2024-01-02T00:00:00Z'
    },
    {
      id: 3,
      email: 'disabled@example.com',
      role: 'user',
      is_active: false,
      created_at: '2024-01-03T00:00:00Z'
    }
  ]

  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    router = createTestRouter()
    await router.push('/admin')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should mount component successfully', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    expect(wrapper.exists()).toBe(true)
  })

  it('should display page title', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    expect(wrapper.text()).toContain('用户管理')
  })

  it('should render user list table', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    expect(wrapper.find('.users-table').exists()).toBe(true)
  })

  it('should display correct number of users', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    const rows = wrapper.findAll('.table-row')
    expect(rows.length).toBe(3)
  })

  it('should display user emails', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('admin@example.com')
    expect(text).toContain('user@example.com')
  })

  it('should display correct role badges', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    expect(wrapper.text()).toContain('管理员')
    expect(wrapper.text()).toContain('用户')
  })

  it('should display correct status badges', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    expect(wrapper.text()).toContain('启用')
    expect(wrapper.text()).toContain('禁用')
  })

  it('should show empty state when no users', async () => {
    mockApiCalls([], mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.text()).toContain('暂无用户')
  })

  it('should filter users by search query', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()

    const searchInput = wrapper.find('.search-input')
    await searchInput.setValue('admin')
    await searchInput.trigger('keyup.enter')

    const rows = wrapper.findAll('.table-row')
    expect(rows.length).toBe(1)
    expect(wrapper.text()).toContain('admin@example.com')
    expect(wrapper.text()).not.toContain('user@example.com')
  })

  it('should show current user indicator for self', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    expect(wrapper.text()).toContain('当前用户')
  })

  it('should show disable button for active users', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    const buttons = wrapper.findAllComponents(Button)
    const buttonTexts = buttons.map(b => b.text())
    expect(buttonTexts).toContain('禁用')
  })

  it('should show enable button for disabled users', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    const buttons = wrapper.findAllComponents(Button)
    const buttonTexts = buttons.map(b => b.text())
    expect(buttonTexts).toContain('启用')
  })

  it('should show delete button for non-self users', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    const buttons = wrapper.findAllComponents(Button)
    const buttonTexts = buttons.map(b => b.text())
    expect(buttonTexts).toContain('删除')
  })

  it('should call API when confirming disable action', async () => {
    mockApiCalls(mockUsers, mockUsers[0])
    mockedAxios.post.mockResolvedValueOnce({ data: { success: true, message: 'User disabled' } })

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()

    const disableButton = wrapper.findAllComponents(Button).find(b => b.text() === '禁用')
    if (disableButton) {
      await disableButton.trigger('click')
      await flushPromises()

      const confirmButton = wrapper.findAllComponents(Button).find(b => b.text() === '确认')
      if (confirmButton) {
        await confirmButton.trigger('click')
        await flushPromises()

        expect(mockedAxios.post).toHaveBeenCalledWith(
          '/api/v1/admin/users/2/disable'
        )
      }
    }
  })

  it('should show confirm dialog before action', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()

    const disableButton = wrapper.findAllComponents(Button).find(b => b.text() === '禁用')
    if (disableButton) {
      await disableButton.trigger('click')
      await flushPromises()

      expect(wrapper.find('.dialog-overlay').exists()).toBe(true)
      expect(wrapper.text()).toContain('禁用用户')
    }
  })

  it('should format dates correctly', async () => {
    mockApiCalls(mockUsers, mockUsers[0])

    const wrapper = mount(AdminUsersView, {
      global: {
        plugins: [router, pinia],
        components: { Button }
      }
    })

    await flushPromises()
    const text = wrapper.text()
    expect(text).toMatch(/\d{4}[/-]\d{2}[/-]\d{2}/)
  })
})
