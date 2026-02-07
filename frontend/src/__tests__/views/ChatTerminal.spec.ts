import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia } from 'pinia'
import ChatTerminal from '@/views/ChatTerminal.vue'

// Mock axios
vi.mock('axios', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: { session_id: 'test-session' } }),
    delete: vi.fn().mockResolvedValue({ status: 200 })
  }
}))

function createTestRouter() {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/chat', component: ChatTerminal }
    ]
  })
}

describe('ChatTerminal Smoke Tests', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/chat')
    await router.isReady()
  })

  it('should mount component successfully', () => {
    const wrapper = mount(ChatTerminal, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.exists()).toBe(true)
  })

  it('should display sidebar button in Chinese', () => {
    const wrapper = mount(ChatTerminal, {
      global: {
        plugins: [router, pinia]
      }
    })
    expect(wrapper.text()).toContain('新建会话')
  })

  it('should display config labels in Chinese', () => {
    const wrapper = mount(ChatTerminal, {
      global: {
        plugins: [router, pinia]
      }
    })
    const text = wrapper.text()
    expect(text).toContain('工作流')
    expect(text).toContain('知识库')
  })

  it('should display input placeholder in Chinese', () => {
    const wrapper = mount(ChatTerminal, {
      global: {
        plugins: [router, pinia]
      }
    })
    const input = wrapper.find('input.chat-input')
    expect(input.attributes('placeholder')).toBe('输入消息...')
  })

  it('should build chat payload without user_id', () => {
    const wrapper = mount(ChatTerminal, {
      global: {
        plugins: [router, pinia]
      }
    })
    const setup = (wrapper.vm as any).$?.setupState
    const payload = setup.buildChatPayload('session-1', 'hello')
    expect(payload.session_id).toBe('session-1')
    expect(payload.message).toBe('hello')
    expect(payload.user_id).toBeUndefined()
  })

  it('should render clickable citations and open panel', async () => {
    const wrapper = mount(ChatTerminal, {
      global: {
        plugins: [router, pinia]
      }
    })

    const setup = (wrapper.vm as any).$?.setupState
    const citationSource = {
      docId: 'doc-1',
      chunkIndex: 1,
      score: 0.8,
      text: '引用内容'
    }

    setup.sessions = [
      {
        id: 'session-1',
        title: '测试会话',
        createdAt: Date.now(),
        updatedAt: Date.now(),
        messages: [
          {
            role: 'assistant',
            content: 'hello',
            citations: [
              citationSource
            ]
          }
        ]
      }
    ]
    setup.currentSessionId = 'session-1'
    await wrapper.vm.$nextTick()

    const citation = wrapper.find('.citation-item')
    expect(citation.exists()).toBe(true)
    setup.activeCitation = citationSource
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.citation-panel').exists()).toBe(true)
    expect(wrapper.text()).toContain('引用内容')
  })
})

