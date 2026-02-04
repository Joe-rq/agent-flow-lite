import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import SkillsView from '@/views/SkillsView.vue'

const mockGet = vi.fn()
const mockDelete = vi.fn()
const mockFetch = vi.fn()

vi.mock('axios', () => ({
  default: {
    get: (...args: any[]) => mockGet(...args),
    delete: (...args: any[]) => mockDelete(...args),
  }
}))

global.fetch = mockFetch

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/skills', component: SkillsView },
      { path: '/skills/new', component: { template: '<div>New Skill</div>' } },
      { path: '/skills/:name', component: { template: '<div>Edit Skill</div>' } }
    ]
  })
}

describe('SkillsView Smoke Tests', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills')
    await router.isReady()
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('should mount component successfully', () => {
    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display Chinese title', () => {
    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('技能管理')
  })

  it('should display buttons in Chinese', () => {
    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })
    const text = wrapper.text()
    expect(text).toContain('新建技能')
  })

  it('should display empty state in Chinese', () => {
    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('暂无技能')
  })
})

describe('SkillsView Skill List', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should load and display skills', async () => {
    const mockSkills = {
      items: [
        {
          name: 'text-summarizer',
          description: 'Summarize text content',
          model: 'deepseek-chat',
          inputs: [{ name: 'text', required: true }],
          updated_at: '2024-01-15T10:00:00Z'
        },
        {
          name: 'code-reviewer',
          description: 'Review code quality',
          model: 'deepseek-coder',
          inputs: [],
          updated_at: '2024-01-14T08:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    expect(mockGet).toHaveBeenCalledWith('/api/v1/skills')
    expect(wrapper.text()).toContain('text-summarizer')
    expect(wrapper.text()).toContain('code-reviewer')
    expect(wrapper.text()).toContain('Summarize text content')
  })

  it('should display skill inputs as tags', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [
            { name: 'input1', required: true },
            { name: 'input2', required: false },
            { name: 'input3', required: false }
          ],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('input1')
    expect(wrapper.text()).toContain('input2')
    expect(wrapper.text()).toContain('input3')
  })

  it('should show +N more for more than 3 inputs', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [
            { name: 'a', required: false },
            { name: 'b', required: false },
            { name: 'c', required: false },
            { name: 'd', required: false },
            { name: 'e', required: false }
          ],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    expect(wrapper.text()).toContain('+2')
  })

  it('should handle API error when loading skills', async () => {
    mockGet.mockRejectedValueOnce(new Error('Network error'))
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    expect(alertSpy).toHaveBeenCalledWith('加载技能列表失败')
    alertSpy.mockRestore()
  })
})

describe('SkillsView Navigation', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should navigate to new skill page when clicking create button', async () => {
    const pushSpy = vi.spyOn(router, 'push')
    mockGet.mockResolvedValueOnce({ data: { items: [] } })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const createButton = wrapper.find('.btn-primary')
    await createButton.trigger('click')

    expect(pushSpy).toHaveBeenCalledWith('/skills/new')
  })

  it('should navigate to edit page when clicking skill card', async () => {
    const pushSpy = vi.spyOn(router, 'push')
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const skillCard = wrapper.find('.skill-card')
    await skillCard.trigger('click')

    expect(pushSpy).toHaveBeenCalledWith('/skills/test-skill')
  })
})

describe('SkillsView Delete', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should delete skill when confirmed', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })
    mockDelete.mockResolvedValueOnce({ status: 200 })
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const deleteButton = wrapper.find('.btn-delete-skill')
    await deleteButton.trigger('click')

    expect(mockDelete).toHaveBeenCalledWith('/api/v1/skills/test-skill')
    await flushPromises()
    expect(wrapper.text()).not.toContain('test-skill')
  })

  it('should not delete skill when cancelled', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })
    vi.spyOn(window, 'confirm').mockReturnValue(false)

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const deleteButton = wrapper.find('.btn-delete-skill')
    await deleteButton.trigger('click')

    expect(mockDelete).not.toHaveBeenCalled()
  })

  it('should show error when delete fails', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })
    mockDelete.mockRejectedValueOnce({
      response: { data: { detail: 'Delete failed' } }
    })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const deleteButton = wrapper.find('.btn-delete-skill')
    await deleteButton.trigger('click')
    await flushPromises()

    expect(alertSpy).toHaveBeenCalledWith('Delete failed')
    alertSpy.mockRestore()
  })
})

