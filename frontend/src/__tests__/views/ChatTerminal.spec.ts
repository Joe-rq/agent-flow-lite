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
    const input = wrapper.find('input[type="text"]')
    expect(input.attributes('placeholder')).toBe('输入消息...')
  })

  it('should include user_id in chat payload', () => {
    localStorage.setItem('user_id', 'user-123')
    const wrapper = mount(ChatTerminal, {
      global: {
        plugins: [router, pinia]
      }
    })
    const setup = (wrapper.vm as any).$?.setupState
    const payload = setup.buildChatPayload('session-1', 'hello')
    expect(payload.user_id).toBe('user-123')
    localStorage.removeItem('user_id')
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