describe('handleSSEEvent', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/chat')
    await router.isReady()
  })

  function getSetup() {
    const wrapper = mount(ChatTerminal, {
      global: { plugins: [router, pinia] }
    })
    return (wrapper.vm as any).$?.setupState
  }

  it('should append token content to lastMessage', () => {
    const setup = getSetup()
    const lastMessage = { role: 'assistant', content: '', isStreaming: true }

    setup.handleSSEEvent('token', { content: 'Hello' }, lastMessage)
    expect(lastMessage.content).toBe('Hello')

    setup.handleSSEEvent('token', { content: ' World' }, lastMessage)
    expect(lastMessage.content).toBe('Hello World')
  })

  it('should set isStreaming=false on done event', () => {
    const setup = getSetup()
    const lastMessage = { role: 'assistant', content: 'test', isStreaming: true }

    setup.handleSSEEvent('done', { status: 'success' }, lastMessage)
    expect(lastMessage.isStreaming).toBe(false)
  })

  it('should handle error event', () => {
    const setup = getSetup()
    const lastMessage = { role: 'assistant', content: '', isStreaming: true }

    setup.handleSSEEvent('error', { message: 'Something broke' }, lastMessage)
    expect(lastMessage.content).toContain('Something broke')
    expect(lastMessage.isStreaming).toBe(false)
  })

  it('should parse citation sources array', () => {
    const setup = getSetup()
    const lastMessage = { role: 'assistant', content: 'test', isStreaming: true, citations: [] as any[] }

    setup.handleSSEEvent('citation', {
      sources: [
        { doc_id: 'doc-1', chunk_index: 0, score: 0.9, text: 'citation text' }
      ]
    }, lastMessage)

    expect(lastMessage.citations).toHaveLength(1)
    expect(lastMessage.citations[0].docId).toBe('doc-1')
    expect(lastMessage.citations[0].score).toBe(0.9)
  })

  it('should update thought for retrieval events', () => {
    const setup = getSetup()
    const lastMessage = { role: 'assistant', content: '', isStreaming: true }

    setup.handleSSEEvent('thought', { type: 'retrieval', status: 'start' }, lastMessage)
    expect(setup.currentThought).toBe('正在检索知识库...')

    setup.handleSSEEvent('thought', { type: 'retrieval', status: 'searching' }, lastMessage)
    expect(setup.currentThought).toBe('正在搜索相关文档...')
  })

  it('should update thought for workflow events', () => {
    const setup = getSetup()
    const lastMessage = { role: 'assistant', content: '', isStreaming: true }

    setup.handleSSEEvent('thought', { type: 'workflow', status: 'start', workflow_name: 'test' }, lastMessage)
    expect(setup.currentThought).toContain('test')
  })

  it('should ignore events when lastMessage is undefined', () => {
    const setup = getSetup()
    // Should not throw
    setup.handleSSEEvent('token', { content: 'test' }, undefined)
  })

  it('should ignore events when lastMessage role is user', () => {
    const setup = getSetup()
    const lastMessage = { role: 'user', content: 'test' }

    setup.handleSSEEvent('token', { content: 'appended' }, lastMessage)
    expect(lastMessage.content).toBe('test') // unchanged
  })
})

describe('Skill autocomplete', () => {
  let router: ReturnType<typeof createTestRouter>
  let pinia: ReturnType<typeof createPinia>

  beforeEach(async () => {
    router = createTestRouter()
    pinia = createPinia()
    await router.push('/chat')
    await router.isReady()
  })

  it('should show suggestions when typing @', async () => {
    const wrapper = mount(ChatTerminal, {
      global: { plugins: [router, pinia] }
    })

    const setup = (wrapper.vm as any).$?.setupState
    setup.skills = [
      { name: 'article-summary', description: 'Summarize articles' },
      { name: 'translate', description: 'Translate text' }
    ]

    setup.inputMessage = '@art'
    setup.onInputChange()

    expect(setup.showSuggestions).toBe(true)
    expect(setup.filteredSkills.length).toBe(1)
    expect(setup.filteredSkills[0].name).toBe('article-summary')
  })

  it('should hide suggestions after space', () => {
    const wrapper = mount(ChatTerminal, {
      global: { plugins: [router, pinia] }
    })

    const setup = (wrapper.vm as any).$?.setupState
    setup.skills = [
      { name: 'translate', description: 'Translate text' }
    ]

    setup.inputMessage = '@translate some text'
    setup.onInputChange()

    expect(setup.showSuggestions).toBe(false)
  })

  it('should replace input on suggestion select', () => {
    const wrapper = mount(ChatTerminal, {
      global: { plugins: [router, pinia] }
    })

    const setup = (wrapper.vm as any).$?.setupState
    setup.inputMessage = '@art'

    setup.selectSuggestion({ name: 'article-summary', description: '' })
    expect(setup.inputMessage).toBe('@article-summary ')
  })
})