describe('SkillsView Run Modal', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills')
    await router.isReady()
    vi.clearAllMocks()
  })

  it('should open run modal when clicking run button', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [{ name: 'text', required: true }],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    expect(wrapper.text()).toContain('运行技能: test-skill')
    expect(wrapper.text()).toContain('text')
  })

  it('should close run modal when clicking cancel', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')
    expect(wrapper.find('.dialog-overlay').exists()).toBe(true)

    const cancelButton = wrapper.findAll('.dialog-actions button').find(b => b.text() === '取消')
    if (cancelButton) {
      await cancelButton.trigger('click')
    }

    expect(wrapper.find('.dialog-overlay').exists()).toBe(false)
  })

  it('should validate required inputs before running', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [{ name: 'text', required: true, description: 'Input text' }],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })
    const alertSpy = vi.spyOn(window, 'alert').mockImplementation(() => {})

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const runConfirmButton = wrapper.findAll('.dialog-actions button').find(b => b.text().includes('运行'))
    if (runConfirmButton) {
      await runConfirmButton.trigger('click')
    }

    expect(alertSpy).toHaveBeenCalledWith(expect.stringContaining('请填写必填项'))
    alertSpy.mockRestore()
  })

  it('should set default values in run form', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [{ name: 'style', required: false, default: 'formal' }],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const input = wrapper.find('.run-inputs input')
    expect(input.element.value).toBe('formal')
  })
})

describe('SkillsView SSE Run', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/skills')
    await router.isReady()
    vi.clearAllMocks()
  })

  function createMockStream(chunks: string[]) {
    const encoder = new TextEncoder()
    let index = 0
    return {
      getReader: () => ({
        read: () => {
          if (index < chunks.length) {
            return Promise.resolve({
              done: false,
              value: encoder.encode(chunks[index++])
            })
          }
          return Promise.resolve({ done: true, value: undefined })
        }
      })
    }
  }

  it('should handle SSE token events', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const mockResponse = {
      ok: true,
      body: createMockStream([
        'event: token\ndata: {"content": "Hello"}\n\n',
        'event: token\ndata: {"content": " World"}\n\n',
        'event: done\ndata: {"status": "success"}\n\n'
      ])
    }
    mockFetch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const runConfirmButton = wrapper.findAll('.dialog-actions button').find(b => b.text().includes('运行'))
    if (runConfirmButton) {
      await runConfirmButton.trigger('click')
    }

    await flushPromises()

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/skills/test-skill/run',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inputs: {} })
      })
    )
  })

  it('should handle SSE thought events', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const mockResponse = {
      ok: true,
      body: createMockStream([
        'event: thought\ndata: {"content": "Processing..."}\n\n',
        'event: token\ndata: {"content": "result"}\n\n',
        'event: done\ndata: {"status": "success"}\n\n'
      ])
    }
    mockFetch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const runConfirmButton = wrapper.findAll('.dialog-actions button').find(b => b.text().includes('运行'))
    if (runConfirmButton) {
      await runConfirmButton.trigger('click')
    }

    await flushPromises()

    const outputContent = wrapper.find('.output-content')
    expect(outputContent.exists()).toBe(true)
  })

  it('should handle SSE citation events', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const mockResponse = {
      ok: true,
      body: createMockStream([
        'event: citation\ndata: {"sources": [{"doc_id": "doc1"}, {"doc_id": "doc2"}]}\n\n',
        'event: done\ndata: {"status": "success"}\n\n'
      ])
    }
    mockFetch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const runConfirmButton = wrapper.findAll('.dialog-actions button').find(b => b.text().includes('运行'))
    if (runConfirmButton) {
      await runConfirmButton.trigger('click')
    }

    await flushPromises()

    expect(wrapper.text()).toContain('引用')
  })

  it('should handle SSE error events', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const mockResponse = {
      ok: true,
      body: createMockStream([
        'event: error\ndata: {"message": "Something went wrong"}\n\n'
      ])
    }
    mockFetch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const runConfirmButton = wrapper.findAll('.dialog-actions button').find(b => b.text().includes('运行'))
    if (runConfirmButton) {
      await runConfirmButton.trigger('click')
    }

    await flushPromises()

    expect(wrapper.text()).toContain('[错误:')
  })

  it('should handle fetch error', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const runConfirmButton = wrapper.findAll('.dialog-actions button').find(b => b.text().includes('运行'))
    if (runConfirmButton) {
      await runConfirmButton.trigger('click')
    }

    await flushPromises()

    expect(wrapper.text()).toContain('[错误:')
  })

  it('should prevent closing modal while running', async () => {
    const mockSkills = {
      items: [
        {
          name: 'test-skill',
          description: 'Test skill',
          inputs: [],
          updated_at: '2024-01-15T10:00:00Z'
        }
      ]
    }
    mockGet.mockResolvedValueOnce({ data: mockSkills })

    const mockResponse = {
      ok: true,
      body: {
        getReader: () => ({
          read: () => new Promise(() => {})
        })
      }
    }
    mockFetch.mockResolvedValueOnce(mockResponse)

    const wrapper = mount(SkillsView, {
      global: {
        plugins: [router, pinia]
      }
    })

    await flushPromises()

    const runButton = wrapper.find('.btn-run')
    await runButton.trigger('click')

    const runConfirmButton = wrapper.findAll('.dialog-actions button').find(b => b.text().includes('运行'))
    if (runConfirmButton) {
      await runConfirmButton.trigger('click')
    }

    await flushPromises()

    const overlay = wrapper.find('.dialog-overlay')
    await overlay.trigger('click')

    expect(wrapper.find('.dialog-overlay').exists()).toBe(true)
  })
})
